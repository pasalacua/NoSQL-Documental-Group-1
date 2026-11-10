# Cómo correr POKÉLAB

## 1. Instalar

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```

## 2. Elegir la base de datos

### Opción A · MongoDB Atlas (recomendada para la exposición)

1. Crear un cluster gratuito (M0) en <https://cloud.mongodb.com>.
2. *Database Access*: crear un usuario con permiso de lectura y escritura.
3. *Network Access*: agregar la IP de la máquina que corre el servidor (o `0.0.0.0/0` solo para la demo).
4. *Connect → Drivers*: copiar la URI `mongodb+srv://...` y pegarla en `MONGO_URI` del `.env`.

### Opción B · MongoDB local

Instalar MongoDB Community Server (o `docker compose up -d` con el `docker-compose.yml` del repo) y dejar
`MONGO_URI=mongodb://localhost:27017`.

## 3. Cargar los datos

El juego carga la Pokédex solo la primera vez que arranca. Para reiniciarla a mano:

```bash
python -m database.seed          # recarga Pokémon, misiones y avistamientos
python -m database.seed --todo   # además borra jugadores, entregas y bitácora
```

También se puede reiniciar desde el panel del expositor.

## 4. Ejecutar

```bash
python run.py          # desarrollo
python run.py --prod   # exposición (servidor waitress, aguanta muchos celulares)
```

- Juego: `http://localhost:5000`
- Panel del expositor: `http://localhost:5000/panel` (PIN en `PANEL_PIN`)
- Estado de la conexión: `http://localhost:5000/api/estado`

Con `HOST=0.0.0.0` los celulares conectados a la **misma red Wi-Fi** entran con la IP de la
notebook (el panel la muestra, por ejemplo `http://192.168.0.15:5000`). Si la red del colegio aísla
los dispositivos, usar el hotspot de un celular.

## 5. Publicarlo en internet (opcional)

Cualquier servicio que corra Python sirve (Render, Railway, Fly.io...):

- Comando de inicio: `waitress-serve --host=0.0.0.0 --port=$PORT run:app`
- Variables de entorno: las mismas del `.env` (`MONGO_URI`, `MONGO_DB_NAME`, `SECRET_KEY`, `PANEL_PIN`).
- En Atlas, permitir el acceso desde las IP del servicio.

## 6. Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Los tests usan `mongomock` (una imitación de MongoDB en memoria), así que no necesitan servidor.
`explain()`, `$jsonSchema` y las colecciones *capped* solo se pueden probar contra un MongoDB real.
