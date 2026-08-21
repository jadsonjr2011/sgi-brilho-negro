from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from collections import OrderedDict

from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# =========================================================
# CACHE DA LOGO
# =========================================================

_logo_cache = {}


# =========================================================
# TABELA DA RIFA COM LOGO
# =========================================================

class TabelaRifaComLogo(Table):

    def __init__(
        self,
        *args,
        caminho_logo=None,
        largura_canhoto=0,
        largura_principal=0,
        altura_rifa=0,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        self.caminho_logo = caminho_logo
        self.largura_canhoto = largura_canhoto
        self.largura_principal = largura_principal
        self.altura_rifa = altura_rifa

    def draw(self):

        canvas = self.canv

        # =====================================================
        # DESENHA A TABELA
        # =====================================================

        super().draw()

        # =====================================================
        # VERIFICA LOGO
        # =====================================================

        caminho_logo = self.caminho_logo

        if not caminho_logo:
            return

        if not os.path.exists(caminho_logo):
            return

        # =====================================================
        # CARREGA LOGO
        # =====================================================

        try:

            if caminho_logo not in _logo_cache:

                _logo_cache[caminho_logo] = ImageReader(
                    caminho_logo
                )

            logo = _logo_cache[caminho_logo]

        except Exception:

            return

        canvas.saveState()

        # =====================================================
        # LOGO
        # =====================================================

        tamanho_logo = min(
            13 * mm,
            self.largura_canhoto - 6 * mm,
            self.altura_rifa - 4 * mm,
        )

        # =====================================================
        # TRANSPARÊNCIA
        # =====================================================

        try:
            canvas.setFillAlpha(0.10)
        except Exception:
            pass

        # =====================================================
        # POSIÇÃO
        # =====================================================

        y = (
            self.altura_rifa - tamanho_logo
        ) / 2

        x_canhoto = (
            self.largura_canhoto - tamanho_logo
        ) / 2

        # =====================================================
        # DESENHA LOGO
        # =====================================================

        canvas.drawImage(
            logo,
            x_canhoto,
            y,
            width=tamanho_logo,
            height=tamanho_logo,
            preserveAspectRatio=True,
            mask="auto",
        )

        canvas.restoreState()


# =========================================================
# GERAR PDF DA RIFA
# =========================================================

def gerar_pdf_rifa(rifa, numeros):

    """
    Gera PDF das rifas.

    Layout:

    A4 retrato

    Duas rifas lado a lado.

    Cada rifa possui:

    - Canhoto maior
    - Comprovante menor
    - Número em destaque
    - Vendedor com primeiro e segundo nome
    - Campo NOME
    - Campo TEL
    - Campo ENDEREÇO
    - Prêmio
    - Valor
    - Data do sorteio

    Altura reduzida para permitir aproximadamente
    11 rifas por coluna.
    """

    buffer = BytesIO()

    # =========================================================
    # TAMANHO DA PÁGINA
    # =========================================================

    largura_pagina, altura_pagina = A4

    # =========================================================
    # MARGENS
    # =========================================================

    margem_horizontal = 3 * mm
    margem_vertical = 3 * mm

    # =========================================================
    # ESPAÇO ENTRE AS DUAS RIFAS
    # =========================================================

    espacamento_colunas = 3 * mm

    # =========================================================
    # LARGURA UTILIZÁVEL
    # =========================================================

    largura_util = (
        largura_pagina
        - (2 * margem_horizontal)
    )

    # =========================================================
    # LARGURA DE CADA RIFA
    # =========================================================

    largura_rifa = (
        largura_util
        - espacamento_colunas
    ) / 2

    # =========================================================
    # DOCUMENTO
    # =========================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=margem_horizontal,
        leftMargin=margem_horizontal,
        topMargin=margem_vertical,
        bottomMargin=margem_vertical,
    )

    estilos = getSampleStyleSheet()

    # =========================================================
    # ALTURA DA RIFA
    # =========================================================
    #
    # 23 mm permite aproximadamente 11 rifas por coluna,
    # mantendo uma pequena folga para separação.
    #

    altura_rifa = 23 * mm

    # =========================================================
    # ESTILO GERAL
    # =========================================================

    estilo_rifa = ParagraphStyle(
        "RifaTitulo",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=8,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =========================================================
    # VENDEDOR
    # =========================================================

    estilo_vendedor_label = ParagraphStyle(
        "VendedorLabel",
        parent=estilos["Normal"],
        alignment=0,
        fontName="Helvetica-Bold",
        fontSize=5,
        leading=5,
        textColor=colors.HexColor("#6c757d"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_vendedor_nome = ParagraphStyle(
        "VendedorNome",
        parent=estilos["Normal"],
        alignment=0,
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=7,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =========================================================
    # CAMPOS DO CANHOTO
    # =========================================================

    estilo_campo = ParagraphStyle(
        "Campo",
        parent=estilos["Normal"],
        alignment=0,
        fontName="Helvetica",
        fontSize=5.5,
        leading=5.5,
        textColor=colors.HexColor("#495057"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =========================================================
    # NÚMERO DO COMPROVANTE
    # =========================================================

    estilo_numero_principal = ParagraphStyle(
        "NumeroPrincipal",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=13,
        textColor=colors.HexColor("#c0392b"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =========================================================
    # INFORMAÇÕES DO COMPROVANTE
    # =========================================================

    estilo_premio = ParagraphStyle(
        "Premio",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=5.7,
        leading=6,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_valor_principal = ParagraphStyle(
        "ValorPrincipal",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=5.8,
        leading=6,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_data = ParagraphStyle(
        "Data",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=5.5,
        leading=6,
        textColor=colors.HexColor("#495057"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =========================================================
    # DADOS DA RIFA
    # =========================================================

    valor = rifa.get("valor_numero") or 0

    try:

        valor_formatado = (
            f"{float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:

        valor_formatado = "0,00"

    data_sorteio = rifa.get("data_sorteio")

    if data_sorteio:

        data_sorteio = data_sorteio.strftime(
            "%d/%m/%Y"
        )

    else:

        data_sorteio = "-"

    premio = rifa.get("premio") or "-"

    # =========================================================
    # LOGO
    # =========================================================

    raiz_projeto = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    caminho_logo = os.path.join(
        raiz_projeto,
        "static",
        "img",
        "logo_transparente.png",
    )

    # =========================================================
    # NÚMEROS
    # =========================================================

    numeros_para_imprimir = [
        numero
        for numero in numeros
        if numero.get("numero") is not None
    ]

    elementos = []

    # =========================================================
    # DIMENSÕES DA RIFA
    # =========================================================

    # Canhoto maior
    largura_canhoto = 56 * mm

    # Comprovante menor
    largura_principal = (
        largura_rifa
        - largura_canhoto
    )

    # =========================================================
    # LIMITAR NOME DO VENDEDOR
    # =========================================================

    def nome_curto_vendedor(nome):

        if not nome:

            return "SEM VENDEDOR"

        partes = str(nome).strip().split()

        if len(partes) >= 2:

            return (
                f"{partes[0]} "
                f"{partes[1]}"
            )

        if len(partes) == 1:

            return partes[0]

        return "SEM VENDEDOR"

    # =========================================================
    # CRIAR BILHETE
    # =========================================================

    def criar_bilhete(numero):

        numero_formatado = (
            f"{int(numero['numero']):03d}"
        )

        vendedor_nome = nome_curto_vendedor(
            numero.get("vendedor_nome")
        )

        # =====================================================
        # CANHOTO
        # =====================================================

        conteudo_canhoto = [

            # -------------------------------------------------
            # VENDEDOR + NÚMERO
            # -------------------------------------------------

            Table(
                [
                    [
                        Paragraph(
                            "VENDEDOR",
                            estilo_vendedor_label,
                        ),

                        Paragraph(
                            f"Nº {numero_formatado}",
                            ParagraphStyle(
                                "NumeroCanhoto",
                                parent=estilo_numero_principal,
                                fontSize=7.5,
                                leading=7.5,
                                alignment=0,
                            ),
                        ),
                    ]
                ],

                colWidths=[
                    39 * mm,
                    14 * mm,
                ],

                rowHeights=[
                    3 * mm
                ],

                style=TableStyle([

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                ]),
            ),

            # -------------------------------------------------
            # NOME DO VENDEDOR
            # -------------------------------------------------

            Paragraph(
                vendedor_nome,
                estilo_vendedor_nome,
            ),

            Spacer(
                1,
                0.15 * mm,
            ),

            # -------------------------------------------------
            # NOME
            # -------------------------------------------------

            Table(
                [
                    [
                        Paragraph(
                            "NOME:",
                            estilo_campo,
                        )
                    ]
                ],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    2.7 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                ]),
            ),

            Table(
                [[""]],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    2.5 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),

                ]),
            ),

            # -------------------------------------------------
            # TELEFONE
            # -------------------------------------------------

            Table(
                [
                    [
                        Paragraph(
                            "TEL:",
                            estilo_campo,
                        )
                    ]
                ],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    2.7 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                ]),
            ),

            # -------------------------------------------------
            # ENDEREÇO
            # -------------------------------------------------

            Table(
                [
                    [
                        Paragraph(
                            "ENDEREÇO:",
                            estilo_campo,
                        )
                    ]
                ],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    2.7 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                ]),
            ),

            Table(
                [[""]],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    2.3 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),

                ]),
            ),
        ]

        # =====================================================
        # COMPROVANTE
        # =====================================================

        principal = Table(
            [

                # -------------------------------------------------
                # NÚMERO
                # -------------------------------------------------

                [
                    Paragraph(
                        f"Nº {numero_formatado}",
                        estilo_numero_principal,
                    )
                ],

                # -------------------------------------------------
                # PRÊMIO + VALOR NA MESMA LINHA
                # -------------------------------------------------

                [
                    Paragraph(
                        f"🏆 Prêmio  R$ {valor_formatado}",
                        estilo_premio,
                    )
                ],

                # -------------------------------------------------
                # DATA NA MESMA LINHA
                # -------------------------------------------------

                [
                    Paragraph(
                        f"📅 Sorteio  {data_sorteio}",
                        estilo_data,
                    )
                ],

            ],

            colWidths=[
                largura_principal - 3 * mm
            ],

            rowHeights=[
                7 * mm,
                6 * mm,
                5 * mm,
            ],
        )

        principal.setStyle(
            TableStyle([

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

            ])
        )

        # =====================================================
        # RIFA COMPLETA
        # =====================================================

        tabela = TabelaRifaComLogo(

            [
                [
                    conteudo_canhoto,
                    principal,
                ]
            ],

            colWidths=[
                largura_canhoto,
                largura_principal,
            ],

            rowHeights=[
                altura_rifa
            ],

            caminho_logo=caminho_logo,

            largura_canhoto=largura_canhoto,

            largura_principal=largura_principal,

            altura_rifa=altura_rifa,

        )

        tabela.setStyle(
            TableStyle([

                # =================================================
                # FUNDO DO CANHOTO
                # =================================================

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#f8f9fa"),
                ),

                # =================================================
                # BORDA EXTERNA
                # =================================================

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#1a252f"),
                ),

                # =================================================
                # DIVISÃO CANHOTO / COMPROVANTE
                # =================================================

                (
                    "LINEAFTER",
                    (0, 0),
                    (0, 0),
                    1,
                    colors.HexColor("#6c757d"),
                ),

                # =================================================
                # ALINHAMENTO
                # =================================================

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                # =================================================
                # PADDING
                # =================================================

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0.5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0.5,
                ),

            ])
        )

        return tabela

    # =========================================================
    # AGRUPAR POR VENDEDOR
    # =========================================================

    grupos_vendedores = OrderedDict()

    for numero in numeros_para_imprimir:

        vendedor_nome = (
            numero.get("vendedor_nome")
            or "SEM VENDEDOR"
        )

        if vendedor_nome not in grupos_vendedores:

            grupos_vendedores[vendedor_nome] = []

        grupos_vendedores[vendedor_nome].append(
            numero
        )

    # =========================================================
    # GERAR PDF
    # =========================================================

    primeiro_grupo = True

    for vendedor_nome, numeros_vendedor in grupos_vendedores.items():

        # =====================================================
        # NOVA PÁGINA PARA CADA VENDEDOR
        # =====================================================

        if not primeiro_grupo:

            elementos.append(
                PageBreak()
            )

        primeiro_grupo = False

        # =====================================================
        # DUAS RIFAS POR LINHA
        # =====================================================

        linha_rifas = []

        for numero in numeros_vendedor:

            linha_rifas.append(
                criar_bilhete(numero)
            )

            # =================================================
            # FECHA COM DUAS RIFAS
            # =================================================

            if len(linha_rifas) == 2:

                linha = Table(
                    [
                        linha_rifas
                    ],

                    colWidths=[
                        largura_rifa,
                        largura_rifa,
                    ],

                    rowHeights=[
                        altura_rifa
                    ],

                    hAlign="LEFT",

                    spaceBefore=0,

                    spaceAfter=0,
                )

                linha.setStyle(
                    TableStyle([

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),

                        # =================================================
                        # ESPAÇO ENTRE AS RIFAS
                        # =================================================

                        (
                            "LEFTPADDING",
                            (1, 0),
                            (1, 0),
                            espacamento_colunas,
                        ),

                    ])
                )

                elementos.append(
                    linha
                )

                # Espaço mínimo entre linhas
                elementos.append(
                    Spacer(
                        1,
                        0.8 * mm,
                    )
                )

                linha_rifas = []

        # =====================================================
        # ÚLTIMA RIFA ÍMPAR
        # =====================================================

        if linha_rifas:

            linha = Table(
                [
                    [
                        linha_rifas[0],
                        "",
                    ]
                ],

                colWidths=[
                    largura_rifa,
                    largura_rifa,
                ],

                rowHeights=[
                    altura_rifa
                ],

                hAlign="LEFT",
            )

            linha.setStyle(
                TableStyle([

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),

                ])
            )

            elementos.append(
                linha
            )

    # =========================================================
    # SEM NÚMEROS
    # =========================================================

    if not numeros_para_imprimir:

        elementos.append(
            Paragraph(
                "Nenhum número disponível para geração da rifa.",
                estilo_rifa,
            )
        )

    # =========================================================
    # GERAR PDF
    # =========================================================

    doc.build(elementos)

    buffer.seek(0)

    return buffer