import json
import logging

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.integracao.conciliacao.models.cartao_dto import CartaoLinhaDTO
from app.integracao.conciliacao.parsers.cartao_parser import CartaoParser
from app.models.enums import StatusProcessamento, TipoLancamento, TipoOrigemUpload
from app.models.upload_file import UploadFile
from app.services.auditoria_service import AuditoriaService
from app.services.lancamento_service import LancamentoService
from app.services.upload_file_service import UploadFileService
from app.utils.hash_utils import gerar_hash

logger = logging.getLogger("uvicorn.error")


def _montar_descricao(linha: CartaoLinhaDTO) -> str:
    """Sem nome do pagador no extrato -- a Bandeira ocupa o lugar onde
    normalmente iria um nome, só como texto informativo (não é usado em
    nenhum critério de match)."""
    return f"Venda cartão {linha.bandeira}"


def _montar_observacao(linha: CartaoLinhaDTO) -> str:
    forma_label = (
        "Crédito" if linha.forma_pagamento.value == "CARTAO_CREDITO" else "Débito"
    )
    return (
        f"{forma_label} {linha.num_parcelas}x | transação {linha.codigo_transacao} | "
        f"status {linha.status}"
    )


class CartaoService:
    @staticmethod
    def iniciar_conciliacao(file, db: Session) -> UploadFile:
        if not file.filename.endswith(".csv"):
            raise Exception("Arquivo deve ser CSV")

        try:
            conteudo_bytes = file.file.read()
            if len(conteudo_bytes) > 3 * 1024 * 1024:
                raise Exception(
                    "Arquivo está acima do limite permitido de tamanho de dados"
                )
            conteudo = conteudo_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise Exception(
                "Erro ao processar arquivo. Utilize o charset UTF-8 para evitar problemas de acentuação."
            )

        return UploadFileService.create(
            db,
            {
                "nome_arquivo": file.filename,
                "conteudo_csv": conteudo,
                "tamanho_bytes": len(conteudo.encode("utf-8")),
                "status": StatusProcessamento.PROCESSANDO,
                "tipo_origem": TipoOrigemUpload.CARTAO,
            },
        )

    @staticmethod
    def _processar_linha(db: Session, linha: CartaoLinhaDTO) -> dict:
        descricao = _montar_descricao(linha)
        observacao = _montar_observacao(linha)
        # O código da transação (UUID único da PagBank) já está embutido na
        # observação, então o hash sai único por venda real -- dispensa o
        # truque de contador de ocorrências usado no BancoInterParser/
        # EspecieParser pra diferenciar vendas repetidas no mesmo arquivo.
        hash_value = gerar_hash(descricao, linha.valor_bruto, linha.data, observacao)

        if LancamentoService.exists_by_hash(db, hash_value):
            return {
                "duplicado": True,
                "descricao": descricao,
                "valor": float(linha.valor_bruto),
                "data": linha.data.isoformat(),
            }

        LancamentoService.create(
            db,
            {
                "descricao": descricao,
                "valor": linha.valor_bruto,
                "tipo": TipoLancamento.RECEITA,
                "forma_pagamento": linha.forma_pagamento,
                "data_pagamento": linha.data,
                "hash_transacao": hash_value,
                "observacao": observacao,
                "cart_taxa": float(linha.valor_taxa),
                "cart_valor_liquido": float(linha.valor_liquido),
                "cart_parcelas": linha.num_parcelas,
                "finalidade_id": None,
                "sugestao_finalidade_id": None,
            },
        )

        return {"duplicado": False}

    @staticmethod
    def processar_em_background(upload_id: int, conteudo: str):
        db = SessionLocal()

        try:
            parser = CartaoParser()
            linhas = parser.parse(conteudo)
            erros = list(parser.erros)
            ignorados = list(parser.ignoradas)
            duplicados = []
            inseridos = 0

            for linha in linhas:
                try:
                    resultado = CartaoService._processar_linha(db, linha)
                    if resultado["duplicado"]:
                        duplicados.append(
                            {
                                "linha": linha.linha_csv,
                                "descricao": resultado["descricao"],
                                "valor": resultado["valor"],
                                "data": resultado["data"],
                            }
                        )
                    else:
                        inseridos += 1
                except Exception as e:
                    erros.append(
                        {
                            "linha": linha.linha_csv,
                            "erro": str(e),
                            "descricao": None,
                        }
                    )

            resultado_resumo = {
                "inseridos": inseridos,
                "duplicados": len(duplicados),
                "ignorados": len(ignorados),
                "erros": len(erros),
                "detalhes_erros": erros,
                "detalhes_duplicados": duplicados,
                "detalhes_ignorados": ignorados,
                "mensagem": (
                    f"Processamento concluído. {inseridos} inseridos, "
                    f"{len(duplicados)} duplicados, {len(ignorados)} ignorados "
                    f"(não aprovadas/canceladas), {len(erros)} erros."
                ),
            }

            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.PROCESSADO,
                resultado_processamento=json.dumps(
                    resultado_resumo, ensure_ascii=False
                ),
            )

            AuditoriaService.processar(db)

        except Exception as e:
            logger.exception(
                "Erro ao processar extrato de cartão (upload_id=%s)", upload_id
            )
            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.ERRO,
                error_code="ERRO_PROCESSAMENTO_CARTAO",
                error_message=str(e),
            )

        finally:
            db.close()
