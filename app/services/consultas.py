"""Construcción, validación y ejecución de consultas sobre la colección pokemon.

El constructor visual del juego manda condiciones del estilo
{"campo": "estadisticas.velocidad", "operador": "$gt", "valor": 60}; este
módulo las traduce a un filtro real de MongoDB, lo ejecuta, resume el plan
de ejecución (explain) y genera el SQL equivalente para comparar.
"""
import json
import re

from app.services.serializar import a_json


class ErrorConsulta(ValueError):
    """Error que se muestra tal cual al jugador."""


TIPOS = [
    "Normal", "Fuego", "Agua", "Planta", "Eléctrico", "Hielo", "Lucha", "Veneno", "Tierra",
    "Volador", "Psíquico", "Bicho", "Roca", "Fantasma", "Dragón", "Siniestro", "Acero", "Hada",
]
CATEGORIAS = ["Físico", "Especial", "Estado"]
ESTADISTICAS = ["ps", "ataque", "defensa", "ataque_especial", "defensa_especial", "velocidad"]

# grupo = array de documentos al que pertenece el campo (para $elemMatch)
CAMPOS = [
    {"campo": "nombre", "etiqueta": "nombre", "tipo": "texto"},
    {"campo": "numero", "etiqueta": "numero (Pokédex)", "tipo": "entero"},
    {"campo": "generacion", "etiqueta": "generacion", "tipo": "entero"},
    {"campo": "tipos", "etiqueta": "tipos  [array]", "tipo": "texto", "array": True, "opciones": TIPOS},
] + [
    {"campo": f"estadisticas.{e}", "etiqueta": f"estadisticas.{e}", "tipo": "entero"} for e in ESTADISTICAS
] + [
    {"campo": "habilidades.nombre", "etiqueta": "habilidades.nombre", "tipo": "texto", "grupo": "habilidades"},
    {"campo": "habilidades.oculta", "etiqueta": "habilidades.oculta", "tipo": "booleano", "grupo": "habilidades"},
    {"campo": "movimientos.nombre", "etiqueta": "movimientos.nombre", "tipo": "texto", "grupo": "movimientos"},
    {"campo": "movimientos.tipo", "etiqueta": "movimientos.tipo", "tipo": "texto", "grupo": "movimientos",
     "opciones": TIPOS},
    {"campo": "movimientos.categoria", "etiqueta": "movimientos.categoria", "tipo": "texto",
     "grupo": "movimientos", "opciones": CATEGORIAS},
    {"campo": "movimientos.potencia", "etiqueta": "movimientos.potencia", "tipo": "entero", "grupo": "movimientos"},
    {"campo": "formas.nombre", "etiqueta": "formas.nombre", "tipo": "texto", "grupo": "formas"},
]
CAMPOS_POR_NOMBRE = {c["campo"]: c for c in CAMPOS}
GRUPOS = ["habilidades", "movimientos", "formas"]

OPERADORES = [
    {"op": "$eq", "etiqueta": "es igual a"},
    {"op": "$ne", "etiqueta": "es distinto de"},
    {"op": "$gt", "etiqueta": "mayor que  (>)"},
    {"op": "$gte", "etiqueta": "mayor o igual  (>=)"},
    {"op": "$lt", "etiqueta": "menor que  (<)"},
    {"op": "$lte", "etiqueta": "menor o igual  (<=)"},
    {"op": "$in", "etiqueta": "es alguno de (lista)"},
    {"op": "$nin", "etiqueta": "no es ninguno de (lista)"},
    {"op": "$exists", "etiqueta": "existe el campo"},
]
OPERADORES_VALIDOS = {o["op"] for o in OPERADORES}

# Operadores habilitados en el modo "escribir la consulta".
OPERADORES_FILTRO = {
    "$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", "$nin", "$and", "$or", "$nor", "$not",
    "$exists", "$elemMatch", "$all", "$size", "$regex", "$options", "$type",
}

MAX_CONDICIONES = 8
MAX_RESULTADOS = 60


# --------------------------------------------------------------------------
# Constructor visual -> filtro de MongoDB
# --------------------------------------------------------------------------

def _convertir(valor, tipo, campo):
    if tipo == "entero":
        if isinstance(valor, bool):
            raise ErrorConsulta(f"'{campo}' espera un número")
        try:
            return int(str(valor).strip())
        except (TypeError, ValueError):
            raise ErrorConsulta(f"'{campo}' espera un número entero (recibí '{valor}')") from None
    if tipo == "booleano":
        if isinstance(valor, bool):
            return valor
        texto = str(valor).strip().lower()
        if texto in ("true", "verdadero", "si", "sí", "1"):
            return True
        if texto in ("false", "falso", "no", "0"):
            return False
        raise ErrorConsulta(f"'{campo}' espera true o false")
    texto = str(valor if valor is not None else "").strip()
    if not texto:
        raise ErrorConsulta(f"Completá el valor de '{campo}'")
    if len(texto) > 60:
        raise ErrorConsulta(f"El valor de '{campo}' es demasiado largo")
    return texto


def _expresion(condicion):
    campo = condicion.get("campo")
    meta = CAMPOS_POR_NOMBRE.get(campo)
    if not meta:
        raise ErrorConsulta(f"El campo '{campo}' no existe en los documentos de pokemon")
    operador = condicion.get("operador", "$eq")
    if operador not in OPERADORES_VALIDOS:
        raise ErrorConsulta(f"Operador no válido: {operador}")
    valor = condicion.get("valor")
    if operador == "$exists":
        return campo, meta, {"$exists": _convertir(valor if valor not in (None, "") else True, "booleano", campo)}
    if operador in ("$in", "$nin"):
        if isinstance(valor, str):
            valor = [v for v in (x.strip() for x in valor.split(",")) if v]
        if not isinstance(valor, list) or not valor:
            raise ErrorConsulta(f"'{campo}' espera una lista de valores separados por coma")
        return campo, meta, {operador: [_convertir(v, meta["tipo"], campo) for v in valor[:20]]}
    convertido = _convertir(valor, meta["tipo"], campo)
    return campo, meta, (convertido if operador == "$eq" else {operador: convertido})


def _es_operadores(expr):
    return isinstance(expr, dict) and expr and all(k.startswith("$") for k in expr)


def _combinar(pares):
    """Une pares (campo, expresión) en un filtro con AND implícito, como se escribe a mano."""
    filtro, extras = {}, []
    for campo, expr in pares:
        if campo not in filtro:
            filtro[campo] = expr
            continue
        previo = filtro[campo]
        if (_es_operadores(previo) and _es_operadores(expr) and "$elemMatch" not in previo
                and "$elemMatch" not in expr and not set(previo) & set(expr)):
            filtro[campo] = {**previo, **expr}
        else:
            extras.append({campo: expr})
    if extras:
        filtro["$and"] = extras
    return filtro


def construir_filtro(condiciones, elem_match=None):
    if not isinstance(condiciones, list):
        raise ErrorConsulta("Formato de condiciones inválido")
    if len(condiciones) > MAX_CONDICIONES:
        raise ErrorConsulta(f"Máximo {MAX_CONDICIONES} condiciones")
    agrupar = {g for g in (elem_match or []) if g in GRUPOS}
    sueltas, grupos = [], {}
    for condicion in condiciones:
        campo, meta, expr = _expresion(condicion)
        grupo = meta.get("grupo")
        if grupo and grupo in agrupar:
            grupos.setdefault(grupo, []).append((campo[len(grupo) + 1:], expr))
        else:
            sueltas.append((campo, expr))
    for grupo, subcondiciones in grupos.items():
        sueltas.append((grupo, {"$elemMatch": _combinar(subcondiciones)}))
    return _combinar(sueltas)


# --------------------------------------------------------------------------
# Modo texto: el jugador escribe el filtro
# --------------------------------------------------------------------------

_CLAVE_SIN_COMILLAS = re.compile(r'([{,]\s*)([A-Za-z_$][\w.$]*)\s*:')
_FIND = re.compile(r"^\s*db\.\w+\.find\(\s*(.*?)\s*\)\s*;?\s*$", re.S)


def parsear_filtro_texto(texto):
    if not isinstance(texto, str) or not texto.strip():
        return {}
    if len(texto) > 2000:
        raise ErrorConsulta("La consulta es demasiado larga")
    texto = texto.strip()
    coincidencia = _FIND.match(texto)
    if coincidencia:
        texto = coincidencia.group(1) or "{}"
    try:
        filtro = json.loads(texto)
    except json.JSONDecodeError:
        flexible = _CLAVE_SIN_COMILLAS.sub(r'\1"\2":', texto.replace("'", '"'))
        try:
            filtro = json.loads(flexible)
        except json.JSONDecodeError as error:
            raise ErrorConsulta(f"No pude leer la consulta: revisá llaves, comillas y comas ({error.msg})") from None
    if not isinstance(filtro, dict):
        raise ErrorConsulta("El filtro tiene que ser un documento: { ... }")
    sanear(filtro, OPERADORES_FILTRO)
    return filtro


def sanear(valor, permitidos, profundidad=0):
    """Recorre el filtro/pipeline y rechaza operadores peligrosos ($where, $function, ...)."""
    if profundidad > 10:
        raise ErrorConsulta("La consulta está demasiado anidada")
    if isinstance(valor, dict):
        if len(valor) > 30:
            raise ErrorConsulta("Demasiados campos en un mismo documento")
        for clave, interno in valor.items():
            if not isinstance(clave, str) or "\x00" in clave:
                raise ErrorConsulta("Nombre de campo inválido")
            if clave.startswith("$") and clave not in permitidos:
                raise ErrorConsulta(f"El operador {clave} no está habilitado en el laboratorio")
            if clave == "$regex" and (not isinstance(interno, str) or len(interno) > 40):
                raise ErrorConsulta("La expresión regular es demasiado larga")
            sanear(interno, permitidos, profundidad + 1)
    elif isinstance(valor, list):
        if len(valor) > 50:
            raise ErrorConsulta("La lista es demasiado larga")
        for interno in valor:
            sanear(interno, permitidos, profundidad + 1)
    elif isinstance(valor, str):
        if len(valor) > 100:
            raise ErrorConsulta("Un texto de la consulta es demasiado largo")
    elif valor is not None and not isinstance(valor, (bool, int, float)):
        raise ErrorConsulta("Valor no soportado en la consulta")


def filtro_desde_pedido(datos):
    """Acepta {modo: 'visual', condiciones, elem_match} o {modo: 'texto', texto}."""
    datos = datos or {}
    if datos.get("modo") == "texto":
        return parsear_filtro_texto(datos.get("texto", "")), None
    condiciones = datos.get("condiciones") or []
    elem_match = datos.get("elem_match") or []
    return construir_filtro(condiciones, elem_match), (condiciones, elem_match)


# --------------------------------------------------------------------------
# Representaciones: shell de MongoDB y SQL equivalente
# --------------------------------------------------------------------------

_IDENTIFICADOR = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def a_shell(valor, sangria=0):
    """Imprime un valor con la sintaxis de mongosh."""
    esp = "  " * sangria
    if isinstance(valor, dict):
        if not valor:
            return "{}"
        partes = []
        for clave, interno in valor.items():
            nombre = clave if _IDENTIFICADOR.match(clave) else json.dumps(clave, ensure_ascii=False)
            partes.append(f"{nombre}: {a_shell(interno, sangria + 1)}")
        en_linea = "{ " + ", ".join(partes) + " }"
        if "\n" not in en_linea and len(en_linea) <= 60:
            return en_linea
        return "{\n" + ",\n".join(f"{esp}  {p}" for p in partes) + f"\n{esp}}}"
    if isinstance(valor, list):
        return "[" + ", ".join(a_shell(v, sangria + 1) for v in valor) + "]"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if valor is None:
        return "null"
    return json.dumps(valor, ensure_ascii=False)


def comando_find(filtro):
    return f"db.pokemon.find({a_shell(filtro)})"


_COLUMNAS = {"nombre": "p.nombre", "numero": "p.numero", "generacion": "p.generacion"}
_COLUMNAS.update({f"estadisticas.{e}": f"p.{e}" for e in ESTADISTICAS})

_TABLAS_ARRAY = {
    "tipos": ("pokemon_tipo pt\n    JOIN tipo t ON t.id = pt.tipo_id", "pt.pokemon_id = p.id", {"": "t.nombre"}),
    "habilidades": ("pokemon_habilidad ph\n    JOIN habilidad h ON h.id = ph.habilidad_id", "ph.pokemon_id = p.id",
                    {"nombre": "h.nombre", "oculta": "ph.oculta"}),
    "movimientos": ("pokemon_movimiento pm\n    JOIN movimiento m ON m.id = pm.movimiento_id", "pm.pokemon_id = p.id",
                    {"nombre": "m.nombre", "tipo": "m.tipo", "categoria": "m.categoria", "potencia": "m.potencia"}),
    "formas": ("forma f", "f.pokemon_id = p.id", {"nombre": "f.nombre"}),
}
_SQL_OP = {"$eq": "=", "$ne": "<>", "$gt": ">", "$gte": ">=", "$lt": "<", "$lte": "<="}


def _literal(valor):
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, (int, float)):
        return str(valor)
    return "'" + str(valor).replace("'", "''") + "'"


def _sql_condicion(columna, expr):
    operador, valor = next(iter(expr.items())) if isinstance(expr, dict) else ("$eq", expr)
    if operador in _SQL_OP:
        return f"{columna} {_SQL_OP[operador]} {_literal(valor)}"
    if operador in ("$in", "$nin"):
        lista = ", ".join(_literal(v) for v in valor)
        return f"{columna} {'NOT IN' if operador == '$nin' else 'IN'} ({lista})"
    return None


def generar_sql(condiciones, elem_match):
    """SQL equivalente para un modelo relacional normalizado de la misma Pokédex."""
    agrupar = {g for g in (elem_match or []) if g in GRUPOS}
    where, tablas = [], {"pokemon"}
    grupos = {}
    for condicion in condiciones:
        campo, meta, expr = _expresion(condicion)
        operador = next(iter(expr)) if isinstance(expr, dict) else "$eq"
        if campo in _COLUMNAS:
            if operador == "$exists":
                where.append(f"{_COLUMNAS[campo]} IS {'NOT ' if expr['$exists'] else ''}NULL")
            else:
                where.append(_sql_condicion(_COLUMNAS[campo], expr))
            continue
        grupo = meta.get("grupo") or campo
        subcampo = campo[len(grupo) + 1:] if campo != grupo else ""
        if grupo in agrupar:
            grupos.setdefault(grupo, []).append((subcampo, operador, expr))
        else:
            where.append(_sql_exists(grupo, [(subcampo, operador, expr)], tablas))
    for grupo, subcondiciones in grupos.items():
        where.append(_sql_exists(grupo, subcondiciones, tablas))
    sql = "SELECT p.*\nFROM pokemon p"
    if where:
        sql += "\nWHERE " + "\n  AND ".join(w for w in where if w)
    sql += ";"
    return {"sql": sql, "tablas": sorted(tablas)}


def _sql_exists(grupo, subcondiciones, tablas):
    desde, union, columnas = _TABLAS_ARRAY[grupo]
    for parte in desde.replace("JOIN", ",").split(","):
        tablas.add(parte.strip().split()[0])
    negar = False
    filtros = [union]
    for subcampo, operador, expr in subcondiciones:
        columna = columnas.get(subcampo, f"{grupo}.{subcampo}")
        if operador == "$exists":
            negar = not expr["$exists"]
            continue
        if operador in ("$ne", "$nin") and len(subcondiciones) == 1:
            # En MongoDB, {tipos: {$ne: 'Agua'}} significa "ningún elemento es Agua".
            negar = True
            expr = {"$eq": expr["$ne"]} if operador == "$ne" else {"$in": expr["$nin"]}
        filtros.append(_sql_condicion(columna, expr))
    cuerpo = f"SELECT 1 FROM {desde}\n    WHERE " + "\n      AND ".join(f for f in filtros if f)
    return f"{'NOT ' if negar else ''}EXISTS (\n    {cuerpo}\n  )"


# --------------------------------------------------------------------------
# Ejecución y plan de ejecución
# --------------------------------------------------------------------------

def _recorrer_plan(nodo, etapas, indices):
    if isinstance(nodo, dict):
        if "stage" in nodo:
            etapas.append(nodo["stage"])
        if nodo.get("indexName"):
            indices.append(nodo["indexName"])
        for clave in ("queryPlan", "inputStage", "inputStages", "shards", "winningPlan"):
            if clave in nodo:
                _recorrer_plan(nodo[clave], etapas, indices)
    elif isinstance(nodo, list):
        for interno in nodo:
            _recorrer_plan(interno, etapas, indices)


def resumir_explain(explicacion):
    planificador = explicacion.get("queryPlanner", {})
    etapas, indices = [], []
    _recorrer_plan(planificador.get("winningPlan", {}), etapas, indices)
    estadisticas = explicacion.get("executionStats", {})
    return {
        "disponible": True,
        "etapas": etapas,
        "indice": indices[0] if indices else None,
        "indices": list(dict.fromkeys(indices)),
        "docs_examinados": estadisticas.get("totalDocsExamined"),
        "claves_examinadas": estadisticas.get("totalKeysExamined"),
        "devueltos": estadisticas.get("nReturned"),
        "tiempo_ms": estadisticas.get("executionTimeMillis"),
        "planes_descartados": len(planificador.get("rejectedPlans", []) or []),
    }


def explicar(db, filtro, hint=None):
    """Ejecuta explain('executionStats'). Si el servidor no lo soporta, lo informa."""
    comando = {"find": "pokemon", "filter": filtro}
    if hint is not None:
        comando["hint"] = hint
    try:
        return resumir_explain(db.command("explain", comando, verbosity="executionStats"))
    except Exception as error:  # mongomock o permisos insuficientes
        return {"disponible": False, "motivo": str(error)[:120]}


def ejecutar_busqueda(db, filtro):
    try:
        documentos = list(db.pokemon.find(filtro).sort("numero", 1).limit(MAX_RESULTADOS))
        total = db.pokemon.count_documents(filtro)
    except ErrorConsulta:
        raise
    except Exception as error:
        raise ErrorConsulta(f"MongoDB rechazó la consulta: {str(error)[:160]}") from None
    return {
        "total": total,
        "documentos": [a_json(d) for d in documentos],
        "plan": explicar(db, filtro),
    }


def catalogo(db):
    """Campos, operadores y valores existentes (con distinct) para el constructor."""
    def distintos(campo):
        try:
            return sorted(v for v in db.pokemon.distinct(campo) if isinstance(v, str))
        except Exception:
            return []

    return {
        "campos": CAMPOS,
        "operadores": OPERADORES,
        "grupos": GRUPOS,
        "valores": {
            "nombre": distintos("nombre"),
            "habilidades.nombre": distintos("habilidades.nombre"),
            "movimientos.nombre": distintos("movimientos.nombre"),
            "formas.nombre": distintos("formas.nombre"),
        },
        "pokemon": list(db.pokemon.find({}, {"_id": 0, "numero": 1, "nombre": 1}).sort("numero", 1)),
        "tipos": TIPOS,
        "categorias": CATEGORIAS,
        "estadisticas": ESTADISTICAS,
    }
