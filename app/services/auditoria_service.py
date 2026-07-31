import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.orm import Session

from app.models.detalhamento import Detalhamento
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.core.exceptions import BadRequestException
from app.models.enums import TipoDetalhamento, TipoLancamento
from app.models.lancamento import Lancamento
from app.services.detalhamento_service import DetalhamentoService
from app.utils.parse_utils import remover_acentos

logger = logging.getLogger("uvicorn.error")

_VALOR_REGEX = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+)")
_TOLERANCIA = Decimal("0.01")


def _decimal(valor) -> Decimal:
    return Decimal(str(valor)) if valor is not None else Decimal("0")


def _capacidade_restante(db: Session, lancamento: Lancamento) -> Decimal:
    consumido = (
        db.query(Detalhamento)
        .filter(Detalhamento.lancamento_id == lancamento.id)
        .all()
    )
    total_consumido = sum((d.valor for d in consumido), Decimal("0"))
    return _decimal(lancamento.valor) - total_consumido


def _texto_contem(texto: str, alvo: str) -> bool:
    return alvo in remover_acentos(texto or "").lower()


def _buscar_lancamento(db: Session, dt_pagamento, valor_necessario: Decimal, nome_pagador: Optional[str]):
    candidatos = (
        db.query(Lancamento)
        .filter(
            Lancamento.data_pagamento == dt_pagamento,
            Lancamento.tipo == TipoLancamento.RECEITA,
        )
        .all()
    )

    candidatos_validos = [
        l for l in candidatos
        if _capacidade_restante(db, l) >= valor_necessario - _TOLERANCIA
    ]

    if not candidatos_validos:
        return None

    if len(candidatos_validos) == 1:
        return candidatos_validos[0]

    exatos = [
        l for l in candidatos_validos
        if abs(_capacidade_restante(db, l) - valor_necessario) <= _TOLERANCIA
    ]
    if len(exatos) == 1:
        return exatos[0]

    if nome_pagador:
        nome_normalizado = remover_acentos(nome_pagador).lower()
        por_nome = [
            l for l in (exatos or candidatos_validos)
            if nome_normalizado and (
                nome_normalizado in remover_acentos(l.descricao or "").lower()
                or nome_normalizado in remover_acentos(l.observacao or "").lower()
            )
        ]
        if len(por_nome) == 1:
            return por_nome[0]

    return None


def _extrair_valor_proximo(texto: str) -> Optional[Decimal]:
    match = _VALOR_REGEX.search(texto)
    if not match:
        return None
    bruto = match.group(1)
    try:
        return Decimal(bruto.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _extrair_nome_apos_palavra(texto_original: str, palavra: str) -> Optional[str]:
    padrao = re.compile(re.escape(palavra), re.IGNORECASE)
    match = padrao.search(remover_acentos(texto_original))
    if not match:
        return None

    resto = texto_original[match.end():]
    resto = re.split(r"[,.;\n]", resto)[0]
    resto = resto.strip(" :-")
    return resto or None


def _processar_observacao(db: Session, lancamento: Lancamento, observacao: Optional[str]):
    """Analisa o texto livre de observacao do Encontreiro/Encontrista para
    identificar outras coisas pagas no mesmo lancamento (oferta, outra
    inscricao), criando Detalhamentos extras quando ainda não existirem."""
    if not observacao:
        return

    if _texto_contem(observacao, "oferta"):
        valor = _extrair_valor_proximo(observacao)
        if valor is None:
            valor = _capacidade_restante(db, lancamento)

        if valor and valor > _TOLERANCIA:
            ja_existe = (
                db.query(Detalhamento)
                .filter(
                    Detalhamento.lancamento_id == lancamento.id,
                    Detalhamento.tipo == TipoDetalhamento.OFERTA,
                    Detalhamento.valor == valor,
                )
                .first()
            )
            if not ja_existe:
                try:
                    DetalhamentoService.create(db, {
                        "lancamento_id": lancamento.id,
                        "tipo": TipoDetalhamento.OFERTA,
                        "referencia_id": None,
                        "valor": valor,
                        "descricao": f"R$ {valor:.2f} em oferta",
                    })
                except BadRequestException as e:
                    logger.info(
                        "Auditoria: oferta extra não pôde ser vinculada ao lançamento id=%s: %s",
                        lancamento.id, e,
                    )

    for palavra, modelo, tipo in (
        ("encontreiro", Encontreiro, TipoDetalhamento.INSCRICAO_ENCONTREIRO),
        ("encontrista", Encontrista, TipoDetalhamento.INSCRICAO_ENCONTRISTA),
    ):
        if not _texto_contem(observacao, palavra):
            continue

        nome_extraido = _extrair_nome_apos_palavra(observacao, palavra)
        if not nome_extraido:
            continue

        pessoa = db.query(modelo).filter(modelo.nome.ilike(f"%{nome_extraido}%")).first()
        if not pessoa or pessoa.auditado:
            continue

        valor_pessoa = _decimal(pessoa.pagamento)
        capacidade = _capacidade_restante(db, lancamento)
        if valor_pessoa <= 0 or valor_pessoa > capacidade + _TOLERANCIA:
            logger.info(
                "Auditoria: %s '%s' citado na observação do lançamento id=%s, "
                "mas o valor não cabe no que resta do lançamento",
                palavra, pessoa.nome, lancamento.id,
            )
            continue

        try:
            DetalhamentoService.create(db, {
                "lancamento_id": lancamento.id,
                "tipo": tipo,
                "referencia_id": pessoa.id,
                "valor": valor_pessoa,
            })
        except BadRequestException as e:
            logger.info(
                "Auditoria: %s '%s' citado na observação não pôde ser vinculado ao lançamento id=%s: %s",
                palavra, pessoa.nome, lancamento.id, e,
            )


def _processar_pendentes(db: Session, modelo, tipo_principal: TipoDetalhamento):
    pendentes = (
        db.query(modelo)
        .filter(
            modelo.pagamento.isnot(None),
            modelo.pagamento > 0,
            modelo.dt_pagamento.isnot(None),
            modelo.auditado.is_(False),
        )
        .order_by(modelo.dt_pagamento)
        .all()
    )

    vinculados = 0
    nao_auditados = []

    for pessoa in pendentes:
        lancamento = _buscar_lancamento(
            db, pessoa.dt_pagamento, _decimal(pessoa.pagamento), pessoa.nome_pagador
        )

        if not lancamento:
            nao_auditados.append({
                "tipo": tipo_principal.value,
                "id": pessoa.id,
                "nome": pessoa.nome,
            })
            continue

        try:
            DetalhamentoService.create(db, {
                "lancamento_id": lancamento.id,
                "tipo": tipo_principal,
                "referencia_id": pessoa.id,
                "valor": pessoa.pagamento,
            })
        except BadRequestException as e:
            nao_auditados.append({
                "tipo": tipo_principal.value,
                "id": pessoa.id,
                "nome": pessoa.nome,
                "motivo": str(e),
            })
            continue

        vinculados += 1

        _processar_observacao(db, lancamento, pessoa.observacao)

    return len(pendentes), vinculados, nao_auditados


class AuditoriaService:

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
