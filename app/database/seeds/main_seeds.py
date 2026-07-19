from sqlalchemy.orm import Session

from app.database.seeds.seed_finalidade import seed_finalidades
from app.database.seeds.seed_usuario import seed_usuarios


def run_seed(db: Session):
    seed_finalidades(db)
    seed_usuarios(db)
