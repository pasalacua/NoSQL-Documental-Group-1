"""Configuración leída desde variables de entorno (archivo .env)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pokelab")
    SECRET_KEY = os.getenv("SECRET_KEY", "pokelab-clave-de-desarrollo")
    PANEL_PIN = os.getenv("PANEL_PIN", "1234")
    # Si la colección pokemon está vacía al arrancar, se carga sola.
    AUTO_SEED = os.getenv("AUTO_SEED", "1") == "1"
    JSON_AS_ASCII = False
