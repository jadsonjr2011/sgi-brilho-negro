from io import BytesIO
from datetime import datetime
import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


# =====================================
# CAMINHO DA RAIZ DO PROJETO
# =====================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# =====================================
# RODAPÉ
# =====================================

def adicionar_rodape(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    # =====================================
    # LINHA DO RODAPÉ
    # =====================================

    canvas.setStrokeColor(colors.grey)

    canvas.line(
        85,
        48,
        largura - 57,
        48
    )

    # =====================================
    # TEXTO DO RODAPÉ
    # =====================================

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
# CABEÇALHO PADRÃO
# =====================================

def adicionar_cabecalho(elementos, estilos, titulo_documento):

    # =====================================
    # LOGO
    # =====================================

    logo_path = os.path.join(
        BASE_DIR,
        "static",
        "img",
        "logo_relatorio.PNG"
    )

    print()
    print("Procurando logo em:")
    print(logo_path)

    if os.path.exists(logo_path):

        print("Logo encontrada!")

        logo = Image(
            logo_path,
            width=320,
            height=79
        )

        logo.hAlign = "CENTER"

        elementos.append(
            logo
        )

        elementos.append(
            Spacer(1, 3)
        )

    else:

        print()
        print("ERRO: Logo não encontrada!")

        print(
            "Verifique se existe:"
        )

        print(
            os.path.join(
                BASE_DIR,
                "static",
                "img",
                "logo_relatorio.PNG"
            )
        )

    # =====================================
    # ESTILO DO CABEÇALHO
    # =====================================

    estilo_cabecalho = ParagraphStyle(
        "Cabecalho",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        leading=13,
        spaceAfter=0
    )

    # =====================================
    # NOME DA ASSOCIAÇÃO
    # =====================================

    elementos.append(
        Paragraph(
            "<b>ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR</b>",
            estilo_cabecalho
        )
    )

    elementos.append(
        Spacer(1, 3)
    )

    # =====================================
    # BRILHO NEGRO
    # =====================================

    elementos.append(
        Paragraph(
            "<b>BRILHO NEGRO</b>",
            ParagraphStyle(
                "Nome",
                parent=estilo_cabecalho,
                fontSize=18,
                leading=20
            )
        )
    )

    elementos.append(
        Spacer(1, 3)
    )

    # =====================================
    # SISTEMA
    # =====================================

    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            estilo_cabecalho
        )
    )

    elementos.append(
        Spacer(1, 7)
    )

    # =====================================
    # LINHA
    # =====================================

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.grey
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    # =====================================
    # TÍTULO DO DOCUMENTO
    # =====================================

    elementos.append(
        Paragraph(
            f"<b>{titulo_documento}</b>",
            ParagraphStyle(
                "Titulo",
                parent=estilo_cabecalho,
                fontSize=14,
                leading=17
            )
        )
    )

    # =====================================
    # ESPAÇO MAIOR ENTRE O TÍTULO
    # E O INÍCIO DO TEXTO
    # =====================================

    elementos.append(
        Spacer(1, 35)
    )


# =====================================
# GERA PDF
# =====================================

def gerar_pdf_apresentacao_banda():

    buffer = BytesIO()

    # =====================================
    # DOCUMENTO A4
    # =====================================

    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        # =====================================
        # MARGENS FORMAIS — ABNT
        # =====================================

        rightMargin=57,     # 2 cm
        leftMargin=85,      # 3 cm
        topMargin=85,       # 3 cm
        bottomMargin=57     # 2 cm

    )

    estilos = getSampleStyleSheet()

    # =====================================
    # TEXTO PRINCIPAL
    # =====================================

    estilo = ParagraphStyle(
        "NormalDocumento",

        parent=estilos["Normal"],

        fontName="Helvetica",

        fontSize=10.5,

        leading=15,

        alignment=TA_JUSTIFY,

        spaceAfter=5
    )

    # =====================================
    # CARGOS / RESPONSÁVEIS
    # =====================================

    estilo_destaque = ParagraphStyle(
        "Destaque",

        parent=estilo,

        fontName="Helvetica",

        alignment=TA_CENTER,

        fontSize=10.5,

        leading=14,

        spaceAfter=1
    )

    # =====================================
    # TÍTULOS DAS SEÇÕES
    # =====================================

    estilo_secao = ParagraphStyle(
        "Secao",

        parent=estilo,

        fontName="Helvetica",

        alignment=TA_CENTER,

        fontSize=11,

        leading=14,

        spaceBefore=3,

        spaceAfter=3
    )

    # =====================================
    # SAUDAÇÃO FINAL
    # =====================================

    estilo_final = ParagraphStyle(
        "Final",

        parent=estilo,

        fontName="Helvetica",

        alignment=TA_CENTER,

        fontSize=11.5,

        leading=14,

        spaceBefore=0,

        spaceAfter=0
    )

    elementos = []

    # =====================================
    # CABEÇALHO
    # =====================================

    adicionar_cabecalho(
        elementos,
        estilos,
        "APRESENTAÇÃO DA CORPORAÇÃO"
    )

    # =====================================
    # TEXTO INSTITUCIONAL
    # =====================================

    elementos.append(
        Paragraph(
            """
            Consolidada no ano de <b>2019</b>, a corporação que se apresenta é a
            <b>Associação Cultural de Percussão Rudimentar Brilho Negro</b>.
            """,
            estilo
        )
    )

    elementos.append(
        Paragraph(
            """
            Na categoria de <b>Percussão</b>, é uma banda genuinamente
            potiguar, contando atualmente com <b>48 componentes</b> e trazendo
            para suas apresentações um estilo único.
            """,
            estilo
        )
    )

    elementos.append(
        Paragraph(
            """
            Em seu repertório, apresenta as peças musicais
            <b>“Cold”</b> e <b>“Condor-Andino”</b>, representando,
            através da música e da expressão, os dois lados da vida:
            <b>o bem e o mal</b>.
            """,
            estilo
        )
    )

    elementos.append(
        Spacer(1, 3)
    )

    # =====================================
    # À FRENTE DA CORPORAÇÃO
    # =====================================

    elementos.append(
        Paragraph(
            "<b>À FRENTE DA CORPORAÇÃO</b>",
            estilo_secao
        )
    )

    elementos.append(
        Paragraph(
            "<b>Capitã-Mor:</b> Inajara Manuelly",
            estilo_destaque
        )
    )

    elementos.append(
        Paragraph(
            "<b>Coreógrafo:</b> Maciel Nascimento",
            estilo_destaque
        )
    )

    elementos.append(
        Paragraph(
            "<b>Regente:</b> Fábio Alves",
            estilo_destaque
        )
    )

    elementos.append(
        Spacer(1, 5)
    )

    # =====================================
    # SEDE E FILIAL
    # =====================================

    elementos.append(
        Paragraph(
            """
            A corporação tem sua sede no <b>Colégio Fonte</b>, na cidade de
            <b>João Câmara</b>, e conta também com uma filial no município de
            <b>Poço Branco</b>.
            """,
            estilo
        )
    )

    elementos.append(
        Spacer(1, 2)
    )

    # =====================================
    # NA GESTÃO
    # =====================================

    elementos.append(
        Paragraph(
            "<b>NA GESTÃO</b>",
            estilo_secao
        )
    )

    elementos.append(
        Paragraph(
            "<b>Mantenedora:</b> Carla Geane",
            estilo_destaque
        )
    )

    elementos.append(
        Paragraph(
            "<b>Direção:</b> Renata Carvalho",
            estilo_destaque
        )
    )

    # =====================================
    # ESPAÇO ANTES DA SAUDAÇÃO FINAL
    # =====================================

    elementos.append(
        Spacer(1, 25)
    )

    # =====================================
    # SAUDAÇÃO FINAL
    # =====================================

    elementos.append(
     Paragraph(
            """
            <b>Senhoras e senhores,</b> recebam com vocês a
            <b>Associação Cultural de Percussão Rudimentar Brilho Negro!</b>
            """,
            estilo_final
        )
    )

    # =====================================
    # GERA PDF
    # =====================================

    doc.build(

        elementos,

        onFirstPage=adicionar_rodape,

        onLaterPages=adicionar_rodape

    )

    buffer.seek(0)

    return buffer


# =====================================
# EXECUÇÃO DIRETA PELO CMD
# =====================================

if __name__ == "__main__":

    pdf = gerar_pdf_apresentacao_banda()

    # =====================================
    # ARQUIVO DE SAÍDA
    # =====================================

    nome_arquivo = "Apresentacao_Brilho_Negro_2019.pdf"

    caminho_saida = os.path.join(
        BASE_DIR,
        nome_arquivo
    )

    with open(
        caminho_saida,
        "wb"
    ) as arquivo:

        arquivo.write(
            pdf.getvalue()
        )

    print()
    print("=" * 60)
    print("PDF GERADO COM SUCESSO")
    print("=" * 60)
    print()
    print(f"Arquivo: {nome_arquivo}")
    print()
    print("Localização:")
    print(caminho_saida)
    print()

