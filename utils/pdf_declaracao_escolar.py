from io import BytesIO
from datetime import datetime
import os
import re

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


# ============================================================
# CORES — BRILHO NEGRO
# ============================================================

DOURADO = colors.HexColor("#D4AF37")
CINZA = colors.HexColor("#666666")
CINZA_CLARO = colors.HexColor("#E5E5E5")
PRETO = colors.HexColor("#222222")


# ============================================================
# RODAPÉ PADRÃO
# ============================================================

def adicionar_rodape(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    canvas.setStrokeColor(CINZA_CLARO)

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
        CINZA
    )

    canvas.drawCentredString(
        largura / 2,
        35,
        "Associação Cultural de Percussão Rudimentar Brilho Negro"
    )

    canvas.drawCentredString(
        largura / 2,
        23,
        "Documento gerado pelo Sistema de Gestão de Integrantes"
    )

    canvas.drawCentredString(
        largura / 2,
        11,
        f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    canvas.restoreState()


# ============================================================
# MARCA-D'ÁGUA
# ============================================================

def adicionar_marca_dagua(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    logo_path = os.path.join(
        "static",
        "img",
        "logo_transparente.png"
    )

    if os.path.exists(logo_path):

        try:
            canvas.setFillAlpha(0.06)
        except Exception:
            pass

        canvas.drawImage(
            logo_path,
            largura / 2 - 170,
            altura / 2 - 170,
            width=340,
            height=340,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.restoreState()


# ============================================================
# FUNÇÃO DE PÁGINA
# ============================================================

def desenhar_pagina(canvas, doc):

    adicionar_marca_dagua(
        canvas,
        doc
    )

    adicionar_rodape(
        canvas,
        doc
    )


# ============================================================
# FORMATAR DATA
# ============================================================

def formatar_data(data):

    if not data:
        return "-"

    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y")

    data = str(data).strip()

    formatos = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y",
    ]

    for formato in formatos:

        try:

            data_convertida = datetime.strptime(
                data,
                formato
            )

            return data_convertida.strftime(
                "%d/%m/%Y"
            )

        except ValueError:
            continue

    return data


# ============================================================
# FORMATAR HORÁRIO
# ============================================================

def formatar_horario(horario):

    if not horario:
        return "-"

    horario = str(horario).strip()

    horario = horario.replace(
        " ás ",
        " às "
    )

    horario = horario.replace(
        " as ",
        " às "
    )

    horario = re.sub(
        r"\b(\d{1,2}):(\d{2})\b",
        r"\1h\2",
        horario
    )

    return horario


# ============================================================
# FORMATAR CPF
# ============================================================

def formatar_cpf(cpf):

    if not cpf:
        return ""

    cpf = str(cpf).strip()

    numeros = re.sub(
        r"\D",
        "",
        cpf
    )

    if len(numeros) == 11:

        return (
            f"{numeros[:3]}."
            f"{numeros[3:6]}."
            f"{numeros[6:9]}-"
            f"{numeros[9:]}"
        )

    return cpf


# ============================================================
# GERA DECLARAÇÃO
# ============================================================

def gerar_pdf_declaracao_escolar(
    nome_integrante,
    cpf_integrante,
    escola,
    data_atividade,
    local_atividade,
    horario,
    observacao=""
):

    # ========================================================
    # FORMATAR DADOS
    # ========================================================

    data_formatada = formatar_data(
        data_atividade
    )

    horario_formatado = formatar_horario(
        horario
    )

    cpf_formatado = formatar_cpf(
        cpf_integrante
    )

    nome_integrante = str(
        nome_integrante or ""
    ).strip()

    escola = str(
        escola or ""
    ).strip()

    local_atividade = str(
        local_atividade or ""
    ).strip()

    observacao = str(
        observacao or ""
    ).strip()


    # ========================================================
    # PDF
    # ========================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=70,
        leftMargin=70,

        topMargin=55,
        bottomMargin=65
    )


    # ========================================================
    # ESTILOS
    # ========================================================

    estilos = getSampleStyleSheet()


    estilo_base = ParagraphStyle(
        "Base",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=19,
        textColor=PRETO
    )


    estilo_centro = ParagraphStyle(
        "Centro",
        parent=estilo_base,
        alignment=TA_CENTER
    )


    estilo_titulo = ParagraphStyle(
        "TituloDeclaracao",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        textColor=PRETO,
        spaceAfter=8
    )


    estilo_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=CINZA
    )


    estilo_corpo = ParagraphStyle(
        "Corpo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=22,
        alignment=TA_JUSTIFY,
        textColor=PRETO,
        firstLineIndent=35,
        spaceAfter=18
    )


    estilo_assinatura = ParagraphStyle(
        "Assinatura",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=CINZA
    )


    # ========================================================
    # ELEMENTOS
    # ========================================================

    elementos = []


    # ========================================================
    # CABEÇALHO
    # ========================================================

    logo_path = os.path.join(
        "static",
        "img",
        "logo_relatorio.PNG"
    )


    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=280,
            height=70
        )

        logo.hAlign = "CENTER"

        elementos.append(
            logo
        )

        elementos.append(
            Spacer(1, 6)
        )


    elementos.append(

        Paragraph(
            "ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR",
            ParagraphStyle(
                "Associacao",
                parent=estilo_subtitulo,
                fontName="Helvetica-Bold",
                fontSize=9
            )
        )

    )


    elementos.append(
        Spacer(1, 5)
    )


    elementos.append(

        HRFlowable(
            width="100%",
            thickness=1,
            color=DOURADO,
            spaceBefore=2,
            spaceAfter=25
        )

    )


    # ========================================================
    # TÍTULO
    # ========================================================

    elementos.append(

        Paragraph(
            "DECLARAÇÃO",
            estilo_titulo
        )

    )


    elementos.append(

        Paragraph(
            "DE PARTICIPAÇÃO EM ATIVIDADE DA BANDA",
            estilo_subtitulo
        )

    )


    elementos.append(
        Spacer(1, 38)
    )


    # ========================================================
    # PRIMEIRO PARÁGRAFO
    # ========================================================

    texto_principal = (

        "Declaramos, para os devidos fins, que <b>"
        f"{nome_integrante}"
        "</b>"

        + (
            f", CPF <b>{cpf_formatado}</b>"
            if cpf_formatado
            else ""
        )

        + ", integrante da "
        "<b>Associação Cultural de Percussão Rudimentar Brilho Negro</b>, "
        "participou de atividade oficial da Banda Brilho Negro, "
        "realizada no dia <b>"
        f"{data_formatada}"
        "</b>, no período de <b>"
        f"{horario_formatado}"
        "</b>, no município de <b>"
        f"{local_atividade}"
        "</b>."
    )


    elementos.append(

        Paragraph(
            texto_principal,
            estilo_corpo
        )

    )


    # ========================================================
    # SEGUNDO PARÁGRAFO
    # ========================================================

    if escola:

        texto_final = (

            "A presente declaração é emitida para fins de "
            "comprovação de participação em atividade oficial "
            "da Banda Brilho Negro, junto à instituição de ensino "
            f"<b>{escola}</b>, justificando sua ausência no período "
            "acima informado."
        )

    else:

        texto_final = (

            "A presente declaração é emitida para fins de "
            "comprovação de participação em atividade oficial "
            "da Banda Brilho Negro, justificando sua ausência "
            "no período acima informado."
        )


    elementos.append(

        Paragraph(
            texto_final,
            estilo_corpo
        )

    )


    # ========================================================
    # TERCEIRO PARÁGRAFO
    # ========================================================

    elementos.append(

        Paragraph(
            "Por ser expressão da verdade, firmamos a presente "
            "declaração para os fins que se fizerem necessários.",
            estilo_corpo
        )

    )


    # ========================================================
    # OBSERVAÇÃO
    # ========================================================

    if observacao:

        elementos.append(

            Paragraph(
                (
                    "<b>Observação:</b> "
                    f"{observacao}"
                ),
                ParagraphStyle(
                    "Observacao",
                    parent=estilo_base,
                    fontSize=10,
                    leading=16,
                    textColor=CINZA,
                    spaceBefore=5,
                    spaceAfter=20
                )
            )

        )


    # ========================================================
    # LOCAL E DATA
    # ========================================================

    elementos.append(
        Spacer(1, 12)
    )


    meses = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro"
    }


    hoje = datetime.now()


    data_emissao = (
        f"{hoje.day} de "
        f"{meses[hoje.month]} de "
        f"{hoje.year}"
    )


    elementos.append(

        Paragraph(
            (
                f"{local_atividade}, "
                f"{data_emissao}."
            ),
            estilo_centro
        )

    )


    elementos.append(
        Spacer(1, 55)
    )


    # ========================================================
    # ASSINATURA
    # ========================================================

    elementos.append(

        HRFlowable(
            width=220,
            thickness=0.8,
            color=CINZA
        )

    )


    elementos.append(
        Spacer(1, 7)
    )


    elementos.append(

        Paragraph(
            "<b>Direção do Colégio Fonte</b>",
            estilo_assinatura
        )

    )


    elementos.append(

        Paragraph(
            "Colégio Fonte",
            estilo_assinatura
        )

    )


    # ========================================================
    # GERAR PDF
    # ========================================================

    doc.build(

        elementos,

        onFirstPage=desenhar_pagina,

        onLaterPages=desenhar_pagina

    )


    buffer.seek(0)

    return buffer