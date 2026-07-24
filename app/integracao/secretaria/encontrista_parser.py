import csv
import io
from dataclasses import dataclass
from typing import List, Optional

from app.utils.parse_utils import normalizar_cabecalho

# O cabeçalho real desse CSV tem rótulos repetidos (ID aparece nas colunas
# 1 e 4; NOME/CONTATO aparecem 3x cada), então o mapeamento é posicional
# (índices fixos), não por nome de coluna como no CSV de Encontreiro.
_NUM_COLUNAS = 32

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
    13: "circulo_nome",
    14: "instagram",
    15: "contato",
    16: "religiao",
    17: "igreja",
    18: "endereco",
    19: "cidade",
    20: "camisa",
    21: "blusa",
    22: "veiculo",
    23: "contato_emerg",
    24: "nome_emerg",
    25: "parentesco_emerg",
    26: "medicacao",
    27: "alergia_comorbidade",
    28: "dt_pagamento",
    29: "nome_pagador",
    30: "pagamento",
    31: "observacao",
}


@dataclass
class EncontristaCsvRow:
    linha: int
    id: int
    padrinho_id: int
    dt_entrega: Optional[str] = None
    dt_validade: Optional[str] = None
    carta: Optional[str] = None
    album: Optional[str] = None
    nome: Optional[str] = None
    apelido: Optional[str] = None
    dt_nascimento: Optional[str] = None
    idade: Optional[str] = None
    circulo_nome: Optional[str] = None
    instagram: Optional[str] = None
    contato: Optional[str] = None
    religiao: Optional[str] = None
    igreja: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    camisa: Optional[str] = None
    blusa: Optional[str] = None
    veiculo: Optional[str] = None
    contato_emerg: Optional[str] = None
    nome_emerg: Optional[str] = None
    parentesco_emerg: Optional[str] = None
    medicacao: Optional[str] = None
    alergia_comorbidade: Optional[str] = None
    dt_pagamento: Optional[str] = None
    nome_pagador: Optional[str] = None
    pagamento: Optional[str] = None
    observacao: Optional[str] = None


def _to_int(valor: Optional[str], linha: int, campo: str) -> int:
    if not valor:
        raise ValueError(f"Linha {linha}: coluna {campo} vazia")
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"Linha {linha}: {campo} inválido '{valor}'") from exc


def parse(conteudo: str) -> List[EncontristaCsvRow]:
    linhas: List[EncontristaCsvRow] = []

    with io.StringIO(conteudo) as arquivo:
        reader = csv.reader(arquivo, delimiter=",")

        cabecalho_encontrado = False
        linha_num = 0

        for row in reader:
            linha_num += 1

            if not cabecalho_encontrado:
                if row and normalizar_cabecalho(row[0]) == "ID" and len(row) >= _NUM_COLUNAS:
                    cabecalho_encontrado = True
                continue

            if not row or not any(c.strip() for c in row):
                continue

            if len(row) < _NUM_COLUNAS:
                raise ValueError(
                    f"Linha {linha_num}: esperado {_NUM_COLUNAS} colunas, encontrado {len(row)}"
                )

            dados = {"linha": linha_num}
            for idx, campo in _CAMPOS_POR_INDICE.items():
                valor = row[idx].strip()
                dados[campo] = valor or None

            dados["id"] = _to_int(dados.get("id"), linha_num, "ID")
            dados["padrinho_id"] = _to_int(dados.get("padrinho_id"), linha_num, "ID do padrinho")

            linhas.append(EncontristaCsvRow(**dados))

        if not cabecalho_encontrado:
            raise ValueError("Cabeçalho do CSV de encontristas não encontrado")

    return linhas
