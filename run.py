"""Punto de entrada.

    python run.py           servidor de desarrollo (recarga automática)
    python run.py --prod    servidor waitress, para la exposición con muchos celulares
"""
import os
import sys

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    if "--prod" in sys.argv:
        from waitress import serve

        print(f"POKÉLAB escuchando en http://{host}:{port}")
        serve(app, host=host, port=port, threads=16)
    else:
        app.run(host=host, port=port, debug=True)
