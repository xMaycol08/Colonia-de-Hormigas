"""Funcion de costo unica, usada por Dijkstra, ACO y el agente.

Costo de una arista = distancia_m (ya incluye el factor de gradas, ver
scripts/build_graph.py) * penalizacion_techado si la arista es techada.
Tiempo estimado = costo_m / velocidad_caminata_m_s.

Ningun numero vive aqui: penalizacion_techado y velocidad_caminata_m_s se
leen siempre de data/config_modelo.json (parametro config pasado por quien
llama a estas funciones).
"""

from __future__ import annotations

from typing import Any


def costo_arista(arista: dict[str, Any], config_modelo: dict[str, Any]) -> float:
    """Calcula el costo (en metros equivalentes) de recorrer una arista.

    costo = distancia_m, multiplicado por penalizacion_techado si la arista
    esta techada. distancia_m ya incluye, para las aristas tipo 'gradas', el
    factor de costo de gradas (ver scripts/build_graph.py).
    """
    distancia = arista["distancia_m"]
    if distancia is None:
        raise ValueError(f"Arista '{arista['id']}' no tiene distancia_m; no se puede calcular su costo.")

    if arista.get("techado"):
        return distancia * config_modelo["penalizacion_techado"]
    return distancia


def tiempo_arista(arista: dict[str, Any], config_modelo: dict[str, Any]) -> float:
    """Calcula el tiempo estimado (en segundos) de recorrer una arista.

    tiempo = costo_arista / velocidad_caminata_m_s.
    """
    costo = costo_arista(arista, config_modelo)
    return costo / config_modelo["velocidad_caminata_m_s"]
