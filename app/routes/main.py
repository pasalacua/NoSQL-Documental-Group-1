from flask import Blueprint, redirect, render_template, session, url_for

from app.db import get_db
from app.services.progreso import buscar_por_id

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/partida")
def partida():
    investigador = buscar_por_id(get_db(), session.get("investigador_id"))
    if not investigador:
        return redirect(url_for("main.index"))
    return render_template("game.html", investigador=investigador,
                           nueva=not investigador.get("misiones"))
