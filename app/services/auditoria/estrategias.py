from typing import ClassVar

from app.services.auditoria.hooks import _aplicar_biscoitos
from app.services.common.tipo_pessoa_config import (
    TIPO_PESSOA_ENCONTREIRO,
    TIPO_PESSOA_ENCONTRISTA,
    TipoPessoaConfig,
)


class EstrategiaAuditoriaPessoa:
    """O que hoje é um `if tipo == INSCRICAO_ENCONTRISTA` solto dentro do
    orquestrador vira um hook por tipo de pessoa. `pos_processar` roda
    depois da Etapa B (Extração) e antes da taxa de cartão."""

    config: ClassVar[TipoPessoaConfig]

    def pos_processar(self, db, itens_com_origem, inscricao_pendente, sink, lancamento):
        return itens_com_origem


class EstrategiaAuditoriaEncontreiro(EstrategiaAuditoriaPessoa):
    config = TIPO_PESSOA_ENCONTREIRO


class EstrategiaAuditoriaEncontrista(EstrategiaAuditoriaPessoa):
    config = TIPO_PESSOA_ENCONTRISTA

    def pos_processar(self, db, itens_com_origem, inscricao_pendente, sink, lancamento):
        ja_tem_biscoitos = sink.ja_tem_biscoitos(db, lancamento)
        itens, aplicado = _aplicar_biscoitos(
            db, itens_com_origem, inscricao_pendente, ja_tem_biscoitos
        )
        if aplicado:
            sink.marcar_biscoitos_aplicado(lancamento)
        return itens
