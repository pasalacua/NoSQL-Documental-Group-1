"""Verifica que el servidor de MongoDB configurado soporte todo lo que usa el juego.

Uso (desde la raíz del proyecto, con el .env completo):
    python -m database.verificar

Trabaja sobre una base temporal (pokelab_verificacion) que se borra al final,
así que no toca los datos del juego.
"""
import os
import sys
from pathlib import Path

from pymongo.errors import PyMongoError, WriteError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config  # noqa: E402
from app.db import crear_cliente  # noqa: E402
from app.misiones import MISIONES_POR_CLAVE  # noqa: E402
from app.services.consultas import explicar  # noqa: E402
from app.services.indices import PLANES  # noqa: E402
from database.seed import sembrar  # noqa: E402

BASE_TEMPORAL = os.getenv("MONGO_DB_VERIFICACION", "pokelab_verificacion")
resultados = []


def chequear(descripcion, condicion, detalle="", critico=True):
    if critico:
        resultados.append(condicion)
    marca = "✓" if condicion else ("✗" if critico else "·")
    print(f"  {marca} {descripcion}{f'  ({detalle})' if detalle else ''}")


def opciones(coleccion):
    try:
        return coleccion.options()
    except Exception:
        return {}


def main():
    print(f"Conectando a {Config.MONGO_URI.split('@')[-1]} ...")
    cliente = crear_cliente(Config.MONGO_URI)
    try:
        version = cliente.server_info().get("version", "?")
    except PyMongoError as error:
        print(f"  ✗ No hay conexión con MongoDB: {error}")
        return 1
    print(f"  ✓ Conectado (MongoDB {version}). Base temporal: {BASE_TEMPORAL}\n")

    db = cliente[BASE_TEMPORAL]
    cliente.drop_database(BASE_TEMPORAL)
    try:
        resumen = sembrar(db, borrar_investigadores=True)
        chequear("Carga de datos", resumen["pokemon"] == 43, f"{resumen['pokemon']} Pokémon")

        con_validador = "validator" in opciones(db.pokemon)
        chequear("Validador $jsonSchema activo", con_validador, critico=False)
        if con_validador:
            try:
                db.pokemon.insert_one({"numero": 999, "nombre": "MissingNo", "tipos": [7]})
                chequear("El validador rechaza documentos inválidos", False, "se insertó un documento inválido")
            except WriteError as error:
                chequear("El validador rechaza documentos inválidos", error.code == 121, f"código {error.code}")

        chequear("Bitácora como colección capped", opciones(db.bitacora).get("capped", False) is True,
                 "opcional: si no, el juego usa una colección normal", critico=False)

        rojo = sorted(d["nombre"] for d in db.pokemon.find(MISIONES_POR_CLAVE["rojo"]["criterio"]))
        chequear("Consulta con notación de punto (Rojo)", rojo == ["Pachirisu", "Togekiss"], ", ".join(rojo))
        azul = sorted(d["nombre"] for d in db.pokemon.find(MISIONES_POR_CLAVE["azul"]["criterio"]))
        trampa = db.pokemon.count_documents(MISIONES_POR_CLAVE["azul"]["trampa"])
        chequear("$elemMatch vs. condiciones sueltas (Azul)", len(azul) == 3 and trampa == 7,
                 f"con $elemMatch {len(azul)}, sin $elemMatch {trampa}")
        top = list(db.pokemon.aggregate(MISIONES_POR_CLAVE["amarilla"]["pipeline"]))
        chequear("Pipeline de agregación (Amarilla)", len(top) == 3,
                 ", ".join(f"{t['_id']}={t['total']}" for t in top))

        print("\n  Planes de ejecución (Plata):")
        filtro = MISIONES_POR_CLAVE["plata"]["filtro"]
        costos = {}
        for plan in PLANES:
            r = explicar(db, filtro, plan["hint"])
            if not r.get("disponible"):
                chequear(f"explain() con {plan['id']}", False, r.get("motivo", ""))
                continue
            costos[plan["id"]] = r["docs_examinados"]
            print(f"    - {plan['etiqueta']}: {' → '.join(r['etapas'])} · docs {r['docs_examinados']}"
                  f" · claves {r['claves_examinadas']} · devueltos {r['devueltos']}")
        motor = explicar(db, filtro)
        chequear("explain() disponible", len(costos) == len(PLANES))
        if costos:
            mejor = min(costos, key=costos.get)
            chequear("El índice de movimientos es el plan más eficiente", mejor == "movimientos",
                     f"mejor: {mejor}")
            chequear("El planificador elige ese mismo índice", motor.get("indice") == "movimientos.nombre_1",
                     f"eligió: {motor.get('indice')}", critico=False)
    finally:
        cliente.drop_database(BASE_TEMPORAL)

    ok = all(resultados)
    print(f"\n{'Todo listo para la exposición.' if ok else 'Hay puntos para revisar (ver ✗).'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
