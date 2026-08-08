from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.detalhamento import tipo_detalhamento_enum
from app.models.enums import ModoExtracaoRegra

modo_extracao_regra_enum = ENUM(ModoExtracaoRegra, name="modo_extracao_regra", create_type=True)


class Regra(Base):
    """Uma Regra avalia a observação de uma pendência e, se "casar", gera
    exatamente 1 Detalhamento do tipo `tipo_detalhamento_resultado`. Duas
    formas de casar (`modo_extracao`):
    - TOKEN_VALOR: TODAS as suas RegraCondicao precisam dar match (AND) —
      o valor vem do grupo de captura da primeira condição, em ordem, que
      tiver um.
    - NOME_NA_LISTA: ignora RegraCondicao — busca o nome da própria pessoa
      (pendência) no texto e captura o valor associado (caso de um único
      pagamento cobrindo várias inscrições nomeadas na mesma observação).
    "Parar no primeiro match" vale por `tipo_detalhamento_resultado`: entre
    Regras do MESMO tipo, só a primeira (em ordem) que bater conta; Regras de
    tipos diferentes (ex. Inscrição vs Oferta) são avaliadas independentemente
    e podem gerar Detalhamentos ao mesmo tempo."""

    __tablename__ = "regras"

    id = Column(Integer, primary_key=True)
    regra_grupo_id = Column(Integer, ForeignKey("regra_grupos.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String(150), nullable=False)
    ordem = Column(Integer, nullable=False)
    ativo = Column(Boolean, nullable=False, server_default="true")
    tipo_detalhamento_resultado = Column(tipo_detalhamento_enum, nullable=False)
    modo_extracao = Column(modo_extracao_regra_enum, nullable=False, server_default=ModoExtracaoRegra.TOKEN_VALOR.value)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    regra_grupo = relationship("RegraGrupo", back_populates="regras")
    condicoes = relationship(
        "RegraCondicao",
        back_populates="regra",
        order_by="RegraCondicao.ordem",
        cascade="all, delete-orphan",
    )
