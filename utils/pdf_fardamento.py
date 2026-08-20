from io import BytesIO
from datetime import datetime
import os

from flask import send_file
from sqlalchemy import text

from database import SessionLocal

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ============================================================
# CABEÇALHO
# ============================================================

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

    estilo_centralizado = ParagraphStyle(
        "CabecalhoCentralizado",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=12
    )

    elementos.append(
        Paragraph(
            "<b>ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR</b>",
            ParagraphStyle(
                "Associacao",
                parent=estilo_centralizado,
                fontSize=12,
                leading=18
            )
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
                parent=estilo_centralizado,
                fontSize=20,
                leading=24
            )
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            ParagraphStyle(
                "Sistema",
                parent=estilo_centralizado,
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
        Spacer(1, 20)
    )

    elementos.append(
        Paragraph(
            f"<b>{titulo_documento}</b>",
            ParagraphStyle(
                "TituloDocumento",
                parent=estilo_centralizado,
                fontSize=16,
                leading=20
            )
        )
    )

    elementos.append(
        Spacer(1, 20)
    )


# ============================================================
# RODAPÉ / MARCA D'ÁGUA
# ============================================================

def adicionar_rodape(canvas, doc):

    canvas.saveState()

    largura, altura = A4

    # ========================================================
    # MARCA D'ÁGUA
    # ========================================================

    logo_path = os.path.join(
        "static",
        "img",
        "logo_transparente.png"
    )

    if os.path.exists(logo_path):

        try:
            canvas.setFillAlpha(0.10)
        except Exception:
            pass

        largura_logo = 360
        altura_logo = 360

        x = (largura - largura_logo) / 2
        y = (altura - altura_logo) / 2

        canvas.drawImage(
            logo_path,
            x,
            y,
            width=largura_logo,
            height=altura_logo,
            preserveAspectRatio=True,
            mask="auto"
        )

    # ========================================================
    # RODAPÉ
    # ========================================================

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


# ============================================================
# GERAR PDF DO TERMO DE FARDAMENTO
# ============================================================

def gerar_pdf_fardamento(termo_id):

    db = SessionLocal()

    try:

        # ====================================================
        # BUSCAR TERMO
        # ====================================================

        termo = db.execute(
            text("""
                SELECT
                    t.id,
                    t.numero_termo,
                    t.tipo,
                    t.integrante_id,
                    t.temporada_id,
                    t.data_emissao,
                    t.status,
                    t.observacao,

                    i.nome AS integrante_nome,
                    i.codigo_integrante,
                    i.funcao,
                    i.calcado,

                    temp.nome AS temporada_nome,
                    temp.ano AS temporada_ano

                FROM termos t

                INNER JOIN integrantes i
                    ON i.id = t.integrante_id

                LEFT JOIN temporadas temp
                    ON temp.id = t.temporada_id

                WHERE t.id = :termo_id
            """),
            {
                "termo_id": termo_id
            }
        ).mappings().first()

        if not termo:

            return "Termo não encontrado."


        # ====================================================
        # BUSCAR ITENS DO TERMO
        # ====================================================

        itens = db.execute(
            text("""
                SELECT
                    ti.id,
                    ti.tamanho_cadastro,
                    ti.tamanho_entregue,
                    ti.quantidade,
                    ti.estado_entrega,
                    ti.observacao,

                    f.nome AS item_nome,
                    f.tipo AS item_tipo

                FROM termo_itens ti

                INNER JOIN itens_fardamento f
                    ON f.id = ti.item_id

                WHERE ti.termo_id = :termo_id

                ORDER BY
                    f.tipo,
                    f.nome,
                    ti.id
            """),
            {
                "termo_id": termo_id
            }
        ).mappings().all()


        # ====================================================
        # CRIAR PDF
        # ====================================================

        arquivo = BytesIO()

        pdf = SimpleDocTemplate(
            arquivo,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=60
        )

        elementos = []

        estilos = getSampleStyleSheet()


        # ====================================================
        # ESTILOS
        # ====================================================

        estilo_info = ParagraphStyle(
            "Info",
            parent=estilos["Normal"],
            fontSize=10.5,
            leading=17,
            alignment=TA_LEFT
        )

        estilo_pequeno = ParagraphStyle(
            "Pequeno",
            parent=estilos["Normal"],
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT
        )

        estilo_centralizado = ParagraphStyle(
            "Centralizado",
            parent=estilos["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER
        )

        estilo_assinatura = ParagraphStyle(
            "Assinatura",
            parent=estilos["Normal"],
            fontSize=9,
            leading=13,
            alignment=TA_CENTER
        )


        # ====================================================
        # CABEÇALHO
        # ====================================================

        adicionar_cabecalho(
            elementos,
            estilos,
            "TERMO DE ENTREGA DE FARDAMENTO"
        )


        # ====================================================
        # IDENTIFICAÇÃO DO TERMO
        # ====================================================

        elementos.append(
            Paragraph(
                f"<b>Termo:</b> {termo['numero_termo']}",
                estilo_info
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Data de emissão:</b> "
                f"{termo['data_emissao'].strftime('%d/%m/%Y')}",
                estilo_info
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Status:</b> {termo['status']}",
                estilo_info
            )
        )

        elementos.append(
            Spacer(1, 10)
        )


        # ====================================================
        # DADOS DO INTEGRANTE
        # ====================================================

        elementos.append(
            Paragraph(
                "<b>DADOS DO INTEGRANTE</b>",
                estilo_info
            )
        )

        elementos.append(
            Spacer(1, 5)
        )

        dados_integrante = [
            [
                Paragraph(
                    "<b>Nome</b>",
                    estilo_pequeno
                ),
                Paragraph(
                    "<b>Matrícula</b>",
                    estilo_pequeno
                )
            ],
            [
                Paragraph(
                    str(termo["integrante_nome"] or "-"),
                    estilo_pequeno
                ),
                Paragraph(
                    str(termo["codigo_integrante"] or "-"),
                    estilo_pequeno
                )
            ],
            [
                Paragraph(
                    "<b>Função</b>",
                    estilo_pequeno
                ),
                Paragraph(
                    "<b>Calçado cadastrado</b>",
                    estilo_pequeno
                )
            ],
            [
                Paragraph(
                    str(termo["funcao"] or "-"),
                    estilo_pequeno
                ),
                Paragraph(
                    str(termo["calcado"] or "-"),
                    estilo_pequeno
                )
            ]
        ]

        tabela_integrante = Table(
            dados_integrante,
            colWidths=[330, 150]
        )

        tabela_integrante.setStyle(
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
                    colors.whitesmoke
                ),
                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.whitesmoke
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
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
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
            tabela_integrante
        )

        elementos.append(
            Spacer(1, 18)
        )


        # ====================================================
        # TEMPORADA
        # ====================================================

        elementos.append(
            Paragraph(
                "<b>TEMPORADA</b>",
                estilo_info
            )
        )

        temporada_texto = (
            termo["temporada_nome"] or "-"
        )

        if termo["temporada_ano"]:

            temporada_texto += (
                f" — {termo['temporada_ano']}"
            )

        elementos.append(
            Paragraph(
                temporada_texto,
                estilo_info
            )
        )

        elementos.append(
            Spacer(1, 18)
        )


        # ====================================================
        # ITENS ENTREGUES
        # ====================================================

        elementos.append(
            Paragraph(
                "<b>ITENS ENTREGUES</b>",
                estilo_info
            )
        )

        elementos.append(
            Spacer(1, 6)
        )


        dados_itens = [

            [
                Paragraph("<b>Item</b>", estilo_pequeno),
                Paragraph("<b>Tipo</b>", estilo_pequeno),
                Paragraph("<b>Tam. Cad.</b>", estilo_pequeno),
                Paragraph("<b>Tam. Ent.</b>", estilo_pequeno),
                Paragraph("<b>Qtd.</b>", estilo_pequeno),
                Paragraph("<b>Estado</b>", estilo_pequeno)
            ]

        ]


        for item in itens:

            dados_itens.append(

                [
                    Paragraph(
                        str(item["item_nome"] or "-"),
                        estilo_pequeno
                    ),

                    Paragraph(
                        str(item["item_tipo"] or "-"),
                        estilo_pequeno
                    ),

                    Paragraph(
                        str(item["tamanho_cadastro"] or "-"),
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(item["tamanho_entregue"] or "-"),
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(item["quantidade"] or 0),
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(item["estado_entrega"] or "-"),
                        estilo_pequeno
                    )
                ]

            )


        tabela_itens = Table(
            dados_itens,
            colWidths=[
                100,
                80,
                65,
                65,
                45,
                105
            ],
            repeatRows=1
        )


        tabela_itens.setStyle(
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
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (4, -1),
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
            tabela_itens
        )


        # ====================================================
        # OBSERVAÇÕES DOS ITENS
        # ====================================================

        observacoes_itens = [

            item
            for item in itens
            if item["observacao"]
        ]


        if observacoes_itens:

            elementos.append(
                Spacer(1, 12)
            )

            elementos.append(
                Paragraph(
                    "<b>OBSERVAÇÕES DOS ITENS</b>",
                    estilo_info
                )
            )

            elementos.append(
                Spacer(1, 5)
            )

            for item in observacoes_itens:

                elementos.append(
                    Paragraph(
                        f"<b>{item['item_nome']}:</b> "
                        f"{item['observacao']}",
                        estilo_pequeno
                    )
                )


        # ====================================================
        # OBSERVAÇÃO GERAL
        # ====================================================

        if termo["observacao"]:

            elementos.append(
                Spacer(1, 12)
            )

            elementos.append(
                Paragraph(
                    "<b>OBSERVAÇÃO GERAL</b>",
                    estilo_info
                )
            )

            elementos.append(
                Paragraph(
                    str(termo["observacao"]),
                    estilo_pequeno
                )
            )


        # ====================================================
        # DECLARAÇÃO
        # ====================================================

        elementos.append(
            Spacer(1, 20)
        )

        texto_declaracao = """
        Declaro que recebi os itens relacionados neste termo, nas
        quantidades, tamanhos e condições informadas, comprometendo-me
        a zelar pela sua conservação e utilização adequada durante as
        atividades da Associação Cultural de Percussão Rudimentar
        Brilho Negro.
        """

        elementos.append(
            Paragraph(
                texto_declaracao,
                estilo_info
            )
        )


        # ====================================================
        # ASSINATURAS
        # ====================================================

        elementos.append(
            Spacer(1, 55)
        )

        assinaturas = Table(
            [
                [
                    Paragraph(
                        "________________________________",
                        estilo_assinatura
                    ),
                    Paragraph(
                        "________________________________",
                        estilo_assinatura
                    )
                ],
                [
                    Paragraph(
                        "Assinatura do Integrante",
                        estilo_assinatura
                    ),
                    Paragraph(
                        "Responsável pela Entrega",
                        estilo_assinatura
                    )
                ],
                [
                    Paragraph(
                        str(termo["integrante_nome"] or ""),
                        estilo_assinatura
                    ),
                    Paragraph(
                        "",
                        estilo_assinatura
                    )
                ]
            ],
            colWidths=[240, 240]
        )


        assinaturas.setStyle(
            TableStyle([
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
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
                )
            ])
        )


        elementos.append(
            assinaturas
        )


        # ====================================================
        # CONSTRUIR PDF
        # ====================================================

        pdf.build(
            elementos,
            onFirstPage=adicionar_rodape,
            onLaterPages=adicionar_rodape
        )


        arquivo.seek(0)


        # ====================================================
        # NOME DO ARQUIVO
        # ====================================================

        nome_pessoa = str(
            termo["integrante_nome"] or "Integrante"
        )

        nome_pessoa = (
            nome_pessoa
            .replace("/", "-")
            .replace("\\", "-")
            .replace(":", "-")
            .replace("*", "")
            .replace("?", "")
            .replace('"', "")
            .replace("<", "")
            .replace(">", "")
            .replace("|", "")
        )


        nome_arquivo = (
            f"{termo['numero_termo']}_{nome_pessoa}.pdf"
        )


        # ====================================================
        # RETORNAR PDF
        # ====================================================

        return send_file(
            arquivo,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype="application/pdf"
        )


    except Exception as e:

        print(
            "ERRO AO GERAR PDF DO FARDAMENTO:",
            e
        )

        return (
            "Erro ao gerar o PDF do termo.",
            500
        )


    finally:

        db.close()