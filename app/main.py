import logging
from contextlib import asynccontextmanager

from alembic.config import Config
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from alembic import command
from app.core.config import APP_PORT, APP_VERSION, CORS_ORIGINS
from app.core.deps import get_current_user
from app.database.seeds.main_seeds import run_seed
from app.database.session import SessionLocal
from app.routers.auth_router import router as auth_router
from app.routers.circulo_router import router as circulo_router
from app.routers.conciliacao_router import router as conciliacao_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.detalhamento_router import router as detalhamento_router
from app.routers.encontreiro_router import router as encontreiro_router
from app.routers.encontrista_router import router as encontrista_router
from app.routers.equipe_router import router as equipe_router
from app.routers.finalidade_router import router as finalidade_router
from app.routers.lancamento_router import router as lancamento_router
from app.routers.regra_router import router as regra_router
from app.routers.relatorio_router import router as relatorio_router
from app.routers.relatorio_secretaria_router import (
    router as relatorio_secretaria_router,
)
from app.routers.upload_file_router import router as upload_file_router
from app.routers.usuario_router import router as usuario_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("=== CONFIG ===")
    logger.info("APP_PORT     : %s", APP_PORT)
    logger.info("APP_VERSION  : %s", APP_VERSION)
    logger.info("CORS_ORIGINS : %s", CORS_ORIGINS)

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except OperationalError as exc:
        logger.exception(
            "ERRO - NÃO FOI POSSÍVEL ESTABELECER CONEXÃO COM O BANCO DE DADOS!"
        )
        raise RuntimeError(
            "ERRO - NÃO FOI POSSÍVEL ESTABELECER CONEXÃO COM O BANCO DE DADOS!"
        ) from exc

    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()

    except OperationalError as exc:
        logger.exception(
            "ERRO - NÃO FOI POSSÍVEL ESTABELECER CONEXÃO COM O BANCO DE DADOS!"
        )
        raise RuntimeError(
            "ERRO - NÃO FOI POSSÍVEL ESTABELECER CONEXÃO COM O BANCO DE DADOS!"
        ) from exc

    logger.info("=======================================")
    logger.info("== Sistema Financeiro Encontro iniciado com sucesso! ==")
    yield


app = FastAPI(
    title="Financeiro Encontro",
    description="Sistema financeiro para gerenciamento do encontro",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# rotas públicas
app.include_router(auth_router)

# rotas protegidas
_protected = {"dependencies": [Depends(get_current_user)]}
app.include_router(lancamento_router, **_protected)
app.include_router(finalidade_router, **_protected)
app.include_router(upload_file_router, **_protected)
app.include_router(conciliacao_router, **_protected)
app.include_router(dashboard_router, **_protected)
app.include_router(relatorio_router, **_protected)
app.include_router(relatorio_secretaria_router, **_protected)
app.include_router(usuario_router, **_protected)
app.include_router(equipe_router, **_protected)
app.include_router(circulo_router, **_protected)
app.include_router(encontreiro_router, **_protected)
app.include_router(encontrista_router, **_protected)
app.include_router(detalhamento_router, **_protected)
app.include_router(regra_router, **_protected)


@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        "HTTPException: %s %s -> %s %s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Erro de validação: %s %s -> %s", request.method, request.url.path, exc.errors()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"},
    )
