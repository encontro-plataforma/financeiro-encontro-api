from unittest.mock import MagicMock

from app.integracao.regras.deteccao_pagamento_multiplo import MOTIVO_PAGAMENTO_MULTIPLO
from app.services.auditoria.relator import RelatorProcessamento
from app.services.common.tipo_pessoa_config import TIPO_PESSOA_ENCONTREIRO, TIPO_PESSOA_ENCONTRISTA


def _pendente(id_, nome):
    return MagicMock(id=id_, nome=nome)


def _lancamento(id_):
    return MagicMock(id=id_)


def test_agrega_vinculados_por_tipo():
    relator = RelatorProcessamento()
    relator.vinculada(TIPO_PESSOA_ENCONTREIRO, _pendente(1, "A"), _lancamento(10), [])
    relator.vinculada(TIPO_PESSOA_ENCONTREIRO, _pendente(2, "B"), _lancamento(11), [])
    relator.vinculada(TIPO_PESSOA_ENCONTRISTA, _pendente(3, "C"), _lancamento(12), [])

    resultado = relator.resultado()

    assert resultado["avaliados"] == 3
    assert resultado["vinculados_encontreiro"] == 2
    assert resultado["vinculados_encontrista"] == 1
    assert resultado["nao_auditados"] == 0
    assert resultado["detalhes_nao_auditados"] == []


def test_pulada_pagamento_multiplo_entra_em_nao_auditados_com_motivo():
    relator = RelatorProcessamento()
    relator.pulada_pagamento_multiplo(TIPO_PESSOA_ENCONTRISTA, _pendente(5, "D"))

    resultado = relator.resultado()

    assert resultado["avaliados"] == 1
    assert resultado["nao_auditados"] == 1
    detalhe = resultado["detalhes_nao_auditados"][0]
    assert detalhe["tipo"] == "INSCRICAO_ENCONTRISTA"
    assert detalhe["motivo"] == MOTIVO_PAGAMENTO_MULTIPLO
    assert "lancamento_id" not in detalhe


def test_sem_lancamento_nao_inclui_lancamento_id_nem_motivo():
    relator = RelatorProcessamento()
    relator.sem_lancamento(TIPO_PESSOA_ENCONTREIRO, _pendente(6, "E"))

    detalhe = relator.resultado()["detalhes_nao_auditados"][0]
    assert "lancamento_id" not in detalhe
    assert "motivo" not in detalhe


def test_com_erro_inclui_lancamento_id_e_motivo():
    relator = RelatorProcessamento()
    relator.com_erro(
        TIPO_PESSOA_ENCONTREIRO, _pendente(7, "F"), _lancamento(20), "capacidade excedida"
    )

    detalhe = relator.resultado()["detalhes_nao_auditados"][0]
    assert detalhe["lancamento_id"] == 20
    assert detalhe["motivo"] == "capacidade excedida"
