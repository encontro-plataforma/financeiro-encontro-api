from dataclasses import replace
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException
from app.integracao.regras.dtos import (
    CandidatoLancamento,
    ItemDetalhamento,
    PendenciaAuditoria,
)
from app.integracao.regras.motor_extracao import extrair_detalhamentos
from app.integracao.regras.motor_match import selecionar_lancamento
from app.models.detalhamento import Detalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import (
    EscopoRegraGrupo,
    StatusLancamento,
    TipoDetalhamento,
    TipoLancamento,
)
from app.models.lancamento import Lancamento
from app.repositories.regra_repository import RegraRepository
from app.services.detalhamento_service import DetalhamentoService
from app.utils.decimal_utils import to_decimal

_TOLERANCIA = Decimal("0.01")

_ESCOPO_POR_TIPO = {
    TipoDetalhamento.INSCRICAO_ENCONTREIRO: EscopoRegraGrupo.EXTRACAO_ENCONTREIRO,
    TipoDetalhamento.INSCRICAO_ENCONTRISTA: EscopoRegraGrupo.EXTRACAO_ENCONTRISTA,
}


def _to_pendencia_auditoria(inscricao_pendente) -> PendenciaAuditoria:
    return PendenciaAuditoria(
        id=inscricao_pendente.id,
        nome=inscricao_pendente.nome,
        nome_pagador=inscricao_pendente.nome_pagador,
        dt_pagamento=inscricao_pendente.dt_pagamento,
        pagamento=to_decimal(inscricao_pendente.pagamento),
        observacao=inscricao_pendente.observacao,
    )


def _buscar_candidatos(
    db: Session, dt_pagamento, pagamento: Decimal
) -> list[Lancamento]:
    return (
        db.query(Lancamento)
        .filter(
            Lancamento.data_pagamento == dt_pagamento,
            Lancamento.tipo == TipoLancamento.RECEITA,
            Lancamento.status == StatusLancamento.NAO_CONCILIADO,
            Lancamento.valor >= pagamento - _TOLERANCIA,
        )
        .all()
    )


def _selecionar_lancamento(
    db: Session, pendencia: PendenciaAuditoria
) -> Lancamento | None:
    """Etapa A (Match): decide qual Lancamento corresponde à pendência."""
    candidatos_orm = _buscar_candidatos(db, pendencia.dt_pagamento, pendencia.pagamento)
    if not candidatos_orm:
        return None

    candidatos_dto = [
        CandidatoLancamento(
            id=candidato.id,
            descricao=candidato.descricao,
            valor=to_decimal(candidato.valor),
            soma_detalhamentos=to_decimal(candidato.soma_detalhamentos),
            forma_pagamento=candidato.forma_pagamento,
            cart_parcelas=candidato.cart_parcelas,
        )
        for candidato in candidatos_orm
    ]

    ## Parte A
    escolhido = selecionar_lancamento(pendencia, candidatos_dto)
    if not escolhido:
        return None

    por_id = {l.id: l for l in candidatos_orm}
    return por_id[escolhido.id]


def _criar_detalhamentos(
    db: Session, lancamento: Lancamento, itens: list[ItemDetalhamento]
) -> str | None:
    """Cria os itens da Etapa B (Extração). Se a soma exceder a capacidade
    restante do lançamento, não cria nada e devolve o motivo do erro."""
    capacidade = to_decimal(lancamento.valor) - to_decimal(
        lancamento.soma_detalhamentos
    )
    soma_itens = sum((item.valor for item in itens), Decimal(0))
    if soma_itens > capacidade + _TOLERANCIA:
        return (
            f"Os detalhamentos identificados na observação somam R$ {soma_itens:.2f}, "
            f"mas o lançamento só tem R$ {capacidade:.2f} de capacidade restante."
        )

    for item in itens:
        try:
            DetalhamentoService.create(
                db,
                {
                    "lancamento_id": lancamento.id,
                    "tipo": item.tipo,
                    "referencia_id": item.referencia_id,
                    "valor": item.valor,
                    "descricao": item.descricao or "",
                },
            )
        except BadRequestException as e:
            return str(e)

    return None


def _processar_pendentes(
    db: Session, modelo: Encontreiro | Encontrista, tipo_detalhamento: TipoDetalhamento
):
    vinculados = 0
    nao_auditados = []

    insc_pendentes: list[Encontreiro | Encontrista] = (
        db.query(modelo)
        .filter(
            modelo.auditado.is_(False),
            modelo.dt_pagamento.isnot(None),
            modelo.pagamento.isnot(None),
            modelo.pagamento > 0,
        )
        .order_by(modelo.dt_pagamento)
        .all()
    )

    for inscricao_pendente in insc_pendentes:
        ## 1 - Match de lancamento (Etapa A)
        pendencia_auditoria = _to_pendencia_auditoria(inscricao_pendente)
        lancamento = _selecionar_lancamento(db, pendencia_auditoria)

        if not lancamento:
            nao_auditados.append(
                {
                    "tipo": tipo_detalhamento.value,
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                }
            )
            continue

        ## 2 - Extração de detalhamentos - Regras (Etapa B)
        valor_resto_lancamento = to_decimal(lancamento.valor) - to_decimal(
            lancamento.soma_detalhamentos
        )
        permite_fallback = valor_resto_lancamento >= (
            to_decimal(lancamento.valor) - _TOLERANCIA
        )

        # Lançamento veio do extrato de cartão: a igreja só fica com o valor
        # líquido (o resto é taxa da maquininha), então a extração usa o
        # líquido no lugar do bruto. A Etapa A (match), acima, já rodou com o
        # pagamento original (bruto), que é o que bate com o valor do lançamento.
        eh_cartao = lancamento.cart_taxa is not None
        pendencia_para_extracao = (
            replace(
                pendencia_auditoria, pagamento=to_decimal(lancamento.cart_valor_liquido)
            )
            if eh_cartao
            else pendencia_auditoria
        )

        grupoRegras = RegraRepository.list_ativos_por_escopos(
            db, [_ESCOPO_POR_TIPO[tipo_detalhamento]]
        )
        itens = extrair_detalhamentos(
            pendencia_para_extracao, grupoRegras, tipo_detalhamento, permite_fallback
        )

        if not itens:
            nao_auditados.append(
                {
                    "tipo": tipo_detalhamento.value,
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                    "lancamento_id": lancamento.id,
                    "motivo": (
                        "Lançamento já possui outra inscrição vinculada e a observação "
                        "não permite identificar o valor desta pessoa."
                    ),
                }
            )
            continue

        if eh_cartao:
            itens = itens + [
                ItemDetalhamento(
                    tipo=TipoDetalhamento.OUTRO,
                    valor=to_decimal(lancamento.cart_taxa),
                    referencia_id=None,
                    descricao="Taxa do Cartão",
                )
            ]

        error_message = _criar_detalhamentos(db, lancamento, itens)

        if error_message:
            nao_auditados.append(
                {
                    "tipo": tipo_detalhamento.value,
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                    "lancamento_id": lancamento.id,
                    "motivo": error_message,
                }
            )
            continue

        vinculados += 1

    return len(insc_pendentes), vinculados, nao_auditados


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
