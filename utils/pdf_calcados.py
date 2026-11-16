
from datetime import datetime
from io import BytesIO

from sqlalchemy import text
from flask import send_file

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Image,
    HRFlowable,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)


def gerar_pdf_calcados(db, filtros):

    try:

        # ==========================================
        # FILTROS
        # ==========================================

        status_filtro = filtros.get("status")
        situacao_filtro = filtros.get("situacao")
        funcao_filtro = filtros.get("funcao")
        excluir_funcao = filtros.get("excluir_funcao")

        condicoes = []
        parametros = {}

        if status_filtro:
            condicoes.append("status = :status")
            parametros["status"] = status_filtro

        if situacao_filtro:
            condicoes.append("situacao = :situacao")
            parametros["situacao"] = situacao_filtro

        if funcao_filtro:
            condicoes.append("funcao = :funcao")
            parametros["funcao"] = funcao_filtro

        where = ""

        if condicoes:
            where = "WHERE " + " AND ".join(condicoes)

        # ==========================================
        # TOTAL ANTES DA EXCLUSÃO
        # ==========================================

        total_localizado = db.execute(
            text(f"""
                SELECT COUNT(*)
                FROM integrantes
                {where}
            """),
            parametros
        ).scalar()

        # ==========================================
        # BUSCAR INTEGRANTES
        # ==========================================

        condicoes_relatorio = list(condicoes)
        parametros_relatorio = dict(parametros)

        if excluir_funcao:

            condicoes_relatorio.append(
                "funcao <> :excluir_funcao"
            )

            parametros_relatorio["excluir_funcao"] = excluir_funcao

        where_relatorio = ""

        if condicoes_relatorio:

            where_relatorio = (
                "WHERE " +
                " AND ".join(condicoes_relatorio)
            )

        integrantes = db.execute(
            text(f"""
                SELECT
                    codigo_integrante,
                    nome,
                    calcado,
                    status,
                    situacao,
                    funcao

                FROM integrantes

                {where_relatorio}

                ORDER BY
                    LOWER(COALESCE(funcao, '')),
                    LOWER(nome)
            """),
            parametros_relatorio
        ).mappings().all()

        total_apresentado = len(integrantes)

        total_excluido = (
            total_localizado - total_apresentado
            if excluir_funcao
            else 0
        )

        # ==========================================
        # DADOS DO PDF
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
            "<b>Relatório de Calçados</b>",
            estilos["Heading2"]
        )

        elementos.append(subtitulo)
        elementos.append(Spacer(1, 10))

        # ==========================================
        # ESTILOS
        # ==========================================

        estilo_resumo = ParagraphStyle(
            "ResumoCalcados",
            parent=estilos["Normal"],
            fontSize=8.5,
            leading=11
        )

        estilo_resumo_cabecalho = ParagraphStyle(
            "ResumoCabecalhoCalcados",
            parent=estilos["Normal"],
            fontSize=8,
            leading=10,
            alignment=1,
            fontName="Helvetica-Bold"
        )

        estilo_funcao = ParagraphStyle(
            "FuncaoCalcados",
            parent=estilos["Heading3"],
            fontSize=10,
            leading=12,
            fontName="Helvetica-Bold"
        )

        estilo_tabela = ParagraphStyle(
            "TabelaCalcado",
            parent=estilos["Normal"],
            fontSize=9,
            leading=11
        )

        estilo_cabecalho = ParagraphStyle(
            "CabecalhoCalcado",
            parent=estilos["Normal"],
            fontSize=9,
            leading=11,
            alignment=1,
            fontName="Helvetica-Bold"
        )

        estilo_centro = ParagraphStyle(
            "CentroCalcado",
            parent=estilos["Normal"],
            fontSize=9,
            leading=11,
            alignment=1
        )

        # ==========================================
        # DATA
        # ==========================================

        data_geracao = datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )

        # ==========================================
        # FILTROS APLICADOS
        # ==========================================

        filtros_html = []

        if status_filtro:
            filtros_html.append(
                f"<b>Status:</b> {status_filtro}"
            )

        if situacao_filtro:
            filtros_html.append(
                f"<b>Situação:</b> {situacao_filtro}"
            )

        if funcao_filtro:
            filtros_html.append(
                f"<b>Função:</b> {funcao_filtro}"
            )

        if not filtros_html:
            filtros_html.append(
                "<b>Todos os integrantes</b>"
            )

        texto_filtros = "<br/>".join(filtros_html)

        # ==========================================
        # EXCLUSÃO
        # ==========================================

        if excluir_funcao:

            texto_exclusao = f"""
                <b>Função excluída:</b><br/>
                {excluir_funcao}
            """

        else:

            texto_exclusao = """
                <b>Nenhuma função excluída</b>
            """

        # ==========================================
        # RESULTADO
        # ==========================================

        if excluir_funcao:

            texto_resultado = f"""
                <b>Total localizado:</b>
                {total_localizado}
                <br/>
                <b>Excluídos:</b>
                {total_excluido}
                <br/>
                <b>Apresentados:</b>
                {total_apresentado}
            """

        else:

            texto_resultado = f"""
                <b>Total apresentado:</b>
                {total_apresentado}
            """

        # ==========================================
        # RESUMO EM 3 COLUNAS
        # ==========================================

        dados_resumo = [
            [
                Paragraph(
                    "FILTROS APLICADOS",
                    estilo_resumo_cabecalho
                ),

                Paragraph(
                    "EXCLUSÃO",
                    estilo_resumo_cabecalho
                ),

                Paragraph(
                    "RESULTADO",
                    estilo_resumo_cabecalho
                )
            ],

            [
                Paragraph(
                    texto_filtros,
                    estilo_resumo
                ),

                Paragraph(
                    texto_exclusao,
                    estilo_resumo
                ),

                Paragraph(
                    texto_resultado,
                    estilo_resumo
                )
            ]
        ]

        tabela_resumo = Table(
            dados_resumo,
            colWidths=[
                170,
                170,
                170
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
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, 0),
                    "CENTER"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        elementos.append(tabela_resumo)
        elementos.append(Spacer(1, 18))

        # ==========================================
        # AGRUPAMENTO POR FUNÇÃO E TAMANHO
        # ==========================================

        grupos_funcoes = {}

        for pessoa in integrantes:

            funcao = pessoa["funcao"]

            if funcao is None or str(funcao).strip() == "":
                funcao = "FUNÇÃO NÃO INFORMADA"
            else:
                funcao = str(funcao).strip()

            calcado = pessoa["calcado"]

            if calcado is None or str(calcado).strip() == "":
                calcado = "Não informado"
            else:
                calcado = str(calcado).strip()

            if funcao not in grupos_funcoes:
                grupos_funcoes[funcao] = {}

            if calcado not in grupos_funcoes[funcao]:
                grupos_funcoes[funcao][calcado] = 0

            grupos_funcoes[funcao][calcado] += 1

        # ==========================================
        # ORDENAR TAMANHOS
        # ==========================================

        def chave_calcado(item):

            valor = item[0]

            try:
                return (
                    0,
                    float(valor)
                )

            except (ValueError, TypeError):
                return (
                    1,
                    str(valor).lower()
                )

        # ==========================================
        # TÍTULO DA SEÇÃO
        # ==========================================

        elementos.append(
            Paragraph(
                "<b>Distribuição de Calçados por Função</b>",
                estilo_resumo_cabecalho
            )
        )

        elementos.append(Spacer(1, 10))

        # ==========================================
        # UMA TABELA PARA CADA FUNÇÃO
        # ==========================================

        for funcao in sorted(
            grupos_funcoes.keys(),
            key=lambda x: str(x).lower()
        ):

            elementos.append(
                Paragraph(
                    f"<b>FUNÇÃO: {funcao.upper()}</b>",
                    estilo_funcao
                )
            )

            elementos.append(Spacer(1, 5))

            dados_funcao = [
                [
                    Paragraph(
                        "TAMANHO",
                        estilo_cabecalho
                    ),

                    Paragraph(
                        "QUANTIDADE",
                        estilo_cabecalho
                    )
                ]
            ]

            distribuicao_funcao = grupos_funcoes[funcao]

            itens_funcao = sorted(
                distribuicao_funcao.items(),
                key=chave_calcado
            )

            total_funcao = 0

            for calcado, quantidade in itens_funcao:

                total_funcao += quantidade

                dados_funcao.append([
                    Paragraph(
                        str(calcado),
                        estilo_centro
                    ),

                    Paragraph(
                        f"<b>{quantidade}</b>",
                        estilo_centro
                    )
                ])

            # ======================================
            # TOTAL DA FUNÇÃO
            # ======================================

            dados_funcao.append([
                Paragraph(
                    "<b>TOTAL</b>",
                    estilo_centro
                ),

                Paragraph(
                    f"<b>{total_funcao}</b>",
                    estilo_centro
                )
            ])

            tabela_funcao = Table(
                dados_funcao,
                colWidths=[
                    180,
                    180
                ],
                repeatRows=1
            )

            tabela_funcao.hAlign = "CENTER"

            tabela_funcao.setStyle(
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
                        "BACKGROUND",
                        (0, -1),
                        (-1, -1),
                        colors.whitesmoke
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
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
                        7
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
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

            elementos.append(tabela_funcao)
            elementos.append(Spacer(1, 12))

        # ==========================================
        # LISTA DE INTEGRANTES
        # ==========================================

        elementos.append(Spacer(1, 8))

        elementos.append(
            Paragraph(
                "<b>Lista de Integrantes</b>",
                estilo_resumo_cabecalho
            )
        )

        elementos.append(Spacer(1, 8))

        # ==========================================
        # DADOS DA TABELA
        # ==========================================

        dados = [
            [
                Paragraph(
                    "Código Integrante",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Integrante",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Calçado",
                    estilo_cabecalho
                )
            ]
        ]

        for pessoa in integrantes:

            dados.append([
                Paragraph(
                    str(
                        pessoa["codigo_integrante"]
                    ),
                    estilo_centro
                ),

                Paragraph(
                    (pessoa["nome"] or "").title(),
                    estilo_tabela
                ),

                Paragraph(
                    str(pessoa["calcado"])
                    if pessoa["calcado"]
                    else "-",
                    estilo_centro
                )
            ])

        # ==========================================
        # TABELA DE INTEGRANTES
        # ==========================================

        tabela = Table(
            dados,
            colWidths=[
                110,
                300,
                70
            ],
            repeatRows=1
        )

        tabela.setStyle(
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
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, 0),
                    "CENTER"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                )
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
            download_name="relatorio_calcados_brilho_negro.pdf",
            mimetype="application/pdf"
        )

    finally:
        db.close()
