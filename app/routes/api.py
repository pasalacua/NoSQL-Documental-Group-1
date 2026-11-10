"""API JSON que usa el juego. Todas las operaciones van contra MongoDB."""
from functools import wraps

from flask import Blueprint, jsonify, request, session

from app.db import es_mongo_real, get_db
from app.misiones import MISIONES_POR_CLAVE
from app.services import agregacion, consultas, evaluar, formas, indices, progreso
from app.services.consultas import ErrorConsulta
from app.services.serializar import a_json

api = Blueprint("api", __name__)


@api.errorhandler(ErrorConsulta)
def _error_consulta(error):
    return jsonify({"error": str(error)}), 400


def _datos():
    return request.get_json(silent=True) or {}


def requiere_investigador(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        investigador = progreso.buscar_por_id(get_db(), session.get("investigador_id"))
        if not investigador:
            return jsonify({"error": "Tu sesión terminó: volvé a la pantalla de inicio."}), 401
        return funcion(investigador, *args, **kwargs)
    return envoltura


# --------------------------------------------------------------------------
# Estado y sesión
# --------------------------------------------------------------------------

@api.get("/estado")
def estado():
    db = get_db()
    try:
        return jsonify({"ok": True, "mongo_real": es_mongo_real(db), "base": db.name,
                        "pokemon": db.pokemon.count_documents({})})
    except Exception as error:
        return jsonify({"ok": False, "error": f"No hay conexión con MongoDB: {str(error)[:200]}"}), 503


@api.post("/investigadores")
def crear_investigador():
    investigador = progreso.crear_investigador(get_db(), _datos().get("nombre"))
    session["investigador_id"] = str(investigador["_id"])
    session.permanent = True
    return jsonify(progreso.perfil(investigador)), 201


@api.post("/investigadores/cargar")
def cargar_investigador():
    investigador = progreso.cargar_investigador(get_db(), _datos().get("nombre"))
    session["investigador_id"] = str(investigador["_id"])
    session.permanent = True
    return jsonify(progreso.perfil(investigador))


@api.get("/yo")
@requiere_investigador
def yo(investigador):
    return jsonify(progreso.perfil(investigador))


@api.post("/salir")
def salir():
    session.pop("investigador_id", None)
    return jsonify({"ok": True})


@api.get("/ranking")
def ranking():
    return jsonify(progreso.ranking(get_db()))


# --------------------------------------------------------------------------
# Misiones
# --------------------------------------------------------------------------

@api.get("/misiones")
@requiere_investigador
def listar_misiones(investigador):
    hechas = {m["clave"]: m for m in investigador.get("misiones", [])}
    lista = []
    for mision in get_db().misiones.find({}, {"_id": 0}).sort("orden", 1):
        mision["completada"] = mision["clave"] in hechas
        mision["puntos"] = hechas.get(mision["clave"], {}).get("puntos", 0)
        mision["fallos"] = investigador.get("intentos", {}).get(mision["clave"], 0)
        lista.append(mision)
    return jsonify(lista)


@api.post("/misiones/<clave>/entregar")
@requiere_investigador
def entregar(investigador, clave):
    db = get_db()
    mision = MISIONES_POR_CLAVE.get(clave)
    if not mision:
        return jsonify({"error": "Misión desconocida"}), 404
    datos = _datos()
    if mision["tipo"] == "busqueda":
        filtro, _ = consultas.filtro_desde_pedido(datos)
        resultado = evaluar.evaluar_busqueda(db, mision, filtro)
        resultado["comando"] = consultas.comando_find(filtro)
    elif mision["tipo"] == "agregacion":
        pipeline = agregacion.pipeline_desde_pedido(datos)
        resultado = evaluar.evaluar_agregacion(db, mision, pipeline)
    elif mision["tipo"] == "indices":
        actual = db.investigadores.find_one({"_id": investigador["_id"]}, {"planes_probados": 1}) or {}
        resultado = evaluar.evaluar_indices(db, mision, datos.get("plan"), actual.get("planes_probados"))
    else:
        return jsonify({"error": "Esta misión se completa registrando la forma"}), 400
    return jsonify(_cerrar_entrega(db, investigador, clave, resultado))


def _cerrar_entrega(db, investigador, clave, resultado):
    progreso.registrar_entrega(db, investigador, clave, resultado["correcta"], resultado.get("error"))
    ya_estaba = progreso.completada(investigador, clave)
    if resultado["correcta"]:
        resultado["puntos_ganados"] = progreso.completar_mision(db, investigador, clave)
    elif not ya_estaba:
        progreso.registrar_fallo(db, investigador, clave)
    resultado["ya_completada"] = ya_estaba
    resultado["perfil"] = progreso.perfil(progreso.buscar_por_id(db, investigador["_id"]))
    return resultado


# --------------------------------------------------------------------------
# Consultas (find)
# --------------------------------------------------------------------------

@api.get("/catalogo")
def catalogo():
    return jsonify(consultas.catalogo(get_db()))


@api.post("/consultas/previsualizar")
def previsualizar():
    filtro, visual = consultas.filtro_desde_pedido(_datos())
    respuesta = {"comando": consultas.comando_find(filtro), "filtro": filtro}
    if visual:
        respuesta.update(consultas.generar_sql(*visual))
    return jsonify(respuesta)


@api.post("/consultas/buscar")
@requiere_investigador
def buscar(investigador):
    db = get_db()
    filtro, visual = consultas.filtro_desde_pedido(_datos())
    resultado = consultas.ejecutar_busqueda(db, filtro)
    resultado["comando"] = consultas.comando_find(filtro)
    if visual:
        resultado.update(consultas.generar_sql(*visual))
    progreso.anotar_bitacora(db, investigador, "find", resultado["comando"], resultado["total"], resultado["plan"])
    return jsonify(resultado)


@api.get("/pokemon/<int:numero>")
def ver_pokemon(numero):
    documento = get_db().pokemon.find_one({"numero": numero})
    if not documento:
        return jsonify({"error": "No existe ese Pokémon"}), 404
    return jsonify(a_json(documento))


# --------------------------------------------------------------------------
# Agregación
# --------------------------------------------------------------------------

@api.get("/agregacion/tarjetas")
def tarjetas():
    return jsonify([{**t, "texto": consultas.a_shell(t["etapa"])} for t in agregacion.TARJETAS])


@api.post("/agregacion/ejecutar")
@requiere_investigador
def ejecutar_agregacion(investigador):
    db = get_db()
    pipeline = agregacion.pipeline_desde_pedido(_datos())
    resultado = agregacion.ejecutar_por_etapas(db, pipeline)
    progreso.anotar_bitacora(db, investigador, "aggregate", resultado["comando"], len(resultado["resultado"]))
    return jsonify(resultado)


# --------------------------------------------------------------------------
# Formas alternativas (escrituras)
# --------------------------------------------------------------------------

@api.get("/formas/avistamiento")
@requiere_investigador
def avistamiento(investigador):
    db = get_db()
    ficha = formas.asignar_avistamiento(db, investigador)
    respuesta = formas.estado_avistamiento(db, ficha)
    respuesta["documento"] = formas.documento_pokemon(db, ficha["numero"])
    return jsonify(respuesta)


@api.post("/formas")
@requiere_investigador
def registrar_forma(investigador):
    db = get_db()
    ficha = formas.asignar_avistamiento(db, investigador)
    forma = formas.construir_forma(_datos(), ficha)
    insertada, comando = formas.registrar_forma(db, ficha, forma, investigador)
    if not insertada:
        estado = formas.estado_avistamiento(db, ficha)
        estado["documento"] = formas.documento_pokemon(db, ficha["numero"])
        estado["error"] = ("Otro investigador registró esta forma hace instantes. Agregale un dato de campo "
                           "nuevo con el operador posicional $.")
        progreso.registrar_entrega(db, investigador, "verde", False, "forma_existente")
        return jsonify(estado), 409
    progreso.anotar_bitacora(db, investigador, "updateOne $push", comando)
    resultado = {"correcta": True, "mensaje": MISIONES_POR_CLAVE["verde"]["exito"], "comando": comando,
                 "documento": formas.documento_pokemon(db, ficha["numero"])}
    return jsonify(_cerrar_entrega(db, investigador, "verde", resultado))


@api.post("/formas/dato")
@requiere_investigador
def agregar_dato(investigador):
    db = get_db()
    ficha = formas.asignar_avistamiento(db, investigador)
    datos = _datos()
    comando = formas.agregar_dato(db, ficha, datos.get("campo"), datos.get("valor"), investigador)
    progreso.anotar_bitacora(db, investigador, "updateOne $set posicional", comando)
    resultado = {"correcta": True, "comando": comando, "documento": formas.documento_pokemon(db, ficha["numero"]),
                 "mensaje": ("¡Dato agregado! Usaste el operador posicional $ (formas.$.campo) para modificar "
                             "SOLO el elemento del array que coincidió con el filtro, sin reescribir el documento.")}
    return jsonify(_cerrar_entrega(db, investigador, "verde", resultado))


# --------------------------------------------------------------------------
# Índices y plan de ejecución
# --------------------------------------------------------------------------

@api.get("/indices/planes")
def planes():
    return jsonify({
        "filtro": consultas.a_shell(indices.filtro_mision()),
        "planes": [{k: v for k, v in p.items() if k != "hint"} for p in indices.PLANES],
        "indices": [i["name"] for i in get_db().pokemon.list_indexes()],
    })


@api.post("/indices/probar")
@requiere_investigador
def probar_plan(investigador):
    db = get_db()
    resultado = indices.probar_plan(db, _datos().get("plan"))
    if resultado.get("disponible"):
        db.investigadores.update_one({"_id": investigador["_id"]},
                                     {"$addToSet": {"planes_probados": resultado["plan"]}})
    progreso.anotar_bitacora(db, investigador, "explain", resultado["comando"], resultado.get("devueltos"),
                             resultado)
    return jsonify(resultado)


@api.get("/indices/motor")
@requiere_investigador
def plan_motor(investigador):
    return jsonify(indices.plan_del_motor(get_db()))
