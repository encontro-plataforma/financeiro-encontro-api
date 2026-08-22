from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.equipe import Equipe
from app.models.enums import AcessoEquipe

DEFAULT_EQUIPES = [
    # ── EDG ──────────────────────────────────────────────────────────────────
    {"id": 1,  "nome": "EDG",                       "acesso": AcessoEquipe.EDG},
    # ── VERDE ────────────────────────────────────────────────────────────────
    {"id": 2,  "nome": "BOA VONTADE",               "acesso": AcessoEquipe.VERDE},
    {"id": 3,  "nome": "CASAL PASTA",               "acesso": AcessoEquipe.VERDE},
    {"id": 4,  "nome": "CIRCULOS",                  "acesso": AcessoEquipe.VERDE},
    {"id": 5,  "nome": "RECEPÇÃO AOS PALESTRANTES", "acesso": AcessoEquipe.VERDE},
    {"id": 6,  "nome": "SECRETARIA",                "acesso": AcessoEquipe.VERDE},
    {"id": 7,  "nome": "SOM & ILUMINAÇÃO",          "acesso": AcessoEquipe.VERDE},
    # ── AMARELO ──────────────────────────────────────────────────────────────
    {"id": 8,  "nome": "BANDINHA",                  "acesso": AcessoEquipe.AMARELO},
    {"id": 9,  "nome": "CAFEZINHO",                 "acesso": AcessoEquipe.AMARELO},
    {"id": 10, "nome": "SAÚDE",                     "acesso": AcessoEquipe.AMARELO},
    {"id": 11, "nome": "CORREIOS",                  "acesso": AcessoEquipe.AMARELO},
    {"id": 12, "nome": "GARÇONS",                   "acesso": AcessoEquipe.AMARELO},
    {"id": 13, "nome": "LIVRARIA",                  "acesso": AcessoEquipe.AMARELO},
    {"id": 14, "nome": "MÍDIAS & COMUNICAÇÃO",      "acesso": AcessoEquipe.AMARELO},
    {"id": 15, "nome": "PERSONALIZADOS",            "acesso": AcessoEquipe.AMARELO},
    {"id": 16, "nome": "TEATRO",                    "acesso": AcessoEquipe.AMARELO},
    {"id": 17, "nome": "TRÂNSITO",                  "acesso": AcessoEquipe.AMARELO},
    # ── VERMELHO ─────────────────────────────────────────────────────────────
    {"id": 18, "nome": "CERIMONIAL",                "acesso": AcessoEquipe.VERMELHO},
    {"id": 19, "nome": "COMPRAS",                   "acesso": AcessoEquipe.VERMELHO},
    {"id": 20, "nome": "COZINHA",                   "acesso": AcessoEquipe.VERMELHO},
    {"id": 21, "nome": "LANCHONETE",                "acesso": AcessoEquipe.VERMELHO},
    {"id": 22, "nome": "MINI MERCADO",              "acesso": AcessoEquipe.VERMELHO},
    {"id": 23, "nome": "ORAÇÃO",                    "acesso": AcessoEquipe.VERMELHO},
    {"id": 24, "nome": "ORDEM",                     "acesso": AcessoEquipe.VERMELHO},
    {"id": 25, "nome": "PATRIMÔNIO",                "acesso": AcessoEquipe.VERMELHO},
    {"id": 26, "nome": "VISITAÇÃO E EXTERNA",       "acesso": AcessoEquipe.VERMELHO},
    {"id": 27, "nome": "N/A",                       "acesso": AcessoEquipe.NA},
]


def seed_equipes(db: Session):
    try:
        inserted = False

        for item in DEFAULT_EQUIPES:
            existente = (
                db.query(Equipe)
                .filter(Equipe.id == item["id"])
                .first()
            )

            if not existente:
                db.add(Equipe(
                    id=item["id"],
                    nome=item["nome"],
                    acesso=item["acesso"],
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
        SELECT setval('equipes_id_seq', (SELECT MAX(id) FROM equipes));
    """))
    db.commit()
