from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "biblioteca123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# MODELOS
# -------------------------

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))
    admin = db.Column(db.Boolean)


class Libro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100))
    autor = db.Column(db.String(100))
    isbn = db.Column(db.String(30))
    disponibles = db.Column(db.Integer)


# -------------------------
# CREAR BASE DE DATOS
# -------------------------

with app.app_context():
    db.create_all()

    if Usuario.query.count() == 0:
        admin = Usuario(
            usuario="admin",
            password="1234",
            admin=True
        )

        usuario = Usuario(
            usuario="andre",
            password="1234",
            admin=False
        )

        db.session.add(admin)
        db.session.add(usuario)
        db.session.commit()


# -------------------------
# LOGIN
# -------------------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        user = Usuario.query.filter_by(
            usuario=usuario,
            password=password
        ).first()

        if user:
            session["usuario"] = user.usuario
            session["admin"] = user.admin
            return redirect("/inicio")

        return "Usuario o contraseña incorrectos"

    return render_template("login.html")


# -------------------------
# INICIO
# -------------------------

@app.route("/inicio")
def inicio():

    if "usuario" not in session:
        return redirect("/")

    libros = Libro.query.all()

    return render_template(
        "inicio.html",
        libros=libros,
        admin=session["admin"],
        usuario=session["usuario"]
    )


# -------------------------
# AGREGAR LIBRO
# -------------------------

@app.route("/agregar", methods=["GET", "POST"])
def agregar():

    if "usuario" not in session:
        return redirect("/")

    if not session["admin"]:
        return "Solo el administrador puede agregar libros."

    if request.method == "POST":

        nuevo = Libro(
            titulo=request.form["titulo"],
            autor=request.form["autor"],
            isbn=request.form["isbn"],
            disponibles=int(request.form["cantidad"])
        )

        db.session.add(nuevo)
        db.session.commit()

        return redirect("/inicio")

    return render_template("agregar.html")


# -------------------------
# PRESTAR
# -------------------------

@app.route("/prestar/<int:id>")
def prestar(id):

    libro = Libro.query.get(id)

    if libro.disponibles > 0:
        libro.disponibles -= 1
        db.session.commit()

    return redirect("/inicio")


# -------------------------
# DEVOLVER
# -------------------------

@app.route("/devolver/<int:id>")
def devolver(id):

    libro = Libro.query.get(id)

    libro.disponibles += 1
    db.session.commit()

    return redirect("/inicio")


# -------------------------
# CERRAR SESIÓN
# -------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# -------------------------
# EDITAR LIBRO
# -------------------------

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    if "usuario" not in session:
        return redirect("/")

    if not session["admin"]:
        return "Solo el administrador puede editar."

    libro = Libro.query.get_or_404(id)

    if request.method == "POST":

        libro.titulo = request.form["titulo"]
        libro.autor = request.form["autor"]
        libro.isbn = request.form["isbn"]
        libro.disponibles = int(request.form["cantidad"])

        db.session.commit()

        return redirect("/inicio")

    return render_template("editar.html", libro=libro)

# -------------------------
# ELIMINAR LIBRO
# -------------------------

@app.route("/eliminar/<int:id>")
def eliminar(id):

    if "usuario" not in session:
        return redirect("/")

    if not session["admin"]:
        return "Solo el administrador puede eliminar."

    libro = Libro.query.get_or_404(id)

    db.session.delete(libro)
    db.session.commit()

    return redirect("/inicio")

# -------------------------
# EJECUTAR
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)