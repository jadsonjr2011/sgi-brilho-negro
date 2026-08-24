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
    PageBreak
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER



# =====================================
# RODAPÉ
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
            estilo
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
                fontSize=20
            )
        )

    )


    elementos.append(
        Spacer(1,8)
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



# =====================================
# FORMATA VALOR
# =====================================

def moeda(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X",".")
    )



# =====================================
# GERA PDF
# =====================================

def gerar_pdf_financeiro(
    movimentacoes,
    receitas,
    despesas,
    saldo,
    total_doacoes,
    total_patrocinios,
    quantidade_movimentos,
    temporada
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
        "normal",
        parent=estilos["Normal"],
        fontSize=11,
        leading=18
    )


    elementos = []



    adicionar_cabecalho(
        elementos,
        estilos,
        f"PRESTAÇÃO DE CONTAS FINANCEIRA - TEMPORADA {temporada}"
    )



    # =====================================
    # 1 - RESUMO
    # =====================================


    elementos.append(

        Paragraph(
            "<b>1 - RESUMO FINANCEIRO</b>",
            estilo
        )

    )


    elementos.append(
        Spacer(1,10)
    )



    resumo = [

        ["Descrição","Valor"],

        ["Total Receitas", moeda(receitas)],

        ["Total Despesas", moeda(despesas)],

        ["Saldo Final", moeda(saldo)],

        ["Doações", moeda(total_doacoes)],

        ["Patrocínios", moeda(total_patrocinios)],

        ["Quantidade Movimentações", str(quantidade_movimentos)]

    ]



    tabela = Table(
        resumo,
        colWidths=[250,150]
    )


    tabela.setStyle(

        TableStyle([

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),

            ("FONT",(0,0),(-1,0),"Helvetica-Bold")

        ])

    )


    elementos.append(tabela)



    elementos.append(
        Spacer(1,25)
    )



    # =====================================
    # FUNÇÃO TABELA
    # =====================================


    def adicionar_tabela(titulo, lista):


        elementos.append(

            Paragraph(
                f"<b>{titulo}</b>",
                estilo
            )

        )


        elementos.append(
            Spacer(1,10)
        )


        dados = [

            [
                "Data",
                "Categoria",
                "Descrição",
                "Valor"
            ]

        ]


        total = 0


        for item in lista:


            total += item.valor


            dados.append(
                [
                    item.data_movimento.strftime("%d/%m/%Y"),
                    item.categoria,
                    Paragraph(
                        str(item.descricao or ""),
                        ParagraphStyle(
                            "DescricaoTabela",
                            parent=estilos["Normal"],
                            fontSize=9,
                            leading=11
                        )
                    ),
                    moeda(item.valor)
                ]
            )



        dados.append(

            [

                "",

                "",

                "TOTAL",

                moeda(total)

            ]

        )



        tabela = Table(

            dados,

            repeatRows=1,

            colWidths=[70,110,180,80]

        )


        tabela.setStyle(

            TableStyle([

                ("GRID",(0,0),(-1,-1),0.5,colors.grey),

                ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),

                ("FONT",(0,0),(-1,0),"Helvetica-Bold"),

                ("FONT",(0,-1),(-1,-1),"Helvetica-Bold"),

                # Alinhamento vertical
                ("VALIGN",(0,0),(-1,-1),"MIDDLE"),

                # Cabeçalhos centralizados
                ("ALIGN",(0,0),(-1,0),"CENTER"),

                # Data centralizada
                ("ALIGN",(0,1),(0,-1),"CENTER"),

                # Categoria centralizada
                ("ALIGN",(1,1),(1,-1),"CENTER"),

                # Valor centralizado
                ("ALIGN",(3,1),(3,-1),"CENTER"),

                # Descrição à esquerda
                ("ALIGN",(2,1),(2,-1),"LEFT"),

                # Espaçamento interno
                ("LEFTPADDING",(0,0),(-1,-1),5),

                ("RIGHTPADDING",(0,0),(-1,-1),5),

                ("TOPPADDING",(0,0),(-1,-1),5),

                ("BOTTOMPADDING",(0,0),(-1,-1),5)

            ])

        )


        elementos.append(tabela)


        elementos.append(
            Spacer(1,20)
        )



    receitas_lista = [

        x for x in movimentacoes

        if x.tipo == "RECEITA"

    ]


    despesas_lista = [

        x for x in movimentacoes

        if x.tipo == "DESPESA"

    ]



    # =====================================
    # RECEITAS
    # =====================================


    elementos.append(
        PageBreak()
    )


    adicionar_tabela(
        "2 - RECEITAS",
        receitas_lista
    )



    # =====================================
    # DESPESAS
    # =====================================


    adicionar_tabela(
        "3 - DESPESAS",
        despesas_lista
    )


    # =====================================
    # 4 - RESULTADO FINANCEIRO
    # =====================================


    elementos.append(
        Spacer(1,20)
    )


    elementos.append(

        Paragraph(
            "<b>4 - RESULTADO FINANCEIRO</b>",
            estilo
        )

    )


    elementos.append(
        Spacer(1,10)
    )



    resultado = saldo


    situacao = "SUPERÁVIT FINANCEIRO"

    if resultado < 0:

        situacao = "DÉFICIT FINANCEIRO"



    resultado_texto = f"""

    O presente relatório apresenta o resultado financeiro da Associação
    Cultural de Percussão Rudimental Brilho Negro referente à temporada
    <b>{temporada}</b>, considerando todas as receitas e despesas registradas
    no sistema de gestão.

    <br/><br/>

    <b>Receitas Totais:</b> {moeda(receitas)}<br/>

    <b>Despesas Totais:</b> {moeda(despesas)}<br/>

    <b>Resultado Financeiro:</b> {moeda(resultado)}<br/>

    <b>Situação:</b> {situacao}

    """



    elementos.append(

        Paragraph(
            resultado_texto,
            estilo
        )

    )



    # =====================================
    # 5 - DECLARAÇÃO DE RESPONSABILIDADE
    # =====================================


    elementos.append(
        Spacer(1,30)
    )


    elementos.append(

        Paragraph(
            "<b>5 - DECLARAÇÃO DE RESPONSABILIDADE</b>",
            estilo
        )

    )


    elementos.append(
        Spacer(1,10)
    )



    declaracao = """

    Declaro, para os devidos fins, que as informações financeiras apresentadas
    neste documento refletem os registros de movimentações cadastrados no
    Sistema de Gestão da Associação Cultural de Percussão Rudimental Brilho Negro.

    <br/><br/>

    A presente prestação de contas contempla receitas, despesas, doações,
    patrocínios e demais movimentações financeiras realizadas durante a
    temporada informada.

    <br/><br/>

    Os responsáveis pela administração financeira da associação declaram estar
    cientes das informações apresentadas e comprometem-se pela veracidade dos
    dados registrados.

    <br/><br/><br/><br/>


    _________________________________________

    <br/>

    Responsável Financeiro

    <br/><br/>


    _________________________________________

    <br/>

    Presidente / Diretoria

    """

    elementos.append(

        Paragraph(
            declaracao,
            estilo
        )

    )

    doc.build(
        elementos,
        onFirstPage=adicionar_rodape,
        onLaterPages=adicionar_rodape
    )


    buffer.seek(0)


    return buffer