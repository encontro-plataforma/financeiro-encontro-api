from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    and_,
    exists,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import TipoDetalhamento
from app.models.lancamento import Lancamento

tipo_detalhamento_enum = ENUM(
    TipoDetalhamento, name="tipo_detalhamento", create_type=True
)


class Detalhamento(Base):
    __tablename__ = "detalhamentos"

    id = Column(Integer, primary_key=True)
    lancamento_id = Column(
        Integer,
        ForeignKey("lancamentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo = Column(tipo_detalhamento_enum, nullable=False)
    referencia_id = Column(Integer, nullable=True, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    # Só usado quando tipo é OFERTA/OUTRO. Para INSCRICAO_*, a "observação"
    # mostrada vem ao vivo do Encontreiro/Encontrista referenciado (sem
    # duplicar/sincronizar texto) — ver DetalhamentoService/AuditoriaService.
    descricao = Column(String(500), nullable=False, server_default="")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lancamento = relationship("Lancamento")


# "auditado" não é uma coluna persistida: é calculado direto no SELECT (sem
# N+1). Definido aqui (e não nos models Encontreiro/Encontrista) para evitar
# import circular com Detalhamento.
#
# Regra normal (ficha sem "pagamento múltiplo" na observação): a mesma de
# sempre -- ter QUALQUER Detalhamento vinculado já basta pra considerar
# auditado, sem comparar soma nenhuma.
#
# Ficha de pagamento múltiplo (observação contém "pagamento múltiplo"): aqui
# sim a soma importa, porque o Etapa A da auditoria automática pula essas
# fichas de propósito (só processa 1 lançamento por vez) e deixa o vínculo
# dos vários lançamentos pro usuário fazer manualmente -- só terminou quando
# TODOS os lançamentos esperados tiverem sido vinculados. A comparação é feita
# contra o valor CHEIO (bruto) de cada Lancamento distinto vinculado à pessoa,
# não contra a soma dos Detalhamento dela -- isso importa sobretudo pra
# lançamentos de cartão, cuja taxa da maquininha nunca vira Detalhamento (só
# é informativa no relatório, via `Lancamento.cart_taxa`): somar só os
# Detalhamento da pessoa bateria igual com o bruto nesse caso específico, mas
# manter a comparação contra o Lancamento cheio evita reintroduzir esse tipo
# de divergência se a extração um dia passar a usar um valor líquido.
_TOLERANCIA_AUDITORIA = Decimal("0.01")

# Mesmo padrão de app/integracao/regras/deteccao_pagamento_multiplo.py
# (case/acento-insensitive em "pagamento(s) multiplo(s)"), mas expresso em SQL
# porque alimenta um column_property (usado como filtro pelo repositório, ex.
# `Encontreiro.auditado.is_(...)`) -- não dá pra rodar em Python por linha.
_PADRAO_PAGAMENTO_MULTIPLO_SQL = r"pagamentos?\s+m[uUúÚ]ltiplos?"


def _existe_vinculo(tipo, referencia_col):
    return exists().where(
        and_(Detalhamento.tipo == tipo, Detalhamento.referencia_id == referencia_col)
    )


def _soma_lancamentos_vinculados(tipo, referencia_col):
    """Soma do valor cheio (bruto) de cada Lancamento distinto vinculado a
    essa pessoa -- ver nota acima sobre por que não é a soma dos Detalhamento
    dela."""
    lancamentos_da_pessoa = (
        select(Detalhamento.lancamento_id)
        .where(Detalhamento.tipo == tipo, Detalhamento.referencia_id == referencia_col)
        .correlate_except(Detalhamento)
    )

    return (
        select(func.coalesce(func.sum(Lancamento.valor), 0))
        .where(Lancamento.id.in_(lancamentos_da_pessoa))
        .correlate_except(Lancamento)
        .scalar_subquery()
    )


def _is_pagamento_multiplo(observacao_col):
    return func.coalesce(observacao_col.op("~*")(_PADRAO_PAGAMENTO_MULTIPLO_SQL), False)


def _auditado(tipo, referencia_col, pagamento_col, observacao_col):
    soma_ok = _soma_lancamentos_vinculados(tipo, referencia_col) >= (
        func.coalesce(pagamento_col, 0) - _TOLERANCIA_AUDITORIA
    )
    return and_(
        _existe_vinculo(tipo, referencia_col),
        # "se não é pagamento múltiplo, só de ter vínculo já é auditado;
        # se é, só quando a soma dos lançamentos vinculados cobrir o pagamento"
        or_(~_is_pagamento_multiplo(observacao_col), soma_ok),
    )


Encontreiro.is_pagamento_multiplo = column_property(
    _is_pagamento_multiplo(Encontreiro.observacao)
)
Encontrista.is_pagamento_multiplo = column_property(
    _is_pagamento_multiplo(Encontrista.observacao)
)

Encontreiro.auditado = column_property(
    _auditado(
        TipoDetalhamento.INSCRICAO_ENCONTREIRO,
        Encontreiro.id,
        Encontreiro.pagamento,
        Encontreiro.observacao,
    )
)

Encontrista.auditado = column_property(
    _auditado(
        TipoDetalhamento.INSCRICAO_ENCONTRISTA,
        Encontrista.id,
        Encontrista.pagamento,
        Encontrista.observacao,
    )
)

# Quantidade de lançamentos vinculados — usada pela listagem pra saber, sem
# N+1, se deve habilitar o botão de "lançamentos vinculados" (agora um
# submenu, já que pode haver mais de um). O detalhe completo de cada vínculo
# vem por fora, via GET /detalhamentos/all?referencia_id=&tipo=.
Encontreiro.quantidade_lancamentos_vinculados = column_property(
    select(func.count(Detalhamento.id))
    .where(
        Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO,
        Detalhamento.referencia_id == Encontreiro.id,
    )
    .correlate_except(Detalhamento)
    .scalar_subquery()
)

Encontrista.quantidade_lancamentos_vinculados = column_property(
    select(func.count(Detalhamento.id))
    .where(
        Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA,
        Detalhamento.referencia_id == Encontrista.id,
    )
    .correlate_except(Detalhamento)
    .scalar_subquery()
)

# Mesmo motivo/padrão acima: evita N+1 nos cards de conciliação, que
# precisam saber quantos Detalhamentos e qual a soma já vinculados a
# cada Lancamento sem uma chamada extra por card.
Lancamento.quantidade_detalhamentos = column_property(
    select(func.count(Detalhamento.id))
    .where(Detalhamento.lancamento_id == Lancamento.id)
    .correlate_except(Detalhamento)
    .scalar_subquery()
)

Lancamento.soma_detalhamentos = column_property(
    select(func.coalesce(func.sum(Detalhamento.valor), 0))
    .where(Detalhamento.lancamento_id == Lancamento.id)
    .correlate_except(Detalhamento)
    .scalar_subquery()
)
