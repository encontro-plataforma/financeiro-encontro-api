from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.enums import SituacaoCamisa
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.equipe_repository import EquipeRepository
from app.services.common.pessoa_service_base import PessoaImportavelServiceBase
from app.services.common.tipo_pessoa_config import TIPO_PESSOA_ENCONTREIRO
from app.utils.parse_utils import normalizar_cabecalho, parse_date_br, parse_decimal_br


def _parse_situacao(valor, default=None):
    if not valor:
        return default

    normalizado = normalizar_cabecalho(valor).replace("_", " ")
    for situacao in SituacaoCamisa:
        if situacao.value.replace("_", " ") == normalizado:
            return situacao

    raise ValueError(f"situação de camisa inválida: '{valor}'")


class EncontreiroService(PessoaImportavelServiceBase):
    CONFIG = TIPO_PESSOA_ENCONTREIRO

    @classmethod
    def alterar_equipe(cls, db: Session, encontreiro_id: int, equipe_id: int):
        obj = EncontreiroRepository.get_by_id(db, encontreiro_id)

        if not obj:
            raise NotFoundException("Encontreiro")

        equipe = EquipeRepository.get_by_id(db, equipe_id)
        if not equipe:
            raise NotFoundException("Equipe")

        return EncontreiroRepository.update(db, obj, {"equipe_id": equipe_id})

    @classmethod
    def _linha_para_dados(cls, db: Session, row, is_new: bool) -> dict:
        # Equipe "N/A" (ou em branco) não é mais motivo para ignorar a linha:
        # a ficha segue participando da inclusão/atualização normalmente,
        # apenas sem equipe resolvida.
        equipe_id = None
        if row.equipe_nome:
            equipe = EquipeRepository.get_by_nome(db, row.equipe_nome)
            if not equipe:
                raise ValueError(f"equipe '{row.equipe_nome}' não encontrada")
            equipe_id = equipe.id

        situacao_default = SituacaoCamisa.SEM_BLUSA if is_new else None

        return {
            # Coluna "DT INSC" vem exportada no formato dos EUA (mm/dd/aaaa HH:MM:SS),
            # diferente das demais datas do CSV (dd/mm/aaaa).
            "dt_inscricao": parse_date_br(row.dt_inscricao, "%m/%d/%Y %H:%M:%S"),
            "nome": row.nome,
            "apelido": row.apelido,
            "instagram": row.instagram,
            "telefone": row.telefone,
            "estado_civil": row.estado_civil,
            "igreja": row.igreja,
            "religiao": row.religiao,
            "contato_emerg": row.contato_emerg,
            "nome_emerg": row.nome_emerg,
            "parentesco_emerg": row.parentesco_emerg,
            "alergia_comorbidade": row.alergia_comorbidade,
            "equipe_id": equipe_id,
            "camisa": row.camisa,
            "situacao_camisa": _parse_situacao(
                row.situacao_camisa, default=situacao_default
            ),
            "veiculo": row.veiculo,
            "dt_pagamento": parse_date_br(row.dt_pagamento),
            "nome_pagador": row.nome_pagador,
            "pagamento": parse_decimal_br(row.pagamento),
            "observacao": row.observacao,
        }

    @classmethod
    def _detectar_duplicata(cls, db: Session, dados: dict):
        return EncontreiroRepository.get_by_nome_telefone(db, dados["nome"], dados["telefone"])

    @classmethod
    def _item_ignorado(cls, row, duplicado) -> dict:
        return {
            "linha": row.linha,
            "id_csv": row.id,
            "encontreiro_existente_id": duplicado.id,
        }

    @classmethod
    def _montar_resultado(cls, inseridos: int, atualizados: int, ignorados: list[dict]) -> dict:
        return {
            "inseridos": inseridos,
            "atualizados": atualizados,
            "ignorados": len(ignorados),
            "detalhes_ignorados": ignorados,
            "mensagem": (
                f"Processamento concluído. {inseridos} inseridos, "
                f"{atualizados} atualizados, {len(ignorados)} ignorados."
            ),
        }
