import csv
import io
from collections import defaultdict

from app.integracao.conciliacao.models.especie_dto import EspecieLinhaDTO
from app.integracao.conciliacao.parsers.base_parser import BaseParser
from app.utils.parse_utils import normalizar_cabecalho, parse_date_br, parse_decimal_br

_CABECALHO_ESPERADO = ["DATA", "TIPO", "NOME", "DESCRICAO", "VALOR", "OBSERVACAO"]


class EspecieParser(BaseParser):
    """Extrato manual de espécie (dinheiro) -- cada linha já diz
    explicitamente do que se trata (tipo, nome, descrição, valor,
    observação), sem texto livre pra interpretar."""

    def __init__(self):
        self.erros: list[dict] = []

    def parse(self, conteudo: str) -> list[EspecieLinhaDTO]:
        result: list[EspecieLinhaDTO] = []
        self.erros = []

        # Mesma técnica do BancoInterParser: conta ocorrências de linhas
        # idênticas dentro do MESMO arquivo (reseta a cada parse()) e
        # sufixa a observação -- evita que pagamentos genuinamente distintos
        # (mesma pessoa/tipo/valor/data) colidam no hash de deduplicação.
        ocorrencias: dict[tuple, int] = defaultdict(int)

        with io.StringIO(conteudo) as csvfile:
            reader = csv.reader(csvfile, delimiter=";")

            header_found = False
            linha_num = 0

            for row in reader:
                linha_num += 1

                if not header_found:
                    cabecalho = [normalizar_cabecalho(c) for c in row]
                    if cabecalho == _CABECALHO_ESPERADO:
                        header_found = True
                    continue

                if not row or all(not c.strip() for c in row):
                    continue

                if len(row) < 6:
                    self.erros.append({
                        "linha": linha_num,
                        "erro": f"Esperado 6 colunas ({';'.join(_CABECALHO_ESPERADO)}), encontrado {len(row)}.",
                        "descricao": None,
                    })
                    continue

                try:
                    data_str, tipo, nome, descricao, valor_str, observacao = row[:6]

                    tipo = tipo.strip()
                    nome = nome.strip()
                    descricao = descricao.strip()
                    observacao = observacao.strip()

                    if not tipo:
                        raise ValueError("coluna 'tipo' é obrigatória")

                    data = parse_date_br(data_str)
                    if data is None:
                        raise ValueError("coluna 'data' é obrigatória")

                    valor = parse_decimal_br(valor_str)
                    if valor is None:
                        raise ValueError("coluna 'valor' é obrigatória")

                    chave = (normalizar_cabecalho(tipo), normalizar_cabecalho(nome), normalizar_cabecalho(descricao), valor, data)
                    ocorrencias[chave] += 1
                    if ocorrencias[chave] > 1:
                        observacao = f"{observacao} | ocor: {ocorrencias[chave]}".strip(" |")

                    result.append(EspecieLinhaDTO(
                        data=data,
                        tipo=tipo,
                        nome=nome or None,
                        descricao=descricao or None,
                        valor=valor,
                        observacao=observacao or None,
                        linha_csv=linha_num,
                    ))

                except Exception as e:
                    self.erros.append({
                        "linha": linha_num,
                        "erro": str(e),
                        "descricao": None,
                    })

        return result
