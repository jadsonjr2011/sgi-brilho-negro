
from io import BytesIO
from datetime import datetime

from sqlalchemy import text

from flask import send_file

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Image,
    HRFlowable,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)


def gerar_pdf_integrantes(db, filtros):

    # ==========================================
    # FILTROS
    # ==========================================

    status_filtro = filtros.get("status")
    situacao_filtro = filtros.get("situacao")
    funcao_filtro = filtros.get("funcao")
    instrumento_filtro = filtros.get("instrumento")

    condicoes = []
    parametros = {}

    if status_filtro:
        condicoes.append(
            "integrantes.status = :status"
        )
        parametros["status"] = status_filtro

    if situacao_filtro:
        condicoes.append(
            "integrantes.situacao = :situacao"
        )
        parametros["situacao"] = situacao_filtro

    if funcao_filtro:
        condicoes.append(
            "integrantes.funcao = :funcao"
        )
        parametros["funcao"] = funcao_filtro

    if instrumento_filtro:
        condicoes.append(
            "integrantes.instrumento_id = :instrumento"
        )
        parametros["instrumento"] = instrumento_filtro

    where = ""

    if condicoes:
        where = "WHERE " + " AND ".join(condicoes)

    # ==========================================
    # BUSCAR INTEGRANTES
    # ==========================================

    try:

        integrantes = db.execute(
            text(f"""
                SELECT
                    integrantes.codigo_integrante,
                    integrantes.nome,
                    integrantes.cpf,
                    integrantes.data_nascimento,
                    integrantes.cidade,
                    integrantes.estado,
                    integrantes.status,
                    integrantes.situacao,
                    integrantes.funcao,
                    instrumentos.nome AS instrumento

                FROM integrantes

                LEFT JOIN instrumentos
                    ON instrumentos.id = integrantes.instrumento_id

                {where}

                ORDER BY LOWER(integrantes.nome)
            """),
            parametros
        ).mappings().all()

        total_apresentado = len(integrantes)

        # ======================================
        # DISTRIBUIÇÃO POR FUNÇÃO
        # ======================================

        distribuicao_funcao = {}

        for pessoa in integrantes:

            funcao = (
                pessoa["funcao"]
                or "Integrantes sem função definida"
            )

            distribuicao_funcao[funcao] = (
                distribuicao_funcao.get(funcao, 0) + 1
            )

        # ======================================
        # NOME DO INSTRUMENTO
        # ======================================

        instrumento_nome = None

        if instrumento_filtro:

            instrumento_nome = db.execute(
                text("""
                    SELECT nome
                    FROM instrumentos
                    WHERE id = :id
                """),
                {
                    "id": instrumento_filtro
                }
            ).scalar()

    finally:
        db.close()

    # ==========================================
    # CRIAR PDF
    # ==========================================

    arquivo = BytesIO()

    pdf = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        topMargin=25,
        bottomMargin=30,
        leftMargin=35,
        rightMargin=35
    )

    elementos = []

    estilos = getSampleStyleSheet()

    # ==========================================
    # LOGO
    # ==========================================

    logo = Image(
        "static/img/logo_relatorio.PNG",
        width=320,
        height=79
    )

    logo.hAlign = "CENTER"

    elementos.append(logo)
    elementos.append(Spacer(1, 5))

    # ==========================================
    # TÍTULO
    # ==========================================

    titulo = Paragraph(
        """
        <b>BRILHO NEGRO</b><br/>
        <font size="14">
        Sistema de Gestão de Integrantes
        </font>
        """,
        estilos["Title"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 8))

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )

    elementos.append(Spacer(1, 15))

    subtitulo = Paragraph(
        "<b>Relatório de Integrantes</b>",
        estilos["Heading2"]
    )

    elementos.append(subtitulo)
    elementos.append(Spacer(1, 15))

    # ==========================================
    # DATA
    # ==========================================

    data_geracao = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    # ==========================================
    # ESTILOS DOS RESUMOS
    # ==========================================

    estilo_resumo = ParagraphStyle(
        "ResumoRelatorio",
        parent=estilos["Normal"],
        fontSize=8.5,
        leading=11
    )

    estilo_resumo_titulo = ParagraphStyle(
        "ResumoTitulo",
        parent=estilos["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold"
    )

    estilo_funcao = ParagraphStyle(
        "DistribuicaoFuncao",
        parent=estilos["Normal"],
        fontSize=8.5,
        leading=11
    )

    # ==========================================
    # FILTROS APLICADOS
    # ==========================================

    filtros_html = []

    if status_filtro:
        filtros_html.append(
            f"<b>Status Cadastro:</b> {status_filtro}"
        )

    if situacao_filtro:
        filtros_html.append(
            f"<b>Situação:</b> {situacao_filtro}"
        )

    if funcao_filtro:
        filtros_html.append(
            f"<b>Função:</b> {funcao_filtro}"
        )

    if instrumento_filtro:
        filtros_html.append(
            f"<b>Instrumento:</b> "
            f"{instrumento_nome or instrumento_filtro}"
        )

    if not filtros_html:
        filtros_html.append(
            "<b>Filtros:</b> Todos"
        )

    texto_filtros = "<br/>".join(filtros_html)

    # ==========================================
    # RESUMO DOS RESULTADOS
    # ==========================================

    texto_resultados = f"""
        <b>Resultados da consulta</b><br/>
        Total apresentado:
        <b>{total_apresentado}</b>
    """

    # ==========================================
    # RESUMO EM 3 COLUNAS
    # ==========================================

    resumo_dados = [
        [
            Paragraph(
                f"""
                <b>Gerado em</b><br/>
                {data_geracao}
                """,
                estilo_resumo
            ),

            Paragraph(
                f"""
                <b>Filtros aplicados</b><br/>
                {texto_filtros}
                """,
                estilo_resumo
            ),

            Paragraph(
                texto_resultados,
                estilo_resumo
            )
        ]
    ]

    tabela_resumo = Table(
        resumo_dados,
        colWidths=[
            160,
            190,
            150
        ]
    )

    tabela_resumo.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
        ])
    )

    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 15))

    # ==========================================
    # DISTRIBUIÇÃO POR FUNÇÃO
    # ==========================================

    elementos.append(
        Paragraph(
            "<b>Distribuição por Função</b>",
            estilo_resumo_titulo
        )
    )

    elementos.append(Spacer(1, 6))

    funcoes_lista = [
        f"<b>{funcao}</b>: {quantidade}"
        for funcao, quantidade in distribuicao_funcao.items()
    ]

    colunas_funcoes = [
        [],
        [],
        []
    ]

    for indice, funcao in enumerate(funcoes_lista):
        colunas_funcoes[indice % 3].append(funcao)

    funcoes_colunas = []

    for coluna in colunas_funcoes:

        funcoes_colunas.append(
            Paragraph(
                "<br/>".join(coluna),
                estilo_funcao
            )
        )

    tabela_funcoes = Table(
        [funcoes_colunas],
        colWidths=[
            167,
            167,
            166
        ]
    )

    tabela_funcoes.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
        ])
    )

    elementos.append(tabela_funcoes)
    elementos.append(Spacer(1, 15))

    # ==========================================
    # ESTILOS DA TABELA
    # ==========================================

    estilo_tabela = ParagraphStyle(
        "Tabela",
        parent=estilos["Normal"],
        fontSize=7.5,
        leading=9,
        alignment=1
    )

    estilo_cabecalho = ParagraphStyle(
        "CabecalhoTabela",
        parent=estilos["Normal"],
        fontSize=7,
        leading=8,
        alignment=1,
        fontName="Helvetica-Bold"
    )

    estilo_centro = ParagraphStyle(
        "Centro",
        parent=estilos["Normal"],
        fontSize=7.5,
        leading=9,
        alignment=1
    )

    estilo_integrante = ParagraphStyle(
        "Integrante",
        parent=estilos["Normal"],
        fontSize=7.5,
        leading=9,
        alignment=0
    )

    # ==========================================
    # DADOS DA TABELA
    # ==========================================

    dados = [
        [
            Paragraph("Nº", estilo_cabecalho),
            Paragraph("CÓDIGO", estilo_cabecalho),
            Paragraph("INTEGRANTE", estilo_cabecalho),
            Paragraph("CPF", estilo_cabecalho),
            Paragraph("NASCIMENTO", estilo_cabecalho),
            Paragraph("CIDADE/UF", estilo_cabecalho),
            Paragraph("FUNÇÃO", estilo_cabecalho),
            Paragraph("INSTRUMENTO", estilo_cabecalho),
            Paragraph("STATUS", estilo_cabecalho)
        ]
    ]

    for numero, pessoa in enumerate(integrantes, start=1):

        if pessoa["data_nascimento"]:

            try:
                data_nascimento = datetime.strptime(
                    str(pessoa["data_nascimento"]),
                    "%Y-%m-%d"
                ).strftime("%d/%m/%Y")

            except ValueError:
                data_nascimento = str(
                    pessoa["data_nascimento"]
                )

        else:
            data_nascimento = "-"

        cidade = pessoa["cidade"] or "-"
        estado = pessoa["estado"] or "-"

        cidade_uf = f"{cidade}/{estado}"

        dados.append([
            Paragraph(
                str(numero),
                estilo_centro
            ),

            Paragraph(
                str(pessoa["codigo_integrante"] or "-"),
                estilo_centro
            ),

            Paragraph(
                (pessoa["nome"] or "-").title(),
                estilo_integrante
            ),

            Paragraph(
                str(pessoa["cpf"] or "-"),
                estilo_centro
            ),

            Paragraph(
                data_nascimento,
                estilo_centro
            ),

            Paragraph(
                cidade_uf,
                estilo_tabela
            ),

            Paragraph(
                pessoa["funcao"] or "-",
                estilo_tabela
            ),

            Paragraph(
                pessoa["instrumento"] or "-",
                estilo_tabela
            ),

            Paragraph(
                pessoa["status"] or "-",
                estilo_tabela
            )
        ])

    # ==========================================
    # TABELA
    # ==========================================

    tabela = Table(
        dados,
        colWidths=[
            20,  # Numeração
            43,  # Código
            100, # Integrante
            65,  # CPF
            55,  # Nascimento
            75,  # Cidade/UF
            52,  # Função
            65,  # Instrumento
            65   # Status
        ],
        repeatRows=1
    )

    tabela.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

            # Cabeçalho centralizado
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),

            # Dados centralizados
            ("ALIGN", (0, 1), (1, -1), "CENTER"),
            ("ALIGN", (3, 1), (-1, -1), "CENTER"),

            # Integrante permanece à esquerda
            ("ALIGN", (2, 1), (2, -1), "LEFT"),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
        ])
    )

    elementos.append(tabela)
    elementos.append(Spacer(1, 20))

    # ==========================================
    # RODAPÉ
    # ==========================================

    rodape = Paragraph(
        """
        SGI Brilho Negro<br/>
        Documento gerado automaticamente.
        """,
        estilos["Normal"]
    )

    elementos.append(rodape)

    # ==========================================
    # GERAR PDF
    # ==========================================

    pdf.build(elementos)

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="relatorio_integrantes_brilho_negro.pdf",
        mimetype="application/pdf"
    )
