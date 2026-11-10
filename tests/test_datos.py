"""Integridad del dataset y de las misiones (lo que el juego da por cierto)."""
from app.misiones import MISIONES_POR_CLAVE
from database.seed import ESTADISTICAS, TIPOS, cargar_json


def nombres(db, filtro):
    return sorted(d["nombre"] for d in db.pokemon.find(filtro))


def test_cada_pokemon_cumple_el_esquema_minimo():
    pokemon = cargar_json("pokemon.json")
    assert len(pokemon) >= 40
    assert len({p["numero"] for p in pokemon}) == len(pokemon)
    assert len({p["nombre"] for p in pokemon}) == len(pokemon)
    for p in pokemon:
        assert isinstance(p["numero"], int) and p["numero"] >= 1
        assert 1 <= len(p["tipos"]) <= 2 and all(t in TIPOS for t in p["tipos"])
        assert set(p["estadisticas"]) == set(ESTADISTICAS)
        assert all(isinstance(v, int) and 1 <= v <= 255 for v in p["estadisticas"].values())
        assert all(isinstance(h["oculta"], bool) for h in p["habilidades"])
        assert sum(h["oculta"] for h in p["habilidades"]) <= 1
        for m in p["movimientos"]:
            assert m["tipo"] in TIPOS and m["categoria"] in ("Físico", "Especial", "Estado")
            assert ("potencia" in m) == (m["categoria"] != "Estado")
        for forma in p.get("formas", []):
            assert {"nombre", "tipos"} <= set(forma)


def test_avistamientos_apuntan_a_pokemon_existentes():
    por_numero = {p["numero"]: p for p in cargar_json("pokemon.json")}
    claves = set()
    for a in cargar_json("avistamientos.json"):
        assert a["clave"] not in claves
        claves.add(a["clave"])
        assert por_numero[a["numero"]]["nombre"] == a["pokemon"]
        assert all(t in TIPOS for t in a["tipos"])
        assert set(a["estadisticas"]) == set(ESTADISTICAS)
        ya = [f["nombre"] for f in por_numero[a["numero"]].get("formas", [])]
        assert a["forma"] not in ya, "el avistamiento no debe venir registrado"


def test_mision_rojo_tiene_una_trampa_en_el_limite(db):
    assert nombres(db, MISIONES_POR_CLAVE["rojo"]["criterio"]) == ["Pachirisu", "Togekiss"]
    # Clefable tiene exactamente 60: queda afuera con $gt y entra con $gte
    assert "Clefable" in nombres(db, {"movimientos.nombre": "Señuelo", "estadisticas.velocidad": {"$gte": 60}})


def test_mision_azul_distingue_elemmatch(db):
    mision = MISIONES_POR_CLAVE["azul"]
    assert nombres(db, mision["criterio"]) == ["Golduck", "Poliwrath", "Psyduck"]
    con_trampa = nombres(db, mision["trampa"])
    assert set(con_trampa) - set(nombres(db, mision["criterio"])) == {"Kabutops", "Kingdra", "Ludicolo", "Magikarp"}


def test_mision_amarilla_resultado_esperado(db):
    resultado = list(db.pokemon.aggregate(MISIONES_POR_CLAVE["amarilla"]["pipeline"]))
    assert [r["_id"] for r in resultado][:2] == ["Agua", "Fuego"]
    assert len(resultado) == 3
