"""Conexión a MongoDB.

Se crea un único MongoClient por proceso (mantiene su propio pool de
conexiones) y cada request usa la misma instancia.
"""
from flask import current_app, g
from pymongo import MongoClient

_clientes = {}


def crear_cliente(uri):
    if uri.startswith("mongomock://"):
        # Solo para tests automáticos: base en memoria que imita a MongoDB.
        import mongomock

        return mongomock.MongoClient()
    return MongoClient(uri, serverSelectionTimeoutMS=8000, appname="pokelab")


def obtener_cliente(uri):
    if uri not in _clientes:
        _clientes[uri] = crear_cliente(uri)
    return _clientes[uri]


def get_db():
    """Devuelve la base de datos configurada para la app actual."""
    if "db" not in g:
        cliente = obtener_cliente(current_app.config["MONGO_URI"])
        g.db = cliente[current_app.config["MONGO_DB_NAME"]]
    return g.db


def es_mongo_real(db):
    return db.client.__class__.__module__.startswith("pymongo")
