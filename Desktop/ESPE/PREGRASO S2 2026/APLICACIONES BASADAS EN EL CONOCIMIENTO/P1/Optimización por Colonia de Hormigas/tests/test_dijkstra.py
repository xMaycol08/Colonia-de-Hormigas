"""Prueba 1 (Fase 2): Dijkstra encuentra el optimo en un grafo pequeno construido a mano."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))
sys.path.insert(0, str(RAIZ_PROYECTO / "tests"))

from grafo import Grafo  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from _grafo_prueba import nodos_y_aristas_prueba, config_modelo_prueba  # noqa: E402


def test_dijkstra_encuentra_el_optimo():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = config_modelo_prueba()

    resultado = buscar_ruta(grafo, "A", config_modelo)

    assert resultado.tiene_ruta
    assert resultado.costo == 3.0
    assert resultado.camino == ["A", "M", "B", "PE"]
    assert resultado.punto_encuentro == "PE"
    assert resultado.nodos_expandidos > 0


def test_dijkstra_sin_ruta_no_lanza_excepcion():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = config_modelo_prueba()

    # Bloquear la unica arista que sale de A.
    resultado = buscar_ruta(grafo, "A", config_modelo, aristas_bloqueadas=frozenset({"A-M"}))

    assert not resultado.tiene_ruta
    assert resultado.camino is None
    assert resultado.costo == float("inf")


def test_dijkstra_sobre_el_grafo_real_encuentra_ruta():
    """Sanity check sobre data/campus_graph.json (el grafo real, no el de prueba)."""
    from grafo import cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH

    grafo_real = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)

    resultado = buscar_ruta(grafo_real, "H301", config_modelo)

    assert resultado.tiene_ruta
    assert resultado.costo > 0
    assert resultado.camino[0] == "H301"
    assert grafo_real.es_punto_encuentro(resultado.camino[-1])
