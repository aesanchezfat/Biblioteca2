import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="Static", static_url_path="/Static")
app.secret_key = "biblioteca123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(app.root_path, "Static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    prestados = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255), nullable=True)
    sinopsis = db.Column(db.Text, nullable=True)
    reporte = db.Column(db.Text, nullable=True)


class Prestamo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey("libro.id"), nullable=False)

    usuario = db.relationship("Usuario", backref="prestamos")
    libro = db.relationship("Libro", backref="prestamos")


# -------------------------
# CREAR Y MIGRAR BASE DE DATOS
# -------------------------

with app.app_context():
    db.create_all()

    # Migración automática de columnas para bases de datos SQLite existentes
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if "libro" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("libro")]
        with db.engine.connect() as conn:
            if "prestados" not in columns:
                conn.execute(text("ALTER TABLE libro ADD COLUMN prestados INTEGER DEFAULT 0"))
            if "imagen" not in columns:
                conn.execute(text("ALTER TABLE libro ADD COLUMN imagen VARCHAR(255)"))
            if "sinopsis" not in columns:
                conn.execute(text("ALTER TABLE libro ADD COLUMN sinopsis TEXT"))
            if "reporte" not in columns:
                conn.execute(text("ALTER TABLE libro ADD COLUMN reporte TEXT"))
            conn.commit()

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
    user = Usuario.query.filter_by(usuario=session["usuario"]).first()

    libros_prestados_ids = []
    if user:
        prestamos = Prestamo.query.filter_by(usuario_id=user.id).all()
        libros_prestados_ids = [p.libro_id for p in prestamos]

    todos_los_prestamos = []
    if session.get("admin"):
        todos_los_prestamos = Prestamo.query.all()

    return render_template(
        "inicio.html",
        libros=libros,
        admin=session["admin"],
        usuario=session["usuario"],
        libros_prestados_ids=libros_prestados_ids,
        todos_los_prestamos=todos_los_prestamos
    )


# -------------------------
# CREAR USUARIO
# -------------------------

@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():

    if "usuario" not in session:
        return redirect("/")

    if not session["admin"]:
        return "Solo el administrador puede crear usuarios."

    if request.method == "POST":

        nombre_usuario = request.form["usuario"].strip()
        password = request.form["password"].strip()
        es_admin = True if request.form.get("admin") else False

        existente = Usuario.query.filter_by(usuario=nombre_usuario).first()
        if existente:
            return render_template("crear_usuario.html", error="El nombre de usuario ya existe.")

        nuevo_usuario = Usuario(
            usuario=nombre_usuario,
            password=password,
            admin=es_admin
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect("/inicio")

    return render_template("crear_usuario.html")


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

        imagen_filename = None
        if "imagen" in request.files:
            file = request.files["imagen"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                imagen_filename = filename

        nuevo = Libro(
            titulo=request.form["titulo"],
            autor=request.form["autor"],
            isbn=request.form["isbn"],
            disponibles=int(request.form["cantidad"]),
            sinopsis=request.form.get("sinopsis", ""),
            reporte=request.form.get("reporte", ""),
            prestados=0,
            imagen=imagen_filename
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

    if "usuario" not in session:
        return redirect("/")

    user = Usuario.query.filter_by(usuario=session["usuario"]).first()
    libro = Libro.query.get_or_404(id)

    if user and libro and libro.disponibles > 0:
        prestamo_existente = Prestamo.query.filter_by(usuario_id=user.id, libro_id=libro.id).first()
        if not prestamo_existente:
            libro.disponibles -= 1
            libro.prestados = (libro.prestados or 0) + 1
            nuevo_prestamo = Prestamo(usuario_id=user.id, libro_id=libro.id)
            db.session.add(nuevo_prestamo)
            db.session.commit()

    return redirect("/inicio")


# -------------------------
# DEVOLVER
# -------------------------

@app.route("/devolver/<int:id>")
def devolver(id):

    if "usuario" not in session:
        return redirect("/")

    user = Usuario.query.filter_by(usuario=session["usuario"]).first()
    libro = Libro.query.get_or_404(id)

    if user and libro:
        prestamo = Prestamo.query.filter_by(usuario_id=user.id, libro_id=libro.id).first()
        if prestamo:
            db.session.delete(prestamo)
            libro.disponibles += 1
            if libro.prestados and libro.prestados > 0:
                libro.prestados -= 1
            else:
                libro.prestados = 0
            db.session.commit()

    return redirect("/inicio")


# -------------------------
# REPORTAR INCIDENCIA
# -------------------------

@app.route("/reportar/<int:id>", methods=["GET", "POST"])
def reportar(id):

    if "usuario" not in session:
        return redirect("/")

    if not session["admin"]:
        return "Solo el administrador puede reportar incidencias."

    libro = Libro.query.get_or_404(id)

    if request.method == "POST":

        libro.reporte = request.form.get("reporte", "").strip()
        db.session.commit()

        return redirect("/inicio")

    return render_template("reportar.html", libro=libro)


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
        libro.sinopsis = request.form.get("sinopsis", "")
        libro.reporte = request.form.get("reporte", "")

        if "imagen" in request.files:
            file = request.files["imagen"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                libro.imagen = filename

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