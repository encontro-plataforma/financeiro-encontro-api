import hashlib

from app.integracao.conciliacao.factory.parser_factory import ParserFactory
from app.integracao.conciliacao.models.conciliacao_dto import ConciliacaoDTO


class Conciliador:

    @staticmethod
    def _normalizar_texto(valor: str) -> str:
        return valor.strip().lower() if valor else ""

    @staticmethod
    def _normalizar_valor(valor: float) -> float:
        return round(float(valor), 2)

    @staticmethod
    def _gerar_hash(lancamento: dict) -> str:
        base = f"{lancamento['data_pagamento']}_{lancamento['valor']}_{lancamento['descricao']}_{lancamento['observacao']}"
        return hashlib.md5(base.encode()).hexdigest()

    @staticmethod
    def processar(conteudo: str, nome_arquivo: str, is_duplicado_callback):
        parser = ParserFactory.get_parser(nome_arquivo)

        registros = parser.parse(conteudo)

        novos: list[ConciliacaoDTO] = []
        duplicados = []
        erros = []

        for idx, dto in enumerate(registros, start=1):
            try:
                if is_duplicado_callback(dto):
                    duplicados.append({
                        "linha": idx,
                        "descricao": dto.descricao,
                        "valor": dto.valor,
                        "data": dto.data.isoformat()
                    })
                    continue

                novos.append(dto)

            except Exception as e:
                erros.append({
                    "linha": idx,
                    "erro": str(e),
                    "descricao": dto.descricao if dto else None
                })

        return {
            "novos": novos,
            "duplicados": duplicados,
            "erros": erros,
            "total_processado": len(registros),
            "total_novos": len(novos),
            "total_duplicados": len(duplicados),
            "total_erros": len(erros),
        }
