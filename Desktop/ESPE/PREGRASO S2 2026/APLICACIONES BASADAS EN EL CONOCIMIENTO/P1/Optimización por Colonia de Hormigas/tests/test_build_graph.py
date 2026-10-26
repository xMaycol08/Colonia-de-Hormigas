"""Pruebas para scripts/build_graph.py (grafo provisional de Fase 1)."""

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
    pisos = int(config["pisos_por_bloque"])
    aulas = int(config["aulas_por_piso_por_bloque"])
    gradas = int(config["escaleras_por_bloque"])

    nodos_interiores_esperados_por_bloque = pisos * (1 + aulas + gradas)  # pasillo + aulas + gradas
    tipos_interiores = {"pasillo", "aula", "gradas"}
    nodos_interiores_h = [n for n in grafo["nodos"] if n["bloque"] == "H" and n["tipo"] in tipos_interiores]
    nodos_interiores_g = [n for n in grafo["nodos"] if n["bloque"] == "G" and n["tipo"] in tipos_interiores]

    assert len(nodos_interiores_h) == nodos_interiores_esperados_por_bloque
    assert len(nodos_interiores_g) == nodos_interiores_esperados_por_bloque

    nodos_exteriores = [n for n in grafo["nodos"] if n["bloque"] == "exterior"]
    # 3 caminos de Maps (Fase 0) + 3 puntos de encuentro provisionales
    assert len(nodos_exteriores) == 6

    salidas = [n for n in grafo["nodos"] if n["tipo"] == "salida"]
    assert len(salidas) == 2


def test_ningun_nodo_sin_confidence(grafo):
    for n in grafo["nodos"]:
        assert n.get("confidence"), f"Nodo sin confidence: {n['id']}"
        assert n["confidence"] in vg.cargar_json(vg.SCHEMA_PATH)["definitions"]["confidence"]["enum"]


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


def test_salida_a_y_b_alcanzables_desde_planta_baja_de_g_y_h(grafo):
    adyacencia = vg.construir_grafo_no_dirigido(grafo["aristas"])

    destinos = {"SALIDA-A", "SALIDA-B"}

    assert vg.existe_camino("H-P1-PAS", destinos, adyacencia), (
        "La planta baja de H no puede llegar a ninguna salida"
    )
    assert vg.existe_camino("G-P1-PAS", destinos, adyacencia), (
        "La planta baja de G no puede llegar a ninguna salida"
    )

    # Mas especifico: por la conexion de planta baja, H y G deben poder
    # alcanzar AMBAS salidas, no solo la propia.
    assert vg.existe_camino("H-P1-PAS", {"SALIDA-A"}, adyacencia)
    assert vg.existe_camino("H-P1-PAS", {"SALIDA-B"}, adyacencia)
    assert vg.existe_camino("G-P1-PAS", {"SALIDA-A"}, adyacencia)
    assert vg.existe_camino("G-P1-PAS", {"SALIDA-B"}, adyacencia)


def test_validador_no_encuentra_errores_graves(grafo):
    schema = vg.cargar_json(vg.SCHEMA_PATH)
    resultado, _resumen = vg.validar(grafo, schema)
    assert not resultado.tiene_errores_graves, resultado.errores


def test_sin_ids_duplicados(grafo):
    ids_nodos = [n["id"] for n in grafo["nodos"]]
    assert len(ids_nodos) == len(set(ids_nodos))

    ids_aristas = [a["id"] for a in grafo["aristas"]]
    assert len(ids_aristas) == len(set(ids_aristas))
