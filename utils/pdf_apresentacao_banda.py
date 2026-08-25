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
            Spacer(1, 5)
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
    # NOME DA ASSOCIAÇÃO
    # =====================================

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

    # =====================================
    # BRILHO NEGRO
    # =====================================

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
        Spacer(1, 8)
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
        Spacer(1, 25)
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
                fontSize=16
            )
        )
    )

    elementos.append(
        Spacer(1, 20)
    )


# =====================================
# GERA PDF
# =====================================

def gerar_pdf_apresentacao_banda():

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=60

    )

    estilos = getSampleStyleSheet()

    # =====================================
    # ESTILO DO TEXTO
    # =====================================

    estilo = ParagraphStyle(
        "NormalDocumento",
        parent=estilos["Normal"],
        fontSize=11,
        leading=19,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    # =====================================
    # ESTILO DOS RESPONSÁVEIS
    # =====================================

    estilo_destaque = ParagraphStyle(
        "Destaque",
        parent=estilo,
        alignment=TA_CENTER,
        fontSize=11,
        leading=18
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
            um estilo único e marcante em suas apresentações.
            """,
            estilo
        )
    )

    elementos.append(
        Paragraph(
            """
            Suas peças musicais são <b>“Cold”</b> e
            <b>“Condor-Andino”</b>.
            """,
            estilo
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    # =====================================
    # RESPONSÁVEIS
    # =====================================

    elementos.append(
        Paragraph(
            "<b>CAPITÃ-MOR: Inajara Manuelly</b>",
            estilo_destaque
        )
    )

    elementos.append(
        Paragraph(
            "<b>COREÓGRAFO: Maciel Nascimento</b>",
            estilo_destaque
        )
    )

    elementos.append(
        Paragraph(
            "<b>REGENTE: Fábio Alves</b>",
            estilo_destaque
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    # =====================================
    # APRESENTAÇÃO FINAL
    # =====================================

    elementos.append(
        Paragraph(
            """
            Diretamente do <b>Colégio Fonte</b>, da cidade de
            <b>João Câmara</b>, com sua filial em <b>Poço Branco</b>,
            apresentamos a
            <b>Associação Cultural de Percussão Rudimentar Brilho Negro</b>.
            """,
            estilo
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

