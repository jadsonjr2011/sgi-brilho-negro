# ============================================================
# PDF — PRESTAÇÃO DE CONTAS DO BINGO
# ============================================================

from io import BytesIO
from datetime import datetime
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
    KeepTogether
)

from sqlalchemy import text


# ============================================================
# CONFIGURAÇÕES
# ============================================================

LOGO_PATH = os.path.join(
    "static",
    "img",
    "logo_relatorio.PNG"
)


# ============================================================
# CORES
# ============================================================

COR_PRINCIPAL = colors.HexColor("#1B0001")
COR_TEXTO = colors.HexColor("#222222")
COR_CINZA = colors.HexColor("#666666")
COR_BORDA = colors.HexColor("#CCCCCC")
COR_FUNDO = colors.HexColor("#F2F2F2")
COR_FUNDO_DESTAQUE = colors.HexColor("#F8F0F0")
COR_BRANCO = colors.white


# ============================================================
# FORMATAÇÃO
# ============================================================

def formatar_moeda(valor):

    valor = float(valor or 0)

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formatar_data(data):

    if not data:
        return "-"

    try:

        if hasattr(data, "strftime"):
            return data.strftime("%d/%m/%Y")

        data = str(data)

        if len(data) >= 10:
            return (
                f"{data[8:10]}/"
                f"{data[5:7]}/"
                f"{data[0:4]}"
            )

    except Exception:
        pass

    return str(data)


def formatar_percentual(valor):

    return (
        f"{float(valor or 0):.1f}%"
        .replace(".", ",")
    )


# ============================================================
# GERAR PDF
# ============================================================

def gerar_pdf_prestacao_bingo(db, bingo_id):

    # ========================================================
    # BINGO
    # ========================================================

    bingo = db.execute(
        text("""
            SELECT
                b.*,
                t.nome AS temporada_nome

            FROM bingos b

            LEFT JOIN temporadas t
                ON t.id = b.temporada_id

            WHERE b.id = :id
        """),
        {
            "id": bingo_id
        }
    ).mappings().first()

    if not bingo:
        raise ValueError("Bingo não encontrado.")


    # ========================================================
    # CARTELAS
    # ========================================================

    resumo_cartelas = db.execute(
        text("""
            SELECT

                COUNT(*) AS total,

                COUNT(
                    CASE
                        WHEN UPPER(status) = 'VENDIDA'
                        THEN 1
                    END
                ) AS vendidas,

                COUNT(
                    CASE
                        WHEN UPPER(status) = 'DISPONIVEL'
                        THEN 1
                    END
                ) AS disponiveis

            FROM bingo_cartelas

            WHERE bingo_id = :bingo_id
        """),
        {
            "bingo_id": bingo_id
        }
    ).mappings().first()


    total_cartelas = int(
        resumo_cartelas["total"] or 0
    )

    cartelas_vendidas = int(
        resumo_cartelas["vendidas"] or 0
    )

    cartelas_disponiveis = int(
        resumo_cartelas["disponiveis"] or 0
    )


    # ========================================================
    # VALOR DA CARTELA
    # ========================================================

    valor_cartela = float(
        bingo["valor_cartela"] or 0
    )


    # ========================================================
    # RECEITA PREVISTA
    # ========================================================

    receita_prevista = (
        total_cartelas * valor_cartela
    )


    # ========================================================
    # VALOR PRESTADO
    #
    # Valor correspondente às cartelas efetivamente vendidas.
    # ========================================================

    valor_prestado = (
        cartelas_vendidas * valor_cartela
    )


    # ========================================================
    # PERCENTUAL VENDIDO
    # ========================================================

    percentual_vendido = 0

    if total_cartelas > 0:

        percentual_vendido = (
            cartelas_vendidas
            / total_cartelas
        ) * 100


    # ========================================================
    # VENDAS
    # ========================================================

    vendas = db.execute(
        text("""
            SELECT
                bv.id,
                bv.cartela_id,
                bv.integrante_id,
                bv.valor,
                bv.status,
                bv.data_venda,
                bv.data_pagamento,
                bv.comprador,
                bv.observacao,

                bc.numero AS numero_cartela,

                i.nome AS integrante_nome

            FROM bingo_vendas bv

            LEFT JOIN bingo_cartelas bc
                ON bc.id = bv.cartela_id

            LEFT JOIN integrantes i
                ON i.id = bv.integrante_id

            WHERE bv.bingo_id = :bingo_id

            ORDER BY
                bv.data_venda ASC NULLS LAST,
                bv.id ASC
        """),
        {
            "bingo_id": bingo_id
        }
    ).mappings().all()


    # ========================================================
    # RESUMO DAS VENDAS
    # ========================================================

    total_vendas_registradas = len(vendas)


    # ========================================================
    # RECEITA REGISTRADA
    # ========================================================

    receita_vendas = sum(
        float(venda["valor"] or 0)
        for venda in vendas
    )


    # ========================================================
    # FALLBACK
    #
    # Caso existam cartelas vendidas, mas ainda não existam
    # registros financeiros nas vendas, usamos o valor prestado.
    # ========================================================

    if receita_vendas <= 0 and cartelas_vendidas > 0:

        receita_vendas = valor_prestado


    # ========================================================
    # STATUS DOS PAGAMENTOS
    # ========================================================

    pagamentos = {}


    for venda in vendas:

        status = (
            venda["status"]
            or "NÃO INFORMADO"
        ).upper()

        valor = float(
            venda["valor"] or 0
        )

        pagamentos[status] = (
            pagamentos.get(status, 0)
            + valor
        )


    # ========================================================
    # VALORES PAGOS E PENDENTES
    # ========================================================

    total_pago = 0
    total_pendente = 0


    for venda in vendas:

        status = (
            venda["status"]
            or ""
        ).upper()

        valor = float(
            venda["valor"] or 0
        )


        if status in {
            "PAGO",
            "PAGA",
            "PAGAMENTO",
            "QUITADO",
            "QUITADA",
            "PAGO_TOTAL",
            "PAGO TOTAL"
        }:

            total_pago += valor


        elif status in {
            "PENDENTE",
            "AGUARDANDO",
            "ABERTO",
            "NAO_PAGO",
            "NÃO_PAGO",
            "NAO PAGO",
            "NÃO PAGO"
        }:

            total_pendente += valor


    # ========================================================
    # PERCENTUAIS FINANCEIROS
    # ========================================================

    percentual_recebido = 0
    percentual_pendente = 0


    if valor_prestado > 0:

        percentual_recebido = (
            total_pago
            / valor_prestado
        ) * 100

        percentual_pendente = (
            total_pendente
            / valor_prestado
        ) * 100


    # ========================================================
    # BUFFER
    # ========================================================

    buffer = BytesIO()


    # ========================================================
    # DOCUMENTO
    # ========================================================

    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=15 * mm,
        leftMargin=15 * mm,

        topMargin=15 * mm,
        bottomMargin=15 * mm

    )


    # ========================================================
    # ESTILOS
    # ========================================================

    estilos = getSampleStyleSheet()


    titulo = ParagraphStyle(
        "TituloBingo",
        parent=estilos["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=20,
        alignment=TA_CENTER,
        textColor=COR_PRINCIPAL,
        spaceAfter=5
    )


    subtitulo = ParagraphStyle(
        "SubtituloBingo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=COR_CINZA
    )


    nome_bingo = ParagraphStyle(
        "NomeBingo",
        parent=subtitulo,
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=COR_PRINCIPAL
    )


    secao = ParagraphStyle(
        "SecaoBingo",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        textColor=COR_PRINCIPAL,
        spaceBefore=8,
        spaceAfter=5
    )


    normal = ParagraphStyle(
        "NormalBingo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=COR_TEXTO
    )


    pequeno = ParagraphStyle(
        "PequenoBingo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=COR_TEXTO
    )


    valor_style = ParagraphStyle(
        "ValorBingo",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        alignment=TA_RIGHT,
        textColor=COR_TEXTO
    )

    valor_centralizado = ParagraphStyle(
        "ValorCentralizadoBingo",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        alignment=TA_CENTER,
        textColor=COR_TEXTO
    )


    # ========================================================
    # ESTILO ESPECÍFICO PARA CABEÇALHOS DAS TABELAS
    #
    # IMPORTANTE:
    # O texto dos Paragraphs precisa ter a cor branca aqui.
    # O TEXTCOLOR da TableStyle sozinho não altera Paragraph.
    # ========================================================

    cabecalho_branco = ParagraphStyle(
        "CabecalhoBrancoBingo",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=COR_BRANCO
    )


    cabecalho_branco_pequeno = ParagraphStyle(
        "CabecalhoBrancoPequenoBingo",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        alignment=TA_CENTER,
        textColor=COR_BRANCO
    )


    # ========================================================
    # ELEMENTOS
    # ========================================================

    elementos = []


    # ========================================================
    # LOGO
    # ========================================================

    if os.path.exists(LOGO_PATH):

        try:

            logo = Image(
                LOGO_PATH,
                width=32 * mm,
                height=18 * mm
            )

            logo.hAlign = "CENTER"

            elementos.append(logo)

            elementos.append(
                Spacer(1, 3 * mm)
            )

        except Exception:

            pass


    # ========================================================
    # CABEÇALHO
    # ========================================================

    elementos.append(
        Paragraph(
            "PRESTAÇÃO DE CONTAS — BINGO",
            titulo
        )
    )


    elementos.append(
        Paragraph(
            str(
                bingo["nome"]
                or "Bingo"
            ),
            nome_bingo
        )
    )


    elementos.append(
        Spacer(1, 3 * mm)
    )


    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=COR_PRINCIPAL,
            spaceBefore=2,
            spaceAfter=7
        )
    )


    # ========================================================
    # DADOS DO BINGO
    # ========================================================

    elementos.append(
        Paragraph(
            "DADOS DO BINGO",
            secao
        )
    )


    dados_bingo = [

        [
            Paragraph(
                "<b>Bingo</b>",
                normal
            ),

            Paragraph(
                str(
                    bingo["nome"]
                    or "-"
                ),
                normal
            ),

            Paragraph(
                "<b>Temporada</b>",
                normal
            ),

            Paragraph(
                str(
                    bingo["temporada_nome"]
                    or "-"
                ),
                normal
            )
        ],

        [
            Paragraph(
                "<b>Data</b>",
                normal
            ),

            Paragraph(
                formatar_data(
                    bingo["data"]
                ),
                normal
            ),

            Paragraph(
                "<b>Horário</b>",
                normal
            ),

            Paragraph(
                str(
                    bingo["horario"]
                    or "-"
                ),
                normal
            )
        ],

        [
            Paragraph(
                "<b>Local</b>",
                normal
            ),

            Paragraph(
                str(
                    bingo["local"]
                    or "-"
                ),
                normal
            ),

            Paragraph(
                "<b>Status</b>",
                normal
            ),

            Paragraph(
                str(
                    bingo["status"]
                    or "-"
                ),
                normal
            )
        ],

        [
            Paragraph(
                "<b>Valor da cartela</b>",
                normal
            ),

            Paragraph(
                formatar_moeda(
                    valor_cartela
                ),
                normal
            ),

            Paragraph(
                "<b>Cartelas previstas</b>",
                normal
            ),

            Paragraph(
                str(
                    total_cartelas
                ),
                normal
            )
        ]
    ]


    tabela = Table(
        dados_bingo,
        colWidths=[
            32 * mm,
            58 * mm,
            35 * mm,
            50 * mm
        ]
    )


    tabela.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                COR_BORDA
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                COR_FUNDO
            ),

            (
                "BACKGROUND",
                (2, 0),
                (2, -1),
                COR_FUNDO
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


    elementos.append(tabela)


    # ========================================================
    # RESUMO DAS CARTELAS
    # ========================================================

    elementos.append(
        Paragraph(
            "RESUMO DAS CARTELAS",
            secao
        )
    )


    resumo = [

        [
            Paragraph(
                "Cartelas",
                cabecalho_branco
            ),

            Paragraph(
                "Vendidas",
                cabecalho_branco
            ),

            Paragraph(
                "Disponíveis",
                cabecalho_branco
            ),

            Paragraph(
                "% vendido",
                cabecalho_branco
            )
        ],

        [
            Paragraph(
                str(total_cartelas),
                valor_centralizado
            ),

            Paragraph(
                str(cartelas_vendidas),
                valor_centralizado
            ),

            Paragraph(
                str(cartelas_disponiveis),
                valor_centralizado
            ),

            Paragraph(
                formatar_percentual(
                    percentual_vendido
                ),
                valor_centralizado
            )
        ]
    ]


    tabela_resumo = Table(
        resumo,
        colWidths=[
            43 * mm,
            43 * mm,
            43 * mm,
            43 * mm
        ]
    )


    tabela_resumo.setStyle(
        TableStyle([

            # ====================================================
            # CABEÇALHO
            # ====================================================

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                COR_PRINCIPAL
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                COR_BRANCO
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            # ====================================================
            # VALORES
            # ====================================================

            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                COR_BRANCO
            ),

            (
                "TEXTCOLOR",
                (0, 1),
                (-1, 1),
                COR_TEXTO
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),

            # ====================================================
            # ALINHAMENTO
            # ====================================================

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

            # ====================================================
            # BORDAS
            # ====================================================

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                COR_BORDA
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                COR_BORDA
            ),

            # ====================================================
            # ESPAÇAMENTO
            # ====================================================

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


    elementos.append(
        tabela_resumo
    )


    # ========================================================
    # RESUMO FINANCEIRO
    # ========================================================

    elementos.append(
        Paragraph(
            "RESUMO FINANCEIRO",
            secao
        )
    )


    financeiro = [

        [
            Paragraph(
                "<b>Receita prevista</b>",
                normal
            ),

            Paragraph(
                formatar_moeda(
                    receita_prevista
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Valor prestado</b>",
                normal
            ),

            Paragraph(
                formatar_moeda(
                    valor_prestado
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Receita registrada nas vendas</b>",
                normal
            ),

            Paragraph(
                formatar_moeda(
                    receita_vendas
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Total de vendas registradas</b>",
                normal
            ),

            Paragraph(
                str(
                    total_vendas_registradas
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Total pago</b>",
                normal
            ),

            Paragraph(
                formatar_moeda(
                    total_pago
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Total pendente</b>",
                normal
            ),

            Paragraph(
                formatar_moeda(
                    total_pendente
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Percentual recebido</b>",
                normal
            ),

            Paragraph(
                formatar_percentual(
                    percentual_recebido
                ),
                valor_style
            )
        ],

        [
            Paragraph(
                "<b>Percentual pendente</b>",
                normal
            ),

            Paragraph(
                formatar_percentual(
                    percentual_pendente
                ),
                valor_style
            )
        ]

    ]


    tabela_financeiro = Table(
        financeiro,
        colWidths=[
            120 * mm,
            52 * mm
        ]
    )


    tabela_financeiro.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                COR_BORDA
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                COR_FUNDO
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "RIGHT"
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
            ),

            # ====================================================
            # DESTAQUE — VALOR PRESTADO
            # ====================================================

            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                COR_FUNDO_DESTAQUE
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),

            (
                "TEXTCOLOR",
                (1, 1),
                (1, 1),
                COR_PRINCIPAL
            )

        ])
    )


    elementos.append(
        tabela_financeiro
    )


    # ========================================================
    # RESUMO POR STATUS
    # ========================================================

    if pagamentos:

        elementos.append(
            Paragraph(
                "RESUMO POR STATUS",
                secao
            )
        )


        dados_status = [

            [
                Paragraph(
                    "Status",
                    cabecalho_branco
                ),

                Paragraph(
                    "Valor",
                    cabecalho_branco
                )
            ]

        ]


        for status, valor in sorted(
            pagamentos.items()
        ):

            dados_status.append(
                [
                    Paragraph(
                        str(status),
                        normal
                    ),

                    Paragraph(
                        formatar_moeda(valor),
                        valor_style
                    )
                ]
            )


        tabela_status = Table(
            dados_status,
            colWidths=[
                120 * mm,
                52 * mm
            ],
            repeatRows=1
        )


        tabela_status.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    COR_PRINCIPAL
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    COR_BRANCO
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT"
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
                    0.4,
                    COR_BORDA
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
            tabela_status
        )


    # ========================================================
    # DETALHAMENTO DAS VENDAS
    # ========================================================

    if vendas:

        elementos.append(
            Paragraph(
                "DETALHAMENTO DAS VENDAS",
                secao
            )
        )


        dados_vendas = [

            [
                Paragraph(
                    "Data",
                    cabecalho_branco_pequeno
                ),

                Paragraph(
                    "Cartela",
                    cabecalho_branco_pequeno
                ),

                Paragraph(
                    "Comprador",
                    cabecalho_branco_pequeno
                ),

                Paragraph(
                    "Responsável",
                    cabecalho_branco_pequeno
                ),

                Paragraph(
                    "Valor",
                    cabecalho_branco_pequeno
                ),

                Paragraph(
                    "Status",
                    cabecalho_branco_pequeno
                )
            ]

        ]


        for venda in vendas:

            comprador = (
                venda["comprador"]
                or "Não informado"
            )


            responsavel = (
                venda["integrante_nome"]
                or "Não informado"
            )


            dados_vendas.append(

                [

                    Paragraph(
                        formatar_data(
                            venda["data_venda"]
                        ),
                        pequeno
                    ),

                    Paragraph(
                        str(
                            venda["numero_cartela"]
                            or venda["cartela_id"]
                            or "-"
                        ),
                        pequeno
                    ),

                    Paragraph(
                        str(comprador),
                        pequeno
                    ),

                    Paragraph(
                        str(responsavel),
                        pequeno
                    ),

                    Paragraph(
                        formatar_moeda(
                            venda["valor"]
                        ),
                        pequeno
                    ),

                    Paragraph(
                        str(
                            venda["status"]
                            or "-"
                        ),
                        pequeno
                    )

                ]

            )


        tabela_vendas = Table(

            dados_vendas,

            colWidths=[

                23 * mm,
                18 * mm,
                43 * mm,
                42 * mm,
                25 * mm,
                22 * mm

            ],

            repeatRows=1

        )


        tabela_vendas.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    COR_PRINCIPAL
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    COR_BRANCO
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
                    7
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (1, -1),
                    "CENTER"
                ),

                (
                    "ALIGN",
                    (4, 1),
                    (4, -1),
                    "RIGHT"
                ),

                (
                    "ALIGN",
                    (5, 1),
                    (5, -1),
                    "CENTER"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    COR_BORDA
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
                    4
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )

            ])
        )


        elementos.append(
            tabela_vendas
        )


    # ========================================================
    # OBSERVAÇÕES
    # ========================================================

    if bingo["observacoes"]:

        elementos.append(
            Paragraph(
                "OBSERVAÇÕES",
                secao
            )
        )


        elementos.append(
            Paragraph(
                str(
                    bingo["observacoes"]
                ).replace(
                    "\n",
                    "<br/>"
                ),
                normal
            )
        )


    # ========================================================
    # DESCRIÇÃO
    # ========================================================

    if bingo["descricao"]:

        elementos.append(
            Paragraph(
                "DESCRIÇÃO",
                secao
            )
        )


        elementos.append(
            Paragraph(
                str(
                    bingo["descricao"]
                ).replace(
                    "\n",
                    "<br/>"
                ),
                normal
            )
        )


    # ========================================================
    # RODAPÉ
    # ========================================================

    elementos.append(
        Spacer(1, 10 * mm)
    )


    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=COR_BORDA,
            spaceBefore=2,
            spaceAfter=4
        )
    )


    elementos.append(
        Paragraph(
            "Documento gerado pelo Sistema de Gestão — Banda Brilho Negro",
            ParagraphStyle(
                "RodapeBingo",
                parent=pequeno,
                alignment=TA_CENTER,
                textColor=COR_CINZA
            )
        )
    )


    elementos.append(
        Paragraph(
            "Emissão: "
            + datetime.now().strftime(
                "%d/%m/%Y às %H:%M"
            ),
            ParagraphStyle(
                "EmissaoBingo",
                parent=pequeno,
                alignment=TA_CENTER,
                textColor=COR_CINZA
            )
        )
    )


    # ========================================================
    # GERAR PDF
    # ========================================================

    doc.build(elementos)


    buffer.seek(0)

    return buffer