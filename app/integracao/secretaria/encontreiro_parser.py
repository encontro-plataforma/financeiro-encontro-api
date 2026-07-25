import csv
import io
from dataclasses import dataclass
from typing import Dict, List, Optional

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
}


@dataclass
class EncontreiroCsvRow:
    linha: int
    id: int
    dt_inscricao: Optional[str] = None
    nome: Optional[str] = None
    apelido: Optional[str] = None
    instagram: Optional[str] = None
    telefone: Optional[str] = None
    estado_civil: Optional[str] = None
    igreja: Optional[str] = None
    religiao: Optional[str] = None
    contato_emerg: Optional[str] = None
    nome_emerg: Optional[str] = None
    parentesco_emerg: Optional[str] = None
    alergia_comorbidade: Optional[str] = None
    equipe_nome: Optional[str] = None
    camisa: Optional[str] = None
    situacao_camisa: Optional[str] = None
    veiculo: Optional[str] = None
    dt_pagamento: Optional[str] = None
    nome_pagador: Optional[str] = None
    pagamento: Optional[str] = None
    observacao: Optional[str] = None


def _mapear_cabecalho(row: List[str]) -> Dict[int, str]:
    indice_para_campo = {}
    for idx, celula in enumerate(row):
        campo = _CABECALHO_PARA_CAMPO.get(normalizar_cabecalho(celula))
        if campo:
            indice_para_campo[idx] = campo
    return indice_para_campo


def parse(conteudo: str) -> List[EncontreiroCsvRow]:
    linhas: List[EncontreiroCsvRow] = []

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
                        raise ValueError("Cabeçalho do CSV de encontreiros não reconhecido")
                continue

            if not row or not any(c.strip() for c in row):
                continue

            dados = {"linha": linha_num}
            for idx, campo in indice_para_campo.items():
                valor = row[idx].strip() if idx < len(row) else ""
                dados[campo] = valor or None

            id_bruto = dados.pop("id", None)
            if not id_bruto:
                raise ValueError(f"Linha {linha_num}: coluna ID vazia")
            try:
                dados["id"] = int(id_bruto)
            except ValueError as exc:
                raise ValueError(f"Linha {linha_num}: ID inválido '{id_bruto}'") from exc

            linhas.append(EncontreiroCsvRow(**dados))

        if indice_para_campo is None:
            raise ValueError("Cabeçalho do CSV de encontreiros não encontrado")

    return linhas
