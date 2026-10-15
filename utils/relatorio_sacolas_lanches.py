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
# A4 RETRATO — 3 ETIQUETAS POR FOLHA
# ============================================================

PAGINA = A4
LARGURA, ALTURA = PAGINA

PRETO = colors.HexColor("#151515")
DOURADO = colors.HexColor("#D4AF37")
CINZA = colors.HexColor("#666666")
CINZA_CORTE = colors.HexColor("#888888")

QUANTIDADE_ETIQUETAS_POR_FOLHA = 3

ALTURA_ETIQUETA = ALTURA / QUANTIDADE_ETIQUETAS_POR_FOLHA

DIRETORIO_PROJETO = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Logo utilizada no cabeçalho
LOGO_PATH = os.path.join(
    DIRETORIO_PROJETO,
    "static",
    "img",
    "logo_relatorio.PNG",
)

# Logo utilizada como marca-d'água
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
# TEXTO CENTRALIZADO
# ============================================================

def desenhar_texto_centralizado(
    pdf,
    texto,
    x,
    y,
    largura,
    tamanho=12,
    negrito=False,
    cor=PRETO,
):
    estilo = ParagraphStyle(
        "EtiquetaTexto",
        fontName=(
            "Helvetica-Bold"
            if negrito
            else "Helvetica"
        ),
        fontSize=tamanho,
        leading=tamanho * 1.2,
        alignment=1,
        textColor=cor,
    )

    paragrafo = Paragraph(
        escape(str(texto)),
        estilo,
    )

    _, altura_real = paragrafo.wrap(
        largura,
        60 * mm,
    )

    paragrafo.drawOn(
        pdf,
        x,
        y - altura_real,
    )

    return altura_real


# ============================================================
# MARCA-D'ÁGUA
# Ajustada ao formato A4 retrato e à etiqueta individual
# ============================================================

def desenhar_marca_dagua(pdf, centro_x, centro_y):
    if not os.path.isfile(MARCA_DAGUA_PATH):
        return

    pdf.saveState()

    try:
        if hasattr(pdf, "setFillAlpha"):
            pdf.setFillAlpha(0.055)

        # Tamanho adequado à largura da etiqueta em retrato.
        # Preserva a proporção original da imagem.
        largura_logo = 155 * mm
        altura_logo = 60 * mm

        pdf.drawImage(
            MARCA_DAGUA_PATH,
            centro_x - largura_logo / 2,
            centro_y - altura_logo / 2,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    finally:
        pdf.restoreState()


# ============================================================
# DESENHAR ETIQUETA
# ============================================================

def desenhar_etiqueta(
    pdf,
    banda,
    encontro,
    y_base,
    altura,
):
    margem = 10 * mm
    largura_util = LARGURA - 2 * margem

    centro_x = LARGURA / 2
    centro_y = y_base + altura / 2

    topo = y_base + altura - 8 * mm

    # ========================================================
    # 1. MARCA-D'ÁGUA
    # ========================================================

    desenhar_marca_dagua(
        pdf,
        centro_x,
        centro_y,
    )

    # ========================================================
    # 2. MOLDURA DOURADA
    # ========================================================

    pdf.saveState()

    pdf.setStrokeColor(DOURADO)
    pdf.setLineWidth(1.2)

    pdf.roundRect(
        margem,
        y_base + 5 * mm,
        largura_util,
        altura - 10 * mm,
        3 * mm,
        stroke=1,
        fill=0,
    )

    pdf.restoreState()

    # ========================================================
    # 3. LOGO DO CABEÇALHO
    # ========================================================

    largura_logo = 45 * mm
    altura_logo = 15 * mm

    x_logo = centro_x - largura_logo / 2
    y_logo = topo - 16 * mm

    if os.path.isfile(LOGO_PATH):
        pdf.drawImage(
            LOGO_PATH,
            x_logo,
            y_logo,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    # ========================================================
    # 4. NOME DA ASSOCIAÇÃO
    # ========================================================

    estilo_associacao = ParagraphStyle(
        "NomeAssociacao",
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        alignment=1,
        textColor=PRETO,
    )

    texto_associacao = Paragraph(
        "ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR",
        estilo_associacao,
    )

    largura_associacao = largura_util - 12 * mm

    _, altura_associacao = texto_associacao.wrap(
        largura_associacao,
        10 * mm,
    )

    texto_associacao.drawOn(
        pdf,
        centro_x - largura_associacao / 2,
        topo - 18 * mm - altura_associacao,
    )

    # ========================================================
    # 5. NOME DA MARCA
    # ========================================================

    pdf.setFillColor(DOURADO)
    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawCentredString(
        centro_x,
        topo - 25 * mm,
        "BRILHO NEGRO",
    )

    # ========================================================
    # 6. NOME DO ENCONTRO
    # ========================================================

    nome_evento = formatar(encontro["nome"])

    desenhar_texto_centralizado(
        pdf,
        nome_evento,
        margem + 5 * mm,
        topo - 27 * mm,
        largura_util - 10 * mm,
        tamanho=7,
        negrito=True,
        cor=CINZA,
    )

    # ========================================================
    # 7. LINHA DIVISÓRIA
    # ========================================================

    pdf.setStrokeColor(DOURADO)
    pdf.setLineWidth(0.8)

    pdf.line(
        margem + 5 * mm,
        topo - 33 * mm,
        LARGURA - margem - 5 * mm,
        topo - 33 * mm,
    )

    # ========================================================
    # 8. NOME DA CORPORAÇÃO
    # ========================================================

    nome_banda = formatar(
        banda["nome_corporacao"]
    )

    if len(nome_banda) <= 24:
        tamanho_nome = 19
    elif len(nome_banda) <= 38:
        tamanho_nome = 16
    elif len(nome_banda) <= 55:
        tamanho_nome = 13
    else:
        tamanho_nome = 10

    nome_estilo = ParagraphStyle(
        "NomeBanda",
        fontName="Helvetica-Bold",
        fontSize=tamanho_nome,
        leading=tamanho_nome * 1.12,
        alignment=1,
        textColor=PRETO,
    )

    paragrafo_nome = Paragraph(
        escape(nome_banda.upper()),
        nome_estilo,
    )

    largura_nome = largura_util - 12 * mm

    _, altura_nome = paragrafo_nome.wrap(
        largura_nome,
        25 * mm,
    )

    paragrafo_nome.drawOn(
        pdf,
        centro_x - largura_nome / 2,
        topo - 36 * mm - altura_nome,
    )

    # ========================================================
    # 9. CIDADE E UF
    # ========================================================

    cidade = formatar(banda["cidade"])
    uf = formatar(banda["uf"])

    # Evita repetir a UF caso ela já esteja na cidade.
    if uf != "-" and not re.search(
        r"(?:/|-|\s)\s*"
        + re.escape(uf)
        + r"\s*$",
        cidade,
        re.IGNORECASE,
    ):
        cidade = f"{cidade}/{uf}"

    desenhar_texto_centralizado(
        pdf,
        cidade.upper(),
        margem + 5 * mm,
        y_base + 39 * mm,
        largura_util - 10 * mm,
        tamanho=10,
        negrito=True,
    )

    # ========================================================
    # 10. QUANTIDADE DE COMPONENTES
    # ========================================================

    quantidade = int(
        banda["quantidade_componentes"] or 0
    )

    desenhar_texto_centralizado(
        pdf,
        f"QUANTIDADE DE COMPONENTES: {quantidade}",
        margem + 5 * mm,
        y_base + 31 * mm,
        largura_util - 10 * mm,
        tamanho=9,
        negrito=True,
    )

    # ========================================================
    # 11. REGENTE E RESPONSÁVEL
    # ========================================================

    estilo_dados = ParagraphStyle(
        "DadosBanda",
        fontName="Helvetica",
        fontSize=7,
        leading=8.5,
        alignment=1,
        textColor=PRETO,
    )

    dados = (
        f"<b>Regente:</b> "
        f"{escape(formatar(banda['nome_regente']))}"
        f"<br/>"
        f"<b>Responsável:</b> "
        f"{escape(formatar(banda['responsavel']))}"
    )

    paragrafo_dados = Paragraph(
        dados,
        estilo_dados,
    )

    largura_dados = largura_util - 14 * mm

    _, altura_dados = paragrafo_dados.wrap(
        largura_dados,
        15 * mm,
    )

    paragrafo_dados.drawOn(
        pdf,
        centro_x - largura_dados / 2,
        y_base + 20 * mm - altura_dados,
    )

    # ========================================================
    # 12. CAMPO PARA CONFERÊNCIA
    # ========================================================

    pdf.setStrokeColor(CINZA)
    pdf.setLineWidth(0.6)

    caixa_largura = 30 * mm
    caixa_altura = 6 * mm

    caixa_x = (
        LARGURA
        - margem
        - caixa_largura
        - 2 * mm
    )

    caixa_y = y_base + 8 * mm

    pdf.rect(
        caixa_x,
        caixa_y,
        caixa_largura,
        caixa_altura,
        stroke=1,
        fill=0,
    )

    pdf.setFillColor(CINZA)
    pdf.setFont("Helvetica", 6.5)

    pdf.drawCentredString(
        caixa_x + caixa_largura / 2,
        caixa_y + 2 * mm,
        "CONFERIDO",
    )


# ============================================================
# LINHAS PONTILHADAS PARA CORTE
# ============================================================

def desenhar_linhas_corte(pdf):
    pdf.saveState()

    pdf.setStrokeColor(CINZA_CORTE)
    pdf.setLineWidth(0.6)
    pdf.setDash(3, 3)

    # Duas linhas horizontais dividem o A4 em três partes.
    for divisao in (1, 2):
        y = ALTURA_ETIQUETA * divisao

        pdf.line(
            3 * mm,
            y,
            LARGURA - 3 * mm,
            y,
        )

    pdf.restoreState()


# ============================================================
# GERAR PDF DAS ETIQUETAS DE LANCHES
# A4 RETRATO — 3 ETIQUETAS POR FOLHA
# ============================================================

def gerar_pdf_etiquetas_lanches_bandas(encontro_id):
    db = SessionLocal()

    try:
        # ====================================================
        # BUSCAR ENCONTRO
        # ====================================================

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

        # ====================================================
        # BUSCAR BANDAS APROVADAS
        # ====================================================

        bandas = db.execute(
            text("""
                SELECT
                    eb.id,
                    b.nome AS nome_corporacao,
                    b.cidade,
                    b.uf,
                    eb.maestro_nome AS nome_regente,
                    eb.responsavel_nome AS responsavel,
                    eb.quantidade_componentes

                FROM encontro_bandas eb

                INNER JOIN bandas b
                    ON b.id = eb.banda_id

                WHERE eb.encontro_id = :id
                  AND eb.status = 'APROVADA'

                ORDER BY b.nome ASC, eb.id ASC
            """),
            {"id": encontro_id},
        ).mappings().all()

        if not bandas:
            raise ValueError(
                "Não existem bandas aprovadas para este encontro."
            )

        # ====================================================
        # PREPARAR DOCUMENTO PDF
        # ====================================================

        buffer = BytesIO()

        pdf = canvas.Canvas(
            buffer,
            pagesize=PAGINA,
            pageCompression=1,
        )

        pdf.setTitle(
            "Etiquetas de Lanches - "
            + formatar(encontro["nome"])
        )

        pdf.setAuthor(
            "Associação Cultural de Percussão Rudimentar "
            "Brilho Negro"
        )

        # ====================================================
        # GERAR AS FOLHAS COM 3 ETIQUETAS CADA
        # ====================================================

        for indice in range(
            0,
            len(bandas),
            QUANTIDADE_ETIQUETAS_POR_FOLHA,
        ):

            # Posições de baixo para cima:
            # etiqueta 1: parte inferior
            # etiqueta 2: parte central
            # etiqueta 3: parte superior

            for posicao in range(
                QUANTIDADE_ETIQUETAS_POR_FOLHA
            ):
                indice_banda = indice + posicao

                # Não desenha etiquetas vazias.
                if indice_banda >= len(bandas):
                    continue

                y_base = ALTURA_ETIQUETA * (
                    QUANTIDADE_ETIQUETAS_POR_FOLHA
                    - 1
                    - posicao
                )

                desenhar_etiqueta(
                    pdf=pdf,
                    banda=bandas[indice_banda],
                    encontro=encontro,
                    y_base=y_base,
                    altura=ALTURA_ETIQUETA,
                )

            # Linhas de corte entre as três etiquetas.
            desenhar_linhas_corte(pdf)

            pdf.showPage()

        # ====================================================
        # FINALIZAR PDF
        # ====================================================

        pdf.save()
        buffer.seek(0)

        return buffer

    finally:
        db.close()
