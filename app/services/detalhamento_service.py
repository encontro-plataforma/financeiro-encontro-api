from decimal import Decimal

from sqlalchemy.orm import Session
from app.repositories.detalhamento_repository import DetalhamentoRepository
from app.repositories.lancamento_repository import LancamentoRepository
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.detalhamento import Detalhamento
from app.models.enums import StatusLancamento, TipoDetalhamento, TipoLancamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository
from app.repositories.finalidade_repository import FinalidadeRepository
from app.services.vinculo_pessoa_service import calcular_saldo_pendente, excede_saldo_pessoa
from app.utils.decimal_utils import TOLERANCIA_VINCULO, to_decimal

_ROTULO_POR_TIPO = {
    TipoDetalhamento.OFERTA: "OFERTA",
    TipoDetalhamento.OUTRO: "OUTRO",
}

_TIPOS_INSCRICAO = {TipoDetalhamento.INSCRICAO_ENCONTREIRO, TipoDetalhamento.INSCRICAO_ENCONTRISTA}

_TOLERANCIA = TOLERANCIA_VINCULO


class DetalhamentoService:
    """create/update/delete mantêm o status do Lancamento sincronizado com a
    cobertura dos detalhamentos (ver _sincronizar_status_lancamento/_desconciliar_lancamento)
    e forçam a finalidade "INSCRIÇÃO" quando o detalhamento é de inscrição
    (ver _aplicar_finalidade_inscricao). AuditoriaService.processar() também passa
    por aqui, então os vínculos automáticos recebem o mesmo tratamento."""

    @staticmethod
    def _enriquecer(db: Session, detalhamento):
        if detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO:
            pessoa = EncontreiroRepository.get_by_id(db, detalhamento.referencia_id)
            detalhamento.detalhe_nome = pessoa.nome if pessoa else "(encontreiro removido)"
            detalhamento.observacao_efetiva = (pessoa.observacao or "") if pessoa else ""

        elif detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA:
            pessoa = EncontristaRepository.get_by_id(db, detalhamento.referencia_id)
            detalhamento.detalhe_nome = pessoa.nome if pessoa else "(encontrista removido)"
            detalhamento.observacao_efetiva = (pessoa.observacao or "") if pessoa else ""

        else:
            detalhamento.detalhe_nome = _ROTULO_POR_TIPO.get(detalhamento.tipo, detalhamento.tipo.value)
            detalhamento.observacao_efetiva = detalhamento.descricao or ""

        return detalhamento

    @staticmethod
    def list_all(db: Session, params):
        items = DetalhamentoRepository.list_all(db, params)
        return [DetalhamentoService._enriquecer(db, item) for item in items]

    @staticmethod
    def list(db: Session, params):
        items, total = DetalhamentoRepository.list_with_count(db, params)
        items = [DetalhamentoService._enriquecer(db, item) for item in items]

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def _validar_vinculo_permitido(db: Session, lancamento_id: int):
        lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
        if not lancamento:
            return  # FK constraint cuida do erro de integridade; fora de escopo aqui

        if lancamento.tipo == TipoLancamento.DESPESA:
            raise BadRequestException(
                "Não é possível vincular detalhamentos a um lançamento de despesa."
            )

        if lancamento.status == StatusLancamento.CONCILIADO:
            raise BadRequestException(
                "Não é possível incluir detalhamentos em um lançamento já conciliado. "
                "Desconcilie antes de alterar."
            )

    @staticmethod
    def _validar_soma(db: Session, lancamento_id: int, novo_valor, excluir_id: int = None):
        lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
        if not lancamento:
            return  # FK constraint cuida do erro de integridade; fora de escopo aqui

        existentes = (
            db.query(Detalhamento)
            .filter(Detalhamento.lancamento_id == lancamento_id)
            .all()
        )
        soma_outros = sum((d.valor for d in existentes if d.id != excluir_id), Decimal("0"))
        resto = to_decimal(lancamento.valor) - soma_outros
        valor_decimal = to_decimal(novo_valor)

        if valor_decimal > resto + _TOLERANCIA:
            raise BadRequestException(
                f"Não é possível incluir um detalhamento de R$ {valor_decimal:.2f}: "
                f"este lançamento tem apenas R$ {resto:.2f} ainda não vinculado."
            )

    @staticmethod
    def _validar_referencia_pessoa(db: Session, tipo, referencia_id):
        """Para INSCRICAO_*, confirma que referencia_id aponta pra uma pessoa
        existente e do tipo compatível (Encontreiro para INSCRICAO_ENCONTREIRO,
        Encontrista para INSCRICAO_ENCONTRISTA). Retorna a pessoa (reaproveitada
        por _validar_soma_pessoa) ou None para OFERTA/OUTRO, que não referenciam
        ninguém."""
        if tipo not in _TIPOS_INSCRICAO:
            return None

        if referencia_id is None:
            raise BadRequestException("Detalhamentos de inscrição precisam de referencia_id.")

        if tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO:
            pessoa = EncontreiroRepository.get_by_id(db, referencia_id)
            if not pessoa:
                raise NotFoundException("Encontreiro")
        else:
            pessoa = EncontristaRepository.get_by_id(db, referencia_id)
            if not pessoa:
                raise NotFoundException("Encontrista")

        return pessoa

    @staticmethod
    def _validar_soma_pessoa(db: Session, tipo, referencia_id, pessoa, novo_valor, excluir_id: int = None):
        """Espelha _validar_soma, mas do lado da pessoa: a soma dos Detalhamentos
        de inscrição dela (possivelmente em vários lançamentos) não pode
        ultrapassar o `pagamento` total esperado da ficha, com a mesma
        tolerância de R$0,01."""
        if pessoa is None or pessoa.pagamento is None:
            return

        existentes = DetalhamentoRepository.list_by_referencia(db, tipo, referencia_id)
        soma_outros = sum((d.valor for d in existentes if d.id != excluir_id), Decimal("0"))
        valor_decimal = to_decimal(novo_valor)
        pagamento = to_decimal(pessoa.pagamento)

        if excede_saldo_pessoa(soma_outros, valor_decimal, pagamento):
            saldo = calcular_saldo_pendente(soma_outros, pagamento)
            raise BadRequestException(
                f"Não é possível vincular R$ {valor_decimal:.2f} a esta inscrição: "
                f"o saldo pendente da pessoa é de apenas R$ {saldo:.2f}."
            )

    @staticmethod
    def _sincronizar_status_lancamento(db: Session, lancamento_id: int):
        """Concilia automaticamente o lançamento quando a soma dos detalhamentos
        atinge (ou ultrapassa, dentro da tolerância) o valor total."""
        lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
        if not lancamento:
            return

        soma = sum(
            (d.valor for d in db.query(Detalhamento).filter(Detalhamento.lancamento_id == lancamento_id).all()),
            Decimal("0"),
        )

        if soma >= to_decimal(lancamento.valor) - _TOLERANCIA:
            lancamento.status = StatusLancamento.CONCILIADO
            db.commit()

    @staticmethod
    def _aplicar_finalidade_inscricao(db: Session, lancamento_id: int, tipo):
        """Vincular uma inscrição (Encontreiro/Encontrista) a um lançamento sempre
        indica que ele é uma receita de inscrição — força a finalidade para não
        depender do usuário lembrar de trocá-la manualmente."""
        if tipo not in _TIPOS_INSCRICAO:
            return

        lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
        if not lancamento:
            return

        finalidade = FinalidadeRepository.get_by_nome(db, "INSCRIÇÃO")
        if not finalidade or lancamento.finalidade_id == finalidade.id:
            return

        lancamento.finalidade_id = finalidade.id
        db.commit()

    @staticmethod
    def _desconciliar_lancamento(db: Session, lancamento_id: int):
        """Um detalhamento removido (ou trocado de lançamento) significa que a
        cobertura anterior não vale mais — o lançamento volta a precisar de revisão."""
        lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
        if not lancamento:
            return

        lancamento.status = StatusLancamento.NAO_CONCILIADO
        db.commit()

    @staticmethod
    def create(db: Session, data: dict):
        DetalhamentoService._validar_vinculo_permitido(db, data["lancamento_id"])
        DetalhamentoService._validar_soma(db, data["lancamento_id"], data["valor"])
        pessoa = DetalhamentoService._validar_referencia_pessoa(db, data["tipo"], data.get("referencia_id"))
        DetalhamentoService._validar_soma_pessoa(db, data["tipo"], data.get("referencia_id"), pessoa, data["valor"])
        obj = DetalhamentoRepository.create(db, data)
        DetalhamentoService._sincronizar_status_lancamento(db, data["lancamento_id"])
        DetalhamentoService._aplicar_finalidade_inscricao(db, data["lancamento_id"], obj.tipo)
        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def update(db: Session, detalhamento_id: int, data: dict):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        lancamento_id_antigo = obj.lancamento_id
        lancamento_id_novo = data.get("lancamento_id", lancamento_id_antigo)

        if lancamento_id_novo != lancamento_id_antigo:
            DetalhamentoService._validar_vinculo_permitido(db, lancamento_id_novo)

        novo_valor = data.get("valor", obj.valor)
        DetalhamentoService._validar_soma(db, lancamento_id_novo, novo_valor, excluir_id=detalhamento_id)

        tipo_novo = data.get("tipo", obj.tipo)
        referencia_id_novo = data.get("referencia_id", obj.referencia_id)
        pessoa = DetalhamentoService._validar_referencia_pessoa(db, tipo_novo, referencia_id_novo)
        DetalhamentoService._validar_soma_pessoa(
            db, tipo_novo, referencia_id_novo, pessoa, novo_valor, excluir_id=detalhamento_id
        )

        obj = DetalhamentoRepository.update(db, obj, data)

        if lancamento_id_novo != lancamento_id_antigo:
            DetalhamentoService._desconciliar_lancamento(db, lancamento_id_antigo)
            DetalhamentoService._sincronizar_status_lancamento(db, lancamento_id_novo)
            DetalhamentoService._aplicar_finalidade_inscricao(db, lancamento_id_novo, obj.tipo)

        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def delete(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        lancamento_id = obj.lancamento_id
        DetalhamentoRepository.delete(db, obj)
        DetalhamentoService._desconciliar_lancamento(db, lancamento_id)
