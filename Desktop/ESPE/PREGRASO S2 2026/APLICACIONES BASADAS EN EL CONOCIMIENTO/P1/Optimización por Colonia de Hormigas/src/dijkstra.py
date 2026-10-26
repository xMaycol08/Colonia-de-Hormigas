"""Dijkstra multi-objetivo: desde un origen hasta CUALQUIERA de los puntos de encuentro.

Como Dijkstra finaliza (saca de la cola de prioridad) los nodos en orden no
decreciente de costo, basta con correr un Dijkstra de un solo origen y
detenerse apenas se finalice el PRIMER nodo tipo punto_encuentro: ese es,
por construccion, el punto de encuentro alcanzable con menor costo total.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any

from costos import costo_arista
from grafo import Grafo


@dataclass
class ResultadoDijkstra:
    """Resultado de una busqueda de Dijkstra."""

    camino: list[str] | None
    costo: float
    punto_encuentro: str | None
    nodos_expandidos: int
    tiene_ruta: bool = field(init=False)

    def __post_init__(self) -> None:
        self.tiene_ruta = self.camino is not None


def buscar_ruta(
    grafo: Grafo,
    origen: str,
    config_modelo: dict[str, Any],
    aristas_bloqueadas: frozenset[str] = frozenset(),
) -> ResultadoDijkstra:
    """Busca la ruta de menor costo desde 'origen' hasta cualquier punto de encuentro.

    Devuelve un ResultadoDijkstra con camino=None y costo=inf si no hay ruta
    (p. ej. porque todas las salidas del nodo estan bloqueadas); nunca lanza
    una excepcion ni entra en bucle infinito.
    """
    if origen not in grafo.nodos_por_id:
        raise KeyError(f"Nodo origen desconocido: '{origen}'")

    distancias: dict[str, float] = {origen: 0.0}
    predecesor: dict[str, str | None] = {origen: None}
    visitados: set[str] = set()
    cola: list[tuple[float, str]] = [(0.0, origen)]
    nodos_expandidos = 0

    while cola:
        costo_actual, nodo_actual = heapq.heappop(cola)
        if nodo_actual in visitados:
            continue
        visitados.add(nodo_actual)
        nodos_expandidos += 1

        if grafo.es_punto_encuentro(nodo_actual):
            camino = _reconstruir_camino(predecesor, nodo_actual)
            return ResultadoDijkstra(
                camino=camino,
                costo=costo_actual,
                punto_encuentro=nodo_actual,
                nodos_expandidos=nodos_expandidos,
            )

        for vecino_id, arista in grafo.vecinos(nodo_actual, aristas_bloqueadas):
            if vecino_id in visitados:
                continue
            nuevo_costo = costo_actual + costo_arista(arista, config_modelo)
            if nuevo_costo < distancias.get(vecino_id, float("inf")):
                distancias[vecino_id] = nuevo_costo
                predecesor[vecino_id] = nodo_actual
                heapq.heappush(cola, (nuevo_costo, vecino_id))

    return ResultadoDijkstra(
        camino=None,
        costo=float("inf"),
        punto_encuentro=None,
        nodos_expandidos=nodos_expandidos,
    )


def _reconstruir_camino(predecesor: dict[str, str | None], destino: str) -> list[str]:
    """Reconstruye el camino desde el origen hasta 'destino' usando el diccionario de predecesores."""
    camino = [destino]
    while predecesor[camino[-1]] is not None:
        camino.append(predecesor[camino[-1]])
    camino.reverse()
    return camino
