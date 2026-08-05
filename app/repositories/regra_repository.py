from sqlalchemy.orm import Session, selectinload

from app.models.regra import Regra
from app.models.regra_condicao import RegraCondicao
from app.models.regra_grupo import RegraGrupo
from app.utils.sort_utils import apply_sort

SORT_FIELDS = {
    "nome": RegraGrupo.nome,
    "escopo": RegraGrupo.escopo,
    "ordem": RegraGrupo.ordem,
}

DEFAULT_SORT = "ordem:asc"

_EAGER = selectinload(RegraGrupo.regras).selectinload(Regra.condicoes)


def _apply_filters(query, params):
    if params.escopo:
        query = query.filter(RegraGrupo.escopo == params.escopo)

    if params.ativo is not None:
        query = query.filter(RegraGrupo.ativo.is_(params.ativo))

    if params.nome:
        query = query.filter(RegraGrupo.nome.ilike(f"%{params.nome}%"))

    return query


def _montar_regra(data: dict) -> Regra:
    data = dict(data)
    condicoes_data = data.pop("condicoes", [])
    regra = Regra(**data)
    regra.condicoes = [RegraCondicao(**c) for c in condicoes_data]
    return regra


class RegraRepository:

    @staticmethod
    def list_ativos_por_escopos(db: Session, escopos: list):
        """Carrega os RegraGrupo ativos para os escopos informados, já com
        Regra e RegraCondicao carregados (sem N+1), ordenados por
        RegraGrupo.ordem e, dentro do grupo, por Regra.ordem/RegraCondicao.ordem
        (ordem definida nos relationships dos modelos)."""
        return (
            db.query(RegraGrupo)
            .options(_EAGER)
            .filter(RegraGrupo.escopo.in_(escopos), RegraGrupo.ativo.is_(True))
            .order_by(RegraGrupo.ordem)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, grupo_id: int):
        return (
            db.query(RegraGrupo)
            .options(_EAGER)
            .filter(RegraGrupo.id == grupo_id)
            .first()
        )

    @staticmethod
    def list_all(db: Session, params):
        query = db.query(RegraGrupo).options(_EAGER)
        query = _apply_filters(query, params)
        query = apply_sort(query, RegraGrupo, params.sort, SORT_FIELDS, DEFAULT_SORT)
        return query.offset(params.skip).limit(params.limit).all()

    @staticmethod
    def list_with_count(db: Session, params):
        query = db.query(RegraGrupo).options(_EAGER)
        query = _apply_filters(query, params)
        query = apply_sort(query, RegraGrupo, params.sort, SORT_FIELDS, DEFAULT_SORT)
        total = query.count()
        items = query.offset(params.skip).limit(params.limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: dict) -> RegraGrupo:
        data = dict(data)
        regras_data = data.pop("regras", [])
        grupo = RegraGrupo(**data)
        grupo.regras = [_montar_regra(r) for r in regras_data]
        db.add(grupo)
        db.commit()
        db.refresh(grupo)
        return grupo

    @staticmethod
    def update(db: Session, obj: RegraGrupo, data: dict) -> RegraGrupo:
        data = dict(data)
        regras_data = data.pop("regras", None)

        for key, value in data.items():
            setattr(obj, key, value)

        if regras_data is not None:
            # Substitui a lista inteira — cascade="all, delete-orphan" no
            # relationship cuida de apagar as Regra/RegraCondicao removidas.
            obj.regras = [_montar_regra(r) for r in regras_data]

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, obj: RegraGrupo):
        db.delete(obj)
        db.commit()
