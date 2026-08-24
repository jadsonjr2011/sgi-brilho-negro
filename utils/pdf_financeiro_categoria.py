from io import BytesIO
from datetime import datetime
import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
    Table,
    TableStyle,
    PageBreak
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


# =====================================
# RODAPÉ
# =====================================

def adicionar_rodape(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    canvas.setStrokeColor(colors.grey)

    canvas.line(
        40,
        50,
        largura - 40,
        50
    )

    canvas.setFont(
        "Helvetica",
        8
    )

    canvas.setFillColor(
        colors.grey
    )

    canvas.drawCentredString(
        largura / 2,
        35,
        "Associação Cultural de Percussão Rudimentar Brilho Negro"
    )

    canvas.drawCentredString(
        largura / 2,
        23,
        "Documento gerado pelo Sistema de Gestão"
    )

    canvas.drawCentredString(
        largura / 2,
        11,
        f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    canvas.restoreState()


# =====================================
# CABEÇALHO
# =====================================

def adicionar_cabecalho(elementos, estilos, temporada):

    logo_path = os.path.join(
        "static",
        "img",
        "logo_relatorio.PNG"
    )

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=320,
            height=79
        )

        logo.hAlign = "CENTER"

        elementos.append(logo)

        elementos.append(
            Spacer(1, 5)
        )

    estilo_cabecalho = ParagraphStyle(
        "Cabecalho",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=12
    )

    elementos.append(
        Paragraph(
            "<b>ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR</b>",
            estilo_cabecalho
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            "<b>BRILHO NEGRO</b>",
            ParagraphStyle(
                "Nome",
                parent=estilo_cabecalho,
                fontSize=20
            )
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            estilo_cabecalho
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )

    elementos.append(
        Spacer(1, 25)
    )

    elementos.append(
        Paragraph(
            f"<b>RELATÓRIO FINANCEIRO POR CATEGORIA</b>",
            ParagraphStyle(
                "Titulo",
                parent=estilo_cabecalho,
                fontSize=16
            )
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            f"Temporada: <b>{temporada}</b>",
            ParagraphStyle(
                "Temporada",
                parent=estilo_cabecalho,
                fontSize=11
            )
        )
    )

    elementos.append(
        Spacer(1, 20)
    )


# =====================================
# FORMATA MOEDA
# =====================================

def moeda(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# =====================================
# FORMATA PERCENTUAL
# =====================================

def percentual(valor):

    return (
        f"{valor:,.2f}%"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# =====================================
# TABELA POR CATEGORIA
# =====================================

def criar_tabela_categoria(
    titulo,
    categorias,
    total_geral,
    estilos
):

    elementos = []

    estilo = ParagraphStyle(
        "TituloSecao",
        parent=estilos["Normal"],
        fontSize=11,
        leading=15
    )

    elementos.append(
        Paragraph(
            f"<b>{titulo}</b>",
            estilo
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    dados = [
        [
            "Categoria",
            "Movimentações",
            "Total",
            "%"
        ]
    ]

    total_quantidade = 0
    total_valor = 0

    for categoria in categorias:

        nome = categoria.categoria or "Sem categoria"
        quantidade = categoria.quantidade or 0
        valor = categoria.total or 0

        if total_geral > 0:
            percentual_categoria = (
                float(valor) / float(total_geral)
            ) * 100
        else:
            percentual_categoria = 0

        total_quantidade += quantidade
        total_valor += valor

        dados.append(
            [
                Paragraph(
                    str(nome),
                    ParagraphStyle(
                        "Categoria",
                        parent=estilos["Normal"],
                        fontSize=9,
                        leading=11
                    )
                ),

                str(quantidade),

                moeda(valor),

                percentual(percentual_categoria)
            ]
        )

    dados.append(
        [
            "TOTAL",
            str(total_quantidade),
            moeda(total_valor),
            "100,00%"
        ]
    )

    tabela = Table(
        dados,
        repeatRows=1,
        colWidths=[220, 85, 90, 65]
    )

    tabela.setStyle(
        TableStyle([

            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

            ("FONT", (0,0), (-1,0), "Helvetica-Bold"),

            ("FONT", (0,-1), (-1,-1), "Helvetica-Bold"),

            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

            ("ALIGN", (0,0), (-1,0), "CENTER"),

            ("ALIGN", (1,1), (-1,-1), "CENTER"),

            ("ALIGN", (0,-1), (-1,-1), "CENTER"),

            ("LEFTPADDING", (0,0), (-1,-1), 5),

            ("RIGHTPADDING", (0,0), (-1,-1), 5),

            ("TOPPADDING", (0,0), (-1,-1), 5),

            ("BOTTOMPADDING", (0,0), (-1,-1), 5)

        ])
    )

    elementos.append(tabela)

    elementos.append(
        Spacer(1, 25)
    )

    return elementos


# =====================================
# GERA PDF
# =====================================

def gerar_pdf_financeiro_categoria(
    receitas_categoria,
    despesas_categoria,
    total_receitas,
    total_despesas,
    temporada
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40

    )

    estilos = getSampleStyleSheet()

    estilo = ParagraphStyle(
        "NormalRelatorio",
        parent=estilos["Normal"],
        fontSize=10,
        leading=15
    )

    elementos = []

    adicionar_cabecalho(
        elementos,
        estilos,
        temporada
    )

    # =====================================
    # RESUMO
    # =====================================

    saldo = total_receitas - total_despesas

    resumo = [

        ["Indicador", "Valor"],

        ["Total de Receitas", moeda(total_receitas)],

        ["Total de Despesas", moeda(total_despesas)],

        ["Saldo", moeda(saldo)]

    ]

    tabela_resumo = Table(
        resumo,
        colWidths=[250, 150]
    )

    tabela_resumo.setStyle(
        TableStyle([

            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

            ("FONT", (0,0), (-1,0), "Helvetica-Bold"),

            ("FONT", (0,-1), (-1,-1), "Helvetica-Bold"),

            ("ALIGN", (0,0), (-1,-1), "CENTER"),

            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

            ("TOPPADDING", (0,0), (-1,-1), 6),

            ("BOTTOMPADDING", (0,0), (-1,-1), 6)

        ])
    )

    elementos.append(tabela_resumo)

    elementos.append(
        Spacer(1, 30)
    )

    # =====================================
    # RECEITAS
    # =====================================

    elementos.extend(
        criar_tabela_categoria(
            "1 - RECEITAS POR CATEGORIA",
            receitas_categoria,
            total_receitas,
            estilos
        )
    )

    # =====================================
    # DESPESAS
    # =====================================

    elementos.extend(
        criar_tabela_categoria(
            "2 - DESPESAS POR CATEGORIA",
            despesas_categoria,
            total_despesas,
            estilos
        )
    )

    # =====================================
    # CONCLUSÃO
    # =====================================

    elementos.append(
        Paragraph(
            "<b>3 - RESULTADO FINANCEIRO</b>",
            ParagraphStyle(
                "ResultadoTitulo",
                parent=estilos["Normal"],
                fontSize=11,
                leading=15
            )
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    situacao = (
        "SUPERÁVIT FINANCEIRO"
        if saldo >= 0
        else
        "DÉFICIT FINANCEIRO"
    )

    texto_resultado = (
        f"O relatório apresenta a distribuição das movimentações "
        f"financeiras por categoria referente à temporada "
        f"<b>{temporada}</b>."
        f"<br/><br/>"
        f"<b>Receitas:</b> {moeda(total_receitas)}<br/>"
        f"<b>Despesas:</b> {moeda(total_despesas)}<br/>"
        f"<b>Resultado:</b> {moeda(saldo)}<br/>"
        f"<b>Situação:</b> {situacao}"
    )

    elementos.append(
        Paragraph(
            texto_resultado,
            estilo
        )
    )

    doc.build(
        elementos,
        onFirstPage=adicionar_rodape,
        onLaterPages=adicionar_rodape
    )

    buffer.seek(0)

    return buffer