import csv
import io
from dataclasses import dataclass

from app.utils.parse_utils import normalizar_cabecalho

# O cabeçalho real desse CSV tem rótulos repetidos (ID aparece nas colunas
# 1 e 4; NOME/CONTATO aparecem 3x cada), então o mapeamento é posicional
# (índices fixos), não por nome de coluna como no CSV de Encontreiro.
_NUM_COLUNAS = 33

_CAMPOS_POR_INDICE = {
    0: "id",
    1: "dt_entrega",
    2: "dt_validade",
    3: "padrinho_id",
    # 4, 5, 6 = nome/contato/equipe do padrinho — ignorados, só o ID importa
    7: "carta",
    8: "album",
    9: "nome",
    10: "apelido",
    11: "dt_nascimento",
    12: "idade",
    13: "onde_veio_ficha",
    14: "circulo_nome",
    15: "instagram",
    16: "contato",
    17: "religiao",
    18: "igreja",
    19: "endereco",
    20: "cidade",
    21: "camisa",
    22: "blusa",
    23: "veiculo",
    24: "contato_emerg",
    25: "nome_emerg",
    26: "parentesco_emerg",
    27: "medicacao",
    28: "alergia_comorbidade",
    29: "dt_pagamento",
    30: "nome_pagador",
    31: "pagamento",
    32: "observacao",
}


@dataclass
class EncontristaCsvRow:
    linha: int
    id: int
    padrinho_id: int
    dt_entrega: str | None = None
    dt_validade: str | None = None
    carta: str | None = None
    album: str | None = None
    nome: str | None = None
    apelido: str | None = None
    dt_nascimento: str | None = None
    idade: str | None = None
    circulo_nome: str | None = None
    onde_veio_ficha: str | None = None
    instagram: str | None = None
    contato: str | None = None
    religiao: str | None = None
    igreja: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    camisa: str | None = None
    blusa: str | None = None
    veiculo: str | None = None
    contato_emerg: str | None = None
    nome_emerg: str | None = None
    parentesco_emerg: str | None = None
    medicacao: str | None = None
    alergia_comorbidade: str | None = None
    dt_pagamento: str | None = None
    nome_pagador: str | None = None
    pagamento: str | None = None
    observacao: str | None = None


def _to_int(valor: str | None, linha: int, campo: str) -> int:
    if not valor:
        raise ValueError(f"Linha {linha}: coluna {campo} vazia")
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"Linha {linha}: {campo} inválido '{valor}'") from exc


def parse(conteudo: str) -> list[EncontristaCsvRow]:
    linhas: list[EncontristaCsvRow] = []

    with io.StringIO(conteudo) as arquivo:
        reader = csv.reader(arquivo, delimiter=",")

        cabecalho_encontrado = False
        linha_num = 0

        for row in reader:
            linha_num += 1

            if not cabecalho_encontrado:
                if (
                    row
                    and normalizar_cabecalho(row[0]) == "ID"
                    and len(row) >= _NUM_COLUNAS
                ):
                    cabecalho_encontrado = True
                continue

            if not row or not any(c.strip() for c in row):
                continue

            # Nome vazio indica o fim dos registros exportados.
            nome_bruto = row[9].strip() if len(row) > 9 else ""
            if nome_bruto == "":
                break

            if len(row) < _NUM_COLUNAS:
                raise ValueError(
                    f"Linha {linha_num}: esperado {_NUM_COLUNAS} colunas, encontrado {len(row)}"
                )

            dados = {"linha": linha_num}
            for idx, campo in _CAMPOS_POR_INDICE.items():
                valor = row[idx].strip()
                dados[campo] = valor or None

            dados["id"] = _to_int(dados.get("id"), linha_num, "ID")
            dados["padrinho_id"] = _to_int(
                dados.get("padrinho_id"), linha_num, "ID do padrinho"
            )

            linhas.append(EncontristaCsvRow(**dados))

        if not cabecalho_encontrado:
            raise ValueError("Cabeçalho do CSV de encontristas não encontrado")

    return linhas
