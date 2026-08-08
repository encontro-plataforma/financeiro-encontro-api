from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException
from app.integracao.regras.dtos import CandidatoLancamento, ItemDetalhamento, PendenciaAuditoria
from app.integracao.regras.motor_extracao import extrair_detalhamentos
from app.integracao.regras.motor_match import selecionar_lancamento
from app.models.detalhamento import Detalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import EscopoRegraGrupo, TipoDetalhamento, TipoLancamento
from app.models.lancamento import Lancamento
from app.repositories.regra_repository import RegraRepository
from app.services.detalhamento_service import DetalhamentoService

_TOLERANCIA = Decimal("0.01")

_ESCOPO_POR_TIPO = {
    TipoDetalhamento.INSCRICAO_ENCONTREIRO: EscopoRegraGrupo.EXTRACAO_ENCONTREIRO,
    TipoDetalhamento.INSCRICAO_ENCONTRISTA: EscopoRegraGrupo.EXTRACAO_ENCONTRISTA,
}


def _decimal(valor) -> Decimal:
    return Decimal(str(valor)) if valor is not None else Decimal("0")


def _capacidade_restante(db: Session, lancamento: Lancamento) -> Decimal:
    consumido = (
        db.query(Detalhamento)
        .filter(Detalhamento.lancamento_id == lancamento.id)
        .all()
    )
    total_consumido = sum((d.valor for d in consumido), Decimal("0"))
    return _decimal(lancamento.valor) - total_consumido


def _montar_pendencia(pessoa) -> PendenciaAuditoria:
    return PendenciaAuditoria(
        id=pessoa.id,
        nome=pessoa.nome,
        nome_pagador=pessoa.nome_pagador,
        dt_pagamento=pessoa.dt_pagamento,
        pagamento=_decimal(pessoa.pagamento),
        observacao=pessoa.observacao,
    )


def _buscar_candidatos(db: Session, dt_pagamento) -> list[Lancamento]:
    return (
        db.query(Lancamento)
        .filter(
            Lancamento.data_pagamento == dt_pagamento,
            Lancamento.tipo == TipoLancamento.RECEITA,
        )
        .all()
    )


def _selecionar_lancamento(db: Session, pendencia: PendenciaAuditoria) -> Optional[Lancamento]:
    """Etapa A (Match): decide qual Lancamento corresponde à pendência."""
    candidatos_orm = _buscar_candidatos(db, pendencia.dt_pagamento)
    if not candidatos_orm:
        return None

    candidatos_dto = [
        CandidatoLancamento(id=candidato.id, descricao=candidato.descricao, capacidade_restante=_capacidade_restante(db, candidato))
        for candidato in candidatos_orm
    ]

    ## Parte A
    escolhido = selecionar_lancamento(pendencia, candidatos_dto)
    if not escolhido:
        return None

    por_id = {l.id: l for l in candidatos_orm}
    return por_id[escolhido.id]


def _criar_detalhamentos(db: Session, lancamento: Lancamento, itens: list[ItemDetalhamento]) -> Optional[str]:
    """Cria os itens da Etapa B (Extração). Se a soma exceder a capacidade
    restante do lançamento, não cria nada e devolve o motivo do erro."""
    capacidade = _capacidade_restante(db, lancamento)
    soma_itens = sum((item.valor for item in itens), Decimal("0"))
    if soma_itens > capacidade + _TOLERANCIA:
        return (
            f"Os detalhamentos identificados na observação somam R$ {soma_itens:.2f}, "
            f"mas o lançamento só tem R$ {capacidade:.2f} de capacidade restante."
        )

    for item in itens:
        try:
            DetalhamentoService.create(db, {
                "lancamento_id": lancamento.id,
                "tipo": item.tipo,
                "referencia_id": item.referencia_id,
                "valor": item.valor,
            })
        except BadRequestException as e:
            return str(e)

    return None


def _processar_pendentes(db: Session, modelo, tipo_principal: TipoDetalhamento):
    grupos = RegraRepository.list_ativos_por_escopos(
        db, [_ESCOPO_POR_TIPO[tipo_principal]]
    )

    pendentes = (
        db.query(modelo)
        .filter(
            modelo.pagamento.isnot(None),
            modelo.pagamento > 0,
            modelo.dt_pagamento.isnot(None),
            modelo.auditado.is_(False),
        )
        .order_by(modelo.dt_pagamento)
        .all()
    )

    vinculados = 0
    nao_auditados = []

    for pessoa in pendentes:
        pendencia = _montar_pendencia(pessoa)
        lancamento = _selecionar_lancamento(db, pendencia)

        if not lancamento:
            nao_auditados.append({
                "tipo": tipo_principal.value,
                "id": pessoa.id,
                "nome": pessoa.nome,
            })
            continue

        itens = extrair_detalhamentos(pendencia, grupos, tipo_principal)
        erro = _criar_detalhamentos(db, lancamento, itens)

        if erro:
            nao_auditados.append({
                "tipo": tipo_principal.value,
                "id": pessoa.id,
                "nome": pessoa.nome,
                "motivo": erro,
            })
            continue

        vinculados += 1

    return len(pendentes), vinculados, nao_auditados


class AuditoriaService:

    @staticmethod
    def processar(db: Session) -> dict:
        total_detalhamentos_antes = db.query(Detalhamento).count()

        avaliados_enco, vinculados_enco, nao_auditados_enco = _processar_pendentes(
            db, Encontreiro, TipoDetalhamento.INSCRICAO_ENCONTREIRO
        )
        avaliados_enca, vinculados_enca, nao_auditados_enca = _processar_pendentes(
            db, Encontrista, TipoDetalhamento.INSCRICAO_ENCONTRISTA
        )

        db.commit()

        total_detalhamentos_depois = db.query(Detalhamento).count()
        extras_via_observacao = (
            total_detalhamentos_depois
            - total_detalhamentos_antes
            - vinculados_enco
            - vinculados_enca
        )

        nao_auditados = nao_auditados_enco + nao_auditados_enca

        return {
            "avaliados": avaliados_enco + avaliados_enca,
            "vinculados_encontreiro": vinculados_enco,
            "vinculados_encontrista": vinculados_enca,
            "detalhamentos_extras_via_observacao": extras_via_observacao,
            "nao_auditados": len(nao_auditados),
            "detalhes_nao_auditados": nao_auditados,
            "mensagem": (
                f"Auditoria concluída. {vinculados_enco} encontreiro(s) e "
                f"{vinculados_enca} encontrista(s) vinculados, "
                f"{extras_via_observacao} detalhamento(s) extra(s) via observação, "
                f"{len(nao_auditados)} inscrição(ões) ainda não auditada(s)."
            ),
        }
