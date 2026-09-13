import csv
import io
from dataclasses import dataclass

from app.utils.parse_utils import normalizar_cabecalho

_CABECALHO_PARA_CAMPO = {
    "ID": "id",
    "DT INSC": "dt_inscricao",
    "NOME": "nome",
    "APELIDO": "apelido",
    "INSTAGRAM": "instagram",
    "TELEFONE": "telefone",
    "ESTADO CIVIL": "estado_civil",
    "IGREJA": "igreja",
    "RELIGIAO": "religiao",
    "TEL EMERGENCIA": "contato_emerg",
    "NOME EMERGENCIA": "nome_emerg",
    "PARENTESCO": "parentesco_emerg",
    "ALERGIA OU COMORBIDADE": "alergia_comorbidade",
    "EQUIPE": "equipe_nome",
    "TAM CAMISA": "camisa",
    "SITUACAO": "situacao_camisa",
    "VEICULO": "veiculo",
    "DT PAGAMENTO": "dt_pagamento",
    "NOME PAGADOR": "nome_pagador",
    "PAGAMENTO": "pagamento",
    "OBSERVACAO": "observacao",
    "MONTAGEM": "montagem",
}


@dataclass
class EncontreiroCsvRow:
    linha: int
    id: int
    dt_inscricao: str | None = None
    nome: str | None = None
    apelido: str | None = None
    instagram: str | None = None
    telefone: str | None = None
    estado_civil: str | None = None
    igreja: str | None = None
    religiao: str | None = None
    contato_emerg: str | None = None
    nome_emerg: str | None = None
    parentesco_emerg: str | None = None
    alergia_comorbidade: str | None = None
    equipe_nome: str | None = None
    camisa: str | None = None
    situacao_camisa: str | None = None
    veiculo: str | None = None
    dt_pagamento: str | None = None
    nome_pagador: str | None = None
    pagamento: str | None = None
    observacao: str | None = None
    montagem: str | None = None


def _mapear_cabecalho(row: list[str]) -> dict[int, str]:
    indice_para_campo = {}
    for idx, celula in enumerate(row):
        campo = _CABECALHO_PARA_CAMPO.get(normalizar_cabecalho(celula))
        if campo:
            indice_para_campo[idx] = campo
    return indice_para_campo


def _extrair_dados_linha(
    row: list[str], indice_para_campo: dict[int, str], linha_num: int
) -> dict:
    dados: dict[str, object] = {"linha": linha_num}
    for idx, campo in indice_para_campo.items():
        valor = row[idx].strip() if idx < len(row) else ""
        dados[campo] = valor or None

    id_bruto = dados.pop("id", None)
    if not id_bruto:
        raise ValueError(f"Linha {linha_num}: coluna ID vazia")
    try:
        dados["id"] = id_bruto
    except ValueError as exc:
        raise ValueError(f"Linha {linha_num}: ID inválido '{id_bruto}'") from exc

    return dados


def parse(conteudo: str) -> list[EncontreiroCsvRow]:
    linhas: list[EncontreiroCsvRow] = []

    with io.StringIO(conteudo) as arquivo:
        reader = csv.reader(arquivo, delimiter=",")

        indice_para_campo = None
        linha_num = 0

        for row in reader:
            linha_num += 1

            if indice_para_campo is None:
                if row and normalizar_cabecalho(row[0]) == "ID":
                    indice_para_campo = _mapear_cabecalho(row)
                    if "nome" not in indice_para_campo.values():
                        raise ValueError(
                            "Cabeçalho do CSV de encontreiros não reconhecido"
                        )
                continue

            if not row or not any(c.strip() for c in row):
                continue

            dados = _extrair_dados_linha(row, indice_para_campo, linha_num)
            linhas.append(EncontreiroCsvRow(**dados))

        if indice_para_campo is None:
            raise ValueError("Cabeçalho do CSV de encontreiros não encontrado")

    return linhas
