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
    TableStyle
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


# =====================================
# FORMATA MOEDA
# =====================================

def moeda(valor):

    valor = float(valor or 0)

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
        f"{float(valor):,.2f}%"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


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

def adicionar_cabecalho(
    elementos,
    estilos,
    temporada,
    data_inicio,
    data_fim
):

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
        "CabecalhoPeriodo",
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
                "NomePeriodo",
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
            "<b>RELATÓRIO FINANCEIRO POR PERÍODO</b>",
            ParagraphStyle(
                "TituloPeriodo",
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
                "TemporadaPeriodo",
                parent=estilo_cabecalho,
                fontSize=11
            )
        )
    )

    elementos.append(
        Spacer(1, 5)
    )

    elementos.append(
        Paragraph(
            f"Período: <b>{data_inicio}</b> até <b>{data_fim}</b>",
            ParagraphStyle(
                "Periodo",
                parent=estilo_cabecalho,
                fontSize=10
            )
        )
    )

    elementos.append(
        Spacer(1, 20)
    )


# =====================================
# TABELA MENSAL
# =====================================

def criar_tabela_mensal(
    movimentacoes,
    total_receitas,
    total_despesas,
    estilos
):

    elementos = []

    elementos.append(
        Paragraph(
            "<b>1 - MOVIMENTAÇÃO FINANCEIRA POR MÊS</b>",
            ParagraphStyle(
                "TituloMensal",
                parent=estilos["Normal"],
                fontSize=11,
                leading=15
            )
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    dados = [

        [
            "Mês",
            "Movimentações",
            "Receitas",
            "Despesas",
            "Resultado"
        ]

    ]

    total_movimentacoes = 0

    for item in movimentacoes:

        quantidade = int(item.quantidade or 0)

        receitas = float(item.receitas or 0)

        despesas = float(item.despesas or 0)

        resultado = receitas - despesas

        total_movimentacoes += quantidade

        dados.append(

            [

                str(item.mes),

                str(quantidade),

                moeda(receitas),

                moeda(despesas),

                moeda(resultado)

            ]

        )

    saldo = (
        float(total_receitas or 0)
        -
        float(total_despesas or 0)
    )

    dados.append(

        [

            "TOTAL",

            str(total_movimentacoes),

            moeda(total_receitas),

            moeda(total_despesas),

            moeda(saldo)

        ]

    )

    tabela = Table(

        dados,

        repeatRows=1,

        colWidths=[
            90,
            90,
            110,
            110,
            100
        ]

    )

    tabela.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONT",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONT",
                (0, -1),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER"
            ),

            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])

    )

    elementos.append(tabela)

    elementos.append(
        Spacer(1, 30)
    )

    return elementos


# =====================================
# GERA PDF
# =====================================

def gerar_pdf_financeiro_periodo(
    movimentacoes,
    total_receitas,
    total_despesas,
    quantidade_movimentacoes,
    temporada,
    data_inicio,
    data_fim
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
        "NormalPeriodo",
        parent=estilos["Normal"],
        fontSize=10,
        leading=15
    )

    elementos = []

    adicionar_cabecalho(
        elementos,
        estilos,
        temporada,
        data_inicio,
        data_fim
    )

    # =====================================
    # RESUMO
    # =====================================

    saldo = (
        float(total_receitas or 0)
        -
        float(total_despesas or 0)
    )

    total_entradas = float(total_receitas or 0)

    total_saidas = float(total_despesas or 0)

    percentual_receitas = 0

    percentual_despesas = 0

    total_movimentado = (
        total_entradas +
        total_saidas
    )

    if total_movimentado > 0:

        percentual_receitas = (
            total_entradas /
            total_movimentado
        ) * 100

        percentual_despesas = (
            total_saidas /
            total_movimentado
        ) * 100

    elementos.append(

        Paragraph(
            "<b>RESUMO DO PERÍODO</b>",
            estilo
        )

    )

    elementos.append(
        Spacer(1, 10)
    )

    resumo = [

        [
            "Indicador",
            "Valor"
        ],

        [
            "Quantidade de Movimentações",
            str(quantidade_movimentacoes)
        ],

        [
            "Total de Receitas",
            moeda(total_receitas)
        ],

        [
            "Total de Despesas",
            moeda(total_despesas)
        ],

        [
            "Total Movimentado",
            moeda(total_movimentado)
        ],

        [
            "Saldo do Período",
            moeda(saldo)
        ]

    ]

    tabela_resumo = Table(

        resumo,

        colWidths=[
            300,
            180
        ]

    )

    tabela_resumo.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONT",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONT",
                (0, -1),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])

    )

    elementos.append(
        tabela_resumo
    )

    elementos.append(
        Spacer(1, 30)
    )

    # =====================================
    # TABELA MENSAL
    # =====================================

    elementos.extend(

        criar_tabela_mensal(
            movimentacoes,
            total_receitas,
            total_despesas,
            estilos
        )

    )

    # =====================================
    # RESULTADO
    # =====================================

    situacao = (

        "SUPERÁVIT FINANCEIRO"

        if saldo >= 0

        else

        "DÉFICIT FINANCEIRO"

    )

    elementos.append(

        Paragraph(
            "<b>2 - RESULTADO DO PERÍODO</b>",
            ParagraphStyle(
                "ResultadoPeriodo",
                parent=estilos["Normal"],
                fontSize=11,
                leading=15
            )
        )

    )

    elementos.append(
        Spacer(1, 10)
    )

    texto_resultado = (

        f"O período analisado apresenta "

        f"<b>{int(quantidade_movimentacoes)}</b> "

        f"movimentações financeiras."

        f"<br/><br/>"

        f"<b>Receitas:</b> "
        f"{moeda(total_receitas)}"

        f"<br/>"

        f"<b>Despesas:</b> "
        f"{moeda(total_despesas)}"

        f"<br/>"

        f"<b>Total movimentado:</b> "
        f"{moeda(total_movimentado)}"

        f"<br/>"

        f"<b>Saldo:</b> "
        f"{moeda(saldo)}"

        f"<br/>"

        f"<b>Participação das receitas:</b> "
        f"{percentual(percentual_receitas)}"

        f"<br/>"

        f"<b>Participação das despesas:</b> "
        f"{percentual(percentual_despesas)}"

        f"<br/>"

        f"<b>Situação:</b> "
        f"{situacao}"

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