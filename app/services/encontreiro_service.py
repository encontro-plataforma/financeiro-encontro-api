import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.integracao.secretaria import encontreiro_parser
from app.models.encontreiro import Encontreiro
from app.models.enums import SituacaoCamisa, StatusProcessamento
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.equipe_repository import EquipeRepository
from app.services.auditoria_service import AuditoriaService
from app.services.upload_file_service import UploadFileService
from app.utils.parse_utils import normalizar_cabecalho, parse_date_br, parse_decimal_br

logger = logging.getLogger("uvicorn.error")


def _parse_situacao(valor, default=None):
    if not valor:
        return default

    normalizado = normalizar_cabecalho(valor).replace("_", " ")
    for situacao in SituacaoCamisa:
        if situacao.value.replace("_", " ") == normalizado:
            return situacao

    raise ValueError(f"situação de camisa inválida: '{valor}'")


class EncontreiroService:

    @staticmethod
    def list_all(db: Session, params):
        return EncontreiroRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = EncontreiroRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, encontreiro_id: int):
        obj = EncontreiroRepository.get_by_id(db, encontreiro_id)

        if not obj:
            raise NotFoundException("Encontreiro")

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return EncontreiroRepository.create(db, data)

    @staticmethod
    def update(db: Session, encontreiro_id: int, data: dict):
        obj = EncontreiroRepository.get_by_id(db, encontreiro_id)

        if not obj:
            raise NotFoundException("Encontreiro")

        return EncontreiroRepository.update(db, obj, data)

    @staticmethod
    def delete(db: Session, encontreiro_id: int):
        obj = EncontreiroRepository.get_by_id(db, encontreiro_id)

        if not obj:
            raise NotFoundException("Encontreiro")

        EncontreiroRepository.delete(db, obj)

    # -------------------------------------------------------------------
    # Conciliação via CSV
    # -------------------------------------------------------------------

    @staticmethod
    def _linha_para_dados(db: Session, row, is_new: bool) -> dict:
        equipe_id = None
        if row.equipe_nome:
            equipe = EquipeRepository.get_by_nome(db, row.equipe_nome)
            if not equipe:
                raise ValueError(f"equipe '{row.equipe_nome}' não encontrada")
            equipe_id = equipe.id
        elif is_new:
            raise ValueError("equipe não informada")

        situacao_default = SituacaoCamisa.SEM_BLUSA if is_new else None

        return {
            "dt_inscricao": parse_date_br(row.dt_inscricao),
            "nome": row.nome,
            "apelido": row.apelido,
            "instagram": row.instagram,
            "telefone": row.telefone,
            "estado_civil": row.estado_civil,
            "igreja": row.igreja,
            "religiao": row.religiao,
            "contato_emerg": row.contato_emerg,
            "nome_emerg": row.nome_emerg,
            "parentesco_emerg": row.parentesco_emerg,
            "alergia_comorbidade": row.alergia_comorbidade,
            "equipe_id": equipe_id,
            "camisa": row.camisa,
            "situacao_camisa": _parse_situacao(row.situacao_camisa, default=situacao_default),
            "veiculo": row.veiculo,
            "dt_pagamento": parse_date_br(row.dt_pagamento),
            "nome_pagador": row.nome_pagador,
            "pagamento": parse_decimal_br(row.pagamento),
            "observacao": row.observacao,
        }

    @staticmethod
    def conciliar_csv(file, db: Session):
        if not file.filename.endswith(".csv"):
            raise Exception("Arquivo deve ser CSV")

        try:
            conteudo_bytes = file.file.read()
            if len(conteudo_bytes) > 3 * 1024 * 1024:
                raise Exception("Arquivo está acima do limite permitido de tamanho de dados")
            conteudo = conteudo_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise Exception(
                "Erro ao processar arquivo. Utilize o charset UTF-8 para evitar problemas de acentuação."
            )

        upload = UploadFileService.create(db, {
            "nome_arquivo": file.filename,
            "conteudo_csv": conteudo,
            "tamanho_bytes": len(conteudo.encode('utf-8')),
            "status": StatusProcessamento.PROCESSANDO,
        })

        try:
            linhas = encontreiro_parser.parse(conteudo)

            inseridos = 0
            atualizados = 0
            ignorados = []

            for row in linhas:
                existente = EncontreiroRepository.get_by_id(db, row.id)

                try:
                    dados = EncontreiroService._linha_para_dados(db, row, is_new=existente is None)
                except ValueError as exc:
                    raise ValueError(f"Linha {row.linha}: {exc}") from exc

                if existente:
                    for key, value in dados.items():
                        if value is not None:
                            setattr(existente, key, value)
                    db.flush()
                    atualizados += 1
                    continue

                duplicado = EncontreiroRepository.get_by_nome_telefone(db, dados["nome"], dados["telefone"])
                if duplicado:
                    logger.warning(
                        "Linha %s ignorada: já existe Encontreiro id=%s com o mesmo nome/telefone",
                        row.linha, duplicado.id,
                    )
                    ignorados.append({
                        "linha": row.linha,
                        "id_csv": row.id,
                        "encontreiro_existente_id": duplicado.id,
                    })
                    continue

                novo = Encontreiro(id=row.id, **dados)
                db.add(novo)
                # sessao usa autoflush=False: sem o flush aqui, linhas do
                # mesmo arquivo nao "enxergam" as anteriores nas checagens
                # de id/nome+telefone acima.
                db.flush()
                inseridos += 1

            if inseridos:
                db.execute(text(
                    "SELECT setval('encontreiros_id_seq', (SELECT MAX(id) FROM encontreiros))"
                ))

            db.commit()

            UploadFileService.update_status(db, upload.id, StatusProcessamento.PROCESSADO)

            AuditoriaService.processar(db)

            return {
                "inseridos": inseridos,
                "atualizados": atualizados,
                "ignorados": len(ignorados),
                "detalhes_ignorados": ignorados,
                "mensagem": (
                    f"Processamento concluído. {inseridos} inseridos, "
                    f"{atualizados} atualizados, {len(ignorados)} ignorados."
                ),
            }

        except Exception as e:
            db.rollback()
            UploadFileService.update_status(
                db,
                upload.id,
                StatusProcessamento.ERRO,
                error_code="ERRO_PROCESSAMENTO_ENCONTREIRO",
                error_message=str(e),
            )
            raise Exception(f"Erro ao processar arquivo: {str(e)}")
