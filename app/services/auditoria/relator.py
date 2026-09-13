from abc import ABC, abstractmethod

from app.integracao.regras.deteccao_pagamento_multiplo import MOTIVO_PAGAMENTO_MULTIPLO
from app.services.auditoria.hooks import _inscricao_resumo, _item_resposta
from app.services.common.tipo_pessoa_config import TipoPessoaConfig
from app.utils.decimal_utils import to_decimal

_REGRA_FALLBACK = "FALLBACK"


class RelatorAuditoria(ABC):
    """Formata o resultado da auditoria sem que o pipeline precise saber se
    está em modo real (grava no banco) ou em modo simulação (dry-run)."""

    @abstractmethod
    def pulada_pagamento_multiplo(self, config: TipoPessoaConfig, pendente) -> None: ...

    @abstractmethod
    def sem_lancamento(self, config: TipoPessoaConfig, pendente) -> None: ...

    @abstractmethod
    def com_erro(
        self, config: TipoPessoaConfig, pendente, lancamento, motivo: str
    ) -> None: ...

    @abstractmethod
    def vinculada(
        self, config: TipoPessoaConfig, pendente, lancamento, itens_com_origem
    ) -> None: ...

    @abstractmethod
    def resultado(self) -> dict: ...


class RelatorProcessamento(RelatorAuditoria):
    """Reconstrói exatamente as chaves de contagem que
    `AuditoriaService.processar` sempre devolveu -- `mensagem` e
    `detalhamentos_extras_via_observacao` continuam montados fora, em
    `AuditoriaService.processar`, por dependerem do diff de contagem global
    de `Detalhamento`, fora do escopo por-pendência do relator."""

    def __init__(self) -> None:
        self._avaliados = 0
        self._vinculados: dict[str, int] = {}
        self._nao_auditados: list[dict] = []

    def pulada_pagamento_multiplo(self, config, pendente):
        self._avaliados += 1
        self._nao_auditados.append(
            {
                "tipo": config.tipo_detalhamento.value,
                "id": pendente.id,
                "nome": pendente.nome,
                "motivo": MOTIVO_PAGAMENTO_MULTIPLO,
            }
        )

    def sem_lancamento(self, config, pendente):
        self._avaliados += 1
        self._nao_auditados.append(
            {
                "tipo": config.tipo_detalhamento.value,
                "id": pendente.id,
                "nome": pendente.nome,
            }
        )

    def com_erro(self, config, pendente, lancamento, motivo):
        self._avaliados += 1
        self._nao_auditados.append(
            {
                "tipo": config.tipo_detalhamento.value,
                "id": pendente.id,
                "nome": pendente.nome,
                "lancamento_id": lancamento.id,
                "motivo": motivo,
            }
        )

    def vinculada(self, config, pendente, lancamento, itens_com_origem):
        self._avaliados += 1
        self._vinculados[config.label] = self._vinculados.get(config.label, 0) + 1

    def resultado(self) -> dict:
        return {
            "avaliados": self._avaliados,
            "vinculados_encontreiro": self._vinculados.get("ENCONTREIRO", 0),
            "vinculados_encontrista": self._vinculados.get("ENCONTRISTA", 0),
            "nao_auditados": len(self._nao_auditados),
            "detalhes_nao_auditados": self._nao_auditados,
        }


class RelatorSimulacao(RelatorAuditoria):
    """Formata o resultado do dry-run de um único lançamento
    (`AuditoriaService.simular`) -- só reporta pendências que a Etapa A
    (Match) já resolveu para ESTE lançamento (`lancamento_id_alvo` no
    pipeline já filtra as demais antes de chamar qualquer callback aqui);
    uma pendência sem match nenhum, ou pulada por pagamento múltiplo, é
    irrelevante pra esta simulação específica e não aparece em
    `nao_incluidos` -- mesmo comportamento que o dry-run sempre teve."""

    def __init__(self, itens_existentes: list[dict]) -> None:
        self._itens_existentes = itens_existentes
        self._detalhamentos_simulados: list[dict] = []
        self._nao_incluidos: list[dict] = []

    def pulada_pagamento_multiplo(self, config, pendente) -> None:
        pass

    def sem_lancamento(self, config, pendente) -> None:
        pass

    def com_erro(self, config, pendente, lancamento, motivo):
        self._nao_incluidos.append(
            {
                "tipo": config.label,
                "id": pendente.id,
                "nome": pendente.nome,
                "pagamento": to_decimal(pendente.pagamento),
                "observacao": pendente.observacao,
                "motivo": motivo,
            }
        )

    def vinculada(self, config, pendente, lancamento, itens_com_origem):
        for item, nome_regra in itens_com_origem:
            inscricao = (
                _inscricao_resumo(
                    item.tipo,
                    pendente.id,
                    pendente.nome,
                    pendente.pagamento,
                    pendente.observacao,
                )
                if item.referencia_id is not None
                else None
            )
            self._detalhamentos_simulados.append(
                _item_resposta(
                    item,
                    origem="SIMULADO",
                    inscricao=inscricao,
                    regra=nome_regra or _REGRA_FALLBACK,
                )
            )

    def resultado(self) -> dict:
        return {
            "detalhamentos": self._itens_existentes + self._detalhamentos_simulados,
            "nao_incluidos": self._nao_incluidos,
        }
