from flask import Flask, render_template, request, redirect, session, jsonify
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from urllib.parse import quote
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
from werkzeug.security import check_password_hash, generate_password_hash
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

# =====================================================
# CONTROLE DE ACESSO POR PERFIL
# =====================================================

PERMISSOES_PERFIS = {

    "ADMIN": {
        "admin",
        "integrantes",
        "inscricoes",
        "carteirinhas",
        "instrumentos",
        "patrimonio",
        "ensaios",
        "viagens",
        "rifas",
        "financeiro",
        "temporadas",
        "relatorios",
        "usuarios",
        "configuracoes",
    },

    "GESTAO": {
        "admin",
        "integrantes",
        "inscricoes",
        "carteirinhas",
        "instrumentos",
        "patrimonio",
        "ensaios",
        "viagens",
        "rifas",
        "financeiro",
        "temporadas",
        "relatorios",
    },

    "OPERADOR": {
        "admin",
        "integrantes",
        "inscricoes",
        "carteirinhas",
        "instrumentos",
        "patrimonio",
        "ensaios",
        "viagens",
        "rifas",
    },

    "CONSULTA": {
        "admin",
        "integrantes",
        "carteirinhas",
        "instrumentos",
        "patrimonio",
        "relatorios",
    }

}


def usuario_tem_permissao(modulo):

    if "usuario_id" not in session:
        return False

    perfil = session.get("perfil")

    permissoes = PERMISSOES_PERFIS.get(perfil, set())

    return modulo in permissoes

from functools import wraps


def requer_permissao(modulo):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            # Usuário não está logado
            if "usuario_id" not in session:

                return redirect("/login")


            # Usuário sem permissão
            if not usuario_tem_permissao(modulo):

                return redirect("/admin")


            return func(*args, **kwargs)

        return wrapper

    return decorator

@app.template_filter('moeda')
def moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =====================================================
# FUNÇÕES DA BANDA
# =====================================================

FUNCOES_BANDA = [
    ("Músico", "🎺 Músico"),
    ("Corpo Coreográfico", "💃 Corpo Coreográfico"),
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

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"].strip()

        senha = request.form["senha"]

        db = SessionLocal()

        try:

            resultado = db.execute(
                text("""
                    SELECT
                        id,
                        usuario,
                        senha,
                        nome,
                        perfil,
                        ativo
                    FROM usuarios
                    WHERE usuario = :usuario
                """),
                {
                    "usuario": usuario
                }
            ).fetchone()


            # ==========================================
            # USUÁRIO NÃO ENCONTRADO
            # ==========================================

            if not resultado:

                return render_template(
                    "admin/login.html",
                    erro="Usuário ou senha inválidos"
                )


            # ==========================================
            # VERIFICAR SENHA
            # ==========================================

            if not check_password_hash(
                resultado.senha,
                senha
            ):

                return render_template(
                    "admin/login.html",
                    erro="Usuário ou senha inválidos"
                )


            # ==========================================
            # VERIFICAR USUÁRIO ATIVO
            # ==========================================

            if not resultado.ativo:

                return render_template(
                    "admin/login.html",
                    erro="Este usuário está inativo."
                )


            # ==========================================
            # CRIAR SESSÃO
            # ==========================================

            session["admin"] = True

            session["usuario"] = resultado.usuario

            session["usuario_id"] = resultado.id

            session["nome_usuario"] = resultado.nome

            session["perfil"] = resultado.perfil


            # ==========================================
            # ENTRAR NO DASHBOARD
            # ==========================================

            return redirect("/admin")


        finally:

            db.close()


    return render_template(
        "admin/login.html"
    )

@app.route("/admin/usuarios")
def usuarios_admin():

    if not usuario_tem_permissao("usuarios"):
        return redirect("/admin")

    db = SessionLocal()

    try:

        usuarios = db.execute(
            text("""
                SELECT
                    id,
                    usuario,
                    nome,
                    perfil,
                    ativo,
                    criado_em
                FROM usuarios
                ORDER BY nome
            """)
        ).fetchall()

        return render_template(
            "admin/usuarios.html",
            usuarios=usuarios
        )

    finally:

        db.close()

@app.route("/admin/usuarios/novo", methods=["POST"])
def novo_usuario():

    if not usuario_tem_permissao("usuarios"):
        return redirect("/admin")

    nome = request.form.get("nome", "").strip()
    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "")
    perfil = request.form.get("perfil", "").strip()
    ativo = request.form.get("ativo") == "on"

    # ==========================================
    # VALIDAÇÕES
    # ==========================================

    if not nome or not usuario or not senha or not perfil:

        return redirect("/admin/usuarios")


    db = SessionLocal()

    try:

        # ==========================================
        # VERIFICAR SE USUÁRIO JÁ EXISTE
        # ==========================================

        existente = db.execute(
            text("""
                SELECT id
                FROM usuarios
                WHERE LOWER(usuario) = LOWER(:usuario)
            """),
            {
                "usuario": usuario
            }
        ).fetchone()


        if existente:

            return redirect("/admin/usuarios")


        # ==========================================
        # CRIPTOGRAFAR SENHA
        # ==========================================

        senha_hash = generate_password_hash(senha)


        # ==========================================
        # CADASTRAR
        # ==========================================

        db.execute(
            text("""
                INSERT INTO usuarios (
                    usuario,
                    senha,
                    nome,
                    perfil,
                    ativo,
                    criado_em
                )
                VALUES (
                    :usuario,
                    :senha,
                    :nome,
                    :perfil,
                    :ativo,
                    CURRENT_TIMESTAMP
                )
            """),
            {
                "usuario": usuario,
                "senha": senha_hash,
                "nome": nome,
                "perfil": perfil,
                "ativo": ativo
            }
        )


        db.commit()


        return redirect("/admin/usuarios")


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()            

@app.route("/admin/usuarios/<int:id>/status", methods=["POST"])
def alterar_status_usuario(id):

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        usuario = db.execute(
            text("""
                SELECT id, ativo
                FROM usuarios
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).fetchone()

        if not usuario:
            return redirect("/admin/usuarios")

        # Inverte o status atual
        novo_status = not usuario.ativo

        db.execute(
            text("""
                UPDATE usuarios
                SET ativo = :ativo
                WHERE id = :id
            """),
            {
                "ativo": novo_status,
                "id": id
            }
        )

        db.commit()

        return redirect("/admin/usuarios")

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

@app.route("/admin/usuarios/<int:id>/editar", methods=["POST"])
def editar_usuario(id):

    if "admin" not in session:
        return redirect("/login")

    nome = request.form.get("nome", "").strip()
    usuario = request.form.get("usuario", "").strip()
    perfil = request.form.get("perfil", "").strip()
    senha = request.form.get("senha", "")

    if not nome or not usuario or not perfil:
        return redirect("/admin/usuarios")

    db = SessionLocal()

    try:

        # ==========================================
        # VERIFICAR SE OUTRO USUÁRIO USA O MESMO LOGIN
        # ==========================================

        existente = db.execute(
            text("""
                SELECT id
                FROM usuarios
                WHERE LOWER(usuario) = LOWER(:usuario)
                AND id <> :id
            """),
            {
                "usuario": usuario,
                "id": id
            }
        ).fetchone()

        if existente:
            return redirect("/admin/usuarios")


        # ==========================================
        # ATUALIZAR SEM TROCAR SENHA
        # ==========================================

        if not senha:

            db.execute(
                text("""
                    UPDATE usuarios
                    SET
                        nome = :nome,
                        usuario = :usuario,
                        perfil = :perfil
                    WHERE id = :id
                """),
                {
                    "nome": nome,
                    "usuario": usuario,
                    "perfil": perfil,
                    "id": id
                }
            )


        # ==========================================
        # ATUALIZAR COM NOVA SENHA
        # ==========================================

        else:

            senha_hash = generate_password_hash(senha)

            db.execute(
                text("""
                    UPDATE usuarios
                    SET
                        nome = :nome,
                        usuario = :usuario,
                        perfil = :perfil,
                        senha = :senha
                    WHERE id = :id
                """),
                {
                    "nome": nome,
                    "usuario": usuario,
                    "perfil": perfil,
                    "senha": senha_hash,
                    "id": id
                }
            )


        db.commit()

        return redirect("/admin/usuarios")

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    if not session.get("usuario_id"):
        session.clear()
        return redirect("/login")


    mensagem_instrumento = request.args.get(
        "instrumento_msg"
    )

    tipo_mensagem_instrumento = request.args.get(
        "instrumento_tipo"
    )

    abrir_instrumentos = request.args.get(
        "abrir_instrumentos"
    )

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


        ativos = db.execute(
            text("""
                SELECT COUNT(*)
                FROM integrantes
                WHERE status = 'APROVADO'
                AND situacao = 'ATIVO'
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
        # INSTRUMENTOS
        # ==========================================

        instrumentos = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    ativo,
                    data_cadastro
                FROM instrumentos
                ORDER BY LOWER(nome)
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

        # RESUMO
        total=total,
        pendentes=pendentes,
        aprovados=aprovados,
        ativos=ativos,

        # TEMPORADAS
        temporadas=temporadas,

        # ANIVERSARIANTES
        aniversariantes=aniversariantes,
        mes_nome=mes_nome,

        # INSCRIÇÕES
        status_inscricoes=status_inscricoes,

        # CARTEIRINHAS
        integrantes_carteirinhas=integrantes_carteirinhas,

        # INSTRUMENTOS
        instrumentos=instrumentos,

        # MENSAGENS
        mensagem_instrumento=mensagem_instrumento,
        tipo_mensagem_instrumento=tipo_mensagem_instrumento,
        abrir_instrumentos=abrir_instrumentos
    )

@app.route("/admin/patrimonio")
def patrimonio():

    if not usuario_tem_permissao("patrimonio"):
        return redirect("/admin")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR INSTRUMENTOS
        # ==========================================

        instrumentos = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    ativo
                FROM instrumentos
                ORDER BY
                    ativo DESC,
                    nome ASC
            """)
        ).mappings().all()


        # ==========================================
        # RESUMO
        # ==========================================

        total_instrumentos = len(instrumentos)

        instrumentos_ativos = sum(
            1
            for instrumento in instrumentos
            if instrumento["ativo"]
        )

        instrumentos_inativos = (
            total_instrumentos
            - instrumentos_ativos
        )


        # ==========================================
        # ABRIR PATRIMÔNIO
        # ==========================================

        return render_template(
            "admin/patrimonio.html",

            instrumentos=instrumentos,

            total_instrumentos=total_instrumentos,

            instrumentos_ativos=instrumentos_ativos,

            instrumentos_inativos=instrumentos_inativos
        )


    except Exception as e:

        print(
            "ERRO AO ABRIR PATRIMÔNIO:",
            e
        )

        return "Erro ao carregar o módulo de patrimônio.", 500


    finally:

        db.close()

@app.route("/admin/instrumentos/novo", methods=["POST"])
def novo_instrumento():

    if not usuario_tem_permissao("instrumentos"):
        return jsonify({
            "sucesso": False,
            "mensagem": "Não autorizado."
        }), 403


    nome = request.form.get("nome", "").strip()


    # ==========================================
    # VALIDAR NOME
    # ==========================================

    if not nome:

        return jsonify({
            "sucesso": False,
            "mensagem": "Informe o nome do instrumento."
        })


    db = SessionLocal()


    try:

        # ==========================================
        # VERIFICAR SE JÁ EXISTE
        # ==========================================

        existente = db.execute(
            text("""
                SELECT id
                FROM instrumentos
                WHERE LOWER(nome) = LOWER(:nome)
                LIMIT 1
            """),
            {
                "nome": nome
            }
        ).scalar()


        if existente:

            return jsonify({
                "sucesso": False,
                "mensagem": f'O instrumento "{nome}" já está cadastrado.'
            })


        # ==========================================
        # CADASTRAR
        # ==========================================

        instrumento = db.execute(
            text("""
                INSERT INTO instrumentos (
                    nome,
                    ativo
                )
                VALUES (
                    :nome,
                    TRUE
                )
                RETURNING id, nome, ativo
            """),
            {
                "nome": nome
            }
        ).mappings().first()


        db.commit()


        return jsonify({
            "sucesso": True,
            "mensagem": f'Instrumento "{instrumento["nome"]}" cadastrado com sucesso.',
            "instrumento": {
                "id": instrumento["id"],
                "nome": instrumento["nome"],
                "ativo": instrumento["ativo"]
            }
        })


    except Exception as e:

        db.rollback()

        print(
            "ERRO AO CADASTRAR INSTRUMENTO:",
            e
        )


        return jsonify({
            "sucesso": False,
            "mensagem": "Erro ao cadastrar o instrumento."
        }), 500


    finally:

        db.close()

@app.route("/admin/instrumentos/<int:id>/editar", methods=["POST"])
def editar_instrumento(id):

    if not usuario_tem_permissao("instrumentos"):
        return jsonify({
            "sucesso": False,
            "mensagem": "Não autorizado."
        }), 403


    nome = request.form.get("nome", "").strip()


    # ==========================================
    # VALIDAR NOME
    # ==========================================

    if not nome:

        return jsonify({
            "sucesso": False,
            "mensagem": "Informe o nome do instrumento."
        })


    db = SessionLocal()


    try:

        # ==========================================
        # VERIFICAR SE O INSTRUMENTO EXISTE
        # ==========================================

        instrumento_atual = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    ativo
                FROM instrumentos
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()


        if not instrumento_atual:

            return jsonify({
                "sucesso": False,
                "mensagem": "Instrumento não encontrado."
            })


        # ==========================================
        # VERIFICAR DUPLICIDADE
        # ==========================================

        existente = db.execute(
            text("""
                SELECT id
                FROM instrumentos
                WHERE LOWER(nome) = LOWER(:nome)
                AND id <> :id
                LIMIT 1
            """),
            {
                "nome": nome,
                "id": id
            }
        ).scalar()


        if existente:

            return jsonify({
                "sucesso": False,
                "mensagem": f'O instrumento "{nome}" já está cadastrado.'
            })


        # ==========================================
        # ATUALIZAR
        # ==========================================

        db.execute(
            text("""
                UPDATE instrumentos
                SET nome = :nome
                WHERE id = :id
            """),
            {
                "nome": nome,
                "id": id
            }
        )


        db.commit()


        return jsonify({
            "sucesso": True,
            "mensagem": f'Instrumento alterado para "{nome}" com sucesso.',
            "instrumento": {
                "id": id,
                "nome": nome,
                "ativo": instrumento_atual["ativo"]
            }
        })


    except Exception as e:

        db.rollback()

        print(
            "ERRO AO EDITAR INSTRUMENTO:",
            e
        )


        return jsonify({
            "sucesso": False,
            "mensagem": "Erro ao editar o instrumento."
        }), 500


    finally:

        db.close()

@app.route("/admin/instrumentos/<int:id>/alternar", methods=["POST"])
def alternar_instrumento(id):

    if not usuario_tem_permissao("instrumentos"):
        return jsonify({
            "sucesso": False,
            "mensagem": "Não autorizado."
        }), 403


    db = SessionLocal()


    try:

        # ==========================================
        # BUSCAR INSTRUMENTO
        # ==========================================

        instrumento = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    ativo
                FROM instrumentos
                WHERE id = :id
            """),
            {
                "id": id
            }
        ).mappings().first()


        if not instrumento:

            return jsonify({
                "sucesso": False,
                "mensagem": "Instrumento não encontrado."
            }), 404


        # ==========================================
        # RECEBER A AÇÃO SOLICITADA
        # ==========================================

        dados = request.get_json(silent=True) or {}

        ativar = dados.get("ativar")


        # ==========================================
        # SE NÃO VEIO PELO JSON,
        # INVERTE O STATUS ATUAL
        # ==========================================

        if ativar is None:

            novo_status = not instrumento["ativo"]

        else:

            novo_status = bool(ativar)


        # ==========================================
        # ATUALIZAR BANCO
        # ==========================================

        db.execute(
            text("""
                UPDATE instrumentos
                SET ativo = :ativo
                WHERE id = :id
            """),
            {
                "ativo": novo_status,
                "id": id
            }
        )


        db.commit()


        # ==========================================
        # MENSAGEM
        # ==========================================

        if novo_status:

            mensagem = (
                f'Instrumento "{instrumento["nome"]}" '
                'ativado com sucesso.'
            )

        else:

            mensagem = (
                f'Instrumento "{instrumento["nome"]}" '
                'inativado com sucesso.'
            )


        # ==========================================
        # RESPOSTA
        # ==========================================

        return jsonify({
            "sucesso": True,
            "mensagem": mensagem,
            "ativo": novo_status,
            "nome": instrumento["nome"],
            "id": instrumento["id"]
        })


    except Exception as e:

        db.rollback()

        print(
            "ERRO AO ALTERAR STATUS DO INSTRUMENTO:",
            e
        )


        return jsonify({
            "sucesso": False,
            "mensagem": "Erro ao alterar o status do instrumento."
        }), 500


    finally:

        db.close()

@app.route("/integrantes")
def integrantes():

    if "usuario_id" not in session:
        return redirect("/login")

    if not usuario_tem_permissao("integrantes"):
        return redirect("/admin")

    db = SessionLocal()

    try:

        # ==========================================
        # LISTA DE INTEGRANTES
        # ==========================================

        integrantes = db.execute(
            text("""
                SELECT
                    i.*,
                    ins.nome AS instrumento_nome
                FROM integrantes i
                LEFT JOIN instrumentos ins
                    ON ins.id = i.instrumento_id
                ORDER BY i.id DESC
            """)
        ).fetchall()


        # ==========================================
        # LISTA DE INSTRUMENTOS
        # ==========================================

        instrumentos = db.execute(
            text("""
                SELECT id, nome
                FROM instrumentos
                WHERE ativo = TRUE
                ORDER BY nome
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


        ativos = db.execute(
            text("""
                SELECT COUNT(*)
                FROM integrantes
                WHERE status = 'APROVADO'
                AND situacao = 'ATIVO'
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
        ativos=ativos,
        inativos=inativos,
        instrumentos=instrumentos
    )

@app.route("/admin/integrante/<int:id>")
def ver_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    db = SessionLocal()


    try:

        integrante = db.execute(
            text("""
                SELECT
                    i.*,
                    ins.nome AS instrumento_nome
                FROM integrantes i
                LEFT JOIN instrumentos ins
                    ON ins.id = i.instrumento_id
                WHERE i.id = :id
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

    if not usuario_tem_permissao("inscricoes"):
        return redirect("/admin")

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

        return redirect("/admin/inscricoes")

    except Exception as e:

        db.rollback()

        print(
            "ERRO AO ALTERAR STATUS DAS INSCRIÇÕES:",
            e
        )

        return f"Erro ao alterar status: {e}", 500

    finally:

        db.close()

@app.route("/admin/inscricoes")
def admin_inscricoes():

    if not usuario_tem_permissao("inscricoes"):
        return redirect("/admin")

    db = SessionLocal()

    try:

        resultado = db.execute(
            text("""
                SELECT valor
                FROM configuracoes
                WHERE chave = 'inscricoes_status'
            """)
        ).scalar()

        status_inscricoes = resultado or "FECHADA"

        return render_template(
            "admin/inscricoes.html",
            status_inscricoes=status_inscricoes
        )

    except Exception as e:

        print(
            "ERRO AO CARREGAR STATUS DAS INSCRIÇÕES:",
            e
        )

        return f"Erro ao carregar inscrições: {e}", 500

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

                funcao=:funcao,
                instrumento_id=:instrumento_id

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
                "funcao": request.form.get("funcao"),
                "instrumento_id": request.form.get("instrumento_id") or None
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

    instrumentos = db.execute(
        text("""
            SELECT id, nome
            FROM instrumentos
            WHERE ativo = TRUE
            ORDER BY nome
        """)
    ).fetchall()

    db.close()


    return render_template(
        "admin/editar.html",
        integrante=integrante,
        funcoes_banda=FUNCOES_BANDA,
        instrumentos=instrumentos
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
    # FILTROS
    # ==============================

    status_filtro = request.args.get("status")
    situacao_filtro = request.args.get("situacao")
    funcao_filtro = request.args.get("funcao")
    instrumento_filtro = request.args.get("instrumento")

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

    # ==============================
    # BUSCAR INTEGRANTES
    # ==============================

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

    # ==============================
    # DISTRIBUIÇÃO POR FUNÇÃO
    # ==============================

    distribuicao_funcao = {}

    for pessoa in integrantes:

        funcao = (
            pessoa["funcao"]
            or
            "Integrantes sem função definida"
        )

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

    # ==============================
    # IMPORTS DO REPORTLAB
    # ==============================

    from reportlab.platypus import (
        Image,
        HRFlowable,
        Table,
        TableStyle,
        Paragraph,
        Spacer
    )

    from reportlab.lib.styles import ParagraphStyle

    # ==============================
    # LOGO
    # ==============================

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

        "<b>Relatório de Integrantes</b>",

        estilos["Heading2"]

    )

    elementos.append(subtitulo)

    elementos.append(
        Spacer(1, 15)
    )

    # ==============================
    # DATA
    # ==============================

    data_geracao = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    # ==============================
    # ESTILOS DOS RESUMOS
    # ==============================

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

    # ==============================
    # FILTROS APLICADOS
    # ==============================

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

    # ==============================
    # NOME DO INSTRUMENTO
    # ==============================

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

        filtros_html.append(
            f"<b>Instrumento:</b> "
            f"{instrumento_nome or instrumento_filtro}"
        )

    if not filtros_html:

        filtros_html.append(
            "<b>Filtros:</b> Todos"
        )

    texto_filtros = "<br/>".join(
        filtros_html
    )

    # Agora podemos fechar o banco
    db.close()

    # ==============================
    # RESUMO DOS RESULTADOS
    # ==============================

    texto_resultados = f"""

        <b>Resultados da consulta</b><br/>

        Total apresentado:
        <b>{total_apresentado}</b>

    """

    # ==============================
    # RESUMO EM 3 COLUNAS
    # ==============================

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

        TableStyle(

            [

                (

                    "BOX",

                    (0, 0),

                    (-1, -1),

                    0.5,

                    colors.grey

                ),

                (

                    "INNERGRID",

                    (0, 0),

                    (-1, -1),

                    0.5,

                    colors.lightgrey

                ),

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

                    8

                ),

                (

                    "BOTTOMPADDING",

                    (0, 0),

                    (-1, -1),

                    8

                )

            ]

        )

    )

    elementos.append(
        tabela_resumo
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ==============================
    # DISTRIBUIÇÃO POR FUNÇÃO
    # ==============================

    elementos.append(

        Paragraph(

            "<b>Distribuição por Função</b>",

            estilo_resumo_titulo

        )

    )

    elementos.append(
        Spacer(1, 6)
    )

    funcoes_lista = [

        f"<b>{funcao}</b>: {quantidade}"

        for funcao, quantidade
        in distribuicao_funcao.items()

    ]

    colunas_funcoes = [

        [],
        [],
        []

    ]

    for indice, funcao in enumerate(funcoes_lista):

        colunas_funcoes[
            indice % 3
        ].append(funcao)

    funcoes_colunas = []

    for coluna in colunas_funcoes:

        if coluna:

            funcoes_colunas.append(

                Paragraph(

                    "<br/>".join(coluna),

                    estilo_funcao

                )

            )

        else:

            funcoes_colunas.append(

                Paragraph(

                    "",

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

        TableStyle(

            [

                (

                    "BOX",

                    (0, 0),

                    (-1, -1),

                    0.5,

                    colors.grey

                ),

                (

                    "INNERGRID",

                    (0, 0),

                    (-1, -1),

                    0.5,

                    colors.lightgrey

                ),

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

            ]

        )

    )

    elementos.append(
        tabela_funcoes
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ==============================
    # ESTILOS DA TABELA
    # ==============================

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

    # ==============================
    # DADOS DA TABELA
    # ==============================

    dados = [

        [

            Paragraph(
                "Código",
                estilo_cabecalho
            ),

            Paragraph(
                "Integrante",
                estilo_cabecalho
            ),

            Paragraph(
                "CPF",
                estilo_cabecalho
            ),

            Paragraph(
                "Data nascimento",
                estilo_cabecalho
            ),

            Paragraph(
                "Cidade/UF",
                estilo_cabecalho
            ),

            Paragraph(
                "Função",
                estilo_cabecalho
            ),

            Paragraph(
                "Instrumento",
                estilo_cabecalho
            ),

            Paragraph(
                "Status",
                estilo_cabecalho
            )

        ]

    ]

    for pessoa in integrantes:

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

        dados.append(

            [

                Paragraph(

                    str(
                        pessoa["codigo_integrante"]
                        or "-"
                    ),

                    estilo_centro

                ),

                Paragraph(

                    (
                        pessoa["nome"]
                        or "-"
                    ).title(),

                    estilo_tabela

                ),

                Paragraph(

                    str(
                        pessoa["cpf"]
                        or "-"
                    ),

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

                    pessoa["funcao"]
                    or "-",

                    estilo_centro

                ),

                Paragraph(

                    pessoa["instrumento"]
                    or "-",

                    estilo_centro

                ),

                Paragraph(

                    pessoa["status"]
                    or "-",

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

            45,   # Código
            120,  # Integrante
            70,   # CPF
            65,   # Data nascimento
            75,   # Cidade/UF
            60,   # Função
            75,   # Instrumento
            50    # Status

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

                    "TOP"

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

    where = ""

    if condicoes:
        where = "WHERE " + " AND ".join(condicoes)

    # ==============================
    # TOTAL ANTES DA EXCLUSÃO
    # ==============================

    total_localizado = db.execute(

        text(f"""
            SELECT COUNT(*)
            FROM integrantes
            {where}
        """),

        parametros

    ).scalar()

    # ==============================
    # BUSCAR INTEGRANTES
    # ==============================

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
    # IMPORTS
    # ==============================

    from reportlab.platypus import (
        Image,
        HRFlowable,
        Table,
        TableStyle,
        Paragraph,
        Spacer
    )

    from reportlab.lib.styles import ParagraphStyle

    # ==============================
    # LOGO
    # ==============================

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
        Spacer(1, 10)
    )

    # ==============================
    # ESTILOS
    # ==============================

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

    # ==============================
    # DATA
    # ==============================

    data_geracao = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    # ==============================
    # FILTROS
    # ==============================

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

    texto_filtros = "<br/>".join(
        filtros_html
    )

    # ==============================
    # EXCLUSÃO
    # ==============================

    if excluir_funcao:

        texto_exclusao = f"""

            <b>Função excluída:</b><br/>

            {excluir_funcao}

        """

    else:

        texto_exclusao = """

            <b>Nenhuma função excluída</b>

        """

    # ==============================
    # RESULTADO
    # ==============================

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

    # ==============================
    # RESUMO EM 3 COLUNAS
    # ==============================

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

            ]

        )

    )

    elementos.append(
        tabela_resumo
    )

    elementos.append(
        Spacer(1, 18)
    )

    # =====================================================
    # AGRUPAMENTO POR FUNÇÃO E TAMANHO
    # =====================================================

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

    # ==============================
    # ORDENAR TAMANHOS
    # ==============================

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

    # ==============================
    # TÍTULO DA SEÇÃO
    # ==============================

    elementos.append(

        Paragraph(

            "<b>Distribuição de Calçados por Função</b>",

            estilo_resumo_cabecalho

        )

    )

    elementos.append(
        Spacer(1, 10)
    )

    # ==============================
    # UMA TABELA PARA CADA FUNÇÃO
    # ==============================

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

        elementos.append(
            Spacer(1, 5)
        )

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

            dados_funcao.append(

                [

                    Paragraph(
                        str(calcado),
                        estilo_centro
                    ),

                    Paragraph(
                        f"<b>{quantidade}</b>",
                        estilo_centro
                    )

                ]

            )

        # ==============================
        # TOTAL DA FUNÇÃO
        # ==============================

        dados_funcao.append(

            [

                Paragraph(
                    "<b>TOTAL</b>",
                    estilo_centro
                ),

                Paragraph(
                    f"<b>{total_funcao}</b>",
                    estilo_centro
                )

            ]

        )

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

                ]

            )

        )

        elementos.append(
            tabela_funcao
        )

        elementos.append(
            Spacer(1, 12)
        )

    # ==============================
    # LISTA DE INTEGRANTES
    # ==============================

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(

        Paragraph(

            "<b>Lista de Integrantes</b>",

            estilo_resumo_cabecalho

        )

    )

    elementos.append(
        Spacer(1, 8)
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

                    str(
                        pessoa["codigo_integrante"]
                    ),

                    estilo_centro

                ),

                Paragraph(

                    (
                        pessoa["nome"] or ""
                    ).title(),

                    estilo_tabela

                ),

                Paragraph(

                    str(
                        pessoa["calcado"]
                    )

                    if pessoa["calcado"]

                    else "-",

                    estilo_centro

                )

            ]

        )

    # ==============================
    # TABELA DE INTEGRANTES
    # ==============================

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

    elementos.append(
        tabela
    )

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

    elementos.append(
        rodape
    )

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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")

    return gerar_documentos_viagem(id)

@app.route(
    "/admin/viagem/<int:viagem_id>/integrante/<int:integrante_id>/termo"
)
def termo_individual_viagem(viagem_id, integrante_id):

    if not usuario_tem_permissao("viagens"):
        return redirect("/admin")

    return gerar_documentos_viagem(
        viagem_id,
        integrante_id
    )



@app.route("/admin/financeiro")
def financeiro():

    if not usuario_tem_permissao("financeiro"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("financeiro"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("financeiro"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("financeiro"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("financeiro"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

@app.route("/admin/rifas/<int:rifa_id>/exportar/pdf/vendedores")
def exportar_pdf_vendedores(rifa_id):

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

    db = SessionLocal()

    try:

        # =====================================================
        # BUSCAR RIFA
        # =====================================================

        rifa = db.execute(
            text("""
                SELECT
                    *
                FROM rifas
                WHERE id = :id
            """),
            {
                "id": rifa_id
            }
        ).mappings().fetchone()

        if not rifa:
            return "Rifa não encontrada", 404


        # =====================================================
        # FILTRO
        # =====================================================

        status_prestacao = request.args.get(
            "status_prestacao"
        )


        # =====================================================
        # BUSCAR VENDEDORES
        # =====================================================

        condicoes = [
            "ri.rifa_id = :rifa_id"
        ]

        parametros = {
            "rifa_id": rifa_id
        }


        if status_prestacao:

            condicoes.append(
                "ri.status_prestacao = :status_prestacao"
            )

            parametros["status_prestacao"] = (
                status_prestacao
            )


        where = " AND ".join(condicoes)


        vendedores = db.execute(
            text(f"""
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

                WHERE {where}

                ORDER BY
                    LOWER(i.nome)
            """),
            parametros
        ).mappings().all()


        # =====================================================
        # RESUMOS
        # =====================================================

        total_vendedores = len(vendedores)

        total_vendidos = sum(
            (v["quantidade_vendida"] or 0)
            for v in vendedores
        )

        total_valor_vendido = sum(
            (v["valor_devido"] or 0)
            for v in vendedores
        )

        total_valor_entregue = sum(
            (v["valor_entregue"] or 0)
            for v in vendedores
        )

        total_saldo = sum(
            (v["saldo_pendente"] or 0)
            for v in vendedores
        )


        # =====================================================
        # CONTAGEM POR STATUS
        # =====================================================

        quantidade_prestados = sum(
            1
            for v in vendedores
            if v["status_prestacao"] == "PRESTADO"
        )

        quantidade_parciais = sum(
            1
            for v in vendedores
            if v["status_prestacao"] == "PARCIAL"
        )

        quantidade_pendentes = sum(
            1
            for v in vendedores
            if v["status_prestacao"] == "PENDENTE"
        )


        # =====================================================
        # FECHAR BANCO
        # =====================================================

        db.close()


        # =====================================================
        # CRIAR PDF
        # =====================================================

        arquivo = BytesIO()

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


        pdf = SimpleDocTemplate(

            arquivo,

            pagesize=A4,

            topMargin=25,
            bottomMargin=30,
            leftMargin=25,
            rightMargin=25

        )


        elementos = []

        estilos = getSampleStyleSheet()


        # =====================================================
        # ESTILOS
        # =====================================================

        estilo_resumo = ParagraphStyle(

            "ResumoVendedores",

            parent=estilos["Normal"],

            fontSize=8.5,
            leading=11

        )


        estilo_resumo_cabecalho = ParagraphStyle(

            "ResumoCabecalhoVendedores",

            parent=estilos["Normal"],

            fontSize=8,
            leading=10,

            alignment=1,

            fontName="Helvetica-Bold"

        )


        estilo_titulo = ParagraphStyle(

            "TituloVendedores",

            parent=estilos["Title"],

            fontSize=18,
            leading=21,

            alignment=1,

            fontName="Helvetica-Bold"

        )


        estilo_tabela = ParagraphStyle(

            "TabelaVendedores",

            parent=estilos["Normal"],

            fontSize=7.5,
            leading=9

        )


        estilo_cabecalho = ParagraphStyle(

            "CabecalhoVendedores",

            parent=estilos["Normal"],

            fontSize=7.5,
            leading=9,

            alignment=1,

            fontName="Helvetica-Bold"

        )


        estilo_centro = ParagraphStyle(

            "CentroVendedores",

            parent=estilos["Normal"],

            fontSize=7.5,
            leading=9,

            alignment=1

        )


        estilo_direita = ParagraphStyle(

            "DireitaVendedores",

            parent=estilos["Normal"],

            fontSize=7.5,
            leading=9,

            alignment=2

        )


        # =====================================================
        # LOGO
        # =====================================================

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


        # =====================================================
        # TÍTULO
        # =====================================================

        elementos.append(

            Paragraph(

                "<b>BRILHO NEGRO</b><br/>"
                "<font size='14'>"
                "Sistema de Gestão de Integrantes"
                "</font>",

                estilos["Title"]

            )

        )

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


        elementos.append(

            Paragraph(

                "<b>Relatório de Vendedores da Rifa</b>",

                estilos["Heading2"]

            )

        )

        elementos.append(
            Spacer(1, 5)
        )


        # =====================================================
        # NOME DA RIFA
        # =====================================================

        elementos.append(

            Paragraph(

                f"<b>Rifa:</b> {rifa['nome']}",

                estilo_resumo

            )

        )

        elementos.append(
            Spacer(1, 10)
        )


        # =====================================================
        # DATA
        # =====================================================

        data_geracao = datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )


        # =====================================================
        # FILTROS
        # =====================================================

        if status_prestacao:

            filtros_html = (

                "<b>Status da prestação:</b> "
                f"{status_prestacao}"

            )

        else:

            filtros_html = (

                "<b>Status da prestação:</b> "
                "Todos"

            )


        # =====================================================
        # RESULTADO
        # =====================================================

        texto_resultado = f"""

            <b>Total de vendedores:</b>
            {total_vendedores}

            <br/>

            <b>Prestados:</b>
            {quantidade_prestados}

            <br/>

            <b>Parciais:</b>
            {quantidade_parciais}

            <br/>

            <b>Pendentes:</b>
            {quantidade_pendentes}

        """


        # =====================================================
        # RIFA
        # =====================================================

        texto_rifa = f"""

            <b>Rifa:</b>
            {rifa['nome']}

            <br/>

            <b>Status:</b>
            {rifa['status']}

            <br/>

            <b>Valor por número:</b>
            R$ {float(rifa['valor_numero'] or 0):,.2f}

        """


        texto_rifa = texto_rifa.replace(
            ",",
            "X"
        ).replace(
            ".",
            ","
        ).replace(
            "X",
            "."
        )


        # =====================================================
        # RESUMO EM 3 COLUNAS
        # =====================================================

        dados_resumo = [

            [

                Paragraph(
                    "FILTROS APLICADOS",
                    estilo_resumo_cabecalho
                ),

                Paragraph(
                    "RIFA",
                    estilo_resumo_cabecalho
                ),

                Paragraph(
                    "RESULTADO",
                    estilo_resumo_cabecalho
                )

            ],

            [

                Paragraph(
                    filtros_html,
                    estilo_resumo
                ),

                Paragraph(
                    texto_rifa,
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

                175,
                175,
                175

            ]

        )


        tabela_resumo.setStyle(

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

                ]

            )

        )


        elementos.append(
            tabela_resumo
        )

        elementos.append(
            Spacer(1, 18)
        )


        # =====================================================
        # TÍTULO DA TABELA
        # =====================================================

        elementos.append(

            Paragraph(

                "<b>Lista de Vendedores</b>",

                estilo_resumo_cabecalho

            )

        )

        elementos.append(
            Spacer(1, 8)
        )


        # =====================================================
        # DADOS DA TABELA
        # =====================================================

        dados = [

            [

                Paragraph(
                    "Nº",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Vendedor",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Função",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Vendidos",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Valor vendido",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Valor entregue",
                    estilo_cabecalho
                ),

                Paragraph(
                    "Saldo",
                    estilo_cabecalho
                )

            ]

        ]


        # =====================================================
        # LINHAS
        # =====================================================

        for numero, vendedor in enumerate(
            vendedores,
            start=1
        ):

            nome = (
                vendedor["nome"] or ""
            ).title()


            funcao = (
                vendedor["funcao"]
                or "-"
            )


            vendidos = (
                vendedor["quantidade_vendida"]
                or 0
            )


            valor_vendido = (
                vendedor["valor_devido"]
                or 0
            )


            valor_entregue = (
                vendedor["valor_entregue"]
                or 0
            )


            saldo = (
                vendedor["saldo_pendente"]
                or 0
            )


            dados.append(

                [

                    Paragraph(
                        str(numero),
                        estilo_centro
                    ),

                    Paragraph(
                        nome,
                        estilo_tabela
                    ),

                    Paragraph(
                        str(funcao),
                        estilo_tabela
                    ),

                    Paragraph(
                        f"<b>{vendidos}</b>",
                        estilo_centro
                    ),

                    Paragraph(
                        f"R$ {float(valor_vendido):,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        estilo_direita
                    ),

                    Paragraph(
                        f"R$ {float(valor_entregue):,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        estilo_direita
                    ),

                    Paragraph(
                        f"R$ {float(saldo):,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        estilo_direita
                    )

                ]

            )


        # =====================================================
        # TOTAL
        # =====================================================

        dados.append(

            [

                Paragraph(
                    "<b>TOTAL</b>",
                    estilo_centro
                ),

                Paragraph(
                    f"<b>{total_vendedores} vendedores</b>",
                    estilo_tabela
                ),

                Paragraph(
                    "",
                    estilo_tabela
                ),

                Paragraph(
                    f"<b>{total_vendidos}</b>",
                    estilo_centro
                ),

                Paragraph(
                    f"<b>R$ {float(total_valor_vendido):,.2f}</b>"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", "."),
                    estilo_direita
                ),

                Paragraph(
                    f"<b>R$ {float(total_valor_entregue):,.2f}</b>"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", "."),
                    estilo_direita
                ),

                Paragraph(
                    f"<b>R$ {float(total_saldo):,.2f}</b>"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", "."),
                    estilo_direita
                )

            ]

        )


        # =====================================================
        # TABELA
        # =====================================================

        tabela = Table(

            dados,

            colWidths=[

                32,
                125,
                90,
                50,
                78,
                78,
                78

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
                        "BACKGROUND",
                        (0, -1),
                        (-1, -1),
                        colors.whitesmoke
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
                        5
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    )

                ]

            )

        )


        elementos.append(
            tabela
        )

        elementos.append(
            Spacer(1, 20)
        )


        # =====================================================
        # RODAPÉ
        # =====================================================

        rodape = Paragraph(

            f"""
            SGI Brilho Negro<br/>
            Documento gerado automaticamente em
            {data_geracao}.
            """,

            estilos["Normal"]

        )


        elementos.append(
            rodape
        )


        # =====================================================
        # GERAR PDF
        # =====================================================

        pdf.build(elementos)

        arquivo.seek(0)


        # =====================================================
        # NOME DO ARQUIVO
        # =====================================================

        nome_rifa = str(
            rifa["nome"] or "rifa"
        )

        nome_rifa = "".join(

            c if c.isalnum() or c in (
                " ",
                "-",
                "_"
            )

            else "_"

            for c in nome_rifa

        ).strip()


        nome_arquivo = (
            f"relatorio_vendedores_"
            f"{nome_rifa}.pdf"
        )


        return send_file(

            arquivo,

            as_attachment=True,

            download_name=nome_arquivo,

            mimetype="application/pdf"

        )


    finally:

        try:
            db.close()
        except:
            pass        

@app.route("/admin/rifas/<int:rifa_id>/vendedores", methods=["POST"])
def salvar_vendedores_rifa(rifa_id):

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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


            try:

                quantidade = int(quantidade)

            except ValueError:

                return (
                    f"Quantidade inválida para o integrante "
                    f"{integrante_id}."
                ), 400


            if quantidade <= 0:
                continue


            # ======================================
            # VERIFICAR SE JÁ EXISTE
            # ======================================

            existente = db.execute(
                text("""
                    SELECT
                        id,
                        quantidade_numeros,
                        status_prestacao,
                        data_prestacao

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
                    existente["quantidade_numeros"] or 0
                )


                # ==================================
                # PRESTAÇÃO JÁ INICIADA
                # ==================================

                if existente["data_prestacao"] is not None:

                    # Depois que a prestação começou,
                    # a quantidade não pode mais mudar.

                    if quantidade != quantidade_atual:

                        return (
                            "Este vendedor já iniciou a "
                            "prestação de conta e a quantidade "
                            "de números não pode mais ser alterada."
                        ), 400


                    # Quantidade igual:
                    # não faz nada.

                    continue


                # ==================================
                # JÁ POSSUI A QUANTIDADE SOLICITADA
                # ==================================

                if quantidade <= quantidade_atual:

                    continue


                # ==================================
                # AUMENTOU A QUANTIDADE
                # ==================================

                quantidade_nova = (
                    quantidade
                    -
                    quantidade_atual
                )


                # ==================================
                # ATUALIZAR QUANTIDADE DO VENDEDOR
                # ==================================

                db.execute(
                    text("""
                        UPDATE rifas_integrantes

                        SET
                            quantidade_numeros = :quantidade

                        WHERE id = :id
                    """),
                    {
                        "quantidade": quantidade,
                        "id": existente["id"]
                    }
                )


                # ==================================
                # GERAR SOMENTE OS NOVOS NÚMEROS
                # ==================================

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
                        quantidade_devolvida,
                        valor_devido,
                        valor_entregue,
                        valor_recebido,
                        saldo_pendente,
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
                        0,
                        0,
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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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


        # ==========================================
        # VERIFICAR STATUS DA RIFA
        # ==========================================

        if vendedor["status_rifa"] != "ATIVA":

            return (
                "Esta rifa está finalizada "
                "e não permite remover vendedores."
            ), 400


        # ==========================================
        # LIBERAR NÚMEROS DO VENDEDOR
        # ==========================================

        db.execute(
            text("""
                UPDATE rifas_numeros

                SET
                    status = 'DISPONIVEL',
                    integrante_id = NULL,
                    data_venda = NULL,
                    observacao = NULL

                WHERE rifa_id = :rifa_id
                AND integrante_id = :integrante_id
            """),
            {
                "rifa_id": vendedor["rifa_id"],
                "integrante_id": vendedor["integrante_id"]
            }
        )


        # ==========================================
        # REMOVER VINCULO DO VENDEDOR
        # ==========================================

        db.execute(
            text("""
                DELETE FROM rifas_integrantes

                WHERE id = :id
            """),
            {
                "id": id
            }
        )


        # ==========================================
        # SALVAR
        # ==========================================

        db.commit()


        return redirect(request.referrer)


    except Exception as e:

        db.rollback()

        return f"Erro: {e}"


    finally:

        db.close()

@app.route("/admin/rifas/vendedor/<int:id>/prestacao")
def prestacao_vendedor(id):

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")


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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

    if not usuario_tem_permissao("rifas"):
        return redirect("/admin")

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

@app.route("/admin/carteirinhas")
def admin_carteirinhas():

    if not usuario_tem_permissao("carteirinhas"):
        return redirect("/admin")

    db = SessionLocal()

    try:

        # ==========================================
        # INTEGRANTES APTOS PARA CARTEIRINHA
        # ==========================================

        integrantes = db.execute(
            text("""
                SELECT
                    id,
                    codigo_integrante,
                    nome,
                    status,
                    situacao
                FROM integrantes
                WHERE status = 'APROVADO'
                  AND situacao = 'ATIVO'
                ORDER BY LOWER(nome)
            """)
        ).mappings().all()

    finally:

        db.close()

    # ==========================================
    # RETORNO
    # ==========================================

    return render_template(
        "admin/carteirinhas.html",
        integrantes=integrantes
    )        

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

@app.route("/admin/temporadas")
def admin_temporadas():

    if "admin" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        # ==========================================
        # TEMPORADAS
        # ==========================================

        temporadas = db.execute(
            text("""
                SELECT
                    id,
                    nome,
                    ano,
                    status,
                    data_cadastro
                FROM temporadas
                ORDER BY ano DESC
            """)
        ).mappings().all()

    finally:

        db.close()

    return render_template(
        "admin/temporadas.html",
        temporadas=temporadas
    )

@app.route("/admin/relatorios")
def admin_relatorios():

    if "admin" not in session:
        return redirect("/login")

    return render_template(
        "admin/relatorios.html"
    )        

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)