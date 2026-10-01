from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.circulo import Circulo

DEFAULT_CIRCULOS = [
    {"id": 1, "nome": "AMARELO",   "rgb": "#ffff00", "cancelado": False},
    {"id": 2, "nome": "AZUL",      "rgb": "#0000ff", "cancelado": False},
    {"id": 3, "nome": "LARANJA",   "rgb": "#ff9900", "cancelado": False},
    {"id": 4, "nome": "ROXO",      "rgb": "#b4a7d6", "cancelado": False},
    {"id": 5, "nome": "VERDE",     "rgb": "#274e13", "cancelado": False},
    {"id": 6, "nome": "VERMELHO",  "rgb": "#980000", "cancelado": False},
    # Círculo sentinela: Encontrista com este círculo é considerado cancelado
    # e já auditado, com ou sem Detalhamento vinculado (ver Encontrista.auditado
    # em app/models/detalhamento.py).
    {"id": 7, "nome": "CANCELADO", "rgb": "#9e9e9e", "cancelado": True},
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
                    cancelado=item["cancelado"],
                ))
                alterado = True
                continue

            # Corrige registros antigos cujo rgb ainda não seja um hex válido
            # (versões anteriores do seed usavam nomes soltos do Google Sheets).
            if not existente.rgb or not existente.rgb.startswith("#"):
                existente.rgb = item["rgb"]
                alterado = True

            # Backfill do flag `cancelado` pra quem já existia antes dele
            # existir (hoje só o círculo "CANCELADO" nasce com True).
            if existente.cancelado != item["cancelado"]:
                existente.cancelado = item["cancelado"]
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
