from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.circulo import Circulo

DEFAULT_CIRCULOS = [
    {"id": 1, "nome": "AMARELO",  "rgb": "yellow"},
    {"id": 2, "nome": "AZUL",     "rgb": "blue"},
    {"id": 3, "nome": "LARANJA",  "rgb": "orange"},
    {"id": 4, "nome": "ROXO",     "rgb": "light purple 1"},
    {"id": 5, "nome": "VERDE",    "rgb": "dark green 2"},
    {"id": 6, "nome": "VERMELHO", "rgb": "red berry"},
]


def seed_circulos(db: Session):
    try:
        inserted = False

        for item in DEFAULT_CIRCULOS:
            existente = (
                db.query(Circulo)
                .filter(Circulo.id == item["id"])
                .first()
            )

            if not existente:
                db.add(Circulo(
                    id=item["id"],
                    nome=item["nome"],
                    rgb=item["rgb"],
                ))
                inserted = True

        if inserted:
            db.commit()
            reset_sequence(db)
        else:
            db.rollback()

    except Exception:
        db.rollback()
        raise


def reset_sequence(db: Session):
    db.execute(text("""
        SELECT setval('circulos_id_seq', (SELECT MAX(id) FROM circulos));
    """))
    db.commit()
