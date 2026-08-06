from io import BytesIO
from datetime import datetime
import os
import requests

from PIL import Image as PILImage

from flask import send_file

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from sqlalchemy import text
from database import SessionLocal

def criar_banner_arredondado(caminho_original, caminho_saida, largura=900, altura=250):

    imagem = PILImage.open(
        caminho_original
    ).convert("RGBA")


    imagem = imagem.resize(
        (largura, altura)
    )


    mascara = PILImage.new(
        "L",
        (largura, altura),
        0
    )


    from PIL import ImageDraw

    desenho = ImageDraw.Draw(
        mascara
    )


    desenho.rounded_rectangle(
        (
            0,
            0,
            largura,
            altura
        ),
        radius=60,
        fill=255
    )


    imagem.putalpha(
        mascara
    )


    imagem.save(
        caminho_saida
    )

def criar_foto_arredondada(caminho_original, caminho_saida, tamanho=300):

    imagem = PILImage.open(caminho_original).convert("RGBA")


    # deixa quadrada cortando o excesso
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
        (tamanho, tamanho)
    )


    # máscara arredondada
    mascara = PILImage.new(
        "L",
        (tamanho, tamanho),
        0
    )


    from PIL import ImageDraw

    desenho = ImageDraw.Draw(
        mascara
    )


    desenho.rounded_rectangle(
        (
            0,
            0,
            tamanho,
            tamanho
        ),
        radius=45,
        fill=255
    )


    imagem.putalpha(
        mascara
    )


    imagem.save(
        caminho_saida
    )

def quebrar_nome(nome, limite=28):

    palavras = nome.upper().split()

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




def baixar_imagem(url, nome):

    try:

        resposta = requests.get(
            url,
            timeout=10
        )

        with open(nome,"wb") as arquivo:
            arquivo.write(resposta.content)

        return nome


    except Exception as e:

        print("Erro imagem:",e)

        return None


from reportlab.lib.utils import ImageReader


def gerar_pdf_carteirinha(id):


    db = SessionLocal()


    integrante = db.execute(
        text("""
            SELECT
                id,
                codigo_integrante,
                nome,
                foto_url
            FROM integrantes
            WHERE id=:id
        """),
        {
            "id":id
        }
    ).mappings().first()


    db.close()



    if not integrante:

        return "Integrante não encontrado"



    arquivo = BytesIO()


    pdf = canvas.Canvas(
        arquivo,
        pagesize=A4
    )


    largura, altura = A4



    # ============================
    # TAMANHO CARTÃO
    # ============================

    card_w = 330
    card_h = 210

    margem_borda = 5


    x = (largura-card_w)/2
    y = (altura-card_h)/2



    azul = colors.HexColor("#0b1522")



    # ============================
    # FUNDO
    # ============================

    pdf.setFillColor(colors.white)

    pdf.roundRect(
        x + 2,
        y + 2,
        card_w - 4,
        card_h - 4,
        18,
        fill=1,
        stroke=0
    )



    # ============================
    # BORDA PRINCIPAL
    # ============================

    pdf.setStrokeColor(azul)

    pdf.setLineWidth(5)

    pdf.roundRect(
        x + margem_borda/2,
        y + margem_borda/2,
        card_w - margem_borda,
        card_h - margem_borda,
        20
    )



    # ============================
    # BANNER SUPERIOR
    # ============================

    header_h = 85


    logo_path = os.path.join(
        "static",
        "img",
        "logo_relatorio.PNG"
    )



    if os.path.exists(logo_path):


        banner_card = "banner_card.png"


        criar_banner_arredondado(
            logo_path,
            banner_card
        )


        pdf.drawImage(
            banner_card,
            x+3,
            y+card_h-header_h-3,
            width=card_w-6,
            height=header_h+3,
            mask="auto"
        )


        os.remove(
            banner_card
        )


    else:


        pdf.setFillColor(
            azul
        )

        pdf.roundRect(
            x+5,
            y+card_h-header_h-5,
            card_w-10,
            header_h,
            17,
            fill=1,
            stroke=0
        )



    # linha abaixo do banner

    pdf.setStrokeColor(
        azul
    )

    pdf.setLineWidth(
        2
    )


    pdf.line(
        x+5,
        y+card_h-header_h,
        x+card_w-5,
        y+card_h-header_h
    )

    # ============================
    # FOTO DO INTEGRANTE
    # ============================

    foto_temp = None


    if integrante["foto_url"]:

        foto_temp = baixar_imagem(
            integrante["foto_url"],
            "temp_integrante.jpg"
        )


    if foto_temp:

        try:

            foto_card = "foto_card.png"


            criar_foto_arredondada(
                foto_temp,
                foto_card,
                tamanho=400
            )


            # borda da foto

            pdf.setStrokeColor(
                azul
            )

            pdf.setLineWidth(
                3
            )


            pdf.roundRect(
                x+22,
                y+42,
                101,
                101,
                12
            )


            # foto arredondada

            pdf.drawImage(
                foto_card,
                x+25,
                y+45,
                width=95,
                height=95,
                mask="auto"
            )


            if os.path.exists(foto_card):
                os.remove(foto_card)


            if os.path.exists(foto_temp):
                os.remove(foto_temp)


        except Exception as e:

            print(
                "Erro foto:",
                e
            )

    # ============================
    # NOME
    # ============================


    pdf.setFillColor(
        azul
    )


    pdf.setFont(
        "Helvetica-Bold",
        12
    )



    linhas = quebrar_nome(
        integrante["nome"]
    )



    pos_y = y+105


    for linha in linhas[:3]:

        pdf.drawString(

            x+150,

            pos_y,

            linha

        )

        pos_y -= 15





    # MATRÍCULA


    pdf.setFont(
        "Helvetica",
        11
    )


    pdf.drawString(

        x+145,

        y+70,

        "Matrícula:"

    )


    pdf.setFont(
        "Helvetica-Bold",
        11
    )


    pdf.drawString(

        x+205,

        y+70,

        integrante["codigo_integrante"]

    )




    # ============================
    # DIVISÓRIA
    # ============================


    pdf.setStrokeColor(
        colors.lightgrey
    )


    pdf.setLineWidth(
        1
    )


    pdf.line(

        x+20,

        y+38,

        x+card_w-20,

        y+38

    )




    # ============================
    # RODAPÉ
    # ============================


    pdf.setFillColor(
        azul
    )


    pdf.setFont(
        "Helvetica-Bold",
        8
    )


    pdf.drawString(

        x+20,

        y+20,

        "CARTEIRINHA DE INTEGRANTE"

    )


    pdf.setFont(
        "Helvetica",
        8
    )


    pdf.drawRightString(

        x+card_w-20,

        y+20,

        datetime.now().strftime("%d/%m/%Y")

    )




    pdf.save()


    arquivo.seek(0)



    return send_file(

        arquivo,

        as_attachment=True,

        download_name=f"Carteirinha_{integrante['nome']}.pdf",

        mimetype="application/pdf"

    )