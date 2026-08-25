from io import BytesIO
from datetime import datetime
import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
    Table,
    TableStyle,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

from sqlalchemy import text

from database import SessionLocal


# =====================================
# RODAPÉ PADRÃO
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
            Spacer(1, 5)
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
            estilo
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            "<b>BRILHO NEGRO</b>",
            ParagraphStyle(
                "Nome",
                parent=estilo,
                fontSize=20
            )
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            estilo
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )

    elementos.append(
        Spacer(1, 25)
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
        Spacer(1, 20)
    )


# =====================================
# GERA PDF
# =====================================

def gerar_pdf_relatorio_viagens():

    db = SessionLocal()

    try:

        # =====================================
        # BUSCAR VIAGENS
        # =====================================

        viagens = db.execute(
            text("""
                SELECT
                    v.id,
                    v.evento,
                    v.destino,
                    v.data_saida,
                    v.data_retorno,
                    v.responsavel,

                    COUNT(
                        vi.integrante_id
                    ) AS total_participantes

                FROM viagens v

                LEFT JOIN viagem_integrantes vi
                    ON vi.viagem_id = v.id

                GROUP BY
                    v.id,
                    v.evento,
                    v.destino,
                    v.data_saida,
                    v.data_retorno,
                    v.responsavel

                ORDER BY
                    v.data_saida DESC,
                    v.id DESC
            """)
        ).mappings().all()


        # =====================================
        # RESUMOS
        # =====================================

        total_viagens = len(viagens)

        total_participacoes = sum(
            int(
                viagem["total_participantes"]
                or 0
            )
            for viagem in viagens
        )


        datas = [
            viagem["data_saida"]
            for viagem in viagens
            if viagem["data_saida"]
        ]


        if datas:

            menor_data = min(datas)
            maior_data = max(datas)

            periodo = (
                f"{menor_data.strftime('%d/%m/%Y')}"
                f" a "
                f"{maior_data.strftime('%d/%m/%Y')}"
            )

        else:

            periodo = "-"


        # =====================================
        # PDF
        # =====================================

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )


        estilos = getSampleStyleSheet()


        estilo = ParagraphStyle(
            "normal",
            parent=estilos["Normal"],
            fontSize=10,
            leading=16
        )


        estilo_tabela = ParagraphStyle(
            "Tabela",
            parent=estilos["Normal"],
            fontSize=8,
            leading=10
        )


        estilo_tabela_centro = ParagraphStyle(
            "TabelaCentro",
            parent=estilo_tabela,
            alignment=TA_CENTER
        )


        elementos = []


        # =====================================
        # CABEÇALHO
        # =====================================

        adicionar_cabecalho(
            elementos,
            estilos,
            "RELATÓRIO GERAL DE VIAGENS"
        )


        # =====================================
        # 1 - RESUMO GERAL
        # =====================================

        elementos.append(
            Paragraph(
                "<b>1 - RESUMO GERAL</b>",
                estilo
            )
        )

        elementos.append(
            Spacer(1, 10)
        )


        resumo = [

            ["Descrição", "Informação"],

            [
                "Total de Viagens",
                str(total_viagens)
            ],

            [
                "Total de Participações",
                str(total_participacoes)
            ],

            [
                "Período",
                periodo
            ]

        ]


        tabela_resumo = Table(
            resumo,
            colWidths=[
                250,
                150
            ]
        )


        tabela_resumo.setStyle(
            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONT",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )

            ])
        )


        elementos.append(
            tabela_resumo
        )


        elementos.append(
            Spacer(1, 25)
        )


        # =====================================
        # 2 - VIAGENS
        # =====================================

        elementos.append(
            Paragraph(
                "<b>2 - VIAGENS</b>",
                estilo
            )
        )


        elementos.append(
            Spacer(1, 10)
        )


        dados = [

            [

                Paragraph(
                    "<b>Data</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Evento</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Destino</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Retorno</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Responsável</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Part.</b>",
                    estilo_tabela_centro
                )

            ]

        ]


        # =====================================
        # DADOS DAS VIAGENS
        # =====================================

        for viagem in viagens:

            data_saida = (

                viagem["data_saida"].strftime(
                    "%d/%m/%Y"
                )

                if viagem["data_saida"]

                else "-"

            )


            data_retorno = (

                viagem["data_retorno"].strftime(
                    "%d/%m/%Y"
                )

                if viagem["data_retorno"]

                else "-"

            )


            dados.append(

                [

                    Paragraph(
                        data_saida,
                        estilo_tabela_centro
                    ),

                    Paragraph(
                        str(
                            viagem["evento"]
                            or "-"
                        ),
                        estilo_tabela
                    ),

                    Paragraph(
                        str(
                            viagem["destino"]
                            or "-"
                        ),
                        estilo_tabela
                    ),

                    Paragraph(
                        data_retorno,
                        estilo_tabela_centro
                    ),

                    Paragraph(
                        str(
                            viagem["responsavel"]
                            or "-"
                        ),
                        estilo_tabela
                    ),

                    Paragraph(
                        str(
                            viagem[
                                "total_participantes"
                            ]
                            or 0
                        ),
                        estilo_tabela_centro
                    )

                ]

            )


        # =====================================
        # NENHUMA VIAGEM
        # =====================================

        if not viagens:

            dados.append(

                [

                    Paragraph(
                        "Nenhuma viagem cadastrada.",
                        estilo_tabela
                    ),

                    "",
                    "",
                    "",
                    "",
                    ""

                ]

            )


        # =====================================
        # TABELA
        # =====================================

        tabela_viagens = Table(

            dados,

            repeatRows=1,

            colWidths=[

                55,     # Data
                105,    # Evento
                90,     # Destino
                55,     # Retorno
                85,     # Responsável
                30      # Participantes

            ]

        )


        tabela_viagens.setStyle(

            TableStyle([

                # Grade
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                # Cabeçalho
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONT",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                # Alinhamento vertical
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                # Data
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "CENTER"
                ),

                # Retorno
                (
                    "ALIGN",
                    (3, 1),
                    (3, -1),
                    "CENTER"
                ),

                # Participantes
                (
                    "ALIGN",
                    (5, 1),
                    (5, -1),
                    "CENTER"
                ),

                # Espaçamento
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )

            ])

        )


        elementos.append(
            tabela_viagens
        )


        # =====================================
        # OBSERVAÇÃO
        # =====================================

        elementos.append(
            Spacer(1, 20)
        )


        elementos.append(
            Paragraph(
                (
                    "Este relatório apresenta o histórico geral "
                    "das viagens cadastradas no Sistema de Gestão, "
                    "incluindo seus respectivos eventos, destinos, "
                    "datas, responsáveis e quantidade de participantes."
                ),
                estilo
            )
        )


        # =====================================
        # GERAR
        # =====================================

        doc.build(

            elementos,

            onFirstPage=adicionar_rodape,

            onLaterPages=adicionar_rodape

        )


        buffer.seek(0)

        return buffer


    finally:

        db.close()