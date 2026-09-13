from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException
from app.integracao.regras.dtos import ItemDetalhamento
from app.models.lancamento import Lancamento
from app.services.auditoria.hooks import (
    _lancamento_ja_tem_biscoitos,
    _lancamento_ja_tem_taxa_cartao,
    _verificar_capacidade,
)
from app.services.detalhamento_service import DetalhamentoService
from app.utils.decimal_utils import to_decimal


class AplicacaoSink(ABC):
    """Abstrai onde a capacidade/flags do lançamento são lidas e se os itens
    da Etapa B são gravados de verdade ou só simulados -- é a ÚNICA diferença
    de fundo entre o fluxo real de auditoria e o dry-run de simulação; Etapa
    A, Etapa B, hooks de pós-processamento (biscoitos) e taxa de cartão são
    idênticos nos dois modos."""

    @abstractmethod
    def capacidade_restante(self, db: Session, lancamento: Lancamento) -> Decimal: ...

    @abstractmethod
    def ja_tem_taxa_cartao(self, db: Session, lancamento: Lancamento) -> bool: ...

    @abstractmethod
    def ja_tem_biscoitos(self, db: Session, lancamento: Lancamento) -> bool: ...

    def marcar_taxa_cartao_aplicada(self, lancamento: Lancamento) -> None:
        """No-op por padrão -- no modo real, a própria escrita no banco já
        garante que a próxima leitura de `ja_tem_taxa_cartao` venha True."""

    def marcar_biscoitos_aplicado(self, lancamento: Lancamento) -> None:
        """No-op por padrão -- idem, para o item de Biscoitos."""

    @abstractmethod
    def aplicar(
        self, db: Session, lancamento: Lancamento, itens: list[ItemDetalhamento]
    ) -> str | None:
        """Tenta gravar (ou simular) os itens contra a capacidade restante
        atual. Devolve o motivo do erro, ou None em sucesso."""


class PersistenciaSink(AplicacaoSink):
    """Modo real: lê tudo fresco do banco (aproveitando os column_property
    `soma_detalhamentos`, que reflete o estado atual após cada commit/flush)
    e grava via `DetalhamentoService.create`."""

    def capacidade_restante(self, db, lancamento):
        return to_decimal(lancamento.valor) - to_decimal(lancamento.soma_detalhamentos)

    def ja_tem_taxa_cartao(self, db, lancamento):
        return _lancamento_ja_tem_taxa_cartao(db, lancamento.id)

    def ja_tem_biscoitos(self, db, lancamento):
        return _lancamento_ja_tem_biscoitos(db, lancamento.id)

    def aplicar(self, db, lancamento, itens):
        erro = _verificar_capacidade(self.capacidade_restante(db, lancamento), itens)
        if erro:
            return erro

        for item in itens:
            try:
                DetalhamentoService.create(
                    db,
                    {
                        "lancamento_id": lancamento.id,
                        "tipo": item.tipo,
                        "referencia_id": item.referencia_id,
                        "valor": item.valor,
                        "descricao": item.descricao or "",
                    },
                )
            except BadRequestException as e:
                return str(e)

        return None


class SimulacaoSink(AplicacaoSink):
    """Modo dry-run: nunca grava. Inicializa capacidade/flags a partir do
    estado atual do banco na primeira vez que toca um lançamento, depois só
    decrementa/seta em memória -- escopado por `lancamento_id` (a simulação
    de hoje só lida com um lançamento por chamada)."""

    def __init__(self) -> None:
        self._capacidade: dict[int, Decimal] = {}
        self._tem_taxa: dict[int, bool] = {}
        self._tem_biscoitos: dict[int, bool] = {}

    def capacidade_restante(self, db, lancamento):
        if lancamento.id not in self._capacidade:
            self._capacidade[lancamento.id] = to_decimal(lancamento.valor) - to_decimal(
                lancamento.soma_detalhamentos
            )
        return self._capacidade[lancamento.id]

    def ja_tem_taxa_cartao(self, db, lancamento):
        if lancamento.id not in self._tem_taxa:
            self._tem_taxa[lancamento.id] = _lancamento_ja_tem_taxa_cartao(
                db, lancamento.id
            )
        return self._tem_taxa[lancamento.id]

    def ja_tem_biscoitos(self, db, lancamento):
        if lancamento.id not in self._tem_biscoitos:
            self._tem_biscoitos[lancamento.id] = _lancamento_ja_tem_biscoitos(
                db, lancamento.id
            )
        return self._tem_biscoitos[lancamento.id]

    def marcar_taxa_cartao_aplicada(self, lancamento):
        self._tem_taxa[lancamento.id] = True

    def marcar_biscoitos_aplicado(self, lancamento):
        self._tem_biscoitos[lancamento.id] = True

    def aplicar(self, db, lancamento, itens):
        erro = _verificar_capacidade(self.capacidade_restante(db, lancamento), itens)
        if erro:
            return erro
        self._capacidade[lancamento.id] -= sum(
            (item.valor for item in itens), Decimal(0)
        )
        return None
