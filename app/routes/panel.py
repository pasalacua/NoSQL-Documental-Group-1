"""Panel del expositor: resultados en vivo, administración de documentos y reinicio."""
import hmac
import json
import socket
from collections import Counter
from functools import wraps

from flask import Blueprint, current_app, jsonify, render_template, request, session
from pymongo.errors import OperationFailure, WriteError

from app.db import get_db
from app.misiones import MISIONES
from app.services.consultas import ErrorConsulta, a_shell, parsear_filtro_texto
from app.services.formas import CAMPOS_FIJOS
from app.services.progreso import anotar_bitacora, ranking
from app.services.serializar import a_json

panel = Blueprint("panel", __name__)

OPERACIONES = ["$set", "$inc", "$unset", "$push", "$addToSet", "$pull"]
CAMPOS_PROTEGIDOS = {"_id", "numero"}


def requiere_pin(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if not session.get("panel"):
            return jsonify({"error": "Ingresá el PIN del panel"}), 401
        return funcion(*args, **kwargs)
    return envoltura


@panel.errorhandler(ErrorConsulta)
def _error_consulta(error):
    return jsonify({"error": str(error)}), 400


@panel.get("/panel")
def pagina_panel():
    return render_template("panel.html", autorizado=bool(session.get("panel")))


@panel.post("/panel/ingresar")
def ingresar():
    pin = str((request.get_json(silent=True) or {}).get("pin", ""))
    if not hmac.compare_digest(pin, str(current_app.config["PANEL_PIN"])):
        return jsonify({"error": "PIN incorrecto"}), 403
    session["panel"] = True
    return jsonify({"ok": True})


@panel.get("/api/panel/resumen")
@requiere_pin
def resumen():
    db = get_db()
    completadas = {f["_id"]: f["total"] for f in db.investigadores.aggregate([
        {"$unwind": "$misiones"},
        {"$group": {"_id": "$misiones.clave", "total": {"$sum": 1}}},
    ])}
    entregas = {}
    for fila in db.entregas.aggregate([
        {"$group": {"_id": {"mision": "$mision", "correcta": "$correcta"}, "total": {"$sum": 1}}},
    ]):
        entregas.setdefault(fila["_id"]["mision"], {})[str(fila["_id"]["correcta"]).lower()] = fila["total"]
    errores = Counter()
    for fila in db.entregas.aggregate([
        {"$match": {"correcta": False, "error": {"$ne": None}}},
        {"$group": {"_id": "$error", "total": {"$sum": 1}}},
    ]):
        errores[fila["_id"]] = fila["total"]

    formas_nuevas = list(db.pokemon.aggregate([
        {"$unwind": "$formas"},
        {"$match": {"formas.registrada_por": {"$ne": "Profesor Oak"}}},
        {"$sort": {"formas.fecha_registro": -1}},
        {"$limit": 20},
        {"$project": {"_id": 0, "pokemon": "$nombre", "forma": "$formas"}},
    ]))
    campos_extra = Counter(
        clave for fila in formas_nuevas for clave in fila["forma"] if clave not in CAMPOS_FIJOS)

    return jsonify({
        "url": _url_publica(),
        "investigadores": db.investigadores.count_documents({}),
        "misiones": [{
            "clave": m["clave"], "entrenador": m["entrenador"], "sprite": m["sprite"], "concepto": m["concepto"],
            "completadas": completadas.get(m["clave"], 0),
            "aciertos": entregas.get(m["clave"], {}).get("true", 0),
            "fallos": entregas.get(m["clave"], {}).get("false", 0),
        } for m in MISIONES],
        "errores": dict(errores),
        "formas": [a_json(f) for f in formas_nuevas],
        "campos_extra": dict(campos_extra),
        "ranking": ranking(db, 10),
    })


@panel.get("/api/panel/bitacora")
@requiere_pin
def bitacora():
    filas = get_db().bitacora.find({}, {"_id": 0}).sort("fecha", -1).limit(25)
    return jsonify([a_json(f) for f in filas])


@panel.post("/api/panel/reiniciar")
@requiere_pin
def reiniciar():
    from database.seed import sembrar

    borrar = bool((request.get_json(silent=True) or {}).get("borrar_investigadores"))
    return jsonify(sembrar(get_db(), borrar_investigadores=borrar))


@panel.get("/api/panel/pokemon")
@requiere_pin
def lista_pokemon():
    return jsonify(list(get_db().pokemon.find({}, {"_id": 0, "numero": 1, "nombre": 1}).sort("numero", 1)))


@panel.post("/api/panel/editar")
@requiere_pin
def editar():
    """Administración de documentos: $set, $inc, $unset, $push, $addToSet y $pull."""
    db = get_db()
    datos = request.get_json(silent=True) or {}
    try:
        numero = int(datos.get("numero"))
    except (TypeError, ValueError):
        raise ErrorConsulta("Elegí un Pokémon") from None
    operacion = datos.get("operacion")
    if operacion not in OPERACIONES:
        raise ErrorConsulta("Operación no permitida")
    campo = str(datos.get("campo") or "").strip()
    partes = campo.split(".")
    if (not campo or len(partes) > 3 or partes[0] in CAMPOS_PROTEGIDOS
            or not all(p.replace("_", "a").isalnum() and not p[0].isdigit() for p in partes if p)
            or any(not p for p in partes)):
        raise ErrorConsulta("Campo inválido (ejemplos: estadisticas.velocidad, movimientos, curiosidad)")
    valor = _valor_admin(datos.get("valor"), operacion)

    filtro = {"numero": numero}
    actualizacion = {operacion: {campo: valor}}
    comando = f"db.pokemon.updateOne({a_shell(filtro)}, {a_shell(actualizacion)})"
    try:
        resultado = db.pokemon.update_one(filtro, actualizacion)
    except WriteError as error:
        if getattr(error, "code", None) == 121:
            return jsonify({"error": "El validador de esquema ($jsonSchema) rechazó el cambio: el documento "
                                     "dejaría de cumplir la estructura mínima de un Pokémon.",
                            "comando": comando}), 400
        return jsonify({"error": f"MongoDB rechazó la operación: {str(error)[:200]}", "comando": comando}), 400
    except OperationFailure as error:
        return jsonify({"error": f"MongoDB rechazó la operación: {str(error)[:200]}", "comando": comando}), 400
    if resultado.matched_count == 0:
        return jsonify({"error": "No existe ese Pokémon", "comando": comando}), 404
    anotar_bitacora(db, None, f"updateOne {operacion}", comando)
    return jsonify({"comando": comando, "modificados": resultado.modified_count,
                    "documento": a_json(db.pokemon.find_one(filtro))})


def _url_publica():
    """Si el panel se abre en localhost, muestra la IP de la red local para los celulares."""
    url = request.host_url
    if request.host.split(":")[0] not in ("localhost", "127.0.0.1"):
        return url
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as prueba:
            prueba.connect(("8.8.8.8", 80))  # no envía datos: solo elige la interfaz de red
            ip = prueba.getsockname()[0]
    except OSError:
        return url
    puerto = request.host.split(":")[1] if ":" in request.host else "80"
    return f"http://{ip}:{puerto}/"


def _valor_admin(valor, operacion):
    if operacion == "$unset":
        return ""
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            raise ErrorConsulta("Completá el valor")
        try:
            valor = json.loads(texto)
        except json.JSONDecodeError:
            if texto.startswith("{"):
                valor = parsear_filtro_texto(texto)  # acepta claves sin comillas
            else:
                valor = texto
    if operacion == "$inc" and (isinstance(valor, bool) or not isinstance(valor, (int, float))):
        raise ErrorConsulta("$inc necesita un número")
    if isinstance(valor, (dict, list)):
        texto = json.dumps(valor)
        if len(texto) > 800 or "$" in texto:
            raise ErrorConsulta("Valor no permitido")
    return valor
