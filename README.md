# POKÉLAB — Pokémon Research Database

Aplicación web interactiva desarrollada con Python, Flask y MongoDB, que simula un laboratorio de investigación Pokémon. El sistema permite consultar, analizar y modificar información de Pokémon mediante operaciones sobre una base de datos documental.

---

## 1. Descripción general

**POKÉLAB** es un proyecto desarrollado en el marco del Trabajo Práctico Integrador N.º 2 de la asignatura Base de Datos 2 del Instituto Técnico Salesiano Villada.

La aplicación propone una experiencia interactiva en la que el usuario asume el rol de un investigador Pokémon. A través de diferentes solicitudes y misiones, debe consultar registros, analizar características y realizar modificaciones sobre la información almacenada en MongoDB.

El propósito principal no es únicamente construir una aplicación temática, sino utilizar sus funcionalidades para demostrar las características del modelo documental y permitir la interacción directa con una base de datos NoSQL.

El proyecto utiliza el universo Pokémon como contexto para representar situaciones de investigación y administración de datos de una manera práctica y accesible.

## 2. Objetivos

El desarrollo de POKÉLAB persigue los siguientes objetivos:

- Implementar una aplicación funcional que utilice MongoDB como sistema de almacenamiento.
- Demostrar las diferencias entre el modelo documental y el modelo relacional.
- Trabajar con documentos BSON, colecciones, estructuras anidadas y arrays.
- Implementar consultas que combinen múltiples condiciones y accedan a campos anidados.
- Realizar operaciones de inserción y actualización sobre documentos existentes.
- Aprovechar la flexibilidad del esquema documental para representar información de distinta naturaleza.
- Proporcionar una interfaz que permita experimentar con estas operaciones sin necesidad de interactuar directamente con la consola de MongoDB.

## 3. Funcionalidades principales

### 3.1. Registro de formas alternativas

Permite incorporar nuevas formas de un Pokémon existente, como las Mega Evoluciones.

El proceso contempla la búsqueda del Pokémon original, la consulta de sus características y el registro de una nueva forma con sus correspondientes estadísticas y habilidades.

Las formas alternativas se representan mediante estructuras anidadas dentro del documento del Pokémon correspondiente.

**Conceptos de MongoDB involucrados:**

- Arrays de documentos.
- Documentos anidados.
- Actualización de documentos.
- Flexibilidad del esquema.

### 3.2. Buscador de Pokémon

Permite localizar Pokémon mediante diferentes criterios de búsqueda.

Entre los atributos que pueden utilizarse se encuentran:

- Nombre de movimientos.
- Tipos.
- Estadísticas mínimas.
- Habilidades disponibles.
- Categorías de movimientos.

La combinación de condiciones permite realizar búsquedas más específicas sobre la información almacenada.

Ejemplo conceptual de una consulta:

```javascript
db.pokemon.find({
    "movimientos.nombre": "Follow Me",
    "estadisticas.velocidad": { $gt: 60 }
})
```

Esta operación permite recuperar los Pokémon que cumplen simultáneamente las condiciones indicadas.

**Conceptos de MongoDB involucrados:**

- Consultas sobre documentos.
- Operadores de comparación.
- Búsquedas dentro de arrays.
- Acceso a campos anidados.
- Combinación de condiciones.

### 3.3. Administración de habilidades y estadísticas

Permite consultar y modificar características de los Pokémon.

La estructura documental facilita la representación de información variable, por ejemplo, Pokémon con diferentes cantidades de habilidades o movimientos con atributos que dependen de su categoría.

También permite conservar registros históricos de determinadas modificaciones, cuando corresponde.

**Conceptos de MongoDB involucrados:**

- Campos opcionales.
- Arrays de longitud variable.
- Estructuras anidadas.
- Actualización de documentos.
- Historiales mediante arrays de documentos.

### 3.4. Sistema de investigación y misiones

La aplicación presenta solicitudes de diferentes entrenadores que representan operaciones de investigación sobre la base de datos.

El usuario debe resolver estas solicitudes utilizando las herramientas disponibles en el laboratorio. De esta manera, las operaciones sobre MongoDB forman parte de la experiencia de uso y no quedan limitadas a ejemplos aislados.

## 4. Arquitectura del sistema

POKÉLAB utiliza una arquitectura web cliente-servidor, organizada en tres componentes principales:

| Componente | Tecnología | Responsabilidad |
|---|---|---|
| Presentación | HTML, CSS y JavaScript | Interfaz, interacción y representación visual |
| Aplicación | Python y Flask | Lógica de negocio, procesamiento de solicitudes y comunicación con la base de datos |
| Persistencia | MongoDB | Almacenamiento y consulta de documentos |

### 4.1. Frontend

La capa de presentación está construida con HTML, CSS y JavaScript.

Se encarga de representar la interfaz del laboratorio, gestionar las interacciones del usuario y mostrar la información recibida desde el servidor.

El frontend no se conecta directamente a MongoDB. Las operaciones de persistencia se realizan a través del backend.

### 4.2. Backend

El servidor está desarrollado en Python utilizando Flask.

Esta capa centraliza el procesamiento de las solicitudes, aplica la lógica correspondiente a cada funcionalidad y ejecuta las operaciones necesarias sobre MongoDB.

La separación entre presentación y lógica de aplicación permite mantener responsabilidades diferenciadas y facilita el mantenimiento del código.

### 4.3. Base de datos

MongoDB es el sistema de gestión de bases de datos utilizado por el proyecto.

La información se almacena en documentos BSON agrupados en colecciones. Este modelo permite representar entidades con estructuras anidadas, arrays y campos opcionales.

La aplicación utiliza estas características para representar información Pokémon sin requerir que todos los registros compartan exactamente la misma estructura.

## 5. Modelo de datos documental

La colección principal del dominio es `pokemon`.

Cada Pokémon se representa mediante un documento que agrupa sus características y relaciones de información más relevantes.

Un documento puede contener, entre otros elementos:

- Nombre.
- Tipos.
- Estadísticas.
- Habilidades.
- Movimientos.
- Formas alternativas.
- Información adicional específica del registro.

Ejemplo conceptual simplificado:

```javascript
{
    nombre: "Tyranitar",

    tipos: [
        "Roca",
        "Siniestro"
    ],

    estadisticas: {
        hp: 100,
        ataque: 134,
        defensa: 110,
        ataqueEspecial: 95,
        defensaEspecial: 100,
        velocidad: 61
    },

    habilidades: [
        {
            nombre: "Chorro Arena",
            tipo: "Normal"
        },
        {
            nombre: "Nerviosismo",
            tipo: "Oculta"
        }
    ],

    movimientos: [
        {
            nombre: "Stone Edge",
            tipo: "Roca",
            categoria: "Fisico",
            potencia: 100
        },
        {
            nombre: "Stealth Rock",
            tipo: "Roca",
            categoria: "Estado",
            efecto: "Coloca trampas de rocas"
        }
    ],

    formas: [
        {
            nombre: "Mega Tyranitar",
            estadisticas: {
                hp: 100,
                ataque: 164,
                defensa: 150,
                ataqueEspecial: 95,
                defensaEspecial: 120,
                velocidad: 71
            },
            habilidad: "Chorro Arena"
        }
    ]
}
```

El ejemplo es ilustrativo y representa el enfoque del modelo documental. La estructura efectiva puede incorporar otros campos según las necesidades de la aplicación.

### 5.1. Flexibilidad del esquema

Una de las características centrales del diseño es que los documentos no necesitan contener exactamente los mismos campos.

Por ejemplo:

- Un movimiento de daño puede incluir potencia y precisión.
- Un movimiento de estado puede no necesitar potencia.
- Un Pokémon puede disponer de distintas cantidades de habilidades.
- Una forma alternativa puede incorporar estadísticas y habilidades propias.
- Determinados registros pueden incluir información histórica adicional.

Esta flexibilidad permite representar datos heterogéneos de forma natural dentro del modelo documental.

## 6. Tecnologías utilizadas

| Tecnología | Uso dentro del proyecto |
|---|---|
| Python | Lenguaje principal del backend |
| Flask | Framework web del servidor |
| MongoDB | Sistema de gestión de base de datos NoSQL documental |
| PyMongo | Comunicación entre Python y MongoDB |
| HTML5 | Estructura de las páginas |
| CSS3 | Estilos y presentación visual |
| JavaScript | Interactividad y comportamiento del frontend |
| MongoDB Atlas | Alternativa de alojamiento de la base de datos en la nube |

Las tecnologías se organizan de manera que Flask actúe como intermediario entre la interfaz web y la base de datos.

## 7. Requisitos previos

Antes de instalar el proyecto, es necesario contar con las siguientes herramientas:

### 7.1. Python

Se requiere una instalación de Python 3.10 o superior.

Comprobar la versión instalada:

```bash
python3 --version
```

En caso de no tener Python instalado, puede obtenerse desde:

https://www.python.org/downloads/

En distribuciones basadas en Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 7.2. MongoDB

El proyecto necesita una instancia de MongoDB accesible desde el backend.

Se puede utilizar cualquiera de las siguientes alternativas:

**MongoDB Atlas**

Servicio administrado de MongoDB en la nube. Permite crear un clúster y conectarse mediante una URI.

https://www.mongodb.com/products/platform/atlas-database

**MongoDB Community Server**

Alternativa para ejecutar MongoDB localmente.

https://www.mongodb.com/try/download/community

En ambos casos se debe disponer de una URI de conexión válida y configurar los permisos de acceso correspondientes.

### 7.3. Git

Se recomienda contar con Git para clonar el repositorio y mantener actualizada la copia local.

https://git-scm.com/downloads

Comprobar la instalación:

```bash
git --version
```

## 8. Instalación y configuración

Los siguientes pasos describen el procedimiento para preparar un entorno de desarrollo local.

### 8.1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
```

Ingresar al directorio del proyecto:

```bash
cd <DIRECTORIO_DEL_PROYECTO>
```

### 8.2. Crear un entorno virtual

Se recomienda utilizar un entorno virtual para aislar las dependencias del proyecto de las instalaciones globales de Python.

En Linux y macOS:

```bash
python3 -m venv .venv
```

Activar el entorno:

```bash
source .venv/bin/activate
```

En Windows:

```powershell
py -m venv .venv
```

Activar el entorno:

```powershell
.venv\Scripts\activate
```

Una vez activado, la terminal debería mostrar el nombre del entorno virtual.

### 8.3. Instalar las dependencias

Actualizar el instalador de paquetes:

```bash
python -m pip install --upgrade pip
```

Si el repositorio incluye un archivo `requirements.txt`, instalar las dependencias declaradas en él:

```bash
pip install -r requirements.txt
```

Las dependencias principales del stack son:

- Flask: servidor y framework web.
- PyMongo: controlador de Python para MongoDB.
- python-dotenv: lectura de variables de entorno desde archivos `.env`, si está integrado en la configuración del proyecto.

Si todavía no existe un archivo de dependencias, estas bibliotecas pueden instalarse individualmente:

```bash
pip install Flask pymongo python-dotenv
```

Para mantener instalaciones reproducibles, se recomienda conservar las dependencias efectivamente utilizadas en `requirements.txt`.

### 8.4. Configurar las variables de entorno

La aplicación necesita conocer los parámetros de conexión a MongoDB.

Se recomienda utilizar un archivo `.env` en el directorio raíz del proyecto, siempre que la configuración del backend esté preparada para leerlo.

Ejemplo ilustrativo:

```env
MONGO_URI=mongodb+srv://<USUARIO>:<CONTRASEÑA>@<CLUSTER>/
MONGO_DB_NAME=pokelab
```

Los nombres de las variables deben coincidir con los que utilice el módulo de conexión de la aplicación. Si el proyecto emplea nombres diferentes, deben conservarse los definidos en su código.

En caso de utilizar MongoDB local, la URI puede tener el siguiente formato:

```env
MONGO_URI=mongodb://localhost:27017/
```

**Importante:**

- No publicar credenciales de MongoDB.
- No subir archivos `.env` al repositorio.
- Verificar que la dirección IP del equipo esté autorizada en MongoDB Atlas.
- Comprobar que el usuario de base de datos tenga los permisos necesarios.
- Utilizar variables de entorno para evitar incorporar información sensible directamente en el código fuente.

### 8.5. Inicializar la base de datos

El proyecto dispone de un proceso de carga inicial de datos mediante el módulo de seed.

Desde la raíz del repositorio, ejecutar:

```bash
python -m database.seed
```

Este procedimiento prepara las colecciones y carga los registros iniciales definidos por el proyecto.

**Advertencia:** el proceso de inicialización puede eliminar y volver a insertar información en determinadas colecciones. No debe ejecutarse indiscriminadamente sobre una base de datos que contenga información que se quiera conservar.

Antes de ejecutarlo, verificar el comportamiento del script y asegurarse de estar conectado a la base de datos correcta.

## 9. Ejecución de la aplicación

Con el entorno virtual activo, las dependencias instaladas y MongoDB correctamente configurado, se puede iniciar el servidor Flask.

Si la aplicación utiliza el paquete `app` como punto de entrada de Flask:

```bash
flask --app app run --debug
```

El servidor de desarrollo estará disponible normalmente en:

```text
http://127.0.0.1:5000/
```

Para detener la ejecución, utilizar `Ctrl + C` en la terminal.

El modo `--debug` está destinado al desarrollo local. No debe utilizarse como configuración de producción.

## 10. Estructura general del proyecto

La organización del repositorio separa los componentes de presentación, lógica de aplicación y persistencia.

La estructura de referencia es la siguiente:

```text
POKELAB/
│
├── app/
│   ├── routes/
│   ├── services/
│   ├── static/
│   │   ├── assets/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   ├── __init__.py
│   └── db.py
│
├── database/
│   └── seed.py
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

Esta representación es orientativa y debe mantenerse alineada con la estructura efectiva del repositorio.

| Directorio o archivo | Responsabilidad |
|---|---|
| `app/` | Código principal de la aplicación Flask |
| `app/routes/` | Rutas y puntos de acceso de la aplicación |
| `app/services/` | Lógica de negocio y operaciones de dominio |
| `app/static/` | Recursos estáticos del frontend |
| `app/templates/` | Plantillas HTML |
| `app/db.py` | Configuración y acceso a MongoDB |
| `database/` | Inicialización y carga de datos |
| `tests/` | Pruebas automatizadas |
| `.env` | Configuración local y credenciales |
| `requirements.txt` | Dependencias de Python |

## 11. Pruebas y verificación

Se recomienda ejecutar las pruebas disponibles antes de considerar una instalación como funcional.

Si el proyecto utiliza `pytest`:

```bash
pip install pytest
pytest
```

Las pruebas deben ejecutarse con la base de datos y las variables de entorno correctamente configuradas cuando requieran acceso a MongoDB.

También se recomienda comprobar manualmente:

- La conexión entre Flask y MongoDB.
- La carga de las colecciones iniciales.
- La visualización de los registros Pokémon.
- La ejecución de búsquedas con múltiples condiciones.
- La inserción de formas alternativas.
- La actualización de estadísticas y habilidades.
- La persistencia de los cambios después de recargar la aplicación.

## 12. Solución de problemas frecuentes

### Error de conexión con MongoDB

Verificar:

1. Que la instancia de MongoDB esté activa.
2. Que la URI esté correctamente configurada.
3. Que las credenciales sean válidas.
4. Que la dirección IP esté autorizada en Atlas.
5. Que el usuario tenga permisos sobre la base de datos.

### Error al importar módulos de Python

Comprobar que el entorno virtual esté activo y que las dependencias se hayan instalado correctamente.

```bash
pip install -r requirements.txt
```

### Flask no encuentra la aplicación

Verificar que se esté ejecutando el comando desde el directorio raíz del repositorio y que el paquete `app` contenga su archivo de inicialización.

### No aparecen los registros iniciales

Comprobar que la base de datos esté correctamente seleccionada y que el proceso de carga inicial haya finalizado sin errores.

### Los cambios no persisten

Verificar que las operaciones de escritura se estén ejecutando sobre la instancia y colección esperadas, y que el usuario de MongoDB disponga de permisos de escritura.

## 13. Alcance del proyecto

POKÉLAB se desarrolla como una experiencia práctica orientada al aprendizaje y demostración de MongoDB.

Su alcance se centra en las operaciones documentales que permiten comprender las características del sistema de base de datos utilizado.

No pretende reemplazar una Pokédex comercial ni implementar un simulador completo de combates Pokémon.

La prioridad del desarrollo es demostrar de manera funcional:

1. La representación de información mediante documentos.
2. La utilización de estructuras anidadas y arrays.
3. La flexibilidad del esquema.
4. La ejecución de consultas con múltiples condiciones.
5. La inserción y actualización de registros.
6. La interacción entre una aplicación web y una base de datos documental.

