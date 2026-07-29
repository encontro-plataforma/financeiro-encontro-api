from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.lancamento_repository import LancamentoRepository
from app.schemas.lancamento_schema import DetalhamentoFinalDto, LancamentoCreate, LancamentoUpdate
from app.models.enums import StatusLancamento, TipoDetalhamento, TipoLancamento
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.detalhamento import Detalhamento
from app.models.lancamento import Lancamento
from app.utils.hash_utils import gerar_hash

_TOLERANCIA = Decimal("0.01")
_TIPOS_INSCRICAO = (TipoDetalhamento.INSCRICAO_ENCONTREIRO, TipoDetalhamento.INSCRICAO_ENCONTRISTA)


class LancamentoService:

    @staticmethod
    def create(db: Session, data: LancamentoCreate | dict):
        payload = data.model_dump() if hasattr(data, "model_dump") else dict(data)

        if not payload.get("hash_transacao"):
            payload["hash_transacao"] = gerar_hash(
                payload["descricao"],
                payload["valor"],
                payload["data_pagamento"],
                payload.get("observacao") or "",
            )

        if LancamentoService.exists_by_hash(db, payload["hash_transacao"]):
            raise BadRequestException(f"Lançamento já existe (descricao: {payload['descricao']}, valor: {payload['valor']}, data_pagamento: {payload['data_pagamento']})")

        payload["status"] = StatusLancamento.NAO_CONCILIADO
        return LancamentoRepository.create(db, payload)

    @staticmethod
    def update(db: Session, lancamento_id: int, data: LancamentoUpdate):
        obj = LancamentoRepository.get_by_id(db, lancamento_id)

        if not obj:
            raise NotFoundException("Lançamento")

        updated = data.model_dump(exclude_unset=True, exclude_none=True)
        return LancamentoRepository.update(db, obj, updated)

    @staticmethod
    def delete(db: Session, lancamento_id: int):
        obj = LancamentoRepository.get_by_id(db, lancamento_id)

        if not obj:
            raise NotFoundException("Lançamento")

        LancamentoRepository.delete(db, obj)

    @staticmethod
    def list_all(db: Session, params):
        return LancamentoRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = LancamentoRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, lancamento_id: int):
        obj = LancamentoRepository.get_by_id(db, lancamento_id)

        if not obj:
            raise NotFoundException("Lançamento")

        return obj

    @staticmethod
    def exists_by_hash(db: Session, hash_value: str) -> bool:
        return (
            db.query(Lancamento)
            .filter(Lancamento.hash_transacao == hash_value)
            .first() is not None
        )

    @staticmethod
    def conciliar(
        db: Session,
        lancamento_id: int,
        finalidade_id: int,
        observacao: str | None = None,
        detalhamento_final: DetalhamentoFinalDto | None = None,
    ):
        from app.services.finalidade_service import FinalidadeService
        try:
            obj = LancamentoRepository.get_by_id(db, lancamento_id)
            if not obj:
                raise NotFoundException("Lançamento")

            finalidade = FinalidadeService.get_by_id(db, finalidade_id)

            if obj.tipo == TipoLancamento.RECEITA:
                detalhamentos = (
                    db.query(Detalhamento)
                    .filter(Detalhamento.lancamento_id == lancamento_id)
                    .all()
                )
                soma = sum((d.valor for d in detalhamentos), Decimal("0"))
                valor = Decimal(str(obj.valor))
                resto = valor - soma

                if resto < -_TOLERANCIA:
                    raise BadRequestException(
                        "A soma dos detalhamentos é maior que o valor do lançamento. "
                        "Revise antes de conciliar."
                    )

                if finalidade.nome == "INSCRIÇÃO" and not any(d.tipo in _TIPOS_INSCRICAO for d in detalhamentos):
                    raise BadRequestException(
                        "Esta finalidade exige que ao menos uma inscrição seja vinculada "
                        "antes de conciliar este lançamento."
                    )

                if resto > _TOLERANCIA and detalhamento_final:
                    tipo_resto = TipoDetalhamento.OFERTA if finalidade.nome == "OFERTA" else TipoDetalhamento.OUTRO
                    db.add(Detalhamento(
                        lancamento_id=lancamento_id,
                        tipo=tipo_resto,
                        referencia_id=None,
                        valor=resto,
                        descricao=detalhamento_final.descricao,
                    ))

            obj.finalidade_id = finalidade_id
            obj.status = StatusLancamento.CONCILIADO
            if observacao is not None:
                obj.observacao = observacao
            db.commit()
            db.refresh(obj)
            return obj
        except (NotFoundException, BadRequestException):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise BadRequestException(detail=f"Erro ao conciliar lançamento: {str(e)}")
