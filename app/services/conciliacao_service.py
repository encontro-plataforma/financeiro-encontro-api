from sqlalchemy.orm import Session

from app.integracao.conciliacao.conciliador import Conciliador
from app.services.extrato_bancario_service import ExtratoBancarioService
from app.services.lancamento_service import LancamentoService
from app.models.enums import FormaPagamento, StatusLancamento, StatusProcessamento, TipoLancamento
from app.utils.hash_utils import gerar_hash

# IDs canônicos das finalidades padrão usadas na sugestão automática
_RECEITA_OFERTA         = 1
_RECEITA_CAMPANHA       = 2
_RECEITA_INSCRICAO_ENCA = 3
_RECEITA_INSCRICAO_ENCO = 4
_RECEITA_OUTROS         = 5

_DESPESA_CAMISAS        = 101
_DESPESA_COMPRAS        = 105
_DESPESA_OUTROS         = 114


class ConciliacaoService:

    @staticmethod
    def _sugerir_finalidade_receita(dto) -> int:
        """Sugere a finalidade de RECEITA com base no valor do lançamento."""
        if dto.valor == 120:
            return _RECEITA_INSCRICAO_ENCO
        if 200 <= dto.valor <= 220:
            return _RECEITA_INSCRICAO_ENCA
        if 10 <= dto.valor <= 50:
            return _RECEITA_CAMPANHA
        if dto.valor > 50:
            return _RECEITA_OUTROS
        
        return _RECEITA_OFERTA

    @staticmethod
    def _sugerir_finalidade_despesa(dto) -> int:
        """Sugere a finalidade de DESPESA com base no lançamento. Escolhe por heurística da descrição."""
        label = dto.descricao.lower() if dto.descricao else ""
        
        if "camisa" in label:
            return _DESPESA_CAMISAS
        if any(w in label for w in ["atacarejo", "atacadão", "atacadao", "supermercado", "mercado", "compras"]):
            return _DESPESA_COMPRAS
        
        return _DESPESA_OUTROS

    @staticmethod
    def _sugerir_finalidade(dto) -> int | None:
        if dto.tipo == "entrada":
            return ConciliacaoService._sugerir_finalidade_receita(dto)
        return ConciliacaoService._sugerir_finalidade_despesa(dto)

    @staticmethod
    def _to_lancamento_dict(dto):
        tipo = (
            TipoLancamento.RECEITA
            if dto.tipo == "entrada"
            else TipoLancamento.DESPESA
        )

        observacao = dto.observacao or ""

        hash_value = gerar_hash(
            dto.descricao,
            dto.valor,
            dto.data,
            observacao,
        )

        sugestao_id = ConciliacaoService._sugerir_finalidade(dto)

        return {
            "descricao": dto.descricao,
            "valor": dto.valor,
            "tipo": tipo,
            "forma_pagamento": FormaPagamento.PIX,
            "status": StatusLancamento.NAO_CONCILIADO,
            "data_pagamento": dto.data,
            "hash_transacao": hash_value,
            "observacao": observacao,
            "finalidade_id": None,
            "sugestao_finalidade_id": sugestao_id,
        }

    @staticmethod
    def upload_and_process(file, db: Session):
        if not file.filename.endswith(".csv"):
            raise Exception("Arquivo deve ser CSV")

        try:
            conteudo_bytes = file.file.read()
            if len(conteudo_bytes) > 3 * 1024 * 1024:
                raise Exception("Arquivo está acima do limite permitido de tamanho de dados")
            conteudo = conteudo_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise Exception(
                "Erro ao processar arquivo. Utilize o charset UTF-8 para evitar problemas de acentuação."
            )

        extrato = ExtratoBancarioService.create(db, {
            "nome_arquivo": file.filename,
            "conteudo_csv": conteudo,
            "tamanho_bytes": len(conteudo.encode('utf-8')),
            "status": StatusProcessamento.PROCESSANDO,
        })

        try:
            def is_duplicado(dto) -> bool:
                data = ConciliacaoService._to_lancamento_dict(dto)
                return LancamentoService.exists_by_hash(db, data["hash_transacao"])

            resultado = Conciliador.processar(
                conteudo,
                file.filename,
                is_duplicado,
            )

            for dto in resultado["novos"]:
                try:
                    lancamento_data = ConciliacaoService._to_lancamento_dict(dto)
                    LancamentoService.create(db, lancamento_data)
                except Exception as e:
                    print(f"[DB ERROR] {e}")

            ExtratoBancarioService.update_status(
                db,
                extrato.id,
                StatusProcessamento.PROCESSADO,
            )

            return {
                "inseridos": resultado["total_novos"],
                "duplicados": resultado["total_duplicados"],
                "erros": resultado["total_erros"],
                "mensagem": (
                    f"Processamento concluído. {resultado['total_novos']} inseridos, "
                    f"{resultado['total_duplicados']} duplicados, {resultado['total_erros']} erros."
                ),
            }

        except Exception as e:
            ExtratoBancarioService.update_status(
                db,
                extrato.id,
                StatusProcessamento.ERRO,
            )
            raise Exception(f"Erro ao processar arquivo: {str(e)}")
