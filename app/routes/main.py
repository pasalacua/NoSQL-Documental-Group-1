
from flask import Blueprint, render_template

# Creamos un grupo de rutas para las páginas principales
main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")
