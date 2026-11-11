"""Definición de las misiones del laboratorio.

La parte narrativa (entrenador, pedido, concepto) se guarda en la colección
`misiones` al sembrar la base y el juego la lee desde MongoDB. Los criterios
de corrección se quedan acá, del lado del servidor, para que nadie pueda
verlos ni modificarlos desde el navegador.
"""


def _dato(doc, ruta):
    valor = doc
    for parte in ruta.split("."):
        if not isinstance(valor, dict):
            return None
        valor = valor.get(parte)
    return valor


def _motivo_habilidad_oculta(doc):
    nombres = [h.get("nombre") for h in doc.get("habilidades", [])]
    if "Nado Rápido" in nombres:
        ocultas = [h["nombre"] for h in doc["habilidades"] if h.get("oculta")]
        oculta = ocultas[0] if ocultas else "ninguna"
        return (f"tiene Nado Rápido como habilidad NORMAL; su habilidad oculta es {oculta}. "
                "Tu filtro cumplió 'nombre' con un elemento del array y 'oculta' con OTRO.")
    return "no tiene la habilidad Nado Rápido"


MISIONES = [
    {
        "clave": "rojo",
        "orden": 1,
        "tipo": "busqueda",
        "entrenador": "Entrenador Rojo",
        "sprite": "👨🏿‍🦰",
        "pedido": ("Necesito TODOS los Pokémon que conozcan el movimiento Señuelo (Follow Me) "
                   "y tengan MÁS de 60 puntos de velocidad."),
        "concepto": "Documentos anidados y arrays de documentos (notación de punto)",
        "pista": ("Los movimientos son un array de documentos: filtrá por 'movimientos.nombre'. "
                  "La velocidad está dentro del documento anidado 'estadisticas'. "
                  "Ojo: 'más de 60' no es lo mismo que '60 o más'."),
        "exito": ("¡Justo lo que necesitaba! Con UNA sola consulta entraste a un array de documentos "
                  "(movimientos.nombre) y a un documento anidado (estadisticas.velocidad). "
                  "En una base relacional eso exige unir pokemon con pokemon_movimiento y movimiento."),
        "criterio": {"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gt": 60}},
        "condiciones": [
            {"filtro": {"movimientos.nombre": "Señuelo"}, "motivo": "no conoce Señuelo"},
            {"filtro": {"estadisticas.velocidad": {"$gt": 60}},
             "motivo": lambda d: f"su velocidad es {_dato(d, 'estadisticas.velocidad')} y no supera 60"},
        ],
    },
    {
        "clave": "azul",
        "orden": 2,
        "tipo": "busqueda",
        "entrenador": "Entrenadora Azul",
        "sprite": "👩🏼‍🦲",
        "pedido": ("Busco TODOS los Pokémon de tipo Agua cuya habilidad OCULTA sea "
                   "Nado Rápido (Swift Swim)."),
        "concepto": "Consultas sobre arrays de documentos con $elemMatch",
        "pista": ("'habilidades' es un array de documentos {nombre, oculta}. Si escribís dos condiciones "
                  "su👷🏻eltas, MongoDB puede cumplir cada una con un elemento DISTINTO del array. "
                  "Activá 'mismo elemento ($elemMatch)' para exigir que se cumplan juntas."),
        "exito": ("¡Perfecto! $elemMatch obliga a que 'nombre' y 'oculta' se cumplan en el MISMO elemento "
                  "del array. Sin él, Kingdra o Magikarp se cuelan porque tienen Nado Rápido como "
                  "habilidad normal y además otra habilidad oculta."),
        "criterio": {"tipos": "Agua", "habilidades": {"$elemMatch": {"nombre": "Nado Rápido", "oculta": True}}},
        "trampa": {"tipos": "Agua", "habilidades.nombre": "Nado Rápido", "habilidades.oculta": True},
        "condiciones": [
            {"filtro": {"tipos": "Agua"}, "motivo": lambda d: f"no es de tipo Agua (es {', '.join(d.get('tipos', []))})"},
            {"filtro": {"habilidades": {"$elemMatch": {"nombre": "Nado Rápido", "oculta": True}}},
             "motivo": _motivo_habilidad_oculta},
        ],
    },
    {
        "clave": "amarilla",
        "orden": 3,
        "tipo": "agregacion",
        "entrenador": "Entrenadora Amarilla",
        "sprite": "🧏‍♂️",
        "pedido": ("Quiero conocer la Pokédex: ¿cuáles son los 3 tipos con MÁS Pokémon y cuántos "
                   "Pokémon hay de cada uno? Armá el pipeline de agregación."),
        "concepto": "Pipeline de agregación ($unwind, $group, $sort, $limit)",
        "pista": ("Un Pokémon puede tener dos tipos guardados en un array. Antes de agrupar por tipo "
                  "hay que 'desarmar' ese array con $unwind. El orden de las etapas importa."),
        "exito": ("¡Excelente! Cada etapa del pipeline transforma los documentos que recibe: $unwind "
                  "desarmó el array, $group contó por tipo, $sort ordenó y $limit recortó. Todo se "
                  "ejecutó dentro del motor de MongoDB."),
        "pipeline": [
            {"$unwind": "$tipos"},
            {"$group": {"_id": "$tipos", "total": {"$sum": 1}}},
            {"$sort": {"total": -1, "_id": 1}},
            {"$limit": 3},
        ],
        "cantidad": 3,
    },
    {
        "clave": "verde",
        "orden": 4,
        "tipo": "registro",
        "entrenador": "Entrenador Verde",
        "sprite": "💁🏼‍♂️",
        "pedido": ("Quiero investigar las formas alternativas de algunos Pokémon. Te pasé un "
                   "avistamiento: registralo como una forma DENTRO del documento del Pokémon."),
        "concepto": "Esquema flexible y documentos embebidos ($push, operador posicional $)",
        "pista": ("Las formas son un array de documentos embebidos en cada Pokémon. Cada forma puede "
                  "tener campos propios: agregá el dato especial con el nombre de campo que vos elijas."),
        "exito": ("¡Registrado! Tu forma quedó EMBEBIDA en el documento del Pokémon, con un campo que el "
                  "resto de los documentos no tiene. MongoDB no te pidió cambiar ningún esquema: en SQL "
                  "hubieras necesitado un ALTER TABLE o una tabla nueva."),
    },
    {
        "clave": "plata",
        "orden": 5,
        "tipo": "indices",
        "entrenador": "Ingeniero Ricky",
        "sprite": "👷🏻",
        "pedido": ("La consulta del Entrenador Rojo se va a ejecutar miles de veces por día. Probá los "
                   "distintos planes de ejecución y elegí el que examina MENOS documentos."),
        "concepto": "Índices y planificador de consultas (explain)",
        "pista": ("Mirá 'documentos examinados' en cada plan. Un índice sobre un campo muy selectivo "
                  "evita leer documentos que después se descartan."),
        "exito": ("¡Bien elegido! Es la misma decisión que toma el planificador de consultas de MongoDB: "
                  "prueba los índices candidatos, se queda con el que trae los resultados haciendo "
                  "menos trabajo y guarda ese plan en caché."),
        "filtro": {"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gt": 60}},
    },
]

MISIONES_POR_CLAVE = {m["clave"]: m for m in MISIONES}

CAMPOS_PUBLICOS = ("clave", "orden", "tipo", "entrenador", "sprite", "pedido", "concepto", "pista", "exito")


def documento_publico(mision):
    """Lo que se guarda en la colección `misiones` (sin criterios de corrección)."""
    return {campo: mision[campo] for campo in CAMPOS_PUBLICOS}


def motivo(condicion, doc):
    texto = condicion["motivo"]
    return texto(doc) if callable(texto) else texto
