from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape
from pathlib import Path

from sqlalchemy import text

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
)


def gerar_pdf_competicao(db, competicao_id, categoria_id=None):

    try:
        # =====================================================
        # DADOS DA COMPETIÇÃO
        # =====================================================

        competicao = db.execute(
            text("""
                SELECT *
                FROM competicoes
                WHERE id = :id
            """),
            {"id": competicao_id}
        ).mappings().first()

        if not competicao:
            return None

        # =====================================================
        # CATEGORIAS E INTEGRANTES
        # =====================================================

        sql = """
            SELECT
                cc.id AS categoria_id,
                cc.nome AS categoria_nome,
                i.id AS integrante_id,
                i.nome AS integrante_nome,
                i.funcao,
                ins.nome AS instrumento
            FROM competicao_categorias cc

            LEFT JOIN competicao_integrantes ci
                ON ci.categoria_id = cc.id

            LEFT JOIN integrantes i
                ON i.id = ci.integrante_id

            LEFT JOIN instrumentos ins
                ON ins.id = i.instrumento_id

            WHERE cc.competicao_id = :competicao_id
        """

        parametros = {
            "competicao_id": competicao_id
        }

        if categoria_id is not None:
            sql += """
                AND cc.id = :categoria_id
            """
            parametros["categoria_id"] = categoria_id

        sql += """
            ORDER BY
                LOWER(cc.nome),
                LOWER(i.nome)
        """

        registros = db.execute(
            text(sql),
            parametros
        ).mappings().all()

        if not registros:
            return None

        # =====================================================
        # AGRUPAR POR CATEGORIA
        # =====================================================

        categorias = {}

        for registro in registros:

            cid = registro["categoria_id"]

            if cid not in categorias:
                categorias[cid] = {
                    "nome": registro["categoria_nome"],
                    "integrantes": []
                }

            if registro["integrante_id"] is not None:
                categorias[cid]["integrantes"].append(registro)

        total_integrantes = sum(
            len(c["integrantes"])
            for c in categorias.values()
        )

        # =====================================================
        # CONFIGURAÇÃO DO PDF
        # =====================================================

        buffer = BytesIO()

        documento = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=35,
            leftMargin=35,
            topMargin=25,
            bottomMargin=30
        )

        estilos = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            "TituloBN",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111111"),
            spaceAfter=3
        )

        estilo_subtitulo = ParagraphStyle(
            "SubtituloBN",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444")
        )

        estilo_relatorio = ParagraphStyle(
            "RelatorioBN",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=10
        )

        estilo_normal = ParagraphStyle(
            "NormalBN",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11
        )

        estilo_categoria = ParagraphStyle(
            "CategoriaBN",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#222222"),
            spaceBefore=12,
            spaceAfter=5
        )

        estilo_cabecalho = ParagraphStyle(
            "CabecalhoBN",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.black
        )

        estilo_nome = ParagraphStyle(
            "NomeBN",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_LEFT
        )

        estilo_celula = ParagraphStyle(
            "CelulaBN",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER
        )

        elementos = []

        # =====================================================
        # CABEÇALHO
        # =====================================================

        caminho_logo = (
            Path(__file__).resolve().parent.parent
            / "static"
            / "img"
            / "logo_relatorio.PNG"
        )

        if caminho_logo.exists():

            logo = Image(
                str(caminho_logo),
                width=320,
                height=79
            )

            logo.hAlign = "CENTER"
            elementos.append(logo)

        elementos.append(
            Paragraph("BRILHO NEGRO", estilo_titulo)
        )

        elementos.append(
            Paragraph(
                "Sistema de Gestão de Integrantes",
                estilo_subtitulo
            )
        )

        elementos.append(Spacer(1, 8))

        elementos.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#555555")
            )
        )

        elementos.append(
            Paragraph(
                "RELATÓRIO DE COMPETIÇÃO",
                estilo_relatorio
            )
        )

        # =====================================================
        # INFORMAÇÕES DA COMPETIÇÃO
        # =====================================================

        data_inicio = competicao["data_inicio"]
        data_termino = competicao["data_termino"]

        if data_inicio:
            data_inicio = data_inicio.strftime("%d/%m/%Y")

        if data_termino:
            data_termino = data_termino.strftime("%d/%m/%Y")

        cidade_uf = " - ".join(
            str(v) for v in [
                competicao["cidade"],
                competicao["uf"]
            ] if v
        )

        nome_categoria = (
            categorias[next(iter(categorias))]["nome"]
            if categoria_id is not None
            else "Todas as categorias"
        )

        dados_info = [
            [
                Paragraph(
                    f"<b>Competição:</b> {escape(str(competicao['nome']))}",
                    estilo_normal
                ),
                Paragraph(
                    f"<b>Status:</b> {escape(str(competicao['status']))}",
                    estilo_normal
                ),
                Paragraph(
                    f"<b>Categoria:</b> {escape(nome_categoria)}",
                    estilo_normal
                )
            ],
            [
                Paragraph(
                    f"<b>Local:</b> {escape(str(competicao['local'] or '-'))}",
                    estilo_normal
                ),
                Paragraph(
                    f"<b>Cidade/UF:</b> {escape(cidade_uf or '-')}",
                    estilo_normal
                ),
                Paragraph(
                    f"<b>Período:</b> {data_inicio or '-'} a {data_termino or '-'}",
                    estilo_normal
                )
            ],
            [
                Paragraph(
                    f"<b>Total de categorias:</b> {len(categorias)}",
                    estilo_normal
                ),
                Paragraph(
                    f"<b>Total de integrantes:</b> {total_integrantes}",
                    estilo_normal
                ),
                Paragraph(
                    f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    estilo_normal
                )
            ]
        ]

        tabela_info = Table(
            dados_info,
            colWidths=[175, 175, 175]
        )

        tabela_info.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ])
        )

        elementos.append(Spacer(1, 8))
        elementos.append(tabela_info)
        elementos.append(Spacer(1, 10))

        # =====================================================
        # TABELAS POR CATEGORIA
        # =====================================================

        for categoria in categorias.values():

            elementos.append(
                Paragraph(
                    escape(str(categoria["nome"])),
                    estilo_categoria
                )
            )

            dados = [[
                Paragraph("Nº", estilo_cabecalho),
                Paragraph("INTEGRANTE", estilo_cabecalho),
                Paragraph("FUNÇÃO", estilo_cabecalho),
                Paragraph("INSTRUMENTO", estilo_cabecalho)
            ]]

            if categoria["integrantes"]:

                for numero, integrante in enumerate(
                    categoria["integrantes"],
                    start=1
                ):

                    dados.append([
                        Paragraph(str(numero), estilo_celula),
                        Paragraph(
                            escape(str(integrante["integrante_nome"] or "-")),
                            estilo_nome
                        ),
                        Paragraph(
                            escape(str(integrante["funcao"] or "-")),
                            estilo_celula
                        ),
                        Paragraph(
                            escape(str(integrante["instrumento"] or "-")),
                            estilo_celula
                        )
                    ])

            else:

                dados.append([
                    Paragraph("-", estilo_celula),
                    Paragraph("Nenhum integrante cadastrado", estilo_nome),
                    Paragraph("-", estilo_celula),
                    Paragraph("-", estilo_celula)
                ])

            tabela = Table(
                dados,
                colWidths=[30, 220, 125, 150],
                repeatRows=1
            )

            tabela.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E5E5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ])
            )

            elementos.append(tabela)
            elementos.append(Spacer(1, 8))

        # =====================================================
        # RODAPÉ
        # =====================================================

        elementos.append(Spacer(1, 15))

        elementos.append(
            Paragraph(
                "SGI Brilho Negro - Documento gerado automaticamente.",
                ParagraphStyle(
                    "RodapeBN",
                    parent=estilos["Normal"],
                    fontSize=8,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor("#666666")
                )
            )
        )

        documento.build(elementos)

        buffer.seek(0)

        return buffer

    finally:
        db.close()
