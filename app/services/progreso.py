"""Investigadores (jugadores), progreso de misiones, bitácora y ranking."""
import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from app.services.consultas import ErrorConsulta
from app.services.serializar import a_json

_NOMBRE = re.compile(r"^[\wÁÉÍÓÚÜÑáéíóúüñ .-]{2,20}$")
PUNTOS_BASE = 100
PENALIDAD = 15
PUNTOS_MINIMOS = 40


def ahora():
    return datetime.now(timezone.utc)


def validar_nombre(nombre):
    nombre = " ".join(str(nombre or "").split())
    if not _NOMBRE.match(nombre):
        raise ErrorConsulta("El nombre debe tener entre 2 y 20 letras o números")
    return nombre


def crear_investigador(db, nombre):
    nombre = validar_nombre(nombre)
    documento = {
        "nombre": nombre,
        "nombre_clave": nombre.casefold(),
        "creado": ahora(),
        "ultima_actividad": ahora(),
        "puntos": 0,
        "misiones": [],   # array de documentos embebidos: {clave, puntos, completada_en}
        "intentos": {},   # documento anidado: {clave_mision: fallos}
    }
    try:
        documento["_id"] = db.investigadores.insert_one(documento).inserted_id
    except DuplicateKeyError:
        raise ErrorConsulta("Ese nombre ya está en uso. Si es tu partida, usá CARGAR PARTIDA.") from None
    return documento


def cargar_investigador(db, nombre):
    nombre = validar_nombre(nombre)
    investigador = db.investigadores.find_one_and_update(
        {"nombre_clave": nombre.casefold()}, {"$set": {"ultima_actividad": ahora()}})
    if not investigador:
        raise ErrorConsulta("No encontré una partida con ese nombre")
    return investigador


def buscar_por_id(db, investigador_id):
    try:
        return db.investigadores.find_one({"_id": ObjectId(investigador_id)})
    except (InvalidId, TypeError):
        return None


def completada(investigador, clave):
    return any(m.get("clave") == clave for m in investigador.get("misiones", []))


def registrar_fallo(db, investigador, clave):
    db.investigadores.update_one({"_id": investigador["_id"]}, {"$inc": {f"intentos.{clave}": 1}})


def completar_mision(db, investigador, clave):
    """Marca la misión como completada una sola vez (el filtro $ne evita sumar dos veces)."""
    actual = db.investigadores.find_one({"_id": investigador["_id"]}, {"intentos": 1})
    fallos = (actual or {}).get("intentos", {}).get(clave, 0)
    puntos = max(PUNTOS_MINIMOS, PUNTOS_BASE - PENALIDAD * fallos)
    resultado = db.investigadores.update_one(
        {"_id": investigador["_id"], "misiones.clave": {"$ne": clave}},
        {"$push": {"misiones": {"clave": clave, "puntos": puntos, "completada_en": ahora()}},
         "$inc": {"puntos": puntos},
         "$set": {"ultima_actividad": ahora()}},
    )
    return puntos if resultado.modified_count else 0


def registrar_entrega(db, investigador, clave, correcta, error=None):
    db.entregas.insert_one({
        "investigador": investigador["nombre"],
        "mision": clave,
        "correcta": correcta,
        "error": error,
        "fecha": ahora(),
    })


def anotar_bitacora(db, investigador, operacion, comando, resultados=None, plan=None):
    """La bitácora es una colección limitada (capped): guarda solo las últimas operaciones."""
    try:
        db.bitacora.insert_one({
            "fecha": ahora(),
            "investigador": investigador["nombre"] if investigador else "panel",
            "operacion": operacion,
            "comando": comando[:600],
            "resultados": resultados,
            "docs_examinados": (plan or {}).get("docs_examinados"),
            "indice": (plan or {}).get("indice"),
        })
    except Exception:
        pass  # la bitácora nunca debe frenar el juego


def ranking(db, limite=10):
    return [a_json(fila) for fila in db.investigadores.aggregate([
        {"$project": {"_id": 0, "nombre": 1, "puntos": 1, "creado": 1,
                      "completadas": {"$size": "$misiones"}}},
        {"$sort": {"puntos": -1, "completadas": -1, "creado": 1}},
        {"$limit": limite},
        {"$project": {"creado": 0}},
    ])]


def perfil(investigador):
    return {
        "nombre": investigador["nombre"],
        "puntos": investigador.get("puntos", 0),
        "misiones": [a_json(m) for m in investigador.get("misiones", [])],
        "intentos": investigador.get("intentos", {}),
    }
