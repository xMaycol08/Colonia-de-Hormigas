"""Pruebas de las correcciones de Fase 2B: poda de callejones, retroceso y tasa de exito.

Ver docs/decisiones_fase2.md para el diagnostico que motivo estas
correcciones (ACO casi nunca encontraba ruta con los parametros originales
sobre el grafo real).
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))
sys.path.insert(0, str(RAIZ_PROYECTO / "tests"))

import random  # noqa: E402

from grafo import Grafo, cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
from aco import podar_callejones, _construir_camino_hormiga, ejecutar_aco  # noqa: E402
from _grafo_prueba import _nodo, _arista, config_modelo_prueba, config_aco_prueba  # noqa: E402


def _grafo_con_callejon():
    """A(origen) -- M -- PE, con un callejon D colgando de M (D no es origen ni PE)."""
    nodos = [_nodo("A", "aula"), _nodo("M", "pasillo"), _nodo("D", "aula"), _nodo("PE", "punto_encuentro")]
    aristas = [
        _arista("A-M", "A", "M", 1.0),
        _arista("M-D", "M", "D", 1.0),
        _arista("M-PE", "M", "PE", 1.0),
    ]
    return Grafo(nodos, aristas)


def test_podar_callejones_elimina_el_nodo_hoja_no_protegido():
    grafo = _grafo_con_callejon()
    vista, podados = podar_callejones(grafo, protegidos={"A", "PE"})

    assert "D" in podados
    assert "D" not in vista.nodos_por_id
    assert "A" in vista.nodos_por_id
    assert "PE" in vista.nodos_por_id
    assert "M" in vista.nodos_por_id  # M queda con grado 2 (A, PE), no se poda


def test_podar_callejones_no_elimina_nodos_protegidos_aunque_sean_hoja():
    """Si el ORIGEN es, el mismo, un nodo hoja (caso normal: un aula), no debe podarse."""
    grafo = _grafo_con_callejon()
    # Aqui 'D' actua como origen: es hoja, pero esta protegido.
    vista, podados = podar_callejones(grafo, protegidos={"D", "PE"})

    assert "D" not in podados
    assert "D" in vista.nodos_por_id


def test_podar_callejones_no_modifica_el_grafo_original():
    grafo = _grafo_con_callejon()
    n_nodos_antes = len(grafo.nodos_por_id)
    n_aristas_antes = len(grafo.aristas_por_id)

    podar_callejones(grafo, protegidos={"A", "PE"})

    assert len(grafo.nodos_por_id) == n_nodos_antes
    assert len(grafo.aristas_por_id) == n_aristas_antes
    assert "D" in grafo.nodos_por_id  # el grafo original sigue intacto


def test_retroceso_permite_recuperarse_de_un_callejon_no_prunado():
    """Verifica _construir_camino_hormiga() directamente (SIN poda previa), sobre un
    grafo donde la feromona empuja fuertemente a la hormiga hacia un callejon sin
    salida (M-D) antes de la unica salida real (M-PE). Con retroceso, deberia
    recuperarse y llegar a PE en vez de fallar de inmediato.
    """
    grafo = _grafo_con_callejon()
    config_modelo = config_modelo_prueba()
    config_aco = config_aco_prueba(alfa=1.0, beta=1.0)

    # Feromona sesgada para que M-D sea ~1000x mas atractivo que M-PE.
    tau = {"A-M": 1.0, "M-D": 1000.0, "M-PE": 0.001}
    heuristica = {n: 0.0 for n in grafo.nodos_por_id}

    exitos = 0
    N = 50
    for semilla in range(N):
        rng = random.Random(semilla)
        camino, costo, pe = _construir_camino_hormiga(grafo, "A", config_modelo, config_aco, tau, heuristica, rng)
        if camino is not None:
            exitos += 1
            assert camino[-1] == "PE"

    # Sin retroceso, cualquier hormiga que entrara a D fallaria de inmediato
    # (D no tiene mas vecinos que M, ya visitado). Con retroceso, SIEMPRE se
    # recupera en este grafo (solo hay un callejon y una unica alternativa).
    assert exitos == N, f"Se esperaba que el retroceso recuperara todas las corridas, exitos={exitos}/{N}"


def test_tasa_de_exito_sobre_el_grafo_real_cumple_el_criterio_de_aceptacion():
    """Version mas liviana (10 corridas/origen en vez de 30) del criterio de
    aceptacion de la tarea (>= 95% de exito). La verificacion oficial con 30
    corridas por origen se corrio aparte (ver docs/decisiones_fase2.md).
    """
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    origenes = [o["id_nodo"] for o in config_modelo["origenes_representativos"]]
    n_corridas_por_origen = 10

    total = 0
    exitos = 0
    for origen in origenes:
        for semilla in range(n_corridas_por_origen):
            resultado = ejecutar_aco(grafo, origen, config_modelo, config_aco, semilla=semilla)
            total += 1
            if resultado.tiene_ruta:
                exitos += 1

    tasa_exito = exitos / total * 100
    assert tasa_exito >= 95.0, f"Tasa de exito {tasa_exito:.1f}% < 95% (criterio de aceptacion de Fase 2B)"
