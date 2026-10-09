
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from xml.sax.saxutils import escape

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
    KeepInFrame,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from sqlalchemy import text

from database import SessionLocal


# ============================================================
# CONFIGURAÇÕES
# ============================================================

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

MESES = [
    "janeiro", "fevereiro", "março", "abril",
    "maio", "junho", "julho", "agosto",
    "setembro", "outubro", "novembro", "dezembro",
]

DIRETORIO_PROJETO = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# ============================================================
# RODAPÉ + MARCA-D'ÁGUA
# ============================================================

def adicionar_rodape(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    # ==========================================
    # MARCA-D'ÁGUA BRILHO NEGRO
    # ==========================================

    logo_path = os.path.join(
        DIRETORIO_PROJETO,
        "static",
        "img",
        "logo_transparente.png",
    )

    if os.path.exists(logo_path):

        largura_logo = 350
        altura_logo = 350

        x = (largura - largura_logo) / 2
        y = (altura - altura_logo) / 2

        canvas.saveState()

        try:
            canvas.setFillAlpha(0.10)
        except Exception:
            pass

        canvas.drawImage(
            logo_path,
            x,
            y,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            mask="auto",
            anchor="c",
        )

        canvas.restoreState()

    # ==========================================
    # RODAPÉ INSTITUCIONAL
    # ==========================================

    canvas.setStrokeColor(colors.grey)
    canvas.setLineWidth(0.5)

    canvas.line(
        40,
        48,
        largura - 40,
        48,
    )

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)

    canvas.drawCentredString(
        largura / 2,
        34,
        "Associação Cultural de Percussão Rudimentar Brilho Negro",
    )

    canvas.drawCentredString(
        largura / 2,
        23,
        "Documento gerado pelo Sistema de Gestão de Integrantes",
    )

    canvas.drawCentredString(
        largura / 2,
        12,
        f"Emitido em {datetime.now(FUSO_HORARIO).strftime('%d/%m/%Y %H:%M')}",
    )

    canvas.restoreState()


# ============================================================
# CABEÇALHO INSTITUCIONAL
# ============================================================

def adicionar_cabecalho(elementos, estilos, titulo_documento):

    logo_path = os.path.join(
        DIRETORIO_PROJETO,
        "static",
        "img",
        "logo_relatorio.PNG",
    )

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=250,
            height=62,
        )

        logo.hAlign = "CENTER"

        elementos.append(logo)
        elementos.append(Spacer(1, 3))

    estilo_cabecalho = ParagraphStyle(
        "CabecalhoOficio",
        parent=estilos["Normal"],
        fontName="Helvetica",
        alignment=TA_CENTER,
        fontSize=9,
        leading=11,
        spaceAfter=2,
    )

    elementos.append(
        Paragraph(
            "<b>ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR</b>",
            estilo_cabecalho,
        )
    )

    elementos.append(
        Paragraph(
            "<b>BRILHO NEGRO</b>",
            ParagraphStyle(
                "NomeOficio",
                parent=estilo_cabecalho,
                fontSize=16,
                leading=18,
            ),
        )
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            estilo_cabecalho,
        )
    )

    elementos.append(Spacer(1, 5))

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.grey,
        )
    )

    elementos.append(Spacer(1, 7))

    elementos.append(
        Paragraph(
            f"<b>{escape(titulo_documento)}</b>",
            ParagraphStyle(
                "TituloOficio",
                parent=estilos["Normal"],
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
                fontSize=15,
                leading=18,
                spaceBefore=3,
                spaceAfter=5,
            ),
        )
    )

    elementos.append(Spacer(1, 7))


# ============================================================
# FORMATAÇÃO DE DATA E HORÁRIO
# ============================================================

def formatar_data(data):

    if not data:
        return "-"

    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y")

    return str(data)


def formatar_horario(horario):

    if not horario:
        return "-"

    if hasattr(horario, "strftime"):
        return horario.strftime("%H:%M")

    return str(horario)


def data_por_extenso(data_hora):

    dia = data_hora.day
    mes = MESES[data_hora.month - 1]
    ano = data_hora.year

    return f"João Câmara/RN, {dia} de {mes} de {ano}."


# ============================================================
# NUMERAÇÃO AUTOMÁTICA DO OFÍCIO
# ============================================================

def obter_numero_oficio(db, encontro_id, ano):

    # Bloqueia a geração simultânea de números no mesmo ano.
    db.execute(
        text("""
            SELECT pg_advisory_xact_lock(
                hashtext(
                    'brilho_negro_oficios_' || CAST(:ano AS TEXT)
                )
            )
        """),
        {"ano": ano},
    )

    # Reutiliza o número caso o ofício já tenha sido emitido.
    registro = db.execute(
        text("""
            SELECT numero
            FROM oficios_encontro_bandas
            WHERE encontro_id = :encontro_id
              AND ano = :ano
              AND tipo = 'SOLICITACAO_APOIO'
        """),
        {
            "encontro_id": encontro_id,
            "ano": ano,
        },
    ).mappings().first()

    if registro:
        return registro["numero"]

    proximo_numero = db.execute(
        text("""
            SELECT COALESCE(MAX(numero), 0) + 1
            FROM oficios_encontro_bandas
            WHERE ano = :ano
        """),
        {"ano": ano},
    ).scalar_one()

    db.execute(
        text("""
            INSERT INTO oficios_encontro_bandas (
                encontro_id,
                ano,
                numero,
                tipo
            )
            VALUES (
                :encontro_id,
                :ano,
                :numero,
                'SOLICITACAO_APOIO'
            )
        """),
        {
            "encontro_id": encontro_id,
            "ano": ano,
            "numero": proximo_numero,
        },
    )

    db.commit()

    return proximo_numero


# ============================================================
# GERAR PDF DO OFÍCIO DE SOLICITAÇÃO DE APOIO
# ============================================================

def gerar_pdf_oficio_solicitacao_apoio(encontro_id):

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR ENCONTRO
        # ==========================================

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
                WHERE id = :encontro_id
            """),
            {"encontro_id": encontro_id},
        ).mappings().first()

        if not encontro:
            raise ValueError("Encontro de bandas não encontrado.")

        # ==========================================
        # DATA E NÚMERO DO OFÍCIO
        # ==========================================

        agora = datetime.now(FUSO_HORARIO)
        ano_emissao = agora.year

        numero_oficio = obter_numero_oficio(
            db,
            encontro_id,
            ano_emissao,
        )

        data_emissao = data_por_extenso(agora)

        # ==========================================
        # DADOS DO EVENTO
        # ==========================================

        nome_evento = escape(
            str(
                encontro["nome"]
                or "VI Encontro de Bandas e Fanfarras — Brilho Negro 2026"
            )
        )

        data_evento = escape(
            formatar_data(encontro["data"])
        )

        horario_evento = escape(
            formatar_horario(encontro["horario"])
        )

        local_evento = escape(
            str(encontro["local"] or "João Câmara/RN")
        )

        # ==========================================
        # CONFIGURAÇÃO DO PDF
        # ==========================================

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.8 * cm,
            leftMargin=1.8 * cm,
            topMargin=0.6 * cm,
            bottomMargin=1.8 * cm,
            title="Ofício de Solicitação de Apoio Institucional",
            author=(
                "Associação Cultural de Percussão Rudimentar "
                "Brilho Negro"
            ),
        )

        estilos = getSampleStyleSheet()

        estilo_corpo = ParagraphStyle(
            "CorpoOficio",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )

        estilo_esquerda = ParagraphStyle(
            "EsquerdaOficio",
            parent=estilo_corpo,
            alignment=TA_LEFT,
            spaceAfter=3,
        )

        estilo_item = ParagraphStyle(
            "ItemOficio",
            parent=estilo_corpo,
            fontSize=9.3,
            leading=11.5,
            leftIndent=15,
            firstLineIndent=-15,
            spaceAfter=4,
        )

        estilo_assinatura = ParagraphStyle(
            "AssinaturaOficio",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=3,
        )

        elementos = []

        # ==========================================
        # CABEÇALHO
        # ==========================================

        adicionar_cabecalho(
            elementos,
            estilos,
            "OFÍCIO DE SOLICITAÇÃO DE APOIO INSTITUCIONAL",
        )

        # ==========================================
        # NÚMERO E DATA AUTOMÁTICOS
        # ==========================================

        elementos.append(
            Paragraph(
                f"<b>OFÍCIO Nº {numero_oficio:03d}/{ano_emissao}</b>",
                estilo_esquerda,
            )
        )

        elementos.append(
            Paragraph(
                escape(data_emissao),
                estilo_esquerda,
            )
        )

        elementos.append(Spacer(1, 6))

        # ==========================================
        # DESTINATÁRIO NEUTRO
        # ==========================================

        elementos.append(
            Paragraph(
                "<b>À Secretaria Municipal de Cultura e Turismo</b><br/>"
                "Prefeitura Municipal de João Câmara/RN",
                estilo_esquerda,
            )
        )

        elementos.append(Spacer(1, 5))

        # ==========================================
        # ASSUNTO
        # ==========================================

        elementos.append(
            Paragraph(
                "<b>Assunto:</b> Solicitação de apoio e infraestrutura "
                f"para o {nome_evento}.",
                estilo_corpo,
            )
        )

        elementos.append(
            Paragraph(
                "À equipe da Secretaria Municipal de Cultura e Turismo,",
                estilo_esquerda,
            )
        )

        elementos.append(Spacer(1, 3))

        # ==========================================
        # APRESENTAÇÃO
        # ==========================================

        elementos.append(
            Paragraph(
                "A Associação Cultural de Percussão Rudimentar "
                "Brilho Negro vem, respeitosamente, solicitar o apoio "
                "da Secretaria Municipal de Cultura e Turismo para "
                f"a realização do <b>{nome_evento}</b>, a ser realizado "
                f"no dia <b>{data_evento}</b>, a partir das "
                f"<b>{horario_evento}</b>, no município de "
                f"<b>{local_evento}</b>.",
                estilo_corpo,
            )
        )

        elementos.append(
            Paragraph(
                "O evento tem como objetivo promover a cultura musical, "
                "valorizar as bandas e fanfarras, incentivar a participação "
                "da juventude e fortalecer as manifestações culturais do "
                "nosso município, proporcionando um momento de integração, "
                "intercâmbio cultural e valorização da música.",
                estilo_corpo,
            )
        )

        elementos.append(
            Paragraph(
                "Para viabilizar a realização do encontro, solicitamos "
                "o apoio dessa Secretaria na disponibilização e articulação "
                "dos seguintes recursos e serviços:",
                estilo_corpo,
            )
        )

        # ==========================================
        # SOLICITAÇÕES
        # ==========================================

        solicitacoes = [
            (
                "<b>1. Grades de contenção:</b> destinadas ao "
                "isolamento e fechamento das vias necessárias "
                "à realização do evento."
            ),
            (
                "<b>2. Sistema de sonorização:</b> adequado às "
                "apresentações musicais das bandas e fanfarras "
                "participantes."
            ),
            (
                "<b>3. 01 (uma) tenda:</b> para apoio à organização "
                "e às atividades do evento."
            ),
            (
                "<b>4. Apoio da Guarda Municipal e do DEMUTRAN:</b> "
                "para auxiliar na segurança, organização do trânsito "
                "e interdição das vias, conforme as necessidades do "
                "evento e as atribuições de cada órgão."
            ),
            (
                "<b>5. Disponibilização da Escola Municipal "
                "Professora Cícero Varela:</b> para apoio logístico "
                "às bandas participantes, conforme autorização da "
                "Secretaria Municipal de Educação e da direção "
                "da unidade escolar."
            ),
        ]

        for solicitacao in solicitacoes:
            elementos.append(
                Paragraph(
                    solicitacao,
                    estilo_item,
                )
            )

        # ==========================================
        # JUSTIFICATIVA
        # ==========================================

        elementos.append(
            Paragraph(
                "Ressaltamos que o apoio do Poder Público Municipal "
                "é de grande importância para a realização deste evento, "
                "que contribui para o fortalecimento da cultura local, "
                "a integração entre os municípios participantes e a "
                "valorização dos jovens músicos e demais integrantes "
                "das bandas e fanfarras.",
                estilo_corpo,
            )
        )

        # ==========================================
        # ENCERRAMENTO
        # ==========================================

        elementos.append(
            Paragraph(
                "Diante do exposto, contamos com a atenção e a "
                "colaboração dessa Secretaria, colocando-nos à "
                "disposição para prestar informações complementares "
                "e alinhar os detalhes necessários à execução "
                "das solicitações.",
                estilo_corpo,
            )
        )

        elementos.append(
            Paragraph(
                "Sem mais para o momento, renovamos nossos votos "
                "de estima e consideração.",
                estilo_corpo,
            )
        )

        elementos.append(Spacer(1, 2))

        elementos.append(
            Paragraph(
                "Atenciosamente,",
                estilo_esquerda,
            )
        )

        # ==========================================
        # ASSINATURA DO REPRESENTANTE
        # ==========================================

        elementos.append(Spacer(1, 35))

        elementos.append(
            Paragraph(
                "____________________________________________",
                estilo_assinatura,
            )
        )

        elementos.append(
            Paragraph(
                "<b>Representante da Associação</b>",
                estilo_assinatura,
            )
        )

        elementos.append(
            Paragraph(
                "Associação Cultural de Percussão Rudimentar Brilho Negro",
                estilo_assinatura,
            )
        )

        # ==========================================
        # AJUSTAR PARA UMA PÁGINA A4
        # ==========================================

        pagina_unica = KeepInFrame(
            doc.width,
            doc.height,
            elementos,
            mode="shrink",
            hAlign="CENTER",
            vAlign="TOP",
        )

        doc.build(
            [pagina_unica],
            onFirstPage=adicionar_rodape,
        )

        buffer.seek(0)

        return buffer

    finally:
        db.close()