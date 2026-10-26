"""Pruebas de src/metricas.py sobre el grafo pequeno de prueba."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))
sys.path.insert(0, str(RAIZ_PROYECTO / "tests"))

from grafo import Grafo  # noqa: E402
from metricas import calcular_metricas_origen, brecha_aco_vs_dijkstra_pct  # noqa: E402
from _grafo_prueba import nodos_y_aristas_prueba, config_modelo_prueba, config_aco_prueba  # noqa: E402


def _config_modelo_con_metricas(**overrides):
    base = config_modelo_prueba()
    base.update({"tiempo_reaccion_s": 10.0, "tiempo_entre_personas_s": 2.0})
    base.update(overrides)
    return base


def test_calcular_metricas_origen_primera_y_ultima_persona():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = _config_modelo_con_metricas()

    metricas = calcular_metricas_origen(grafo, "A", poblacion=5, config_modelo=config_modelo)

    assert metricas.tiene_ruta
    # costo optimo = 3.0 metros, velocidad = 1.2 m/s -> tiempo_recorrido = 2.5 s
    assert metricas.tiempo_recorrido_s == 2.5
    assert metricas.tiempo_primera_persona_s == 10.0 + 2.5
    # ultima = primera + (5-1)*2.0
    assert metricas.tiempo_ultima_persona_s == (10.0 + 2.5) + 4 * 2.0
    assert metricas.tiempo_ultima_persona_s >= metricas.tiempo_primera_persona_s


def test_calcular_metricas_origen_sin_ruta():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = _config_modelo_con_metricas()

    metricas = calcular_metricas_origen(
        grafo, "A", poblacion=5, config_modelo=config_modelo, aristas_bloqueadas=frozenset({"A-M"})
    )

    assert not metricas.tiene_ruta
    assert metricas.tiempo_primera_persona_s == float("inf")
    assert metricas.tiempo_ultima_persona_s == float("inf")


def test_brecha_aco_vs_dijkstra_no_negativa():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(semilla=5)

    brecha = brecha_aco_vs_dijkstra_pct(grafo, "A", config_modelo, config_aco)

    assert brecha is not None
    assert brecha >= -1e-9  # ACO nunca deberia ser "mejor" que el optimo
