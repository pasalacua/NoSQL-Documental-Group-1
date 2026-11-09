
from flask import Flask


def create_app():
    # Creamos la instancia principal de Flask
    app = Flask(__name__)

    # Registramos las rutas principales de la aplicación
    from app.routes.main import main
    app.register_blueprint(main)

    return app
