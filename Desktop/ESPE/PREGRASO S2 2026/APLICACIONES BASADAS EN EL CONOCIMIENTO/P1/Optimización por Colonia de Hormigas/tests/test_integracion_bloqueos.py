"""Prueba 5 (Fase 2) + Tarea E (Fase 1-bis): si se bloquea el acceso a Salida A
(gradas sur -> Salida A), un origen en H sigue encontrando ruta por Salida B
(via el pasillo central y gradas norte).

Se usa el grafo REAL (data/campus_graph.json) y Dijkstra: esta prueba es
sobre la TOPOLOGIA/bloqueo del grafo (que existe un camino alterno), no
sobre el comportamiento estocastico de ACO.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402

ID_ARISTA_GRADAS_SUR_SALIDA_A = "GRADAS-SUR-PB-SALIDA-A"
ID_ARISTA_GRADAS_NORTE_SALIDA_B = "GRADAS-NORTE-PB-SALIDA-B"


def test_salida_a_bloqueada_origen_en_h_encuentra_ruta_por_salida_b():
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)

    resultado_sin_bloqueo = buscar_ruta(grafo, "H101", config_modelo)
    assert resultado_sin_bloqueo.tiene_ruta

    resultado_con_bloqueo = buscar_ruta(
        grafo, "H101", config_modelo, aristas_bloqueadas=frozenset({ID_ARISTA_GRADAS_SUR_SALIDA_A})
    )

    assert resultado_con_bloqueo.tiene_ruta, (
        "Con el acceso a Salida A bloqueado, deberia seguir existiendo ruta via "
        "el pasillo central y gradas norte hacia Salida B."
    )
    assert "SALIDA-A" not in resultado_con_bloqueo.camino
    assert "SALIDA-B" in resultado_con_bloqueo.camino


def test_bloquear_todas_las_salidas_no_deja_ruta():
    """Si se bloquean los dos accesos de PB a las salidas, ningun origen interior
    deberia encontrar ruta, y la busqueda debe terminar sin colgarse.
    """
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)

    bloqueadas = frozenset({ID_ARISTA_GRADAS_SUR_SALIDA_A, ID_ARISTA_GRADAS_NORTE_SALIDA_B})
    resultado = buscar_ruta(grafo, "H101", config_modelo, aristas_bloqueadas=bloqueadas)

    assert not resultado.tiene_ruta
    assert resultado.camino is None
