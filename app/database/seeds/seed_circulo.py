from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.circulo import Circulo

DEFAULT_CIRCULOS = [
    {"id": 1, "nome": "AMARELO",  "rgb": "#ffff00"},
    {"id": 2, "nome": "AZUL",     "rgb": "#0000ff"},
    {"id": 3, "nome": "LARANJA",  "rgb": "#ff9900"},
    {"id": 4, "nome": "ROXO",     "rgb": "#b4a7d6"},
    {"id": 5, "nome": "VERDE",    "rgb": "#274e13"},
    {"id": 6, "nome": "VERMELHO", "rgb": "#980000"},
]


def seed_circulos(db: Session):
    try:
        alterado = False

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
                alterado = True
                continue

            # Corrige registros antigos cujo rgb ainda não seja um hex válido
            # (versões anteriores do seed usavam nomes soltos do Google Sheets).
            if not existente.rgb or not existente.rgb.startswith("#"):
                existente.rgb = item["rgb"]
                alterado = True

        if alterado:
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
