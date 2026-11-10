"""Traducción del constructor visual a filtros reales de MongoDB."""
import pytest

from app.services.agregacion import pipeline_desde_pedido
from app.services.consultas import (
    ErrorConsulta, a_shell, construir_filtro, generar_sql, parsear_filtro_texto, resumir_explain,
)
from tests.conftest import cond


def test_condiciones_sueltas_usan_notacion_de_punto():
    filtro = construir_filtro([
        cond("movimientos.nombre", "$eq", "Señuelo"),
        cond("estadisticas.velocidad", "$gt", "60"),
    ])
    assert filtro == {"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gt": 60}}


def test_elem_match_agrupa_condiciones_del_mismo_array():
    filtro = construir_filtro([
        cond("tipos", "$eq", "Agua"),
        cond("habilidades.nombre", "$eq", "Nado Rápido"),
        cond("habilidades.oculta", "$eq", "true"),
    ], ["habilidades"])
    assert filtro == {"tipos": "Agua", "habilidades": {"$elemMatch": {"nombre": "Nado Rápido", "oculta": True}}}


def test_rango_sobre_el_mismo_campo_se_combina():
    filtro = construir_filtro([
        cond("estadisticas.velocidad", "$gte", 80),
        cond("estadisticas.velocidad", "$lt", 100),
    ])
    assert filtro == {"estadisticas.velocidad": {"$gte": 80, "$lt": 100}}


def test_mismo_campo_y_operador_repetido_usa_and():
    filtro = construir_filtro([cond("tipos", "$eq", "Agua"), cond("tipos", "$eq", "Volador")])
    assert filtro == {"tipos": "Agua", "$and": [{"tipos": "Volador"}]}


def test_in_acepta_lista_separada_por_comas():
    assert construir_filtro([cond("tipos", "$in", "Agua, Fuego")]) == {"tipos": {"$in": ["Agua", "Fuego"]}}


@pytest.mark.parametrize("condicion", [
    cond("password", "$eq", "x"),
    cond("nombre", "$where", "1"),
    cond("estadisticas.velocidad", "$gt", "rapido"),
    cond("nombre", "$eq", ""),
])
def test_condiciones_invalidas(condicion):
    with pytest.raises(ErrorConsulta):
        construir_filtro([condicion])


def test_texto_acepta_sintaxis_de_mongosh():
    assert parsear_filtro_texto('db.pokemon.find({tipos: "Agua", "estadisticas.ps": {$gte: 100}})') == {
        "tipos": "Agua", "estadisticas.ps": {"$gte": 100}}
    assert parsear_filtro_texto("{ 'nombre': 'Pikachu' }") == {"nombre": "Pikachu"}


@pytest.mark.parametrize("texto", [
    '{"$where": "sleep(1000)"}',
    '{"nombre": {"$function": {}}}',
    '{"$expr": {"$gt": ["$a", 1]}}',
    "[1, 2]",
    "{nombre: ",
])
def test_texto_rechaza_operadores_peligrosos_y_errores(texto):
    with pytest.raises(ErrorConsulta):
        parsear_filtro_texto(texto)


def test_sql_refleja_la_diferencia_con_elem_match():
    condiciones = [cond("habilidades.nombre", "$eq", "Nado Rápido"), cond("habilidades.oculta", "$eq", True)]
    suelto = generar_sql(condiciones, [])["sql"]
    agrupado = generar_sql(condiciones, ["habilidades"])["sql"]
    assert suelto.count("EXISTS") == 2
    assert agrupado.count("EXISTS") == 1
    assert "pokemon_habilidad" in generar_sql(condiciones, [])["tablas"]


def test_sql_de_distinto_en_array_es_not_exists():
    assert "NOT EXISTS" in generar_sql([cond("tipos", "$ne", "Agua")], [])["sql"]


def test_shell_imprime_como_mongosh():
    assert a_shell({"estadisticas.velocidad": {"$gt": 60}}) == '{ "estadisticas.velocidad": { $gt: 60 } }'


def test_pipeline_de_tarjetas_y_texto():
    assert pipeline_desde_pedido({"tarjetas": ["unwind", "limit"]}) == [{"$unwind": "$tipos"}, {"$limit": 3}]
    with pytest.raises(ErrorConsulta):
        pipeline_desde_pedido({"modo": "texto", "texto": '[{"$out": "robada"}]'})
    with pytest.raises(ErrorConsulta):
        pipeline_desde_pedido({"modo": "texto", "texto": '[{"$lookup": {"from": "investigadores"}}]'})
    with pytest.raises(ErrorConsulta):
        pipeline_desde_pedido({"tarjetas": ["inexistente"]})


def test_resumen_de_explain_clasico_y_sbe():
    clasico = {
        "queryPlanner": {"winningPlan": {"stage": "FETCH", "inputStage": {"stage": "IXSCAN", "indexName": "tipos_1"}},
                         "rejectedPlans": [{}]},
        "executionStats": {"totalDocsExamined": 12, "totalKeysExamined": 12, "nReturned": 12, "executionTimeMillis": 0},
    }
    r = resumir_explain(clasico)
    assert r["etapas"] == ["FETCH", "IXSCAN"] and r["indice"] == "tipos_1" and r["planes_descartados"] == 1
    sbe = {"queryPlanner": {"winningPlan": {"queryPlan": {"stage": "COLLSCAN"}, "slotBasedPlan": {}}},
           "executionStats": {"totalDocsExamined": 43, "totalKeysExamined": 0, "nReturned": 2}}
    r = resumir_explain(sbe)
    assert r["etapas"] == ["COLLSCAN"] and r["indice"] is None and r["docs_examinados"] == 43
