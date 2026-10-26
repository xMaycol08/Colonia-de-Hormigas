"""Pruebas para scripts/build_graph.py (grafo provisional de Fase 1-bis: complejo G/H
con 2 secciones de gradas compartidas y 2 salidas)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "scripts"))

import build_graph as bg  # noqa: E402
import validate_graph as vg  # noqa: E402


@pytest.fixture(scope="module")
def grafo():
    """Construye el grafo una sola vez para todas las pruebas de este modulo."""
    grafo, _advertencias = bg.construir_grafo()
    return grafo


@pytest.fixture(scope="module")
def config():
    """Carga la configuracion del modelo una sola vez."""
    return bg.cargar_configuracion()


def test_grafo_valido_contra_el_schema(grafo):
    schema = vg.cargar_json(vg.SCHEMA_PATH)
    errores = vg.validar_contra_schema(grafo, schema)
    assert errores == []


def test_cantidad_de_nodos_segun_config(grafo, config):
    niveles = config["niveles"]  # ["PB","1","2","3","4"]
    aulas_por_piso = int(config["aulas_por_piso"])

    aulas = [n for n in grafo["nodos"] if n["tipo"] == "aula" and n["id"] not in ("H-PB-OFICINAS_CC", "G-PB-LAB_BIOTEC")]
    # 40 aulas: (niveles - PB) * aulas_por_piso * 2 bloques
    assert len(aulas) == (len(niveles) - 1) * aulas_por_piso * 2 == 40

    origenes_pb = [n for n in grafo["nodos"] if n["id"] in ("H-PB-OFICINAS_CC", "G-PB-LAB_BIOTEC")]
    assert len(origenes_pb) == 2

    pasillos = [n for n in grafo["nodos"] if n["tipo"] == "pasillo"]
    # 3 pasillos (H, G, central) por nivel
    assert len(pasillos) == len(niveles) * 3

    gradas = [n for n in grafo["nodos"] if n["tipo"] == "gradas"]
    # 2 secciones (norte, sur) por nivel
    assert len(gradas) == len(niveles) * 2

    salidas = [n for n in grafo["nodos"] if n["tipo"] == "salida"]
    assert len(salidas) == 2


def test_40_aulas_con_nombres_correctos(grafo, config):
    niveles_con_aulas = [n for n in config["niveles"] if n != "PB"]
    aulas_por_piso = int(config["aulas_por_piso"])

    nombres_esperados = set()
    for bloque in ("H", "G"):
        for nivel in niveles_con_aulas:
            for n in range(1, aulas_por_piso + 1):
                nombres_esperados.add(f"{bloque}{nivel}0{n}")

    nombres_reales = {n["id"] for n in grafo["nodos"] if n["tipo"] == "aula" and n["id"] not in ("H-PB-OFICINAS_CC", "G-PB-LAB_BIOTEC")}

    assert nombres_reales == nombres_esperados
    assert "H101" in nombres_reales and "H405" in nombres_reales
    assert "G101" in nombres_reales and "G405" in nombres_reales


def test_exactamente_dos_secciones_de_gradas_y_dos_salidas(grafo):
    secciones = {n["id"].split("-")[1] for n in grafo["nodos"] if n["tipo"] == "gradas"}
    assert secciones == {"NORTE", "SUR"}

    salidas = {n["id"] for n in grafo["nodos"] if n["tipo"] == "salida"}
    assert salidas == {"SALIDA-A", "SALIDA-B"}


def test_pb_tiene_dos_origenes(grafo):
    origenes_pb = [n for n in grafo["nodos"] if n["piso"] == 0 and n["tipo"] == "aula"]
    ids = {n["id"] for n in origenes_pb}
    assert ids == {"H-PB-OFICINAS_CC", "G-PB-LAB_BIOTEC"}


def test_ningun_nodo_sin_confidence(grafo):
    enum_confidence = vg.cargar_json(vg.SCHEMA_PATH)["definitions"]["confidence"]["enum"]
    for n in grafo["nodos"]:
        assert n.get("confidence"), f"Nodo sin confidence: {n['id']}"
        assert n["confidence"] in enum_confidence


def test_ninguna_arista_sin_confidence(grafo):
    for a in grafo["aristas"]:
        assert a.get("confidence"), f"Arista sin confidence: {a['id']}"


def test_cada_aula_tiene_camino_a_un_punto_de_encuentro(grafo):
    resultado = vg.ResultadoValidacion()
    vg.verificar_caminos_a_punto_encuentro(grafo["nodos"], grafo["aristas"], resultado)
    assert not resultado.tiene_errores_graves, resultado.errores


def test_ambos_bloques_tienen_salida(grafo):
    resultado = vg.ResultadoValidacion()
    vg.verificar_salidas_por_bloque(grafo["nodos"], resultado)
    assert not resultado.tiene_errores_graves, resultado.errores


def test_cada_aula_alcanza_ambas_salidas(grafo):
    """Cada una de las 40 aulas + 2 origenes de PB debe poder llegar a Salida A Y a Salida B."""
    adyacencia = vg.construir_grafo_no_dirigido(grafo["aristas"])
    destinos = {"SALIDA-A", "SALIDA-B"}

    origenes = [n["id"] for n in grafo["nodos"] if n["tipo"] == "aula"]
    assert len(origenes) == 42

    for origen in origenes:
        assert vg.existe_camino(origen, {"SALIDA-A"}, adyacencia), f"{origen} no alcanza Salida A"
        assert vg.existe_camino(origen, {"SALIDA-B"}, adyacencia), f"{origen} no alcanza Salida B"
        assert vg.existe_camino(origen, destinos, adyacencia)


def test_bloquear_una_seccion_de_gradas_deja_ruta_por_la_otra(grafo):
    """Si se bloquean todas las aristas verticales de gradas NORTE, un aula de piso alto
    sigue llegando a un punto de encuentro usando gradas SUR."""
    aristas_bloqueadas = frozenset(
        a["id"] for a in grafo["aristas"] if a["tipo"] == "gradas" and "NORTE" in a["id"]
    )
    assert len(aristas_bloqueadas) > 0

    aristas_restantes = [a for a in grafo["aristas"] if a["id"] not in aristas_bloqueadas]
    resultado = vg.ResultadoValidacion()
    vg.verificar_caminos_a_punto_encuentro(grafo["nodos"], aristas_restantes, resultado)
    assert not resultado.tiene_errores_graves, resultado.errores


def test_bloquear_una_salida_deja_la_otra_disponible(grafo):
    adyacencia_sin_a = vg.construir_grafo_no_dirigido(
        [a for a in grafo["aristas"] if "SALIDA-A" not in (a["desde"], a["hasta"])]
    )
    assert vg.existe_camino("H401", {"SALIDA-B"}, adyacencia_sin_a)
    assert vg.existe_camino("G401", {"SALIDA-B"}, adyacencia_sin_a)

    adyacencia_sin_b = vg.construir_grafo_no_dirigido(
        [a for a in grafo["aristas"] if "SALIDA-B" not in (a["desde"], a["hasta"])]
    )
    assert vg.existe_camino("H401", {"SALIDA-A"}, adyacencia_sin_b)
    assert vg.existe_camino("G401", {"SALIDA-A"}, adyacencia_sin_b)


def test_validador_no_encuentra_errores_graves(grafo):
    schema = vg.cargar_json(vg.SCHEMA_PATH)
    resultado, _resumen = vg.validar(grafo, schema)
    assert not resultado.tiene_errores_graves, resultado.errores


def test_sin_ids_duplicados(grafo):
    ids_nodos = [n["id"] for n in grafo["nodos"]]
    assert len(ids_nodos) == len(set(ids_nodos))

    ids_aristas = [a["id"] for a in grafo["aristas"]]
    assert len(ids_aristas) == len(set(ids_aristas))
