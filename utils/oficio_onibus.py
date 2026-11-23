
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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT


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
    horario_atividade,
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

    horario_atividade = formatar_horario(
        horario_atividade
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

        rightMargin=50,
        leftMargin=50,

        topMargin=25,
        bottomMargin=58
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


    estilo_topico = ParagraphStyle(
        "Topico",
        parent=estilo_base,
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        leftIndent=15,
        firstLineIndent=-12,
        spaceAfter=7,
        alignment=TA_LEFT
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
            "<b>ASSUNTO: Solicitação de transporte para "
            "deslocamento da Banda Brilho Negro</b>",
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
            "Prezados(as) Senhores(as),",
            estilo_oficio
        )
    )

    elementos.append(
        Spacer(1, 14)
    )


    # ========================================================
    # APRESENTAÇÃO E SOLICITAÇÃO
    # ========================================================

    texto_1 = (

        "A Associação Cultural de Percussão Rudimentar Brilho Negro, "
        "entidade cultural sediada no município de João Câmara/RN, "
        "vem, respeitosamente, por meio deste, solicitar a "
        "disponibilização de <b>01 (um) ônibus</b> para o transporte "
        "dos integrantes da Banda Brilho Negro, visando à "
        f"{finalidade}."
    )


    elementos.append(
        Paragraph(
            texto_1,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 14)
    )


    # ========================================================
    # DATA E LOCAL DA ATIVIDADE
    # ========================================================

    texto_2 = (

        f"A atividade será realizada no dia <b>{data_viagem}</b>, "
        f"no local <b>{destino}</b>, com previsão de início "
        f"às <b>{horario_atividade}</b>."
    )


    elementos.append(
        Paragraph(
            texto_2,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 14)
    )


    # ========================================================
    # INFORMAÇÕES DA VIAGEM
    # ========================================================

    elementos.append(
        Paragraph(
            "<b>Para fins de organização e planejamento do transporte, "
            "seguem as informações da viagem:</b>",
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 9)
    )


    topicos = [

        ("DESTINO", destino),

        ("DATA", data_viagem),

        ("HORÁRIO DA ATIVIDADE", horario_atividade),

        ("HORÁRIO DE SAÍDA", f"{horario_saida} – {origem}"),

        ("PREVISÃO DE RETORNO", horario_retorno),

        ("QUANTIDADE DE PESSOAS", f"{quantidade_pessoas} pessoas"),

        ("TRANSPORTE SOLICITADO", "01 (um) ônibus"),

        ("TRAJETO", f"{origem} → {destino} → {origem}")

    ]


    for titulo, informacao in topicos:

        elementos.append(
            Paragraph(
                f"<b>{titulo}:</b> {informacao}",
                estilo_topico,
                bulletText="•"
            )
        )


    elementos.append(
        Spacer(1, 10)
    )


    # ========================================================
    # JUSTIFICATIVA INSTITUCIONAL
    # ========================================================

    texto_3 = (

        "A participação da Banda Brilho Negro na referida atividade "
        "representa uma oportunidade de levar o nome e a cultura "
        "do município de João Câmara para outros territórios, "
        "fortalecendo a valorização da música, da cultura e da "
        "participação dos jovens em atividades culturais."
    )


    elementos.append(
        Paragraph(
            texto_3,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 14)
    )


    # ========================================================
    # SOLICITAÇÃO FINAL
    # ========================================================

    texto_4 = (

        "Dessa forma, solicitamos a atenção e o apoio da Prefeitura "
        "Municipal de João Câmara/RN para a disponibilização do "
        "transporte necessário, possibilitando o deslocamento "
        "seguro dos integrantes e representantes da associação."
    )


    elementos.append(
        Paragraph(
            texto_4,
            estilo_oficio
        )
    )


    elementos.append(
        Spacer(1, 14)
    )


    # ========================================================
    # ENCERRAMENTO
    # ========================================================

    elementos.append(

        Paragraph(
            "Certos de podermos contar com a colaboração do "
            "Poder Público Municipal, agradecemos antecipadamente.",
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
        destinatario = "Prefeitura Municipal de João Câmara/RN"


    cargo = input(
        "Cargo do destinatário [ex.: A/C: Administração Municipal]: "
    ).strip()


    data_viagem = input(
        "Data da viagem [ex.: 29/11/2026]: "
    ).strip()


    horario_saida = input(
        "Horário de saída [ex.: 08:30]: "
    ).strip()


    horario_retorno = input(
        "Horário previsto de retorno [ex.: 21:30]: "
    ).strip()


    horario_atividade = input(
        "Horário de início da atividade [ex.: 10:00]: "
    ).strip()


    origem = input(
        "Local de saída [ex.: João Câmara/RN]: "
    ).strip()

    if not origem:
        origem = "João Câmara/RN"


    destino = input(
        "Destino [ex.: Centro Esportivo João Gomes da Costa Neto, "
        "Bairro Liberdade, Parnamirim/RN]: "
    ).strip()


    quantidade = input(
        "Quantidade de pessoas [ex.: 46]: "
    ).strip()


    finalidade = input(
        "Finalidade da viagem: "
    ).strip()

    if not finalidade:
        finalidade = (
            "participação em competição de bandas e fanfarras"
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

        horario_atividade=horario_atividade,

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
