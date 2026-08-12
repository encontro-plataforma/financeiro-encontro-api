from enum import Enum

class TipoLancamento(str, Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"


class FormaPagamento(str, Enum):
    PIX = "PIX"
    DINHEIRO = "DINHEIRO"
    CARTAO_CREDITO = "CARTAO_CREDITO"
    CARTAO_DEBITO = "CARTAO_DEBITO"


class StatusLancamento(str, Enum):
    CONCILIADO = "CONCILIADO"
    NAO_CONCILIADO = "NAO_CONCILIADO"
    

class StatusProcessamento(str, Enum):
    PROCESSANDO = "PROCESSANDO"
    PROCESSADO = "PROCESSADO"
    ERRO = "ERRO"


class PerfilUsuario(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    CONCILIADOR   = "CONCILIADOR"
    REPORTER      = "REPORTER"
    SECRETARIO    = "SECRETARIO"


class AcessoEquipe(str, Enum):
    EDG      = "EDG"
    VERMELHO = "VERMELHO"
    AMARELO  = "AMARELO"
    VERDE    = "VERDE"


class SituacaoCamisa(str, Enum):
    PENDENTE  = "PENDENTE"
    SOLICITADA = "SOLICITADA"
    RECEBIDA  = "RECEBIDA"
    ENTREGUE  = "ENTREGUE"
    SEM_BLUSA = "SEM_BLUSA"


class TipoDetalhamento(str, Enum):
    INSCRICAO_ENCONTREIRO = "INSCRICAO_ENCONTREIRO"
    INSCRICAO_ENCONTRISTA = "INSCRICAO_ENCONTRISTA"
    OFERTA = "OFERTA"
    OUTRO  = "OUTRO"


class EscopoRegraGrupo(str, Enum):
    EXTRACAO_ENCONTREIRO = "EXTRACAO_ENCONTREIRO"
    EXTRACAO_ENCONTRISTA = "EXTRACAO_ENCONTRISTA"
    OFERTAS = "OFERTAS"


class ModoExtracaoRegra(str, Enum):
    TOKEN_VALOR = "TOKEN_VALOR"
    NOME_NA_LISTA = "NOME_NA_LISTA"
