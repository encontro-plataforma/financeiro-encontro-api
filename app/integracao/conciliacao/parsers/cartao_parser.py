from app.integracao.conciliacao.parsers.base_parser import BaseParser


class CartaoParser(BaseParser):
    """Extrato da maquininha de cartão -- rota/endpoint já existe (Fase 4,
    pré-requisito), mas o formato real do arquivo ainda não foi definido.
    Levanta um erro claro em vez de tentar adivinhar um layout."""

    def parse(self, conteudo: str) -> list:
        raise NotImplementedError(
            "Importação de extrato de cartão ainda não está disponível "
            "-- o formato do arquivo da maquininha ainda será definido."
        )
