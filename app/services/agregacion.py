"""Pipeline de agregación armado por el jugador (misión de la Entrenadora Amarilla)."""
import json

from app.services.consultas import OPERADORES_FILTRO, ErrorConsulta, a_shell, sanear
from app.services.serializar import a_json

# Tarjetas que el jugador ordena para armar el pipeline.
TARJETAS = [
    {"id": "unwind", "etapa": {"$unwind": "$tipos"},
     "explicacion": "Desarma el array 'tipos': genera un documento por cada tipo del Pokémon."},
    {"id": "group", "etapa": {"$group": {"_id": "$tipos", "total": {"$sum": 1}}},
     "explicacion": "Agrupa los documentos por el valor de 'tipos' y cuenta cuántos hay en cada grupo."},
    {"id": "sort", "etapa": {"$sort": {"total": -1, "_id": 1}},
     "explicacion": "Ordena por 'total' de mayor a menor (y por nombre si hay empate)."},
    {"id": "limit", "etapa": {"$limit": 3},
     "explicacion": "Deja pasar solo los 3 primeros documentos."},
    {"id": "match", "etapa": {"$match": {"generacion": 1}},
     "explicacion": "Filtra: deja pasar solo los Pokémon de la 1.ª generación."},
    {"id": "project", "etapa": {"$project": {"_id": 0, "nombre": 1, "tipos": 1}},
     "explicacion": "Proyección: muestra solo 'nombre' y 'tipos'."},
    {"id": "count", "etapa": {"$count": "total"},
     "explicacion": "Cuenta cuántos documentos llegan a esta etapa."},
]
TARJETAS_POR_ID = {t["id"]: t for t in TARJETAS}

ETAPAS_PERMITIDAS = {
    "$match", "$unwind", "$group", "$sort", "$limit", "$skip", "$project", "$count",
    "$addFields", "$set", "$sortByCount", "$unset",
}
EXPRESIONES_PERMITIDAS = OPERADORES_FILTRO | ETAPAS_PERMITIDAS | {
    "$sum", "$avg", "$min", "$max", "$first", "$last", "$push", "$addToSet", "$size", "$round",
    "$concat", "$toUpper", "$toLower", "$cond", "$ifNull", "$add", "$subtract", "$multiply",
    "$divide", "$arrayElemAt", "$literal", "$path", "$preserveNullAndEmptyArrays",
}
MAX_ETAPAS = 8


def pipeline_desde_pedido(datos):
    datos = datos or {}
    if datos.get("modo") == "texto":
        texto = datos.get("texto", "")
        if not isinstance(texto, str) or not texto.strip():
            raise ErrorConsulta("Escribí el pipeline como una lista de etapas: [ {...}, {...} ]")
        if len(texto) > 3000:
            raise ErrorConsulta("El pipeline es demasiado largo")
        try:
            pipeline = json.loads(texto)
        except json.JSONDecodeError as error:
            raise ErrorConsulta(f"No pude leer el pipeline: revisá el JSON ({error.msg})") from None
    else:
        ids = datos.get("tarjetas") or []
        if not isinstance(ids, list):
            raise ErrorConsulta("Formato de pipeline inválido")
        try:
            pipeline = [TARJETAS_POR_ID[i]["etapa"] for i in ids]
        except (KeyError, TypeError):
            raise ErrorConsulta("Hay una tarjeta desconocida en el pipeline") from None
    validar_pipeline(pipeline)
    return pipeline


def validar_pipeline(pipeline):
    if not isinstance(pipeline, list) or not pipeline:
        raise ErrorConsulta("El pipeline tiene que tener al menos una etapa")
    if len(pipeline) > MAX_ETAPAS:
        raise ErrorConsulta(f"Máximo {MAX_ETAPAS} etapas")
    for etapa in pipeline:
        if not isinstance(etapa, dict) or len(etapa) != 1:
            raise ErrorConsulta("Cada etapa debe ser un documento con un solo operador, por ejemplo { $limit: 3 }")
        nombre = next(iter(etapa))
        if nombre not in ETAPAS_PERMITIDAS:
            raise ErrorConsulta(f"La etapa {nombre} no está habilitada en el laboratorio")
    sanear(pipeline, EXPRESIONES_PERMITIDAS)


def ejecutar_por_etapas(db, pipeline):
    """Ejecuta el pipeline etapa por etapa para mostrar qué sale de cada una."""
    etapas = []
    resultado = []
    for i in range(len(pipeline)):
        try:
            resultado = list(db.pokemon.aggregate(pipeline[: i + 1] + [{"$limit": 500}]))
        except Exception as error:
            raise ErrorConsulta(
                f"MongoDB rechazó la etapa {i + 1} ({next(iter(pipeline[i]))}): {str(error)[:140]}") from None
        etapas.append({
            "etapa": a_shell(pipeline[i]),
            "operador": next(iter(pipeline[i])),
            "cantidad": len(resultado),
            "muestra": [a_json(_resumir(d)) for d in resultado[:4]],
        })
    return {
        "comando": "db.pokemon.aggregate([\n  " + ",\n  ".join(a_shell(e, 1) for e in pipeline) + "\n])",
        "etapas": etapas,
        "resultado": [a_json(d) for d in resultado[:50]],
    }


def _resumir(doc):
    """Achica documentos enteros para que la muestra entre en pantalla."""
    if "movimientos" in doc or "habilidades" in doc:
        return {k: v for k, v in doc.items() if k in ("_id", "numero", "nombre", "tipos", "generacion")}
    return doc
