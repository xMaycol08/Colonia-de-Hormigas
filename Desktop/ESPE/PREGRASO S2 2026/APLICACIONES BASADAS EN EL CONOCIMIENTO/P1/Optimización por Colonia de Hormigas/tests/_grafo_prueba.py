"""Grafo pequeno construido a mano, compartido por varias pruebas de Fase 2.

No es el grafo real del campus: es un grafo minimo, diseniado para que el
resultado optimo (via Dijkstra) y el comportamiento de ACO sean faciles de
verificar a mano.

Topologia:

    A --(1)-- M --(1)-- B --(1)-- PE
              |
              +--(5)---- C --(1)-- PE

- A: origen (aula).
- M: nodo intermedio (pasillo).
- B, C: dos rutas alternativas desde M hasta PE (via_exterior).
- PE: punto de encuentro.

Camino optimo: A-M-B-PE, costo 3. Camino alternativo: A-M-C-PE, costo 7.
Ninguna arista es techada (penalizacion_techado no afecta estas pruebas).
"""

from __future__ import annotations

from typing import Any


def _nodo(id: str, tipo: str) -> dict[str, Any]:
    return {
        "id": id,
        "nombre": id,
        "tipo": tipo,
        "bloque": "exterior",
        "piso": None,
        "lat": None,
        "lon": None,
        "x_m": None,
        "y_m": None,
        "techado": False,
        "riesgo_caida": False,
        "capacidad_estimada_personas": None,
        "source": "grafo de prueba (hecho a mano)",
        "confidence": "supuesto",
        "status": "provisional",
        "notes": None,
    }


def _arista(id: str, desde: str, hasta: str, distancia_m: float, techado: bool = False) -> dict[str, Any]:
    return {
        "id": id,
        "desde": desde,
        "hasta": hasta,
        "distancia_m": distancia_m,
        "tipo": "plano",
        "techado": techado,
        "ancho_m": 2.0,
        "bloqueable": True,
        "source": "grafo de prueba (hecho a mano)",
        "confidence": "supuesto",
        "status": "provisional",
        "notes": None,
    }


def nodos_y_aristas_prueba() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Devuelve (nodos, aristas) del grafo pequeno de prueba."""
    nodos = [
        _nodo("A", "aula"),
        _nodo("M", "pasillo"),
        _nodo("B", "via_exterior"),
        _nodo("C", "via_exterior"),
        _nodo("PE", "punto_encuentro"),
    ]
    aristas = [
        _arista("A-M", "A", "M", 1.0),
        _arista("M-B", "M", "B", 1.0),
        _arista("M-C", "M", "C", 5.0),
        _arista("B-PE", "B", "PE", 1.0),
        _arista("C-PE", "C", "PE", 1.0),
    ]
    return nodos, aristas


def config_modelo_prueba() -> dict[str, Any]:
    """Config de modelo minima para las pruebas (penalizacion_techado y velocidad no afectan este grafo)."""
    return {
        "penalizacion_techado": 1.5,
        "velocidad_caminata_m_s": 1.2,
    }


def config_aco_prueba(**overrides: Any) -> dict[str, Any]:
    """Config de ACO para pruebas: pocas hormigas/iteraciones, suficientes para este grafo diminuto."""
    base = {
        "n_hormigas": 20,
        "n_iteraciones": 30,
        "alfa": 1.0,
        "beta": 2.0,
        "rho": 0.3,
        "Q": 1.0,
        "tau_inicial": 1.0,
        "tau_min": 0.01,
        "tau_max": 10.0,
        "paciencia_estancamiento": 15,
        "semilla": 42,
        "intervalo_snapshot_feromona": 5,
        "max_pasos_factor": 4,
    }
    base.update(overrides)
    return base
