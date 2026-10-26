"""Prueba (Fase 3): aco_iterativo() da el mismo resultado final que ejecutar_aco()
con la misma semilla (ejecutar_aco no duplica logica, solo consume el generador).
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))
sys.path.insert(0, str(RAIZ_PROYECTO / "tests"))

from grafo import Grafo, cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
from aco import ejecutar_aco, aco_iterativo  # noqa: E402
from _grafo_prueba import nodos_y_aristas_prueba, config_modelo_prueba, config_aco_prueba  # noqa: E402


def test_aco_iterativo_coincide_con_ejecutar_aco_grafo_pequeno():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(semilla=7)

    resultado = ejecutar_aco(grafo, "A", config_modelo, config_aco)

    ultimo_snap = None
    for snap in aco_iterativo(grafo, "A", config_modelo, config_aco):
        ultimo_snap = snap

    assert ultimo_snap is not None
    assert ultimo_snap.mejor_camino_global == resultado.mejor_camino
    assert ultimo_snap.mejor_costo_global == resultado.mejor_costo
    assert ultimo_snap.punto_encuentro_global == resultado.punto_encuentro
    assert ultimo_snap.iteracion_mejor_global == resultado.iteracion_mejor_solucion


def test_aco_iterativo_coincide_con_ejecutar_aco_grafo_real():
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    origen = config_modelo["origenes_representativos"][0]["id_nodo"]

    resultado = ejecutar_aco(grafo, origen, config_modelo, config_aco, semilla=3)

    ultimo_snap = None
    for snap in aco_iterativo(grafo, origen, config_modelo, config_aco, semilla=3):
        ultimo_snap = snap

    assert ultimo_snap is not None
    assert ultimo_snap.mejor_costo_global == resultado.mejor_costo
    assert ultimo_snap.mejor_camino_global == resultado.mejor_camino


def test_aco_iterativo_entrega_feromona_en_cada_iteracion():
    nodos, aristas = nodos_y_aristas_prueba()
    grafo = Grafo(nodos, aristas)
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(semilla=1, n_iteraciones=5, paciencia_estancamiento=5)

    snapshots = list(aco_iterativo(grafo, "A", config_modelo, config_aco))

    assert len(snapshots) >= 1
    for snap in snapshots:
        assert isinstance(snap.feromona, dict)
        assert set(snap.feromona.keys()) == set(grafo.aristas_por_id.keys())
