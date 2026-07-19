from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.enums import TipoLancamento
from app.models.finalidade import Finalidade
from app.models.lancamento import Lancamento


def _receitas_expr():
    return func.coalesce(
        func.sum(case((Lancamento.tipo == TipoLancamento.RECEITA, Lancamento.valor), else_=0)),
        0,
    )


def _despesas_expr():
    return func.coalesce(
        func.sum(case((Lancamento.tipo == TipoLancamento.DESPESA, Lancamento.valor), else_=0)),
        0,
    )


def _apply_filters(query, params):
    if params.data_inicio:
        query = query.filter(Lancamento.data_pagamento >= params.data_inicio)
    if params.data_fim:
        query = query.filter(Lancamento.data_pagamento <= params.data_fim)

    if params.forma_pagamento:
        query = query.filter(Lancamento.forma_pagamento.in_(params.forma_pagamento))

    if params.finalidade_id:
        query = query.filter(Lancamento.finalidade_id.in_(params.finalidade_id))

    if params.tipo:
        query = query.filter(Lancamento.tipo == params.tipo)

    if params.status:
        query = query.filter(Lancamento.status == params.status)

    return query


class DashboardRepository:

    @staticmethod
    def get_totais(db: Session, params):
        query = db.query(
            _receitas_expr().label("total_receitas"),
            _despesas_expr().label("total_despesas"),
            func.count(Lancamento.id).label("quantidade"),
        )
        return _apply_filters(query, params).one()

    @staticmethod
    def get_por_dia(db: Session, params):
        dia_col = func.date_trunc("day", Lancamento.data_pagamento).label("dia")
        query = db.query(
            dia_col,
            _receitas_expr().label("total_receitas"),
            _despesas_expr().label("total_despesas"),
        ).group_by(dia_col).order_by(dia_col)
        return _apply_filters(query, params).all()

    @staticmethod
    def get_por_mes(db: Session, params):
        mes_col = func.date_trunc("month", Lancamento.data_pagamento).label("mes")
        query = db.query(
            mes_col,
            _receitas_expr().label("total_receitas"),
            _despesas_expr().label("total_despesas"),
        ).group_by(mes_col).order_by(mes_col)
        return _apply_filters(query, params).all()

    @staticmethod
    def get_por_finalidade(db: Session, params):
        nome_col = func.coalesce(Finalidade.nome, "Não Conciliado").label("nome")
        total_col = func.sum(Lancamento.valor).label("total_valor")
        count_col = func.count(Lancamento.id).label("quantidade")

        query = db.query(
            Lancamento.finalidade_id,
            nome_col,
            total_col,
            count_col,
        ).outerjoin(Finalidade, Lancamento.finalidade_id == Finalidade.id)

        query = _apply_filters(query, params)
        query = query.group_by(Lancamento.finalidade_id, Finalidade.nome)
        query = query.order_by(func.sum(Lancamento.valor).desc())

        return query.all()
