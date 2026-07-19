from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import FormaPagamento
from app.schemas.lancamento_filter_dto import LancamentoFilterDto
from app.schemas.lancamento_schema import (
    LancamentoConciliarRequest,
    LancamentoCreate,
    LancamentoResponse,
    LancamentoUpdate,
)
from app.schemas.pagination_schema import Page
from app.services.lancamento_service import LancamentoService

router = APIRouter(prefix="/lancamentos", tags=["Lançamentos"])


@router.post("/", response_model=LancamentoResponse)
def create(data: LancamentoCreate, db: Session = Depends(get_db)):
    return LancamentoService.create(db, data)


@router.get("/", response_model=Page[LancamentoResponse])
def list_lancamentos(
    params: LancamentoFilterDto = Depends(),
    finalidade_ids: Optional[List[int]] = Query(default=None),
    forma_pagamento: Optional[List[FormaPagamento]] = Query(default=None),
    exclude_ids: Optional[List[int]] = Query(default=None),
    db: Session = Depends(get_db),
):
    params.exclude_ids = exclude_ids
    params.finalidade_ids = finalidade_ids
    params.forma_pagamento = forma_pagamento
    return LancamentoService.list(db, params)


@router.get("/all", response_model=List[LancamentoResponse])
def list_all(
    params: LancamentoFilterDto = Depends(),
    finalidade_ids: Optional[List[int]] = Query(default=None),
    forma_pagamento: Optional[List[FormaPagamento]] = Query(default=None),
    db: Session = Depends(get_db),
):
    params.finalidade_ids = finalidade_ids
    params.forma_pagamento = forma_pagamento
    return LancamentoService.list_all(db, params)


@router.get("/{lancamento_id}", response_model=LancamentoResponse)
def get_by_id(lancamento_id: int, db: Session = Depends(get_db)):
    return LancamentoService.get_by_id(db, lancamento_id)


@router.put("/{lancamento_id}", response_model=LancamentoResponse)
def update(
    lancamento_id: int,
    data: LancamentoUpdate,
    db: Session = Depends(get_db),
):
    return LancamentoService.update(db, lancamento_id, data)


@router.delete("/{lancamento_id}")
def delete(lancamento_id: int, db: Session = Depends(get_db)):
    LancamentoService.delete(db, lancamento_id)
    return {"message": "Lançamento removido com sucesso"}


@router.patch(
    "/conciliar/{lancamento_id}/finalidade/{finalidade_id}",
    response_model=LancamentoResponse,
)
def conciliar_lancamento(
    lancamento_id: int,
    finalidade_id: int,
    data: Optional[LancamentoConciliarRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    observacao = data.observacao if data else None
    return LancamentoService.conciliar(db, lancamento_id, finalidade_id, observacao)
