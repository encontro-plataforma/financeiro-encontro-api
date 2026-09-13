import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories.circulo_repository import CirculoRepository
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository
from app.services.common.pessoa_service_base import PessoaImportavelServiceBase
from app.services.common.tipo_pessoa_config import TIPO_PESSOA_ENCONTRISTA
from app.utils.parse_utils import parse_bool, parse_date_br, parse_decimal_br

logger = logging.getLogger("uvicorn.error")


def _parse_bool_campo(valor, is_new: bool):
    if valor is None:
        return False if is_new else None
    return parse_bool(valor)


def _parse_idade(valor):
    if not valor:
        return None
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"idade inválida: '{valor}'") from exc


class EncontristaService(PessoaImportavelServiceBase):
    CONFIG = TIPO_PESSOA_ENCONTRISTA

    @classmethod
    def alterar_circulo(cls, db: Session, encontrista_id: int, circulo_id: int):
        obj = EncontristaRepository.get_by_id(db, encontrista_id)

        if not obj:
            raise NotFoundException("Encontrista")

        # 0 é o sentinela de "Sem Círculo" (mesma convenção do filtro de
        # círculo da listagem) -- não corresponde a um Circulo real.
        if circulo_id == 0:
            return EncontristaRepository.update(db, obj, {"circulo_id": None})

        circulo = CirculoRepository.get_by_id(db, circulo_id)

        if not circulo:
            raise NotFoundException("Círculo")

        return EncontristaRepository.update(db, obj, {"circulo_id": circulo_id})

    @classmethod
    def padrinhos_disponiveis(cls, db: Session):
        return EncontristaRepository.get_padrinhos_disponiveis(db)

    @classmethod
    def _linha_para_dados(cls, db: Session, row, is_new: bool) -> dict:
        padrinho = EncontreiroRepository.get_by_id(db, row.padrinho_id)
        if not padrinho:
            raise ValueError(
                f"padrinho (Encontreiro id={row.padrinho_id}) não encontrado"
            )

        circulo_id = None
        if row.circulo_nome:
            circulo = CirculoRepository.get_by_nome(db, row.circulo_nome)
            if circulo:
                circulo_id = circulo.id
            else:
                logger.warning(
                    "Linha %s: círculo '%s' não encontrado, ficará em branco",
                    row.linha,
                    row.circulo_nome,
                )

        return {
            "dt_entrega": parse_date_br(row.dt_entrega),
            "dt_validade": parse_date_br(row.dt_validade),
            "padrinho_id": padrinho.id,
            "carta": _parse_bool_campo(row.carta, is_new),
            "album": _parse_bool_campo(row.album, is_new),
            "nome": row.nome,
            "apelido": row.apelido,
            "dt_nascimento": parse_date_br(row.dt_nascimento),
            "idade": _parse_idade(row.idade),
            "circulo_id": circulo_id,
            "onde_veio_ficha": row.onde_veio_ficha or "",
            "instagram": row.instagram,
            "contato": row.contato,
            "religiao": row.religiao,
            "igreja": row.igreja,
            "endereco": row.endereco,
            "cidade": row.cidade,
            "camisa": row.camisa,
            "blusa": _parse_bool_campo(row.blusa, is_new),
            "veiculo": row.veiculo,
            "contato_emerg": row.contato_emerg,
            "nome_emerg": row.nome_emerg,
            "parentesco_emerg": row.parentesco_emerg,
            "medicacao": row.medicacao,
            "alergia_comorbidade": row.alergia_comorbidade,
            "dt_pagamento": parse_date_br(row.dt_pagamento),
            "nome_pagador": row.nome_pagador,
            "pagamento": parse_decimal_br(row.pagamento),
            "observacao": row.observacao,
        }
