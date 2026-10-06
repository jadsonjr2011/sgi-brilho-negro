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
# CAMINHOS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(
    BASE_DIR,
    "static",
    "img",
    "logo_relatorio.PNG"
)

LOGO_TRANSPARENTE = os.path.join(
    BASE_DIR,
    "static",
    "img",
    "logo_transparente.png"
)


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
        "Brilho Negro — Sistema de Gestão de Integrantes"
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

    if os.path.exists(LOGO_TRANSPARENTE):

        try:
            canvas.setFillAlpha(0.06)
        except Exception:
            pass

        canvas.drawImage(
            LOGO_TRANSPARENTE,
            largura / 2 - 170,
            altura / 2 - 170,
            width=340,
            height=340,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.restoreState()


# ============================================================
# PÁGINA
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
# GERAR OFÍCIO
# ============================================================

def gerar_oficio_onibus(
    numero_oficio,
    destinatario,
    cargo_destinatario,
    data_viagem,
    horario_saida,
    horario_retorno,
    origem,
    destino,
    quantidade_pessoas,
    finalidade,
    responsavel="Direção / Presidência da Brilho Negro",
    local_emissao="João Câmara/RN"
):

    # ========================================================
    # DADOS
    # ========================================================

    data_viagem = formatar_data(data_viagem)

    horario_saida = formatar_horario(
        horario_saida
    )

    horario_retorno = formatar_horario(
        horario_retorno
    )

    numero_oficio = str(
        numero_oficio or "___/2026"
    ).strip()

    destinatario = str(
        destinatario or "Prefeitura Municipal"
    ).strip()

    cargo_destinatario = str(
        cargo_destinatario or ""
    ).strip()

    origem = str(
        origem or "João Câmara/RN"
    ).strip()

    destino = str(
        destino or ""
    ).strip()

    finalidade = str(
        finalidade or "participação em atividade oficial da Banda Brilho Negro"
    ).strip()

    responsavel = str(
        responsavel or ""
    ).strip()

    local_emissao = str(
        local_emissao or "João Câmara/RN"
    ).strip()

    quantidade_pessoas = str(
        quantidade_pessoas or ""
    ).strip()


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

        rightMargin=65,
        leftMargin=65,

        topMargin=45,
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
        leading=18,
        textColor=PRETO
    )


    estilo_centro = ParagraphStyle(
        "Centro",
        parent=estilo_base,
        alignment=TA_CENTER
    )


    estilo_oficio = ParagraphStyle(
        "Oficio",
        parent=estilo_base,
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        alignment=TA_JUSTIFY
    )


    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        alignment=TA_CENTER,
        textColor=PRETO
    )


    estilo_assunto = ParagraphStyle(
        "Assunto",
        parent=estilo_base,
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=17
    )


    estilo_destinatario = ParagraphStyle(
        "Destinatario",
        parent=estilo_base,
        fontName="Helvetica",
        fontSize=11,
        leading=16
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

    if os.path.exists(LOGO_PATH):

        logo = Image(
            LOGO_PATH,
            width=280,
            height=70
        )

        logo.hAlign = "CENTER"

        elementos.append(
            logo
        )

        elementos.append(
            Spacer(1, 5)
        )


    elementos.append(

        Paragraph(
            "ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR",
            ParagraphStyle(
                "Associacao",
                parent=estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=CINZA
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
            spaceAfter=22
        )

    )


    # ========================================================
    # NÚMERO E DATA
    # ========================================================

    elementos.append(

        Paragraph(
            f"<b>OFÍCIO Nº {numero_oficio}</b>",
            estilo_base
        )

    )


    elementos.append(
        Spacer(1, 5)
    )


    hoje = datetime.now()

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


    data_emissao = (
        f"{hoje.day} de "
        f"{meses[hoje.month]} de "
        f"{hoje.year}"
    )


    elementos.append(

        Paragraph(
            f"{local_emissao}, {data_emissao}.",
            ParagraphStyle(
                "Data",
                parent=estilo_base,
                alignment=TA_CENTER,
                fontSize=10
            )
        )

    )


    elementos.append(
        Spacer(1, 24)
    )


    # ========================================================
    # DESTINATÁRIO
    # ========================================================

    elementos.append(

        Paragraph(
            f"<b>À {destinatario}</b>",
            estilo_destinatario
        )

    )


    if cargo_destinatario:

        elementos.append(

            Paragraph(
                cargo_destinatario,
                estilo_destinatario
            )

        )


    elementos.append(
        Spacer(1, 20)
    )


    # ========================================================
    # ASSUNTO
    # ========================================================

    elementos.append(

        Paragraph(
            "<b>Assunto: Solicitação de disponibilização de ônibus "
            "para transporte da Banda Brilho Negro</b>",
            estilo_assunto
        )

    )


    elementos.append(
        Spacer(1, 22)
    )


    # ========================================================
    # SAUDAÇÃO
    # ========================================================

    elementos.append(

        Paragraph(
            "Prezados(as),",
            estilo_oficio
        )

    )


    elementos.append(
        Spacer(1, 14)
    )


    # ========================================================
    # PRIMEIRO PARÁGRAFO
    # ========================================================

    texto_1 = (

        "A Associação Cultural de Percussão Rudimentar Brilho Negro, "
        "por meio deste, vem respeitosamente solicitar a disponibilização "
        "de <b>um ônibus</b> para o transporte dos integrantes e "
        "demais participantes da Banda Brilho Negro, em razão da "
        f"atividade oficial que será realizada no dia <b>{data_viagem}</b>, "
        f"com saída prevista para as <b>{horario_saida}</b>, "
        f"partindo de <b>{origem}</b>, com destino a "
        f"<b>{destino}</b>."
    )


    elementos.append(
        Paragraph(
            texto_1,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 15)
    )


    # ========================================================
    # SEGUNDO PARÁGRAFO
    # ========================================================

    texto_2 = (

        f"A referida viagem tem como finalidade {finalidade}. "
        f"Para o deslocamento, estima-se a participação de "
        f"<b>{quantidade_pessoas} pessoas</b>, entre integrantes, "
        "equipe de apoio e responsáveis pela atividade."
    )


    elementos.append(
        Paragraph(
            texto_2,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 15)
    )


    # ========================================================
    # TERCEIRO PARÁGRAFO
    # ========================================================

    texto_3 = (

        f"Solicitamos, ainda, que seja considerado o retorno do veículo "
        f"após a conclusão da atividade, com previsão para "
        f"<b>{horario_retorno}</b>, de acordo com a programação "
        "e as necessidades do grupo."
    )


    elementos.append(
        Paragraph(
            texto_3,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 15)
    )


    # ========================================================
    # QUARTO PARÁGRAFO
    # ========================================================

    texto_4 = (

        "Ressaltamos que o apoio solicitado é de grande importância "
        "para garantir o deslocamento seguro e adequado dos integrantes "
        "e participantes da Banda Brilho Negro, contribuindo para a "
        "realização da atividade previamente programada."
    )


    elementos.append(
        Paragraph(
            texto_4,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 15)
    )


    # ========================================================
    # ENCERRAMENTO
    # ========================================================

    elementos.append(

        Paragraph(
            "Certos de podermos contar com a atenção e colaboração "
            "dessa Administração Pública, agradecemos antecipadamente "
            "e colocamo-nos à disposição para quaisquer esclarecimentos.",
            estilo_oficio
        )

    )


    elementos.append(
        Spacer(1, 20)
    )


    elementos.append(

        Paragraph(
            "Atenciosamente,",
            estilo_oficio
        )

    )


    elementos.append(
        Spacer(1, 42)
    )


    # ========================================================
    # ASSINATURA
    # ========================================================

    elementos.append(

        HRFlowable(
            width=230,
            thickness=0.8,
            color=CINZA
        )

    )


    elementos.append(
        Spacer(1, 7)
    )


    elementos.append(

        Paragraph(
            f"<b>{responsavel}</b>",
            estilo_assinatura
        )

    )


    elementos.append(

        Paragraph(
            "Associação Cultural de Percussão Rudimentar Brilho Negro",
            estilo_assinatura
        )

    )


    # ========================================================
    # GERAR
    # ========================================================

    doc.build(

        elementos,

        onFirstPage=desenhar_pagina,

        onLaterPages=desenhar_pagina

    )


    buffer.seek(0)

    return buffer


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("       BRILHO NEGRO — OFÍCIO PARA SOLICITAÇÃO DE ÔNIBUS")
    print("=" * 65)
    print()

    numero = input(
        "Número do Ofício [ex.: 015/2026]: "
    ).strip()

    if not numero:
        numero = "___/2026"


    destinatario = input(
        "Destinatário [ex.: Prefeitura Municipal de João Câmara]: "
    ).strip()

    if not destinatario:
        destinatario = "Prefeitura Municipal de João Câmara"


    cargo = input(
        "Cargo do destinatário [ex.: Ao Excelentíssimo Senhor Prefeito Municipal]: "
    ).strip()


    data_viagem = input(
        "Data da viagem [ex.: 15/09/2026]: "
    ).strip()


    horario_saida = input(
        "Horário de saída [ex.: 07:00]: "
    ).strip()


    horario_retorno = input(
        "Horário previsto de retorno [ex.: 20:00]: "
    ).strip()


    origem = input(
        "Local de saída [ex.: João Câmara/RN]: "
    ).strip()

    if not origem:
        origem = "João Câmara/RN"


    destino = input(
        "Destino [ex.: Rio do Fogo/RN]: "
    ).strip()


    quantidade = input(
        "Quantidade de pessoas [ex.: 45]: "
    ).strip()


    finalidade = input(
        "Finalidade da viagem: "
    ).strip()

    if not finalidade:
        finalidade = (
            "participação em atividade oficial da Banda Brilho Negro"
        )


    responsavel = input(
        "Nome do responsável que assinará: "
    ).strip()

    if not responsavel:
        responsavel = "Direção / Presidência da Brilho Negro"


    print()
    print("Gerando ofício...")
    print()


    pdf = gerar_oficio_onibus(

        numero_oficio=numero,

        destinatario=destinatario,

        cargo_destinatario=cargo,

        data_viagem=data_viagem,

        horario_saida=horario_saida,

        horario_retorno=horario_retorno,

        origem=origem,

        destino=destino,

        quantidade_pessoas=quantidade,

        finalidade=finalidade,

        responsavel=responsavel,

        local_emissao="João Câmara/RN"
    )


    nome_arquivo = (
        f"Oficio_Solicitacao_Onibus_"
        f"{numero.replace('/', '_')}.pdf"
    )


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


    print("=" * 65)
    print("PDF GERADO COM SUCESSO!")
    print("=" * 65)
    print()
    print(f"Arquivo: {caminho_saida}")
    print()