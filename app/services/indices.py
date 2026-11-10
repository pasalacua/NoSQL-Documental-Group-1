"""Comparación de planes de ejecución (misión del Ingeniero Plata).

El jugador fuerza cada plan con `hint()` y compara cuántos documentos y
claves de índice examinó el motor. Después se compara su elección con la
del planificador de consultas de MongoDB (la consulta sin hint).
"""
from app.misiones import MISIONES_POR_CLAVE
from app.services.consultas import ErrorConsulta, a_shell, explicar

PLANES = [
    {"id": "coleccion", "etiqueta": "Sin índice: recorrer toda la colección", "hint": {"$natural": 1},
     "hint_texto": "{ $natural: 1 }"},
    {"id": "tipos", "etiqueta": "Índice sobre tipos", "hint": "tipos_1", "hint_texto": '"tipos_1"'},
    {"id": "velocidad", "etiqueta": "Índice sobre estadisticas.velocidad", "hint": "estadisticas.velocidad_1",
     "hint_texto": '"estadisticas.velocidad_1"'},
    {"id": "movimientos", "etiqueta": "Índice sobre movimientos.nombre", "hint": "movimientos.nombre_1",
     "hint_texto": '"movimientos.nombre_1"'},
]
PLANES_POR_ID = {p["id"]: p for p in PLANES}


def filtro_mision():
    return MISIONES_POR_CLAVE["plata"]["filtro"]


def probar_plan(db, plan_id):
    plan = PLANES_POR_ID.get(plan_id)
    if not plan:
        raise ErrorConsulta("Plan desconocido")
    filtro = filtro_mision()
    resultado = explicar(db, filtro, plan["hint"])
    resultado["plan"] = plan_id
    resultado["comando"] = f"db.pokemon.find({a_shell(filtro)})\n  .hint({plan['hint_texto']})\n  .explain(\"executionStats\")"
    return resultado


def plan_del_motor(db):
    filtro = filtro_mision()
    resultado = explicar(db, filtro)
    resultado["comando"] = f"db.pokemon.find({a_shell(filtro)}).explain(\"executionStats\")"
    if resultado.get("disponible"):
        indice = resultado.get("indice")
        resultado["plan"] = next((p["id"] for p in PLANES if p["hint"] == indice), "coleccion" if not indice else None)
    return resultado


def mejores_planes(db):
    """Devuelve (ids de los planes que examinan menos documentos, mediciones por plan)."""
    mediciones = {p["id"]: probar_plan(db, p["id"]) for p in PLANES}
    if not all(m.get("disponible") for m in mediciones.values()):
        raise ErrorConsulta("Este servidor de MongoDB no permite usar explain(); no se puede evaluar la misión")

    def costo(m):
        return (m["docs_examinados"] or 0, m["claves_examinadas"] or 0)

    minimo = min(costo(m) for m in mediciones.values())
    return [pid for pid, m in mediciones.items() if costo(m) == minimo], mediciones
