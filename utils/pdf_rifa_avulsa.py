from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# =========================================================
# CONFIGURAÇÃO DA RIFA
# =========================================================
#
# ALTERE SOMENTE ESTES CAMPOS
# =========================================================

VALOR_POR_NUMERO = 2.00

# Quantidade de pessoas que receberão rifas
QUANTIDADE_PESSOAS = 50

# Quantidade de rifas que cada pessoa receberá
RIFAS_POR_PESSOA = 25

# Número onde a sequência começa
NUMERO_INICIAL = 2321

# Nome que aparecerá nas rifas
VENDEDOR = "Brilho Negro"

PREMIO = "Prêmio da Rifa"

DATA_SORTEIO = "03/09/2026"


# =========================================================
# CÁLCULO AUTOMÁTICO
# =========================================================

TOTAL_RIFAS = (
    QUANTIDADE_PESSOAS
    * RIFAS_POR_PESSOA
)

NUMERO_FINAL = (
    NUMERO_INICIAL
    + TOTAL_RIFAS
    - 1
)


# =========================================================
# CAMINHOS
# =========================================================

PASTA_PROGRAMA = os.path.dirname(
    os.path.abspath(__file__)
)


# A pasta static/img fica junto do .py
PASTA_LOGO = os.path.join(
    PASTA_PROGRAMA,
    "static",
    "img"
)


CAMINHO_LOGO = os.path.join(
    PASTA_LOGO,
    "logo_transparente.png"
)


# =========================================================
# NOME DO ARQUIVO
# =========================================================

NOME_ARQUIVO = (
    f"rifas_avulsas_"
    f"{NUMERO_INICIAL:03d}_a_"
    f"{NUMERO_FINAL:03d}.pdf"
)


CAMINHO_PDF = os.path.join(
    PASTA_PROGRAMA,
    NOME_ARQUIVO
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
        # TAMANHO DA LOGO
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
            self.altura_rifa
            - tamanho_logo
        ) / 2

        x_canhoto = (
            self.largura_canhoto
            - tamanho_logo
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
# GERAR PDF
# =========================================================

def gerar_pdf_rifas_avulsas():

    buffer = BytesIO()

    # =====================================================
    # TAMANHO DA PÁGINA
    # =====================================================

    largura_pagina, altura_pagina = A4

    # =====================================================
    # MARGENS
    # =====================================================

    margem_horizontal = 3 * mm
    margem_vertical = 3 * mm

    # =====================================================
    # ESPAÇAMENTO ENTRE RIFAS
    # =====================================================

    espacamento_colunas = 3 * mm

    # =====================================================
    # LARGURA UTILIZÁVEL
    # =====================================================

    largura_util = (
        largura_pagina
        - (2 * margem_horizontal)
    )

    # =====================================================
    # LARGURA DE CADA RIFA
    # =====================================================

    largura_rifa = (
        largura_util
        - espacamento_colunas
    ) / 2

    # =====================================================
    # DOCUMENTO
    # =====================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=margem_horizontal,
        leftMargin=margem_horizontal,
        topMargin=margem_vertical,
        bottomMargin=margem_vertical,
    )

    estilos = getSampleStyleSheet()

    # =====================================================
    # ALTURA DA RIFA
    # =====================================================

    altura_rifa = 24 * mm

    # =====================================================
    # ESTILOS
    # =====================================================

    estilo_vendedor_label = ParagraphStyle(
        "VendedorLabel",
        parent=estilos["Normal"],
        alignment=0,
        fontName="Helvetica-Bold",
        fontSize=6,
        leading=6,
        textColor=colors.HexColor("#6c757d"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_vendedor_nome = ParagraphStyle(
        "VendedorNome",
        parent=estilos["Normal"],
        alignment=0,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=7.5,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =====================================================
    # CAMPOS NOME / TEL / ENDEREÇO
    # =====================================================

    estilo_campo = ParagraphStyle(
        "Campo",
        parent=estilos["Normal"],
        alignment=0,
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=6.5,
        textColor=colors.HexColor("#343a40"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =====================================================
    # NÚMERO
    # =====================================================

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

    # =====================================================
    # PRÊMIO
    # =====================================================

    estilo_premio = ParagraphStyle(
        "Premio",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=8.5,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =====================================================
    # DATA
    # =====================================================

    estilo_data = ParagraphStyle(
        "Data",
        parent=estilos["Normal"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=8,
        textColor=colors.HexColor("#495057"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # =====================================================
    # VALOR FORMATADO
    # =====================================================

    valor_formatado = (
        f"{VALOR_POR_NUMERO:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    # =====================================================
    # DIMENSÕES
    # =====================================================

    largura_canhoto = 56 * mm

    largura_principal = (
        largura_rifa
        - largura_canhoto
    )

    # =====================================================
    # NOME DO VENDEDOR
    # =====================================================

    def nome_curto_vendedor(nome):

        if not nome:
            return "SEM VENDEDOR"

        partes = (
            str(nome)
            .strip()
            .split()
        )

        if len(partes) >= 2:

            return (
                f"{partes[0]} "
                f"{partes[1]}"
            )

        if len(partes) == 1:

            return partes[0]

        return "SEM VENDEDOR"

    # =====================================================
    # CAMPO COM LINHA
    # =====================================================

    def criar_campo_linha(
        texto,
        altura=3.5 * mm
    ):

        return Table(
            [
                [
                    Paragraph(
                        texto,
                        estilo_campo,
                    )
                ]
            ],

            colWidths=[
                largura_canhoto - 4 * mm
            ],

            rowHeights=[
                altura
            ],

            style=TableStyle([

                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    0.6,
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

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "BOTTOM",
                ),

            ]),
        )

    # =====================================================
    # CRIAR UMA RIFA
    # =====================================================

    def criar_bilhete(numero):

        numero_formatado = (
            f"{int(numero):03d}"
        )

        vendedor_nome = (
            nome_curto_vendedor(VENDEDOR)
        )

        # =================================================
        # CANHOTO
        # =================================================

        conteudo_canhoto = [

            # =================================================
            # VENDEDOR + NÚMERO
            # =================================================

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

            # =================================================
            # NOME DO VENDEDOR
            # =================================================

            Paragraph(
                vendedor_nome,
                estilo_vendedor_nome,
            ),

            Spacer(
                1,
                0.3 * mm,
            ),

            # =================================================
            # NOME
            # =================================================

            criar_campo_linha(
                "NOME:",
                3.8 * mm
            ),

            # =================================================
            # ESPAÇO PARA PREENCHER NOME
            # =================================================

            Table(
                [[""]],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    3.0 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.black,
                    ),

                ]),
            ),

            # =================================================
            # TELEFONE
            # =================================================

            criar_campo_linha(
                "TEL:",
                3.8 * mm
            ),

            # =================================================
            # ENDEREÇO
            # =================================================

            criar_campo_linha(
                "ENDEREÇO:",
                3.8 * mm
            ),

            # =================================================
            # ESPAÇO FINAL
            # =================================================

            Table(
                [[""]],

                colWidths=[
                    largura_canhoto - 4 * mm
                ],

                rowHeights=[
                    3.0 * mm
                ],

                style=TableStyle([

                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.black,
                    ),

                ]),
            ),
        ]

        # =================================================
        # COMPROVANTE
        # =================================================

        principal = Table(
            [

                # =================================================
                # NÚMERO
                # =================================================

                [
                    Paragraph(
                        f"Nº {numero_formatado}",
                        estilo_numero_principal,
                    )
                ],

                # =================================================
                # PRÊMIO + VALOR
                # =================================================

                [
                    Paragraph(
                        f"🏆 {PREMIO}  R$ {valor_formatado}",
                        estilo_premio,
                    )
                ],

                # =================================================
                # DATA
                # =================================================

                [
                    Paragraph(
                        f"📅 Sorteio  {DATA_SORTEIO}",
                        estilo_data,
                    )
                ],

            ],

            colWidths=[
                largura_principal - 3 * mm
            ],

            rowHeights=[
                7 * mm,
                7 * mm,
                6 * mm,
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

        # =================================================
        # RIFA COMPLETA
        # =================================================

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

            caminho_logo=CAMINHO_LOGO,

            largura_canhoto=largura_canhoto,

            largura_principal=largura_principal,

            altura_rifa=altura_rifa,

        )

        tabela.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#f8f9fa"),
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#1a252f"),
                ),

                (
                    "LINEAFTER",
                    (0, 0),
                    (0, 0),
                    1,
                    colors.HexColor("#6c757d"),
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

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

    # =====================================================
    # ELEMENTOS DO PDF
    # =====================================================

    elementos = []

    # =====================================================
    # GERAR TODOS OS NÚMEROS
    # =====================================================

    numeros = range(
        NUMERO_INICIAL,
        NUMERO_FINAL + 1
    )

    linha_rifas = []

    for numero in numeros:

        linha_rifas.append(
            criar_bilhete(numero)
        )

        # =================================================
        # DUAS RIFAS POR LINHA
        # =================================================

        if len(linha_rifas) == 2:

            linha = Table(
                [linha_rifas],

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

                    (
                        "LEFTPADDING",
                        (1, 0),
                        (1, 0),
                        espacamento_colunas,
                    ),

                ])
            )

            elementos.append(linha)

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

        elementos.append(linha)

    # =====================================================
    # GERAR PDF
    # =====================================================

    doc.build(elementos)

    buffer.seek(0)

    with open(
        CAMINHO_PDF,
        "wb"
    ) as arquivo:

        arquivo.write(
            buffer.getvalue()
        )

    return CAMINHO_PDF


# =========================================================
# EXECUÇÃO DIRETA
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("             GERADOR DE RIFAS AVULSAS")
    print("=" * 65)
    print()

    print(
        f"Valor por número      : R$ {VALOR_POR_NUMERO:.2f}"
    )

    print(
        f"Quantidade de pessoas : {QUANTIDADE_PESSOAS}"
    )

    print(
        f"Rifas por pessoa      : {RIFAS_POR_PESSOA}"
    )

    print(
        f"Total de rifas        : {TOTAL_RIFAS}"
    )

    print(
        f"Número inicial        : {NUMERO_INICIAL:03d}"
    )

    print(
        f"Número final          : {NUMERO_FINAL:03d}"
    )

    print(
        f"Vendedor              : {VENDEDOR}"
    )

    print(
        f"Prêmio                : {PREMIO}"
    )

    print(
        f"Data do sorteio       : {DATA_SORTEIO}"
    )

    print()

    # =====================================================
    # CONFERÊNCIA
    # =====================================================

    print(
        f"Distribuição          : "
        f"{QUANTIDADE_PESSOAS} pessoas x "
        f"{RIFAS_POR_PESSOA} rifas"
    )

    print(
        f"                       = {TOTAL_RIFAS} rifas"
    )

    print()

    # =====================================================
    # VERIFICAR LOGO
    # =====================================================

    if not os.path.exists(CAMINHO_LOGO):

        print("AVISO: Logo não encontrada!")
        print()
        print("Esperado em:")
        print(CAMINHO_LOGO)
        print()

    else:

        print("Logo encontrada.")

    # =====================================================
    # GERAR
    # =====================================================

    try:

        caminho = gerar_pdf_rifas_avulsas()

        print()
        print("=" * 65)
        print("              PDF GERADO COM SUCESSO!")
        print("=" * 65)
        print()

        print("Arquivo:")
        print(caminho)

        print()

        print(
            f"Total de rifas: {TOTAL_RIFAS}"
        )

        print(
            f"Sequência: "
            f"{NUMERO_INICIAL:03d} "
            f"até "
            f"{NUMERO_FINAL:03d}"
        )

        print()

        print(
            f"Cada pessoa recebe: "
            f"{RIFAS_POR_PESSOA} rifas"
        )

        print(
            f"Quantidade de pessoas: "
            f"{QUANTIDADE_PESSOAS}"
        )

        print()

        print("=" * 65)

    except Exception as erro:

        print()
        print("=" * 65)
        print("                ERRO AO GERAR O PDF")
        print("=" * 65)
        print()

        print(erro)

        print()