"""Carga inicial de la base de datos del laboratorio.

Uso:
    python -m database.seed            # recarga Pokémon, misiones y avistamientos
    python -m database.seed --todo     # además borra investigadores, entregas y bitácora

Colecciones:
    pokemon        un documento por Pokémon, con documentos anidados y arrays
    misiones       textos de las misiones que lee el juego
    avistamientos  fichas de formas alternativas para registrar
    investigadores jugadores y su progreso
    entregas       cada intento de resolver una misión (para el panel)
    bitacora       colección limitada (capped) con las últimas operaciones
"""
import json
import sys
from pathlib import Path

from pymongo import ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid, OperationFailure

CARPETA_DATOS = Path(__file__).resolve().parent / "data"

TIPOS = [
    "Normal", "Fuego", "Agua", "Planta", "Eléctrico", "Hielo", "Lucha", "Veneno", "Tierra",
    "Volador", "Psíquico", "Bicho", "Roca", "Fantasma", "Dragón", "Siniestro", "Acero", "Hada",
]
ESTADISTICAS = ["ps", "ataque", "defensa", "ataque_especial", "defensa_especial", "velocidad"]

# Validación de esquema: exige la estructura base de cada Pokémon pero deja
# agregar campos nuevos (por eso no se usa additionalProperties: false).
VALIDADOR_POKEMON = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["numero", "nombre", "tipos", "estadisticas", "habilidades", "movimientos"],
        "properties": {
            "numero": {"bsonType": "int", "minimum": 1},
            "nombre": {"bsonType": "string", "minLength": 1},
            "generacion": {"bsonType": "int", "minimum": 1},
            "tipos": {"bsonType": "array", "minItems": 1, "maxItems": 2, "items": {"enum": TIPOS}},
            "estadisticas": {
                "bsonType": "object",
                "required": ESTADISTICAS,
                "properties": {e: {"bsonType": "int", "minimum": 1, "maximum": 255} for e in ESTADISTICAS},
            },
            "habilidades": {
                "bsonType": "array",
                "items": {"bsonType": "object", "required": ["nombre", "oculta"],
                          "properties": {"nombre": {"bsonType": "string"}, "oculta": {"bsonType": "bool"}}},
            },
            "movimientos": {
                "bsonType": "array",
                "items": {"bsonType": "object", "required": ["nombre", "tipo", "categoria"],
                          "properties": {"nombre": {"bsonType": "string"}, "tipo": {"enum": TIPOS},
                                         "categoria": {"enum": ["Físico", "Especial", "Estado"]}}},
            },
            "formas": {
                "bsonType": "array",
                "items": {"bsonType": "object", "required": ["nombre", "tipos"]},
            },
        },
    }
}


def cargar_json(nombre):
    with open(CARPETA_DATOS / nombre, encoding="utf-8") as archivo:
        return json.load(archivo)


def preparar_colecciones(db):
    existentes = set(db.list_collection_names())

    if "pokemon" not in existentes:
        try:
            db.create_collection("pokemon", validator=VALIDADOR_POKEMON, validationLevel="strict")
        except (CollectionInvalid, OperationFailure, NotImplementedError, TypeError):
            pass
    else:
        try:
            db.command("collMod", "pokemon", validator=VALIDADOR_POKEMON, validationLevel="strict")
        except Exception:
            pass  # algunos planes gratuitos o mongomock no lo permiten; el juego funciona igual

    if "bitacora" not in existentes:
        try:
            db.create_collection("bitacora", capped=True, size=512 * 1024, max=300)
        except Exception:
            pass

    db.pokemon.create_index([("numero", ASCENDING)], unique=True, name="numero_1")
    db.pokemon.create_index([("nombre", ASCENDING)], unique=True, name="nombre_1")
    db.pokemon.create_index([("tipos", ASCENDING)], name="tipos_1")  # índice multiclave (array)
    db.pokemon.create_index([("estadisticas.velocidad", ASCENDING)], name="estadisticas.velocidad_1")
    db.pokemon.create_index([("movimientos.nombre", ASCENDING)], name="movimientos.nombre_1")
    db.pokemon.create_index([("habilidades.nombre", ASCENDING)], name="habilidades.nombre_1")
    db.misiones.create_index([("clave", ASCENDING)], unique=True)
    db.avistamientos.create_index([("clave", ASCENDING)], unique=True)
    db.investigadores.create_index([("nombre_clave", ASCENDING)], unique=True)
    db.investigadores.create_index([("puntos", DESCENDING)])
    db.entregas.create_index([("mision", ASCENDING), ("correcta", ASCENDING)])


def sembrar(db, borrar_investigadores=False):
    from app.misiones import MISIONES, documento_publico

    preparar_colecciones(db)

    db.pokemon.delete_many({})
    db.pokemon.insert_many(cargar_json("pokemon.json"))

    db.misiones.delete_many({})
    db.misiones.insert_many([documento_publico(m) for m in MISIONES])

    db.avistamientos.delete_many({})
    db.avistamientos.insert_many(cargar_json("avistamientos.json"))

    if borrar_investigadores:
        db.investigadores.delete_many({})
        db.entregas.delete_many({})
        try:
            db.bitacora.drop()  # una colección capped no admite delete_many
            db.create_collection("bitacora", capped=True, size=512 * 1024, max=300)
        except Exception:
            pass
    else:
        # Los avistamientos asignados apuntan a formas que se borraron con la recarga.
        db.investigadores.update_many({}, {"$unset": {"avistamiento": ""}})

    return {
        "pokemon": db.pokemon.count_documents({}),
        "misiones": db.misiones.count_documents({}),
        "avistamientos": db.avistamientos.count_documents({}),
        "investigadores": db.investigadores.count_documents({}),
    }


def sembrar_si_vacia(db):
    if db.pokemon.estimated_document_count() == 0:
        return sembrar(db)
    preparar_colecciones(db)
    return None


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.config import Config
    from app.db import obtener_cliente

    db = obtener_cliente(Config.MONGO_URI)[Config.MONGO_DB_NAME]
    resumen = sembrar(db, borrar_investigadores="--todo" in sys.argv)
    print(f"Base '{Config.MONGO_DB_NAME}' lista:", ", ".join(f"{k}={v}" for k, v in resumen.items()))


if __name__ == "__main__":
    main()
