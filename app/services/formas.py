"""Registro de formas alternativas (misión del Entrenador Verde).

Cada forma se guarda EMBEBIDA en el array `formas` del documento del Pokémon:

    db.pokemon.updateOne(
      { numero: 248, "formas.nombre": { $ne: "Mega Tyranitar" } },
      { $push: { formas: { nombre: "Mega Tyranitar", ..., objeto_requerido: "Tyranitarita" } } }
    )

La condición `$ne` hace que la escritura sea atómica: si dos investigadores
registran la misma forma al mismo tiempo, solo uno la inserta.
"""
import random
import re
import unicodedata
from datetime import datetime, timezone

from app.services.consultas import ESTADISTICAS, TIPOS, ErrorConsulta, a_shell
from app.services.serializar import a_json

CAMPOS_FIJOS = {"nombre", "tipos", "estadisticas", "habilidad", "registrada_por", "fecha_registro"}
_NOMBRE_CAMPO = re.compile(r"^[a-z_][a-z0-9_]{0,29}$")
MAX_CAMPOS_FORMA = 14


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


def nombre_de_campo(texto):
    clave = normalizar(texto).replace(" ", "_").replace("-", "_")
    if not _NOMBRE_CAMPO.match(clave):
        raise ErrorConsulta(
            f"'{texto}' no sirve como nombre de campo: usá letras, números y guiones bajos (ej: objeto_requerido)")
    if clave in CAMPOS_FIJOS:
        raise ErrorConsulta(f"'{clave}' ya es un campo fijo de la forma: elegí otro nombre")
    return clave


def valor_de_campo(valor):
    if isinstance(valor, bool):
        return valor
    texto = str(valor if valor is not None else "").strip()
    if not texto:
        raise ErrorConsulta("Completá el valor del campo")
    if len(texto) > 60:
        raise ErrorConsulta("El valor es demasiado largo (máximo 60 caracteres)")
    if re.fullmatch(r"-?\d+", texto):
        return int(texto)
    if re.fullmatch(r"-?\d+[.,]\d+", texto):
        return float(texto.replace(",", "."))
    if texto.lower() in ("true", "verdadero", "si", "sí"):
        return True
    if texto.lower() in ("false", "falso", "no"):
        return False
    return texto


# --------------------------------------------------------------------------
# Avistamientos
# --------------------------------------------------------------------------

def _registrada(db, avistamiento):
    return db.pokemon.count_documents(
        {"numero": avistamiento["numero"], "formas.nombre": avistamiento["forma"]}, limit=1) > 0


def asignar_avistamiento(db, investigador):
    """Le da a cada investigador un avistamiento, priorizando los que nadie registró."""
    clave = investigador.get("avistamiento")
    if clave:
        avistamiento = db.avistamientos.find_one({"clave": clave}, {"_id": 0})
        if avistamiento:
            return avistamiento
    todos = list(db.avistamientos.find({}, {"_id": 0}))
    if not todos:
        raise ErrorConsulta("No hay avistamientos cargados: reiniciá la base desde el panel")
    asignados = {}
    for fila in db.investigadores.aggregate([
        {"$match": {"avistamiento": {"$exists": True}}},
        {"$group": {"_id": "$avistamiento", "total": {"$sum": 1}}},
    ]):
        asignados[fila["_id"]] = fila["total"]
    libres = [a for a in todos if not _registrada(db, a)] or todos
    menor = min(asignados.get(a["clave"], 0) for a in libres)
    elegido = random.choice([a for a in libres if asignados.get(a["clave"], 0) == menor])
    db.investigadores.update_one({"_id": investigador["_id"]}, {"$set": {"avistamiento": elegido["clave"]}})
    return elegido


def estado_avistamiento(db, avistamiento):
    pokemon = db.pokemon.find_one({"numero": avistamiento["numero"]}, {"nombre": 1, "numero": 1, "formas": 1})
    forma = None
    if pokemon:
        forma = next((f for f in pokemon.get("formas", []) if f.get("nombre") == avistamiento["forma"]), None)
    return {
        "avistamiento": {k: v for k, v in avistamiento.items() if k != "_id"},
        "ya_registrada": forma is not None,
        "forma_existente": a_json(forma) if forma else None,
    }


# --------------------------------------------------------------------------
# Validación del formulario contra la ficha del avistamiento
# --------------------------------------------------------------------------

def construir_forma(datos, avistamiento):
    errores = []
    try:
        numero = int(datos.get("numero"))
    except (TypeError, ValueError):
        numero = None
    if numero != avistamiento["numero"]:
        errores.append(f"El avistamiento es de {avistamiento['pokemon']}: elegí ese Pokémon como base")
    nombre = str(datos.get("nombre") or "").strip()
    if normalizar(nombre) != normalizar(avistamiento["forma"]):
        errores.append("El nombre de la forma no coincide con la ficha")
    tipos = datos.get("tipos") or []
    if not isinstance(tipos, list) or any(t not in TIPOS for t in tipos):
        raise ErrorConsulta("Tipos inválidos")
    if sorted(tipos) != sorted(avistamiento["tipos"]):
        errores.append("Los tipos no coinciden con la ficha")
    estadisticas = {}
    for stat in ESTADISTICAS:
        try:
            estadisticas[stat] = int(str((datos.get("estadisticas") or {}).get(stat, "")).strip())
        except ValueError:
            errores.append(f"Falta la estadística '{stat}'")
            continue
        if estadisticas[stat] != avistamiento["estadisticas"][stat]:
            errores.append(f"La estadística '{stat}' no coincide con la ficha")
    habilidad = str(datos.get("habilidad") or "").strip()
    if normalizar(habilidad) != normalizar(avistamiento["habilidad"]):
        errores.append("La habilidad no coincide con la ficha")

    extras = {}
    for fila in (datos.get("extras") or [])[:6]:
        if not str(fila.get("campo") or "").strip():
            continue
        extras[nombre_de_campo(fila.get("campo"))] = valor_de_campo(fila.get("valor"))
    esperado = normalizar(avistamiento["dato_especial"]["valor"])
    if not any(normalizar(v) == esperado for v in extras.values()):
        errores.append(
            f"Falta el dato especial de la ficha ({avistamiento['dato_especial']['descripcion'].lower()}) "
            "en un campo extra")
    if errores:
        raise ErrorConsulta("Revisá la ficha: " + "; ".join(errores) + ".")

    forma = {"nombre": avistamiento["forma"], "tipos": tipos, "estadisticas": estadisticas,
             "habilidad": avistamiento["habilidad"]}
    forma.update(extras)
    return forma


def registrar_forma(db, avistamiento, forma, investigador):
    forma = dict(forma)
    forma["registrada_por"] = investigador["nombre"]
    forma["fecha_registro"] = datetime.now(timezone.utc)
    filtro = {"numero": avistamiento["numero"], "formas.nombre": {"$ne": avistamiento["forma"]}}
    actualizacion = {"$push": {"formas": forma}}
    resultado = db.pokemon.update_one(filtro, actualizacion)
    comando = (f"db.pokemon.updateOne(\n  {a_shell(filtro, 1)},\n  "
               f"{a_shell({'$push': {'formas': _para_mostrar(forma)}}, 1)}\n)")
    return resultado.modified_count == 1, comando


def agregar_dato(db, avistamiento, campo, valor, investigador):
    """Agrega un campo nuevo a una forma ya registrada usando el operador posicional $."""
    campo = nombre_de_campo(campo)
    valor = valor_de_campo(valor)
    pokemon = db.pokemon.find_one({"numero": avistamiento["numero"], "formas.nombre": avistamiento["forma"]},
                                  {"formas": 1})
    if not pokemon:
        raise ErrorConsulta("Esa forma todavía no está registrada: registrala primero")
    forma = next(f for f in pokemon["formas"] if f.get("nombre") == avistamiento["forma"])
    if campo in forma:
        raise ErrorConsulta(f"La forma ya tiene el campo '{campo}': elegí un dato nuevo")
    if len(forma) >= MAX_CAMPOS_FORMA:
        raise ErrorConsulta("Esta forma ya tiene demasiados datos")
    filtro = {"numero": avistamiento["numero"], "formas.nombre": avistamiento["forma"]}
    actualizacion = {"$set": {f"formas.$.{campo}": valor}}
    db.pokemon.update_one(filtro, actualizacion)
    comando = f"db.pokemon.updateOne(\n  {a_shell(filtro, 1)},\n  {a_shell(actualizacion, 1)}\n)"
    return comando


def _para_mostrar(forma):
    copia = {k: v for k, v in forma.items() if k != "fecha_registro"}
    copia["fecha_registro"] = "ISODate(...)"
    return copia


def documento_pokemon(db, numero):
    return a_json(db.pokemon.find_one({"numero": numero}))
