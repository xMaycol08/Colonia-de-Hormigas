"""Carga del grafo de evacuacion y construccion de la lista de adyacencia.

Modulo auxiliar compartido por dijkstra.py, aco.py, agente.py y metricas.py,
para no repetir la logica de carga/indexado del grafo en cada uno (decision
de diseno de la Fase 2, no pedida explicitamente en el enunciado).

El grafo se trata como NO DIRIGIDO: cada arista se puede recorrer en
cualquier sentido (igual que en scripts/validate_graph.py, Fase 0).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
GRAFO_PATH = RAIZ_PROYECTO / "data" / "campus_graph.json"
CONFIG_MODELO_PATH = RAIZ_PROYECTO / "data" / "config_modelo.json"
CONFIG_ACO_PATH = RAIZ_PROYECTO / "data" / "config_aco.json"


def cargar_json(ruta: Path) -> dict[str, Any]:
    """Carga un archivo JSON desde disco."""
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_configuracion(ruta: Path) -> dict[str, Any]:
    """Carga un archivo de config (config_modelo.json o config_aco.json) como {parametro: valor}."""
    datos = cargar_json(ruta)
    return {nombre: info["value"] for nombre, info in datos["parametros"].items()}


class Grafo:
    """Representacion en memoria del grafo de evacuacion, lista para busqueda de rutas."""

    def __init__(self, nodos: list[dict[str, Any]], aristas: list[dict[str, Any]]):
        self.nodos_por_id: dict[str, dict[str, Any]] = {n["id"]: n for n in nodos}
        self.aristas_por_id: dict[str, dict[str, Any]] = {a["id"]: a for a in aristas}
        self.ids_puntos_encuentro: set[str] = {
            n["id"] for n in nodos if n["tipo"] == "punto_encuentro"
        }
        self._adyacencia: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for arista in aristas:
            self._adyacencia.setdefault(arista["desde"], []).append((arista["hasta"], arista))
            self._adyacencia.setdefault(arista["hasta"], []).append((arista["desde"], arista))

    def vecinos(self, nodo_id: str, aristas_bloqueadas: frozenset[str] = frozenset()) -> list[tuple[str, dict[str, Any]]]:
        """Devuelve [(vecino_id, arista), ...] desde nodo_id, ignorando aristas bloqueadas."""
        return [
            (vecino_id, arista)
            for vecino_id, arista in self._adyacencia.get(nodo_id, [])
            if arista["id"] not in aristas_bloqueadas
        ]

    def es_punto_encuentro(self, nodo_id: str) -> bool:
        """Indica si un nodo es de tipo punto_encuentro."""
        return nodo_id in self.ids_puntos_encuentro


def cargar_grafo(ruta: Path = GRAFO_PATH) -> Grafo:
    """Carga data/campus_graph.json y devuelve un objeto Grafo listo para usar."""
    datos = cargar_json(ruta)
    return Grafo(datos["nodos"], datos["aristas"])


def aplicar_congestion(grafo: Grafo, congestion: dict[str, float]) -> Grafo:
    """Devuelve un Grafo cuyas aristas tienen distancia_m escalada por congestion.

    congestion: {id_arista: factor multiplicativo >= 1.0}. Usado por
    agente.py y benchmark.py para modelar congestion sin tocar
    costos.costo_arista() (que no la contempla).
    """
    if not congestion:
        return grafo

    import copy

    datos_nodos = list(grafo.nodos_por_id.values())
    datos_aristas = []
    for arista in grafo.aristas_por_id.values():
        factor = congestion.get(arista["id"])
        if factor is None or arista["distancia_m"] is None:
            datos_aristas.append(arista)
        else:
            arista_congestionada = copy.deepcopy(arista)
            arista_congestionada["distancia_m"] = arista["distancia_m"] * factor
            datos_aristas.append(arista_congestionada)

    return Grafo(datos_nodos, datos_aristas)
