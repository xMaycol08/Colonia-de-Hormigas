"""Prueba 5 (Fase 2): si se bloquea la Salida A, un origen en H sigue encontrando
ruta por la Salida B, via la conexion de planta baja H<->G.

Se usa el grafo REAL (data/campus_graph.json) y Dijkstra: esta prueba es
sobre la TOPOLOGIA/bloqueo del grafo (que existe un camino alterno), no
sobre el comportamiento estocastico de ACO. Ver tests/test_aco.py para el
porque de usar un grafo pequeno para las pruebas de ACO.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402

ID_ARISTA_SALIDA_H = "H-PB-SALIDA"
ID_ARISTA_CONEXION_H_G = "CONEXION-PB-H-G"


def test_salida_a_bloqueada_origen_en_h_encuentra_ruta_por_salida_b():
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)

    resultado_sin_bloqueo = buscar_ruta(grafo, "H-P1-AULA01", config_modelo)
    assert resultado_sin_bloqueo.tiene_ruta
    assert resultado_sin_bloqueo.punto_encuentro == "PE-2", (
        "Sanity check: sin bloqueos, la ruta optima desde H-P1-AULA01 deberia "
        "salir por SALIDA-A y PE-2 (ver src/grafo.py / data/campus_graph.json)."
    )

    resultado_con_bloqueo = buscar_ruta(
        grafo, "H-P1-AULA01", config_modelo, aristas_bloqueadas=frozenset({ID_ARISTA_SALIDA_H})
    )

    assert resultado_con_bloqueo.tiene_ruta, (
        "Con la salida de H bloqueada, deberia seguir existiendo ruta via la "
        "conexion de planta baja H<->G y Salida B."
    )
    assert "SALIDA-A" not in resultado_con_bloqueo.camino
    assert "SALIDA-B" in resultado_con_bloqueo.camino
    assert ID_ARISTA_CONEXION_H_G in _aristas_usadas(grafo, resultado_con_bloqueo.camino)


def test_bloquear_todas_las_salidas_de_h_y_g_no_deja_ruta():
    """Caso extremo (no pedido explicitamente, pero coherente con la prueba 4):
    si se bloquean AMBAS puertas de salida y la conexion entre bloques, ningun
    origen interior deberia encontrar ruta, y la busqueda debe terminar sin
    colgarse.
    """
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)

    bloqueadas = frozenset({ID_ARISTA_SALIDA_H, "G-PB-SALIDA", ID_ARISTA_CONEXION_H_G})
    resultado = buscar_ruta(grafo, "H-P1-AULA01", config_modelo, aristas_bloqueadas=bloqueadas)

    assert not resultado.tiene_ruta
    assert resultado.camino is None


def _aristas_usadas(grafo, camino: list[str]) -> set[str]:
    """Devuelve el conjunto de ids de arista usados por un camino de nodos."""
    ids = set()
    for a, b in zip(camino, camino[1:]):
        for vecino_id, arista in grafo.vecinos(a):
            if vecino_id == b:
                ids.add(arista["id"])
                break
    return ids
