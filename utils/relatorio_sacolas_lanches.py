
from io import BytesIO
import os
import re
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

from sqlalchemy import text
from database import SessionLocal


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

PAGINA = landscape(A4)
LARGURA, ALTURA = PAGINA

PRETO = colors.HexColor("#151515")
DOURADO = colors.HexColor("#D4AF37")
CINZA = colors.HexColor("#666666")

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

# Logo exclusiva da marca-d'água
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
# MARCA-D'ÁGUA AMPLIADA
# ============================================================

def desenhar_marca_dagua(pdf, centro_x, centro_y):
    """
    Marca-d'água ampliada e centralizada em cada etiqueta.
    Mantém a proporção original da imagem.
    """

    if not os.path.isfile(MARCA_DAGUA_PATH):
        return

    pdf.saveState()

    try:
        # Transparência suave para manter a leitura dos dados.
        if hasattr(pdf, "setFillAlpha"):
            pdf.setFillAlpha(0.055)

        # Área maior que a utilizada anteriormente.
        # A imagem será ajustada sem distorcer sua proporção.
        largura_logo = 230 * mm
        altura_logo = 88 * mm

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
    margem = 12 * mm
    largura_util = LARGURA - 2 * margem

    centro_x = LARGURA / 2
    centro_y = y_base + altura / 2

    topo = y_base + altura - 10 * mm

    # ========================================================
    # 1. MARCA-D'ÁGUA
    # ========================================================

    desenhar_marca_dagua(
        pdf,
        centro_x,
        centro_y,
    )

    # ========================================================
    # 2. MOLDURA
    # ========================================================

    pdf.saveState()

    pdf.setStrokeColor(DOURADO)
    pdf.setLineWidth(1.4)

    pdf.roundRect(
        margem,
        y_base + 7 * mm,
        largura_util,
        altura - 14 * mm,
        3 * mm,
        stroke=1,
        fill=0,
    )

    pdf.restoreState()

    # ========================================================
    # 3. CABEÇALHO CENTRALIZADO
    # ========================================================
    #
    # Logo no topo, centralizada e maior.
    # Nome institucional abaixo, em tamanho equilibrado.
    # Nome BRILHO NEGRO destacado sem exagero.
    #
    # ========================================================

    largura_logo = 55 * mm
    altura_logo = 19 * mm

    x_logo = centro_x - largura_logo / 2
    y_logo = topo - 20 * mm

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

    # Nome completo da associação.
    estilo_associacao = ParagraphStyle(
        "NomeAssociacao",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9,
        alignment=1,
        textColor=PRETO,
    )

    texto_associacao = Paragraph(
        "ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR",
        estilo_associacao,
    )

    largura_associacao = largura_util - 20 * mm

    _, altura_associacao = texto_associacao.wrap(
        largura_associacao,
        10 * mm,
    )

    texto_associacao.drawOn(
        pdf,
        centro_x - largura_associacao / 2,
        topo - 22 * mm - altura_associacao,
    )

    # Nome da marca.
    pdf.setFillColor(DOURADO)
    pdf.setFont("Helvetica-Bold", 13)

    pdf.drawCentredString(
        centro_x,
        topo - 29 * mm,
        "BRILHO NEGRO",
    )

    # ========================================================
    # 4. NOME DO ENCONTRO
    # ========================================================

    nome_evento = formatar(
        encontro["nome"]
    )

    desenhar_texto_centralizado(
        pdf,
        nome_evento,
        margem + 8 * mm,
        topo - 31 * mm,
        largura_util - 16 * mm,
        tamanho=8,
        negrito=True,
        cor=CINZA,
    )

    # Linha divisória dourada.
    pdf.setStrokeColor(DOURADO)
    pdf.setLineWidth(1.0)

    pdf.line(
        margem + 6 * mm,
        topo - 36 * mm,
        LARGURA - margem - 6 * mm,
        topo - 36 * mm,
    )

    # ========================================================
    # 5. NOME DA CORPORAÇÃO
    # ========================================================

    nome_banda = formatar(
        banda["nome_corporacao"]
    )

    tamanho_nome = (
        24 if len(nome_banda) <= 30
        else 19
    )

    if len(nome_banda) > 55:
        tamanho_nome = 15

    nome_estilo = ParagraphStyle(
        "NomeBanda",
        fontName="Helvetica-Bold",
        fontSize=tamanho_nome,
        leading=tamanho_nome * 1.15,
        alignment=1,
        textColor=PRETO,
    )

    paragrafo_nome = Paragraph(
        escape(nome_banda.upper()),
        nome_estilo,
    )

    largura_nome = largura_util - 20 * mm

    _, altura_nome = paragrafo_nome.wrap(
        largura_nome,
        20 * mm,
    )

    paragrafo_nome.drawOn(
        pdf,
        centro_x - largura_nome / 2,
        topo - 39 * mm - altura_nome,
    )

    # ========================================================
    # 6. CIDADE E UF
    # ========================================================

    cidade = formatar(
        banda["cidade"]
    )

    uf = formatar(
        banda["uf"]
    )

    # Evita acrescentar novamente a UF.
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
        y_base + 42 * mm,
        largura_util - 10 * mm,
        tamanho=11,
        negrito=True,
    )

    # ========================================================
    # 7. QUANTIDADE DE COMPONENTES
    # ========================================================

    quantidade = int(
        banda["quantidade_componentes"] or 0
    )

    desenhar_texto_centralizado(
        pdf,
        f"QUANTIDADE DE COMPONENTES: {quantidade}",
        margem + 5 * mm,
        y_base + 33 * mm,
        largura_util - 10 * mm,
        tamanho=10,
        negrito=True,
    )

    # ========================================================
    # 8. REGENTE E RESPONSÁVEL
    # ========================================================

    estilo_dados = ParagraphStyle(
        "DadosBanda",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=PRETO,
    )

    dados = (
        f"<b>Regente:</b> "
        f"{escape(formatar(banda['nome_regente']))}"
        f" &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"<b>Responsável:</b> "
        f"{escape(formatar(banda['responsavel']))}"
    )

    paragrafo_dados = Paragraph(
        dados,
        estilo_dados,
    )

    largura_dados = largura_util - 16 * mm

    _, altura_dados = paragrafo_dados.wrap(
        largura_dados,
        15 * mm,
    )

    paragrafo_dados.drawOn(
        pdf,
        centro_x - largura_dados / 2,
        y_base + 22 * mm - altura_dados,
    )

    # ========================================================
    # 9. CAMPO PARA CONFERÊNCIA
    # ========================================================

    pdf.setStrokeColor(CINZA)
    pdf.setLineWidth(0.6)

    caixa_x = LARGURA - margem - 38 * mm
    caixa_y = y_base + 11 * mm

    pdf.rect(
        caixa_x,
        caixa_y,
        32 * mm,
        7 * mm,
        stroke=1,
        fill=0,
    )

    pdf.setFillColor(CINZA)
    pdf.setFont("Helvetica", 7)

    pdf.drawCentredString(
        caixa_x + 16 * mm,
        caixa_y + 2.3 * mm,
        "CONFERIDO",
    )


# ============================================================
# GERAR PDF DAS ETIQUETAS DE LANCHES
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
        # PREPARAR DOCUMENTO
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

        altura_etiqueta = ALTURA / 2

        # ====================================================
        # DUAS ETIQUETAS POR FOLHA
        # ====================================================

        for indice in range(0, len(bandas), 2):

            # Etiqueta superior.
            desenhar_etiqueta(
                pdf,
                bandas[indice],
                encontro,
                altura_etiqueta,
                altura_etiqueta,
            )

            # Etiqueta inferior, quando houver outra banda.
            if indice + 1 < len(bandas):
                desenhar_etiqueta(
                    pdf,
                    bandas[indice + 1],
                    encontro,
                    0,
                    altura_etiqueta,
                )

            # Linha pontilhada para corte.
            pdf.saveState()

            pdf.setStrokeColor(
                colors.HexColor("#888888")
            )
            pdf.setLineWidth(0.7)
            pdf.setDash(3, 3)

            pdf.line(
                5 * mm,
                altura_etiqueta,
                LARGURA - 5 * mm,
                altura_etiqueta,
            )

            pdf.restoreState()

            pdf.showPage()

        # ====================================================
        # FINALIZAR
        # ====================================================

        pdf.save()
        buffer.seek(0)

        return buffer

    finally:
        db.close()
