from flask import Flask, render_template, request, redirect, session
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from flask import send_file
from io import BytesIO
from utils.pdf_carteirinha import gerar_pdf_carteirinha
from utils.pdf_financeiro import gerar_pdf_financeiro

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from datetime import datetime, date
from zoneinfo import ZoneInfo
from database import SessionLocal
from sqlalchemy import text
from werkzeug.security import check_password_hash

import os
import requests
import cloudinary
import cloudinary.uploader
from utils.pdf_viagem import gerar_documentos_viagem
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = Flask(__name__)
app.secret_key = "brilho_negro_2026"

# ==============================
# HISTÓRICO DE ALTERAÇÕES
# ==============================

def registrar_historico(integrante_id, acao, status_anterior, status_novo):

    db = SessionLocal()

    try:

        db.execute(
            text("""
            INSERT INTO historico_integrantes
            (
                integrante_id,
                acao,
                status_anterior,
                status_novo,
                data_hora,
                usuario
            )

            VALUES
            (
                :integrante_id,
                :acao,
                :status_anterior,
                :status_novo,
                :data_hora,
                :usuario
            )
            """),
            {

                "integrante_id": integrante_id,

                "acao": acao,

                "status_anterior": status_anterior,

                "status_novo": status_novo,

                "data_hora": datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                ),

                "usuario": "Administrador"

            }
        )


        db.commit()


    except Exception as e:

        db.rollback()

        print("Erro no histórico:", e)


    finally:

        db.close()

# ==============================
# INICIALIZAÇÃO DO BANCO
# ==============================

# Banco PostgreSQL já criado pelo script externo
# criar_banco()
# atualizar_banco()


# ==============================
# ROTAS
# ==============================


@app.route("/")
def inicio():

    return render_template("index.html")

@app.route("/cadastro")
def cadastro():

    return render_template("cadastro/cadastro.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]

        senha = request.form["senha"]


        db = SessionLocal()

        try:

            resultado = db.execute(
                text("""
                    SELECT usuario, senha
                    FROM usuarios
                    WHERE usuario = :usuario
                """),
                {
                    "usuario": usuario
                }
            ).fetchone()


            if resultado:

                senha_banco = resultado.senha


                if check_password_hash(
                    senha_banco,
                    senha
                ):

                    session["admin"] = True
                    session["usuario"] = usuario


                    return redirect("/admin")



            return render_template(
                "admin/login.html",
                erro="Usuário ou senha inválidos"
            )


        finally:

            db.close()


    return render_template("admin/login.html")

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")


@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        integrantes = db.execute(
            text("""
                SELECT *
                FROM integrantes
                ORDER BY id DESC
            """)
        ).fetchall()


        total = db.execute(
            text("""
                SELECT COUNT(*)
                FROM integrantes
            """)
        ).scalar()


        pendentes = db.execute(
            text("""
                SELECT COUNT(*)
                FROM integrantes
                WHERE status = 'PENDENTE'
            """)
        ).scalar()


        aprovados = db.execute(
            text("""
                SELECT COUNT(*)
                FROM integrantes
                WHERE status = 'APROVADO'
            """)
        ).scalar()


    finally:

        db.close()


    return render_template(
        "admin/integrantes.html",
        integrantes=integrantes,
        total=total,
        pendentes=pendentes,
        aprovados=aprovados
    )

@app.route("/admin/integrante/<int:id>")
def ver_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    try:

        integrante = db.execute(
            text("""
                SELECT *
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).fetchone()



        historico = db.execute(
            text("""
                SELECT *
                FROM historico_integrantes
                WHERE integrante_id = :id
                ORDER BY id DESC
            """),
            {
                "id": id
            }
        ).fetchall()



        return render_template(
            "admin/ficha.html",
            integrante=integrante,
            historico=historico
        )


    except Exception as e:

        print("Erro ao abrir integrante:", e)

        return f"Erro: {e}"


    finally:

        db.close()

@app.route("/admin/integrante/<int:id>/editar", methods=["GET","POST"])
def editar_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()



    if request.method == "POST":

        integrante_atual = db.execute(
            text("""
                SELECT foto_url
                FROM integrantes
                WHERE id=:id
            """),
            {
                "id": id
            }
        ).fetchone()


        foto_url = integrante_atual.foto_url if integrante_atual else None



        foto = request.files.get("foto")


        if foto and foto.filename:

            resultado = cloudinary.uploader.upload(
                foto,
                folder="brilho_negro/integrantes"
            )

            foto_url = resultado["secure_url"]

        print("FUNÇÃO RECEBIDA:", request.form.get("funcao"))
        
        db.execute(
            text("""
            UPDATE integrantes SET

                nome=:nome,
                data_nascimento=:data_nascimento,
                telefone=:telefone,
                email=:email,
                cpf=:cpf,

                possui_alergia=:possui_alergia,
                descricao_alergia=:descricao_alergia,
                alergia_medicamento=:alergia_medicamento,

                responsavel=:responsavel,
                parentesco=:parentesco,
                telefone_responsavel=:telefone_responsavel,

                rua=:rua,
                numero=:numero,
                complemento=:complemento,
                bairro=:bairro,
                cidade=:cidade,
                estado=:estado,
                cep=:cep,
                foto_url=:foto_url,

                calcado=:calcado,
                estuda=:estuda,
                local_estudo=:local_estudo,

                trabalha=:trabalha,
                profissao=:profissao,

                experiencia_banda=:experiencia_banda,
                descricao_experiencia=:descricao_experiencia,

                funcao=:funcao

            WHERE id=:id
            """),
            {
                "nome": request.form["nome"],
                "data_nascimento": request.form["data_nascimento"],
                "possui_alergia": request.form["possui_alergia"],
                "descricao_alergia": request.form["descricao_alergia"],
                "alergia_medicamento": request.form["alergia_medicamento"],

                "responsavel": request.form["responsavel"],
                "parentesco": request.form["parentesco"],
                "telefone_responsavel": request.form["telefone_responsavel"],
                "telefone": request.form["telefone"],
                "email": request.form["email"],
                "cpf": request.form["cpf"],
                "rua": request.form["rua"],
                "numero": request.form["numero"],
                "complemento": request.form["complemento"],
                "bairro": request.form["bairro"],
                "cidade": request.form["cidade"],
                "estado": request.form["estado"],
                "cep": request.form["cep"],
                "foto_url": foto_url,
                "id": id,
                "calcado": request.form.get("calcado"),
                "estuda": request.form.get("estuda"),
                "local_estudo": request.form.get("local_estudo"),
                "trabalha": request.form.get("trabalha"),
                "profissao": request.form.get("profissao"),
                "experiencia_banda": request.form.get("experiencia_banda"),
                "descricao_experiencia": request.form.get("descricao_experiencia"),
                "funcao": request.form.get("funcao")
            }
        )


        db.commit()

        db.close()


        return redirect(f"/admin/integrante/{id}")



    integrante = db.execute(
        text("""
            SELECT *
            FROM integrantes
            WHERE id=:id
        """),
        {
            "id": id
        }
    ).fetchone()


    db.close()


    return render_template(
        "admin/editar.html",
        integrante=integrante
    )

@app.route("/admin/aprovar/<int:id>")
def aprovar_integrante(id):

    db = SessionLocal()

    try:

        # Buscar status atual

        anterior = db.execute(
            text("""
                SELECT status
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).fetchone()[0]


        # Atualizar status

        db.execute(
            text("""
                UPDATE integrantes
                SET status = 'APROVADO'
                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        db.commit()


        registrar_historico(
            id,
            "APROVAÇÃO",
            anterior,
            "APROVADO"
        )


        # NOVO:
        # se vier parâmetro voltar=pendentes
        # retorna para lista de pendentes

        if request.args.get("voltar") == "pendentes":

            return redirect(
                "/admin?status=PENDENTE"
            )


        # comportamento antigo permanece

        return redirect(
            f"/admin/integrante/{id}"
        )


    except Exception as e:

        db.rollback()

        print("Erro ao aprovar:", e)

        return f"Erro: {e}"


    finally:

        db.close()

@app.route("/admin/reprovar/<int:id>")
def reprovar_integrante(id):

    db = SessionLocal()

    try:

        # Buscar status atual

        anterior = db.execute(
            text("""
                SELECT status
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).fetchone()[0]


        # Atualizar status

        db.execute(
            text("""
                UPDATE integrantes
                SET status = 'REPROVADO'
                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        db.commit()


        registrar_historico(
            id,
            "REPROVAÇÃO",
            anterior,
            "REPROVADO"
        )


        return redirect(
            f"/admin/integrante/{id}"
        )


    except Exception as e:

        db.rollback()

        print("Erro ao reprovar:", e)

        return f"Erro: {e}"


    finally:

        db.close()

@app.route("/admin/integrante/<int:id>/excluir")
def excluir_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()

    try:

        db.execute(
            text("""
                DELETE FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        db.commit()


    except Exception as e:

        db.rollback()

        print("Erro ao excluir:", e)

        return f"Erro: {e}"


    finally:

        db.close()


    return redirect("/admin")

@app.route("/admin/integrante/<int:id>/inativar")
def inativar_integrante(id):

    db = SessionLocal()

    try:

        anterior = db.execute(
            text("""
                SELECT status
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).fetchone()[0]


        db.execute(
            text("""
                UPDATE integrantes
                SET status = 'INATIVO'
                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        db.commit()


        registrar_historico(
            id,
            "INATIVAÇÃO",
            anterior,
            "INATIVO"
        )


        return redirect(
            f"/admin/integrante/{id}"
        )


    except Exception as e:

        db.rollback()

        print("Erro ao inativar:", e)

        return f"Erro: {e}"


    finally:

        db.close()

@app.route("/admin/integrante/<int:id>/reativar")
def reativar_integrante(id):

    db = SessionLocal()

    try:

        anterior = db.execute(
            text("""
                SELECT status
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).fetchone()[0]


        db.execute(
            text("""
                UPDATE integrantes
                SET status = 'APROVADO'
                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        db.commit()


        registrar_historico(
            id,
            "REATIVAÇÃO",
            anterior,
            "APROVADO"
        )


        return redirect(
            f"/admin/integrante/{id}"
        )


    except Exception as e:

        db.rollback()

        print("Erro ao reativar:", e)

        return f"Erro: {e}"


    finally:

        db.close()

@app.route("/salvar_cadastro", methods=["POST"])
def salvar_cadastro():

    db = SessionLocal()

    try:

        print("Conectado ao PostgreSQL")


        # ==============================
        # VERIFICAR CPF DUPLICADO
        # ==============================

        cpf = request.form.get("cpf")


        cpf_existente = db.execute(
            text("""
                SELECT nome
                FROM integrantes
                WHERE cpf = :cpf
            """),
            {
                "cpf": cpf
            }
        ).fetchone()


        if cpf_existente:

            return render_template(
                "cadastro/erro.html"
            )


        # ==============================
        # GERAR CÓDIGO DO INTEGRANTE
        # ==============================

        ultimo_id = db.execute(
            text("""
                SELECT MAX(id)
                FROM integrantes
            """)
        ).scalar()


        if ultimo_id:
            total = ultimo_id + 1
        else:
            total = 1


        codigo_integrante = f"BN{total:06d}"


        # ==============================
        # DATA CADASTRO
        # ==============================

        data_cadastro = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime(
            "%d/%m/%Y %H:%M"
        )


        # ==============================
        # DADOS DO FORMULÁRIO
        # ==============================

        nome_integrante = request.form.get(
            "nome",
            ""
        ).title()


        db.execute(
            text("""
            INSERT INTO integrantes

            (

            codigo_integrante,
            nome,
            cpf,
            data_nascimento,

            telefone,
            email,

            cep,
            rua,
            numero,
            complemento,
            bairro,
            cidade,
            estado,

            alergia_medicamento,
            descricao_alergia,

            calcado,
            estuda,
            local_estudo,

            trabalha,
            profissao,

            experiencia_banda,
            descricao_experiencia,
            funcao,

            responsavel,
            telefone_responsavel,

            data_cadastro,
            status

            )

            VALUES

            (

            :codigo_integrante,
            :nome,
            :cpf,
            :data_nascimento,

            :telefone,
            :email,

            :cep,
            :rua,
            :numero,
            :complemento,
            :bairro,
            :cidade,
            :estado,

            :alergia_medicamento,
            :descricao_alergia,

            :calcado,
            :estuda,
            :local_estudo,

            :trabalha,
            :profissao,

            :experiencia_banda,
            :descricao_experiencia,
            :funcao,

            :responsavel,
            :telefone_responsavel,

            :data_cadastro,
            :status

            )

            """),
            {

            "codigo_integrante": codigo_integrante,

            "nome": nome_integrante,

            "cpf": request.form.get("cpf"),

            "data_nascimento": request.form.get("data_nascimento"),

            "telefone": request.form.get("telefone"),

            "email": request.form.get("email"),

            "cep": request.form.get("cep"),

            "rua": request.form.get("rua"),

            "numero": request.form.get("numero"),

            "complemento": request.form.get("complemento"),

            "bairro": request.form.get("bairro"),

            "cidade": request.form.get("cidade"),

            "estado": request.form.get("estado"),

            "alergia_medicamento": request.form.get("alergia_medicamento"),

            "descricao_alergia": request.form.get("descricao_alergia"),

            "calcado": request.form.get("calcado"),

            "estuda": request.form.get("estuda"),

            "local_estudo": request.form.get("local_estudo"),

            "trabalha": request.form.get("trabalha"),

            "profissao": request.form.get("profissao"),

            "experiencia_banda": request.form.get("experiencia_banda"),

            "descricao_experiencia": request.form.get("descricao_experiencia"),

            "funcao": request.form.get("funcao"),

            "responsavel": request.form.get("responsavel"),

            "telefone_responsavel": request.form.get("telefone_responsavel"),

            "data_cadastro": data_cadastro,

            "status": "PENDENTE"

            }

        )


        db.commit()


        return render_template(
            "cadastro/sucesso.html",
            codigo=codigo_integrante
        )


    except Exception as e:

        db.rollback()

        print("ERRO AO SALVAR:", e)

        return f"Erro ao salvar cadastro: {e}"


    finally:

        db.close()

@app.route("/admin/exportar/pdf")
def exportar_pdf():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()

    # ==============================
    # FILTRO
    # ==============================

    status_filtro = request.args.get("status")

    funcao_filtro = request.args.get("funcao")


    condicoes = []

    parametros = {}


    if status_filtro:

        condicoes.append(
            "status = :status"
        )

        parametros["status"] = status_filtro



    if funcao_filtro:

        condicoes.append(
            "funcao = :funcao"
        )

        parametros["funcao"] = funcao_filtro



    where = ""

    if condicoes:

        where = "WHERE " + " AND ".join(condicoes)



    integrantes = db.execute(

        text(f"""

            SELECT

                codigo_integrante,
                nome,
                cpf,
                data_nascimento,
                cidade,
                estado,
                status,
                funcao

            FROM integrantes

            {where}

            ORDER BY LOWER(nome)

        """),

        parametros

    ).mappings().all()


    db.close()

    # ==============================
    # CRIA PDF
    # ==============================

    arquivo = BytesIO()

    from reportlab.lib.pagesizes import A4

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



    # LOGO

    from reportlab.platypus import Image


    logo = Image(
        "static/img/logo_relatorio.PNG",
        width=320,
        height=79
    )

    logo.hAlign = "CENTER"


    elementos.append(logo)


    elementos.append(
        Spacer(1,5)
    )



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

    from reportlab.platypus import HRFlowable


    elementos.append(
        Spacer(1,8)
    )


    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )


    elementos.append(
        Spacer(1,15)
    )


    subtitulo = Paragraph(
        "<b>Relatório de Integrantes</b>",
        estilos["Heading2"]
    )


    elementos.append(subtitulo)



    elementos.append(
        Spacer(1,15)
    )



    filtro_texto = (
        status_filtro
        if status_filtro
        else
        "TODOS OS INTEGRANTES"
    )



    informacoes = Paragraph(

        f"""
        Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}<br/>
        Filtro: {filtro_texto}<br/>
        Total encontrado: {len(integrantes)}
        """,

        estilos["Normal"]

    )


    elementos.append(informacoes)



    elementos.append(
        Spacer(1,20)
    )



    # ==============================
    # TABELA
    # ==============================

    from reportlab.lib.styles import ParagraphStyle


    estilo_tabela = ParagraphStyle(
        "Tabela",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10
    )


    estilo_cabecalho = ParagraphStyle(
        "CabecalhoTabela",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
        alignment=1,
        fontName="Helvetica-Bold"
    )

    estilo_centro = ParagraphStyle(
        "Centro",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
        alignment=1
    )



    dados = [

        [
            Paragraph("Código", estilo_cabecalho),
            Paragraph("Integrante", estilo_cabecalho),
            Paragraph("CPF", estilo_cabecalho),
            Paragraph("Data nascimento", estilo_cabecalho),
            Paragraph("Cidade/UF", estilo_cabecalho),
            Paragraph("Função", estilo_cabecalho),
            Paragraph("Status", estilo_cabecalho)
        ]

    ]



    for pessoa in integrantes:

        data_nascimento = datetime.strptime(
            pessoa["data_nascimento"],
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")


        dados.append(
            [
                Paragraph(
                    str(pessoa["codigo_integrante"]),
                    estilo_centro
                ),

                Paragraph(
                    pessoa["nome"].title(),
                    estilo_tabela
                ),

                Paragraph(
                    pessoa["cpf"],
                    estilo_centro
                ),

                Paragraph(
                    data_nascimento,
                    estilo_centro
                ),

                Paragraph(
                    f'{pessoa["cidade"]}/{pessoa["estado"]}',
                    estilo_tabela
                ),

                Paragraph(
                    pessoa["funcao"] or "-",
                    estilo_centro
                ),

                Paragraph(
                    pessoa["status"],
                    estilo_centro
                )
            ]
        )



    tabela = Table(
        dados,
        colWidths=[
            50,   # código
            130,  # nome
            80,   # cpf
            70,   # nascimento
            80,   # cidade
            70,   # função
            55    # status
        ],
        repeatRows=1
    )


    tabela.setStyle(

        TableStyle(

            [

                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0,0),
                    (-1,0),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (0,0),
                    (-1,0),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0,0),
                    (-1,-1),
                    "TOP"
                )

            ]

        )

    )


    elementos.append(tabela)



    elementos.append(
        Spacer(1,20)
    )


    rodape = Paragraph(
        """
        SGI Brilho Negro<br/>
        Documento gerado automaticamente.
        """,
        estilos["Normal"]
    )

    elementos.append(rodape)

    pdf.build(elementos)

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="relatorio_integrantes_brilho_negro.pdf",
        mimetype="application/pdf"
    )

@app.route("/admin/integrante/<int:id>/pdf")
def pdf_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    integrante = db.execute(
        text("""
            SELECT *
            FROM integrantes
            WHERE id=:id
        """),
        {
            "id": id
        }
    ).mappings().first()


    db.close()


    if not integrante:
        return "Integrante não encontrado"


    arquivo = BytesIO()


    pdf = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        topMargin=40,
        bottomMargin=40,
        leftMargin=40,
        rightMargin=40
    )


    elementos = []


    estilos = getSampleStyleSheet()

    # ==============================
    # CABEÇALHO PADRÃO RELATÓRIO
    # ==============================


    logo = Image(
        "static/img/logo_relatorio.PNG",
        width=320,
        height=79
    )

    logo.hAlign = "CENTER"


    elementos.append(logo)


    elementos.append(
        Spacer(1,5)
    )



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

    data_geracao = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )


    elementos.append(
        Spacer(1,8)
    )


    informacao = Paragraph(
        f"""
        <font size="9">
        Ficha individual do integrante<br/>
        Gerado em: {data_geracao}
        </font>
        """,
        estilos["Normal"]
    )


    elementos.append(informacao)


    elementos.append(
        Spacer(1,8)
    )


    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )


    elementos.append(
        Spacer(1,15)
    )


    elementos.append(
        Spacer(1,20)
    )

    # ===========================
    # RESUMO FINANCEIRO
    # ===========================

    resumo = [
        ["Receitas", f"R$ {receitas:,.2f}"],
        ["Despesas", f"R$ {despesas:,.2f}"],
        ["Saldo", f"R$ {saldo:,.2f}"]
    ]

    tabela = Table(
        resumo,
        colWidths=[140,120]
    )

    tabela.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),0.5,colors.grey),

        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EAEAEA")),

        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),

        ("ALIGN",(1,0),(1,-1),"RIGHT"),

        ("BOTTOMPADDING",(0,0),(-1,-1),8)

    ]))

    elementos.append(tabela)

    elementos.append(Spacer(1,18))

    # ===========================
    # TÍTULO DA TABELA
    # ===========================

    elementos.append(
        Paragraph(
            "<b>MOVIMENTAÇÕES FINANCEIRAS</b>",
            estilos["Heading2"]
        )
    )

    elementos.append(Spacer(1,8))

    # ===========================
    # TABELA DAS MOVIMENTAÇÕES
    # ===========================

    dados = [
        [
            "Data",
            "Tipo",
            "Categoria",
            "Descrição",
            "Valor"
        ]
    ]

    for item in movimentacoes:
        dados.append(
            [
                item.data_movimento.strftime("%d/%m/%Y"),
                item.tipo,
                item.categoria,
                item.descricao,
                f'R$ {item.valor:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            ]
        )

    tabela = Table(
        dados,
        colWidths=[70,70,110,170,80]
    )

    tabela.setStyle(
        TableStyle(
            [
                ("GRID",(0,0),(-1,-1),0.5,colors.grey),
                ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("ALIGN",(0,0),(-1,0),"CENTER"),
                ("ALIGN",(4,1),(4,-1),"RIGHT"),
                ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                ("BOTTOMPADDING",(0,0),(-1,0),8),
            ]
        )
    )

    elementos.append(tabela)

    elementos.append(Spacer(1,15))

    # ==========================
    # FOTO + IDENTIFICAÇÃO
    # ==========================


    foto = ""


    if integrante["foto_url"]:


        resposta = requests.get(
            integrante["foto_url"]
        )


        imagem = BytesIO(
            resposta.content
        )


        foto = Image(
            imagem,
            width=90,
            height=90
        )


    estilo_nome = ParagraphStyle(
        "NomeIntegrante",
        parent=estilos["Normal"],
        fontSize=15,
        leading=18
    )


    identificacao = Paragraph(
        f"""
        <b>{integrante['nome']}</b><br/><br/>

        <b>Código:</b> {integrante['codigo_integrante']}<br/>

        <b>Status:</b> {integrante['status']}
        """,
        estilo_nome
    )



    cabecalho_integrante = Table(
        [
            [foto, identificacao]
        ],
        colWidths=[130,270]
    )


    cabecalho_integrante.setStyle(
        TableStyle(
            [
                ("VALIGN",(0,0),(-1,-1),"TOP"),

                (
                    "BOX",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                ),

                (
                    "LEFTPADDING",
                    (0,0),
                    (-1,-1),
                    10
                ),

                (
                    "RIGHTPADDING",
                    (0,0),
                    (-1,-1),
                    10
                ),

                (
                    "TOPPADDING",
                    (0,0),
                    (-1,-1),
                    10
                ),

                (
                    "BOTTOMPADDING",
                    (0,0),
                    (-1,-1),
                    10
                )
            ]
        )
    )


    elementos.append(
        cabecalho_integrante
    )


    elementos.append(
        Spacer(1,20)
    )  


    # ==========================
    # DADOS DA FICHA
    # ==========================


    estilo_secao = ParagraphStyle(
        "Secao",
        parent=estilos["Heading3"],
        fontSize=12,
        leading=14,
        spaceAfter=5
    )


    def adicionar_secao(titulo_secao):

        elementos.append(
            Spacer(1,5)
        )

        elementos.append(
            Paragraph(
                f"<b>{titulo_secao}</b>",
                estilo_secao
            )
        )

        elementos.append(
            HRFlowable(
                width="100%",
                thickness=0.5
            )
        )

    estilo_dados = ParagraphStyle(
        "Dados",
        parent=estilos["Normal"],
        fontSize=9,
        leading=11
    )

    def adicionar_linha(texto):

        elementos.append(
            Paragraph(
                texto,
                estilos["Normal"]
            )
        )



    # DADOS PESSOAIS

    adicionar_secao("Dados Pessoais")


    adicionar_linha(
        f"""
        <b>CPF:</b> {integrante['cpf'] or ''}<br/>
        <b>Data nascimento:</b> {integrante['data_nascimento'] or ''}
        """
    )



    # CONTATO

    adicionar_secao("Contato")


    adicionar_linha(
        f"""
        <b>Telefone:</b> {integrante['telefone'] or ''}<br/>
        <b>Email:</b> {integrante['email'] or ''}
        """
    )



    # ENDEREÇO

    adicionar_secao("Endereço")


    adicionar_linha(
        f"""
        <b>Rua:</b> {integrante['rua'] or ''}, 
        Nº {integrante['numero'] or ''}<br/>

        <b>Bairro:</b> {integrante['bairro'] or ''}<br/>

        <b>Cidade:</b> {integrante['cidade'] or ''} -
        {integrante['estado'] or ''}<br/>

        <b>CEP:</b> {integrante['cep'] or ''}
        """
    )



    # SAÚDE

    adicionar_secao("Saúde")


    adicionar_linha(
        f"""
        <b>Possui alergia:</b> {integrante['possui_alergia'] or ''}<br/>

        <b>Alergia medicamentos:</b>
        {integrante['alergia_medicamento'] or ''}
        """
    )



    # RESPONSÁVEL

    adicionar_secao("Responsável")


    adicionar_linha(
        f"""
        <b>Nome:</b> {integrante['responsavel'] or 'Não informado'}<br/>

        <b>Parentesco:</b> {integrante['parentesco'] or ''}<br/>

        <b>Telefone:</b> {integrante['telefone_responsavel'] or ''}
        """
    )



    # INFORMAÇÕES

    adicionar_secao("Informações")


    adicionar_linha(
        f"""
        <b>Calçado:</b> {integrante['calcado'] or ''}<br/>

        <b>Estuda:</b> {integrante['estuda'] or ''}<br/>

        <b>Trabalha:</b> {integrante['trabalha'] or ''}<br/>

        <b>Profissão:</b> {integrante['profissao'] or ''}<br/>

        <b>Experiência musical:</b>
        {integrante['experiencia_banda'] or ''}
        """
    )



    # CADASTRO

    adicionar_secao("Cadastro")


    adicionar_linha(
        f"""
        <b>Data cadastro:</b>
        {integrante['data_cadastro'] or ''}
        """
    )

    def rodape_pdf(canvas, doc):

        canvas.saveState()

        canvas.setFont(
            "Helvetica",
            8
        )

        texto = (
            "SGI Brilho Negro | "
            "Documento gerado automaticamente | "
            f"Página {doc.page}"
        )

        canvas.drawCentredString(
            A4[0] / 2,
            20,
            texto
        )

        canvas.restoreState()

    pdf.build(
        elementos,
        onFirstPage=rodape_pdf,
        onLaterPages=rodape_pdf
    )


    arquivo.seek(0)


    return send_file(
        arquivo,
        as_attachment=True,
        download_name=f"ficha_{integrante['codigo_integrante']}.pdf",
        mimetype="application/pdf"
    )

@app.route("/admin/exportar/excel")
def exportar_excel():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    integrantes = db.execute(
        text("""
            SELECT
            codigo_integrante,
            nome,
            cpf,
            data_nascimento,
            telefone,
            email,
            endereco,
            cidade,
            estado,
            possui_alergia,
            descricao_alergia,
            responsavel,
            parentesco,
            telefone_responsavel,
            calcado,
            funcao,
            status,
            data_cadastro,
            calcado

            FROM integrantes

            ORDER BY nome
        """)
    ).mappings().all()


    db.close()



    arquivo = BytesIO()


    wb = Workbook()

    ws = wb.active

    ws.title = "Integrantes"



    cabecalho = [

        "Código",
        "Nome",
        "CPF",
        "Data Nascimento",
        "Telefone",
        "Email",
        "Endereço",
        "Cidade",
        "Estado",
        "Possui Alergia",
        "Descrição Alergia",
        "Responsável",
        "Parentesco",
        "Telefone Responsável",
        "Tamanho Calçado",
        "funcao",
        "Status",
        "Data Cadastro"

    ]


    ws.append(cabecalho)



    for celula in ws[1]:

        celula.font = Font(bold=True)

        celula.alignment = Alignment(
            horizontal="center"
        )



    for pessoa in integrantes:

        ws.append([

            pessoa["codigo_integrante"],
            pessoa["nome"],
            pessoa["cpf"],
            pessoa["data_nascimento"],
            pessoa["telefone"],
            pessoa["email"],
            pessoa["endereco"],
            pessoa["cidade"],
            pessoa["estado"],
            pessoa["possui_alergia"],
            pessoa["descricao_alergia"],
            pessoa["responsavel"],
            pessoa["parentesco"],
            pessoa["telefone_responsavel"],
            pessoa["calcado"],
            pessoa["funcao"],
            pessoa["status"],
            pessoa["data_cadastro"]

        ])



    for coluna in ws.columns:

        tamanho = max(
            len(str(c.value))
            if c.value else 0
            for c in coluna
        )

        ws.column_dimensions[
            coluna[0].column_letter
        ].width = tamanho + 3



    wb.save(arquivo)


    arquivo.seek(0)


    return send_file(

        arquivo,

        as_attachment=True,

        download_name="integrantes_brilho_negro.xlsx",

        mimetype=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

@app.route("/admin/viagens")
def viagens():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    lista = db.execute(
        text("""
            SELECT
                v.*,

                COUNT(vi.integrante_id) AS total_participantes

            FROM viagens v

            LEFT JOIN viagem_integrantes vi
            ON vi.viagem_id = v.id

            GROUP BY v.id

            ORDER BY v.data_saida DESC
        """)
    ).mappings().all()


    db.close()


    return render_template(
        "admin/viagens.html",
        viagens=lista
    )


@app.route("/admin/viagens/nova", methods=["POST"])
def nova_viagem():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    db.execute(
        text("""
            INSERT INTO viagens
            (
                evento,
                destino,
                data_saida,
                data_retorno,
                responsavel,
                observacoes
            )

            VALUES
            (
                :evento,
                :destino,
                :data_saida,
                :data_retorno,
                :responsavel,
                :observacoes
            )
        """),
        {
            "evento": request.form["evento"],
            "destino": request.form["destino"],
            "data_saida": request.form["data_saida"],
            "data_retorno": request.form["data_retorno"] or None,
            "responsavel": request.form["responsavel"],
            "observacoes": request.form["observacoes"]
        }
    )


    db.commit()

    db.close()


    return redirect("/admin/viagens")


@app.route("/admin/viagem/<int:id>/integrantes")
def integrantes_viagem(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    viagem = db.execute(
        text("""
            SELECT *
            FROM viagens
            WHERE id=:id
        """),
        {
            "id": id
        }
    ).mappings().first()



    integrantes = db.execute(
        text("""
            SELECT
                id,
                codigo_integrante,
                nome,
                cidade,
                status

            FROM integrantes

            ORDER BY nome
        """)
    ).mappings().all()



    selecionados = db.execute(
        text("""
            SELECT integrante_id
            FROM viagem_integrantes
            WHERE viagem_id=:id
        """),
        {
            "id": id
        }
    ).scalars().all()



    participantes = db.execute(
        text("""
            SELECT
                i.id,
                i.codigo_integrante,
                i.nome,
                i.cidade,
                i.status

            FROM viagem_integrantes v

            JOIN integrantes i
            ON i.id = v.integrante_id

            WHERE v.viagem_id=:id

            ORDER BY i.nome
        """),
        {
            "id": id
        }
    ).mappings().all()



    db.close()


    return render_template(
        "admin/integrantes_viagem.html",
        viagem=viagem,
        integrantes=integrantes,
        selecionados=selecionados,
        participantes=participantes
    )

@app.route("/admin/viagem/<int:id>/integrantes/salvar", methods=["POST"])
def salvar_integrantes_viagem(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    # Remove os integrantes atuais dessa viagem
    db.execute(
        text("""
            DELETE FROM viagem_integrantes
            WHERE viagem_id=:id
        """),
        {
            "id": id
        }
    )


    integrantes = request.form.getlist("integrantes")


    for integrante_id in integrantes:

        db.execute(
            text("""
                INSERT INTO viagem_integrantes
                (
                    viagem_id,
                    integrante_id
                )
                VALUES
                (
                    :viagem_id,
                    :integrante_id
                )
            """),
            {
                "viagem_id": id,
                "integrante_id": integrante_id
            }
        )


    db.commit()

    db.close()


    return redirect(
        f"/admin/viagem/{id}/integrantes"
    )

@app.route("/admin/viagem/<int:id>")
def detalhe_viagem(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    viagem = db.execute(
        text("""
            SELECT *
            FROM viagens
            WHERE id=:id
        """),
        {
            "id": id
        }
    ).mappings().first()



    participantes = db.execute(
        text("""
            SELECT
                i.codigo_integrante,
                i.nome,
                i.cidade,
                i.status

            FROM viagem_integrantes vi

            INNER JOIN integrantes i
            ON i.id = vi.integrante_id

            WHERE vi.viagem_id=:id

            ORDER BY i.nome
        """),
        {
            "id": id
        }
    ).mappings().all()



    db.close()



    return render_template(
        "admin/detalhe_viagem.html",
        viagem=viagem,
        participantes=participantes
    )

@app.route("/admin/viagem/<int:id>/documentos")
def documentos_viagem(id):

    if "admin" not in session:
        return redirect("/login")

    return gerar_documentos_viagem(id)

@app.route("/admin/carteirinhas")
def admin_carteirinhas():

    db = SessionLocal()

    integrantes = db.execute(text("""
        SELECT
            id,
            codigo_integrante,
            nome,
            foto,
            status
        FROM integrantes
        WHERE status = 'APROVADO'
        ORDER BY nome
    """)).mappings().all()

    db.close()

    return render_template(
        "admin/carteirinhas.html",
        integrantes=integrantes
    )

@app.route("/admin/financeiro")
def financeiro():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    receitas = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='RECEITA'
        """)
    ).scalar()


    despesas = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='DESPESA'
        """)
    ).scalar()


    saldo = receitas - despesas


    db.close()

    movimento_ok = request.args.get("novo")

    return render_template(
        "admin/financeiro.html",
        receitas=f"{receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        despesas=f"{despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        saldo=f"{saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        movimento_ok=movimento_ok
    )

@app.route("/admin/financeiro/nova", methods=["GET","POST"])
def nova_movimentacao():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    if request.method == "POST":

        valor = request.form["valor"]

        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")        

        db.execute(
            text("""
                INSERT INTO financeiro
                (
                    temporada,
                    tipo,
                    categoria,
                    descricao,
                    valor,
                    data_movimento,
                    observacao
                )

                VALUES
                (
                    :temporada,
                    :tipo,
                    :categoria,
                    :descricao,
                    :valor,
                    :data_movimento,
                    :observacao
                )
            """),
            {

                "temporada": request.form.get("temporada"),
                "tipo": request.form["tipo"],
                "categoria": request.form["categoria"],
                "descricao": request.form["descricao"],
                "valor": valor,
                "data_movimento": request.form["data_movimento"],
                "observacao": request.form["observacao"]

            }
        )


        db.commit()
        db.close()


        return redirect("/admin/financeiro?novo=ok")


    db.close()


    return render_template(
        "admin/nova_movimentacao.html"
    )

@app.route("/admin/financeiro/movimentacoes")
def movimentacoes_financeiro():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    temporada = request.args.get("temporada", "")
    tipo = request.args.get("tipo", "")
    categoria = request.args.get("categoria", "")


    query = """
        SELECT
            id,
            temporada,
            data_movimento,
            tipo,
            categoria,
            descricao,
            valor,
            observacao

        FROM financeiro

        WHERE 1=1
    """


    parametros = {}


    if temporada:

        query += """
            AND temporada = :temporada
        """

        parametros["temporada"] = temporada



    if tipo:

        query += """
            AND tipo = :tipo
        """

        parametros["tipo"] = tipo



    if categoria:

        query += """
            AND categoria ILIKE :categoria
        """

        parametros["categoria"] = f"%{categoria}%"



    query += """
        ORDER BY data_movimento DESC, id DESC
    """



    movimentacoes = db.execute(
        text(query),
        parametros
    ).fetchall()



    receitas = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='RECEITA'
        """)
    ).scalar()



    despesas = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='DESPESA'
        """)
    ).scalar()



    saldo = receitas - despesas



    db.close()



    return render_template(
        "admin/movimentacoes.html",
        movimentacoes=movimentacoes,
        receitas=receitas,
        despesas=despesas,
        saldo=saldo
    )

@app.route("/admin/financeiro/prestacao")
def prestacao_financeira():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    movimentacoes = db.execute(
        text("""
            SELECT *
            FROM financeiro
            ORDER BY data_movimento
        """)
    ).fetchall()



    receitas = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='RECEITA'
        """)
    ).scalar()



    despesas = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='DESPESA'
        """)
    ).scalar()



    saldo = receitas - despesas



    total_doacoes = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='RECEITA'
            AND categoria ILIKE '%Doação%'
        """)
    ).scalar()



    total_patrocinios = db.execute(
        text("""
            SELECT COALESCE(SUM(valor),0)
            FROM financeiro
            WHERE tipo='RECEITA'
            AND categoria ILIKE '%Patrocínio%'
        """)
    ).scalar()



    quantidade_movimentos = db.execute(
        text("""
            SELECT COUNT(*)
            FROM financeiro
        """)
    ).scalar()



    db.close()



    pdf = gerar_pdf_financeiro(
        movimentacoes,
        receitas,
        despesas,
        saldo,
        total_doacoes,
        total_patrocinios,
        quantidade_movimentos,
        "2026"
    )



    return send_file(
        pdf,
        mimetype="application/pdf",
        download_name="Prestacao_Contas_2026.pdf",
        as_attachment=False
    )

@app.route("/admin/api/integrante/<int:id>")
def api_integrante(id):

    db = SessionLocal()

    integrante = db.execute(
        text("""
            SELECT
                id,
                codigo_integrante,
                nome,
                foto_url,
                tipo_sanguineo
            FROM integrantes
            WHERE id=:id
        """),
        {
            "id": id
        }
    ).mappings().first()

    db.close()


    if not integrante:

        return {
            "erro": "Integrante não encontrado"
        }, 404


    return {
        "nome": integrante["nome"],
        "codigo": integrante["codigo_integrante"],
        "foto": integrante["foto_url"],
        "tipo_sanguineo": integrante["tipo_sanguineo"]
    }

@app.route("/admin/carteirinha/pdf/<int:id>")
def baixar_carteirinha_pdf(id):

    return gerar_pdf_carteirinha(id)

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)