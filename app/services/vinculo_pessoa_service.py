from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import TipoDetalhamento
from app.repositories.detalhamento_repository import DetalhamentoRepository
from app.utils.decimal_utils import TOLERANCIA_VINCULO

_TIPO_POR_MODELO = {
    Encontreiro: TipoDetalhamento.INSCRICAO_ENCONTREIRO,
    Encontrista: TipoDetalhamento.INSCRICAO_ENCONTRISTA,
}


def soma_bate_com_pagamento(
    soma: Decimal, pagamento: "Decimal | None", tolerancia: Decimal = TOLERANCIA_VINCULO
) -> bool:
    if pagamento is None:
        return False
    return soma >= pagamento - tolerancia


def calcular_saldo_pendente(soma: Decimal, pagamento: "Decimal | None") -> "Decimal | None":
    if pagamento is None:
        return None
    resto = pagamento - soma
    return resto if resto > 0 else Decimal("0")


def excede_saldo_pessoa(
    soma_outros: Decimal,
    novo_valor: Decimal,
    pagamento: "Decimal | None",
    tolerancia: Decimal = TOLERANCIA_VINCULO,
) -> bool:
    if pagamento is None:
        return False
    return soma_outros + novo_valor > pagamento + tolerancia


def enriquecer_vinculos(db: Session, pessoa) -> None:
    """Popula, no objeto ORM da pessoa, a lista completa de vínculos e mantém
    os campos legados (detalhamento_id, lancamento_vinculado) preenchidos com
    o vínculo mais antigo (mesmo critério do column_property
    Encontreiro/Encontrista.lancamento_vinculado_id em app/models/detalhamento.py)
    para nunca divergirem entre si. total_vinculado/saldo_pendente/auditado já
    vêm prontos no `pessoa` como column_property, computados na mesma query
    que trouxe o objeto — não recalculados aqui."""
    tipo = _TIPO_POR_MODELO[type(pessoa)]
    vinculos = DetalhamentoRepository.list_by_referencia(db, tipo, pessoa.id)

    pessoa.detalhamentos_vinculados = vinculos
    pessoa.lancamentos_vinculados = [v.lancamento for v in vinculos]

    primeiro = vinculos[0] if vinculos else None
    pessoa.detalhamento_id = primeiro.id if primeiro else None
    pessoa.lancamento_vinculado = primeiro.lancamento if primeiro else None
