from dataclasses import dataclass, replace
from decimal import Decimal

from sqlalchemy.orm import Session

from app.integracao.regras.deteccao_pagamento_multiplo import eh_pagamento_multiplo
from app.integracao.regras.dtos import (
    CandidatoLancamento,
    ItemDetalhamento,
    PendenciaAuditoria,
)
from app.integracao.regras.motor_extracao import extrair_detalhamentos_com_origem
from app.integracao.regras.motor_match import selecionar_lancamento
from app.models.enums import StatusLancamento, TipoLancamento
from app.models.lancamento import Lancamento
from app.repositories.regra_repository import RegraRepository
from app.services.auditoria.estrategias import EstrategiaAuditoriaPessoa
from app.services.auditoria.hooks import _aplicar_taxa_cartao, _to_pendencia_auditoria
from app.services.auditoria.relator import RelatorAuditoria
from app.services.auditoria.sink import AplicacaoSink
from app.utils.decimal_utils import to_decimal

_TOLERANCIA = Decimal("0.01")

MOTIVO_SEM_VALOR_IDENTIFICADO = (
    "Lançamento já possui outra inscrição vinculada e a observação "
    "não permite identificar o valor desta pessoa."
)

# Nome de "regra" exibido pra o item de taxa de cartão na resposta de
# simulação -- no fluxo real esse nome é descartado (Detalhamento não tem
# coluna de "regra"), mas passá-lo sempre aqui evita que o pipeline precise
# saber se está em modo real ou simulação.
_REGRA_TAXA_CARTAO = "Taxa do Cartão (automático)"


def _buscar_pendentes(db: Session, estrategia: EstrategiaAuditoriaPessoa):
    """Passo 1: pega as fichas (Encontreiro ou Encontrista, conforme a
    estratégia) ainda não conciliadas com um pagamento pendente, na ordem em
    que os pagamentos entraram -- mesma ordenação usada tanto pelo fluxo real
    quanto pela simulação, pra não haver divergência de comportamento entre
    os dois modos."""
    modelo = estrategia.config.modelo
    return (
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


def _buscar_candidatos(
    db: Session, pendencia: PendenciaAuditoria
) -> tuple[list[CandidatoLancamento], list[Lancamento]] | None:
    """Passo 2: monta a listagem de lançamentos candidatos pra Etapa A --
    já podendo decidir, a partir da observação, que a pendência nem deve ser
    processada ainda (pagamento múltiplo): devolve None nesse caso, sem
    gastar nenhuma query de candidatos."""
    if eh_pagamento_multiplo(pendencia.observacao):
        return None

    candidatos_orm = (
        db.query(Lancamento)
        .filter(
            Lancamento.data_pagamento == pendencia.dt_pagamento,
            Lancamento.tipo == TipoLancamento.RECEITA,
            Lancamento.status == StatusLancamento.NAO_CONCILIADO,
            Lancamento.valor >= pendencia.pagamento - _TOLERANCIA,
        )
        .all()
    )
    candidatos_dto = [
        CandidatoLancamento(
            id=c.id,
            descricao=c.descricao,
            valor=to_decimal(c.valor),
            soma_detalhamentos=to_decimal(c.soma_detalhamentos),
            forma_pagamento=c.forma_pagamento,
            cart_parcelas=c.cart_parcelas,
        )
        for c in candidatos_orm
    ]
    return candidatos_dto, candidatos_orm


def _selecionar_match(
    pendencia: PendenciaAuditoria,
    candidatos_dto: list[CandidatoLancamento],
    candidatos_orm: list[Lancamento],
) -> Lancamento | None:
    """Passo 3: dentre os candidatos, decide qual lançamento corresponde à
    pendência (algoritmo fixo -- ver `motor_match.selecionar_lancamento`)."""
    escolhido = selecionar_lancamento(pendencia, candidatos_dto)
    if not escolhido:
        return None
    return {c.id: c for c in candidatos_orm}[escolhido.id]


@dataclass
class ResultadoPendencia:
    sucesso: bool
    motivo: str | None = None
    itens_com_origem: list[tuple[ItemDetalhamento, str | None]] | None = None


class PipelineAuditoria:
    """Orquestra os 4 passos da auditoria (pegar ficha pendente -> buscar
    candidatos -> selecionar match -> determinar e aplicar detalhamentos),
    reaproveitado tanto pelo fluxo real (`AplicacaoSink` que grava no banco)
    quanto pela simulação (`AplicacaoSink` que só acumula em memória)."""

    def __init__(self, estrategias: list[EstrategiaAuditoriaPessoa]):
        self._estrategias = estrategias

    def _determinar_e_aplicar_detalhamentos(
        self,
        db: Session,
        estrategia: EstrategiaAuditoriaPessoa,
        pendencia: PendenciaAuditoria,
        inscricao_pendente,
        lancamento: Lancamento,
        sink: AplicacaoSink,
    ) -> ResultadoPendencia:
        """Passo 4: Etapa B (Extração) + hook de pós-processamento por tipo
        de pessoa (ex.: biscoitos) + taxa de cartão + aplicação (grava de
        verdade ou só simula, via `sink`)."""
        permite_fallback = sink.capacidade_restante(db, lancamento) >= (
            to_decimal(lancamento.valor) - _TOLERANCIA
        )

        # Lançamento veio do extrato de cartão: a igreja só fica com o valor
        # líquido (o resto é taxa da maquininha), então a extração usa o
        # líquido no lugar do bruto. O match (passo 3), acima, já rodou com o
        # pagamento original (bruto), que é o que bate com o valor do lançamento.
        eh_cartao = lancamento.cart_taxa is not None
        pendencia_extracao = (
            replace(pendencia, pagamento=to_decimal(lancamento.cart_valor_liquido))
            if eh_cartao
            else pendencia
        )

        grupos = RegraRepository.list_ativos_por_escopos(
            db, [estrategia.config.escopo_regra_grupo]
        )
        itens_com_origem = extrair_detalhamentos_com_origem(
            pendencia_extracao,
            grupos,
            estrategia.config.tipo_detalhamento,
            permite_fallback,
        )
        if not itens_com_origem:
            return ResultadoPendencia(False, MOTIVO_SEM_VALOR_IDENTIFICADO)

        itens_com_origem = estrategia.pos_processar(
            db, itens_com_origem, inscricao_pendente, sink, lancamento
        )

        if eh_cartao:
            ja_tem_taxa = sink.ja_tem_taxa_cartao(db, lancamento)
            itens_com_origem = _aplicar_taxa_cartao(
                itens_com_origem,
                to_decimal(lancamento.cart_taxa),
                ja_tem_taxa,
                origem_taxa=_REGRA_TAXA_CARTAO,
            )
            sink.marcar_taxa_cartao_aplicada(lancamento)

        erro = sink.aplicar(db, lancamento, [item for item, _ in itens_com_origem])
        if erro:
            return ResultadoPendencia(False, erro)
        return ResultadoPendencia(True, itens_com_origem=itens_com_origem)

    def _processar_tipo(
        self,
        db: Session,
        estrategia: EstrategiaAuditoriaPessoa,
        sink: AplicacaoSink,
        relator: RelatorAuditoria,
        lancamento_id_alvo: int | None = None,
    ) -> None:
        pendentes = _buscar_pendentes(db, estrategia)

        for pendente in pendentes:
            pendencia = _to_pendencia_auditoria(pendente)

            busca = _buscar_candidatos(db, pendencia)
            if busca is None:
                relator.pulada_pagamento_multiplo(estrategia.config, pendente)
                continue

            lancamento = _selecionar_match(pendencia, *busca)
            if not lancamento:
                relator.sem_lancamento(estrategia.config, pendente)
                continue

            if lancamento_id_alvo is not None and lancamento.id != lancamento_id_alvo:
                continue

            resultado = self._determinar_e_aplicar_detalhamentos(
                db, estrategia, pendencia, pendente, lancamento, sink
            )
            if resultado.sucesso:
                relator.vinculada(
                    estrategia.config, pendente, lancamento, resultado.itens_com_origem
                )
            else:
                relator.com_erro(
                    estrategia.config, pendente, lancamento, resultado.motivo
                )

    def executar(
        self,
        db: Session,
        sink: AplicacaoSink,
        relator: RelatorAuditoria,
        lancamento_id_alvo: int | None = None,
    ) -> dict:
        for estrategia in self._estrategias:
            self._processar_tipo(db, estrategia, sink, relator, lancamento_id_alvo)
        return relator.resultado()
