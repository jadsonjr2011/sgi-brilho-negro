from io import BytesIO
from datetime import datetime
from reportlab.platypus import Flowable
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
# CAIXA DE CONFERÊNCIA
# =====================================

class CaixaConferencia(Flowable):

    def __init__(self, tamanho=10):
        Flowable.__init__(self)
        self.tamanho = tamanho
        self.width = tamanho
        self.height = tamanho

    def draw(self):

        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(1)

        self.canv.rect(
            0,
            0,
            self.tamanho,
            self.tamanho,
            stroke=1,
            fill=0
        )

# =====================================
# GERA PDF — LISTA DE EMBARQUE
# =====================================

def gerar_pdf_lista_embarque(
    viagem,
    participantes
):

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
        "normal_embarque",
        parent=estilos["Normal"],
        fontSize=10,
        leading=16
    )

    estilo_tabela = ParagraphStyle(
        "TabelaEmbarque",
        parent=estilos["Normal"],
        fontSize=9,
        leading=11
    )

    estilo_tabela_centro = ParagraphStyle(
        "TabelaEmbarqueCentro",
        parent=estilo_tabela,
        alignment=TA_CENTER
    )

    estilo_info = ParagraphStyle(
        "TabelaInfo",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
        alignment=TA_CENTER
    )

    # =====================================
    # ESTILO PARA AS CAIXAS DE CONFERÊNCIA
    # =====================================

    estilo_check = ParagraphStyle(
        "TabelaCheck",
        parent=estilos["Normal"],
        fontSize=13,
        leading=14,
        alignment=TA_CENTER
    )

    elementos = []

    # =====================================
    # CABEÇALHO PADRÃO
    # =====================================

    adicionar_cabecalho(
        elementos,
        estilos,
        "CONTROLE DE EMBARQUE"
    )

    # =====================================
    # INFORMAÇÕES DA VIAGEM
    # =====================================

    data_saida = (
        viagem["data_saida"].strftime("%d/%m/%Y")
        if viagem["data_saida"]
        else "-"
    )

    data_retorno = (
        viagem["data_retorno"].strftime("%d/%m/%Y")
        if viagem["data_retorno"]
        else "-"
    )

    # =====================================
    # TABELA HORIZONTAL — DADOS DA VIAGEM
    # =====================================

    dados_viagem = [

        [

            Paragraph(
                "<b>EVENTO</b>",
                estilo_info
            ),

            Paragraph(
                "<b>DESTINO</b>",
                estilo_info
            ),

            Paragraph(
                "<b>SAÍDA</b>",
                estilo_info
            ),

            Paragraph(
                "<b>RETORNO</b>",
                estilo_info
            ),

            Paragraph(
                "<b>RESPONSÁVEL</b>",
                estilo_info
            ),

            Paragraph(
                "<b>PASSAGEIROS</b>",
                estilo_info
            )

        ],

        [

            Paragraph(
                str(
                    viagem["evento"]
                    or "-"
                ),
                estilo_info
            ),

            Paragraph(
                str(
                    viagem["destino"]
                    or "-"
                ),
                estilo_info
            ),

            Paragraph(
                data_saida,
                estilo_info
            ),

            Paragraph(
                data_retorno,
                estilo_info
            ),

            Paragraph(
                str(
                    viagem["responsavel"]
                    or "-"
                ),
                estilo_info
            ),

            Paragraph(
                str(len(participantes)),
                estilo_info
            )

        ]

    ]

    tabela_viagem = Table(
        dados_viagem,
        colWidths=[
            110,
            90,
            60,
            60,
            105,
            55
        ],
        repeatRows=1
    )

    tabela_viagem.setStyle(
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
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

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
        tabela_viagem
    )

    elementos.append(
        Spacer(1, 25)
    )

    # =====================================
    # RELAÇÃO DE PASSAGEIROS
    # =====================================

    elementos.append(
        Paragraph(
            "<b>RELAÇÃO DE PASSAGEIROS</b>",
            estilo
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    # =====================================
    # CABEÇALHO DA TABELA
    # =====================================

    dados = [

        [

            Paragraph(
                "<b>Nº</b>",
                estilo_tabela_centro
            ),

            Paragraph(
                "<b>NOME COMPLETO</b>",
                estilo_tabela_centro
            ),

            Paragraph(
                "<b>CPF</b>",
                estilo_tabela_centro
            ),

            Paragraph(
                "<b>IDA</b>",
                estilo_tabela_centro
            ),

            Paragraph(
                "<b>VOLTA</b>",
                estilo_tabela_centro
            )

        ]

    ]

    # =====================================
    # PARTICIPANTES
    # =====================================

    for numero, pessoa in enumerate(
        participantes,
        start=1
    ):

        nome = (
            pessoa["nome"]
            or "-"
        )

        cpf = pessoa["cpf"]

        if cpf:

            cpf_limpo = (
                str(cpf)
                .replace(".", "")
                .replace("-", "")
                .replace("/", "")
                .replace(" ", "")
            )

            if len(cpf_limpo) == 11:

                cpf = (
                    f"{cpf_limpo[0:3]}."
                    f"{cpf_limpo[3:6]}."
                    f"{cpf_limpo[6:9]}-"
                    f"{cpf_limpo[9:11]}"
                )

            else:

                cpf = str(cpf)

        else:

            cpf = "Não informado"

        dados.append(

            [

                Paragraph(
                    str(numero),
                    estilo_tabela_centro
                ),

                Paragraph(
                    nome,
                    estilo_tabela
                ),

                Paragraph(
                    cpf,
                    estilo_tabela_centro
                ),

                CaixaConferencia(10),

                CaixaConferencia(10)

            ]

        )

    # =====================================
    # NENHUM PARTICIPANTE
    # =====================================

    if not participantes:

        dados.append(

            [

                Paragraph(
                    "-",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "Nenhum participante cadastrado.",
                    estilo_tabela
                ),

                Paragraph(
                    "-",
                    estilo_tabela_centro
                ),

                Paragraph(
                    "☐",
                    estilo_check
                ),

                Paragraph(
                    "☐",
                    estilo_check
                )

            ]

        )

    # =====================================
    # TABELA DE PASSAGEIROS
    # =====================================

    tabela_participantes = Table(

        dados,

        repeatRows=1,

        colWidths=[

            30,     # Nº
            230,    # Nome
            110,    # CPF
            55,     # Ida
            55      # Volta

        ]

    )

    tabela_participantes.setStyle(

        TableStyle([

            # =====================================
            # GRADE
            # =====================================

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            # =====================================
            # CABEÇALHO
            # =====================================

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

            # =====================================
            # ALINHAMENTO VERTICAL
            # =====================================

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            # =====================================
            # NÚMERO
            # =====================================

            (
                "ALIGN",
                (0, 1),
                (0, -1),
                "CENTER"
            ),

            # =====================================
            # CPF
            # =====================================

            (
                "ALIGN",
                (2, 1),
                (2, -1),
                "CENTER"
            ),

            # =====================================
            # IDA
            # =====================================

            (
                "ALIGN",
                (3, 1),
                (3, -1),
                "CENTER"
            ),

            # =====================================
            # VOLTA
            # =====================================

            (
                "ALIGN",
                (4, 1),
                (4, -1),
                "CENTER"
            ),

            # =====================================
            # ESPAÇAMENTO
            # =====================================

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
        tabela_participantes
    )

    elementos.append(
        Spacer(1, 20)
    )

    # =====================================
    # OBSERVAÇÃO
    # =====================================

    elementos.append(

        Paragraph(
            (
                "Marque a coluna <b>IDA</b> após a conferência "
                "do embarque na saída e a coluna <b>VOLTA</b> "
                "após a conferência do retorno."
            ),
            estilo
        )

    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(

        Paragraph(
            (
                "Esta relação destina-se ao controle e "
                "conferência dos passageiros durante o "
                "embarque e desembarque da viagem."
            ),
            estilo
        )

    )

    # =====================================
    # GERAR PDF
    # =====================================

    doc.build(

        elementos,

        onFirstPage=adicionar_rodape,

        onLaterPages=adicionar_rodape

    )

    buffer.seek(0)

    return buffer