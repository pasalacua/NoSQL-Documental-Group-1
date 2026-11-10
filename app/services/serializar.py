"""Conversión de documentos BSON a JSON para enviarlos al navegador."""
from datetime import datetime

from bson import ObjectId


def a_json(valor):
    if isinstance(valor, dict):
        return {clave: a_json(interno) for clave, interno in valor.items()}
    if isinstance(valor, list):
        return [a_json(interno) for interno in valor]
    if isinstance(valor, ObjectId):
        return str(valor)
    if isinstance(valor, datetime):
        return valor.isoformat(timespec="seconds")
    return valor
