# Modelo de datos de POKÉLAB

Base de datos: `pokelab` (configurable con `MONGO_DB_NAME`).

| Colección | Qué guarda | Características de MongoDB que muestra |
|---|---|---|
| `pokemon` | Un documento por Pokémon (43 en total) | Documentos anidados, arrays de valores, arrays de documentos, esquema flexible, validación `$jsonSchema`, índices multiclave |
| `misiones` | Textos de las 5 misiones que lee el juego | Colección simple de referencia |
| `avistamientos` | Fichas de formas alternativas para registrar | Datos de referencia para las escrituras |
| `investigadores` | Cada jugador y su progreso | Documento anidado `intentos`, array `misiones`, índice único, `$inc`, `$push`, `$addToSet` |
| `entregas` | Cada intento de resolver una misión | Fuente de las estadísticas del panel (`aggregate`) |
| `bitacora` | Últimas operaciones ejecutadas | Colección limitada (*capped*): guarda solo las más recientes, en orden de inserción |

## Documento de la colección `pokemon`

```js
{
  _id: ObjectId("..."),
  numero: 248,
  nombre: "Tyranitar",
  generacion: 2,
  tipos: ["Roca", "Siniestro"],                 // array de valores (índice multiclave)
  estadisticas: {                               // documento anidado
    ps: 100, ataque: 134, defensa: 110,
    ataque_especial: 95, defensa_especial: 100, velocidad: 61
  },
  habilidades: [                                // array de documentos
    { nombre: "Chorro Arena", oculta: false },
    { nombre: "Nerviosismo",  oculta: true }
  ],
  movimientos: [                                // array de documentos
    { nombre: "Triturar", tipo: "Siniestro", categoria: "Físico", potencia: 80 },
    { nombre: "Danza Dragón", tipo: "Dragón", categoria: "Estado" }   // sin potencia: no hace falta el campo
  ],
  formas: [                                     // documentos embebidos que agrega el público
    {
      nombre: "Mega Tyranitar",
      tipos: ["Roca", "Siniestro"],
      estadisticas: { ps: 100, ataque: 164, defensa: 150, ataque_especial: 95, defensa_especial: 120, velocidad: 71 },
      habilidad: "Chorro Arena",
      objeto_requerido: "Tyranitarita",         // campo que solo tiene esta forma
      registrada_por: "Lolo",
      fecha_registro: ISODate("2026-11-10T18:30:00Z")
    }
  ]
}
```

Algunos documentos tienen campos que el resto no tiene (`legendario`, `curiosidades`,
`evoluciona_de`, `fosil`, `puede_transformarse`...). Es a propósito: muestra el esquema flexible.

### ¿Por qué embebido y no referenciado?

- Un Pokémon se lee siempre completo: con todo embebido es **una sola lectura** y no hay JOINs.
- Las habilidades, movimientos y formas pertenecen al Pokémon y se consultan junto con él.
- Los arrays están acotados (pocas decenas de elementos), lejos del límite de 16 MB por documento.
- Contra: si se quisiera renombrar un movimiento en todos los Pokémon habría que actualizar muchos
  documentos (`updateMany` con `arrayFilters`). En el juego ese caso no existe.

### Validación de esquema

`database/seed.py` crea la colección con un validador `$jsonSchema` que exige la estructura mínima
(número, nombre, 1 o 2 tipos válidos, las 6 estadísticas enteras entre 1 y 255, etc.) **pero permite
campos extra**. Desde el panel del expositor se puede intentar romperlo (por ejemplo `$set` de
`tipos` con un número) y MongoDB rechaza la escritura con el error 121.

> Si el usuario de Atlas no tiene permiso `collMod`, el validador se crea igual cuando la colección
> todavía no existe (primer arranque). Si ya existía, el juego sigue funcionando sin validador.

### Índices

| Índice | Para qué |
|---|---|
| `numero_1` (único) | Buscar un Pokémon por número; evita duplicados |
| `nombre_1` (único) | Evita nombres repetidos |
| `tipos_1` | Índice **multiclave** (una entrada por cada tipo del array) |
| `estadisticas.velocidad_1` | Índice sobre un campo de un documento anidado |
| `movimientos.nombre_1` | Índice multiclave sobre un array de documentos |
| `habilidades.nombre_1` | Ídem |
| `investigadores.nombre_clave_1` (único) | Un nombre por partida |

La misión del Ingeniero Plata ejecuta la consulta del Entrenador Rojo con cada índice forzado
(`hint`) y muestra `explain("executionStats")`: documentos examinados, claves examinadas y etapas
(`COLLSCAN`, `IXSCAN`, `FETCH`). Después se compara con el plan que elige el motor solo.

## Operaciones que ejecuta el juego

```js
// Misión Rojo · notación de punto en documento anidado y array de documentos
db.pokemon.find({ "movimientos.nombre": "Señuelo", "estadisticas.velocidad": { $gt: 60 } })

// Misión Azul · $elemMatch (las dos condiciones en el MISMO elemento del array)
db.pokemon.find({ tipos: "Agua", habilidades: { $elemMatch: { nombre: "Nado Rápido", oculta: true } } })

// Misión Amarilla · pipeline de agregación
db.pokemon.aggregate([
  { $unwind: "$tipos" },
  { $group: { _id: "$tipos", total: { $sum: 1 } } },
  { $sort: { total: -1, _id: 1 } },
  { $limit: 3 }
])

// Misión Verde · escritura atómica de un documento embebido
db.pokemon.updateOne(
  { numero: 248, "formas.nombre": { $ne: "Mega Tyranitar" } },
  { $push: { formas: { nombre: "Mega Tyranitar", /* ... */ objeto_requerido: "Tyranitarita" } } }
)
// ... y si la forma ya existe, operador posicional
db.pokemon.updateOne(
  { numero: 248, "formas.nombre": "Mega Tyranitar" },
  { $set: { "formas.$.clima": "Tormenta de arena" } }
)

// Misión Plata · plan de ejecución
db.pokemon.find({ "movimientos.nombre": "Señuelo", "estadisticas.velocidad": { $gt: 60 } })
  .hint("movimientos.nombre_1")
  .explain("executionStats")

// Progreso del jugador (colección investigadores)
db.investigadores.updateOne(
  { _id: id, "misiones.clave": { $ne: "rojo" } },
  { $push: { misiones: { clave: "rojo", puntos: 85, completada_en: new Date() } }, $inc: { puntos: 85 } }
)

// Ranking
db.investigadores.aggregate([
  { $project: { nombre: 1, puntos: 1, completadas: { $size: "$misiones" } } },
  { $sort: { puntos: -1, completadas: -1 } },
  { $limit: 10 }
])
```

## El mismo dato en un modelo relacional

Para guardar lo mismo en SQL harían falta 7 tablas: `pokemon` (con las estadísticas como columnas),
`tipo`, `pokemon_tipo`, `habilidad`, `pokemon_habilidad` (con la columna `oculta`), `movimiento`,
`pokemon_movimiento` y `forma`. Los campos propios de cada forma (`objeto_requerido`, `region`,
`electrodomestico`...) exigirían `ALTER TABLE` con columnas casi siempre vacías o una tabla
clave-valor aparte. La terminal del juego muestra, para cada consulta, el SQL equivalente con sus
`EXISTS`/`JOIN`, y para cada documento cuántas filas y tablas ocuparía.
