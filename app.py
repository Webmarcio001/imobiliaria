from flask import Flask, render_template, request, redirect, session
import sqlite3, os, datetime
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "123"

UPLOAD_FOLDER = "static/fotos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ================= BANCO =================
def conectar():
    return sqlite3.connect("imoveis.db")

def criar_banco():
    conn = conectar()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS imoveis(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        endereco TEXT,
        preco REAL,
        quartos INTEGER,
        foto TEXT,
        status TEXT,
        comissao REAL,
        data_venda TEXT
    )
    """)
    conn.commit()
    conn.close()

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == "admin" and request.form["pass"] == "123":
            session["logado"] = True
            return redirect("/admin")
    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= INDEX =================
@app.route("/")
def index():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM imoveis")
    imoveis = c.fetchall()
    conn.close()
    return render_template("index.html", imoveis=imoveis)

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("logado"):
        return redirect("/login")

    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM imoveis")
    imoveis = c.fetchall()
    conn.close()

    return render_template("admin.html", imoveis=imoveis)

# ================= CADASTRAR =================
@app.route("/cadastrar", methods=["GET","POST"])
def cadastrar():
    if request.method == "POST":
        tipo = request.form["tipo"]
        endereco = request.form["endereco"]
        preco = float(request.form["preco"])
        quartos = request.form["quartos"]
        foto = request.files["foto"]

        if foto:
            caminho = os.path.join(app.config["UPLOAD_FOLDER"], foto.filename)
            foto.save(caminho)
        else:
            caminho = ""

        comissao = preco * 0.05

        conn = conectar()
        c = conn.cursor()
        c.execute("""
        INSERT INTO imoveis(tipo,endereco,preco,quartos,foto,status,comissao,data_venda)
        VALUES (?,?,?,?,?,?,?,?)
        """,(tipo,endereco,preco,quartos,caminho,"Disponível",comissao,""))
        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("cadastrar.html")

# ================= VENDER =================
@app.route("/vender/<int:id>")
def vender(id):
    conn = conectar()
    c = conn.cursor()
    data = str(datetime.date.today())
    c.execute("UPDATE imoveis SET status='Vendido', data_venda=? WHERE id=?", (data,id))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ================= BUSCAR =================
@app.route("/buscar")
def buscar():
    termo = request.args.get("q")
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM imoveis WHERE endereco LIKE ?",('%'+termo+'%',))
    imoveis = c.fetchall()
    conn.close()
    return render_template("index.html", imoveis=imoveis)

# ================= FILTRO =================
@app.route("/filtro")
def filtro():
    preco = request.args.get("preco")
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM imoveis WHERE preco <= ?",(preco,))
    imoveis = c.fetchall()
    conn.close()
    return render_template("index.html", imoveis=imoveis)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT SUM(comissao) FROM imoveis WHERE status='Vendido'")
    total = c.fetchone()[0]
    conn.close()
    return render_template("dashboard.html", total=total)

# ================= PDF =================
@app.route("/pdf")
def pdf():
    c = canvas.Canvas("relatorio.pdf")
    c.drawString(100,750,"Relatório de Imóveis Vendidos")
    c.save()
    return "PDF gerado!"

# ================= MAIN =================
if __name__ == "__main__":
    criar_banco()
    app.run()