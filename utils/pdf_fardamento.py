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
    HRFlowable,
    PageBreak
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# ============================================================
# CABEÇALHO
# ============================================================

def adicionar_cabecalho(elementos, estilos, titulo_documento):

    logo_path = os.path.join(
        "static",
        "img",
        "logo_relatorio.PNG"
    )

    estilo_cabecalho = ParagraphStyle(
        "Cabecalho",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=9.5,
        leading=12
    )

    estilo_nome = ParagraphStyle(
        "NomeAssociacao",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=20
    )

    estilo_sistema = ParagraphStyle(
        "Sistema",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=10
    )

    estilo_titulo = ParagraphStyle(
        "TituloDocumento",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=14,
        leading=17,
        spaceBefore=5,
        spaceAfter=4
    )

    # ========================================================
    # LOGO
    # ========================================================

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=245,
            height=60
        )

        logo.hAlign = "CENTER"

        elementos.append(logo)

        elementos.append(
            Spacer(1, 2)
        )

    # ========================================================
    # IDENTIFICAÇÃO DA ASSOCIAÇÃO
    # ========================================================

    elementos.append(
        Paragraph(
            "<b>ASSOCIAÇÃO CULTURAL DE PERCUSSÃO RUDIMENTAR</b>",
            estilo_cabecalho
        )
    )

    elementos.append(
        Paragraph(
            "<b>BRILHO NEGRO</b>",
            estilo_nome
        )
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestão de Integrantes",
            estilo_sistema
        )
    )

    elementos.append(
        Spacer(1, 4)
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.grey
        )
    )

    elementos.append(
        Paragraph(
            f"<b>{titulo_documento}</b>",
            estilo_titulo
        )
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
            canvas.setFillAlpha(0.07)
        except Exception:
            pass

        largura_logo = 300
        altura_logo = 300

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
        35,
        37,
        largura - 35,
        37
    )

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.setFillColor(
        colors.grey
    )

    canvas.drawCentredString(
        largura / 2,
        25,
        "Associação Cultural de Percussão Rudimentar Brilho Negro"
    )

    canvas.drawCentredString(
        largura / 2,
        15,
        f"Documento gerado pelo Sistema de Gestão de Integrantes • "
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
            return "Termo não encontrado.", 404

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
            rightMargin=35,
            leftMargin=35,
            topMargin=25,
            bottomMargin=48
        )

        elementos = []

        estilos = getSampleStyleSheet()

        # ====================================================
        # ESTILOS
        # ====================================================

        estilo_secao = ParagraphStyle(
            "Secao",
            parent=estilos["Normal"],
            fontSize=9.5,
            leading=11,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=4
        )

        estilo_info = ParagraphStyle(
            "Info",
            parent=estilos["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT
        )

        estilo_pequeno = ParagraphStyle(
            "Pequeno",
            parent=estilos["Normal"],
            fontSize=7.7,
            leading=9.5,
            alignment=TA_LEFT
        )

        estilo_centralizado = ParagraphStyle(
            "Centralizado",
            parent=estilos["Normal"],
            fontSize=7.7,
            leading=9.5,
            alignment=TA_CENTER
        )

        # ====================================================
        # CABEÇALHO DE TABELA
        # ====================================================

        estilo_cabecalho_tabela = ParagraphStyle(
            "CabecalhoTabela",
            parent=estilos["Normal"],
            fontSize=7.7,
            leading=9.5,
            alignment=TA_CENTER
        )

        estilo_declaracao = ParagraphStyle(
            "Declaracao",
            parent=estilos["Normal"],
            fontSize=9.8,
            leading=14.5,
            alignment=TA_JUSTIFY,
            firstLineIndent=18,
            spaceAfter=7
        )

        estilo_assinatura = ParagraphStyle(
            "Assinatura",
            parent=estilos["Normal"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER
        )

        # ====================================================
        # DATA
        # ====================================================

        data_emissao = "-"

        if termo["data_emissao"]:

            data_emissao = termo["data_emissao"].strftime(
                "%d/%m/%Y"
            )

        # ====================================================
        # TEMPORADA
        # ====================================================

        temporada_texto = termo["temporada_nome"] or "-"

        if termo["temporada_ano"]:

            temporada_texto += (
                f" — {termo['temporada_ano']}"
            )

        # ====================================================
        # FUNÇÃO PARA MONTAR UMA VIA
        # ====================================================

        def montar_via(tipo_via):

            # =================================================
            # CABEÇALHO
            # =================================================

            adicionar_cabecalho(
                elementos,
                estilos,
                "TERMO DE ENTREGA E RESPONSABILIDADE DE FARDAMENTO"
            )

            elementos.append(
                Paragraph(
                    f"<b>{tipo_via}</b>",
                    estilo_cabecalho_tabela
                )
            )

            elementos.append(
                Spacer(1, 5)
            )

            # =================================================
            # IDENTIFICAÇÃO DO TERMO
            # =================================================

            dados_termo = [
                [
                    Paragraph(
                        "<b>TERMO Nº</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>DATA DE EMISSÃO</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>STATUS</b>",
                        estilo_cabecalho_tabela
                    )
                ],
                [
                    Paragraph(
                        str(termo["numero_termo"] or "-"),
                        estilo_centralizado
                    ),
                    Paragraph(
                        data_emissao,
                        estilo_centralizado
                    ),
                    Paragraph(
                        str(termo["status"] or "-"),
                        estilo_centralizado
                    )
                ]
            ]

            tabela_termo = Table(
                dados_termo,
                colWidths=[170, 170, 140]
            )

            tabela_termo.setStyle(
                TableStyle([
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
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
                        3
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3
                    )
                ])
            )

            elementos.append(
                tabela_termo
            )

            elementos.append(
                Spacer(1, 7)
            )

            # =================================================
            # TEMPORADA
            # =================================================

            dados_temporada = [
                [
                    Paragraph(
                        "<b>TEMPORADA</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        temporada_texto,
                        estilo_centralizado
                    )
                ]
            ]

            tabela_temporada = Table(
                dados_temporada,
                colWidths=[100, 380]
            )

            tabela_temporada.setStyle(
                TableStyle([
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
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
                        3
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3
                    )
                ])
            )

            elementos.append(
                tabela_temporada
            )

            elementos.append(
                Spacer(1, 8)
            )

            # =================================================
            # DADOS DO INTEGRANTE
            # =================================================

            elementos.append(
                Paragraph(
                    "<b>DADOS DO INTEGRANTE</b>",
                    estilo_secao
                )
            )

            dados_integrante = [
                [
                    Paragraph(
                        "<b>Nome</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Matrícula</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Função</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Calçado cadastrado</b>",
                        estilo_cabecalho_tabela
                    )
                ],
                [
                    Paragraph(
                        str(termo["integrante_nome"] or "-"),
                        estilo_centralizado
                    ),
                    Paragraph(
                        str(termo["codigo_integrante"] or "-"),
                        estilo_centralizado
                    ),
                    Paragraph(
                        str(termo["funcao"] or "-"),
                        estilo_centralizado
                    ),
                    Paragraph(
                        str(termo["calcado"] or "-"),
                        estilo_centralizado
                    )
                ]
            ]

            tabela_integrante = Table(
                dados_integrante,
                colWidths=[210, 65, 120, 85]
            )

            tabela_integrante.setStyle(
                TableStyle([
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
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
                        4
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4
                    )
                ])
            )

            elementos.append(
                tabela_integrante
            )

            elementos.append(
                Spacer(1, 9)
            )

            # =================================================
            # ITENS ENTREGUES
            # =================================================

            elementos.append(
                Paragraph(
                    "<b>ITENS ENTREGUES</b>",
                    estilo_secao
                )
            )

            dados_itens = [
                [
                    Paragraph(
                        "<b>Item</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Categoria</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Tam. Cad.</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Tam. Ent.</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Qtd.</b>",
                        estilo_cabecalho_tabela
                    ),
                    Paragraph(
                        "<b>Condição na Entrega</b>",
                        estilo_cabecalho_tabela
                    )
                ]
            ]

            for item in itens:

                dados_itens.append(
                    [
                        Paragraph(
                            str(item["item_nome"] or "-"),
                            estilo_centralizado
                        ),
                        Paragraph(
                            str(item["item_tipo"] or "-"),
                            estilo_centralizado
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
                            estilo_centralizado
                        )
                    ]
                )

            if not itens:

                dados_itens.append(
                    [
                        Paragraph(
                            "Nenhum item registrado neste termo.",
                            estilo_pequeno
                        ),
                        "",
                        "",
                        "",
                        "",
                        ""
                    ]
                )

            tabela_itens = Table(
                dados_itens,
                colWidths=[
                    105,
                    80,
                    60,
                    60,
                    45,
                    130
                ],
                repeatRows=1
            )

            tabela_itens.setStyle(
                TableStyle([
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
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
                        3
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3
                    )
                ])
            )

            if not itens:

                tabela_itens.setStyle(
                    TableStyle([
                        (
                            "SPAN",
                            (0, 1),
                            (5, 1)
                        ),
                        (
                            "ALIGN",
                            (0, 1),
                            (5, 1),
                            "CENTER"
                        )
                    ])
                )

            elementos.append(
                tabela_itens
            )

            # =================================================
            # OBSERVAÇÕES DOS ITENS
            # =================================================

            observacoes_itens = [
                item
                for item in itens
                if item["observacao"]
            ]

            if observacoes_itens:

                elementos.append(
                    Spacer(1, 6)
                )

                elementos.append(
                    Paragraph(
                        "<b>OBSERVAÇÕES DOS ITENS</b>",
                        estilo_secao
                    )
                )

                for item in observacoes_itens:

                    elementos.append(
                        Paragraph(
                            f"<b>{item['item_nome']}:</b> "
                            f"{item['observacao']}",
                            estilo_pequeno
                        )
                    )

            # =================================================
            # OBSERVAÇÃO GERAL
            # =================================================

            if termo["observacao"]:

                elementos.append(
                    Spacer(1, 6)
                )

                elementos.append(
                    Paragraph(
                        "<b>OBSERVAÇÃO GERAL</b>",
                        estilo_secao
                    )
                )

                elementos.append(
                    Paragraph(
                        str(termo["observacao"]),
                        estilo_pequeno
                    )
                )

            # =================================================
            # DECLARAÇÃO
            # =================================================

            elementos.append(
                Spacer(1, 9)
            )

            elementos.append(
                Paragraph(
                    "<b>DECLARAÇÃO DE RECEBIMENTO E RESPONSABILIDADE</b>",
                    estilo_secao
                )
            )

            textos_declaracao = [

                """
                Declaro, para os devidos fins, que recebi os itens relacionados neste
                termo, nas respectivas quantidades, tamanhos e condições nele
                informadas, passando a mantê-los sob minha guarda e responsabilidade
                enquanto permanecerem em minha posse.
                """,

                """
                Declaro estar ciente de que os itens recebidos pertencem ou estão sob
                controle da Associação Cultural de Percussão Rudimentar Brilho Negro
                e destinam-se ao uso nas atividades oficiais da Associação, tais como
                ensaios, apresentações, eventos, deslocamentos e demais atividades
                relacionadas à sua finalidade.
                """,

                """
                Comprometo-me a utilizar os itens de maneira adequada, compatível com
                sua finalidade, preservando suas condições de uso e conservação durante
                o período em que estiverem sob minha guarda. Estou ciente de que o
                desgaste natural decorrente do uso regular e adequado não caracteriza,
                por si só, irregularidade.
                """,

                """
                Os itens poderão permanecer sob minha guarda durante toda a temporada
                e nos intervalos entre ensaios, apresentações e demais atividades,
                não sendo necessária sua devolução após cada utilização. A devolução
                será realizada quando solicitada pela Associação, ao término da
                temporada, em caso de substituição ou troca do material, desligamento
                do integrante ou em qualquer outra situação que justifique o
                recolhimento ou a atualização do controle patrimonial e de estoque.
                """,

                """
                Declaro, ainda, estar ciente de que qualquer perda, extravio, dano
                anormal ou outra ocorrência que comprometa a utilização dos itens
                deverá ser comunicada à Associação tão logo seja identificada,
                permitindo o devido registro e avaliação da situação.
                """,

                """
                Por fim, reconheço que este termo constitui o registro formal da
                entrega dos itens nele relacionados e da respectiva responsabilidade
                pela guarda enquanto permanecerem sob minha posse, devendo os materiais
                ser apresentados ou devolvidos sempre que solicitado pela Associação.
                """
            ]

            for texto in textos_declaracao:

                elementos.append(
                    Paragraph(
                        texto,
                        estilo_declaracao
                    )
                )

            # =================================================
            # ASSINATURAS
            # =================================================

            elementos.append(
                Spacer(1, 20)
            )

            assinaturas = Table(
                [
                    [
                        Paragraph(
                            "__________________________________",
                            estilo_assinatura
                        ),
                        Paragraph(
                            "__________________________________",
                            estilo_assinatura
                        )
                    ],
                    [
                        Paragraph(
                            "<b>Assinatura do Integrante</b>",
                            estilo_assinatura
                        ),
                        Paragraph(
                            "<b>Responsável pela Entrega</b>",
                            estilo_assinatura
                        )
                    ],
                    [
                        Paragraph(
                            str(
                                termo["integrante_nome"] or ""
                            ),
                            estilo_assinatura
                        ),
                        Paragraph(
                            "Centro Educacional Fonte do Saber",
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
                        2
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2
                    )
                ])
            )

            elementos.append(
                assinaturas
            )

        # ====================================================
        # VIA 1
        # ====================================================

        montar_via(
            "VIA DA ASSOCIAÇÃO"
        )

        # ====================================================
        # NOVA PÁGINA
        # ====================================================

        elementos.append(
            PageBreak()
        )

        # ====================================================
        # VIA 2
        # ====================================================

        montar_via(
            "VIA DO INTEGRANTE"
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

# ============================================================
# GERAR PDF DE TODOS OS TERMOS DE FARDAMENTO
# ============================================================

def gerar_pdf_todos_fardamentos():

    db = SessionLocal()

    try:

        # ====================================================
        # BUSCAR TODOS OS TERMOS DE ENTREGA
        # ====================================================

        termos = db.execute(
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

                WHERE t.tipo = 'ENTREGA'

                ORDER BY
                    t.id DESC
            """)
        ).mappings().all()


        # ====================================================
        # VERIFICAR SE EXISTEM TERMOS
        # ====================================================

        if not termos:

            return (
                "Nenhum termo de entrega de fardamento "
                "foi encontrado.",
                404
            )


        # ====================================================
        # CRIAR PDF
        # ====================================================

        arquivo = BytesIO()

        pdf = SimpleDocTemplate(
            arquivo,
            pagesize=A4,
            rightMargin=35,
            leftMargin=35,
            topMargin=25,
            bottomMargin=48
        )

        elementos = []

        estilos = getSampleStyleSheet()


        # ====================================================
        # ESTILOS
        # ====================================================

        estilo_secao = ParagraphStyle(
            "SecaoTodos",
            parent=estilos["Normal"],
            fontSize=9.5,
            leading=11,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=4
        )


        estilo_pequeno = ParagraphStyle(
            "PequenoTodos",
            parent=estilos["Normal"],
            fontSize=7.7,
            leading=9.5,
            alignment=TA_LEFT
        )


        estilo_centralizado = ParagraphStyle(
            "CentralizadoTodos",
            parent=estilos["Normal"],
            fontSize=7.7,
            leading=9.5,
            alignment=TA_CENTER
        )


        estilo_cabecalho_tabela = ParagraphStyle(
            "CabecalhoTabelaTodos",
            parent=estilos["Normal"],
            fontSize=7.7,
            leading=9.5,
            alignment=TA_CENTER
        )


        estilo_declaracao = ParagraphStyle(
            "DeclaracaoTodos",
            parent=estilos["Normal"],
            fontSize=9.8,
            leading=14.5,
            alignment=TA_JUSTIFY,
            firstLineIndent=18,
            spaceAfter=7
        )


        estilo_assinatura = ParagraphStyle(
            "AssinaturaTodos",
            parent=estilos["Normal"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER
        )


        # ====================================================
        # FUNÇÃO PARA MONTAR UMA VIA
        # ====================================================

        def montar_via(termo, itens, tipo_via):


            # =================================================
            # CABEÇALHO
            # =================================================

            adicionar_cabecalho(
                elementos,
                estilos,
                "TERMO DE ENTREGA E RESPONSABILIDADE DE FARDAMENTO"
            )


            elementos.append(
                Paragraph(
                    f"<b>{tipo_via}</b>",
                    estilo_cabecalho_tabela
                )
            )


            elementos.append(
                Spacer(1, 5)
            )


            # =================================================
            # DATA
            # =================================================

            data_emissao = "-"

            if termo["data_emissao"]:

                data_emissao = termo["data_emissao"].strftime(
                    "%d/%m/%Y"
                )


            # =================================================
            # IDENTIFICAÇÃO DO TERMO
            # =================================================

            dados_termo = [

                [

                    Paragraph(
                        "<b>TERMO Nº</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>DATA DE EMISSÃO</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>STATUS</b>",
                        estilo_cabecalho_tabela
                    )

                ],

                [

                    Paragraph(
                        str(
                            termo["numero_termo"] or "-"
                        ),
                        estilo_centralizado
                    ),

                    Paragraph(
                        data_emissao,
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(
                            termo["status"] or "-"
                        ),
                        estilo_centralizado
                    )

                ]

            ]


            tabela_termo = Table(
                dados_termo,
                colWidths=[
                    170,
                    170,
                    140
                ]
            )


            tabela_termo.setStyle(
                TableStyle([

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
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
                        3
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3
                    )

                ])
            )


            elementos.append(
                tabela_termo
            )


            elementos.append(
                Spacer(1, 7)
            )


            # =================================================
            # TEMPORADA
            # =================================================

            temporada_texto = (
                termo["temporada_nome"] or "-"
            )

            if termo["temporada_ano"]:

                temporada_texto += (
                    f" — {termo['temporada_ano']}"
                )


            dados_temporada = [

                [

                    Paragraph(
                        "<b>TEMPORADA</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        temporada_texto,
                        estilo_centralizado
                    )

                ]

            ]


            tabela_temporada = Table(
                dados_temporada,
                colWidths=[
                    100,
                    380
                ]
            )


            tabela_temporada.setStyle(
                TableStyle([

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey
                    ),

                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
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
                        3
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3
                    )

                ])
            )


            elementos.append(
                tabela_temporada
            )


            elementos.append(
                Spacer(1, 8)
            )


            # =================================================
            # DADOS DO INTEGRANTE
            # =================================================

            elementos.append(
                Paragraph(
                    "<b>DADOS DO INTEGRANTE</b>",
                    estilo_secao
                )
            )


            dados_integrante = [

                [

                    Paragraph(
                        "<b>Nome</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Matrícula</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Função</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Calçado cadastrado</b>",
                        estilo_cabecalho_tabela
                    )

                ],

                [

                    Paragraph(
                        str(
                            termo["integrante_nome"] or "-"
                        ),
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(
                            termo["codigo_integrante"] or "-"
                        ),
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(
                            termo["funcao"] or "-"
                        ),
                        estilo_centralizado
                    ),

                    Paragraph(
                        str(
                            termo["calcado"] or "-"
                        ),
                        estilo_centralizado
                    )

                ]

            ]


            tabela_integrante = Table(
                dados_integrante,
                colWidths=[
                    210,
                    65,
                    120,
                    85
                ]
            )


            tabela_integrante.setStyle(
                TableStyle([

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
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
                        4
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4
                    )

                ])
            )


            elementos.append(
                tabela_integrante
            )


            elementos.append(
                Spacer(1, 9)
            )


            # =================================================
            # ITENS ENTREGUES
            # =================================================

            elementos.append(
                Paragraph(
                    "<b>ITENS ENTREGUES</b>",
                    estilo_secao
                )
            )


            dados_itens = [

                [

                    Paragraph(
                        "<b>Item</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Categoria</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Tam. Cad.</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Tam. Ent.</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Qtd.</b>",
                        estilo_cabecalho_tabela
                    ),

                    Paragraph(
                        "<b>Condição na Entrega</b>",
                        estilo_cabecalho_tabela
                    )

                ]

            ]


            for item in itens:

                dados_itens.append(

                    [

                        Paragraph(
                            str(
                                item["item_nome"] or "-"
                            ),
                            estilo_centralizado
                        ),

                        Paragraph(
                            str(
                                item["item_tipo"] or "-"
                            ),
                            estilo_centralizado
                        ),

                        Paragraph(
                            str(
                                item["tamanho_cadastro"] or "-"
                            ),
                            estilo_centralizado
                        ),

                        Paragraph(
                            str(
                                item["tamanho_entregue"] or "-"
                            ),
                            estilo_centralizado
                        ),

                        Paragraph(
                            str(
                                item["quantidade"] or 0
                            ),
                            estilo_centralizado
                        ),

                        Paragraph(
                            str(
                                item["estado_entrega"] or "-"
                            ),
                            estilo_centralizado
                        )

                    ]

                )


            if not itens:

                dados_itens.append(

                    [

                        Paragraph(
                            "Nenhum item registrado neste termo.",
                            estilo_pequeno
                        ),

                        "",

                        "",

                        "",

                        "",

                        ""

                    ]

                )


            tabela_itens = Table(
                dados_itens,
                colWidths=[
                    105,
                    80,
                    60,
                    60,
                    45,
                    130
                ],
                repeatRows=1
            )


            tabela_itens.setStyle(
                TableStyle([

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
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
                        3
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3
                    )

                ])
            )


            if not itens:

                tabela_itens.setStyle(
                    TableStyle([

                        (
                            "SPAN",
                            (0, 1),
                            (5, 1)
                        ),

                        (
                            "ALIGN",
                            (0, 1),
                            (5, 1),
                            "CENTER"
                        )

                    ])
                )


            elementos.append(
                tabela_itens
            )


            # =================================================
            # OBSERVAÇÕES DOS ITENS
            # =================================================

            observacoes_itens = [

                item
                for item in itens
                if item["observacao"]

            ]


            if observacoes_itens:

                elementos.append(
                    Spacer(1, 6)
                )

                elementos.append(
                    Paragraph(
                        "<b>OBSERVAÇÕES DOS ITENS</b>",
                        estilo_secao
                    )
                )


                for item in observacoes_itens:

                    elementos.append(
                        Paragraph(

                            f"<b>{item['item_nome']}:</b> "
                            f"{item['observacao']}",

                            estilo_pequeno

                        )
                    )


            # =================================================
            # OBSERVAÇÃO GERAL
            # =================================================

            if termo["observacao"]:

                elementos.append(
                    Spacer(1, 6)
                )

                elementos.append(
                    Paragraph(
                        "<b>OBSERVAÇÃO GERAL</b>",
                        estilo_secao
                    )
                )

                elementos.append(
                    Paragraph(
                        str(
                            termo["observacao"]
                        ),
                        estilo_pequeno
                    )
                )


            # =================================================
            # DECLARAÇÃO
            # =================================================

            elementos.append(
                Spacer(1, 9)
            )


            elementos.append(
                Paragraph(
                    "<b>DECLARAÇÃO DE RECEBIMENTO E RESPONSABILIDADE</b>",
                    estilo_secao
                )
            )


            textos_declaracao = [

                """
                Declaro, para os devidos fins, que recebi os itens relacionados neste
                termo, nas respectivas quantidades, tamanhos e condições nele
                informadas, passando a mantê-los sob minha guarda e responsabilidade
                enquanto permanecerem em minha posse.
                """,

                """
                Declaro estar ciente de que os itens recebidos pertencem ou estão sob
                controle da Associação Cultural de Percussão Rudimentar Brilho Negro
                e destinam-se ao uso nas atividades oficiais da Associação, tais como
                ensaios, apresentações, eventos, deslocamentos e demais atividades
                relacionadas à sua finalidade.
                """,

                """
                Comprometo-me a utilizar os itens de maneira adequada, compatível com
                sua finalidade, preservando suas condições de uso e conservação durante
                o período em que estiverem sob minha guarda. Estou ciente de que o
                desgaste natural decorrente do uso regular e adequado não caracteriza,
                por si só, irregularidade.
                """,

                """
                Os itens poderão permanecer sob minha guarda durante toda a temporada
                e nos intervalos entre ensaios, apresentações e demais atividades,
                não sendo necessária sua devolução após cada utilização. A devolução
                será realizada quando solicitada pela Associação, ao término da
                temporada, em caso de substituição ou troca do material, desligamento
                do integrante ou em qualquer outra situação que justifique o
                recolhimento ou a atualização do controle patrimonial e de estoque.
                """,

                """
                Declaro, ainda, estar ciente de que qualquer perda, extravio, dano
                anormal ou outra ocorrência que comprometa a utilização dos itens
                deverá ser comunicada à Associação tão logo seja identificada,
                permitindo o devido registro e avaliação da situação.
                """,

                """
                Por fim, reconheço que este termo constitui o registro formal da
                entrega dos itens nele relacionados e da respectiva responsabilidade
                pela guarda enquanto permanecerem sob minha posse, devendo os materiais
                ser apresentados ou devolvidos sempre que solicitado pela Associação.
                """

            ]


            for texto in textos_declaracao:

                elementos.append(
                    Paragraph(
                        texto,
                        estilo_declaracao
                    )
                )


            # =================================================
            # ASSINATURAS
            # =================================================

            elementos.append(
                Spacer(1, 20)
            )


            assinaturas = Table(

                [

                    [

                        Paragraph(
                            "__________________________________",
                            estilo_assinatura
                        ),

                        Paragraph(
                            "__________________________________",
                            estilo_assinatura
                        )

                    ],

                    [

                        Paragraph(
                            "<b>Assinatura do Integrante</b>",
                            estilo_assinatura
                        ),

                        Paragraph(
                            "<b>Responsável pela Entrega</b>",
                            estilo_assinatura
                        )

                    ],

                    [

                        Paragraph(
                            str(
                                termo["integrante_nome"] or ""
                            ),
                            estilo_assinatura
                        ),

                        Paragraph(
                            "Centro Educacional Fonte do Saber",
                            estilo_assinatura
                        )

                    ]

                ],

                colWidths=[
                    240,
                    240
                ]

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
                        2
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2
                    )

                ])
            )


            elementos.append(
                assinaturas
            )


        # ====================================================
        # MONTAR TODOS OS TERMOS
        # ====================================================

        for indice, termo in enumerate(termos):

            # =================================================
            # BUSCAR ITENS DO TERMO
            # =================================================

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
                    "termo_id": termo["id"]
                }
            ).mappings().all()


            # =================================================
            # VIA DA ASSOCIAÇÃO
            # =================================================

            montar_via(
                termo,
                itens,
                "VIA DA ASSOCIAÇÃO"
            )


            # =================================================
            # VIA DO INTEGRANTE
            # =================================================

            elementos.append(
                PageBreak()
            )


            montar_via(
                termo,
                itens,
                "VIA DO INTEGRANTE"
            )


            # =================================================
            # SE NÃO FOR O ÚLTIMO TERMO
            # =================================================

            if indice < len(termos) - 1:

                elementos.append(
                    PageBreak()
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

        nome_arquivo = (
            f"Todos_Termos_Fardamento_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
            "ERRO AO GERAR PDF DE TODOS OS TERMOS DE FARDAMENTO:",
            e
        )

        return (
            "Erro ao gerar o PDF de todos os termos.",
            500
        )


    finally:

        db.close()        