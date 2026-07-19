from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:

    @staticmethod
    def get_totais(db: Session, params):
        row = DashboardRepository.get_totais(db, params)
        total_receitas = float(row.total_receitas)
        total_despesas = float(row.total_despesas)
        return {
            "total_receitas": total_receitas,
            "total_despesas": total_despesas,
            "saldo": total_receitas - total_despesas,
            "quantidade": row.quantidade,
        }

    @staticmethod
    def get_por_dia(db: Session, params):
        rows = DashboardRepository.get_por_dia(db, params)
        return [
            {
                "dia": row.dia.strftime("%Y-%m-%d"),
                "total_receitas": float(row.total_receitas),
                "total_despesas": float(row.total_despesas),
                "saldo": float(row.total_receitas) - float(row.total_despesas),
            }
            for row in rows
        ]

    @staticmethod
    def get_por_mes(db: Session, params):
        rows = DashboardRepository.get_por_mes(db, params)
        return [
            {
                "mes": row.mes.strftime("%Y-%m"),
                "total_receitas": float(row.total_receitas),
                "total_despesas": float(row.total_despesas),
                "saldo": float(row.total_receitas) - float(row.total_despesas),
            }
            for row in rows
        ]

    @staticmethod
    def get_por_finalidade(db: Session, params):
        rows = DashboardRepository.get_por_finalidade(db, params)
        return [
            {
                "finalidade_id": row.finalidade_id,
                "nome": row.nome or "Não Conciliado",
                "total_valor": float(row.total_valor),
                "quantidade": row.quantidade,
            }
            for row in rows
        ]
