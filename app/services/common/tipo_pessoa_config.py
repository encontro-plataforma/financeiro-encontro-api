from dataclasses import dataclass
from types import ModuleType

from app.integracao.secretaria import encontreiro_parser, encontrista_parser
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import EscopoRegraGrupo, TipoDetalhamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository


@dataclass(frozen=True)
class TipoPessoaConfig:
    """Fonte única de verdade sobre o que diferencia Encontreiro de
    Encontrista -- usada tanto pelo motor de auditoria (match/extração)
    quanto pela importação de CSV, no lugar dos dicts/duplicações que hoje
    espalham essa mesma informação pelos dois domínios."""

    modelo: type
    tipo_detalhamento: TipoDetalhamento
    escopo_regra_grupo: EscopoRegraGrupo
    label: str
    repository: type
    parser: ModuleType
    sequence_name: str
    error_code_importacao: str


TIPO_PESSOA_ENCONTREIRO = TipoPessoaConfig(
    modelo=Encontreiro,
    tipo_detalhamento=TipoDetalhamento.INSCRICAO_ENCONTREIRO,
    escopo_regra_grupo=EscopoRegraGrupo.EXTRACAO_ENCONTREIRO,
    label="ENCONTREIRO",
    repository=EncontreiroRepository,
    parser=encontreiro_parser,
    sequence_name="encontreiros_id_seq",
    error_code_importacao="ERRO_PROCESSAMENTO_ENCONTREIRO",
)

TIPO_PESSOA_ENCONTRISTA = TipoPessoaConfig(
    modelo=Encontrista,
    tipo_detalhamento=TipoDetalhamento.INSCRICAO_ENCONTRISTA,
    escopo_regra_grupo=EscopoRegraGrupo.EXTRACAO_ENCONTRISTA,
    label="ENCONTRISTA",
    repository=EncontristaRepository,
    parser=encontrista_parser,
    sequence_name="encontristas_id_seq",
    error_code_importacao="ERRO_PROCESSAMENTO_ENCONTRISTA",
)
