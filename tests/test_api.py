"""Recorridos completos de la API: partidas, misiones, escrituras y panel."""
from app.services import consultas
from tests.conftest import cond


def entregar(cliente, clave, **datos):
    return cliente.post(f"/api/misiones/{clave}/entregar", json=datos).get_json()


# ---------------------------------------------------------------- partidas

def test_crear_y_cargar_partida(cliente):
    assert cliente.post("/api/investigadores", json={"nombre": "Misty"}).status_code == 201
    repetido = cliente.post("/api/investigadores", json={"nombre": "misty"})
    assert repetido.status_code == 400 and "en uso" in repetido.get_json()["error"]
    cliente.post("/api/salir")
    assert cliente.get("/api/yo").status_code == 401
    assert cliente.post("/api/investigadores/cargar", json={"nombre": "MISTY"}).status_code == 200
    assert cliente.get("/api/yo").get_json()["nombre"] == "Misty"
    assert cliente.post("/api/investigadores/cargar", json={"nombre": "Nadie"}).status_code == 400


def test_nombre_invalido(cliente):
    assert cliente.post("/api/investigadores", json={"nombre": "<script>"}).status_code == 400


def test_partida_requiere_sesion(cliente):
    assert cliente.get("/partida").status_code == 302


def test_paginas_cargan(jugador):
    assert jugador.get("/").status_code == 200
    pagina = jugador.get("/partida")
    assert pagina.status_code == 200 and b"terminal-body" in pagina.data


def test_misiones_vienen_de_la_base(jugador, db):
    misiones = jugador.get("/api/misiones").get_json()
    assert [m["clave"] for m in misiones] == ["rojo", "azul", "amarilla", "verde", "plata"]
    assert "criterio" not in misiones[0]  # los criterios no salen del servidor
    assert db.misiones.count_documents({}) == 5


# ---------------------------------------------------------------- búsquedas

def test_busqueda_devuelve_documentos_y_sql(jugador):
    r = jugador.post("/api/consultas/buscar", json={"condiciones": [cond("tipos", "$eq", "Fuego")]}).get_json()
    assert r["total"] == 6
    assert all("Fuego" in d["tipos"] for d in r["documentos"])
    assert "db.pokemon.find" in r["comando"] and "pokemon_tipo" in r["sql"]


def test_mision_rojo_detecta_el_limite_y_luego_aprueba(jugador):
    mal = entregar(jugador, "rojo", condiciones=[cond("movimientos.nombre", "$eq", "Señuelo"),
                                                  cond("estadisticas.velocidad", "$gte", 60)])
    assert not mal["correcta"] and mal["sobran"][0]["nombre"] == "Clefable"
    assert "60" in mal["sobran"][0]["motivo"]
    bien = entregar(jugador, "rojo", modo="texto",
                    texto='{"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gt": 60}}')
    assert bien["correcta"] and bien["puntos_ganados"] == 85
    otra_vez = entregar(jugador, "rojo", modo="texto",
                        texto='{"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gt": 60}}')
    assert otra_vez["correcta"] and otra_vez["puntos_ganados"] == 0 and otra_vez["perfil"]["puntos"] == 85


def test_mision_azul_trampa_elemmatch(jugador, db):
    condiciones = [cond("tipos", "$eq", "Agua"), cond("habilidades.nombre", "$eq", "Nado Rápido"),
                   cond("habilidades.oculta", "$eq", "true")]
    trampa = entregar(jugador, "azul", condiciones=condiciones)
    assert trampa["error"] == "trampa_elemmatch"
    assert {p["nombre"] for p in trampa["sobran"]} == {"Kingdra", "Ludicolo", "Kabutops", "Magikarp"}
    bien = entregar(jugador, "azul", condiciones=condiciones, elem_match=["habilidades"])
    assert bien["correcta"]
    assert db.entregas.count_documents({"mision": "azul", "error": "trampa_elemmatch"}) == 1


def test_consulta_vacia_da_pista(jugador):
    r = entregar(jugador, "rojo", condiciones=[cond("movimientos.nombre", "$eq", "señuelo")])
    assert r["error"] == "vacio"


def test_previsualizar_no_requiere_ejecutar(cliente):
    r = cliente.post("/api/consultas/previsualizar",
                     json={"condiciones": [cond("estadisticas.ps", "$gte", 100)]}).get_json()
    assert r["filtro"] == {"estadisticas.ps": {"$gte": 100}} and "p.ps >= 100" in r["sql"]


def test_operador_peligroso_rechazado(jugador):
    r = jugador.post("/api/consultas/buscar", json={"modo": "texto", "texto": '{"$where": "true"}'})
    assert r.status_code == 400


# ---------------------------------------------------------------- agregación

def test_mision_amarilla_devoluciones(jugador):
    assert entregar(jugador, "amarilla", tarjetas=["group", "sort", "limit"])["error"] == "falta_unwind"
    assert entregar(jugador, "amarilla", tarjetas=["unwind", "group", "sort"])["error"] == "falta_limit"
    assert entregar(jugador, "amarilla", tarjetas=["match", "unwind", "group", "sort", "limit"])["error"] == "totales"
    assert entregar(jugador, "amarilla", tarjetas=["unwind", "group", "limit", "sort"])["error"] in ("orden_limit",
                                                                                                    "orden")
    assert entregar(jugador, "amarilla", tarjetas=["unwind", "group", "sort", "limit"])["correcta"]


def test_amarilla_acepta_pipeline_escrito_con_otros_nombres(jugador):
    texto = ('[{"$unwind": "$tipos"}, {"$group": {"_id": "$tipos", "cantidad": {"$sum": 1}}},'
             ' {"$sort": {"cantidad": -1}}, {"$limit": 3}]')
    assert entregar(jugador, "amarilla", modo="texto", texto=texto)["correcta"]


def test_ejecutar_pipeline_por_etapas(jugador):
    r = jugador.post("/api/agregacion/ejecutar", json={"tarjetas": ["unwind", "group"]}).get_json()
    assert r["etapas"][0]["cantidad"] > 43  # $unwind multiplica los documentos
    assert r["etapas"][1]["operador"] == "$group"


# ---------------------------------------------------------------- escrituras

def ficha(jugador):
    return jugador.get("/api/formas/avistamiento").get_json()


def datos_forma(a, **cambios):
    datos = {
        "numero": a["numero"], "nombre": a["forma"], "tipos": a["tipos"],
        "estadisticas": {k: str(v) for k, v in a["estadisticas"].items()}, "habilidad": a["habilidad"],
        "extras": [{"campo": "Dato Especial", "valor": a["dato_especial"]["valor"]}],
    }
    datos.update(cambios)
    return datos


def test_registrar_forma_embebida(jugador, db):
    a = ficha(jugador)["avistamiento"]
    mal = jugador.post("/api/formas", json=datos_forma(a, habilidad="Otra"))
    assert mal.status_code == 400 and "habilidad" in mal.get_json()["error"]
    sin_dato = jugador.post("/api/formas", json=datos_forma(a, extras=[]))
    assert sin_dato.status_code == 400
    r = jugador.post("/api/formas", json=datos_forma(a)).get_json()
    assert r["correcta"] and r["puntos_ganados"] == 100 and "$push" in r["comando"]
    doc = db.pokemon.find_one({"numero": a["numero"]})
    forma = next(f for f in doc["formas"] if f["nombre"] == a["forma"])
    assert forma["dato_especial"] == a["dato_especial"]["valor"]
    assert forma["registrada_por"] == "Ash"
    assert ficha(jugador)["ya_registrada"]


def test_forma_ya_registrada_usa_operador_posicional(cliente, db):
    cliente.post("/api/investigadores", json={"nombre": "Brock"})
    a = ficha(cliente)["avistamiento"]
    cliente.post("/api/formas", json=datos_forma(a))
    cliente.post("/api/salir")

    # Otro investigador recibe el mismo avistamiento ya registrado
    cliente.post("/api/investigadores", json={"nombre": "Tracey"})
    db.investigadores.update_one({"nombre": "Tracey"}, {"$set": {"avistamiento": a["clave"]}})
    estado = ficha(cliente)
    assert estado["ya_registrada"]
    conflicto = cliente.post("/api/formas", json=datos_forma(a))
    assert conflicto.status_code == 409
    r = cliente.post("/api/formas/dato", json={"campo": "clima", "valor": "Lluvioso"}).get_json()
    assert r["correcta"] and "formas.$.clima" in r["comando"]
    repetido = cliente.post("/api/formas/dato", json={"campo": "clima", "valor": "Soleado"})
    assert repetido.status_code == 400
    doc = db.pokemon.find_one({"numero": a["numero"]})
    formas = [f for f in doc["formas"] if f["nombre"] == a["forma"]]
    assert len(formas) == 1 and formas[0]["clima"] == "Lluvioso"


def test_campo_extra_invalido(jugador):
    a = ficha(jugador)["avistamiento"]
    r = jugador.post("/api/formas", json=datos_forma(a, extras=[{"campo": "$set", "valor": "x"}]))
    assert r.status_code == 400


def test_avistamientos_se_reparten(cliente, db):
    claves = set()
    for nombre in ("Uno", "Dos", "Tres", "Cuatro"):
        cliente.post("/api/salir")
        cliente.post("/api/investigadores", json={"nombre": nombre})
        claves.add(ficha(cliente)["avistamiento"]["clave"])
    assert len(claves) == 4


# ---------------------------------------------------------------- índices

def simular_explain(monkeypatch):
    """mongomock no implementa explain(): se simula lo que devolvería MongoDB."""
    costos = {
        repr({"$natural": 1}): ("COLLSCAN", None, 43, 0),
        "tipos_1": ("IXSCAN", "tipos_1", 43, 58),
        "estadisticas.velocidad_1": ("IXSCAN", "estadisticas.velocidad_1", 24, 24),
        "movimientos.nombre_1": ("IXSCAN", "movimientos.nombre_1", 4, 4),
        None: ("IXSCAN", "movimientos.nombre_1", 4, 4),
    }

    def falso(db, filtro, hint=None):
        clave = repr(hint) if isinstance(hint, dict) else hint
        etapa, indice, docs, claves = costos[clave]
        etapas = ["FETCH", etapa] if indice else [etapa]
        return {"disponible": True, "etapas": etapas, "indice": indice, "indices": [indice] if indice else [],
                "docs_examinados": docs, "claves_examinadas": claves, "devueltos": 2, "tiempo_ms": 0,
                "planes_descartados": 1}

    monkeypatch.setattr("app.services.indices.explicar", falso)


def test_mision_plata(jugador, monkeypatch):
    simular_explain(monkeypatch)
    assert entregar(jugador, "plata", plan="movimientos")["error"] == "pocos_planes"
    for plan in ("coleccion", "velocidad"):
        r = jugador.post("/api/indices/probar", json={"plan": plan}).get_json()
        assert r["disponible"]
    mal = entregar(jugador, "plata", plan="velocidad")
    assert not mal["correcta"] and mal["error"] == "plan_ineficiente"
    bien = entregar(jugador, "plata", plan="movimientos")
    assert bien["correcta"] and "movimientos.nombre_1" in bien["mensaje"]


def test_planes_listan_indices(jugador):
    r = jugador.get("/api/indices/planes").get_json()
    assert {"tipos_1", "movimientos.nombre_1", "estadisticas.velocidad_1"} <= set(r["indices"])


def test_explain_sin_soporte_no_rompe(jugador):
    r = jugador.post("/api/indices/probar", json={"plan": "coleccion"}).get_json()
    assert r["disponible"] is False


# ---------------------------------------------------------------- ranking y panel

def test_ranking_ordenado(cliente):
    for nombre in ("Gary", "Red"):
        cliente.post("/api/salir")
        cliente.post("/api/investigadores", json={"nombre": nombre})
    entregar(cliente, "rojo", modo="texto", texto='{"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gt": 60}}')
    ranking = cliente.get("/api/ranking").get_json()
    assert ranking[0] == {"nombre": "Red", "puntos": 100, "completadas": 1}


def test_panel_requiere_pin(cliente):
    assert cliente.get("/api/panel/resumen").status_code == 401
    assert cliente.post("/panel/ingresar", json={"pin": "0000"}).status_code == 403
    assert cliente.post("/panel/ingresar", json={"pin": "4321"}).status_code == 200
    resumen = cliente.get("/api/panel/resumen").get_json()
    assert len(resumen["misiones"]) == 5


def test_panel_editar_y_reiniciar(cliente, db, jugador):
    cliente.post("/panel/ingresar", json={"pin": "4321"})
    r = cliente.post("/api/panel/editar", json={"numero": 25, "operacion": "$inc",
                                                "campo": "estadisticas.velocidad", "valor": "10"}).get_json()
    assert r["documento"]["estadisticas"]["velocidad"] == 100
    r = cliente.post("/api/panel/editar", json={"numero": 25, "operacion": "$addToSet", "campo": "movimientos",
                                                "valor": '{"nombre": "Surf", "tipo": "Agua", "categoria": "Especial", "potencia": 90}'})
    assert r.status_code == 200
    assert cliente.post("/api/panel/editar", json={"numero": 25, "operacion": "$set", "campo": "_id",
                                                   "valor": "1"}).status_code == 400
    assert cliente.post("/api/panel/editar", json={"numero": 25, "operacion": "$rename", "campo": "nombre",
                                                   "valor": "x"}).status_code == 400
    assert cliente.post("/api/panel/editar", json={"numero": 25, "operacion": "$set", "campo": "x",
                                                   "valor": '{"$gt": 1}'}).status_code == 400
    resumen = cliente.post("/api/panel/reiniciar", json={"borrar_investigadores": False}).get_json()
    assert resumen["pokemon"] == 43 and resumen["investigadores"] == 1
    assert db.pokemon.find_one({"numero": 25})["estadisticas"]["velocidad"] == 90
    assert cliente.post("/api/panel/reiniciar", json={"borrar_investigadores": True}).get_json()["investigadores"] == 0


def test_catalogo_usa_distinct(cliente):
    catalogo = cliente.get("/api/catalogo").get_json()
    assert "Señuelo" in catalogo["valores"]["movimientos.nombre"]
    assert len(catalogo["pokemon"]) == 43
    assert {c["campo"] for c in catalogo["campos"]} >= {"estadisticas.velocidad", "habilidades.oculta"}
    assert consultas.MAX_RESULTADOS >= 43
