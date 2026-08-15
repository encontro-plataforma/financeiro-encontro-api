from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session, joinedload

from app.models.circulo import Circulo
from app.models.encontreiro import Encontreiro
from app.models.encontrista import Encontrista
from app.utils.parse_utils import remover_acentos

_COR_PRIMARIA  = colors.HexColor("#1a237e")
_COR_LINHA_PAR = colors.HexColor("#f0f4ff")

_MARGENS = dict(leftMargin=15 * mm, rightMargin=15 * mm, topMargin=20 * mm, bottomMargin=20 * mm)


def _valido(texto) -> bool:
    if not texto or not texto.strip():
        return False
    return remover_acentos(texto).strip().upper() != "NAO"


def _tabela(header: list[str], rows: list[list[str]], col_widths: list[float]) -> Table:
    dados = [header] + rows
    n = len(dados)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), _COR_PRIMARIA),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 7.5),
        *[("BACKGROUND", (0, i), (-1, i), _COR_LINHA_PAR) for i in range(2, n, 2)],
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("LINEBELOW",  (0, 0), (-1, 0), 1, colors.white),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]
    table = Table(dados, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    return table


def _titulo_style() -> ParagraphStyle:
    return ParagraphStyle(
        "titulo", fontName="Helvetica-Bold", fontSize=16,
        textColor=_COR_PRIMARIA, alignment=TA_CENTER, spaceAfter=2 * mm,
    )


def _subtitulo_style() -> ParagraphStyle:
    return ParagraphStyle(
        "subtitulo", fontName="Helvetica-Bold", fontSize=12,
        textColor=_COR_PRIMARIA, alignment=TA_CENTER, spaceAfter=5 * mm,
    )


def _info_style() -> ParagraphStyle:
    return ParagraphStyle(
        "info", fontName="Helvetica", fontSize=9,
        textColor=colors.grey, alignment=TA_CENTER, spaceAfter=5 * mm,
    )


def _rodape_style() -> ParagraphStyle:
    return ParagraphStyle(
        "rodape", fontName="Helvetica", fontSize=8,
        textColor=colors.grey, alignment=TA_RIGHT,
    )


def _rodape() -> Paragraph:
    return Paragraph(f"Emitido em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", _rodape_style())


class RelatorioSecretariaService:

    @staticmethod
    def gerar_encontristas_por_circulo(db: Session) -> bytes:
        circulos = db.query(Circulo).order_by(Circulo.nome.asc()).all()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, **_MARGENS)

        col_widths = [32 * mm, 24 * mm, 16 * mm, 14 * mm, 32 * mm, 32 * mm, 30 * mm]
        header = ["Nome", "Apelido", "Camisa", "Idade", "Padrinho", "Equipe do Padrinho", "Contato do Padrinho"]

        story = []
        primeiro = True

        for circulo in circulos:
            encontristas = (
                db.query(Encontrista)
                .options(joinedload(Encontrista.padrinho).joinedload(Encontreiro.equipe))
                .filter(Encontrista.circulo_id == circulo.id)
                .order_by(Encontrista.nome.asc())
                .all()
            )
            if not encontristas:
                continue

            if not primeiro:
                story.append(PageBreak())
            primeiro = False

            titulo_circulo = ParagraphStyle(
                "titulo_circulo", fontName="Helvetica-Bold", fontSize=14,
                textColor=colors.HexColor(circulo.rgb), alignment=TA_CENTER, spaceAfter=5 * mm,
            )
            story.append(Paragraph(circulo.nome, titulo_circulo))

            rows = []
            for e in encontristas:
                padrinho = e.padrinho
                equipe_padrinho = padrinho.equipe.nome if padrinho and padrinho.equipe else "-"
                rows.append([
                    e.nome,
                    e.apelido or "-",
                    e.camisa or "-",
                    str(e.idade) if e.idade is not None else "-",
                    padrinho.nome if padrinho else "-",
                    equipe_padrinho,
                    padrinho.telefone if padrinho and padrinho.telefone else "-",
                ])
            story.append(_tabela(header, rows, col_widths))

        if not story:
            story.append(Paragraph("Encontristas por Círculo", _titulo_style()))
            story.append(Paragraph("Nenhum encontrista com círculo cadastrado.", _info_style()))

        story.append(Spacer(1, 8 * mm))
        story.append(_rodape())

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def gerar_comorbidades(db: Session) -> bytes:
        encontreiros = (
            db.query(Encontreiro)
            .options(joinedload(Encontreiro.equipe))
            .order_by(Encontreiro.nome.asc())
            .all()
        )
        encontreiros = [e for e in encontreiros if _valido(e.alergia_comorbidade)]

        encontristas = (
            db.query(Encontrista)
            .options(
                joinedload(Encontrista.circulo),
                joinedload(Encontrista.padrinho).joinedload(Encontreiro.equipe),
            )
            .order_by(Encontrista.nome.asc())
            .all()
        )
        encontristas = [
            e for e in encontristas
            if _valido(e.medicacao) or _valido(e.alergia_comorbidade)
        ]

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, **_MARGENS)

        story = [
            Paragraph("Encontro com Cristo", _titulo_style()),
            Paragraph("COMORBIDADES", _subtitulo_style()),
        ]

        sec_encontreiros = ParagraphStyle(
            "sec_encontreiros", fontName="Helvetica-Bold", fontSize=11,
            textColor=_COR_PRIMARIA, spaceAfter=2 * mm,
        )
        sec_encontristas = ParagraphStyle(
            "sec_encontristas", fontName="Helvetica-Bold", fontSize=11,
            textColor=_COR_PRIMARIA, spaceAfter=2 * mm,
        )

        story.append(Paragraph("Encontreiros", sec_encontreiros))
        if encontreiros:
            header = ["Nome", "Apelido", "Equipe", "Alergia ou Comorbidade"]
            col_widths = [45 * mm, 35 * mm, 35 * mm, 65 * mm]
            rows = [[
                e.nome,
                e.apelido or "-",
                e.equipe.nome if e.equipe else "-",
                e.alergia_comorbidade,
            ] for e in encontreiros]
            story.append(_tabela(header, rows, col_widths))
        else:
            story.append(Paragraph("Nenhum registro encontrado.", _info_style()))

        story.append(PageBreak())

        story.append(Paragraph("Encontristas", sec_encontristas))
        if encontristas:
            header = ["Nome", "Apelido", "Círculo", "Nome do Padrinho", "Equipe do Padrinho", "Usa Medicação", "Alergia ou Comorbidade"]
            col_widths = [28 * mm, 20 * mm, 20 * mm, 28 * mm, 28 * mm, 26 * mm, 30 * mm]
            rows = []
            for e in encontristas:
                padrinho = e.padrinho
                equipe_padrinho = padrinho.equipe.nome if padrinho and padrinho.equipe else "-"
                rows.append([
                    e.nome,
                    e.apelido or "-",
                    e.circulo.nome if e.circulo else "-",
                    padrinho.nome if padrinho else "-",
                    equipe_padrinho,
                    e.medicacao or "-",
                    e.alergia_comorbidade or "-",
                ])
            story.append(_tabela(header, rows, col_widths))
        else:
            story.append(Paragraph("Nenhum registro encontrado.", _info_style()))

        story.append(Spacer(1, 8 * mm))
        story.append(_rodape())

        doc.build(story)
        return buffer.getvalue()
