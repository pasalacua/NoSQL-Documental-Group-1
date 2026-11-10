"""Corrección de las entregas de cada misión, con devoluciones que explican el porqué."""
from app.misiones import motivo
from app.services.consultas import ErrorConsulta
from app.services.indices import PLANES_POR_ID, mejores_planes, plan_del_motor

PIPELINE_COMPLETO = [{"$unwind": "$tipos"}, {"$group": {"_id": "$tipos", "total": {"$sum": 1}}}]


def _ficha(doc):
    return {"numero": doc.get("numero"), "nombre": doc.get("nombre")}


def evaluar_busqueda(db, mision, filtro):
    try:
        obtenidos = {d["_id"]: d for d in db.pokemon.find(filtro)}
    except Exception as error:
        raise ErrorConsulta(f"MongoDB rechazó la consulta: {str(error)[:160]}") from None
    esperados = {d["_id"]: d for d in db.pokemon.find(mision["criterio"])}

    sobran = []
    for _id, doc in obtenidos.items():
        if _id in esperados:
            continue
        razon = next((motivo(c, doc) for c in mision["condiciones"]
                      if db.pokemon.count_documents({"$and": [{"_id": _id}, c["filtro"]]}) == 0),
                     "no cumple lo que pidió el entrenador")
        sobran.append({**_ficha(doc), "motivo": razon})
    faltan = [{**_ficha(d), "motivo": "cumple todo lo que pidió el entrenador, pero tu filtro lo dejó afuera"}
              for _id, d in esperados.items() if _id not in obtenidos]

    trampa = False
    if mision.get("trampa") and sobran:
        ids_trampa = {d["_id"] for d in db.pokemon.find(mision["trampa"], {"_id": 1})} - set(esperados)
        trampa = any(_id in ids_trampa for _id in obtenidos)

    correcta = not sobran and not faltan
    if correcta:
        return {"correcta": True, "mensaje": mision["exito"], "error": None}
    if not obtenidos:
        mensaje = ("Tu consulta no devolvió ningún Pokémon. Revisá los nombres de los campos "
                   "(¿usaste notación de punto?) y los valores: mayúsculas y tildes cuentan.")
        error = "vacio"
    elif trampa:
        mensaje = ("¡Cuidado! Se colaron Pokémon que tienen Nado Rápido como habilidad NORMAL. "
                   "Con dos condiciones sueltas sobre un array de documentos, MongoDB acepta que cada "
                   "condición la cumpla un elemento distinto. Usá $elemMatch para exigir el MISMO elemento.")
        error = "trampa_elemmatch"
    else:
        partes = []
        if sobran:
            partes.append(f"sobran {len(sobran)}")
        if faltan:
            partes.append(f"faltan {len(faltan)}")
        mensaje = "Todavía no es lo que pidió el entrenador: " + " y ".join(partes) + "."
        error = "sobran" if sobran else "faltan"
    return {"correcta": False, "mensaje": mensaje, "error": error, "sobran": sobran, "faltan": faltan}


def evaluar_agregacion(db, mision, pipeline):
    cantidad = mision["cantidad"]
    completo = {f["_id"]: f["total"] for f in db.pokemon.aggregate(PIPELINE_COMPLETO)}
    esperado = sorted(completo.values(), reverse=True)[:cantidad]
    try:
        resultado = list(db.pokemon.aggregate(pipeline + [{"$limit": 100}]))
    except Exception as error:
        raise ErrorConsulta(f"MongoDB rechazó el pipeline: {str(error)[:160]}") from None

    def falla(mensaje, error):
        return {"correcta": False, "mensaje": mensaje, "error": error}

    if not resultado:
        return falla("El pipeline no devolvió ningún documento.", "vacio")
    if any(isinstance(r.get("_id"), list) for r in resultado):
        return falla("Agrupaste arrays enteros (por ejemplo [\"Fuego\", \"Volador\"]) en vez de tipos sueltos. "
                     "Te falta $unwind ANTES de $group.", "falta_unwind")
    totales = []
    for fila in resultado:
        numeros = [v for k, v in fila.items()
                   if k != "_id" and isinstance(v, (int, float)) and not isinstance(v, bool)]
        if not isinstance(fila.get("_id"), str) or len(numeros) != 1:
            return falla("Cada resultado tiene que verse así: { _id: \"Agua\", total: 12 }. "
                         "¿Agrupaste por tipo?", "formato")
        if completo.get(fila["_id"]) != numeros[0]:
            return falla("Los totales no coinciden con la Pokédex completa. ¿Filtraste documentos antes de "
                         "agrupar o contaste otra cosa?", "totales")
        totales.append(numeros[0])
    if len(resultado) > cantidad:
        return falla(f"Te sobran resultados: la entrenadora quiere solo {cantidad}. Falta $limit.", "falta_limit")
    if len(resultado) < cantidad:
        return falla(f"Faltan resultados: tienen que ser {cantidad} tipos.", "faltan")
    if totales != sorted(totales, reverse=True):
        return falla("Los tipos no están ordenados de mayor a menor. Falta $sort.", "orden")
    if totales != esperado:
        return falla("Esos no son los tipos con MÁS Pokémon. ¿Limitaste antes de ordenar? "
                     "El orden de las etapas importa.", "orden_limit")
    return {"correcta": True, "mensaje": mision["exito"], "error": None}


def evaluar_indices(db, mision, plan_id, probados):
    if plan_id not in PLANES_POR_ID:
        raise ErrorConsulta("Elegí uno de los planes")
    if len(set(probados or [])) < 2:
        return {"correcta": False, "error": "pocos_planes",
                "mensaje": "Antes de decidir, ejecutá al menos dos planes distintos y compará sus números."}
    mejores, mediciones = mejores_planes(db)
    motor = plan_del_motor(db)
    resumen = {pid: {"docs_examinados": m["docs_examinados"], "claves_examinadas": m["claves_examinadas"]}
               for pid, m in mediciones.items()}
    elegido = mediciones[plan_id]
    if plan_id in mejores:
        mensaje = mision["exito"]
        if motor.get("indice"):
            mensaje += f" El motor, sin ayuda, eligió el índice {motor['indice']}."
        return {"correcta": True, "mensaje": mensaje, "error": None, "mediciones": resumen, "motor": motor}
    mejor = mediciones[mejores[0]]
    return {"correcta": False, "error": "plan_ineficiente", "mediciones": resumen,
            "mensaje": (f"Ese plan examina {elegido['docs_examinados']} documentos. Hay uno que examina solo "
                        f"{mejor['docs_examinados']}: probá los que te falten.")}
