from sqlalchemy.orm import Session
from app.repositories.detalhamento_repository import DetalhamentoRepository
from app.core.exceptions import NotFoundException
from app.models.enums import TipoDetalhamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository

_ROTULO_POR_TIPO = {
    TipoDetalhamento.OFERTA: "OFERTA",
    TipoDetalhamento.OUTRO: "OUTRO",
}


class DetalhamentoService:

    @staticmethod
    def _enriquecer(db: Session, detalhamento):
        if detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO:
            pessoa = EncontreiroRepository.get_by_id(db, detalhamento.referencia_id)
            detalhamento.detalhe_nome = pessoa.nome if pessoa else "(encontreiro removido)"
            detalhamento.observacao_efetiva = (pessoa.observacao or "") if pessoa else ""

        elif detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA:
            pessoa = EncontristaRepository.get_by_id(db, detalhamento.referencia_id)
            detalhamento.detalhe_nome = pessoa.nome if pessoa else "(encontrista removido)"
            detalhamento.observacao_efetiva = (pessoa.observacao or "") if pessoa else ""

        else:
            detalhamento.detalhe_nome = _ROTULO_POR_TIPO.get(detalhamento.tipo, detalhamento.tipo.value)
            detalhamento.observacao_efetiva = detalhamento.descricao or ""

        return detalhamento

    @staticmethod
    def list_all(db: Session, params):
        items = DetalhamentoRepository.list_all(db, params)
        return [DetalhamentoService._enriquecer(db, item) for item in items]

    @staticmethod
    def list(db: Session, params):
        items, total = DetalhamentoRepository.list_with_count(db, params)
        items = [DetalhamentoService._enriquecer(db, item) for item in items]

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def create(db: Session, data: dict):
        obj = DetalhamentoRepository.create(db, data)
        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def update(db: Session, detalhamento_id: int, data: dict):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        obj = DetalhamentoRepository.update(db, obj, data)
        return DetalhamentoService._enriquecer(db, obj)

    @staticmethod
    def delete(db: Session, detalhamento_id: int):
        obj = DetalhamentoRepository.get_by_id(db, detalhamento_id)

        if not obj:
            raise NotFoundException("Detalhamento")

        DetalhamentoRepository.delete(db, obj)
