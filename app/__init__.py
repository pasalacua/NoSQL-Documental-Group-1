from flask import Flask

from app.config import Config


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    app.json.ensure_ascii = False
    app.json.sort_keys = False  # respeta el orden de los campos del documento

    from app.routes.main import main
    from app.routes.api import api
    from app.routes.panel import panel

    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(panel)

    if app.config.get("AUTO_SEED"):
        with app.app_context():
            from app.db import get_db
            from database.seed import sembrar_si_vacia

            try:
                sembrar_si_vacia(get_db())
            except Exception as error:  # la app arranca igual y muestra el error en /api/estado
                app.logger.error("No se pudo preparar la base de datos: %s", error)

    return app
