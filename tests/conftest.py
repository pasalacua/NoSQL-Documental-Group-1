"""Los tests usan mongomock: una imitación de MongoDB en memoria.

Así se pueden correr sin servidor. Lo que mongomock no implementa
(explain, validación $jsonSchema, colecciones capped) se prueba aparte o
se simula.
"""
import uuid

import pytest

from app import create_app
from app.db import obtener_cliente


@pytest.fixture
def app():
    nombre_base = f"pokelab_test_{uuid.uuid4().hex[:8]}"
    aplicacion = create_app({
        "TESTING": True,
        "MONGO_URI": "mongomock://tests",
        "MONGO_DB_NAME": nombre_base,
        "PANEL_PIN": "4321",
        "AUTO_SEED": True,
    })
    yield aplicacion
    obtener_cliente("mongomock://tests").drop_database(nombre_base)


@pytest.fixture
def db(app):
    return obtener_cliente("mongomock://tests")[app.config["MONGO_DB_NAME"]]


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def jugador(cliente):
    respuesta = cliente.post("/api/investigadores", json={"nombre": "Ash"})
    assert respuesta.status_code == 201
    return cliente


def cond(campo, operador, valor):
    return {"campo": campo, "operador": operador, "valor": valor}
