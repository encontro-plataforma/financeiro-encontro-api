from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.enums import FormaPagamento


@dataclass
class CartaoLinhaDTO:
    """Uma venda aprovada do extrato da maquininha (PagBank) -- sem nome do
    pagador, só dados da venda em si."""
    data: date
    bandeira: str
    forma_pagamento: FormaPagamento
    num_parcelas: int
    valor_bruto: Decimal
    valor_taxa: Decimal
    valor_liquido: Decimal
    status: str
    codigo_transacao: str
    linha_csv: int
