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

def adicionar_cabecalho(
    elementos,
    estilos,
    titulo_documento
):

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

        elementos.append(
            logo
        )

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
# FORMATAÇÃO DE DATA
# =====================================

def formatar_data(data):

    if not data:
        return "-"

    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y")

    return str(data)


# =====================================
# GERA PDF
# =====================================

def gerar_pdf_relatorio_bandas_participantes(
    encontro_id
):

    db = SessionLocal()

    try:

        # =====================================
        # BUSCAR ENCONTRO
        # =====================================

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
            {
                "encontro_id": encontro_id
            }
        ).mappings().first()


        if not encontro:

            raise ValueError(
                "Encontro de bandas não encontrado."
            )


        # =====================================
        # BUSCAR BANDAS PARTICIPANTES
        # =====================================

        bandas = db.execute(
            text("""
                SELECT
                    eb.id,
                    b.nome AS banda_nome,
                    b.cidade,
                    b.uf,
                    eb.responsavel_nome,
                    eb.capitao_nome,
                    eb.maestro_nome,
                    eb.quantidade_componentes

                FROM encontro_bandas eb

                INNER JOIN bandas b
                    ON b.id = eb.banda_id

                WHERE eb.encontro_id = :encontro_id

                ORDER BY
                    b.nome ASC,
                    eb.id ASC
            """),
            {
                "encontro_id": encontro_id
            }
        ).mappings().all()


        # =====================================
        # RESUMOS
        # =====================================

        total_bandas = len(
            bandas
        )

        total_pessoas = sum(
            int(
                banda["quantidade_componentes"]
                or 0
            )
            for banda in bandas
        )


        # =====================================
        # PDF
        # =====================================

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=40,
            bottomMargin=60
        )


        estilos = getSampleStyleSheet()


        estilo = ParagraphStyle(
            "NormalRelatorio",
            parent=estilos["Normal"],
            fontSize=10,
            leading=16
        )


        estilo_tabela = ParagraphStyle(
            "Tabela",
            parent=estilos["Normal"],
            fontSize=7.5,
            leading=9
        )


        estilo_tabela_centro = ParagraphStyle(
            "TabelaCentro",
            parent=estilo_tabela,
            alignment=TA_CENTER
        )


        estilo_tabela_negrito = ParagraphStyle(
            "TabelaNegrito",
            parent=estilo_tabela,
            fontName="Helvetica-Bold"
        )


        elementos = []


        # =====================================
        # CABEÇALHO
        # =====================================

        adicionar_cabecalho(
            elementos,
            estilos,
            "RELATÓRIO DE BANDAS PARTICIPANTES"
        )


        # =====================================
        # 1 - DADOS DO ENCONTRO
        # =====================================

        elementos.append(
            Paragraph(
                "<b>1 - DADOS DO ENCONTRO</b>",
                estilo
            )
        )

        elementos.append(
            Spacer(1, 10)
        )


        dados_encontro = [

            [
                Paragraph(
                    "<b>Evento</b>",
                    estilo_tabela
                ),
                Paragraph(
                    str(
                        encontro["nome"]
                        or "-"
                    ),
                    estilo_tabela
                )
            ],

            [
                Paragraph(
                    "<b>Data</b>",
                    estilo_tabela
                ),
                Paragraph(
                    formatar_data(
                        encontro["data"]
                    ),
                    estilo_tabela
                )
            ],

            [
                Paragraph(
                    "<b>Local</b>",
                    estilo_tabela
                ),
                Paragraph(
                    str(
                        encontro["local"]
                        or "-"
                    ),
                    estilo_tabela
                )
            ],

            [
                Paragraph(
                    "<b>Horário</b>",
                    estilo_tabela
                ),
                Paragraph(
                    str(
                        encontro["horario"]
                        or "-"
                    ),
                    estilo_tabela
                )
            ],

            [
                Paragraph(
                    "<b>Status</b>",
                    estilo_tabela
                ),
                Paragraph(
                    str(
                        encontro["status"]
                        or "-"
                    ),
                    estilo_tabela
                )
            ]

        ]


        tabela_encontro = Table(
            dados_encontro,
            colWidths=[
                120,
                420
            ]
        )


        tabela_encontro.setStyle(
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
                    (0, -1),
                    colors.lightgrey
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
            tabela_encontro
        )


        elementos.append(
            Spacer(1, 20)
        )


        # =====================================
        # 2 - RESUMO
        # =====================================

        elementos.append(
            Paragraph(
                "<b>2 - RESUMO</b>",
                estilo
            )
        )

        elementos.append(
            Spacer(1, 10)
        )


        resumo = [

            [
                Paragraph(
                    "<b>Descrição</b>",
                    estilo_tabela
                ),

                Paragraph(
                    "<b>Quantidade</b>",
                    estilo_tabela_centro
                )
            ],

            [
                Paragraph(
                    "Bandas participantes",
                    estilo_tabela
                ),

                Paragraph(
                    str(total_bandas),
                    estilo_tabela_centro
                )
            ],

            [
                Paragraph(
                    "Total de componentes",
                    estilo_tabela
                ),

                Paragraph(
                    str(total_pessoas),
                    estilo_tabela_centro
                )
            ]

        ]


        tabela_resumo = Table(
            resumo,
            colWidths=[
                400,
                140
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
        # 3 - BANDAS PARTICIPANTES
        # =====================================

        elementos.append(
            Paragraph(
                "<b>3 - BANDAS PARTICIPANTES</b>",
                estilo
            )
        )

        elementos.append(
            Spacer(1, 10)
        )


        dados = [

            [

                Paragraph(
                    "<b>Nº</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Banda</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Cidade/UF</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Responsável</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Capitão</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Maestro</b>",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "<b>Pessoas</b>",
                    estilo_tabela_centro
                )

            ]

        ]


        # =====================================
        # DADOS DAS BANDAS
        # =====================================

        for numero, banda in enumerate(
            bandas,
            start=1
        ):

            cidade = (
                str(
                    banda["cidade"]
                    or ""
                ).strip()
            )

            uf = (
                str(
                    banda["uf"]
                    or ""
                ).strip().upper()
            )


            if cidade and uf:
                cidade_uf = f"{cidade} / {uf}"

            elif cidade:
                cidade_uf = cidade

            elif uf:
                cidade_uf = uf

            else:
                cidade_uf = "-"


            dados.append(

                [

                    Paragraph(
                        str(numero),
                        estilo_tabela_centro
                    ),

                    Paragraph(
                        str(
                            banda["banda_nome"]
                            or "-"
                        ),
                        estilo_tabela_negrito
                    ),

                    Paragraph(
                        cidade_uf,
                        estilo_tabela
                    ),

                    Paragraph(
                        str(
                            banda["responsavel_nome"]
                            or "-"
                        ),
                        estilo_tabela
                    ),

                    Paragraph(
                        str(
                            banda["capitao_nome"]
                            or "-"
                        ),
                        estilo_tabela
                    ),

                    Paragraph(
                        str(
                            banda["maestro_nome"]
                            or "-"
                        ),
                        estilo_tabela
                    ),

                    Paragraph(
                        str(
                            banda["quantidade_componentes"]
                            or 0
                        ),
                        estilo_tabela_centro
                    )

                ]

            )


        # =====================================
        # NENHUMA BANDA
        # =====================================

        if not bandas:

            dados.append(

                [

                    Paragraph(
                        "Nenhuma banda participante cadastrada.",
                        estilo_tabela
                    ),

                    "",
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

        tabela_bandas = Table(

            dados,

            repeatRows=1,

            colWidths=[

                25,     # Nº
                105,    # Banda
                80,     # Cidade/UF
                125,    # Responsável
                80,     # Capitão
                85,     # Maestro
                40      # Pessoas

            ]

        )


        tabela_bandas.setStyle(

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

                # Nº
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "CENTER"
                ),

                # Pessoas
                (
                    "ALIGN",
                    (6, 1),
                    (6, -1),
                    "CENTER"
                ),

                # Espaçamento
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
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
            tabela_bandas
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
                    "Este relatório apresenta as bandas "
                    "participantes cadastradas para o encontro, "
                    "incluindo seus responsáveis, representantes, "
                    "cidade de origem e quantidade de componentes."
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