from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
    Image,
    PageBreak,
)

class TabelaRifaComLogo(Table):

    def draw(self):

        canvas = self.canv

        # =====================================================
        # DESENHA PRIMEIRO A TABELA COMPLETA
        # =====================================================

        super().draw()

        # =====================================================
        # VERIFICA LOGO
        # =====================================================

        if not getattr(self, "caminho_logo", None):
            return

        if not os.path.exists(self.caminho_logo):
            return

        canvas.saveState()

        # =====================================================
        # TAMANHO DA MARCA D'ÁGUA
        # =====================================================

        tamanho_logo = 41 * mm

        # =====================================================
        # TRANSPARÊNCIA
        # =====================================================

        try:
            canvas.setFillAlpha(0.12)
        except Exception:
            pass

        # =====================================================
        # POSIÇÃO VERTICAL
        # =====================================================

        y = (
            (altura_rifa_local - tamanho_logo) / 2
        )

        # =====================================================
        # LOGO NO CANHOTO
        # =====================================================

        x_canhoto = (
            (largura_canhoto_local - tamanho_logo) / 2
        )

        canvas.drawImage(
            self.caminho_logo,
            x_canhoto,
            y,
            width=tamanho_logo,
            height=tamanho_logo,
            preserveAspectRatio=True,
            mask="auto",
        )

        # =====================================================
        # LOGO NO BILHETE PRINCIPAL
        # =====================================================

        x_principal = (
            largura_canhoto_local
            + (largura_principal_local - tamanho_logo) / 2
        )

        canvas.drawImage(
            self.caminho_logo,
            x_principal,
            y,
            width=tamanho_logo,
            height=tamanho_logo,
            preserveAspectRatio=True,
            mask="auto",
        )

        canvas.restoreState()

def gerar_pdf_rifa(rifa, numeros):
    """
    Gera PDF das rifas otimizado para caber em A4 sem estouro de layout.

    Layout:
    - A4 vertical
    - 1 rifa por linha
    - aproximadamente 6 rifas por folha
    - canhoto à esquerda
    - bilhete principal à direita
    - campos para preenchimento manual
    - logo transparente como marca d'água no canhoto
    - somente números DISPONIVEL e VENDIDO
    """

    buffer = BytesIO()

    # =========================================================
    # DOCUMENTO
    # =========================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=7 * mm,
        leftMargin=7 * mm,
        topMargin=2 * mm,
        bottomMargin=2 * mm,
    )

    estilos = getSampleStyleSheet()

    # =========================================================
    # ESTILOS
    # =========================================================

    # ---------------------------------------------------------
    # TÍTULO DA RIFA
    # ---------------------------------------------------------

    estilo_rifa = ParagraphStyle(
        "RifaTitulo",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_nome_rifa = ParagraphStyle(
        "NomeRifa",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#e67e22"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # VENDEDOR
    # ---------------------------------------------------------

    estilo_vendedor_label = ParagraphStyle(
        "VendedorLabel",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#6c757d"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_vendedor_nome = ParagraphStyle(
        "VendedorNome",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=10,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # CANHOTO
    # ---------------------------------------------------------

    estilo_canhoto = ParagraphStyle(
        "CanhotoTitulo",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_label = ParagraphStyle(
        "Label",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#495057"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_campo = ParagraphStyle(
        "Campo",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#495057"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # PRÊMIO
    # ---------------------------------------------------------

    estilo_premio_label = ParagraphStyle(
        "PremioLabel",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#6c757d"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_premio = ParagraphStyle(
        "Premio",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # INFORMAÇÕES
    # ---------------------------------------------------------

    estilo_info = ParagraphStyle(
        "Info",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#495057"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # RODAPÉ
    # ---------------------------------------------------------

    estilo_footer = ParagraphStyle(
        "Footer",
        parent=estilos["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#6c757d"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # NÚMEROS
    # ---------------------------------------------------------

    estilo_numero = ParagraphStyle(
        "Numero",
        parent=estilos["Normal"],
        alignment=TA_RIGHT,
        fontName="Courier-Bold",
        fontSize=11,
        leading=12,
        textColor=colors.HexColor("#c0392b"),
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_numero_grande = ParagraphStyle(
        "NumeroGrande",
        parent=estilos["Normal"],
        alignment=TA_RIGHT,
        fontName="Courier-Bold",
        fontSize=12,
        leading=13,
        textColor=colors.HexColor("#c0392b"),
        spaceAfter=0,
        spaceBefore=0,
    )

    # ---------------------------------------------------------
    # VALOR
    # ---------------------------------------------------------

    estilo_valor = ParagraphStyle(
        "Valor",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        spaceAfter=0,
        spaceBefore=0,
    )

    # =========================================================
    # DADOS DINÂMICOS DA RIFA
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
        data_sorteio = data_sorteio.strftime("%d/%m/%Y")
    else:
        data_sorteio = "-"

    nome_rifa = rifa.get("nome") or "-"
    premio = rifa.get("premio") or "-"

    # =========================================================
    # LOGO
    # =========================================================

    # Caminho da logo:
    # C:\Users\jadson.silva\Documents\Projeto_Brilho_Negro
    # \static\img\logo_transparente.png

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
    # NÚMEROS QUE SERÃO IMPRESSOS
    # =========================================================
    # Imprime todos os números cadastrados para o sorteio,
    # independentemente de estarem DISPONIVEL ou VENDIDO.
    #
    # O status será utilizado somente posteriormente,
    # durante a prestação de contas.

    numeros_para_imprimir = [
        numero
        for numero in numeros
        if numero.get("numero") is not None
    ]

    # =========================================================
    # ELEMENTOS DO PDF
    # =========================================================

    elementos = []

    # =========================================================
    # DIMENSÕES DA RIFA
    # =========================================================

    largura_canhoto = 53 * mm
    largura_principal = 143 * mm

    # Mantém exatamente o tamanho aprovado.
    altura_rifa = 40 * mm

    global largura_canhoto_local
    global largura_principal_local
    global altura_rifa_local

    largura_canhoto_local = largura_canhoto
    largura_principal_local = largura_principal
    altura_rifa_local = altura_rifa

    # =========================================================
    # FUNÇÃO PARA CRIAR UMA RIFA
    # =========================================================

    def criar_bilhete(numero, mostrar_vendedor=False):

        numero_formatado = f"{int(numero['numero']):03d}"
        vendedor_nome = (
            numero.get("vendedor_nome")
            or "SEM VENDEDOR"
        )

        # =====================================================
        # CANHOTO
        # =====================================================

        conteudo_canhoto = [

            # PRIMEIRA LINHA
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
                                parent=estilo_numero_grande,
                                fontSize=10,
                                leading=11,
                                alignment=TA_LEFT,
                                spaceAfter=0,
                                spaceBefore=0,
                            ),
                        ),
                    ]
                ],
                colWidths=[
                    27 * mm,
                    22 * mm,
                ],
                style=TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]),
            ),

            Spacer(1, 0.5 * mm),

            # NOME DO VENDEDOR
            Paragraph(
                vendedor_nome,
                estilo_vendedor_nome,
            ),

            Spacer(1, 1.5 * mm),

            # =====================================================
            # CAMPOS DO CLIENTE (CORRIGIDO)
            # =====================================================

            # NOME (Texto na 1ª linha)
            Table(
                [[Paragraph("NOME:", estilo_campo)]],
                colWidths=[49 * mm],
                style=TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]),
            ),

            # LINHA 1 DO NOME (Linha de preenchimento via Borda Inferior)
            Table(
                [[""]],
                colWidths=[49 * mm],
                rowHeights=[4.5 * mm],
                style=TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]),
            ),

            # LINHA 2 DO NOME
            Table(
                [[""]],
                colWidths=[49 * mm],
                rowHeights=[4.5 * mm],
                style=TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]),
            ),

            Spacer(1, 1.5 * mm),

            # TELEFONE
            Table(
                [[Paragraph("TEL:", estilo_campo)]],
                colWidths=[49 * mm],
                style=TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]),
            ),

            Spacer(1, 1.5 * mm),

            # ENDEREÇO
            Table(
                [[Paragraph("ENDEREÇO:", estilo_campo)]],
                colWidths=[49 * mm],
                style=TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]),
            ),

            # LINHA EXTRA DO ENDEREÇO
            Table(
                [[""]],
                colWidths=[49 * mm],
                rowHeights=[4.5 * mm],
                style=TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]),
            ),
        ]



        # =====================================================
        # CANHOTO
        # =====================================================

        canhoto = conteudo_canhoto

        # =====================================================
        # BILHETE PRINCIPAL
        # =====================================================

        header_esquerda = [

            Paragraph(
                "RIFA",
                estilo_rifa,
            ),

            Spacer(1, 1 * mm),

            Paragraph(
                str(nome_rifa),
                estilo_nome_rifa,
            ),
        ]

        # -----------------------------------------------------
        # VALOR
        # -----------------------------------------------------

        badge_valor = Table(
            [
                [
                    Paragraph(
                        f"R$ {valor_formatado}",
                        estilo_valor,
                    )
                ]
            ],
            colWidths=[
                24 * mm
            ],
        )

        badge_valor.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#1a252f"),
                    ),
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
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        1,
                    ),
                ]
            )
        )

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        header = Table(
            [
                [
                    header_esquerda,
                    badge_valor,
                ]
            ],
            colWidths=[
                105 * mm,
                26 * mm,
            ],
        )

        header.setStyle(
            TableStyle(
                [
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
                ]
            )
        )

        # =====================================================
        # PRÊMIO
        # =====================================================

        premio_box = Table(
            [
                [
                    [
                        Paragraph(
                            "🏆 PRÊMIO PRINCIPAL",
                            estilo_premio_label,
                        ),

                        Spacer(
                            1,
                            0.5 * mm,
                        ),

                        Paragraph(
                            str(premio),
                            estilo_premio,
                        ),
                    ]
                ]
            ],
            colWidths=[
                131 * mm
            ],
        )

        premio_box.setStyle(
            TableStyle(
                [
                    (
                        "LINEBEFORE",
                        (0, 0),
                        (0, 0),
                        2.5,
                        colors.HexColor("#e67e22"),
                    ),
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
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                ]
            )
        )

        # =====================================================
        # INFORMAÇÕES
        # =====================================================

        info = Table(
            [
                [
                    Paragraph(
                        f"<b>Data:</b> {data_sorteio}",
                        estilo_info,
                    ),

                    Paragraph(
                        f"<b>Valor:</b> R$ {valor_formatado}",
                        estilo_info,
                    ),
                ]
            ],
            colWidths=[
                42 * mm,
                55 * mm,
                34 * mm,
            ],
        )

        info.setStyle(
            TableStyle(
                [
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
                ]
            )
        )

        # =====================================================
        # RODAPÉ
        # =====================================================

        footer = Table(
            [
                [
                    Paragraph(
                        "Arrecadação destinada à aquisição dos calçados dos integrantes.",
                        estilo_footer,
                    ),
                    Paragraph(
                        f"Nº {numero_formatado}",
                        estilo_numero,
                    ),
                ],
                [
                    Paragraph(
                        "Guarde este bilhete para conferência. Boa sorte!",
                        estilo_footer,
                    ),
                    "",
                ],
            ],
            colWidths=[
                104 * mm,
                27 * mm,
            ],
        )

        footer.setStyle(
            TableStyle(
                [
                    (
                        "LINEABOVE",
                        (0, 0),
                        (-1, 0),
                        0.4,
                        colors.HexColor("#dee2e6"),
                    ),
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
                        1,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "SPAN",
                        (1, 0),
                        (1, 1),
                    ),
                ]
            )
        )

        # =====================================================
        # PRINCIPAL
        # =====================================================

        principal = [
            header,

            Spacer(
                1,
                2 * mm,
            ),

            premio_box,

            Spacer(
                1,
                2 * mm,
            ),

            info,

            Spacer(
                1,
                1 * mm,
            ),

            footer,
        ]

        # =====================================================
        # RIFA COMPLETA
        # =====================================================

        tabela = TabelaRifaComLogo(
            [
                [
                    canhoto,
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
        )

        tabela.caminho_logo = caminho_logo

        tabela.setStyle(
            TableStyle(
                [
                    # Fundo do canhoto
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
                        colors.HexColor("#f8f9fa"),
                    ),

                    # Borda externa
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        colors.HexColor("#1a252f"),
                    ),

                    # Linha de corte
                    (
                        "LINEAFTER",
                        (0, 0),
                        (0, 0),
                        1,
                        colors.HexColor("#8c98a4"),
                    ),

                    # Alinhamento
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),

                    # Padding canhoto
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (0, 0),
                        3,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (0, 0),
                        3,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (0, 0),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (0, 0),
                        2,
                    ),

                    # Padding principal
                    (
                        "LEFTPADDING",
                        (1, 0),
                        (1, 0),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (1, 0),
                        (1, 0),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (1, 0),
                        (1, 0),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (1, 0),
                        (1, 0),
                        2,
                    ),
                ]
            )
        )

        return tabela

    # =========================================================
    # AGRUPAR NÚMEROS POR VENDEDOR
    # =========================================================

    grupos_vendedores = OrderedDict()

    for numero in numeros_para_imprimir:

        vendedor_nome = (
            numero.get("vendedor_nome")
            or "SEM VENDEDOR"
        )

        if vendedor_nome not in grupos_vendedores:
            grupos_vendedores[vendedor_nome] = []

        grupos_vendedores[vendedor_nome].append(numero)


    # =========================================================
    # GERAR RIFAS SEPARADAS POR VENDEDOR
    # =========================================================

    primeiro_grupo = True

    for vendedor_nome, numeros_vendedor in grupos_vendedores.items():

        # -----------------------------------------------------
        # NOVA PÁGINA PARA CADA VENDEDOR
        # -----------------------------------------------------

        if not primeiro_grupo:

            elementos.append(
                PageBreak()
            )

        primeiro_grupo = False

        # -----------------------------------------------------
        # RIFAS DO VENDEDOR
        # -----------------------------------------------------

        for numero in numeros_vendedor:

            elementos.append(
                criar_bilhete(
                    numero,
                    mostrar_vendedor=True
                )
            )

            elementos.append(
                Spacer(
                    1,
                    1 * mm,
                )
            )

    # =========================================================
    # CASO NÃO TENHA NÚMEROS
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

