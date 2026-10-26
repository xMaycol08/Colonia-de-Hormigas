"""Metricas de evacuacion para los origenes representativos.

Reproduce, de forma aproximada, las dos metricas oficiales de la Guia de
simulacros (docs/base_informe.md, seccion (b), seccion 5): tiempo de la
PRIMERA persona y tiempo de la ULTIMA persona en llegar a un punto de
encuentro, medidos desde la emision de la alerta (aqui: desde tiempo 0).

Tambien calcula la brecha de ACO frente al optimo de Dijkstra.

Todos los numeros (tiempo_reaccion_s, poblacion_por_origen,
tiempo_entre_personas_s, origenes_representativos) vienen de
data/config_modelo.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aco import ejecutar_aco
from costos import tiempo_arista
from dijkstra import buscar_ruta
from grafo import Grafo


@dataclass
class MetricasOrigen:
    """Metricas de tiempo de evacuacion para un origen representativo."""

    origen: str
    poblacion: int
    tiempo_recorrido_s: float
    tiempo_primera_persona_s: float
    tiempo_ultima_persona_s: float
    punto_encuentro: str | None
    tiene_ruta: bool


def tiempo_recorrido_ruta(grafo: Grafo, camino: list[str], config_modelo: dict[str, Any]) -> float:
    """Suma el tiempo estimado (segundos) de recorrer todas las aristas de un camino."""
    total = 0.0
    for a, b in zip(camino, camino[1:]):
        for vecino_id, arista in grafo.vecinos(a):
            if vecino_id == b:
                total += tiempo_arista(arista, config_modelo)
                break
    return total


def calcular_metricas_origen(
    grafo: Grafo,
    origen: str,
    poblacion: int,
    config_modelo: dict[str, Any],
    aristas_bloqueadas: frozenset[str] = frozenset(),
) -> MetricasOrigen:
    """Calcula tiempo de primera y ultima persona para un origen, usando la ruta optima (Dijkstra).

    Modelo simplificado (ver data/config_modelo.json, parametro
    tiempo_entre_personas_s, para la justificacion y limitaciones):
        tiempo_primera_persona = tiempo_reaccion_s + tiempo_recorrido_ruta
        tiempo_ultima_persona  = tiempo_primera_persona
                                  + (poblacion - 1) * tiempo_entre_personas_s
    """
    resultado = buscar_ruta(grafo, origen, config_modelo, aristas_bloqueadas)

    if not resultado.tiene_ruta:
        return MetricasOrigen(
            origen=origen,
            poblacion=poblacion,
            tiempo_recorrido_s=float("inf"),
            tiempo_primera_persona_s=float("inf"),
            tiempo_ultima_persona_s=float("inf"),
            punto_encuentro=None,
            tiene_ruta=False,
        )

    tiempo_recorrido = tiempo_recorrido_ruta(grafo, resultado.camino, config_modelo)
    tiempo_reaccion = config_modelo["tiempo_reaccion_s"]
    tiempo_entre_personas = config_modelo["tiempo_entre_personas_s"]

    tiempo_primera = tiempo_reaccion + tiempo_recorrido
    tiempo_ultima = tiempo_primera + (poblacion - 1) * tiempo_entre_personas

    return MetricasOrigen(
        origen=origen,
        poblacion=poblacion,
        tiempo_recorrido_s=tiempo_recorrido,
        tiempo_primera_persona_s=tiempo_primera,
        tiempo_ultima_persona_s=tiempo_ultima,
        punto_encuentro=resultado.punto_encuentro,
        tiene_ruta=True,
    )


def calcular_metricas_todos_los_origenes(
    grafo: Grafo,
    config_modelo: dict[str, Any],
    aristas_bloqueadas: frozenset[str] = frozenset(),
) -> list[MetricasOrigen]:
    """Calcula MetricasOrigen para cada uno de los 42 origenes de poblacion_por_origen
    (40 aulas + 2 origenes de PB), que son los origenes oficiales para los experimentos
    (ver data/config_modelo.json). Para pruebas rapidas con menos origenes, usar
    config_modelo['origenes_representativos'] (10) directamente con calcular_metricas_origen().
    """
    poblaciones = config_modelo["poblacion_por_origen"]

    return [
        calcular_metricas_origen(grafo, id_origen, poblacion, config_modelo, aristas_bloqueadas)
        for id_origen, poblacion in poblaciones.items()
    ]


def brecha_aco_vs_dijkstra_pct(
    grafo: Grafo,
    origen: str,
    config_modelo: dict[str, Any],
    config_aco: dict[str, Any],
    aristas_bloqueadas: frozenset[str] = frozenset(),
) -> float | None:
    """Calcula la brecha (%) del costo de ACO frente al optimo de Dijkstra para un origen.

    brecha = (costo_aco - costo_dijkstra) / costo_dijkstra * 100.
    Devuelve None si Dijkstra no encuentra ruta (no se puede calcular brecha).
    """
    resultado_dijkstra = buscar_ruta(grafo, origen, config_modelo, aristas_bloqueadas)
    if not resultado_dijkstra.tiene_ruta:
        return None

    resultado_aco = ejecutar_aco(
        grafo, origen, config_modelo, config_aco, aristas_bloqueadas=aristas_bloqueadas
    )
    if not resultado_aco.tiene_ruta:
        return None

    return (resultado_aco.mejor_costo - resultado_dijkstra.costo) / resultado_dijkstra.costo * 100
