from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario

DEFAULT_USUARIOS = [
    {
        "nome":   "Administrador",
        "email":  "admin@encontro.com",
        "senha":  "admin123",
        "perfil": PerfilUsuario.ADMINISTRADOR,
    },
    {
        "nome":   "Anderson Dourado",
        "email":  "anderson.ictus@gmail.com",
        "senha":  "andyneo84",
        "perfil": PerfilUsuario.ADMINISTRADOR,
    },
]


def seed_usuarios(db: Session):
    try:
        alterado = False

        for item in DEFAULT_USUARIOS:
            existente = db.query(Usuario).filter(Usuario.email == item["email"]).first()
            if existente:
                if existente.perfil != item["perfil"]:
                    existente.perfil = item["perfil"]
                    alterado = True
                continue

            db.add(Usuario(
                nome=item["nome"],
                email=item["email"],
                senha_hash=hash_password(item["senha"]),
                ativo=True,
                perfil=item["perfil"],
            ))
            alterado = True

        if alterado:
            db.commit()

    except Exception:
        db.rollback()
        raise
