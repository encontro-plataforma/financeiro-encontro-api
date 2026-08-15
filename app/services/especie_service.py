import json
import logging

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.integracao.conciliacao.models.especie_dto import EspecieLinhaDTO
from app.integracao.conciliacao.parsers.especie_parser import EspecieParser
from app.models.enums import (
    FormaPagamento,
    StatusProcessamento,
    TipoDetalhamento,
    TipoLancamento,
    TipoOrigemUpload,
)
from app.models.upload_file import UploadFile
from app.repositories.finalidade_repository import FinalidadeRepository
from app.services.auditoria_service import AuditoriaService
from app.services.detalhamento_service import DetalhamentoService
from app.services.lancamento_service import LancamentoService
from app.services.upload_file_service import UploadFileService
from app.utils.hash_utils import gerar_hash
from app.utils.parse_utils import remover_acentos

logger = logging.getLogger("uvicorn.error")

_TIPOS_INSCRICAO = {TipoDetalhamento.INSCRICAO_ENCONTREIRO, TipoDetalhamento.INSCRICAO_ENCONTRISTA}

_ALIASES_INSCRICAO = {
    "ENCONTREIRO": TipoDetalhamento.INSCRICAO_ENCONTREIRO,
    "INSCRICAO_ENCONTREIRO": TipoDetalhamento.INSCRICAO_ENCONTREIRO,
    "ENCONTRISTA": TipoDetalhamento.INSCRICAO_ENCONTRISTA,
    "INSCRICAO_ENCONTRISTA": TipoDetalhamento.INSCRICAO_ENCONTRISTA,
}

# Nomes de Finalidade de RECEITA já seedados que um "tipo" avulso do CSV pode
# corresponder diretamente (ver app/database/seeds/seed_finalidade.py).
_NOMES_FINALIDADE_AVULSO = {"OFERTA", "CAMPANHA", "PERSONALIZADO", "LANCHONETE", "LIVRARIA"}


def _tipo_normalizado(tipo_csv: str) -> str:
    return remover_acentos(tipo_csv or "").strip().upper()


def resolver_tipo_detalhamento(tipo_csv: str) -> TipoDetalhamento:
    """"ENCONTREIRO"/"ENCONTRISTA" (ou os nomes completos do enum) viram
    Inscrição; "OFERTA" mapeia direto; qualquer outra coisa vira OUTRO."""
    norm = _tipo_normalizado(tipo_csv)
    if norm in _ALIASES_INSCRICAO:
        return _ALIASES_INSCRICAO[norm]
    if norm == "OFERTA":
        return TipoDetalhamento.OFERTA
    return TipoDetalhamento.OUTRO


def formatar_descricao_detalhamento(tipo_csv: str, descricao: str | None, observacao: str | None) -> str:
    """"Lançamento de {tipo} para {descricao} (${observacao})" -- partes
    vazias são omitidas."""
    base = f"Lançamento de {_tipo_normalizado(tipo_csv)}"
    if descricao:
        base = f"{base} para {descricao}"
    if observacao:
        base = f"{base} ({observacao})"
    return base


def resolver_nome_finalidade_avulso(tipo_csv: str) -> str | None:
    norm = _tipo_normalizado(tipo_csv)
    return norm if norm in _NOMES_FINALIDADE_AVULSO else None


class EspecieService:

    @staticmethod
    def iniciar_conciliacao(file, db: Session) -> UploadFile:
        """Valida e registra o arquivo (síncrono); o processamento em si roda em
        background (ver `processar_em_background`)."""
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
            "tipo_origem": TipoOrigemUpload.ESPECIE,
        })

    @staticmethod
    def _processar_linha(db: Session, linha: EspecieLinhaDTO) -> dict:
        """Cria o(s) registro(s) da linha. Retorna {"duplicado": bool, ...}
        pra quem chama decidir a contagem -- exceções (ValueError, etc.) sobem
        pra virar "erro" de linha."""
        tipo_detalhamento = resolver_tipo_detalhamento(linha.tipo)

        if tipo_detalhamento in _TIPOS_INSCRICAO:
            if not linha.nome:
                raise ValueError("coluna 'nome' é obrigatória para linhas de inscrição (ENCONTREIRO/ENCONTRISTA)")

            descricao_lancamento = f"Espécie - {linha.nome}"
            observacao_lancamento = linha.observacao or ""
            hash_value = gerar_hash(descricao_lancamento, linha.valor, linha.data, observacao_lancamento)

            if LancamentoService.exists_by_hash(db, hash_value):
                return {"duplicado": True, "descricao": descricao_lancamento, "valor": linha.valor, "data": linha.data.isoformat()}

            finalidade_inscricao = FinalidadeRepository.get_by_nome(db, "INSCRIÇÃO")

            # Inscrição nasce NAO_CONCILIADO (LancamentoService.create já força
            # isso) -- não cria Detalhamento aqui; a Auditoria (Etapa A/B) que
            # roda no fim do processamento é quem liga isso à pendência certa.
            LancamentoService.create(db, {
                "descricao": descricao_lancamento,
                "valor": linha.valor,
                "tipo": TipoLancamento.RECEITA,
                "forma_pagamento": FormaPagamento.DINHEIRO,
                "data_pagamento": linha.data,
                "hash_transacao": hash_value,
                "observacao": observacao_lancamento,
                "finalidade_id": None,
                "sugestao_finalidade_id": finalidade_inscricao.id if finalidade_inscricao else None,
            })
            return {"duplicado": False}

        # Linha avulsa (Oferta/Campanha/Personalizado/Livraria/Lanchonete/
        # qualquer outra) -- a própria linha já é a informação completa, então
        # Lancamento + Detalhamento nascem juntos, sem passar pela Auditoria.
        descricao_completa = formatar_descricao_detalhamento(linha.tipo, linha.descricao, linha.observacao)
        hash_value = gerar_hash(descricao_completa, linha.valor, linha.data, "")

        if LancamentoService.exists_by_hash(db, hash_value):
            return {"duplicado": True, "descricao": descricao_completa, "valor": linha.valor, "data": linha.data.isoformat()}

        nome_finalidade = resolver_nome_finalidade_avulso(linha.tipo)
        finalidade = FinalidadeRepository.get_by_nome(db, nome_finalidade) if nome_finalidade else None

        lancamento = LancamentoService.create(db, {
            "descricao": descricao_completa,
            "valor": linha.valor,
            "tipo": TipoLancamento.RECEITA,
            "forma_pagamento": FormaPagamento.DINHEIRO,
            "data_pagamento": linha.data,
            "hash_transacao": hash_value,
            "observacao": "",
            "finalidade_id": finalidade.id if finalidade else None,
            "sugestao_finalidade_id": None,
        })

        # DetalhamentoService.create já sincroniza o status do Lancamento pra
        # CONCILIADO sozinho (soma dos detalhamentos cobre o valor total).
        DetalhamentoService.create(db, {
            "lancamento_id": lancamento.id,
            "tipo": tipo_detalhamento,
            "referencia_id": None,
            "valor": linha.valor,
            "descricao": descricao_completa,
        })
        return {"duplicado": False}

    @staticmethod
    def processar_em_background(upload_id: int, conteudo: str):
        db = SessionLocal()

        try:
            parser = EspecieParser()
            linhas = parser.parse(conteudo)
            erros = list(parser.erros)
            duplicados = []
            inseridos = 0

            for linha in linhas:
                try:
                    resultado = EspecieService._processar_linha(db, linha)
                    if resultado["duplicado"]:
                        duplicados.append({
                            "linha": linha.linha_csv,
                            "descricao": resultado["descricao"],
                            "valor": resultado["valor"],
                            "data": resultado["data"],
                        })
                    else:
                        inseridos += 1
                except Exception as e:
                    erros.append({
                        "linha": linha.linha_csv,
                        "erro": str(e),
                        "descricao": linha.descricao,
                    })

            resultado_resumo = {
                "inseridos": inseridos,
                "duplicados": len(duplicados),
                "erros": len(erros),
                "detalhes_erros": erros,
                "detalhes_duplicados": duplicados,
                "mensagem": (
                    f"Processamento concluído. {inseridos} inseridos, "
                    f"{len(duplicados)} duplicados, {len(erros)} erros."
                ),
            }

            UploadFileService.update_status(
                db, upload_id, StatusProcessamento.PROCESSADO,
                resultado_processamento=json.dumps(resultado_resumo, ensure_ascii=False),
            )

            AuditoriaService.processar(db)

        except Exception as e:
            logger.exception("Erro ao processar extrato de espécie (upload_id=%s)", upload_id)
            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.ERRO,
                error_code="ERRO_PROCESSAMENTO_ESPECIE",
                error_message=str(e),
            )

        finally:
            db.close()
