from decimal import Decimal

from sqlalchemy.orm import Session
from app.repositories.detalhamento_repository import DetalhamentoRepository
from app.repositories.lancamento_repository import LancamentoRepository
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.detalhamento import Detalhamento
from app.models.enums import StatusLancamento, TipoDetalhamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository

_ROTULO_POR_TIPO = {
    TipoDetalhamento.OFERTA: "OFERTA",
    TipoDetalhamento.OUTRO: "OUTRO",
}

_TOLERANCIA = Decimal("0.01")


class DetalhamentoService:
    """create/update/delete mantêm o status do Lancamento sincronizado com a
    cobertura dos detalhamentos (ver _sincronizar_status_lancamento/_desconciliar_lancamento).
    Nota: AuditoriaService.processar() cria Detalhamento diretamente via db.add(),
    sem passar por este service — a auditoria automática ainda não aciona essa
    sincronização (fora do escopo desta mudança)."""

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
        resto = Decimal(str(lancamento.valor)) - soma_outros
        valor_decimal = Decimal(str(novo_valor))

        if valor_decimal > resto + _TOLERANCIA:
            raise BadRequestException(
                f"Não é possível incluir um detalhamento de R$ {valor_decimal:.2f}: "
                f"este lançamento tem apenas R$ {resto:.2f} ainda não vinculado."
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

        if soma >= Decimal(str(lancamento.valor)) - _TOLERANCIA:
            lancamento.status = StatusLancamento.CONCILIADO
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
        DetalhamentoService._validar_soma(db, data["lancamento_id"], data["valor"])
        obj = DetalhamentoRepository.create(db, data)
        DetalhamentoService._sincronizar_status_lancamento(db, data["lancamento_id"])
        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def update(db: Session, detalhamento_id: int, data: dict):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        lancamento_id_antigo = obj.lancamento_id
        lancamento_id_novo = data.get("lancamento_id", lancamento_id_antigo)
        novo_valor = data.get("valor", obj.valor)
        DetalhamentoService._validar_soma(db, lancamento_id_novo, novo_valor, excluir_id=detalhamento_id)

        obj = DetalhamentoRepository.update(db, obj, data)

        if lancamento_id_novo != lancamento_id_antigo:
            DetalhamentoService._desconciliar_lancamento(db, lancamento_id_antigo)
            DetalhamentoService._sincronizar_status_lancamento(db, lancamento_id_novo)

        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def delete(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        lancamento_id = obj.lancamento_id
        DetalhamentoRepository.delete(db, obj)
        DetalhamentoService._desconciliar_lancamento(db, lancamento_id)
