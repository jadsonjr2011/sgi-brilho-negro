
from io import BytesIO
import os
import re
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

from sqlalchemy import text
from database import SessionLocal


# ============================================================
# CONFIGURAÇÕES GERAIS
# A4 RETRATO — LISTA DE DISTRIBUIÇÃO DE LANCHES
# ============================================================

PAGINA = A4
LARGURA, ALTURA = PAGINA

PRETO = colors.HexColor("#151515")
DOURADO = colors.HexColor("#D4AF37")
CINZA = colors.HexColor("#666666")
CINZA_CLARO = colors.HexColor("#E5E5E5")
CINZA_CABECALHO = colors.HexColor("#D6D6D6")
BRANCO = colors.white

MARGEM = 12 * mm

DIRETORIO_PROJETO = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

LOGO_PATH = os.path.join(
    DIRETORIO_PROJETO,
    "static",
    "img",
    "logo_relatorio.PNG",
)

MARCA_DAGUA_PATH = os.path.join(
    DIRETORIO_PROJETO,
    "static",
    "img",
    "logo_transparente.png",
)


# ============================================================
# FORMATAÇÃO
# ============================================================

def formatar(valor):
    if valor is None or not str(valor).strip():
        return "-"

    return re.sub(r"\s+", " ", str(valor)).strip()


# ============================================================
# MARCA-D'ÁGUA
# ============================================================

def desenhar_marca_dagua(pdf):
    if not os.path.isfile(MARCA_DAGUA_PATH):
        return

    pdf.saveState()

    try:
        if hasattr(pdf, "setFillAlpha"):
            pdf.setFillAlpha(0.055)

        largura_logo = 155 * mm
        altura_logo = 60 * mm

        pdf.drawImage(
            MARCA_DAGUA_PATH,
            (LARGURA - largura_logo) / 2,
            (ALTURA - altura_logo) / 2,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    finally:
        pdf.restoreState()


# ============================================================
# CABEÇALHO
# ============================================================

def desenhar_cabecalho(pdf, encontro, numero_pagina):
    centro_x = LARGURA / 2
    topo = ALTURA - 10 * mm

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    if os.path.isfile(LOGO_PATH):
        largura_logo = 43 * mm
        altura_logo = 15 * mm

        pdf.drawImage(
            LOGO_PATH,
            centro_x - largura_logo / 2,
            topo - altura_logo,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    # --------------------------------------------------------
    # NOME DA ASSOCIAÇÃO
    # --------------------------------------------------------

    pdf.setFillColor(PRETO)
    pdf.setFont("Helvetica-Bold", 7)

    pdf.drawCentredString(
        centro_x,
        topo - 18 * mm,
        "ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR",
    )

    # --------------------------------------------------------
    # MARCA
    # --------------------------------------------------------

    pdf.setFillColor(DOURADO)
    pdf.setFont("Helvetica-Bold", 13)

    pdf.drawCentredString(
        centro_x,
        topo - 24 * mm,
        "BRILHO NEGRO",
    )

    # --------------------------------------------------------
    # TÍTULO DO RELATÓRIO
    # --------------------------------------------------------

    pdf.setFillColor(PRETO)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawCentredString(
        centro_x,
        topo - 32 * mm,
        "CONTROLE DE DISTRIBUIÇÃO DE LANCHES",
    )

    # --------------------------------------------------------
    # NOME DO ENCONTRO
    # --------------------------------------------------------

    estilo_evento = ParagraphStyle(
        "Evento",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=CINZA,
    )

    paragrafo = Paragraph(
        escape(formatar(encontro["nome"])),
        estilo_evento,
    )

    largura_texto = LARGURA - 2 * MARGEM

    _, altura_texto = paragrafo.wrap(
        largura_texto,
        15 * mm,
    )

    paragrafo.drawOn(
        pdf,
        MARGEM,
        topo - 34 * mm - altura_texto,
    )

    # --------------------------------------------------------
    # LINHA DIVISÓRIA DOURADA
    # --------------------------------------------------------

    y_linha = topo - 37 * mm - altura_texto

    pdf.setStrokeColor(DOURADO)
    pdf.setLineWidth(1)

    pdf.line(
        MARGEM,
        y_linha,
        LARGURA - MARGEM,
        y_linha,
    )

    return y_linha - 7 * mm


# ============================================================
# CABEÇALHO DA TABELA
# FUNDO CINZA E GRADE PRETA
# ============================================================

def desenhar_cabecalho_tabela(pdf, y_topo):
    altura_cabecalho = 10 * mm

    largura_util = LARGURA - 2 * MARGEM

    # Nº | Corporação | Pães | Refrigerantes | Conferido
    larguras = [
        10 * mm,
        76 * mm,
        22 * mm,
        30 * mm,
        largura_util - 138 * mm,
    ]

    y_base = y_topo - altura_cabecalho

    # Fundo cinza e contorno preto
    pdf.setFillColor(CINZA_CABECALHO)
    pdf.setStrokeColor(PRETO)
    pdf.setLineWidth(0.8)

    pdf.rect(
        MARGEM,
        y_base,
        largura_util,
        altura_cabecalho,
        stroke=1,
        fill=1,
    )

    titulos = [
        "Nº",
        "CORPORAÇÃO",
        "PÃES",
        "REFRIGERANTES",
        "OK",
    ]

    # Divisões verticais do cabeçalho
    pdf.setStrokeColor(PRETO)
    pdf.setLineWidth(0.7)

    x = MARGEM

    for largura in larguras[:-1]:
        x += largura

        pdf.line(
            x,
            y_base,
            x,
            y_topo,
        )

    # Títulos em preto
    pdf.setFillColor(PRETO)
    pdf.setFont("Helvetica-Bold", 7)

    x = MARGEM

    for titulo, largura in zip(titulos, larguras):
        pdf.drawCentredString(
            x + largura / 2,
            y_base + 3.5 * mm,
            titulo,
        )

        x += largura

    return y_base, larguras


# ============================================================
# LINHA DE UMA BANDA
# GRADE PRETA — SEM QUADRADOS EM PÃES E REFRIGERANTES
# ============================================================

def desenhar_linha_banda(
    pdf,
    y_topo,
    numero,
    banda,
    larguras,
    altura_minima=12 * mm,
):
    largura_util = LARGURA - 2 * MARGEM

    estilo_nome = ParagraphStyle(
        "NomeCorporacao",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9.5,
        textColor=PRETO,
        alignment=0,
    )

    nome = escape(
        formatar(banda["nome_corporacao"]).upper()
    )

    paragrafo = Paragraph(
        nome,
        estilo_nome,
    )

    largura_nome = larguras[1] - 4 * mm

    _, altura_texto = paragrafo.wrap(
        largura_nome,
        30 * mm,
    )

    altura_linha = max(
        altura_minima,
        altura_texto + 4 * mm,
    )

    y_base = y_topo - altura_linha

    pdf.saveState()

    # --------------------------------------------------------
    # CONTORNO DA LINHA
    # --------------------------------------------------------

    pdf.setStrokeColor(PRETO)
    pdf.setLineWidth(0.7)
    pdf.setFillColor(BRANCO)

    pdf.rect(
        MARGEM,
        y_base,
        largura_util,
        altura_linha,
        stroke=1,
        fill=1,
    )

    # --------------------------------------------------------
    # DIVISÕES VERTICAIS
    # --------------------------------------------------------

    x = MARGEM

    for largura in larguras[:-1]:
        x += largura

        pdf.line(
            x,
            y_base,
            x,
            y_topo,
        )

    # --------------------------------------------------------
    # NÚMERO DA BANDA
    # --------------------------------------------------------

    pdf.setFillColor(PRETO)
    pdf.setFont("Helvetica", 8)

    pdf.drawCentredString(
        MARGEM + larguras[0] / 2,
        y_base + altura_linha / 2 - 2,
        str(numero),
    )

    # --------------------------------------------------------
    # NOME DA CORPORAÇÃO
    # --------------------------------------------------------

    paragrafo.drawOn(
        pdf,
        MARGEM + larguras[0] + 2 * mm,
        y_base + (altura_linha - altura_texto) / 2,
    )

    # --------------------------------------------------------
    # CAMPOS DE ANOTAÇÃO
    # PÃES E REFRIGERANTES FICAM SEM QUADRADOS
    # --------------------------------------------------------

    inicio_paes = MARGEM + larguras[0] + larguras[1]

    inicio_refrigerantes = (
        inicio_paes + larguras[2]
    )

    inicio_conferido = (
        inicio_refrigerantes + larguras[3]
    )

    # --------------------------------------------------------
    # QUADRADO DE CONFERÊNCIA — COLUNA OK
    # --------------------------------------------------------

    pdf.setStrokeColor(PRETO)
    pdf.setLineWidth(0.7)

    caixa = 5 * mm
    centro_y = y_base + altura_linha / 2
    largura_ok = larguras[4]

    pdf.rect(
        inicio_conferido + (largura_ok - caixa) / 2,
        centro_y - caixa / 2,
        caixa,
        caixa,
        stroke=1,
        fill=0,
    )

    pdf.restoreState()

    return y_base


# ============================================================
# RODAPÉ
# ============================================================

def desenhar_rodape(pdf, numero_pagina):
    pdf.saveState()

    pdf.setStrokeColor(DOURADO)
    pdf.setLineWidth(0.5)

    pdf.line(
        MARGEM,
        13 * mm,
        LARGURA - MARGEM,
        13 * mm,
    )

    pdf.setFillColor(CINZA)
    pdf.setFont("Helvetica", 6.5)

    pdf.drawCentredString(
        LARGURA / 2,
        9 * mm,
        "Associação Cultural de Percussão Rudimentar Brilho Negro",
    )

    pdf.drawRightString(
        LARGURA - MARGEM,
        9 * mm,
        f"Página {numero_pagina}",
    )

    pdf.restoreState()


# ============================================================
# GERAR PDF
# ============================================================

def gerar_pdf_relatorio_distribuicao_lanches(encontro_id):
    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # BUSCAR ENCONTRO
        # ----------------------------------------------------

        encontro = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    data,
                    local,
                    horario,
                    status
                FROM encontros_bandas
                WHERE id = :id
            """),
            {"id": encontro_id},
        ).mappings().first()

        if not encontro:
            raise ValueError(
                "Encontro de bandas não encontrado."
            )

        # ----------------------------------------------------
        # BUSCAR BANDAS APROVADAS
        # ----------------------------------------------------

        bandas = db.execute(
            text("""
                SELECT
                    eb.id,
                    b.nome AS nome_corporacao
                FROM encontro_bandas eb
                INNER JOIN bandas b
                    ON b.id = eb.banda_id
                WHERE eb.encontro_id = :id
                  AND eb.status = 'APROVADA'
                ORDER BY
                    LOWER(TRIM(b.nome)) ASC,
                    eb.id ASC
            """),
            {"id": encontro_id},
        ).mappings().all()

        if not bandas:
            raise ValueError(
                "Não existem bandas aprovadas para este encontro."
            )

        # ----------------------------------------------------
        # PREPARAR PDF
        # ----------------------------------------------------

        buffer = BytesIO()

        pdf = canvas.Canvas(
            buffer,
            pagesize=PAGINA,
            pageCompression=1,
        )

        pdf.setTitle(
            "Controle de Distribuição de Lanches - "
            + formatar(encontro["nome"])
        )

        pdf.setAuthor(
            "Associação Cultural de Percussão Rudimentar "
            "Brilho Negro"
        )

        numero_pagina = 1

        # Desenhar primeiro a marca-d'água para ficar atrás
        # dos textos, das linhas e dos campos da tabela.
        desenhar_marca_dagua(pdf)

        y_topo = desenhar_cabecalho(
            pdf,
            encontro,
            numero_pagina,
        )

        y_atual, larguras = desenhar_cabecalho_tabela(
            pdf,
            y_topo,
        )

        numero = 1
        limite_inferior = 19 * mm

        # ----------------------------------------------------
        # DESENHAR BANDAS
        # ----------------------------------------------------

        for banda in bandas:

            estilo_medicao = ParagraphStyle(
                "MedicaoNome",
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=9.5,
            )

            nome = Paragraph(
                escape(
                    formatar(
                        banda["nome_corporacao"]
                    ).upper()
                ),
                estilo_medicao,
            )

            _, altura_texto = nome.wrap(
                larguras[1] - 4 * mm,
                30 * mm,
            )

            altura_linha = max(
                12 * mm,
                altura_texto + 4 * mm,
            )

            # Se não houver espaço, iniciar nova página
            if y_atual - altura_linha < limite_inferior:

                desenhar_rodape(
                    pdf,
                    numero_pagina,
                )

                pdf.showPage()

                numero_pagina += 1

                # Nova página: marca-d'água primeiro
                desenhar_marca_dagua(pdf)

                y_topo = desenhar_cabecalho(
                    pdf,
                    encontro,
                    numero_pagina,
                )

                y_atual, larguras = (
                    desenhar_cabecalho_tabela(
                        pdf,
                        y_topo,
                    )
                )

            y_atual = desenhar_linha_banda(
                pdf=pdf,
                y_topo=y_atual,
                numero=numero,
                banda=banda,
                larguras=larguras,
            )

            numero += 1

        # ----------------------------------------------------
        # FINALIZAR DOCUMENTO
        # ----------------------------------------------------

        desenhar_rodape(
            pdf,
            numero_pagina,
        )

        pdf.save()
        buffer.seek(0)

        return buffer

    finally:
        db.close()
