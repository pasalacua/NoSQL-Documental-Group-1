# PokéLab Group 1

# POKÉLAB — Pokémon Research Database

**POKÉLAB** es una aplicación web interactiva ambientada en un laboratorio de investigación Pokémon, desarrollada como parte del Trabajo Práctico Integrador N.º 2 de Base de Datos 2 del Instituto Técnico Salesiano Villada.

El proyecto busca demostrar las características del modelo documental de **MongoDB** mediante diferentes operaciones sobre una Pokédex.

Los usuarios asumirán el rol de investigadores encargados de administrar información sobre Pokémon, registrar formas alternativas y resolver solicitudes de otros entrenadores.

## 🎯 Objetivos

- Explorar las características del modelo documental de MongoDB.
- Trabajar con documentos anidados y arrays de documentos.
- Realizar consultas con múltiples condiciones.
- Experimentar con la flexibilidad del esquema documental.
- Implementar operaciones de inserción, consulta y actualización.

## ⚙️ Tecnologías

| Tecnología | Utilización |
|---|---|
| Python | Lenguaje del backend |
| Flask | Framework web |
| HTML5 | Estructura de la interfaz |
| CSS3 | Diseño visual |
| JavaScript | Interactividad del frontend |
| MongoDB | Base de datos documental |
| MongoDB Atlas | Alojamiento de la base de datos |

## 🎮 Cómo se juega

Cada participante entra desde su celular, crea su **investigador** (un documento en la colección
`investigadores`) y ayuda a los entrenadores que visitan el laboratorio. Cada pedido se resuelve
operando directamente sobre MongoDB desde la **terminal de la Pokédex**:

| Entrenador | Pedido | Concepto de MongoDB |
|---|---|---|
| 🧢 Rojo | Pokémon que conozcan Señuelo y tengan más de 60 de velocidad | Notación de punto en documentos anidados y arrays de documentos |
| 👩 Azul | Pokémon de tipo Agua cuya habilidad **oculta** sea Nado Rápido | `$elemMatch` (la trampa de los arrays de documentos) |
| 🎒 Amarilla | Los 3 tipos con más Pokémon | Pipeline de agregación (`$unwind`, `$group`, `$sort`, `$limit`) |
| 🧑 Verde | Registrar una forma alternativa (Megaevolución, forma regional...) | Esquema flexible, documentos embebidos, `$push` y operador posicional `$` |
| 🔧 Plata | Elegir el plan de ejecución más eficiente | Índices, `hint()` y `explain()` (planificador de consultas) |

La terminal muestra siempre el comando real de MongoDB, el **SQL equivalente** en un modelo
relacional y cuántas tablas/filas ocuparía cada documento. El cuaderno de investigación funciona
como ayuda-memoria de sintaxis.

El **panel del expositor** (`/panel`, protegido con PIN) muestra en vivo, con pipelines de
agregación: la URL para entrar, cuántos cayeron en cada error, las formas que escribió el público,
la bitácora de operaciones (colección *capped*), el ranking, un editor de documentos
(`$set`, `$inc`, `$unset`, `$push`, `$addToSet`, `$pull`) y el reinicio de la base.

## 🗂️ Estructura del proyecto

```text
NoSQL-Documental-Group-1/
├── app/
│   ├── __init__.py          # create_app: config, blueprints y carga inicial
│   ├── config.py            # variables de entorno (.env)
│   ├── db.py                # conexión a MongoDB (pymongo)
│   ├── misiones.py          # misiones y criterios de corrección
│   ├── routes/              # páginas (main), API JSON (api) y panel del expositor
│   ├── services/            # consultas, agregación, formas, índices, progreso y corrección
│   ├── static/              # css, js y assets (apartado gráfico)
│   └── templates/
├── database/
│   ├── seed.py              # colecciones, validador $jsonSchema, índices y datos
│   └── data/                # pokemon.json y avistamientos.json
├── docs/                    # modelo de datos, guión de la experiencia y despliegue
├── tests/                   # pytest + mongomock
├── tools/                   # recortes de sprites (apartado gráfico)
├── .env.example
├── docker-compose.yml       # MongoDB local opcional
├── requirements.txt
└── run.py
```

## 🚀 Instalación y ejecución

```bash
git clone <URL_DEL_REPOSITORIO>
cd NoSQL-Documental-Group-1
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # completar MONGO_URI (Atlas o local)
python run.py                   # o: python run.py --prod para la exposición
```

- Juego: `http://localhost:5000` · Panel: `http://localhost:5000/panel`
- La Pokédex se carga sola la primera vez. Para reiniciarla: `python -m database.seed --todo`.
- Para comprobar que tu MongoDB soporta todo (explain, validador, capped): `python -m database.verificar`.
- Detalles (Atlas, red Wi-Fi, publicación): [`docs/despliegue.md`](docs/despliegue.md).

## 📚 Documentación

- [`docs/modelo_de_datos.md`](docs/modelo_de_datos.md): colecciones, documento de ejemplo, índices, validación y comparación con SQL.
- [`docs/guion_experiencia.md`](docs/guion_experiencia.md): propuesta, guión minuto a minuto y cierre de la experiencia práctica.
- [`docs/despliegue.md`](docs/despliegue.md): instalación, Atlas, red local y tests.

## 👥 Equipo de desarrollo

Trabajo Práctico Integrador N.º 2 — Base de Datos 2.

**Instituto Técnico Salesiano Villada**

Integrantes: *Por completar.*

## 📌 Estado del proyecto

<code>Funcional — juego conectado a MongoDB. Pendiente: arte definitivo de entrenadores y Pokémon (hoy hay placeholders).</code>

---

*POKÉLAB — Pokémon Research Database*
