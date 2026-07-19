from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth_schema import LoginRequest, TokenResponse, UsuarioResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, data.email, data.senha)


@router.get("/me", response_model=UsuarioResponse)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user
