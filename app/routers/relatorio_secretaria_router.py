from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.relatorio_secretaria_service import RelatorioSecretariaService

router = APIRouter(prefix="/relatorios-secretaria", tags=["Relatórios Secretaria"])


@router.get("/encontristas-por-circulo")
def encontristas_por_circulo(db: Session = Depends(get_db)):
    pdf = RelatorioSecretariaService.gerar_encontristas_por_circulo(db)
    nome = f"encontristas-por-circulo-{date.today()}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get("/comorbidades")
def comorbidades(db: Session = Depends(get_db)):
    pdf = RelatorioSecretariaService.gerar_comorbidades(db)
    nome = f"comorbidades-{date.today()}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
