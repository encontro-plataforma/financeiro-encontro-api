from dataclasses import replace
from decimal import Decimal

from sqlalchemy.orm import Session

from app.integracao.regras.dtos import ItemDetalhamento, PendenciaAuditoria
from app.models.detalhamento import Detalhamento
from app.models.encontrista import Encontrista
from app.models.enums import TipoDetalhamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository
from app.utils.decimal_utils import to_decimal

_TOLERANCIA = Decimal("0.01")

_LABEL_TIPO_PESSOA = {
    TipoDetalhamento.INSCRICAO_ENCONTREIRO: "ENCONTREIRO",
    TipoDetalhamento.INSCRICAO_ENCONTRISTA: "ENCONTRISTA",
}


def _to_pendencia_auditoria(inscricao_pendente) -> PendenciaAuditoria:
    return PendenciaAuditoria(
        id=inscricao_pendente.id,
        nome=inscricao_pendente.nome,
        nome_pagador=inscricao_pendente.nome_pagador,
        dt_pagamento=inscricao_pendente.dt_pagamento,
        pagamento=to_decimal(inscricao_pendente.pagamento),
        observacao=inscricao_pendente.observacao,
    )


def _verificar_capacidade(capacidade: Decimal, itens: list[ItemDetalhamento]) -> str | None:
    """Confere se a soma dos itens cabe na capacidade restante do lançamento.
    Devolve o motivo do erro (ou None se couber) — usado tanto na criação real
    quanto na simulação de auditoria."""
    soma_itens = sum((item.valor for item in itens), Decimal(0))
    if soma_itens > capacidade + _TOLERANCIA:
        return (
            f"Os detalhamentos identificados na observação somam R$ {soma_itens:.2f}, "
            f"mas o lançamento só tem R$ {capacidade:.2f} de capacidade restante."
        )
    return None


_NOME_REGRA_BISCOITOS = "Biscoitos"
_PREFIXO_DESCRICAO_BISCOITOS = "Biscoitos da ficha "


def _lancamento_ja_tem_biscoitos(db: Session, lancamento_id: int) -> bool:
    return (
        db.query(Detalhamento)
        .filter(
            Detalhamento.lancamento_id == lancamento_id,
            Detalhamento.tipo == TipoDetalhamento.OUTRO,
            Detalhamento.descricao.like(f"{_PREFIXO_DESCRICAO_BISCOITOS}%"),
        )
        .first()
        is not None
    )


def _descricao_biscoitos(db: Session, encontrista: Encontrista) -> str:
    padrinho = EncontreiroRepository.get_by_id(db, encontrista.padrinho_id)
    nome_padrinho = padrinho.nome if padrinho else "(padrinho removido)"
    return f"{_PREFIXO_DESCRICAO_BISCOITOS}{encontrista.id} - {nome_padrinho}"


def _aplicar_biscoitos(
    db: Session,
    itens_com_origem: list[tuple[ItemDetalhamento, object]],
    encontrista: Encontrista,
    ja_tem_biscoitos: bool,
) -> tuple[list[tuple[ItemDetalhamento, object]], bool]:
    """Biscoitos é um item físico só reconhecido UMA VEZ por lançamento:
    quando várias fichas de Encontrista compartilham o mesmo pagamento, só a
    primeira que casar recebe o item de
    Biscoitos; as próximas não repetem, mesmo que a própria observação delas
    também mencione biscoito. A descrição identifica de qual ficha veio (id
    da ficha + nome do padrinho), já que o item de Biscoitos não carrega
    `referencia_id`. Devolve os itens ajustados e se o item foi aplicado
    agora (pra quem chama marcar o lançamento como "já tem biscoitos")."""
    aplicado_agora = False
    ajustados: list[tuple[ItemDetalhamento, object]] = []
    for item, origem in itens_com_origem:
        if origem != _NOME_REGRA_BISCOITOS:
            ajustados.append((item, origem))
            continue
        if ja_tem_biscoitos:
            continue
        ajustados.append((replace(item, descricao=_descricao_biscoitos(db, encontrista)), origem))
        aplicado_agora = True
    return ajustados, aplicado_agora


def _inscricao_resumo(
    tipo: TipoDetalhamento,
    pessoa_id: int,
    nome: str,
    pagamento,
    observacao: str | None,
) -> dict | None:
    if tipo not in _LABEL_TIPO_PESSOA:
        return None
    return {
        "id": pessoa_id,
        "nome": nome,
        "tipo": _LABEL_TIPO_PESSOA[tipo],
        "pagamento": to_decimal(pagamento) if pagamento is not None else None,
        "observacao": observacao,
    }


def _inscricao_resumo_existente(db: Session, detalhamento: Detalhamento) -> dict | None:
    if detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTREIRO:
        pessoa = EncontreiroRepository.get_by_id(db, detalhamento.referencia_id)
    elif detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA:
        pessoa = EncontristaRepository.get_by_id(db, detalhamento.referencia_id)
    else:
        return None

    if not pessoa:
        return None

    return _inscricao_resumo(
        detalhamento.tipo, pessoa.id, pessoa.nome, pessoa.pagamento, pessoa.observacao
    )


def _item_resposta(
    item: ItemDetalhamento, origem: str, inscricao: dict | None, regra: str | None = None
) -> dict:
    return {
        "tipo": item.tipo,
        "valor": item.valor,
        "referencia_id": item.referencia_id,
        "descricao": item.descricao or "",
        "origem": origem,
        "regra": regra,
        "inscricao": inscricao,
    }
