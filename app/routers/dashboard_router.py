from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.dashboard_filter_dto import DashboardFilterDto
from app.schemas.dashboard_schema import PorDiaItem, PorFinalidadeItem, PorMesItem, TotaisResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/totais", response_model=TotaisResponse)
def totais(params: DashboardFilterDto = Depends(), db: Session = Depends(get_db)):
    return DashboardService.get_totais(db, params)


@router.get("/por-dia", response_model=List[PorDiaItem])
def por_dia(params: DashboardFilterDto = Depends(), db: Session = Depends(get_db)):
    return DashboardService.get_por_dia(db, params)


@router.get("/por-mes", response_model=List[PorMesItem])
def por_mes(params: DashboardFilterDto = Depends(), db: Session = Depends(get_db)):
    return DashboardService.get_por_mes(db, params)


@router.get("/por-finalidade", response_model=List[PorFinalidadeItem])
def por_finalidade(params: DashboardFilterDto = Depends(), db: Session = Depends(get_db)):
    return DashboardService.get_por_finalidade(db, params)
