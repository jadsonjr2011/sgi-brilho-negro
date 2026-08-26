from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable
)


# =========================================================
# CONFIGURAÇÕES
# =========================================================

LOGO_PATH = os.path.join(
    "static",
    "img",
    "logo_relatorio.PNG"
)


# =========================================================
# FORMATAÇÃO
# =========================================================

def moeda(valor):

    if valor is None:
        valor = 0

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def percentual(valor):

    if valor is None:
        valor = 0

    return f"{valor:.2f}%".replace(".", ",")


# =========================================================
# CABEÇALHO
# =========================================================

def adicionar_cabecalho(canvas, doc):

    canvas.saveState()

    largura, altura = A4


    # =====================================================
    # LOGO
    # =====================================================

    if os.path.exists(LOGO_PATH):

        try:

            canvas.drawImage(
                LOGO_PATH,

                (largura - 320) / 2,

                altura - 105,

                width=320,
                height=79,

                preserveAspectRatio=True,
                mask="auto"
            )

        except Exception:
            pass


    # =====================================================
    # IDENTIFICAÇÃO DA ASSOCIAÇÃO
    # =====================================================

    canvas.setFillColor(colors.black)

    canvas.setFont(
        "Helvetica-Bold",
        12
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 125,
        "ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR"
    )


    # =====================================================
    # BRILHO NEGRO
    # =====================================================

    canvas.setFont(
        "Helvetica-Bold",
        20
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 150,
        "BRILHO NEGRO"
    )


    # =====================================================
    # SISTEMA
    # =====================================================

    canvas.setFont(
        "Helvetica",
        12
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 171,
        "Sistema de Gestão de Integrantes"
    )


    # =====================================================
    # LINHA
    # =====================================================

    canvas.setStrokeColor(
        colors.grey
    )

    canvas.line(
        40,
        altura - 187,
        largura - 40,
        altura - 187
    )


    # =====================================================
    # TÍTULO DO RELATÓRIO
    # =====================================================

    canvas.setFillColor(colors.black)

    canvas.setFont(
        "Helvetica-Bold",
        16
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 215,
        "RELATÓRIO FINANCEIRO — RECEITAS X DESPESAS"
    )

    # =====================================================
    # TEMPORADA + PERÍODO
    # =====================================================

    canvas.setFillColor(
        colors.HexColor("#666666")
    )

    canvas.setFont(
        "Helvetica",
        10
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 229,
        f"Temporada {doc.temporada} | "
        f"Período: {doc.data_inicio} a {doc.data_fim}"
    )


    canvas.restoreState()


# =========================================================
# RODAPÉ
# =========================================================

def adicionar_rodape(canvas, doc):

    canvas.saveState()

    largura, _ = A4

    canvas.setStrokeColor(
        colors.HexColor("#cccccc")
    )

    canvas.line(
        18 * mm,
        15 * mm,
        largura - 18 * mm,
        15 * mm
    )


    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.setFillColor(
        colors.HexColor("#666666")
    )


    canvas.drawString(
        18 * mm,
        10 * mm,
        "Brilho Negro - Relatório Financeiro"
    )


    canvas.drawRightString(
        largura - 18 * mm,
        10 * mm,
        f"Página {doc.page}"
    )


    canvas.restoreState()


# =========================================================
# ESTILOS
# =========================================================

def criar_estilos():

    estilos = getSampleStyleSheet()


    titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=8
    )


    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12
    )


    secao = ParagraphStyle(
        "Secao",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=6
    )


    normal = ParagraphStyle(
        "NormalFinanceiro",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11
    )


    pequeno = ParagraphStyle(
        "Pequeno",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9
    )


    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "secao": secao,
        "normal": normal,
        "pequeno": pequeno
    }


# =========================================================
# TABELA RESUMO
# =========================================================

def criar_tabela_resumo(
    total_receitas,
    total_despesas,
    resultado,
    percentual_despesas
):

    dados = [

        [
            "RECEITAS",
            "DESPESAS",
            "RESULTADO",
            "DESPESAS / RECEITAS"
        ],

        [
            moeda(total_receitas),
            moeda(total_despesas),
            moeda(resultado),
            percentual(percentual_despesas)
        ]

    ]


    tabela = Table(
        dados,
        colWidths=[
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm
        ]
    )


    tabela.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#222222")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#999999")
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor("#cccccc")
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )


    return tabela


# =========================================================
# TABELA MENSAL
# =========================================================

def criar_tabela_mensal(movimentos_mensais):

    dados = [

        [
            "MÊS",
            "RECEITAS",
            "DESPESAS",
            "RESULTADO"
        ]

    ]


    for item in movimentos_mensais:

        dados.append([

            item.get("mes", "-"),

            moeda(
                item.get(
                    "receitas",
                    0
                )
            ),

            moeda(
                item.get(
                    "despesas",
                    0
                )
            ),

            moeda(
                item.get(
                    "resultado",
                    0
                )
            )

        ])


    tabela = Table(
        dados,
        colWidths=[
            45 * mm,
            45 * mm,
            45 * mm,
            45 * mm
        ],
        repeatRows=1
    )


    tabela.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#333333")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT"
            ),

            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "LEFT"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#cccccc")
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f5f5f5")
                ]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )

        ])
    )


    return tabela


# =========================================================
# TABELA DE CATEGORIAS
# =========================================================

def criar_tabela_categorias(
    categorias,
    titulo_tipo
):

    dados = [

        [
            "CATEGORIA",
            "VALOR"
        ]

    ]


    for item in categorias:

        dados.append([

            item.get(
                "categoria",
                "-"
            ),

            moeda(
                item.get(
                    "valor",
                    0
                )
            )

        ])


    tabela = Table(
        dados,
        colWidths=[
            120 * mm,
            60 * mm
        ],
        repeatRows=1
    )


    tabela.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#333333")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "RIGHT"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#cccccc")
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f5f5f5")
                ]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )

        ])
    )


    return tabela


# =========================================================
# GERAR PDF
# =========================================================

def gerar_pdf_receitas_despesas(
    temporada,
    data_inicio,
    data_fim,
    total_receitas,
    total_despesas,
    resultado,
    percentual_despesas,
    movimentos_mensais=None,
    maiores_receitas=None,
    maiores_despesas=None
):

    buffer = BytesIO()


    documento = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=18 * mm,
        leftMargin=18 * mm,

        topMargin=92 * mm,
        bottomMargin=22 * mm

    )


    documento.temporada = temporada
    documento.data_inicio = data_inicio
    documento.data_fim = data_fim


    estilos = criar_estilos()


    elementos = []

    # =====================================================
    # ESPAÇO APÓS O CABEÇALHO
    # =====================================================

    elementos.append(
    Spacer(1, 5)
    )

    # =====================================================
    # RESUMO FINANCEIRO
    # =====================================================

    elementos.append(

        Paragraph(
            "Resumo Financeiro",
            estilos["secao"]
        )

    )


    elementos.append(

        criar_tabela_resumo(

            total_receitas,
            total_despesas,
            resultado,
            percentual_despesas

        )

    )


    elementos.append(
        Spacer(1, 12)
    )


    # =====================================================
    # ANÁLISE
    # =====================================================

    if resultado > 0:

        texto_resultado = (
            f"O período apresentou resultado positivo de "
            f"<b>{moeda(resultado)}</b>."
        )

    elif resultado < 0:

        texto_resultado = (
            f"O período apresentou resultado negativo de "
            f"<b>{moeda(abs(resultado))}</b>."
        )

    else:

        texto_resultado = (
            "O período apresentou resultado financeiro "
            "<b>zerado</b>."
        )


    elementos.append(

        Paragraph(
            texto_resultado,
            estilos["normal"]
        )

    )


    elementos.append(
        Spacer(1, 10)
    )


    # =====================================================
    # EVOLUÇÃO MENSAL
    # =====================================================

    if movimentos_mensais:

        elementos.append(

            Paragraph(
                "Evolução Mensal",
                estilos["secao"]
            )

        )


        elementos.append(

            criar_tabela_mensal(
                movimentos_mensais
            )

        )


        elementos.append(
            Spacer(1, 12)
        )


    # =====================================================
    # MAIORES RECEITAS
    # =====================================================

    if maiores_receitas:

        elementos.append(

            Paragraph(
                "Principais Receitas",
                estilos["secao"]
            )

        )


        elementos.append(

            criar_tabela_categorias(

                maiores_receitas,
                "Receitas"

            )

        )


        elementos.append(
            Spacer(1, 12)
        )


    # =====================================================
    # MAIORES DESPESAS
    # =====================================================

    if maiores_despesas:

        elementos.append(

            Paragraph(
                "Principais Despesas",
                estilos["secao"]
            )

        )


        elementos.append(

            criar_tabela_categorias(

                maiores_despesas,
                "Despesas"

            )

        )


        elementos.append(
            Spacer(1, 12)
        )


    # =====================================================
    # CONSTRUÇÃO
    # =====================================================

    documento.build(

        elementos,

        onFirstPage=lambda canvas, doc: (
            adicionar_cabecalho(canvas, doc),
            adicionar_rodape(canvas, doc)
        ),

        onLaterPages=lambda canvas, doc: (
            adicionar_cabecalho(canvas, doc),
            adicionar_rodape(canvas, doc)
        )

    )


    buffer.seek(0)

    return buffer