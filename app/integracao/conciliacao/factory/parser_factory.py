from app.integracao.conciliacao.parsers.banco_inter_parser import BancoInterParser


class ParserFactory:

    @staticmethod
    def get_parser(nome_arquivo: str):
        nome = nome_arquivo.lower()

        if "extrato" in nome or "inter" in nome:
            return BancoInterParser()

        raise Exception("Banco não suportado")