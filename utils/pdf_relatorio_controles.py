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
    PageBreak,
    KeepTogether
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
        f"R$ {float(valor):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def quantidade_formatada(valor):

    if valor is None:
        return "0"

    try:

        valor = float(valor)

        if valor.is_integer():
            return str(int(valor))

        return f"{valor:.2f}".replace(".", ",")

    except Exception:

        return str(valor)


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
    # TÍTULO
    # =====================================================

    canvas.setFillColor(colors.black)

    canvas.setFont(
        "Helvetica-Bold",
        16
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 215,
        "RELATÓRIO DE CONTROLES FINANCEIROS"
    )

    # =====================================================
    # TEMPORADA
    # =====================================================

    canvas.setFillColor(
        colors.HexColor("#666666")
    )

    canvas.setFont(
        "Helvetica",
        10
    )

    temporada = getattr(
        doc,
        "temporada",
        "-"
    )

    canvas.drawCentredString(
        largura / 2,
        altura - 229,
        f"Temporada {temporada}"
    )

    # =====================================================
    # GRUPO
    # =====================================================

    grupo = getattr(
        doc,
        "grupo",
        ""
    )

    if grupo:

        canvas.setFont(
            "Helvetica-Bold",
            10
        )

        canvas.setFillColor(
            colors.HexColor("#333333")
        )

        canvas.drawCentredString(
            largura / 2,
            altura - 243,
            f"Grupo: {grupo}"
        )

    else:

        canvas.setFont(
            "Helvetica",
            10
        )

        canvas.setFillColor(
            colors.HexColor("#666666")
        )

        canvas.drawCentredString(
            largura / 2,
            altura - 243,
            "Todos os grupos"
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
        "Brilho Negro - Relatório de Controles Financeiros"
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
        "TituloControles",
        parent=estilos["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=8
    )

    subtitulo = ParagraphStyle(
        "SubtituloControles",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12
    )

    secao = ParagraphStyle(
        "SecaoControles",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=6
    )

    normal = ParagraphStyle(
        "NormalControles",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11
    )

    pequeno = ParagraphStyle(
        "PequenoControles",
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
    total_controles,
    total_pago,
    total_pendente,
    quantidade_pagos,
    quantidade_parciais,
    quantidade_pendentes
):

    dados = [

        [
            "PEDIDOS",
            "PAGOS",
            "PARCIAIS",
            "PENDENTES",
            "VALOR PAGO",
            "VALOR PENDENTE"
        ],

        [
            quantidade_formatada(total_controles),
            quantidade_formatada(quantidade_pagos),
            quantidade_formatada(quantidade_parciais),
            quantidade_formatada(quantidade_pendentes),
            moeda(total_pago),
            moeda(total_pendente)
        ]

    ]

    tabela = Table(
        dados,
        colWidths=[
            27 * mm,
            23 * mm,
            27 * mm,
            28 * mm,
            35 * mm,
            43 * mm
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
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                7.5
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 1),
                (-1, 1),
                9
            ),

            (
                "TEXTCOLOR",
                (0, 1),
                (-1, 1),
                colors.HexColor("#222222")
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "ALIGN",
                (4, 1),
                (5, 1),
                "RIGHT"
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
                (-1, 0),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                6
            ),

            (
                "TOPPADDING",
                (0, 1),
                (-1, 1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 1),
                (-1, 1),
                7
            )

        ])
    )

    return tabela


# =========================================================
# TABELA DE CONTROLES
# =========================================================

def criar_tabela_controles(controles):

    dados = [

        [
            "PESSOA",
            "CONTROLE",
            "TAM.",
            "QTD.",
            "TOTAL",
            "PAGO",
            "RESTANTE",
            "STATUS"
        ]

    ]

    for item in controles:

        total = float(
            item.get("valor_total", 0) or 0
        )

        pago = float(
            item.get("valor_pago", 0) or 0
        )

        restante = max(
            total - pago,
            0
        )

        nome = (
            item.get("nome_pessoa")
            or "Integrante"
        )

        descricao = (
            item.get("descricao")
            or "-"
        )

        tamanho = (
            item.get("tamanho")
            or "-"
        )

        quantidade = (
            item.get("quantidade")
            or 0
        )

        status = (
            item.get("status")
            or "PENDENTE"
        )

        if status == "PAGO":

            status_exibicao = "PAGO"

        elif status == "PARCIAL":

            status_exibicao = "PARCIAL"

        elif status == "CANCELADO":

            status_exibicao = "CANCELADO"

        else:

            status_exibicao = "PENDENTE"

        dados.append([

            Paragraph(
                str(nome),
                ParagraphStyle(
                    "PessoaTabela",
                    fontName="Helvetica",
                    fontSize=7,
                    leading=8
                )
            ),

            Paragraph(
                str(descricao),
                ParagraphStyle(
                    "DescricaoTabela",
                    fontName="Helvetica",
                    fontSize=7,
                    leading=8
                )
            ),

            str(tamanho),

            quantidade_formatada(
                quantidade
            ),

            moeda(total),

            moeda(pago),

            moeda(restante),

            status_exibicao

        ])

    tabela = Table(
        dados,
        colWidths=[
            38 * mm,
            40 * mm,
            15 * mm,
            12 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
            20 * mm
        ],
        repeatRows=1
    )

    estilo = [

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
            (-1, 0),
            7
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, 0),
            "CENTER"
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

        (
            "FONTNAME",
            (0, 1),
            (-1, -1),
            "Helvetica"
        ),

        (
            "FONTSIZE",
            (0, 1),
            (-1, -1),
            7
        ),

        (
            "ALIGN",
            (2, 1),
            (3, -1),
            "CENTER"
        ),

        (
            "ALIGN",
            (4, 1),
            (6, -1),
            "RIGHT"
        ),

        (
            "ALIGN",
            (7, 1),
            (7, -1),
            "CENTER"
        ),

        (
            "ALIGN",
            (0, 1),
            (1, -1),
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

    ]

    # =====================================================
    # STATUS
    # =====================================================

    for linha in range(1, len(dados)):

        status = dados[linha][7]

        if status == "PAGO":

            estilo.extend([

                (
                    "TEXTCOLOR",
                    (7, linha),
                    (7, linha),
                    colors.HexColor("#198754")
                ),

                (
                    "FONTNAME",
                    (7, linha),
                    (7, linha),
                    "Helvetica-Bold"
                )

            ])

        elif status == "PARCIAL":

            estilo.extend([

                (
                    "TEXTCOLOR",
                    (7, linha),
                    (7, linha),
                    colors.HexColor("#996c00")
                ),

                (
                    "FONTNAME",
                    (7, linha),
                    (7, linha),
                    "Helvetica-Bold"
                )

            ])

        elif status == "CANCELADO":

            estilo.extend([

                (
                    "TEXTCOLOR",
                    (7, linha),
                    (7, linha),
                    colors.HexColor("#dc3545")
                ),

                (
                    "FONTNAME",
                    (7, linha),
                    (7, linha),
                    "Helvetica-Bold"
                )

            ])

        else:

            estilo.extend([

                (
                    "TEXTCOLOR",
                    (7, linha),
                    (7, linha),
                    colors.HexColor("#666666")
                ),

                (
                    "FONTNAME",
                    (7, linha),
                    (7, linha),
                    "Helvetica-Bold"
                )

            ])

    tabela.setStyle(
        TableStyle(estilo)
    )

    return tabela


# =========================================================
# TABELA RESUMO POR TAMANHO
# =========================================================

def criar_tabela_resumo_tamanhos(controles):

    tamanhos_ordem = [
        "PP",
        "P",
        "M",
        "G",
        "GG",
        "XG",
        "XXG",
        "XXXL"
    ]

    quantidades = {}

    for item in controles:

        tamanho = (
            str(item.get("tamanho") or "-")
            .strip()
            .upper()
        )

        quantidade = (
            item.get("quantidade", 0)
            or 0
        )

        try:
            quantidade = float(quantidade)
        except Exception:
            quantidade = 0

        quantidades[tamanho] = (
            quantidades.get(tamanho, 0)
            + quantidade
        )

    tamanhos_encontrados = [
        tamanho
        for tamanho in tamanhos_ordem
        if tamanho in quantidades
    ]

    outros = sorted(
        [
            tamanho
            for tamanho in quantidades
            if tamanho not in tamanhos_ordem
        ]
    )

    tamanhos_finais = (
        tamanhos_encontrados
        + outros
    )

    dados = [

        [
            "TAM.",
            "QTD."
        ]

    ]

    total_quantidade = 0

    for tamanho in tamanhos_finais:

        quantidade = quantidades[tamanho]

        total_quantidade += quantidade

        dados.append([

            tamanho,

            quantidade_formatada(
                quantidade
            )

        ])

    dados.append([

        "TOTAL",

        quantidade_formatada(
            total_quantidade
        )

    ])

    tabela = Table(
        dados,
        colWidths=[
            35 * mm,
            35 * mm
        ],
        hAlign="LEFT"
    )

    estilo = [

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
            (-1, 0),
            8
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, 0),
            "CENTER"
        ),

        (
            "FONTNAME",
            (0, 1),
            (-1, -2),
            "Helvetica"
        ),

        (
            "FONTSIZE",
            (0, 1),
            (-1, -2),
            8
        ),

        (
            "ALIGN",
            (0, 1),
            (0, -1),
            "CENTER"
        ),

        (
            "ALIGN",
            (1, 1),
            (1, -1),
            "CENTER"
        ),

        (
            "BACKGROUND",
            (0, -1),
            (-1, -1),
            colors.HexColor("#eeeeee")
        ),

        (
            "FONTNAME",
            (0, -1),
            (-1, -1),
            "Helvetica-Bold"
        ),

        (
            "FONTSIZE",
            (0, -1),
            (-1, -1),
            8
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
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -2),
            [
                colors.white,
                colors.HexColor("#f5f5f5")
            ]
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4
        )

    ]

    tabela.setStyle(
        TableStyle(estilo)
    )

    return tabela


# =========================================================
# GERAR PDF
# =========================================================

def gerar_pdf_relatorio_controles(
    temporada,
    controles,
    grupo=None
):

    buffer = BytesIO()

    documento = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=18 * mm,
        leftMargin=18 * mm,

        topMargin=98 * mm,
        bottomMargin=22 * mm

    )

    documento.temporada = temporada

    documento.grupo = (
        grupo
        if grupo
        else ""
    )

    estilos = criar_estilos()

    elementos = []

    # =====================================================
    # ESPAÇO APÓS CABEÇALHO
    # =====================================================

    elementos.append(
        Spacer(1, 5)
    )

    # =====================================================
    # GARANTIR LISTA
    # =====================================================

    controles = controles or []

    # =====================================================
    # ORDENAR CONTROLES POR STATUS
    # =====================================================

    ordem_status = {
        "PAGO": 1,
        "PARCIAL": 2,
        "PENDENTE": 3,
        "CANCELADO": 4
    }

    controles = sorted(
        controles,
        key=lambda item: ordem_status.get(
            item.get("status") or "PENDENTE",
            3
        )
    )

    # =====================================================
    # CALCULAR RESUMO
    # =====================================================

    total_controles = 0

    total_valor = 0
    total_pago = 0
    total_pendente = 0

    quantidade_pagos = 0
    quantidade_parciais = 0
    quantidade_pendentes = 0

    for item in controles:

        # =================================================
        # QUANTIDADE DO PEDIDO
        # =================================================

        quantidade = item.get(
            "quantidade",
            0
        ) or 0

        try:
            quantidade = float(quantidade)
        except Exception:
            quantidade = 0

        total_controles += quantidade

        # =================================================
        # VALORES
        # =================================================

        total = float(
            item.get("valor_total", 0) or 0
        )

        pago = float(
            item.get("valor_pago", 0) or 0
        )

        restante = max(
            total - pago,
            0
        )

        total_valor += total
        total_pago += pago
        total_pendente += restante

        # =================================================
        # STATUS
        # =================================================

        status = (
            item.get("status")
            or "PENDENTE"
        )

        if status == "CANCELADO":
            continue

        if pago >= total and total > 0:

            quantidade_pagos += quantidade

        elif pago > 0:

            quantidade_parciais += quantidade

        else:

            quantidade_pendentes += quantidade

    # =====================================================
    # TÍTULO DA SEÇÃO
    # =====================================================

    elementos.append(

        Paragraph(
            "Resumo dos Controles",
            estilos["secao"]
        )

    )

    # =====================================================
    # TABELA RESUMO
    # =====================================================

    elementos.append(

        criar_tabela_resumo(

            total_controles,
            total_pago,
            total_pendente,
            quantidade_pagos,
            quantidade_parciais,
            quantidade_pendentes

        )

    )

    elementos.append(
        Spacer(1, 12)
    )

    # =====================================================
    # INFORMAÇÃO FINANCEIRA
    # =====================================================

    percentual_pago = 0

    if total_valor > 0:

        percentual_pago = (
            total_pago / total_valor
        ) * 100

    percentual_pendente = 0

    if total_valor > 0:

        percentual_pendente = (
            total_pendente / total_valor
        ) * 100

    texto = (

        f"<b>Valor total dos controles:</b> "
        f"{moeda(total_valor)} &nbsp;&nbsp; "

        f"<b>Total recebido:</b> "
        f"{moeda(total_pago)} &nbsp;&nbsp; "

        f"<b>Total pendente:</b> "
        f"{moeda(total_pendente)}"

    )

    elementos.append(

        Paragraph(
            texto,
            estilos["normal"]
        )

    )

    elementos.append(
        Spacer(1, 5)
    )

    texto_percentuais = (

        f"<b>Percentual recebido:</b> "
        f"{percentual_pago:.2f}%".replace(".", ",")

        + " &nbsp;&nbsp; "

        +

        f"<b>Percentual pendente:</b> "
        f"{percentual_pendente:.2f}%".replace(".", ",")

    )

    elementos.append(

        Paragraph(
            texto_percentuais,
            estilos["normal"]
        )

    )

    elementos.append(
        Spacer(1, 12)
    )

    # =====================================================
    # RELAÇÃO DE CONTROLES
    # =====================================================

    elementos.append(

        Paragraph(
            "Situação dos Controles",
            estilos["secao"]
        )

    )

    # =====================================================
    # TABELA
    # =====================================================

    if controles:

        elementos.append(

            criar_tabela_controles(
                controles
            )

        )

    else:

        elementos.append(

            Paragraph(
                "Nenhum controle financeiro cadastrado para os filtros selecionados.",
                estilos["normal"]
            )

        )

    # =====================================================
    # RESUMO POR TAMANHO
    # =====================================================

    if controles:

        resumo_tamanhos = [

            Spacer(1, 12),

            Paragraph(
                "Resumo por Tamanho",
                estilos["secao"]
            ),

            criar_tabela_resumo_tamanhos(
                controles
            )

        ]

        elementos.append(
            KeepTogether(
                resumo_tamanhos
            )
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