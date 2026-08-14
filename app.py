from flask import Flask, render_template, request, redirect, session
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from flask import send_file
from io import BytesIO
from utils.pdf_carteirinha import (
    gerar_pdf_carteirinha,
    gerar_pdf_todas_carteirinhas
)
from utils.pdf_financeiro import gerar_pdf_financeiro
from utils.pdf_rifa import gerar_pdf_rifa
from decimal import Decimal

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
from collections import Counter

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

@app.template_filter('moeda')
def moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =====================================================
# FUNÇÕES DA BANDA
# =====================================================

FUNCOES_BANDA = [
    ("Músico", "🎺 Músico"),
    ("Corpo Coreográfico", "💃 Corpo Coreográfico"),
    ("Apoio", "🛠️ Apoio"),
    ("Maestro", "🥁 Maestro"),
    ("Instrutor", "🎼 Instrutor"),
    ("Capitão-mor", "🫡 Capitão-mor"),
    ("Guardião", "🛡️ Guardião"),
    ("Produção", "🎬 Produção"),
]

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

@app.context_processor
def disponibilizar_funcoes():

    return {
        "funcoes_banda": FUNCOES_BANDA
    }

@app.route("/")
def inicio():

    return render_template("index.html")

@app.route("/cadastro")
def cadastro():

    db = SessionLocal()

    try:

        status = db.execute(
            text("""
                SELECT valor
                FROM configuracoes
                WHERE chave = 'inscricoes_status'
            """)
        ).scalar()

        # Se não existir configuração,
        # mantém o cadastro aberto.
        if not status:
            status = "ABERTA"

        # ==========================================
        # INSCRIÇÕES PAUSADAS
        # ==========================================

        if status == "PAUSADA":

            return render_template(
                "cadastro/pausado.html"
            )

        # ==========================================
        # INSCRIÇÕES FECHADAS
        # ==========================================

        if status == "FECHADA":

            return render_template(
                "cadastro/fechado.html"
            )

        # ==========================================
        # INSCRIÇÕES ABERTAS
        # ==========================================

        return render_template(
            "cadastro/cadastro.html"
        )

    finally:

        db.close()

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

        # ==========================================
        # RESUMO DOS INTEGRANTES
        # ==========================================

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

        # ==========================================
        # INTEGRANTES PARA CARTEIRINHAS
        # ==========================================

        integrantes_carteirinhas = db.execute(
            text("""
                SELECT
                    id,
                    codigo_integrante,
                    nome
                FROM integrantes
                WHERE status = 'APROVADO'
                AND situacao = 'ATIVO'
                ORDER BY LOWER(nome)
            """)
        ).mappings().all()

        # ==========================================
        # TEMPORADAS
        # ==========================================

        temporadas = db.execute(
            text("""
                SELECT *
                FROM temporadas
                ORDER BY ano DESC
            """)
        ).mappings().all()

        # ==========================================
        # STATUS DAS INSCRIÇÕES
        # ==========================================

        status_inscricoes = db.execute(
            text("""
                SELECT valor
                FROM configuracoes
                WHERE chave = 'inscricoes_status'
            """)
        ).scalar()

        status_inscricoes = status_inscricoes or "ABERTA"

        # ==========================================
        # ANIVERSARIANTES DO MÊS
        # ==========================================

        mes_atual = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).month


        aniversariantes = db.execute(
            text("""
                SELECT
                    id,
                    codigo_integrante,
                    nome,
                    data_nascimento,
                    cidade,
                    funcao,

                    TO_CHAR(
                        CAST(data_nascimento AS DATE),
                        'DD/MM'
                    ) AS aniversario

                FROM integrantes

                WHERE data_nascimento IS NOT NULL
                AND data_nascimento <> ''
                AND status = 'APROVADO'
                AND situacao = 'ATIVO'


                AND EXTRACT(
                    MONTH FROM CAST(data_nascimento AS DATE)
                ) = :mes

                ORDER BY
                    EXTRACT(
                        DAY FROM CAST(data_nascimento AS DATE)
                    ),
                    LOWER(nome)
            """),
            {
                "mes": mes_atual
            }
        ).mappings().all()


        # ==========================================
        # NOME DO MÊS
        # ==========================================

        meses = [
            "",
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro"
        ]

        mes_nome = meses[mes_atual]


    finally:

        db.close()


    # ==========================================
    # RETORNO DA PÁGINA
    # ==========================================

    return render_template(
        "admin/admin.html",
        total=total,
        pendentes=pendentes,
        aprovados=aprovados,
        temporadas=temporadas,
        aniversariantes=aniversariantes,
        mes_nome=mes_nome,
        status_inscricoes=status_inscricoes,
        integrantes_carteirinhas=integrantes_carteirinhas
    )

@app.route("/integrantes")
def integrantes():

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # LISTA DE INTEGRANTES
        # ==========================================

        integrantes = db.execute(
            text("""
                SELECT *
                FROM integrantes
                ORDER BY id DESC
            """)
        ).fetchall()


        # ==========================================
        # RESUMO DOS INTEGRANTES
        # ==========================================

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


        inativos = db.execute(
            text("""
                SELECT COUNT(*)
                FROM integrantes
                WHERE situacao = 'INATIVO'
            """)
        ).scalar()


    finally:

        db.close()


    return render_template(
        "admin/integrantes.html",
        integrantes=integrantes,
        total=total,
        pendentes=pendentes,
        aprovados=aprovados,
        inativos=inativos
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

@app.route("/admin/inscricoes/status", methods=["POST"])
def alterar_status_inscricoes():

    if "admin" not in session:
        return redirect("/login")

    novo_status = request.form.get("status")

    status_validos = [
        "ABERTA",
        "PAUSADA",
        "FECHADA"
    ]

    if novo_status not in status_validos:
        return "Status de inscrição inválido", 400

    db = SessionLocal()

    try:

        db.execute(
            text("""
                UPDATE configuracoes
                SET valor = :valor
                WHERE chave = 'inscricoes_status'
            """),
            {
                "valor": novo_status
            }
        )

        db.commit()

        print(
            f"Status das inscrições alterado para: {novo_status}"
        )

        return redirect("/admin")

    except Exception as e:

        db.rollback()

        print(
            "ERRO AO ALTERAR STATUS DAS INSCRIÇÕES:",
            e
        )

        return f"Erro ao alterar status: {e}", 500

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
            {"id": id}
        ).fetchone()[0]

        # Atualizar status
        db.execute(
            text("""
                UPDATE integrantes
                SET status = 'APROVADO'
                WHERE id = :id
            """),
            {"id": id}
        )

        db.commit()

        registrar_historico(
            id,
            "APROVAÇÃO",
            anterior,
            "APROVADO"
        )

        # ==========================================
        # APROVOU → VOLTA PARA INTEGRANTES
        # ==========================================

        if request.args.get("voltar") == "pendentes":
            return redirect("/integrantes")

        # Comportamento normal
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
                SELECT situacao
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).scalar()

        if anterior == "INATIVO":
            return redirect(f"/admin/integrante/{id}")

        db.execute(
            text("""
                UPDATE integrantes
                SET situacao = 'INATIVO'
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
                SELECT situacao
                FROM integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).scalar()

        if anterior == "ATIVO":
            return redirect(f"/admin/integrante/{id}")

        db.execute(
            text("""
                UPDATE integrantes
                SET situacao = 'ATIVO'
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
            "ATIVO"
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
        # VERIFICAR STATUS DAS INSCRIÇÕES
        # ==============================

        status_inscricoes = db.execute(
            text("""
                SELECT valor
                FROM configuracoes
                WHERE chave = 'inscricoes_status'
            """)
        ).scalar()

        if status_inscricoes != "ABERTA":

            if status_inscricoes == "PAUSADA":

                return render_template(
                    "cadastro/pausado.html"
                )

            if status_inscricoes == "FECHADA":

                return render_template(
                    "cadastro/fechado.html"
                )        

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

    situacao_filtro = request.args.get("situacao")

    funcao_filtro = request.args.get("funcao")


    condicoes = []

    parametros = {}


    if status_filtro:

        condicoes.append(
            "status = :status"
        )

        parametros["status"] = status_filtro


    if situacao_filtro:

        condicoes.append(
            "situacao = :situacao"
        )

    parametros["situacao"] = situacao_filtro    



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
                situacao,
                funcao

            FROM integrantes

            {where}

            ORDER BY LOWER(nome)

        """),

        parametros

    ).mappings().all()


    db.close()

    # ==============================
    # DISTRIBUIÇÃO POR FUNÇÃO
    # ==============================

    distribuicao_funcao = {}

    for pessoa in integrantes:

        funcao = pessoa["funcao"] or "Integrantes sem função definida"

        if funcao in distribuicao_funcao:
            distribuicao_funcao[funcao] += 1
        else:
            distribuicao_funcao[funcao] = 1

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



    filtros_aplicados = []

    if status_filtro:
        filtros_aplicados.append(
            f"Status: {status_filtro}"
            )

    if situacao_filtro:
        filtros_aplicados.append(
            f"Situação: {situacao_filtro}"
        )

    if funcao_filtro:
        filtros_aplicados.append(
            f"Função: {funcao_filtro}"
        )


    filtro_texto = (
        " | ".join(filtros_aplicados)
        if filtros_aplicados
        else
        "TODOS OS INTEGRANTES"
    )



    texto_funcoes = "<br/>".join(
        [
            f"{funcao}: {quantidade}"
            for funcao, quantidade in distribuicao_funcao.items()
        ]
    )


    informacoes = Paragraph(

        f"""
        Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}<br/>
        Filtro: {filtro_texto}<br/><br/>

        <b>Distribuição por Função:</b><br/>

        {texto_funcoes}

        <br/><br/>

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

@app.route("/admin/exportar/pdf/calcados")
def exportar_pdf_calcados():

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    # ==============================
    # FILTROS
    # ==============================

    status_filtro = request.args.get("status")
    situacao_filtro = request.args.get("situacao")
    funcao_filtro = request.args.get("funcao")
    excluir_funcao = request.args.get("excluir_funcao")

    condicoes = []
    parametros = {}

    if status_filtro:

        condicoes.append(
            "status = :status"
        )

        parametros["status"] = status_filtro

    if situacao_filtro:

        condicoes.append(
            "situacao = :situacao"
        )

        parametros["situacao"] = situacao_filtro

    if funcao_filtro:

        condicoes.append(
            "funcao = :funcao"
        )

        parametros["funcao"] = funcao_filtro

    if excluir_funcao:

        condicoes.append(
            "funcao <> :excluir_funcao"
        )

    parametros["excluir_funcao"] = excluir_funcao    

    where = ""

    if condicoes:

        where = "WHERE " + " AND ".join(condicoes)

    # ==============================
    # BUSCAR INTEGRANTES
    # ==============================

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

    # ==============================
    # LOGO
    # ==============================

    from reportlab.platypus import Image

    logo = Image(
        "static/img/logo_relatorio.PNG",
        width=320,
        height=79
    )

    logo.hAlign = "CENTER"

    elementos.append(logo)

    elementos.append(
        Spacer(1, 5)
    )

    # ==============================
    # TÍTULO
    # ==============================

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
        Spacer(1, 8)
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1
        )
    )

    elementos.append(
        Spacer(1, 15)
    )

    subtitulo = Paragraph(
        "<b>Relatório de Calçados</b>",
        estilos["Heading2"]
    )

    elementos.append(subtitulo)

    elementos.append(
        Spacer(1, 15)
    )

    # ==============================
    # FILTROS APLICADOS
    # ==============================

    filtros_aplicados = []

    if status_filtro:

        filtros_aplicados.append(
            f"Status Cadastro: {status_filtro}"
        )

    if situacao_filtro:

        filtros_aplicados.append(
            f"Situação: {situacao_filtro}"
        )

    if funcao_filtro:

        filtros_aplicados.append(
            f"Função: {funcao_filtro}"
        )

    filtro_texto = (

        " | ".join(filtros_aplicados)

        if filtros_aplicados

        else

        "TODOS OS INTEGRANTES"

    )

    informacoes = Paragraph(

        f"""
        Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}<br/>
        Filtro: {filtro_texto}<br/><br/>

        <b>Total encontrado:</b> {len(integrantes)}
        """,

        estilos["Normal"]

    )

    elementos.append(informacoes)

    elementos.append(
        Spacer(1, 20)
    )

    # ==============================
    # ESTILOS DA TABELA
    # ==============================

    from reportlab.lib.styles import ParagraphStyle

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

    # ==============================
    # DADOS DA TABELA
    # ==============================

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

        dados.append(

            [

                Paragraph(
                    str(pessoa["codigo_integrante"]),
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

            ]

        )

    # ==============================
    # TABELA
    # ==============================

    tabela = Table(

        dados,

        colWidths=[
            110,   # código
            300,   # integrante
            70     # calçado
        ],

        repeatRows=1
    )

    tabela.setStyle(

        TableStyle(

            [

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

            ]

        )

    )

    elementos.append(tabela)

    elementos.append(
        Spacer(1, 20)
    )

    # ==============================
    # RODAPÉ
    # ==============================

    rodape = Paragraph(
        """
        SGI Brilho Negro<br/>
        Documento gerado automaticamente.
        """,
        estilos["Normal"]
    )

    elementos.append(rodape)

    # ==============================
    # GERAR PDF
    # ==============================

    pdf.build(elementos)

    arquivo.seek(0)

    return send_file(

        arquivo,

        as_attachment=True,

        download_name="relatorio_calcados_brilho_negro.pdf",

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

    # ==========================================
    # VIAGENS
    # ==========================================

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


    # ==========================================
    # INTEGRANTES APROVADOS E ATIVOS
    # ==========================================

    integrantes = db.execute(
        text("""
            SELECT
                id,
                codigo_integrante,
                nome,
                cidade,
                status,
                situacao

            FROM integrantes

            WHERE TRIM(status) = 'APROVADO'
            AND TRIM(situacao) = 'ATIVO'

            ORDER BY nome
        """)
    ).mappings().all()


    # ==========================================
    # INTEGRANTES JÁ SELECIONADOS POR VIAGEM
    # ==========================================

    selecionados = db.execute(
        text("""
            SELECT
                viagem_id,
                integrante_id

            FROM viagem_integrantes
        """)
    ).mappings().all()


    selecionados_por_viagem = {}

    for item in selecionados:

        viagem_id = item["viagem_id"]
        integrante_id = item["integrante_id"]

        if viagem_id not in selecionados_por_viagem:
            selecionados_por_viagem[viagem_id] = []

        selecionados_por_viagem[viagem_id].append(
            integrante_id
        )


    db.close()


    return render_template(
        "admin/viagens.html",
        viagens=lista,
        integrantes=integrantes,
        selecionados_por_viagem=selecionados_por_viagem
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


    return redirect("/admin/viagens")

@app.route(
    "/admin/viagem/<int:viagem_id>/integrante/<int:integrante_id>/remover",
    methods=["POST"]
)
def remover_integrante_viagem(viagem_id, integrante_id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        db.execute(
            text("""
                DELETE FROM viagem_integrantes
                WHERE viagem_id = :viagem_id
                AND integrante_id = :integrante_id
            """),
            {
                "viagem_id": viagem_id,
                "integrante_id": integrante_id
            }
        )

        db.commit()

    finally:

        db.close()

    return redirect(
        f"/admin/viagem/{viagem_id}"
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
                i.id,
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

@app.route(
    "/admin/viagem/<int:viagem_id>/integrante/<int:integrante_id>/termo"
)
def termo_individual_viagem(viagem_id, integrante_id):

    if "admin" not in session:
        return redirect("/login")

    return gerar_documentos_viagem(
        viagem_id,
        integrante_id
    )

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

@app.route("/admin/financeiro/excluir/<int:id>", methods=["POST"])
def excluir_movimentacao_financeiro(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    db.execute(
        text("""
            DELETE FROM financeiro
            WHERE id = :id
        """),
        {
            "id": id
        }
    )


    db.commit()

    db.close()


    return redirect("/admin/financeiro/movimentacoes")

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

@app.route("/admin/rifas")
def rifas():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    try:

        lista_rifas = db.execute(
            text("""
                SELECT

                    r.id,
                    r.nome,
                    r.premio,
                    r.valor_numero,
                    r.quantidade_por_integrante,
                    r.data_sorteio,
                    r.status,

                    t.nome AS temporada_nome

                FROM rifas r

                LEFT JOIN temporadas t
                ON t.id = r.temporada_id

                ORDER BY r.id DESC

            """)
        ).mappings().all()



        temporadas = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    ano,
                    status

                FROM temporadas

                WHERE status='ATIVA'

                ORDER BY ano DESC

            """)
        ).mappings().all()



        return render_template(
            "admin/rifas.html",
            rifas=lista_rifas,
            temporadas=temporadas
        )


    finally:

        db.close()

@app.route("/admin/rifas/nova", methods=["GET","POST"])
def nova_rifa():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    try:

        if request.method == "POST":


            valor = request.form["valor_numero"]

            valor = valor.replace(",", ".")


            db.execute(
                text("""
                    INSERT INTO rifas
                    (
                        nome,
                        premio,
                        valor_numero,
                        quantidade_por_integrante,
                        data_sorteio,
                        observacao,
                        temporada_id
                    )

                    VALUES
                    (
                        :nome,
                        :premio,
                        :valor_numero,
                        :quantidade_por_integrante,
                        :data_sorteio,
                        :observacao,
                        :temporada_id
                    )
                """),
                {

                    "nome": request.form["nome"],

                    "premio": request.form["premio"],

                    "valor_numero": valor,


                    "quantidade_por_integrante":
                        request.form["quantidade_por_integrante"],


                    "data_sorteio":
                        request.form["data_sorteio"],


                    "observacao":
                        request.form["observacao"],


                    "temporada_id":
                        request.form["temporada_id"]

                }
            )


            db.commit()


            return redirect("/admin/rifas?novo=ok")


        return render_template(
            "admin/nova_rifa.html"
        )


    finally:

        db.close()

@app.route("/admin/rifas/<int:id>/editar", methods=["POST"])
def editar_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR RIFA
        # ==========================================

        rifa = db.execute(
            text("""
                SELECT
                    id,
                    status
                FROM rifas
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()

        if not rifa:
            return "Rifa não encontrada", 404


        # ==========================================
        # PEGAR DADOS DO FORMULÁRIO
        # ==========================================

        nome = request.form.get("nome", "").strip()

        premio = request.form.get("premio", "").strip()

        valor_numero = request.form.get(
            "valor_numero",
            ""
        ).strip()

        data_sorteio = request.form.get(
            "data_sorteio",
            ""
        ).strip()

        observacao = request.form.get(
            "observacao",
            ""
        ).strip()

        temporada_id = request.form.get(
            "temporada_id",
            ""
        ).strip()


        # ==========================================
        # VALIDAR CAMPOS OBRIGATÓRIOS
        # ==========================================

        if not nome:

            return "O nome da rifa é obrigatório.", 400


        if not premio:

            return "O prêmio da rifa é obrigatório.", 400


        if not valor_numero:

            return "O valor do número é obrigatório.", 400


        if not temporada_id:

            return "A temporada é obrigatória.", 400


        # ==========================================
        # CONVERTER VALOR
        # ==========================================

        try:

            valor_numero = valor_numero.replace(
                ",",
                "."
            )

            valor_numero = Decimal(
                valor_numero
            )

        except Exception:

            return (
                "Valor do número inválido."
            ), 400

        # ==========================================
        # ATUALIZAR RIFA
        # ==========================================

        db.execute(
            text("""
                UPDATE rifas

                SET
                    nome = :nome,
                    premio = :premio,
                    valor_numero = :valor_numero,
                    data_sorteio = :data_sorteio,
                    observacao = :observacao,
                    temporada_id = :temporada_id

                WHERE id = :id
            """),
            {
                "nome": nome,
                "premio": premio,
                "valor_numero": valor_numero,
                "data_sorteio": data_sorteio or None,
                "observacao": observacao,
                "temporada_id": temporada_id,
                "id": id
            }
        )


        # ==========================================
        # SALVAR
        # ==========================================

        db.commit()


        return redirect(
            "/admin/rifas?editado=ok"
        )


    except Exception as e:

        db.rollback()

        print(
            "=========================================="
        )

        print(
            "ERRO AO EDITAR RIFA:"
        )

        print(e)

        print(
            "=========================================="
        )

        raise


    finally:

        db.close() 

@app.route("/admin/temporadas/nova", methods=["POST"])
def nova_temporada():

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    db.execute(
        text("""
            INSERT INTO temporadas
            (
                nome,
                ano,
                status
            )

            VALUES
            (
                :nome,
                :ano,
                :status
            )
        """),
        {
            "nome": request.form["nome"],
            "ano": request.form["ano"],
            "status": request.form["status"]
        }
    )


    db.commit()
    db.close()


    return redirect("/admin")

@app.route("/admin/rifas/excluir/<int:id>", methods=["POST"])
def excluir_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    db.execute(
        text("""
            DELETE FROM rifas
            WHERE id = :id
        """),
        {
            "id": id
        }
    )

    db.commit()
    db.close()

    return redirect("/admin/rifas?excluido=ok")

@app.route("/admin/rifas/<int:id>")
def detalhes_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # =====================================================
        # DADOS DA RIFA
        # =====================================================

        rifa = db.execute(
            text("""
                SELECT
                    r.id,
                    r.nome,
                    r.premio,
                    r.valor_numero,
                    r.quantidade_por_integrante,
                    r.data_sorteio,
                    r.status,
                    r.observacao,

                    r.numero_sorteado,
                    r.vendedor_sorteado_id,
                    r.data_sorteio_realizado,

                    t.nome AS temporada_nome

                                FROM rifas r

                                LEFT JOIN temporadas t
                                    ON t.id = r.temporada_id

                                WHERE r.id = :id
                            """),
                            {
                                "id": id
                            }
                        ).mappings().first()


        if not rifa:
            return redirect("/admin/rifas")


        # =====================================================
        # RESUMO DOS NÚMEROS
        # =====================================================

        resumo_numeros = db.execute(
            text("""
                SELECT

                    COUNT(*) AS total_numeros,

                    COUNT(*) FILTER (
                        WHERE status = 'VENDIDO'
                    ) AS numeros_vendidos,

                    COUNT(*) FILTER (
                        WHERE status = 'DISPONIVEL'
                    ) AS numeros_disponiveis,

                    COUNT(*) FILTER (
                        WHERE status = 'DEVOLVIDO'
                    ) AS numeros_devolvidos

                FROM rifas_numeros

                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": id
            }
        ).mappings().first()


        # =====================================================
        # RESUMO FINANCEIRO
        # =====================================================

        resumo_financeiro = db.execute(
            text("""
                SELECT

                    COALESCE(
                        SUM(valor_devido),
                        0
                    ) AS valor_vendido,

                    COALESCE(
                        SUM(valor_entregue),
                        0
                    ) AS valor_recebido,

                    COALESCE(
                        SUM(saldo_pendente),
                        0
                    ) AS valor_pendente

                FROM rifas_integrantes

                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": id
            }
        ).mappings().first()


        # =====================================================
        # RESUMO DOS VENDEDORES
        # =====================================================

        resumo_vendedores = db.execute(
            text("""
                SELECT

                    COUNT(*) AS total_vendedores,

                    COUNT(*) FILTER (
                        WHERE status_prestacao = 'PRESTADO'
                    ) AS vendedores_prestados,

                    COUNT(*) FILTER (
                        WHERE status_prestacao = 'PENDENTE'
                    ) AS vendedores_pendentes,

                    COUNT(*) FILTER (
                        WHERE status_prestacao = 'PARCIAL'
                    ) AS vendedores_parciais

                FROM rifas_integrantes

                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": id
            }
        ).mappings().first()


        # =====================================================
        # PERCENTUAL VENDIDO
        # =====================================================

        total_numeros = (
            resumo_numeros["total_numeros"] or 0
        )

        numeros_vendidos = (
            resumo_numeros["numeros_vendidos"] or 0
        )


        if total_numeros > 0:

            percentual_vendido = (
                numeros_vendidos
                / total_numeros
            ) * 100

        else:

            percentual_vendido = 0

        # =====================================================
        # NÚMEROS DA RIFA
        # =====================================================

        numeros = db.execute(
            text("""
                SELECT
                    rn.id,
                    rn.numero,
                    rn.status,
                    rn.data_venda,
                    rn.observacao,

                    rn.integrante_id,

                    i.nome AS vendedor_nome

                FROM rifas_numeros rn

                LEFT JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id

                ORDER BY rn.numero
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()    


        # =====================================================
        # RANKING DOS VENDEDORES
        # =====================================================

        vendedores = db.execute(
            text("""
                SELECT

                    ri.id,
                    ri.integrante_id,

                    i.nome,
                    i.funcao,

                    ri.quantidade_numeros,
                    ri.quantidade_vendida,
                    ri.quantidade_devolvida,

                    ri.valor_devido,
                    ri.valor_entregue,
                    ri.saldo_pendente,

                    ri.status_prestacao,
                    ri.status

                FROM rifas_integrantes ri

                JOIN integrantes i
                    ON i.id = ri.integrante_id

                WHERE ri.rifa_id = :rifa_id

                ORDER BY
                    ri.quantidade_vendida DESC,
                    i.nome
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()

        vendedor_sorteado_nome = None

        if rifa["vendedor_sorteado_id"]:

            vendedor_sorteado = db.execute(
                text("""
                    SELECT nome
                    FROM integrantes
                    WHERE id = :id
                """),
                {
                    "id": rifa["vendedor_sorteado_id"]
                }
            ).mappings().first()

            if vendedor_sorteado:
                vendedor_sorteado_nome = vendedor_sorteado["nome"]

        # =====================================================
        # ABRIR DASHBOARD
        # =====================================================

        return render_template(
            "admin/detalhes_rifa.html",

            rifa=rifa,
            resumo_numeros=resumo_numeros,
            resumo_financeiro=resumo_financeiro,
            resumo_vendedores=resumo_vendedores,
            percentual_vendido=percentual_vendido,
            vendedores=vendedores,
            numeros=numeros,
            vendedor_sorteado_nome=vendedor_sorteado_nome
        )


    finally:

        db.close()

@app.route("/admin/rifas/<int:id>/vendedores")
def vendedores_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==============================
        # BUSCAR RIFA
        # ==============================

        rifa = db.execute(
            text("""
                SELECT
                    *
                FROM rifas
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().fetchone()


        if not rifa:
            return "Rifa não encontrada", 404


        # ==============================
        # VERIFICAR SE ESTÁ FINALIZADA
        # ==============================

        rifa_finalizada = (
            rifa["status"] != "ATIVA"
        )


        # ==============================
        # BUSCAR INTEGRANTES ATIVOS
        # ==============================

        integrantes = db.execute(
            text("""
                SELECT
                    i.id,
                    i.nome,
                    i.funcao
                FROM integrantes i
                WHERE i.status = 'APROVADO'
                AND i.situacao = 'ATIVO'

                AND NOT EXISTS (
                    SELECT 1
                    FROM rifas_integrantes ri
                    WHERE ri.rifa_id = :rifa_id
                    AND ri.integrante_id = i.id
                )

                ORDER BY i.nome
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # ==============================
        # BUSCAR VENDEDORES DA RIFA
        # ==============================

        vendedores = db.execute(
            text("""
                SELECT

                    ri.id,
                    ri.integrante_id,

                    ri.quantidade_numeros,
                    ri.quantidade_vendida,
                    ri.quantidade_devolvida,

                    ri.valor_recebido,
                    ri.valor_devido,
                    ri.valor_entregue,
                    ri.saldo_pendente,

                    ri.status,
                    ri.status_prestacao,
                    ri.data_prestacao,
                    ri.observacao,

                    i.nome,
                    i.funcao

                FROM rifas_integrantes ri

                JOIN integrantes i
                    ON i.id = ri.integrante_id

                WHERE ri.rifa_id = :rifa_id

                ORDER BY i.nome
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # ==============================
        # BUSCAR NÚMEROS DA RIFA
        # ==============================

        numeros = db.execute(
            text("""
                SELECT
                    rn.id,
                    rn.rifa_id,
                    rn.integrante_id,
                    rn.numero,
                    rn.status,
                    rn.data_venda,
                    rn.observacao,

                    i.nome AS vendedor

                FROM rifas_numeros rn

                LEFT JOIN integrantes i
                    ON i.codigo_integrante = rn.integrante_id::text

                WHERE rn.rifa_id = :rifa_id

                ORDER BY rn.numero
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # ==============================
        # ASSOCIAR NÚMEROS A CADA VENDEDOR
        # ==============================

        vendedores = [
            dict(vendedor)
            for vendedor in vendedores
        ]


        for vendedor in vendedores:

            vendedor["numeros"] = [
                numero
                for numero in numeros
                if numero["integrante_id"]
                == vendedor["integrante_id"]
            ]


        # ==============================
        # RESUMO DA RIFA
        # ==============================

        resumo = db.execute(
            text("""
                SELECT

                    COUNT(id) AS total_vendedores,

                    COALESCE(
                        SUM(quantidade_numeros),
                        0
                    ) AS numeros_distribuidos,

                    COALESCE(
                        SUM(quantidade_vendida),
                        0
                    ) AS numeros_vendidos,

                    COALESCE(
                        SUM(valor_recebido),
                        0
                    ) AS valor_recebido

                FROM rifas_integrantes

                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": id
            }
        ).mappings().fetchone()


        # ==============================
        # VENDEDORES JÁ VINCULADOS
        # ==============================

        participantes = db.execute(
            text("""
                SELECT
                    integrante_id

                FROM rifas_integrantes

                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": id
            }
        ).scalars().all()


        # ==============================
        # ABRIR PAINEL
        # ==============================

        return render_template(
            "admin/vendedores_rifa.html",

            rifa=rifa,

            integrantes=integrantes,

            participantes=participantes,

            vendedores=vendedores,

            resumo=resumo,

            rifa_finalizada=rifa_finalizada
        )


    finally:

        db.close()

@app.route("/admin/rifas/<int:rifa_id>/vendedores", methods=["POST"])
def salvar_vendedores_rifa(rifa_id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # VERIFICAR SE A RIFA EXISTE
        # ==========================================

        rifa = db.execute(
            text("""
                SELECT
                    id,
                    status
                FROM rifas
                WHERE id = :rifa_id
            """),
            {
                "rifa_id": rifa_id
            }
        ).mappings().fetchone()

        if not rifa:
            return "Rifa não encontrada", 404

        # ==========================================
        # VERIFICAR STATUS DA RIFA
        # ==========================================

        if rifa["status"] != "ATIVA":

            return redirect(
                f"/admin/rifas/{rifa_id}?erro=rifa_finalizada"
            )

        # ==========================================
        # INTEGRANTES SELECIONADOS
        # ==========================================

        integrantes = request.form.getlist("integrantes")


        # ==========================================
        # DESCOBRIR O PRÓXIMO NÚMERO DA RIFA
        # ==========================================

        maior_numero = db.execute(
            text("""
                SELECT
                    COALESCE(MAX(numero), 0)
                FROM rifas_numeros
                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": rifa_id
            }
        ).scalar()

        proximo_numero = int(maior_numero) + 1


        # ==========================================
        # PROCESSAR CADA INTEGRANTE
        # ==========================================

        for integrante_id in integrantes:

            quantidade = request.form.get(
                f"quantidade_{integrante_id}"
            )

            if not quantidade:
                continue


            quantidade = int(quantidade)


            if quantidade <= 0:
                continue


            # ======================================
            # VERIFICAR SE JÁ EXISTE
            # ======================================

            existente = db.execute(
                text("""
                    SELECT
                        id,
                        quantidade_numeros
                    FROM rifas_integrantes
                    WHERE rifa_id = :rifa_id
                    AND integrante_id = :integrante_id
                """),
                {
                    "rifa_id": rifa_id,
                    "integrante_id": integrante_id
                }
            ).mappings().fetchone()


            # ======================================
            # VENDEDOR JÁ EXISTE
            # ======================================

            if existente:

                quantidade_atual = (
                    existente.quantidade_numeros or 0
                )


                # ----------------------------------
                # JÁ POSSUI A QUANTIDADE SOLICITADA
                # ----------------------------------

                if quantidade <= quantidade_atual:

                    continue


                # ----------------------------------
                # AUMENTOU A QUANTIDADE
                # ----------------------------------

                quantidade_nova = (
                    quantidade
                    -
                    quantidade_atual
                )


                # Atualiza a quantidade distribuída

                db.execute(
                    text("""
                        UPDATE rifas_integrantes

                        SET
                            quantidade_numeros =
                                :quantidade

                        WHERE id = :id
                    """),
                    {
                        "quantidade": quantidade,
                        "id": existente.id
                    }
                )


                # ----------------------------------
                # GERAR SOMENTE OS NOVOS NÚMEROS
                # ----------------------------------

                for _ in range(quantidade_nova):

                    db.execute(
                        text("""
                            INSERT INTO rifas_numeros
                            (
                                rifa_id,
                                integrante_id,
                                numero,
                                status
                            )

                            VALUES
                            (
                                :rifa_id,
                                :integrante_id,
                                :numero,
                                'DISPONIVEL'
                            )
                        """),
                        {
                            "rifa_id": rifa_id,
                            "integrante_id": integrante_id,
                            "numero": proximo_numero
                        }
                    )


                    proximo_numero += 1


                continue


            # ======================================
            # NOVO VENDEDOR
            # ======================================

            novo_vendedor = db.execute(
                text("""
                    INSERT INTO rifas_integrantes
                    (
                        rifa_id,
                        integrante_id,
                        quantidade_numeros,
                        quantidade_vendida,
                        valor_recebido,
                        status,
                        status_prestacao
                    )

                    VALUES
                    (
                        :rifa_id,
                        :integrante_id,
                        :quantidade,
                        0,
                        0,
                        'ATIVO',
                        'PENDENTE'
                    )

                    RETURNING id
                """),
                {
                    "rifa_id": rifa_id,
                    "integrante_id": integrante_id,
                    "quantidade": quantidade
                }
            ).scalar()


            # ======================================
            # GERAR NÚMEROS DO NOVO VENDEDOR
            # ======================================

            for _ in range(quantidade):

                db.execute(
                    text("""
                        INSERT INTO rifas_numeros
                        (
                            rifa_id,
                            integrante_id,
                            numero,
                            status
                        )

                        VALUES
                        (
                            :rifa_id,
                            :integrante_id,
                            :numero,
                            'DISPONIVEL'
                        )
                    """),
                    {
                        "rifa_id": rifa_id,
                        "integrante_id": integrante_id,
                        "numero": proximo_numero
                    }
                )


                proximo_numero += 1


        # ==========================================
        # SALVAR
        # ==========================================

        db.commit()


        return redirect(
            f"/admin/rifas/{rifa_id}/vendedores"
        )


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()

@app.route("/admin/rifas/vendedor/<int:id>/remover")
def remover_vendedor_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        vendedor = db.execute(
            text("""
                SELECT
                    ri.id,
                    ri.rifa_id,
                    r.status AS status_rifa
                FROM rifas_integrantes ri
                JOIN rifas r
                    ON r.id = ri.rifa_id
                WHERE ri.id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()

        if not vendedor:
            return "Vendedor não encontrado", 404

        if vendedor["status_rifa"] != "ATIVA":
            return (
                "Esta rifa está finalizada "
                "e não permite remover vendedores."
            ), 400

        db.execute(
            text("""
                DELETE FROM rifas_integrantes
                WHERE id = :id
            """),
            {
                "id": id
            }
        )

        db.commit()

        return redirect(request.referrer)

    except Exception as e:

        db.rollback()

        return f"Erro: {e}"

    finally:

        db.close()

@app.route("/admin/rifas/vendedor/<int:id>/prestacao")
def prestacao_vendedor(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    try:

        prestacao = db.execute(
            text("""
                SELECT

                    ri.id,
                    ri.quantidade_numeros,
                    ri.quantidade_vendida,
                    ri.valor_recebido,
                    ri.status_prestacao,

                    i.nome,
                    i.funcao,

                    r.nome AS rifa_nome,
                    r.valor_numero,

                    t.nome AS temporada_nome

                FROM rifas_integrantes ri


                JOIN integrantes i
                ON i.id = ri.integrante_id


                JOIN rifas r
                ON r.id = ri.rifa_id


                LEFT JOIN temporadas t
                ON t.id = r.temporada_id


                WHERE ri.id = :id

            """),
            {
                "id": id
            }
        ).mappings().fetchone()



        return render_template(
            "admin/prestacao_vendedor.html",
            prestacao=prestacao
        )


    finally:

        db.close()

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

@app.route("/admin/rifas/vendedor/<int:id>/prestar-conta")
def prestar_conta(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR VENDEDOR
        # ==========================================

        vendedor = db.execute(
            text("""
                SELECT

                    ri.id,
                    ri.rifa_id,
                    ri.integrante_id,

                    ri.quantidade_numeros,
                    ri.quantidade_vendida,
                    ri.quantidade_devolvida,

                    ri.valor_recebido,
                    ri.valor_devido,
                    ri.valor_entregue,
                    ri.saldo_pendente,

                    ri.status_prestacao,
                    ri.data_prestacao,
                    ri.observacao,

                    i.nome,
                    i.funcao,

                    r.nome AS rifa_nome,
                    r.valor_numero,

                    t.nome AS temporada_nome

                FROM rifas_integrantes ri

                JOIN integrantes i
                    ON i.id = ri.integrante_id

                JOIN rifas r
                    ON r.id = ri.rifa_id

                LEFT JOIN temporadas t
                    ON t.id = r.temporada_id

                WHERE ri.id = :id
            """),
            {
                "id": id
            }
        ).mappings().fetchone()


        if not vendedor:
            return "Vendedor não encontrado", 404


        # ==========================================
        # BUSCAR NÚMEROS DO VENDEDOR
        # ==========================================

        numeros = db.execute(
            text("""
                SELECT

                    id,
                    numero,
                    status,
                    data_venda,
                    observacao

                FROM rifas_numeros

                WHERE rifa_id = :rifa_id
                AND integrante_id = :integrante_id

                ORDER BY numero
            """),
            {
                "rifa_id": vendedor["rifa_id"],
                "integrante_id": vendedor["integrante_id"]
            }
        ).mappings().all()


        # ==========================================
        # ABRIR TELA
        # ==========================================

        return render_template(
            "admin/prestar_conta.html",
            vendedor=vendedor,
            numeros=numeros
        )


    finally:

        db.close()

 
@app.route("/admin/rifas/vendedor/<int:id>/prestar-conta", methods=["POST"])
def salvar_prestacao(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR VENDEDOR
        # ==========================================

        prestacao = db.execute(
            text("""
                SELECT
                    ri.id,
                    ri.rifa_id,
                    ri.integrante_id,
                    ri.quantidade_numeros,
                    r.valor_numero

                FROM rifas_integrantes ri

                JOIN rifas r
                    ON r.id = ri.rifa_id

                WHERE ri.id = :id
            """),
            {
                "id": id
            }
        ).mappings().fetchone()


        if not prestacao:
            return "Prestação não encontrada", 404

        status_rifa = db.execute(
            text("""
                SELECT status
                FROM rifas
                WHERE id = :rifa_id
            """),
            {
                "rifa_id": prestacao["rifa_id"]
            }
        ).scalar()

        if status_rifa != "ATIVA":
            return (
                "Esta rifa está finalizada "
                "e não permite novas prestações."
            ), 400


        # ==========================================
        # NÚMEROS MARCADOS COMO VENDIDOS
        # ==========================================

        numeros_vendidos_ids = request.form.getlist(
            "numeros_vendidos"
        )


        numeros_vendidos_ids = [
            int(numero_id)
            for numero_id in numeros_vendidos_ids
        ]


        quantidade_vendida = len(
            numeros_vendidos_ids
        )


        # ==========================================
        # VALIDAR QUANTIDADE
        # ==========================================

        if quantidade_vendida > prestacao.quantidade_numeros:

            return (
                "Quantidade de números vendidos "
                "não pode ser maior que a quantidade distribuída."
            )


        # ==========================================
        # VALOR ENTREGUE
        # ==========================================

        valor_entregue = Decimal(
            request.form.get(
                "valor_entregue",
                "0"
            ).replace(",", ".")
            or "0"
        )


        if valor_entregue < 0:

            return "Valor entregue inválido"


        observacao = request.form.get(
            "observacao",
            ""
        )


        # ==========================================
        # VALOR DAS VENDAS
        # ==========================================

        valor_devido = (
            Decimal(quantidade_vendida)
            *
            Decimal(str(prestacao.valor_numero))
        )


        # ==========================================
        # VALOR ENTREGUE NÃO PODE SER MAIOR
        # ==========================================

        if valor_entregue > valor_devido:

            return (
                f"O valor entregue "
                f"(R$ {valor_entregue:.2f}) "
                f"não pode ser maior que o valor "
                f"dos números vendidos "
                f"(R$ {valor_devido:.2f})."
            )


        # ==========================================
        # QUANTIDADE DEVOLVIDA
        # ==========================================

        quantidade_devolvida = (
            prestacao.quantidade_numeros
            -
            quantidade_vendida
        )


        # ==========================================
        # SALDO
        # ==========================================

        saldo_pendente = (
            valor_devido
            -
            valor_entregue
        )


        # ==========================================
        # STATUS
        # ==========================================

        if valor_devido == 0:

            status_prestacao = "PRESTADO"

        elif valor_entregue >= valor_devido:

            status_prestacao = "PRESTADO"

        elif valor_entregue > 0:

            status_prestacao = "PARCIAL"

        else:

            status_prestacao = "PENDENTE"


        # ==========================================
        # BUSCAR TODOS OS NÚMEROS DO VENDEDOR
        # ==========================================

        # ==========================================
        # BUSCAR NÚMEROS
        # ==========================================

        numeros = db.execute(
            text("""
                SELECT
                    rn.id,
                    rn.rifa_id,
                    rn.integrante_id,
                    rn.numero,
                    rn.status,
                    rn.data_venda,
                    rn.observacao,

                    i.nome AS vendedor

                FROM rifas_numeros rn

                LEFT JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id
                AND rn.integrante_id = :integrante_id

                ORDER BY rn.numero
            """),
            {
                "rifa_id": prestacao["rifa_id"],
                "integrante_id": prestacao["integrante_id"]
            }
        ).mappings().all()


        # ==========================================
        # VALIDAR QUANTIDADE
        # ==========================================

        if len(numeros) != prestacao.quantidade_numeros:

            return (
                "A quantidade de números cadastrados "
                "para este vendedor está inconsistente."
            )


        # ==========================================
        # ATUALIZAR CADA NÚMERO
        # ==========================================

        for numero in numeros:

            if numero["id"] in numeros_vendidos_ids:

                # ------------------------------
                # VENDIDO
                # ------------------------------

                db.execute(
                    text("""
                        UPDATE rifas_numeros

                        SET
                            status = 'VENDIDO',
                            data_venda = CURRENT_TIMESTAMP,
                            observacao = :observacao

                        WHERE id = :numero_id
                    """),
                    {
                        "numero_id": numero.id,
                        "observacao": observacao
                    }
                )

            else:

                # ------------------------------
                # DEVOLVIDO
                # ------------------------------

                db.execute(
                    text("""
                        UPDATE rifas_numeros

                        SET
                            status = 'DEVOLVIDO',
                            data_venda = NULL,
                            observacao = :observacao

                        WHERE id = :numero_id
                    """),
                    {
                        "numero_id": numero.id,
                        "observacao": observacao
                    }
                )


        # ==========================================
        # ATUALIZAR PRESTAÇÃO
        # ==========================================

        db.execute(
            text("""
                UPDATE rifas_integrantes

                SET

                    quantidade_vendida =
                        :quantidade_vendida,

                    quantidade_devolvida =
                        :quantidade_devolvida,

                    valor_recebido =
                        :valor_entregue,

                    valor_devido =
                        :valor_devido,

                    valor_entregue =
                        :valor_entregue,

                    saldo_pendente =
                        :saldo_pendente,

                    observacao =
                        :observacao,

                    data_prestacao =
                        CURRENT_TIMESTAMP,

                    status_prestacao =
                        :status_prestacao

                WHERE id = :id
            """),
            {
                "quantidade_vendida":
                    quantidade_vendida,

                "quantidade_devolvida":
                    quantidade_devolvida,

                "valor_entregue":
                    valor_entregue,

                "valor_devido":
                    valor_devido,

                "saldo_pendente":
                    saldo_pendente,

                "observacao":
                    observacao,

                "status_prestacao":
                    status_prestacao,

                "id": id
            }
        )




        # ==========================================
        # SALVAR
        # ==========================================

        db.commit()


        return redirect(
            f"/admin/rifas/{prestacao.rifa_id}/vendedores"
        )


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()

@app.route("/admin/rifas/<int:id>/finalizar", methods=["POST"])
def finalizar_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR RIFA
        # ==========================================

        rifa = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    status
                FROM rifas
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().fetchone()

        if not rifa:
            return "Rifa não encontrada", 404


        # ==========================================
        # VERIFICAR STATUS
        # ==========================================

        if rifa["status"] != "ATIVA":

            return (
                "Esta rifa não está ativa "
                "e não pode ser finalizada."
            ), 400


        # ==========================================
        # VERIFICAR PRESTAÇÕES
        # ==========================================

        pendencias = db.execute(
            text("""
                SELECT
                    ri.id,
                    i.nome,
                    ri.saldo_pendente,
                    ri.status_prestacao

                FROM rifas_integrantes ri

                JOIN integrantes i
                    ON i.id = ri.integrante_id

                WHERE ri.rifa_id = :rifa_id

                AND (
                    ri.status_prestacao <> 'PRESTADO'
                    OR COALESCE(ri.saldo_pendente, 0) > 0
                )

                ORDER BY i.nome
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # ==========================================
        # NÃO PERMITIR FINALIZAÇÃO COM PENDÊNCIA
        # ==========================================

        if pendencias:

            nomes = ", ".join(
                p["nome"]
                for p in pendencias
            )

            return (
                f"Não é possível finalizar a rifa. "
                f"Existem prestações pendentes: {nomes}."
            ), 400


        # ==========================================
        # FINALIZAR
        # ==========================================

        db.execute(
            text("""
                UPDATE rifas

                SET status = 'FINALIZADA'

                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        db.commit()


        return redirect(
            f"/admin/rifas/{id}?finalizada=ok"
        )


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


@app.route("/admin/rifas/<int:id>/numeros")
def numeros_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # =====================================================
        # BUSCAR RIFA
        # =====================================================

        rifa = db.execute(
            text("""
                SELECT

                    r.id,
                    r.nome,
                    r.premio,
                    r.valor_numero,
                    r.status,
                    r.data_sorteio,

                    t.nome AS temporada_nome

                FROM rifas r

                LEFT JOIN temporadas t
                    ON t.id = r.temporada_id

                WHERE r.id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()


        if not rifa:

            return "Rifa não encontrada", 404


        # =====================================================
        # BUSCAR NÚMEROS
        # =====================================================

        numeros = db.execute(
            text("""
                SELECT

                    rn.id,
                    rn.numero,
                    rn.status,
                    rn.data_venda,
                    rn.observacao,

                    rn.integrante_id,

                    i.nome AS vendedor_nome,
                    i.funcao AS vendedor_funcao

                FROM rifas_numeros rn

                LEFT JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id

                ORDER BY rn.numero
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # =====================================================
        # RESUMO
        # =====================================================

        resumo = db.execute(
            text("""
                SELECT

                    COUNT(*) AS total,

                    COUNT(*) FILTER (
                        WHERE status = 'VENDIDO'
                    ) AS vendidos,

                    COUNT(*) FILTER (
                        WHERE status = 'DISPONIVEL'
                    ) AS disponiveis,

                    COUNT(*) FILTER (
                        WHERE status = 'DEVOLVIDO'
                    ) AS devolvidos

                FROM rifas_numeros

                WHERE rifa_id = :rifa_id
            """),
            {
                "rifa_id": id
            }
        ).mappings().first()


        # =====================================================
        # VENDEDORES
        # =====================================================

        vendedores = db.execute(
            text("""
                SELECT DISTINCT

                    i.id,
                    i.nome

                FROM rifas_numeros rn

                JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id

                ORDER BY i.nome
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # =====================================================
        # PERCENTUAL VENDIDO
        # =====================================================

        total = resumo["total"] or 0
        vendidos = resumo["vendidos"] or 0

        if total > 0:

            percentual_vendido = (
                vendidos / total
            ) * 100

        else:

            percentual_vendido = 0


        # =====================================================
        # ABRIR TELA
        # =====================================================

        return render_template(
            "admin/numeros_rifa.html",

            rifa=rifa,

            numeros=numeros,

            resumo=resumo,

            vendedores=vendedores,

            percentual_vendido=percentual_vendido
        )


    finally:

        db.close()
           

@app.route("/admin/rifas/<int:id>/sortear", methods=["POST"])
def sortear_rifa(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR RIFA
        # ==========================================

        rifa = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    status,
                    numero_sorteado,
                    vendedor_sorteado_id,
                    data_sorteio_realizado
                FROM rifas
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()

        if not rifa:
            return "Rifa não encontrada", 404


        # ==========================================
        # IMPEDIR NOVO SORTEIO
        # ==========================================

        if rifa["numero_sorteado"] is not None:

            return redirect(
                f"/admin/rifas/{id}?erro=sorteio_realizado"
            )


        # ==========================================
        # SÓ PODE SORTEAR RIFA FINALIZADA
        # ==========================================

        if rifa["status"] != "FINALIZADA":

            return redirect(
                f"/admin/rifas/{id}?erro=rifa_nao_finalizada"
            )


        # ==========================================
        # BUSCAR SOMENTE NÚMEROS VENDIDOS
        # ==========================================

        numeros_vendidos = db.execute(
            text("""
                SELECT
                    rn.id,
                    rn.numero,
                    rn.integrante_id,
                    i.nome,
                    i.funcao

                FROM rifas_numeros rn

                JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id
                AND rn.status = 'VENDIDO'

                ORDER BY rn.numero
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()


        # ==========================================
        # VERIFICAR SE EXISTEM NÚMEROS VENDIDOS
        # ==========================================

        if not numeros_vendidos:

            return redirect(
                f"/admin/rifas/{id}?erro=sem_numeros_vendidos"
            )


        # ==========================================
        # REALIZAR SORTEIO
        # ==========================================

        import random

        numero_sorteado = random.choice(
            numeros_vendidos
        )


        # ==========================================
        # REGISTRAR RESULTADO
        # ==========================================

        db.execute(
            text("""
                UPDATE rifas

                SET
                    numero_sorteado = :numero,
                    vendedor_sorteado_id = :vendedor_id,
                    data_sorteio_realizado = CURRENT_TIMESTAMP

                WHERE id = :rifa_id
            """),
            {
                "numero": numero_sorteado["numero"],
                "vendedor_id": numero_sorteado["integrante_id"],
                "rifa_id": id
            }
        )


        db.commit()


        return redirect(
            f"/admin/rifas/{id}?sorteio=ok"
        )


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()

@app.route("/admin/rifas/<int:id>/gerar-pdf")
def gerar_pdf_rifa_admin(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR RIFA
        # ==========================================

        rifa = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    premio,
                    valor_numero,
                    data_sorteio,
                    status
                FROM rifas
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()

        if not rifa:
            return "Rifa não encontrada", 404

        # ==========================================
        # BUSCAR NÚMEROS
        # ==========================================

        numeros = db.execute(
            text("""
                SELECT
                    rn.id,
                    rn.numero,
                    rn.status,
                    rn.integrante_id,
                    i.nome AS vendedor_nome
                FROM rifas_numeros rn

                LEFT JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id

                ORDER BY
                    COALESCE(i.nome, 'SEM VENDEDOR'),
                    rn.numero
            """),
            {
                "rifa_id": id
            }
        ).mappings().all()

        # ==========================================
        # GERAR PDF
        # ==========================================

        pdf = gerar_pdf_rifa(
            rifa,
            numeros
        )

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"rifa_{rifa['nome']}.pdf"
        )

    finally:

        db.close()        

@app.route("/admin/rifas/<int:rifa_id>/vendedor/<int:integrante_id>/gerar-pdf")
def gerar_pdf_rifa_vendedor(rifa_id, integrante_id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR RIFA
        # ==========================================

        rifa = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    premio,
                    valor_numero,
                    data_sorteio,
                    status
                FROM rifas
                WHERE id = :rifa_id
            """),
            {
                "rifa_id": rifa_id
            }
        ).mappings().first()

        if not rifa:
            return "Rifa não encontrada", 404


        # ==========================================
        # VERIFICAR SE O VENDEDOR PERTENCE À RIFA
        # ==========================================

        vendedor = db.execute(
            text("""
                SELECT
                    ri.id,
                    ri.integrante_id,
                    i.nome
                FROM rifas_integrantes ri

                JOIN integrantes i
                    ON i.id = ri.integrante_id

                WHERE ri.rifa_id = :rifa_id
                AND ri.integrante_id = :integrante_id
            """),
            {
                "rifa_id": rifa_id,
                "integrante_id": integrante_id
            }
        ).mappings().first()

        if not vendedor:
            return "Vendedor não encontrado nesta rifa", 404


        # ==========================================
        # BUSCAR SOMENTE OS NÚMEROS DO VENDEDOR
        # ==========================================

        numeros = db.execute(
            text("""
                SELECT
                    rn.id,
                    rn.numero,
                    rn.status,
                    rn.integrante_id,
                    i.nome AS vendedor_nome

                FROM rifas_numeros rn

                LEFT JOIN integrantes i
                    ON i.id = rn.integrante_id

                WHERE rn.rifa_id = :rifa_id
                AND rn.integrante_id = :integrante_id

                ORDER BY rn.numero
            """),
            {
                "rifa_id": rifa_id,
                "integrante_id": integrante_id
            }
        ).mappings().all()


        if not numeros:
            return "Nenhum número encontrado para este vendedor", 404


        # ==========================================
        # GERAR PDF
        # ==========================================

        pdf = gerar_pdf_rifa(
            rifa,
            numeros
        )


        # ==========================================
        # ENVIAR PDF
        # ==========================================

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=(
                f"rifa_{rifa['nome']}_"
                f"{vendedor['nome']}.pdf"
            )
        )


    finally:

        db.close()

@app.route("/admin/carteirinha/pdf/<int:id>")
def baixar_carteirinha_pdf(id):

    if "admin" not in session:
        return redirect("/login")

    return gerar_pdf_carteirinha(id)

@app.route("/admin/carteirinha/pdf/todas")
def baixar_todas_carteirinhas_pdf():

    if "admin" not in session:
        return redirect("/login")

    return gerar_pdf_todas_carteirinhas()    

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)