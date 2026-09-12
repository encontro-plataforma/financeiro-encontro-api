from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import FormaPagamento
from app.services.auditoria.estrategias import (
    EstrategiaAuditoriaEncontreiro,
    EstrategiaAuditoriaEncontrista,
)
from app.services.auditoria.pipeline import PipelineAuditoria
from app.services.auditoria.relator import RelatorProcessamento
from app.services.auditoria.sink import SimulacaoSink


def _pendente(id_, nome, nome_pagador, pagamento, observacao):
    return MagicMock(
        id=id_,
        nome=nome,
        nome_pagador=nome_pagador,
        pagamento=Decimal(str(pagamento)),
        observacao=observacao,
        dt_pagamento=date(2026, 1, 1),
    )


def _lancamento_candidato(id_, descricao, valor):
    lancamento = MagicMock(id=id_, descricao=descricao)
    lancamento.valor = Decimal(str(valor))
    lancamento.soma_detalhamentos = Decimal("0")
    lancamento.forma_pagamento = FormaPagamento.PIX
    lancamento.cart_parcelas = None
    lancamento.cart_taxa = None
    return lancamento


def _db_com(pendente_encontreiro, pendente_encontrista, lancamento_candidato):
    db = MagicMock()

    def fake_query(modelo):
        query = MagicMock()
        if modelo is Encontreiro:
            query.filter.return_value.order_by.return_value.all.return_value = (
                [pendente_encontreiro] if pendente_encontreiro else []
            )
        elif modelo is Encontrista:
            query.filter.return_value.order_by.return_value.all.return_value = (
                [pendente_encontrista] if pendente_encontrista else []
            )
        else:  # Lancamento
            query.filter.return_value.all.return_value = (
                [lancamento_candidato] if lancamento_candidato else []
            )
        return query

    db.query.side_effect = fake_query
    return db


def test_pipeline_pula_pagamento_multiplo_e_vincula_pendencia_normal_via_fallback():
    """Cenário fim-a-fim (sem regras ativas -- extração cai no fallback do
    valor bruto): a pendência de Encontreiro tem "pagamento múltiplo" na
    observação e deve ser pulada sem tentar match nenhum; a de Encontrista é
    normal e deve casar com o lançamento candidato e gerar 1 Detalhamento."""
    pendente_encontreiro = _pendente(1, "Joao Silva", None, 100, "Pagamento múltiplo, ver planilha")
    pendente_encontrista = _pendente(2, "Maria Souza", "Maria Souza", 100, "Pix")
    lancamento = _lancamento_candidato(50, "PIX MARIA SOUZA", 100)

    db = _db_com(pendente_encontreiro, pendente_encontrista, lancamento)

    with patch(
        "app.services.auditoria.pipeline.RegraRepository.list_ativos_por_escopos",
        return_value=[],
    ):
        pipeline = PipelineAuditoria(
            [EstrategiaAuditoriaEncontreiro(), EstrategiaAuditoriaEncontrista()]
        )
        resultado = pipeline.executar(db, SimulacaoSink(), RelatorProcessamento())

    assert resultado["avaliados"] == 2
    assert resultado["vinculados_encontreiro"] == 0
    assert resultado["vinculados_encontrista"] == 1
    assert resultado["nao_auditados"] == 1

    detalhe = resultado["detalhes_nao_auditados"][0]
    assert detalhe["id"] == 1
    assert detalhe["tipo"] == "INSCRICAO_ENCONTREIRO"
    assert "múltiplo" in detalhe["motivo"].lower()


def test_pipeline_reporta_sem_lancamento_quando_etapa_a_nao_acha_candidato():
    pendente_encontrista = _pendente(2, "Maria Souza", "Maria Souza", 100, "Pix")
    db = _db_com(pendente_encontreiro=None, pendente_encontrista=pendente_encontrista, lancamento_candidato=None)

    pipeline = PipelineAuditoria([EstrategiaAuditoriaEncontrista()])
    resultado = pipeline.executar(db, SimulacaoSink(), RelatorProcessamento())

    assert resultado["avaliados"] == 1
    assert resultado["vinculados_encontrista"] == 0
    assert resultado["nao_auditados"] == 1
    detalhe = resultado["detalhes_nao_auditados"][0]
    assert "motivo" not in detalhe
    assert "lancamento_id" not in detalhe
