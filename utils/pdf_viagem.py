from io import BytesIO
from datetime import datetime, date
import os
from reportlab.pdfgen import canvas

from flask import send_file
from sqlalchemy import text

from database import SessionLocal

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    HRFlowable
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER



def calcular_idade(data_nascimento):

    if isinstance(data_nascimento, str):

        data_nascimento = datetime.strptime(
            data_nascimento,
            "%Y-%m-%d"
        ).date()

    hoje = date.today()

    idade = hoje.year - data_nascimento.year

    if (
        hoje.month,
        hoje.day
    ) < (
        data_nascimento.month,
        data_nascimento.day
    ):

        idade -= 1

    return idade

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
        "Documento gerado pelo Sistema de Gestão de Integrantes"
    )

    canvas.drawCentredString(
        largura / 2,
        11,
        f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    canvas.restoreState()

def adicionar_cabecalho(elementos, estilos, titulo_documento):


    logo_path = os.path.join(
        "static",
        "img",
        "logo_relatorio.PNG"
    )


    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=320,
            height=79
        )

        logo.hAlign = "CENTER"

        elementos.append(logo)

        elementos.append(
            Spacer(1,5)
        )


    estilo = ParagraphStyle(
        "Cabecalho",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=12
    )


    elementos.append(
        Paragraph(
            "<b>ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR</b>",
            ParagraphStyle(
                "Associacao",
                parent=estilo,
                fontSize=12,
                leading=18
            )
        )
    )


    elementos.append(
        Spacer(1,8)
    )


    elementos.append(
        Paragraph(
            "<b>BRILHO NEGRO</b>",
            ParagraphStyle(
                "Nome",
                parent=estilo,
                fontSize=20,
                leading=24
            )
        )
    )


    elementos.append(
        Spacer(1,8)
    )


    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            ParagraphStyle(
                "Sistema",
                parent=estilo,
                fontSize=11,
                leading=18
            )
        )
    )


    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )


    elementos.append(
        Spacer(1,25)
    )


    elementos.append(
        Paragraph(
            f"<b>{titulo_documento}</b>",
            ParagraphStyle(
                "Titulo",
                parent=estilo,
                fontSize=16
            )
        )
    )


    elementos.append(
        Spacer(1,20)
    )

def gerar_documentos_viagem(id):

    db = SessionLocal()


    viagem = db.execute(
        text("""
            SELECT *
            FROM viagens
            WHERE id=:id
        """),
        {
            "id": id
        }
    ).mappings().first()


    participantes = db.execute(
        text("""
            SELECT i.*

            FROM viagem_integrantes vi

            INNER JOIN integrantes i
            ON i.id = vi.integrante_id

            WHERE vi.viagem_id=:id

            ORDER BY i.nome
        """),
        {
            "id": id
        }
    ).mappings().all()


    db.close()


    if not viagem:

        return "Viagem não encontrada"



    arquivo = BytesIO()



    pdf = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )



    elementos = []


    estilos = getSampleStyleSheet()



    estiloInfo = ParagraphStyle(
        "Info",
        parent=estilos["Normal"],
        fontSize=12,
        leading=22
    )



    # ==========================
    # CAPA
    # ==========================


    adicionar_cabecalho(
        elementos,
        estilos,
        "DOCUMENTAÇÃO DE VIAGEM"
    )


    elementos.append(
        Paragraph(
            f"<b>Evento:</b> {viagem['evento']}",
            estiloInfo
        )
    )


    elementos.append(
        Paragraph(
            f"<b>Destino:</b> {viagem['destino']}",
            estiloInfo
        )
    )


    elementos.append(
        Paragraph(
            f"<b>Saída:</b> {viagem['data_saida'].strftime('%d/%m/%Y')}",
            estiloInfo
        )
    )


    retorno = "-"

    if viagem["data_retorno"]:

        retorno = viagem["data_retorno"].strftime(
            "%d/%m/%Y"
        )


    elementos.append(
        Paragraph(
            f"<b>Retorno:</b> {retorno}",
            estiloInfo
        )
    )


    elementos.append(
        Paragraph(
            f"<b>Responsável:</b> {viagem['responsavel']}",
            estiloInfo
        )
    )


    elementos.append(
        Paragraph(
            f"<b>Participantes:</b> {len(participantes)}",
            estiloInfo
        )
    )


    elementos.append(
        Spacer(1,20)
    )


    elementos.append(
        Paragraph(
            f"Documento emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            estiloInfo
        )
    )



    # ==========================
    # DOCUMENTOS DOS PARTICIPANTES
    # ==========================


    for pessoa in participantes:


        elementos.append(
            PageBreak()
        )



        idade = calcular_idade(
            pessoa["data_nascimento"]
        )



        data_nascimento = pessoa["data_nascimento"]


        if isinstance(data_nascimento, str):

            data_nascimento = datetime.strptime(
                data_nascimento,
                "%Y-%m-%d"
            ).strftime("%d/%m/%Y")


        elif hasattr(data_nascimento, "strftime"):

            data_nascimento = data_nascimento.strftime(
                "%d/%m/%Y"
            )



        # ==========================
        # MENOR DE IDADE
        # ==========================


        if idade < 18:


            titulo_documento = (
                "TERMO DE AUTORIZAÇÃO DO RESPONSÁVEL"
            )


            texto = f"""

            Eu, _________________________________________________,
            responsável legal pelo(a) integrante <b>{pessoa['nome']}</b>,
            portador do CPF <b>{pessoa['cpf'] or '-'}</b>,
            nascido em <b>{data_nascimento}</b>,
            declaro para os devidos fins que AUTORIZO sua participação
            na viagem promovida pela Associação Cultural de Percussão
            Rudimentar Brilho Negro.

            <br/><br/>

            Declaro estar ciente das atividades programadas, dos horários,
            das orientações da diretoria e das responsabilidades envolvidas
            durante todo o período da viagem.

            <br/><br/>

            <b>Dados da viagem:</b><br/>

            Evento: <b>{viagem['evento']}</b>
            Destino: <b>{viagem['destino']}</b><br/>

            Período:
            <b>{viagem['data_saida'].strftime('%d/%m/%Y')}
            até {retorno}</b><br/>

            Por estar de acordo, firmo a presente autorização.

            """


            assinatura = (
                "Assinatura do Responsável"
            )



        # ==========================
        # MAIOR DE IDADE
        # ==========================


        else:


            titulo_documento = (
                "DECLARAÇÃO DE CIÊNCIA"
            )


            texto = f"""

            Eu, <b>{pessoa['nome']}</b>, portador do CPF
            <b>{pessoa['cpf'] or '-'}</b>,
            nascido em <b>{data_nascimento}</b>,
            declaro para os devidos fins que estou ciente da participação
            na viagem promovida pela Associação Cultural de Percussão
            Rudimentar Brilho Negro.

            <br/><br/>

            Declaro ter conhecimento da programação da viagem, das atividades
            previstas, dos horários estabelecidos e das orientações repassadas
            pela diretoria da associação, comprometendo-me a cumprir as normas
            de convivência, organização e segurança durante todo o período
            da viagem.

            <br/><br/>

            <b>Dados da viagem:</b><br/>

            Evento: <b>{viagem['evento']}</b><br/>
            Destino: <b>{viagem['destino']}</b><br/>
            Período:
            <b>{viagem['data_saida'].strftime('%d/%m/%Y')}
            até {retorno}</b><br/>

            Declaro estar ciente e de acordo com todas as informações
            apresentadas.

            """


            assinatura = (
                "Assinatura do Integrante"
            )



        # CABEÇALHO DO DOCUMENTO

        adicionar_cabecalho(
            elementos,
            estilos,
            titulo_documento
        )



        elementos.append(
            Paragraph(
                texto,
                estiloInfo
            )
        )

        if idade < 18:
            espaco_assinatura = 120
        else:
            espaco_assinatura = 90

        elementos.append(
            Spacer(1, espaco_assinatura)
        )

        elementos.append(
            Paragraph(
                "___________________________________",
                estiloInfo
            )
        )


        elementos.append(
            Paragraph(
                assinatura,
                estiloInfo
            )
        )


        elementos.append(
            Spacer(1,40)
        )



    pdf.build(
        elementos,
        onFirstPage=adicionar_rodape,
        onLaterPages=adicionar_rodape
    )



    arquivo.seek(0)



    return send_file(
        arquivo,
        as_attachment=True,
        download_name=f"Viagem_{viagem['evento']}.pdf",
        mimetype="application/pdf"
    )