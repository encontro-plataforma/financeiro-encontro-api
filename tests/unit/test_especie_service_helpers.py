from app.models.enums import TipoDetalhamento
from app.services.especie_service import (
    formatar_descricao_detalhamento,
    resolver_nome_finalidade_avulso,
    resolver_tipo_detalhamento,
)


def test_encontreiro_e_apelido_de_inscricao_encontreiro():
    assert resolver_tipo_detalhamento("ENCONTREIRO") == TipoDetalhamento.INSCRICAO_ENCONTREIRO
    assert resolver_tipo_detalhamento("encontreiro") == TipoDetalhamento.INSCRICAO_ENCONTREIRO
    assert resolver_tipo_detalhamento("INSCRICAO_ENCONTREIRO") == TipoDetalhamento.INSCRICAO_ENCONTREIRO


def test_encontrista_e_apelido_de_inscricao_encontrista():
    assert resolver_tipo_detalhamento("ENCONTRISTA") == TipoDetalhamento.INSCRICAO_ENCONTRISTA


def test_oferta_mapeia_direto():
    assert resolver_tipo_detalhamento("OFERTA") == TipoDetalhamento.OFERTA
    assert resolver_tipo_detalhamento("oferta") == TipoDetalhamento.OFERTA


def test_qualquer_outro_tipo_vira_outro():
    assert resolver_tipo_detalhamento("PERSONALIZADO") == TipoDetalhamento.OUTRO
    assert resolver_tipo_detalhamento("CAMPANHA") == TipoDetalhamento.OUTRO
    assert resolver_tipo_detalhamento("LIVRARIA") == TipoDetalhamento.OUTRO
    assert resolver_tipo_detalhamento("QUALQUER_COISA_NOVA") == TipoDetalhamento.OUTRO


def test_formata_descricao_com_descricao_e_observacao():
    resultado = formatar_descricao_detalhamento("PERSONALIZADO", "Caneca", "Cor azul, tamanho G")
    assert resultado == "Lançamento de PERSONALIZADO para Caneca (Cor azul, tamanho G)"


def test_formata_descricao_sem_observacao():
    resultado = formatar_descricao_detalhamento("OFERTA", "Oferta do culto", None)
    assert resultado == "Lançamento de OFERTA para Oferta do culto"


def test_formata_descricao_sem_descricao_nem_observacao():
    resultado = formatar_descricao_detalhamento("OFERTA", None, None)
    assert resultado == "Lançamento de OFERTA"


def test_resolver_finalidade_avulso_conhece_categorias_seedadas():
    assert resolver_nome_finalidade_avulso("OFERTA") == "OFERTA"
    assert resolver_nome_finalidade_avulso("campanha") == "CAMPANHA"
    assert resolver_nome_finalidade_avulso("Personalizado") == "PERSONALIZADO"
    assert resolver_nome_finalidade_avulso("lanchonete") == "LANCHONETE"
    assert resolver_nome_finalidade_avulso("LIVRARIA") == "LIVRARIA"


def test_resolver_finalidade_avulso_categoria_desconhecida_retorna_none():
    assert resolver_nome_finalidade_avulso("PATIO_DE_JOGOS") is None
