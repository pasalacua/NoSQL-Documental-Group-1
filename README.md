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

## 🧪 Funcionalidades previstas

### 1. Registro de formas alternativas
Permite consultar un Pokémon y registrar nuevas formas, incorporando sus estadísticas y habilidades.

Ejemplo: Mega Tyranitar.

### 2. Buscador competitivo
Permite encontrar Pokémon mediante diferentes criterios:

- Movimientos disponibles.
- Tipos.
- Estadísticas mínimas.
- Habilidades.
- Categorías de movimientos.

### 3. Administración de información
Permite consultar y modificar estadísticas, habilidades y movimientos, aprovechando la flexibilidad de los documentos de MongoDB.

### 4. Flujo inicial estilo Pokémon
La partida comienza con un selector de nombre inspirado en `Intro-Screens-PKM.png`.
El nombre se guarda en el navegador y se utiliza en la introducción del laboratorio.
Los diálogos y la lista de entrenadores utilizan marcos extraídos de `Menu-Frames-PKM.png`.

## 🗂️ Estructura del proyecto

```text
POKELAB/
├── app/
├── database/
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## 🚀 Instalación y ejecución

### Requisitos previos

- Python 3.
- Git.
- Una instancia de MongoDB o una cuenta de MongoDB Atlas.

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd POKELAB
```

### 2. Crear un entorno virtual

```bash
python -m venv venv
```

Activarlo:

**Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Crear un archivo `.env` tomando como referencia `.env.example`.

Completar las credenciales y la configuración de conexión a MongoDB.

### 5. Ejecutar la aplicación

```bash
python run.py
```

## 📚 Documentación

La carpeta `docs/` contiene documentación complementaria sobre el desarrollo, incluyendo el diseño del modelo de datos y las decisiones técnicas del proyecto.

Las herramientas de `tools/` permiten regenerar los recortes de personajes y los marcos de interfaz a partir de las spritesheets originales.

## 👥 Equipo de desarrollo

Trabajo Práctico Integrador N.º 2 — Base de Datos 2.

**Instituto Técnico Salesiano Villada**

Integrantes: *Por completar.*

## 📌 Estado del proyecto

<code>En desarrollo — MVP en planificación e implementación.</code>

---

*POKÉLAB — Pokémon Research Database*
