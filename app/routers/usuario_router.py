from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.pagination_schema import Page
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.schemas.usuario_filter_dto import UsuarioFilterDto
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("/", response_model=Page[UsuarioResponse])
def list_usuarios(
    params: UsuarioFilterDto = Depends(),
    db: Session = Depends(get_db),
):
    return UsuarioService.list(db, params)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return UsuarioService.get_by_id(db, usuario_id)


@router.post("/", response_model=UsuarioResponse, status_code=201)
def create_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    return UsuarioService.create(db, data)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db)):
    return UsuarioService.update(db, usuario_id, data)


@router.delete("/{usuario_id}", status_code=204)
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    UsuarioService.delete(db, usuario_id, current_user)
