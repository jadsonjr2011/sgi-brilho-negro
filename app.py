from flask import Flask, render_template, request, redirect, session
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from flask import send_file
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3


app = Flask(__name__)
app.secret_key = "brilho_negro_2026"


# ==============================
# CONFIGURAÇÃO DO BANCO
# ==============================

BANCO = "brilhonegro.db"


def criar_banco():

    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS integrantes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT NOT NULL,

        data_nascimento TEXT,

        telefone TEXT,

        email TEXT,

        rua TEXT,
        numero TEXT,
        complemento TEXT,
        bairro TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,

        tipo_sanguineo TEXT,

        possui_alergia TEXT,

        descricao_alergia TEXT,

        responsavel TEXT,

        parentesco TEXT,

        telefone_responsavel TEXT,

        status TEXT DEFAULT 'PENDENTE'

    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_integrantes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        integrante_id INTEGER NOT NULL,

        acao TEXT NOT NULL,

        status_anterior TEXT,

        status_novo TEXT,

        data_hora TEXT,

        usuario TEXT

    )
    """)


    conexao.commit()

    conexao.close()


def atualizar_banco():

    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    campos = [

        ("codigo_integrante","TEXT"),
        ("cpf","TEXT"),
        ("genero","TEXT"),

        ("cep","TEXT"),
        ("rua","TEXT"),
        ("numero","TEXT"),
        ("complemento","TEXT"),
        ("bairro","TEXT"),
        ("cidade","TEXT"),
        ("estado","TEXT"),

        ("alergia_medicamento","TEXT"),

        ("calcado","TEXT"),
        ("estuda","TEXT"),
        ("local_estudo","TEXT"),

        ("trabalha","TEXT"),
        ("profissao","TEXT"),

        ("experiencia_banda","TEXT"),
        ("descricao_experiencia","TEXT"),

        ("responsavel","TEXT"),
        ("telefone_responsavel","TEXT"),

        ("data_cadastro","TEXT")

    ]


    for campo,tipo in campos:

        try:

            cursor.execute(
                f"ALTER TABLE integrantes ADD COLUMN {campo} {tipo}"
            )

        except sqlite3.OperationalError:

            pass


    conexao.commit()

    conexao.close()

# ==============================
# HISTÓRICO DE ALTERAÇÕES
# ==============================

def registrar_historico(integrante_id, acao, status_anterior, status_novo):

    from datetime import datetime


    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
    INSERT INTO historico_integrantes
    (
        integrante_id,
        acao,
        status_anterior,
        status_novo,
        data_hora,
        usuario
    )

    VALUES (?,?,?,?,?,?)

    """,
    (
        integrante_id,
        acao,
        status_anterior,
        status_novo,
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Administrador"
    ))


    conexao.commit()

    conexao.close()

# ==============================
# INICIALIZAÇÃO DO BANCO
# ==============================

criar_banco()

atualizar_banco()



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


        # usuário inicial administrativo

        if usuario == "administrativo" and senha == "123456":


            session["admin"] = True


            return redirect("/admin")


        else:

            return render_template(
                "admin/login.html",
                erro="Usuário ou senha inválidos"
            )


    return render_template("admin/login.html")

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")

@app.route("/admin")
def admin():


    if "admin" not in session:

        return redirect("/login")


    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT *
        FROM integrantes
        ORDER BY id DESC
    """)

    integrantes = cursor.fetchall()


    cursor.execute("""
        SELECT COUNT(*)
        FROM integrantes
    """)

    total = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM integrantes
        WHERE status = 'PENDENTE'
    """)

    pendentes = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM integrantes
        WHERE status = 'APROVADO'
    """)

    aprovados = cursor.fetchone()[0]


    conexao.close()


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


    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT *
        FROM integrantes
        WHERE id = ?
    """,(id,))


    integrante = cursor.fetchone()



    cursor.execute("""
        SELECT *
        FROM historico_integrantes
        WHERE integrante_id = ?
        ORDER BY id DESC
    """,(id,))


    historico = cursor.fetchall()



    conexao.close()


    return render_template(
        "admin/ficha.html",
        integrante=integrante,
        historico=historico
    )

@app.route("/admin/integrante/<int:id>/editar", methods=["GET","POST"])
def editar_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()



    if request.method == "POST":

        cursor.execute("""
        UPDATE integrantes SET

            nome=?,
            data_nascimento=?,
            telefone=?,
            email=?,
            rua=?,
            numero=?,
            complemento=?,
            bairro=?,
            cidade=?,
            estado=?,
            cep=?

        WHERE id=?

        """,
        (

            request.form["nome"],
            request.form["data_nascimento"],
            request.form["telefone"],
            request.form["email"],
            request.form["rua"],
            request.form["numero"],
            request.form["complemento"],
            request.form["bairro"],
            request.form["cidade"],
            request.form["estado"],
            request.form["cep"],
            id

        ))


        conexao.commit()

        conexao.close()


        return redirect(f"/admin/integrante/{id}")



    cursor.execute("""
    SELECT *
    FROM integrantes
    WHERE id=?
    """,(id,))


    integrante = cursor.fetchone()


    conexao.close()


    return render_template(
        "admin/editar.html",
        integrante=integrante
    )

@app.route("/admin/aprovar/<int:id>")
def aprovar_integrante(id):

    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT status
        FROM integrantes
        WHERE id = ?
    """,(id,))


    anterior = cursor.fetchone()[0]


    cursor.execute("""
        UPDATE integrantes
        SET status = 'APROVADO'
        WHERE id = ?
    """,(id,))


    conexao.commit()

    conexao.close()


    registrar_historico(
        id,
        "APROVAÇÃO",
        anterior,
        "APROVADO"
    )


    return redirect(f"/admin/integrante/{id}")



@app.route("/admin/reprovar/<int:id>")
def reprovar_integrante(id):

    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT status
        FROM integrantes
        WHERE id = ?
    """,(id,))


    anterior = cursor.fetchone()[0]


    cursor.execute("""
        UPDATE integrantes
        SET status = 'REPROVADO'
        WHERE id = ?
    """,(id,))


    conexao.commit()

    conexao.close()


    registrar_historico(
        id,
        "REPROVAÇÃO",
        anterior,
        "REPROVADO"
    )


    return redirect(f"/admin/integrante/{id}")

@app.route("/admin/integrante/<int:id>/excluir")
def excluir_integrante(id):

    if "admin" not in session:
        return redirect("/login")


    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
        DELETE FROM integrantes
        WHERE id = ?
    """,(id,))


    conexao.commit()

    conexao.close()


    return redirect("/admin")

@app.route("/admin/integrante/<int:id>/inativar")
def inativar_integrante(id):

    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT status
        FROM integrantes
        WHERE id = ?
    """,(id,))


    anterior = cursor.fetchone()[0]


    cursor.execute("""
        UPDATE integrantes
        SET status = 'INATIVO'
        WHERE id = ?
    """,(id,))


    conexao.commit()

    conexao.close()


    registrar_historico(
        id,
        "INATIVAÇÃO",
        anterior,
        "INATIVO"
    )


    return redirect(f"/admin/integrante/{id}")

@app.route("/admin/integrante/<int:id>/reativar")
def reativar_integrante(id):

    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT status
        FROM integrantes
        WHERE id = ?
    """,(id,))


    anterior = cursor.fetchone()[0]


    cursor.execute("""
        UPDATE integrantes
        SET status = 'APROVADO'
        WHERE id = ?
    """,(id,))


    conexao.commit()

    conexao.close()


    registrar_historico(
        id,
        "REATIVAÇÃO",
        anterior,
        "APROVADO"
    )


    return redirect(f"/admin/integrante/{id}")

@app.route("/salvar_cadastro", methods=["POST"])
def salvar_cadastro():


    conexao = sqlite3.connect(BANCO)

    cursor = conexao.cursor()


    # ==============================
    # GERAR CÓDIGO DO INTEGRANTE
    # ==============================

    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM integrantes
        """
    )

    total = cursor.fetchone()[0] + 1


    codigo_integrante = f"BN{total:06d}"



    # ==============================
    # DATA CADASTRO
    # ==============================

    import datetime

    data_cadastro = datetime.datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )


    # ==============================
    # DADOS DO FORMULÁRIO
    # ==============================


    dados = (

        codigo_integrante,

        request.form.get("nome"),
        request.form.get("cpf"),
        request.form.get("data_nascimento"),

        request.form.get("telefone"),
        request.form.get("email"),

        request.form.get("cep"),
        request.form.get("rua"),
        request.form.get("numero"),
        request.form.get("complemento"),
        request.form.get("bairro"),
        request.form.get("cidade"),
        request.form.get("estado"),


        request.form.get("alergia_medicamento"),
        request.form.get("descricao_alergia"),


        request.form.get("calcado"),
        request.form.get("estuda"),
        request.form.get("local_estudo"),

        request.form.get("trabalha"),
        request.form.get("profissao"),

        request.form.get("experiencia_banda"),
        request.form.get("descricao_experiencia"),


        request.form.get("responsavel"),
        request.form.get("telefone_responsavel"),


        data_cadastro,

        "PENDENTE"

    )


    cursor.execute(
    """

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


    responsavel,
    telefone_responsavel,


    data_cadastro,

    status

    )


VALUES

(
    ?,?,?,?,?,?,?,?,?,?,
    ?,?,?,?,?,?,?,?,?,?,
    ?,?,?,?,?,?
)

    """,

    dados

    )


    conexao.commit()

    conexao.close()



    return render_template(
    "cadastro/sucesso.html",
    codigo=codigo_integrante
    )

@app.route("/admin/exportar/pdf")
def exportar_pdf():

    if "admin" not in session:
        return redirect("/login")


    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT
            codigo_integrante,
            nome,
            cidade,
            estado,
            status

        FROM integrantes

        ORDER BY nome
    """)


    integrantes = cursor.fetchall()


    conexao.close()



    arquivo = BytesIO()


    pdf = SimpleDocTemplate(
        arquivo
    )


    elementos = []


    estilos = getSampleStyleSheet()


    titulo = Paragraph(
        "Brilho Negro<br/>Relatório de Integrantes",
        estilos["Title"]
    )


    elementos.append(titulo)

    elementos.append(Spacer(1,20))



    dados = [

        [
            "Código",
            "Nome",
            "Cidade",
            "Estado",
            "Status"
        ]

    ]



    for pessoa in integrantes:

        dados.append(

            [
                pessoa["codigo_integrante"],
                pessoa["nome"],
                pessoa["cidade"],
                pessoa["estado"],
                pessoa["status"]
            ]

        )



    tabela = Table(dados)


    tabela.setStyle(

        TableStyle(

            [

                ("GRID",(0,0),(-1,-1),0.5,None),

                ("BACKGROUND",(0,0),(-1,0),None),

                ("ALIGN",(0,0),(-1,-1),"CENTER")

            ]

        )

    )


    elementos.append(tabela)


    pdf.build(elementos)


    arquivo.seek(0)


    return send_file(

        arquivo,

        as_attachment=True,

        download_name="integrantes_brilho_negro.pdf",

        mimetype="application/pdf"

    )

@app.route("/admin/exportar/excel")
def exportar_excel():

    if "admin" not in session:
        return redirect("/login")


    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()


    cursor.execute("""
        SELECT
            codigo_integrante,
            nome,
            cpf,
            data_nascimento,
            telefone,
            email,
            cidade,
            estado,
            status,
            data_cadastro

        FROM integrantes

        ORDER BY nome
    """)


    integrantes = cursor.fetchall()


    conexao.close()



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
        "Cidade",
        "Estado",
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
            pessoa["cidade"],
            pessoa["estado"],
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


if __name__ == "__main__":

    app.run(debug=True)