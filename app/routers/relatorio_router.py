from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.relatorio_service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/livro-caixa")
def livro_caixa(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    db: Session = Depends(get_db),
):
    pdf = RelatorioService.gerar_livro_caixa(db, data_inicio, data_fim)
    nome = f"livro-caixa-{data_inicio}-{data_fim}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get("/resumo-geral")
def resumo_geral(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    db: Session = Depends(get_db),
):
    pdf = RelatorioService.gerar_resumo_geral(db, data_inicio, data_fim)
    nome = f"resumo-geral-{data_inicio}-{data_fim}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
