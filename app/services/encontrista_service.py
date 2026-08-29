import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.database.session import SessionLocal
from app.integracao.secretaria import encontrista_parser
from app.models.detalhamento import Detalhamento
from app.models.encontrista import Encontrista
from app.models.enums import StatusProcessamento, TipoDetalhamento
from app.models.upload_file import UploadFile
from app.repositories.circulo_repository import CirculoRepository
from app.repositories.encontreiro_repository import EncontreiroRepository
from app.repositories.encontrista_repository import EncontristaRepository
from app.services.auditoria_service import AuditoriaService
from app.services.upload_file_service import UploadFileService
from app.utils.parse_utils import parse_bool, parse_date_br, parse_decimal_br

logger = logging.getLogger("uvicorn.error")


def _parse_bool_campo(valor, is_new: bool):
    if valor is None:
        return False if is_new else None
    return parse_bool(valor)


def _parse_idade(valor):
    if not valor:
        return None
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"idade inválida: '{valor}'") from exc


class EncontristaService:

    @staticmethod
    def list_all(db: Session, params):
        return EncontristaRepository.list_all(db, params)

    @staticmethod
    def list(db: Session, params):
        items, total = EncontristaRepository.list_with_count(db, params)

        return {
            "items": items,
            "total": total,
            "skip": params.skip,
            "limit": params.limit
        }

    @staticmethod
    def get_by_id(db: Session, encontrista_id: int):
        obj = EncontristaRepository.get_by_id(db, encontrista_id)

        if not obj:
            raise NotFoundException("Encontrista")

        detalhamento = (
            db.query(Detalhamento)
            .filter(
                Detalhamento.tipo == TipoDetalhamento.INSCRICAO_ENCONTRISTA,
                Detalhamento.referencia_id == obj.id,
            )
            .first()
        )
        obj.detalhamento_id = detalhamento.id if detalhamento else None
        obj.lancamento_vinculado = detalhamento.lancamento if detalhamento else None

        return obj

    @staticmethod
    def create(db: Session, data: dict):
        return EncontristaRepository.create(db, data)

    @staticmethod
    def update(db: Session, encontrista_id: int, data: dict):
        obj = EncontristaRepository.get_by_id(db, encontrista_id)

        if not obj:
            raise NotFoundException("Encontrista")

        return EncontristaRepository.update(db, obj, data)

    @staticmethod
    def alterar_circulo(db: Session, encontrista_id: int, circulo_id: int):
        obj = EncontristaRepository.get_by_id(db, encontrista_id)

        if not obj:
            raise NotFoundException("Encontrista")

        # 0 é o sentinela de "Sem Círculo" (mesma convenção do filtro de
        # círculo da listagem) -- não corresponde a um Circulo real.
        if circulo_id == 0:
            return EncontristaRepository.update(db, obj, {"circulo_id": None})

        circulo = CirculoRepository.get_by_id(db, circulo_id)

        if not circulo:
            raise NotFoundException("Círculo")

        return EncontristaRepository.update(db, obj, {"circulo_id": circulo_id})

    @staticmethod
    def delete(db: Session, encontrista_id: int):
        obj = EncontristaRepository.get_by_id(db, encontrista_id)

        if not obj:
            raise NotFoundException("Encontrista")

        EncontristaRepository.delete(db, obj)

    @staticmethod
    def padrinhos_disponiveis(db: Session):
        return EncontristaRepository.get_padrinhos_disponiveis(db)

    # -------------------------------------------------------------------
    # Conciliação via CSV
    # -------------------------------------------------------------------

    @staticmethod
    def _linha_para_dados(db: Session, row, is_new: bool) -> dict:
        padrinho = EncontreiroRepository.get_by_id(db, row.padrinho_id)
        if not padrinho:
            raise ValueError(f"padrinho (Encontreiro id={row.padrinho_id}) não encontrado")

        circulo_id = None
        if row.circulo_nome:
            circulo = CirculoRepository.get_by_nome(db, row.circulo_nome)
            if circulo:
                circulo_id = circulo.id
            else:
                logger.warning(
                    "Linha %s: círculo '%s' não encontrado, ficará em branco",
                    row.linha, row.circulo_nome,
                )

        return {
            "dt_entrega": parse_date_br(row.dt_entrega),
            "dt_validade": parse_date_br(row.dt_validade),
            "padrinho_id": padrinho.id,
            "carta": _parse_bool_campo(row.carta, is_new),
            "album": _parse_bool_campo(row.album, is_new),
            "nome": row.nome,
            "apelido": row.apelido,
            "dt_nascimento": parse_date_br(row.dt_nascimento),
            "idade": _parse_idade(row.idade),
            "circulo_id": circulo_id,
            "onde_veio_ficha": row.onde_veio_ficha or "",
            "instagram": row.instagram,
            "contato": row.contato,
            "religiao": row.religiao,
            "igreja": row.igreja,
            "endereco": row.endereco,
            "cidade": row.cidade,
            "camisa": row.camisa,
            "blusa": _parse_bool_campo(row.blusa, is_new),
            "veiculo": row.veiculo,
            "contato_emerg": row.contato_emerg,
            "nome_emerg": row.nome_emerg,
            "parentesco_emerg": row.parentesco_emerg,
            "medicacao": row.medicacao,
            "alergia_comorbidade": row.alergia_comorbidade,
            "dt_pagamento": parse_date_br(row.dt_pagamento),
            "nome_pagador": row.nome_pagador,
            "pagamento": parse_decimal_br(row.pagamento),
            "observacao": row.observacao,
        }

    @staticmethod
    def iniciar_conciliacao(file, db: Session) -> UploadFile:
        """Valida e registra o arquivo (síncrono); o processamento em si roda em
        background (ver `processar_em_background`)."""
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

        return UploadFileService.create(db, {
            "nome_arquivo": file.filename,
            "conteudo_csv": conteudo,
            "tamanho_bytes": len(conteudo.encode('utf-8')),
            "status": StatusProcessamento.PROCESSANDO,
        })

    @staticmethod
    def processar_em_background(upload_id: int, conteudo: str):
        db = SessionLocal()

        try:
            linhas = encontrista_parser.parse(conteudo)

            inseridos = 0
            atualizados = 0

            for row in linhas:
                existente = EncontristaRepository.get_by_id(db, row.id)

                try:
                    dados = EncontristaService._linha_para_dados(db, row, is_new=existente is None)
                except ValueError as exc:
                    raise ValueError(f"Linha {row.linha}: {exc}") from exc

                if existente:
                    for key, value in dados.items():
                        if value is not None:
                            setattr(existente, key, value)
                    db.flush()
                    atualizados += 1
                    continue

                db.add(Encontrista(id=row.id, **dados))
                # sessao usa autoflush=False: sem o flush aqui, linhas do
                # mesmo arquivo nao "enxergam" as anteriores em get_by_id.
                db.flush()
                inseridos += 1

            if inseridos:
                db.execute(text(
                    "SELECT setval('encontristas_id_seq', (SELECT MAX(id) FROM encontristas))"
                ))

            db.commit()

            resultado = {
                "inseridos": inseridos,
                "atualizados": atualizados,
                "mensagem": (
                    f"Processamento concluído. {inseridos} inseridos, "
                    f"{atualizados} atualizados."
                ),
            }

            UploadFileService.update_status(
                db, upload_id, StatusProcessamento.PROCESSADO,
                resultado_processamento=json.dumps(resultado, ensure_ascii=False),
            )

            AuditoriaService.processar(db)

        except Exception as e:
            db.rollback()
            logger.exception("Erro ao processar CSV de encontristas (upload_id=%s)", upload_id)
            UploadFileService.update_status(
                db,
                upload_id,
                StatusProcessamento.ERRO,
                error_code="ERRO_PROCESSAMENTO_ENCONTRISTA",
                error_message=str(e),
            )

        finally:
            db.close()
