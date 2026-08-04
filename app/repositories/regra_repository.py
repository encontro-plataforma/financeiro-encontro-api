from sqlalchemy.orm import Session, selectinload

from app.models.regra import Regra
from app.models.regra_grupo import RegraGrupo


class RegraRepository:

    @staticmethod
    def list_ativos_por_escopos(db: Session, escopos: list):
        """Carrega os RegraGrupo ativos para os escopos informados, já com
        Regra e RegraCondicao carregados (sem N+1), ordenados por
        RegraGrupo.ordem e, dentro do grupo, por Regra.ordem/RegraCondicao.ordem
        (ordem definida nos relationships dos modelos)."""
        return (
            db.query(RegraGrupo)
            .options(selectinload(RegraGrupo.regras).selectinload(Regra.condicoes))
            .filter(RegraGrupo.escopo.in_(escopos), RegraGrupo.ativo.is_(True))
            .order_by(RegraGrupo.ordem)
            .all()
        )
