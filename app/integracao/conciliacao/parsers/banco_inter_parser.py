from datetime import datetime
from app.integracao.conciliacao.parsers.base_parser import BaseParser
from app.integracao.conciliacao.models.conciliacao_dto import ConciliacaoDTO


class BancoInterParser(BaseParser):

    def __init__(self):
        self.erros: list[dict] = []

    def _to_float(self, valor_str: str) -> float:
        return float(valor_str.replace(".", "").replace(",", "."))

    def _parse_tipo(self, historico: str) -> str:
        historico = historico.lower()

        if "recebido" in historico:
            return "entrada"

        return "saida"

    def parse(self, conteudo: str) -> list[ConciliacaoDTO]:
        import csv
        import io

        result = []
        self.erros = []

        with io.StringIO(conteudo) as csvfile:
            reader = csv.reader(csvfile, delimiter=";")

            header_found = False
            linha_num = 0

            for row in reader:
                linha_num += 1

                if not header_found:
                    if "Data Lançamento" in row:
                        header_found = True
                    continue

                if not row or len(row) < 5:
                    continue

                try:
                    data_str, historico, descricao, valor_str, saldo = row

                    dto = ConciliacaoDTO(
                        descricao=descricao.strip(),
                        valor=abs(self._to_float(valor_str)),
                        data=datetime.strptime(data_str, "%d/%m/%Y"),
                        tipo=self._parse_tipo(historico),
                        observacao=historico.strip() + " | Saldo: " + saldo.strip(),
                        # observacao=historico.strip(),
                        banco="INTER",
                        linha_csv=linha_num,
                    )

                    result.append(dto)

                except Exception as e:
                    self.erros.append({
                        "linha": linha_num,
                        "erro": str(e),
                        "descricao": None,
                    })

        if self.erros:
            print(f"[Parser] Linhas com erro: {len(self.erros)}")
            for e in self.erros:
                print(e)

        return result