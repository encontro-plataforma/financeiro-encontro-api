from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import ClassVar

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.database.session import SessionLocal
from app.models.detalhamento import Detalhamento
from app.models.enums import StatusProcessamento
from app.models.upload_file import UploadFile
from app.services.auditoria_service import AuditoriaService
from app.services.common.tipo_pessoa_config import TipoPessoaConfig
from app.services.upload_file_service import UploadFileService

logger = logging.getLogger("uvicorn.error")


class PessoaImportavelServiceBase(ABC):
    """Template Method compartilhado por EncontreiroService/EncontristaService
    -- CRUD + importação de CSV. Todos os métodos são @classmethod (nunca de
    instância) porque os routers chamam `EncontreiroService.processar_em_background`
    direto na classe, inclusive passando a referência crua pra
    `background_tasks.add_task(...)`; isso continua funcionando sem tocar nos
    routers."""

    CONFIG: ClassVar[TipoPessoaConfig]
    MAX_SIZE_DATA = 3 * 1024 * 1024  # 3 MB

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @classmethod
    def list_all(cls, db: Session, params):
        return cls.CONFIG.repository.list_all(db, params)

    @classmethod
    def list(cls, db: Session, params) -> dict:
        items, total = cls.CONFIG.repository.list_with_count(db, params)
        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit,
        }

    @classmethod
    def get_by_id(cls, db: Session, pessoa_id: int):
        obj = cls.CONFIG.repository.get_by_id(db, pessoa_id)
        if not obj:
            raise NotFoundException(cls.CONFIG.modelo.__name__)

        detalhamento = (
            db.query(Detalhamento)
            .filter(
                Detalhamento.tipo == cls.CONFIG.tipo_detalhamento,
                Detalhamento.referencia_id == obj.id,
            )
            .first()
        )
        obj.detalhamento_id = detalhamento.id if detalhamento else None
        obj.lancamento_vinculado = detalhamento.lancamento if detalhamento else None

        return obj

    @classmethod
    def create(cls, db: Session, data: dict):
        return cls.CONFIG.repository.create(db, data)

    @classmethod
    def update(cls, db: Session, pessoa_id: int, data: dict):
        obj = cls.CONFIG.repository.get_by_id(db, pessoa_id)
        if not obj:
            raise NotFoundException(cls.CONFIG.modelo.__name__)
        return cls.CONFIG.repository.update(db, obj, data)

    @classmethod
    def delete(cls, db: Session, pessoa_id: int) -> None:
        obj = cls.CONFIG.repository.get_by_id(db, pessoa_id)
        if not obj:
            raise NotFoundException(cls.CONFIG.modelo.__name__)
        cls.CONFIG.repository.delete(db, obj)

    # ------------------------------------------------------------------
    # Hooks de importação -- sobrescritos pelas subclasses conforme
    # necessário; os defaults reproduzem o comportamento atual do Encontrista
    # (sem detecção de duplicata, sem `ignorados`/`detalhes_ignorados` no
    # resultado).
    # ------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def _linha_para_dados(cls, db: Session, row, is_new: bool) -> dict: ...

    @classmethod
    def _detectar_duplicata(cls, db: Session, dados: dict):
        return None

    @classmethod
    def _item_ignorado(cls, row, duplicado) -> dict:
        return {"linha": row.linha, "id_csv": row.id, "existente_id": duplicado.id}

    @classmethod
    def _montar_resultado(
        cls, inseridos: int, atualizados: int, ignorados: list[dict]
    ) -> dict:
        return {
            "inseridos": inseridos,
            "atualizados": atualizados,
            "mensagem": (
                f"Processamento concluído. {inseridos} inseridos, {atualizados} atualizados."
            ),
        }

    # ------------------------------------------------------------------
    # Conciliação via CSV
    # ------------------------------------------------------------------

    @classmethod
    def iniciar_conciliacao(cls, file, db: Session) -> UploadFile:
        """Valida e registra o arquivo (síncrono); o processamento em si roda
        em background (ver `processar_em_background`)."""
        if not file.filename.endswith(".csv"):
            raise BadRequestException("Arquivo deve ser CSV")

        try:
            conteudo_bytes = file.file.read()
            if len(conteudo_bytes) > cls.MAX_SIZE_DATA:
                raise BadRequestException(
                    "Arquivo está acima do limite permitido de tamanho de dados"
                )
            conteudo = conteudo_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise BadRequestException(
                "Erro ao processar arquivo. Utilize o charset UTF-8 para evitar problemas de acentuação."
            )

        return UploadFileService.create(
            db,
            {
                "nome_arquivo": file.filename,
                "conteudo_csv": conteudo,
                "tamanho_bytes": len(conteudo.encode("utf-8")),
                "status": StatusProcessamento.PROCESSANDO,
            },
        )

    @classmethod
    def processar_em_background(cls, upload_id: int, conteudo: str) -> None:
        db = SessionLocal()

        try:
            linhas = cls.CONFIG.parser.parse(conteudo)

            inseridos = 0
            atualizados = 0
            ignorados: list[dict] = []

            for row in linhas:
                existente = cls.CONFIG.repository.get_by_id(db, row.id)

                try:
                    dados = cls._linha_para_dados(db, row, is_new=existente is None)
                except ValueError as exc:
                    raise ValueError(f"Linha {row.linha}: {exc}") from exc

                if existente:
                    for key, value in dados.items():
                        if value is not None:
                            setattr(existente, key, value)
                    db.flush()
                    atualizados += 1
                    continue

                duplicado = cls._detectar_duplicata(db, dados)
                if duplicado:
                    logger.warning(
                        "Linha %s ignorada: já existe %s id=%s com o mesmo nome/telefone",
                        row.linha,
                        cls.CONFIG.modelo.__name__,
                        duplicado.id,
                    )
                    ignorados.append(cls._item_ignorado(row, duplicado))
                    continue

                novo = cls.CONFIG.modelo(id=row.id, **dados)
                db.add(novo)
                # sessao usa autoflush=False: sem o flush aqui, linhas do
                # mesmo arquivo nao "enxergam" as anteriores nas checagens
                # de id/duplicata acima.
                db.flush()
                inseridos += 1

            if inseridos:
                db.execute(
                    text(
                        f"SELECT setval('{cls.CONFIG.sequence_name}', "
                        f"(SELECT MAX(id) FROM {cls.CONFIG.modelo.__tablename__}))"
                    )
                )

            db.commit()

            resultado = cls._montar_resultado(inseridos, atualizados, ignorados)

            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.PROCESSADO,
                resultado_processamento=json.dumps(resultado, ensure_ascii=False),
            )

            AuditoriaService.processar(db)

        except Exception as e:
            db.rollback()
            logger.exception(
                "Erro ao processar CSV de %s (upload_id=%s)",
                cls.CONFIG.modelo.__name__,
                upload_id,
            )
            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.ERRO,
                error_code=cls.CONFIG.error_code_importacao,
                error_message=str(e),
            )

        finally:
            db.close()
