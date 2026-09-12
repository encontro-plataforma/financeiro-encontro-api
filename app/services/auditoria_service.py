from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.integracao.regras.dtos import ItemDetalhamento
from app.models.detalhamento import Detalhamento
from app.models.enums import StatusLancamento
from app.repositories.lancamento_repository import LancamentoRepository
from app.services.auditoria.estrategias import (
    EstrategiaAuditoriaEncontreiro,
    EstrategiaAuditoriaEncontrista,
)
from app.services.auditoria.hooks import _inscricao_resumo_existente, _item_resposta
from app.services.auditoria.pipeline import PipelineAuditoria
from app.services.auditoria.relator import RelatorProcessamento, RelatorSimulacao
from app.services.auditoria.sink import PersistenciaSink, SimulacaoSink
from app.utils.decimal_utils import to_decimal


def _itens_existentes(db: Session, lancamento_id: int) -> list[dict]:
    detalhamentos = (
        db.query(Detalhamento).filter(Detalhamento.lancamento_id == lancamento_id).all()
    )
    return [
        _item_resposta(
            ItemDetalhamento(
                tipo=d.tipo,
                valor=to_decimal(d.valor),
                referencia_id=d.referencia_id,
                descricao=d.descricao,
            ),
            origem="EXISTENTE",
            inscricao=_inscricao_resumo_existente(db, d),
        )
        for d in detalhamentos
    ]


class AuditoriaService:
    @staticmethod
    def simular(db: Session, lancamento_id: int) -> dict:
        """Dry-run da auditoria para um único lançamento — não grava nada no
        banco. Compara com as pendências (Encontreiro/Encontrista) não
        auditadas atuais e devolve quais Detalhamentos a auditoria geraria,
        junto dos que já existem de fato."""
        lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
        if not lancamento:
            raise NotFoundException("Lançamento")

        itens_existentes = _itens_existentes(db, lancamento_id)

        base = {
            "lancamento_id": lancamento.id,
            "descricao": lancamento.descricao,
            "data_pagamento": lancamento.data_pagamento,
            "valor": to_decimal(lancamento.valor),
            "forma_pagamento": lancamento.forma_pagamento,
            "parcelas": lancamento.cart_parcelas,
            "status_lancamento": lancamento.status.value,
        }

        if lancamento.status == StatusLancamento.CONCILIADO:
            return {
                **base,
                "ja_conciliado": True,
                "detalhamentos": itens_existentes,
                "nao_incluidos": [],
            }

        pipeline = PipelineAuditoria(
            [EstrategiaAuditoriaEncontreiro(), EstrategiaAuditoriaEncontrista()]
        )
        resultado_pipeline = pipeline.executar(
            db,
            SimulacaoSink(),
            RelatorSimulacao(itens_existentes),
            lancamento_id_alvo=lancamento_id,
        )

        return {**base, "ja_conciliado": False, **resultado_pipeline}

    @staticmethod
    def processar(db: Session) -> dict:
        total_detalhamentos_antes = db.query(Detalhamento).count()

        pipeline = PipelineAuditoria(
            [EstrategiaAuditoriaEncontreiro(), EstrategiaAuditoriaEncontrista()]
        )
        resultado = pipeline.executar(db, PersistenciaSink(), RelatorProcessamento())

        db.commit()

        total_detalhamentos_depois = db.query(Detalhamento).count()
        extras_via_observacao = (
            total_detalhamentos_depois
            - total_detalhamentos_antes
            - resultado["vinculados_encontreiro"]
            - resultado["vinculados_encontrista"]
        )

        resultado["detalhamentos_extras_via_observacao"] = extras_via_observacao
        resultado["mensagem"] = (
            f"Auditoria concluída. {resultado['vinculados_encontreiro']} encontreiro(s) e "
            f"{resultado['vinculados_encontrista']} encontrista(s) vinculados, "
            f"{extras_via_observacao} detalhamento(s) extra(s) via observação, "
            f"{resultado['nao_auditados']} inscrição(ões) ainda não auditada(s)."
        )
        return resultado
