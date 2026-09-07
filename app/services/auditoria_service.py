from dataclasses import replace
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.integracao.regras.dtos import (
    CandidatoLancamento,
    ItemDetalhamento,
    PendenciaAuditoria,
)
from app.integracao.regras.motor_extracao import extrair_detalhamentos_com_origem
from app.integracao.regras.motor_match import selecionar_lancamento
from app.models.detalhamento import Detalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.models.enums import (
    EscopoRegraGrupo,
    StatusLancamento,
    TipoDetalhamento,
    TipoLancamento,
)
from app.models.lancamento import Lancamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository
from app.repositories.lancamento_repository import LancamentoRepository
from app.repositories.regra_repository import RegraRepository
from app.services.detalhamento_service import DetalhamentoService
from app.utils.decimal_utils import to_decimal

_TOLERANCIA = Decimal("0.01")

_ESCOPO_POR_TIPO = {
    TipoDetalhamento.INSCRICAO_ENCONTREIRO: EscopoRegraGrupo.EXTRACAO_ENCONTREIRO,
    TipoDetalhamento.INSCRICAO_ENCONTRISTA: EscopoRegraGrupo.EXTRACAO_ENCONTRISTA,
}

_LABEL_TIPO_PESSOA = {
    TipoDetalhamento.INSCRICAO_ENCONTREIRO: "ENCONTREIRO",
    TipoDetalhamento.INSCRICAO_ENCONTRISTA: "ENCONTRISTA",
}

_MOTIVO_SEM_VALOR_IDENTIFICADO = (
    "Lançamento já possui outra inscrição vinculada e a observação "
    "não permite identificar o valor desta pessoa."
)


def _to_pendencia_auditoria(inscricao_pendente) -> PendenciaAuditoria:
    return PendenciaAuditoria(
        id=inscricao_pendente.id,
        nome=inscricao_pendente.nome,
        nome_pagador=inscricao_pendente.nome_pagador,
        dt_pagamento=inscricao_pendente.dt_pagamento,
        pagamento=to_decimal(inscricao_pendente.pagamento),
        observacao=inscricao_pendente.observacao,
    )


def _buscar_candidatos(
    db: Session, dt_pagamento, pagamento: Decimal
) -> list[Lancamento]:
    return (
        db.query(Lancamento)
        .filter(
            Lancamento.data_pagamento == dt_pagamento,
            Lancamento.tipo == TipoLancamento.RECEITA,
            Lancamento.status == StatusLancamento.NAO_CONCILIADO,
            Lancamento.valor >= pagamento - _TOLERANCIA,
        )
        .all()
    )


def _selecionar_lancamento(
    db: Session, pendencia: PendenciaAuditoria
) -> Lancamento | None:
    """Etapa A (Match): decide qual Lancamento corresponde à pendência."""
    candidatos_orm = _buscar_candidatos(db, pendencia.dt_pagamento, pendencia.pagamento)
    if not candidatos_orm:
        return None

    candidatos_dto = [
        CandidatoLancamento(
            id=candidato.id,
            descricao=candidato.descricao,
            valor=to_decimal(candidato.valor),
            soma_detalhamentos=to_decimal(candidato.soma_detalhamentos),
            forma_pagamento=candidato.forma_pagamento,
            cart_parcelas=candidato.cart_parcelas,
        )
        for candidato in candidatos_orm
    ]

    ## Parte A
    escolhido = selecionar_lancamento(pendencia, candidatos_dto)
    if not escolhido:
        return None

    por_id = {l.id: l for l in candidatos_orm}
    return por_id[escolhido.id]


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


def _criar_detalhamentos(
    db: Session, lancamento: Lancamento, itens: list[ItemDetalhamento]
) -> str | None:
    """Cria os itens da Etapa B (Extração). Se a soma exceder a capacidade
    restante do lançamento, não cria nada e devolve o motivo do erro."""
    capacidade = to_decimal(lancamento.valor) - to_decimal(
        lancamento.soma_detalhamentos
    )
    erro = _verificar_capacidade(capacidade, itens)
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


_DESCRICAO_TAXA_CARTAO = "Taxa do Cartão"


def _lancamento_ja_tem_taxa_cartao(db: Session, lancamento_id: int) -> bool:
    return (
        db.query(Detalhamento)
        .filter(
            Detalhamento.lancamento_id == lancamento_id,
            Detalhamento.tipo == TipoDetalhamento.OUTRO,
            Detalhamento.descricao == _DESCRICAO_TAXA_CARTAO,
        )
        .first()
        is not None
    )


def _aplicar_taxa_cartao(
    itens_com_origem: list[tuple[ItemDetalhamento, object]],
    taxa: Decimal,
    ja_tem_taxa: bool,
    origem_taxa: object = None,
) -> list[tuple[ItemDetalhamento, object]]:
    """Ajusta os itens extraídos pra refletir a taxa da maquininha de um
    lançamento de cartão. No PRIMEIRO Detalhamento vinculado a este
    lançamento, desconta a taxa do item de Inscrição e acrescenta um item
    'Taxa do Cartão' -- a igreja só fica com o valor líquido, o resto é taxa
    da maquininha, então a soma final continua batendo com o valor bruto do
    lançamento. Nos PRÓXIMOS Detalhamentos do MESMO lançamento (pagamento
    compartilhado por várias pessoas), a taxa já foi contabilizada no
    primeiro match -- os itens seguintes usam o valor cheio, sem descontar
    nem repetir a taxa."""
    if ja_tem_taxa:
        return itens_com_origem

    ajustados = list(itens_com_origem)
    indice_inscricao = next(
        (i for i, (item, _) in enumerate(ajustados) if item.tipo in _LABEL_TIPO_PESSOA),
        0 if ajustados else None,
    )
    if indice_inscricao is not None:
        item, origem = ajustados[indice_inscricao]
        ajustados[indice_inscricao] = (replace(item, valor=item.valor - taxa), origem)

    ajustados.append(
        (
            ItemDetalhamento(
                tipo=TipoDetalhamento.OUTRO,
                valor=taxa,
                referencia_id=None,
                descricao=_DESCRICAO_TAXA_CARTAO,
            ),
            origem_taxa,
        )
    )
    return ajustados


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
    """Biscoitos é um item físico só reconhecido UMA VEZ por lançamento —
    mesma lógica da taxa de cartão: quando várias fichas de Encontrista
    compartilham o mesmo pagamento, só a primeira que casar recebe o item de
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


def _processar_pendentes(
    db: Session, modelo: Encontreiro | Encontrista, tipo_detalhamento: TipoDetalhamento
):
    vinculados = 0
    nao_auditados = []

    insc_pendentes: list[Encontreiro | Encontrista] = (
        db.query(modelo)
        .filter(
            modelo.auditado.is_(False),
            modelo.dt_pagamento.isnot(None),
            modelo.pagamento.isnot(None),
            modelo.pagamento > 0,
        )
        .order_by(modelo.dt_pagamento)
        .all()
    )

    for inscricao_pendente in insc_pendentes:
        ## 1 - Match de lancamento (Etapa A)
        pendencia_auditoria = _to_pendencia_auditoria(inscricao_pendente)
        lancamento = _selecionar_lancamento(db, pendencia_auditoria)

        if not lancamento:
            nao_auditados.append(
                {
                    "tipo": tipo_detalhamento.value,
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                }
            )
            continue

        ## 2 - Extração de detalhamentos - Regras (Etapa B)
        valor_resto_lancamento = to_decimal(lancamento.valor) - to_decimal(
            lancamento.soma_detalhamentos
        )
        permite_fallback = valor_resto_lancamento >= (
            to_decimal(lancamento.valor) - _TOLERANCIA
        )

        # Lançamento veio do extrato de cartão: a igreja só fica com o valor
        # líquido (o resto é taxa da maquininha), então a extração usa o
        # líquido no lugar do bruto. A Etapa A (match), acima, já rodou com o
        # pagamento original (bruto), que é o que bate com o valor do lançamento.
        eh_cartao = lancamento.cart_taxa is not None
        pendencia_para_extracao = (
            replace(
                pendencia_auditoria, pagamento=to_decimal(lancamento.cart_valor_liquido)
            )
            if eh_cartao
            else pendencia_auditoria
        )

        grupoRegras = RegraRepository.list_ativos_por_escopos(
            db, [_ESCOPO_POR_TIPO[tipo_detalhamento]]
        )
        itens_com_origem = extrair_detalhamentos_com_origem(
            pendencia_para_extracao, grupoRegras, tipo_detalhamento, permite_fallback
        )

        if not itens_com_origem:
            nao_auditados.append(
                {
                    "tipo": tipo_detalhamento.value,
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                    "lancamento_id": lancamento.id,
                    "motivo": _MOTIVO_SEM_VALOR_IDENTIFICADO,
                }
            )
            continue

        if tipo_detalhamento == TipoDetalhamento.INSCRICAO_ENCONTRISTA:
            ja_tem_biscoitos = _lancamento_ja_tem_biscoitos(db, lancamento.id)
            itens_com_origem, _ = _aplicar_biscoitos(
                db, itens_com_origem, inscricao_pendente, ja_tem_biscoitos
            )

        if eh_cartao:
            ja_tem_taxa = _lancamento_ja_tem_taxa_cartao(db, lancamento.id)
            itens_com_origem = _aplicar_taxa_cartao(
                itens_com_origem, to_decimal(lancamento.cart_taxa), ja_tem_taxa
            )

        itens = [item for item, _ in itens_com_origem]

        error_message = _criar_detalhamentos(db, lancamento, itens)

        if error_message:
            nao_auditados.append(
                {
                    "tipo": tipo_detalhamento.value,
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                    "lancamento_id": lancamento.id,
                    "motivo": error_message,
                }
            )
            continue

        vinculados += 1

    return len(insc_pendentes), vinculados, nao_auditados


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


_REGRA_TAXA_CARTAO = "Taxa do Cartão (automático)"
_REGRA_FALLBACK = "FALLBACK"


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


def _candidatos_do_lancamento(
    db: Session, lancamento_id: int
) -> list[tuple[TipoDetalhamento, Encontreiro | Encontrista]]:
    """Entre todas as pendências (Encontreiro/Encontrista) ainda não
    auditadas, roda a mesma Etapa A (Match) do fluxo real e devolve só as
    que, hoje, resolveriam justamente para este lançamento — na mesma ordem
    de processamento do fluxo real (Encontreiro antes de Encontrista, cada
    grupo por id)."""
    candidatos: list[tuple[TipoDetalhamento, Encontreiro | Encontrista]] = []

    for modelo, tipo_detalhamento in (
        (Encontreiro, TipoDetalhamento.INSCRICAO_ENCONTREIRO),
        (Encontrista, TipoDetalhamento.INSCRICAO_ENCONTRISTA),
    ):
        pendentes = (
            db.query(modelo)
            .filter(
                modelo.auditado.is_(False),
                modelo.dt_pagamento.isnot(None),
                modelo.pagamento.isnot(None),
                modelo.pagamento > 0,
            )
            .order_by(modelo.id)
            .all()
        )
        for pendente in pendentes:
            selecionado = _selecionar_lancamento(db, _to_pendencia_auditoria(pendente))
            if selecionado and selecionado.id == lancamento_id:
                candidatos.append((tipo_detalhamento, pendente))

    return candidatos


def _simular_auditoria(db: Session, lancamento_id: int) -> dict:
    """Dry-run da auditoria para um único lançamento — não grava nada no
    banco. Compara com as pendências (Encontreiro/Encontrista) não auditadas
    atuais e devolve quais Detalhamentos a auditoria geraria, junto dos que
    já existem de fato."""
    lancamento = LancamentoRepository.get_by_id(db, lancamento_id)
    if not lancamento:
        raise NotFoundException("Lançamento")

    detalhamentos_existentes = (
        db.query(Detalhamento)
        .filter(Detalhamento.lancamento_id == lancamento_id)
        .all()
    )
    itens_existentes = [
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
        for d in detalhamentos_existentes
    ]

    if lancamento.status == StatusLancamento.CONCILIADO:
        return {
            "lancamento_id": lancamento.id,
            "descricao": lancamento.descricao,
            "data_pagamento": lancamento.data_pagamento,
            "valor": to_decimal(lancamento.valor),
            "forma_pagamento": lancamento.forma_pagamento,
            "parcelas": lancamento.cart_parcelas,
            "status_lancamento": lancamento.status.value,
            "ja_conciliado": True,
            "detalhamentos": itens_existentes,
            "nao_incluidos": [],
        }

    capacidade_restante = to_decimal(lancamento.valor) - to_decimal(lancamento.soma_detalhamentos)
    grupos_por_tipo = {
        tipo: RegraRepository.list_ativos_por_escopos(db, [escopo])
        for tipo, escopo in _ESCOPO_POR_TIPO.items()
    }

    resultado_itens = list(itens_existentes)
    nao_incluidos = []
    taxa_cartao_aplicada = _lancamento_ja_tem_taxa_cartao(db, lancamento_id)
    biscoitos_aplicado = _lancamento_ja_tem_biscoitos(db, lancamento_id)

    for tipo_detalhamento, inscricao_pendente in _candidatos_do_lancamento(db, lancamento_id):
        pendencia_auditoria = _to_pendencia_auditoria(inscricao_pendente)

        # Fallback só é permitido pra quem chega primeiro na fila (mesma regra
        # do fluxo real): nada pode ter sido consumido ainda, nem por
        # detalhamentos já existentes nem pelos já simulados neste laço.
        permite_fallback = capacidade_restante >= (to_decimal(lancamento.valor) - _TOLERANCIA)

        eh_cartao = lancamento.cart_taxa is not None
        pendencia_para_extracao = (
            replace(pendencia_auditoria, pagamento=to_decimal(lancamento.cart_valor_liquido))
            if eh_cartao
            else pendencia_auditoria
        )

        itens_com_origem = extrair_detalhamentos_com_origem(
            pendencia_para_extracao,
            grupos_por_tipo[tipo_detalhamento],
            tipo_detalhamento,
            permite_fallback,
        )

        if not itens_com_origem:
            nao_incluidos.append(
                {
                    "tipo": _LABEL_TIPO_PESSOA[tipo_detalhamento],
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                    "pagamento": to_decimal(inscricao_pendente.pagamento),
                    "observacao": inscricao_pendente.observacao,
                    "motivo": _MOTIVO_SEM_VALOR_IDENTIFICADO,
                }
            )
            continue

        if tipo_detalhamento == TipoDetalhamento.INSCRICAO_ENCONTRISTA:
            itens_com_origem, aplicou_biscoitos = _aplicar_biscoitos(
                db, itens_com_origem, inscricao_pendente, biscoitos_aplicado
            )
            biscoitos_aplicado = biscoitos_aplicado or aplicou_biscoitos

        if eh_cartao:
            itens_com_origem = _aplicar_taxa_cartao(
                itens_com_origem,
                to_decimal(lancamento.cart_taxa),
                taxa_cartao_aplicada,
                origem_taxa=_REGRA_TAXA_CARTAO,
            )
            taxa_cartao_aplicada = True

        itens = [item for item, _ in itens_com_origem]
        erro = _verificar_capacidade(capacidade_restante, itens)
        if erro:
            nao_incluidos.append(
                {
                    "tipo": _LABEL_TIPO_PESSOA[tipo_detalhamento],
                    "id": inscricao_pendente.id,
                    "nome": inscricao_pendente.nome,
                    "pagamento": to_decimal(inscricao_pendente.pagamento),
                    "observacao": inscricao_pendente.observacao,
                    "motivo": erro,
                }
            )
            continue

        for item, nome_regra in itens_com_origem:
            inscricao = (
                _inscricao_resumo(
                    item.tipo,
                    inscricao_pendente.id,
                    inscricao_pendente.nome,
                    inscricao_pendente.pagamento,
                    inscricao_pendente.observacao,
                )
                if item.referencia_id is not None
                else None
            )
            resultado_itens.append(
                _item_resposta(
                    item,
                    origem="SIMULADO",
                    inscricao=inscricao,
                    regra=nome_regra or _REGRA_FALLBACK,
                )
            )

        capacidade_restante -= sum((item.valor for item in itens), Decimal(0))

    return {
        "lancamento_id": lancamento.id,
        "descricao": lancamento.descricao,
        "data_pagamento": lancamento.data_pagamento,
        "valor": to_decimal(lancamento.valor),
        "forma_pagamento": lancamento.forma_pagamento,
        "parcelas": lancamento.cart_parcelas,
        "status_lancamento": lancamento.status.value,
        "ja_conciliado": False,
        "detalhamentos": resultado_itens,
        "nao_incluidos": nao_incluidos,
    }


class AuditoriaService:
    @staticmethod
    def simular(db: Session, lancamento_id: int) -> dict:
        return _simular_auditoria(db, lancamento_id)

    @staticmethod
    def processar(db: Session) -> dict:
        total_detalhamentos_antes = db.query(Detalhamento).count()

        avaliados_enco, vinculados_enco, nao_auditados_enco = _processar_pendentes(
            db, Encontreiro, TipoDetalhamento.INSCRICAO_ENCONTREIRO
        )
        avaliados_enca, vinculados_enca, nao_auditados_enca = _processar_pendentes(
            db, Encontrista, TipoDetalhamento.INSCRICAO_ENCONTRISTA
        )

        db.commit()

        total_detalhamentos_depois = db.query(Detalhamento).count()
        extras_via_observacao = (
            total_detalhamentos_depois
            - total_detalhamentos_antes
            - vinculados_enco
            - vinculados_enca
        )

        nao_auditados = nao_auditados_enco + nao_auditados_enca

        return {
            "avaliados": avaliados_enco + avaliados_enca,
            "vinculados_encontreiro": vinculados_enco,
            "vinculados_encontrista": vinculados_enca,
            "detalhamentos_extras_via_observacao": extras_via_observacao,
            "nao_auditados": len(nao_auditados),
            "detalhes_nao_auditados": nao_auditados,
            "mensagem": (
                f"Auditoria concluída. {vinculados_enco} encontreiro(s) e "
                f"{vinculados_enca} encontrista(s) vinculados, "
                f"{extras_via_observacao} detalhamento(s) extra(s) via observação, "
                f"{len(nao_auditados)} inscrição(ões) ainda não auditada(s)."
            ),
        }
