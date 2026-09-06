from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.integracao.regras.dtos import PendenciaAuditoria
from app.integracao.regras.motor_extracao import diagnosticar_detalhamentos
from app.integracao.regras.motor_match import (
    _forma_pagamento_mencionada,
    _parcelas_mencionadas,
)
from app.models.enums import FormaPagamento
from app.repositories.regra_repository import RegraRepository
from app.utils.parse_utils import remover_acentos


class RegraService:
    @staticmethod
    def list_all(db: Session, params):
        return RegraRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = RegraRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit,
        }

    @staticmethod
    def get_by_id(db: Session, grupo_id: int):
        obj = RegraRepository.get_by_id(db, grupo_id)

        if not obj:
            raise NotFoundException("Grupo de Regras")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return RegraRepository.create(db, data)

    @staticmethod
    def update(db: Session, grupo_id: int, data: dict):
        obj = RegraRepository.get_by_id(db, grupo_id)

        if not obj:
            raise NotFoundException("Grupo de Regras")

        return RegraRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, grupo_id: int):
        obj = RegraRepository.get_by_id(db, grupo_id)

        if not obj:
            raise NotFoundException("Grupo de Regras")

        RegraRepository.delete(db, obj)

    @staticmethod
    def testar_observacao(db: Session, grupo_id: int, observacao: str, nome: str):
        grupo = RegraService.get_by_id(db, grupo_id)
        pendencia = PendenciaAuditoria(
            id=0,
            nome=nome,
            nome_pagador=None,
            dt_pagamento=datetime.now(timezone.utc).date(),
            pagamento=Decimal(0),
            observacao=observacao,
        )
        obs_normalizada = remover_acentos(observacao).lower()
        diagnosticos = diagnosticar_detalhamentos(pendencia, [grupo])
        forma_enum = _forma_pagamento_mencionada(obs_normalizada)
        forma = forma_enum.value
        total_gerado = sum(
            (item.valor for _, itens in diagnosticos for item in itens),
            Decimal(0),
        )
        # Número de parcelas só faz sentido para cartão de crédito -- para
        # as demais formas (pix, dinheiro, cartão de débito) é sempre 1,
        # mesmo que a observação mencione "parcelas" por engano.
        numero_parcelas = Decimal(
            _parcelas_mencionadas(obs_normalizada)
            if forma_enum == FormaPagamento.CARTAO_CREDITO
            else 1
        )
        return {
            "modelo_extracao": grupo.nome,
            "total_gerado": total_gerado,
            "numero_parcelas": numero_parcelas,
            "regras": [
                {
                    "nome": regra.nome,
                    "forma_pagamento": forma,
                    "detalhamentos": [
                        {
                            "tipo": item.tipo,
                            "valor": item.valor,
                            "referencia_id": item.referencia_id,
                        }
                        for item in itens
                    ],
                }
                for regra, itens in diagnosticos
                if itens
            ],
        }
