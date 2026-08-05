from app.models.enums import TipoDetalhamento
from app.models.regra_grupo import RegraGrupo
from app.repositories.regra_repository import _montar_regra, _sincronizar_ativo_grupo


def test_regra_sem_condicao_nasce_desativada():
    regra = _montar_regra({
        "nome": "Nova regra",
        "ordem": 1,
        "ativo": True,  # tentativa de forçar ativo mesmo sem condição
        "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
        "condicoes": [],
    })

    assert regra.ativo is False


def test_regra_com_condicao_respeita_ativo_informado():
    regra = _montar_regra({
        "nome": "Oferta",
        "ordem": 1,
        "ativo": True,
        "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
        "condicoes": [{"ordem": 1, "padrao_regex": "oferta"}],
    })

    assert regra.ativo is True
    assert len(regra.condicoes) == 1


def test_remover_todas_condicoes_desativa_regra():
    regra = _montar_regra({
        "nome": "Oferta",
        "ordem": 1,
        "ativo": True,
        "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
        "condicoes": [],  # todas as condições foram removidas nesta edição
    })

    assert regra.ativo is False


def _grupo_com_regras(*, grupo_ativo: bool, regras_ativas: list):
    grupo = RegraGrupo(nome="Teste", escopo="OFERTAS", ordem=1, ativo=grupo_ativo)
    grupo.regras = [
        _montar_regra({
            "nome": f"Regra {i}",
            "ordem": i,
            "ativo": ativa,
            "tipo_detalhamento_resultado": TipoDetalhamento.OFERTA,
            "condicoes": [{"ordem": 1, "padrao_regex": "x"}] if ativa else [],
        })
        for i, ativa in enumerate(regras_ativas, start=1)
    ]
    return grupo


def test_grupo_desativa_sozinho_sem_nenhuma_regra_ativa():
    grupo = _grupo_com_regras(grupo_ativo=True, regras_ativas=[False, False])
    _sincronizar_ativo_grupo(grupo)
    assert grupo.ativo is False


def test_grupo_desativa_sozinho_sem_nenhuma_regra():
    grupo = _grupo_com_regras(grupo_ativo=True, regras_ativas=[])
    _sincronizar_ativo_grupo(grupo)
    assert grupo.ativo is False


def test_grupo_continua_ativo_com_pelo_menos_uma_regra_ativa():
    grupo = _grupo_com_regras(grupo_ativo=True, regras_ativas=[False, True])
    _sincronizar_ativo_grupo(grupo)
    assert grupo.ativo is True


def test_grupo_inativo_nao_reativa_sozinho():
    # Confirma que a sincronização só DESATIVA — nunca ativa o grupo sozinha.
    grupo = _grupo_com_regras(grupo_ativo=False, regras_ativas=[True])
    _sincronizar_ativo_grupo(grupo)
    assert grupo.ativo is False
