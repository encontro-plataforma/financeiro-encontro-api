import csv
import io
import re

from app.integracao.conciliacao.models.cartao_dto import CartaoLinhaDTO
from app.integracao.conciliacao.parsers.base_parser import BaseParser
from app.models.enums import FormaPagamento
from app.utils.parse_utils import normalizar_cabecalho, parse_date_br, parse_decimal_br

_COL_DATA = "DATA DA TRANSACAO"
_COL_BANDEIRA = "BANDEIRA"
_COL_FORMA = "FORMA DE PAGAMENTO"
_COL_PARCELA = "PARCELA"
_COL_VALOR_BRUTO = "VALOR BRUTO"
_COL_VALOR_TAXA = "VALOR TAXA"
_COL_VALOR_LIQUIDO = "VALOR LIQUIDO"
_COL_STATUS = "STATUS"
_COL_CANCELAMENTO = "DATA DO CANCELAMENTO"
_COL_CODIGO_TRANSACAO = "CODIGO DA TRANSACAO"

_COLUNAS_OBRIGATORIAS = [
    _COL_DATA, _COL_BANDEIRA, _COL_FORMA, _COL_PARCELA,
    _COL_VALOR_BRUTO, _COL_VALOR_TAXA, _COL_VALOR_LIQUIDO,
    _COL_STATUS, _COL_CANCELAMENTO, _COL_CODIGO_TRANSACAO,
]

_RE_NUMERO = re.compile(r"(\d+)")


class CartaoParser(BaseParser):
    """Extrato de vendas da maquininha (PagBank) -- sem nome do pagador, só
    dados da venda (data, bandeira, forma de pagamento, parcelas, valores
    bruto/taxa/líquido). Cada linha "Aprovada" vira um Lancamento novo (ver
    CartaoService); linhas reprovadas/canceladas nunca geraram dinheiro real
    e só são contadas à parte, em `ignoradas`."""

    def __init__(self):
        self.erros: list[dict] = []
        self.ignoradas: list[dict] = []

    @staticmethod
    def _forma_pagamento(valor: str) -> FormaPagamento:
        normalizado = normalizar_cabecalho(valor)
        if "CREDITO" in normalizado:
            return FormaPagamento.CARTAO_CREDITO
        if "DEBITO" in normalizado:
            return FormaPagamento.CARTAO_DEBITO
        raise ValueError(f"Forma de pagamento não reconhecida: '{valor}'")

    @staticmethod
    def _num_parcelas(valor: str) -> int:
        normalizado = normalizar_cabecalho(valor)
        if not normalizado or normalizado == "A VISTA":
            return 1
        match = _RE_NUMERO.search(normalizado)
        return int(match.group(1)) if match else 1

    def parse(self, conteudo: str) -> list[CartaoLinhaDTO]:
        result: list[CartaoLinhaDTO] = []
        self.erros = []
        self.ignoradas = []

        # O arquivo é um export fixo de terceiro (PagBank); o BOM que sobra
        # da decodificação UTF-8 feita no CartaoService gruda no primeiro
        # campo do cabeçalho e precisa ser descartado antes de comparar.
        with io.StringIO(conteudo.lstrip("﻿")) as csvfile:
            reader = csv.reader(csvfile, delimiter=";")

            indices: dict[str, int] = {}
            header_found = False
            linha_num = 0

            for row in reader:
                linha_num += 1

                if not header_found:
                    cabecalho = [normalizar_cabecalho(c) for c in row]
                    if all(col in cabecalho for col in _COLUNAS_OBRIGATORIAS):
                        indices = {col: cabecalho.index(col) for col in _COLUNAS_OBRIGATORIAS}
                        header_found = True
                    continue

                if not row or all(not c.strip() for c in row):
                    continue

                try:
                    status = row[indices[_COL_STATUS]].strip()
                    data_cancelamento = row[indices[_COL_CANCELAMENTO]].strip()
                    codigo_transacao = row[indices[_COL_CODIGO_TRANSACAO]].strip()

                    if normalizar_cabecalho(status) != "APROVADA" or data_cancelamento:
                        self.ignoradas.append({
                            "linha": linha_num,
                            "codigo_transacao": codigo_transacao,
                            "status": status,
                        })
                        continue

                    data_str = row[indices[_COL_DATA]].strip().split(" ")[0]
                    data = parse_date_br(data_str)
                    if data is None:
                        raise ValueError("coluna 'Data da Transação' é obrigatória")

                    if not codigo_transacao:
                        raise ValueError("coluna 'Código da Transação' é obrigatória")

                    forma_pagamento = self._forma_pagamento(row[indices[_COL_FORMA]])
                    num_parcelas = self._num_parcelas(row[indices[_COL_PARCELA]])

                    valor_bruto = parse_decimal_br(row[indices[_COL_VALOR_BRUTO]])
                    valor_taxa = parse_decimal_br(row[indices[_COL_VALOR_TAXA]])
                    valor_liquido = parse_decimal_br(row[indices[_COL_VALOR_LIQUIDO]])
                    if valor_bruto is None or valor_taxa is None or valor_liquido is None:
                        raise ValueError("valores da venda (bruto/taxa/líquido) são obrigatórios")

                    result.append(CartaoLinhaDTO(
                        data=data,
                        bandeira=row[indices[_COL_BANDEIRA]].strip(),
                        forma_pagamento=forma_pagamento,
                        num_parcelas=num_parcelas,
                        valor_bruto=valor_bruto,
                        valor_taxa=valor_taxa,
                        valor_liquido=valor_liquido,
                        status=status,
                        codigo_transacao=codigo_transacao,
                        linha_csv=linha_num,
                    ))

                except Exception as e:
                    self.erros.append({
                        "linha": linha_num,
                        "erro": str(e),
                        "descricao": None,
                    })

        if not header_found:
            raise ValueError(
                "Cabeçalho do extrato de cartão não reconhecido. Verifique se o "
                "arquivo é o export de vendas da maquininha (PagBank) e se o "
                "charset é UTF-8."
            )

        return result
