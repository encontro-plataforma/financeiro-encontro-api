import json
from unittest.mock import MagicMock, patch

from app.models.enums import StatusProcessamento
from app.services.encontreiro_service import EncontreiroService
from app.services.encontrista_service import EncontristaService


def _row_encontreiro(**overrides):
    defaults = dict(
        id=1,
        linha=2,
        dt_inscricao=None,
        nome="Joao Silva",
        apelido=None,
        instagram=None,
        telefone="11999999999",
        estado_civil=None,
        igreja=None,
        religiao=None,
        contato_emerg=None,
        nome_emerg=None,
        parentesco_emerg=None,
        alergia_comorbidade=None,
        equipe_nome=None,
        camisa=None,
        situacao_camisa=None,
        veiculo=None,
        dt_pagamento=None,
        nome_pagador=None,
        pagamento=None,
        observacao=None,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


def _row_encontrista(**overrides):
    defaults = dict(
        id=1,
        linha=2,
        dt_entrega=None,
        dt_validade=None,
        padrinho_id=1,
        carta=None,
        album=None,
        nome="Maria Souza",
        apelido=None,
        dt_nascimento=None,
        idade=None,
        circulo_nome=None,
        onde_veio_ficha=None,
        instagram=None,
        contato=None,
        religiao=None,
        igreja=None,
        endereco=None,
        cidade=None,
        camisa=None,
        blusa=None,
        veiculo=None,
        contato_emerg=None,
        nome_emerg=None,
        parentesco_emerg=None,
        medicacao=None,
        alergia_comorbidade=None,
        dt_pagamento=None,
        nome_pagador=None,
        pagamento=None,
        observacao=None,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


def test_encontrista_processar_em_background_sem_duplicata_nao_inclui_ignorados():
    """Comportamento atual do Encontrista: sem detecção de duplicata, sem
    `ignorados`/`detalhes_ignorados` no resultado -- contrato preservado
    após a migração pra base compartilhada."""
    row = _row_encontrista()
    db = MagicMock()
    padrinho = MagicMock(id=1)

    with (
        patch("app.services.common.pessoa_service_base.SessionLocal", return_value=db),
        patch("app.services.common.tipo_pessoa_config.encontrista_parser.parse", return_value=[row]),
        patch(
            "app.repositories.encontrista_repository.EncontristaRepository.get_by_id",
            return_value=None,
        ),
        patch(
            "app.repositories.encontreiro_repository.EncontreiroRepository.get_by_id",
            return_value=padrinho,
        ),
        patch("app.services.common.pessoa_service_base.UploadFileService.update_status") as mock_update,
        patch("app.services.common.pessoa_service_base.AuditoriaService.processar"),
    ):
        EncontristaService.processar_em_background(upload_id=99, conteudo="csv...")

    args, kwargs = mock_update.call_args
    assert args[2] == StatusProcessamento.PROCESSADO
    resultado = json.loads(kwargs["resultado_processamento"])

    assert resultado["inseridos"] == 1
    assert "ignorados" not in resultado
    assert "detalhes_ignorados" not in resultado


def test_encontreiro_processar_em_background_com_duplicata_inclui_ignorados():
    """Comportamento atual do Encontreiro: detecta duplicata por
    nome+telefone e reporta em `ignorados`/`detalhes_ignorados` --
    comportamento que o Encontrista não tem, preservado após a migração."""
    row = _row_encontreiro()
    db = MagicMock()
    duplicado = MagicMock(id=5)

    with (
        patch("app.services.common.pessoa_service_base.SessionLocal", return_value=db),
        patch("app.services.common.tipo_pessoa_config.encontreiro_parser.parse", return_value=[row]),
        patch(
            "app.repositories.encontreiro_repository.EncontreiroRepository.get_by_id",
            return_value=None,
        ),
        patch(
            "app.repositories.encontreiro_repository.EncontreiroRepository.get_by_nome_telefone",
            return_value=duplicado,
        ),
        patch("app.services.common.pessoa_service_base.UploadFileService.update_status") as mock_update,
        patch("app.services.common.pessoa_service_base.AuditoriaService.processar"),
    ):
        EncontreiroService.processar_em_background(upload_id=1, conteudo="csv...")

    _, kwargs = mock_update.call_args
    resultado = json.loads(kwargs["resultado_processamento"])

    assert resultado["inseridos"] == 0
    assert resultado["ignorados"] == 1
    assert resultado["detalhes_ignorados"][0]["encontreiro_existente_id"] == 5


def test_processar_em_background_dispara_auditoria_apos_sucesso():
    row = _row_encontrista()
    db = MagicMock()
    padrinho = MagicMock(id=1)

    with (
        patch("app.services.common.pessoa_service_base.SessionLocal", return_value=db),
        patch("app.services.common.tipo_pessoa_config.encontrista_parser.parse", return_value=[row]),
        patch(
            "app.repositories.encontrista_repository.EncontristaRepository.get_by_id",
            return_value=None,
        ),
        patch(
            "app.repositories.encontreiro_repository.EncontreiroRepository.get_by_id",
            return_value=padrinho,
        ),
        patch("app.services.common.pessoa_service_base.UploadFileService.update_status"),
        patch("app.services.common.pessoa_service_base.AuditoriaService.processar") as mock_auditoria,
    ):
        EncontristaService.processar_em_background(upload_id=99, conteudo="csv...")

    mock_auditoria.assert_called_once_with(db)


def test_processar_em_background_erro_marca_upload_como_erro_e_nao_roda_auditoria():
    db = MagicMock()

    with (
        patch("app.services.common.pessoa_service_base.SessionLocal", return_value=db),
        patch(
            "app.services.common.tipo_pessoa_config.encontrista_parser.parse",
            side_effect=Exception("csv malformado"),
        ),
        patch("app.services.common.pessoa_service_base.UploadFileService.update_status") as mock_update,
        patch("app.services.common.pessoa_service_base.AuditoriaService.processar") as mock_auditoria,
    ):
        EncontristaService.processar_em_background(upload_id=99, conteudo="csv...")

    mock_auditoria.assert_not_called()
    db.rollback.assert_called_once()
    args, kwargs = mock_update.call_args
    assert args[2] == StatusProcessamento.ERRO
    assert kwargs["error_code"] == "ERRO_PROCESSAMENTO_ENCONTRISTA"
