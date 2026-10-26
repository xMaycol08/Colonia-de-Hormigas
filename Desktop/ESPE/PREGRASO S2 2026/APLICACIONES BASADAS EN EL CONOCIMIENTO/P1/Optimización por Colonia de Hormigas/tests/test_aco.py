"""Pruebas 2, 3, 4 y 6 (Fase 2) del algoritmo ACO, sobre el grafo pequeno de prueba.

Se usa el grafo pequeno (no el real) para que el mecanismo de ACO (muestreo,
feromona, tabu, bloqueos, warm start) se pueda verificar de forma rapida y
determinista. Ver docs/decisiones_fase2.md para la justificacion: con los
valores por defecto de data/config_aco.json, el grafo REAL tiene una tasa de
exito por hormiga tan baja (~0.01%-0.05%) que ACO casi nunca converge en
100 iteraciones / paciencia 25; eso no es un bug, es un hallazgo de esta
fase que se reporta aparte (no se puede usar el grafo real para probar
reproducibilidad o comparaciones de costo de forma fiable).
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))
sys.path.insert(0, str(RAIZ_PROYECTO / "tests"))

from grafo import Grafo  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from aco import ejecutar_aco  # noqa: E402
from _grafo_prueba import (  # noqa: E402
    nodos_y_aristas_prueba,
    config_modelo_prueba,
    config_aco_prueba,
)


def _construir_grafo():
    nodos, aristas = nodos_y_aristas_prueba()
    return Grafo(nodos, aristas)


def test_aco_con_semilla_fija_es_reproducible():
    grafo = _construir_grafo()
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(semilla=123)

    r1 = ejecutar_aco(grafo, "A", config_modelo, config_aco)
    r2 = ejecutar_aco(grafo, "A", config_modelo, config_aco)

    assert r1.tiene_ruta and r2.tiene_ruta
    assert r1.mejor_costo == r2.mejor_costo
    assert r1.mejor_camino == r2.mejor_camino
    assert r1.iteracion_mejor_solucion == r2.iteracion_mejor_solucion
    assert [h.mejor_costo_iteracion for h in r1.historial] == [h.mejor_costo_iteracion for h in r2.historial]


def test_costo_de_aco_nunca_es_menor_que_dijkstra():
    grafo = _construir_grafo()
    config_modelo = config_modelo_prueba()

    resultado_dijkstra = buscar_ruta(grafo, "A", config_modelo)
    assert resultado_dijkstra.tiene_ruta

    for semilla in range(10):
        config_aco = config_aco_prueba(semilla=semilla)
        resultado_aco = ejecutar_aco(grafo, "A", config_modelo, config_aco)
        if resultado_aco.tiene_ruta:
            assert resultado_aco.mejor_costo >= resultado_dijkstra.costo - 1e-9, (
                f"semilla={semilla}: ACO={resultado_aco.mejor_costo} < "
                f"Dijkstra={resultado_dijkstra.costo} (esto seria un bug)"
            )


def test_aco_respeta_aristas_bloqueadas():
    grafo = _construir_grafo()
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(semilla=1)

    # Bloquear la ruta optima (M-B); solo debe quedar la ruta via C (costo 7).
    resultado = ejecutar_aco(grafo, "A", config_modelo, config_aco, aristas_bloqueadas=frozenset({"M-B"}))

    assert resultado.tiene_ruta
    assert "B" not in resultado.mejor_camino
    assert resultado.mejor_costo == 7.0


def test_aco_sin_salida_devuelve_sin_ruta_sin_colgarse():
    grafo = _construir_grafo()
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(semilla=2, n_iteraciones=10, paciencia_estancamiento=5)

    # Bloquear la unica arista que sale del origen A.
    resultado = ejecutar_aco(grafo, "A", config_modelo, config_aco, aristas_bloqueadas=frozenset({"A-M"}))

    assert not resultado.tiene_ruta
    assert resultado.mejor_camino is None
    assert resultado.mejor_costo == float("inf")
    # Si llegamos aqui, el test termino (no se colgo).


def test_warm_start_no_empeora_el_resultado_frente_a_cold_start():
    """Escenario de bloqueo: se ejecuta ACO sin bloqueos, luego se bloquea la ruta
    optima (M-B) y se compara continuar con warm start vs. empezar en frio,
    con la misma semilla y el mismo numero de iteraciones.
    """
    grafo = _construir_grafo()
    config_modelo = config_modelo_prueba()

    semillas_que_fallan = []

    for semilla in range(10):
        config_aco = config_aco_prueba(semilla=semilla, n_iteraciones=15, paciencia_estancamiento=15)

        resultado_previo = ejecutar_aco(grafo, "A", config_modelo, config_aco)
        assert resultado_previo.tiene_ruta

        resultado_cold = ejecutar_aco(
            grafo, "A", config_modelo, config_aco, aristas_bloqueadas=frozenset({"M-B"})
        )
        resultado_warm = ejecutar_aco(
            grafo,
            "A",
            config_modelo,
            config_aco,
            aristas_bloqueadas=frozenset({"M-B"}),
            feromona_inicial=resultado_previo.feromona_final,
        )

        assert resultado_cold.tiene_ruta and resultado_warm.tiene_ruta

        if resultado_warm.mejor_costo > resultado_cold.mejor_costo + 1e-9:
            semillas_que_fallan.append(semilla)

    assert not semillas_que_fallan, (
        f"El warm start empeoro el resultado frente al cold start con las semillas: {semillas_que_fallan}"
    )
