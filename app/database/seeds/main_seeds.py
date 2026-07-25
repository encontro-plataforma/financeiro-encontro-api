from sqlalchemy.orm import Session

from app.database.seeds.seed_circulo import seed_circulos
from app.database.seeds.seed_equipe import seed_equipes
from app.database.seeds.seed_finalidade import seed_finalidades
from app.database.seeds.seed_usuario import seed_usuarios


def run_seed(db: Session):
    seed_finalidades(db)
    seed_usuarios(db)
    seed_equipes(db)
    seed_circulos(db)
