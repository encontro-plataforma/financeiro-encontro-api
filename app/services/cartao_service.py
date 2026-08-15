import logging

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.integracao.conciliacao.parsers.cartao_parser import CartaoParser
from app.models.enums import StatusProcessamento, TipoOrigemUpload
from app.models.upload_file import UploadFile
from app.services.upload_file_service import UploadFileService

logger = logging.getLogger("uvicorn.error")


class CartaoService:
    """Pré-requisito da Fase 4: rota e fluxo de upload já existem, mas o
    formato do extrato da maquininha ainda não foi definido -- o parser
    (`CartaoParser`) recusa com uma mensagem clara em vez de tentar
    adivinhar um layout. Assim que o formato real chegar, só
    `CartaoParser.parse` + a lógica de linha (nos moldes de
    `EspecieService`) precisam ser implementados."""

    @staticmethod
    def iniciar_conciliacao(file, db: Session) -> UploadFile:
        if not file.filename.endswith(".csv"):
            raise Exception("Arquivo deve ser CSV")

        try:
            conteudo_bytes = file.file.read()
            if len(conteudo_bytes) > 3 * 1024 * 1024:
                raise Exception("Arquivo está acima do limite permitido de tamanho de dados")
            conteudo = conteudo_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise Exception(
                "Erro ao processar arquivo. Utilize o charset UTF-8 para evitar problemas de acentuação."
            )

        return UploadFileService.create(db, {
            "nome_arquivo": file.filename,
            "conteudo_csv": conteudo,
            "tamanho_bytes": len(conteudo.encode("utf-8")),
            "status": StatusProcessamento.PROCESSANDO,
            "tipo_origem": TipoOrigemUpload.CARTAO,
        })

    @staticmethod
    def processar_em_background(upload_id: int, conteudo: str):
        db = SessionLocal()

        try:
            CartaoParser().parse(conteudo)

        except Exception as e:
            logger.info("Extrato de cartão ainda não suportado (upload_id=%s): %s", upload_id, e)
            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.ERRO,
                error_code="FORMATO_CARTAO_NAO_DEFINIDO",
                error_message=str(e),
            )

        finally:
            db.close()
