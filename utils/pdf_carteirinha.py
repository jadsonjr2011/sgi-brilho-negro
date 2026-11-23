
from io import BytesIO
from datetime import datetime
import os
import re
import requests

from PIL import Image as PILImage, ImageDraw, ImageOps

from flask import send_file

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from sqlalchemy import text
from database import SessionLocal


# ==========================================================
# IDENTIDADE VISUAL
# ==========================================================

AZUL_BN = colors.HexColor("#0b1522")
AZUL_CLARO_BN = colors.HexColor("#eaf0f5")
CINZA_BN = colors.HexColor("#667085")
CINZA_LINHA_BN = colors.HexColor("#dce2e8")
BRANCO_BN = colors.white


# ==========================================================
# CONFIGURAÇÃO DAS CARTEIRINHAS
# ==========================================================

CARD_W = 245
CARD_H = 154

CARD_RAIO = 10

HEADER_H = 40

FOTO_TAMANHO = 62

LOGO_PATH = os.path.join(
    "static",
    "img",
    "logo_relatorio.PNG"
)


# ==========================================================
# IMAGENS
# ==========================================================

def criar_banner_arredondado(
    caminho_original,
    caminho_saida,
    largura=900,
    altura=250
):

    imagem = PILImage.open(
        caminho_original
    ).convert("RGBA")

    imagem = ImageOps.fit(
        imagem,
        (largura, altura),
        method=PILImage.Resampling.LANCZOS
    )

    mascara = PILImage.new(
        "L",
        (largura, altura),
        0
    )

    desenho = ImageDraw.Draw(mascara)

    desenho.rounded_rectangle(
        (0, 0, largura - 1, altura - 1),
        radius=60,
        fill=255
    )

    imagem.putalpha(mascara)

    imagem.save(caminho_saida, format="PNG")


def criar_foto_arredondada(
    caminho_original,
    caminho_saida,
    tamanho=300
):

    imagem = PILImage.open(
        caminho_original
    ).convert("RGBA")

    largura, altura = imagem.size

    menor = min(largura, altura)

    esquerda = (largura - menor) // 2
    cima = (altura - menor) // 2

    imagem = imagem.crop(
        (
            esquerda,
            cima,
            esquerda + menor,
            cima + menor
        )
    )

    imagem = imagem.resize(
        (tamanho, tamanho),
        PILImage.Resampling.LANCZOS
    )

    mascara = PILImage.new(
        "L",
        (tamanho, tamanho),
        0
    )

    desenho = ImageDraw.Draw(mascara)

    desenho.rounded_rectangle(
        (0, 0, tamanho - 1, tamanho - 1),
        radius=45,
        fill=255
    )

    imagem.putalpha(mascara)

    imagem.save(caminho_saida, format="PNG")


def baixar_imagem(url, nome):

    try:

        resposta = requests.get(
            url,
            timeout=10
        )

        resposta.raise_for_status()

        imagem = PILImage.open(
            BytesIO(resposta.content)
        )

        imagem.verify()

        with open(nome, "wb") as arquivo:

            arquivo.write(
                resposta.content
            )

        return nome

    except Exception as e:

        print("Erro imagem:", e)

        return None


def carregar_imagem_url(url):

    if not url:
        return None

    try:

        resposta = requests.get(
            url,
            timeout=10
        )

        resposta.raise_for_status()

        imagem = PILImage.open(
            BytesIO(resposta.content)
        ).convert("RGBA")

        return imagem

    except Exception as e:

        print("Erro ao carregar foto:", e)

        return None


def imagem_arredondada_memoria(
    imagem,
    largura,
    altura,
    raio=12
):

    imagem = ImageOps.fit(
        imagem.convert("RGBA"),
        (largura, altura),
        method=PILImage.Resampling.LANCZOS
    )

    mascara = PILImage.new(
        "L",
        (largura, altura),
        0
    )

    desenho = ImageDraw.Draw(mascara)

    desenho.rounded_rectangle(
        (0, 0, largura - 1, altura - 1),
        radius=raio,
        fill=255
    )

    imagem.putalpha(mascara)

    arquivo = BytesIO()

    imagem.save(
        arquivo,
        format="PNG"
    )

    arquivo.seek(0)

    return ImageReader(arquivo)


# ==========================================================
# QUEBRA DE TEXTO
# ==========================================================

def quebrar_nome(nome, limite=28):

    palavras = str(nome or "").upper().split()

    linhas = []

    linha = ""

    for palavra in palavras:

        teste = (linha + " " + palavra).strip()

        if len(teste) <= limite:

            linha = teste

        else:

            if linha:
                linhas.append(linha)

            linha = palavra

    if linha:
        linhas.append(linha)

    return linhas


def quebrar_texto_largura(
    texto,
    fonte,
    tamanho,
    largura_maxima
):

    palavras = str(texto or "").upper().split()

    linhas = []

    linha = ""

    for palavra in palavras:

        teste = (linha + " " + palavra).strip()

        largura = stringWidth(
            teste,
            fonte,
            tamanho
        )

        if largura <= largura_maxima:

            linha = teste

        else:

            if linha:
                linhas.append(linha)

            linha = palavra

    if linha:
        linhas.append(linha)

    return linhas


def ajustar_nome(
    pdf,
    nome,
    largura_maxima,
    max_linhas=2
):

    fonte = "Helvetica-Bold"

    for tamanho in (12, 11, 10, 9, 8, 7):

        linhas = quebrar_texto_largura(
            nome,
            fonte,
            tamanho,
            largura_maxima
        )

        if len(linhas) <= max_linhas:

            return fonte, tamanho, linhas

    # Último recurso para nomes muito extensos.

    tamanho = 7

    palavras = str(nome or "").upper().split()

    texto = ""

    for palavra in palavras:

        teste = (texto + " " + palavra).strip()

        if stringWidth(
            teste,
            fonte,
            tamanho
        ) <= largura_maxima:

            texto = teste

        else:

            break

    return fonte, tamanho, [texto or "INTEGRANTE"]


# ==========================================================
# DESENHO DA FOTO
# ==========================================================

def desenhar_foto(
    pdf,
    integrante,
    x,
    y
):

    foto = carregar_imagem_url(
        integrante.get("foto_url")
    )

    foto_x = x + 17
    foto_y = y + 43

    # Moldura externa.

    pdf.setFillColor(
        AZUL_CLARO_BN
    )

    pdf.roundRect(
        foto_x - 3,
        foto_y - 3,
        FOTO_TAMANHO + 6,
        FOTO_TAMANHO + 6,
        9,
        fill=1,
        stroke=0
    )

    if foto:

        foto_reader = imagem_arredondada_memoria(
            foto,
            400,
            400,
            raio=45
        )

        pdf.drawImage(
            foto_reader,
            foto_x,
            foto_y,
            width=FOTO_TAMANHO,
            height=FOTO_TAMANHO,
            mask="auto"
        )

    else:

        # Identificação visual quando não existe foto.

        pdf.setFillColor(
            AZUL_CLARO_BN
        )

        pdf.roundRect(
            foto_x,
            foto_y,
            FOTO_TAMANHO,
            FOTO_TAMANHO,
            7,
            fill=1,
            stroke=0
        )

        pdf.setFillColor(
            AZUL_BN
        )

        pdf.setFont(
            "Helvetica-Bold",
            9
        )

        pdf.drawCentredString(
            foto_x + FOTO_TAMANHO / 2,
            foto_y + FOTO_TAMANHO / 2 - 3,
            "SEM FOTO"
        )



# ==========================================================
# DESENHO DO NOME E MATRÍCULA
# ==========================================================

def desenhar_informacoes(
    pdf,
    integrante,
    x,
    y
):

    info_x = x + 98

    info_largura = CARD_W - 115

    # IDENTIFICAÇÃO DO CAMPO

    pdf.setFillColor(CINZA_BN)

    pdf.setFont(
        "Helvetica-Bold",
        6.5
    )

    pdf.drawString(
        info_x,
        y + 104,
        "NOME DO INTEGRANTE"
    )

    # NOME DO INTEGRANTE

    nome = integrante.get("nome") or "INTEGRANTE"

    fonte, tamanho, linhas = ajustar_nome(
        pdf,
        nome,
        info_largura,
        max_linhas=2
    )

    pdf.setFillColor(AZUL_BN)

    pdf.setFont(
        fonte,
        tamanho
    )

    pos_y = y + 88

    for linha in linhas:

        pdf.drawString(
            info_x,
            pos_y,
            linha
        )

        pos_y -= tamanho + 3

    # DIVISÓRIA

    pdf.setStrokeColor(CINZA_LINHA_BN)

    pdf.setLineWidth(0.7)

    pdf.line(
        info_x,
        y + 65,
        x + CARD_W - 17,
        y + 65
    )

    # IDENTIFICAÇÃO DA MATRÍCULA

    pdf.setFillColor(CINZA_BN)

    pdf.setFont(
        "Helvetica",
        7
    )

    pdf.drawString(
        info_x,
        y + 52,
        "MATRÍCULA"
    )

    # CÓDIGO

    codigo = str(
        integrante.get("codigo_integrante") or "-"
    ).strip()

    tamanho_codigo = 10

    while tamanho_codigo > 7 and stringWidth(
        codigo,
        "Helvetica-Bold",
        tamanho_codigo
    ) > info_largura:

        tamanho_codigo -= 0.5

    pdf.setFillColor(AZUL_BN)

    pdf.setFont(
        "Helvetica-Bold",
        tamanho_codigo
    )

    pdf.drawString(
        info_x,
        y + 38,
        codigo
    )


# ==========================================================
# DESENHO DA CARTEIRINHA
# ==========================================================

def desenhar_carteirinha(
    pdf,
    integrante,
    x,
    y,
    data_emissao=None,
    logo_reader=None
):

    # ==========================================
    # FUNDO
    # ==========================================

    pdf.setFillColor(
        BRANCO_BN
    )

    pdf.roundRect(
        x,
        y,
        CARD_W,
        CARD_H,
        CARD_RAIO,
        fill=1,
        stroke=0
    )

    # ==========================================
    # BORDA EXTERNA
    # ==========================================

    pdf.setStrokeColor(AZUL_BN)
    pdf.setLineWidth(2)

    pdf.roundRect(
        x + 1,
        y + 1,
        CARD_W - 2,
        CARD_H - 2,
        CARD_RAIO,
        fill=0,
        stroke=1
    )

    # ==========================================
    # CABEÇALHO
    # ==========================================

    header_y = y + CARD_H - HEADER_H - 1.5

    if logo_reader:

        pdf.drawImage(
            logo_reader,
            x + 2,
            header_y,
            width=CARD_W - 4,
            height=HEADER_H,
            mask="auto"
        )

    else:

        pdf.setFillColor(AZUL_BN)

        pdf.roundRect(
            x + 2,
            header_y,
            CARD_W - 4,
            HEADER_H,
            8,
            fill=1,
            stroke=0
        )

    # ==========================================
    # FOTO
    # ==========================================

    desenhar_foto(
        pdf,
        integrante,
        x,
        y
    )

    # ==========================================
    # INFORMAÇÕES
    # ==========================================

    desenhar_informacoes(
        pdf,
        integrante,
        x,
        y
    )

    # ==========================================
    # DIVISÓRIA DO RODAPÉ
    # ==========================================

    pdf.setStrokeColor(
        CINZA_LINHA_BN
    )

    pdf.setLineWidth(0.7)

    pdf.line(
        x + 13,
        y + 32,
        x + CARD_W - 13,
        y + 32
    )

    # ==========================================
    # RODAPÉ
    # ==========================================

    pdf.setFillColor(
        AZUL_BN
    )

    pdf.setFont(
        "Helvetica-Bold",
        7
    )

    pdf.drawString(
        x + 15,
        y + 17,
        "CARTEIRINHA DE INTEGRANTE"
    )

    pdf.setFillColor(
        CINZA_BN
    )

    pdf.setFont(
        "Helvetica",
        7
    )

    data = data_emissao or datetime.now()

    pdf.drawRightString(
        x + CARD_W - 15,
        y + 17,
        data.strftime("%d/%m/%Y")
    )


# ==========================================================
# PREPARAÇÃO DO LOGO
# ==========================================================

def carregar_logo():

    if not os.path.exists(LOGO_PATH):
        return None

    try:

        imagem = PILImage.open(
            LOGO_PATH
        ).convert("RGBA")

        imagem = imagem_arredondada_para_banner(
            imagem,
            1000,
            180
        )

        arquivo = BytesIO()

        imagem.save(
            arquivo,
            format="PNG"
        )

        arquivo.seek(0)

        return ImageReader(arquivo)

    except Exception as e:

        print("Erro ao carregar logo:", e)

        return None



def imagem_arredondada_para_banner(
    imagem,
    largura,
    altura
):

    imagem = ImageOps.fit(
        imagem,
        (largura, altura),
        method=PILImage.Resampling.LANCZOS
    )

    mascara = PILImage.new(
        "L",
        (largura, altura),
        0
    )

    desenho = ImageDraw.Draw(mascara)

    # Arredonda somente os cantos superiores.
    desenho.rounded_rectangle(
        (0, 0, largura - 1, altura + 40),
        radius=40,
        fill=255
    )

    # Mantém toda a parte inferior reta.
    desenho.rectangle(
        (0, altura // 2, largura, altura),
        fill=255
    )

    imagem.putalpha(mascara)

    return imagem



# ==========================================================
# GERAÇÃO DO PDF INDIVIDUAL
# ==========================================================

def gerar_pdf_carteirinha(id):

    db = SessionLocal()

    try:

        integrante = db.execute(
            text("""
                SELECT
                    id,
                    codigo_integrante,
                    nome,
                    foto_url
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()

        if not integrante:

            return "Integrante não encontrado"

        integrante = dict(integrante)

    finally:

        db.close()

    arquivo = BytesIO()

    pdf = canvas.Canvas(
        arquivo,
        pagesize=A4
    )

    largura, altura = A4

    # Centraliza a carteirinha na folha.

    x = (largura - CARD_W) / 2

    y = (altura - CARD_H) / 2

    logo_reader = carregar_logo()

    desenhar_carteirinha(
        pdf,
        integrante,
        x,
        y,
        data_emissao=datetime.now(),
        logo_reader=logo_reader
    )

    pdf.save()

    arquivo.seek(0)

    nome_arquivo = re.sub(
        r'[\\/:*?"<>|]+',
        "_",
        str(integrante.get("nome") or "Integrante")
    ).strip()

    return send_file(
        arquivo,
        as_attachment=True,
        download_name=f"Carteirinha_{nome_arquivo}.pdf",
        mimetype="application/pdf"
    )


# ==========================================================
# GERAÇÃO DO PDF COLETIVO
# ==========================================================

def gerar_pdf_todas_carteirinhas():

    db = SessionLocal()

    try:

        integrantes = db.execute(
            text("""
                SELECT
                    id,
                    codigo_integrante,
                    nome,
                    foto_url
                FROM integrantes
                WHERE status = 'APROVADO'
                AND situacao = 'ATIVO'
                ORDER BY LOWER(nome)
            """)
        ).mappings().all()

        integrantes = [
            dict(integrante)
            for integrante in integrantes
        ]

    finally:

        db.close()

    if not integrantes:

        return "Nenhum integrante aprovado e ativo encontrado"

    arquivo = BytesIO()

    pdf = canvas.Canvas(
        arquivo,
        pagesize=A4
    )

    largura, altura = A4

    # ==========================================
    # ORGANIZAÇÃO DA FOLHA A4
    # ==========================================

    margem_x = 30

    margem_y = 65

    espacamento_x = 20

    espacamento_y = 18

    colunas = 2

    linhas = 4

    por_pagina = colunas * linhas

    largura_grade = (
        colunas * CARD_W
        + (colunas - 1) * espacamento_x
    )

    altura_grade = (
        linhas * CARD_H
        + (linhas - 1) * espacamento_y
    )

    inicio_x = (
        largura - largura_grade
    ) / 2

    inicio_y = (
        altura - altura_grade
    ) / 2

    logo_reader = carregar_logo()

    data_emissao = datetime.now()

    # ==========================================
    # GERAÇÃO DAS CARTEIRINHAS
    # ==========================================

    total = len(integrantes)

    for indice, integrante in enumerate(integrantes):

        posicao = indice % por_pagina

        coluna = posicao % colunas

        linha = posicao // colunas

        x = (
            inicio_x
            + coluna * (CARD_W + espacamento_x)
        )

        y = (
            altura
            - inicio_y
            - CARD_H
            - linha * (CARD_H + espacamento_y)
        )

        desenhar_carteirinha(
            pdf,
            integrante,
            x,
            y,
            data_emissao=data_emissao,
            logo_reader=logo_reader
        )

        # Nova página a cada oito carteirinhas.

        if (
            (indice + 1) % por_pagina == 0
            and (indice + 1) < total
        ):

            pdf.showPage()

    # ==========================================
    # FINALIZAÇÃO
    # ==========================================

    pdf.save()

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="Carteirinhas_Integrantes.pdf",
        mimetype="application/pdf"
    )
