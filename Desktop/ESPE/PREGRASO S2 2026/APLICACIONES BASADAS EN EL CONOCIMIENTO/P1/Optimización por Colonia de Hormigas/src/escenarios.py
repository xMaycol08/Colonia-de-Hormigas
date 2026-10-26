"""Escenarios de bloqueo y congestion, compartidos por scripts/correr_experimentos.py y app/app.py.

Los 6 escenarios oficiales traducen un nombre a aristas bloqueadas y/o
congestion sobre el grafo. El factor de congestion sale de
data/config_modelo.json (factor_congestion_demo).
"""

from __future__ import annotations

from dataclasses import dataclass

from grafo import Grafo

ID_ARISTA_GRADAS_SUR_SALIDA_A = "GRADAS-SUR-PB-SALIDA-A"
ID_ARISTA_GRADAS_NORTE_SALIDA_B = "GRADAS-NORTE-PB-SALIDA-B"

ESCENARIOS_DISPONIBLES = [
    "Normal",
    "Gradas Norte bloqueadas",
    "Gradas Sur bloqueadas",
    "Salida A bloqueada",
    "Salida B bloqueada",
    "Congestion en una salida",
]


ETIQUETA_ESCENARIO = {
    "Normal": "Normal",
    "Gradas Norte bloqueadas": "Gradas norte bloqueadas",
    "Gradas Sur bloqueadas": "Gradas sur bloqueadas",
    "Salida A bloqueada": "Salida A bloqueada",
    "Salida B bloqueada": "Salida B bloqueada",
    "Congestion en una salida": "Congestión en una salida",
}

ETIQUETA_VARIANTE = {
    "Dijkstra": "Dijkstra",
    "ACO clasico": "ACO clásico",
    "ACO guiado": "ACO guiado",
}


@dataclass
class Escenario:
    """Un escenario de bloqueo/congestion para el benchmark o la app."""

    nombre: str
    aristas_bloqueadas: frozenset[str]
    congestion: dict[str, float]


def construir_escenario(nombre: str, grafo: Grafo, config_modelo: dict) -> Escenario:
    """Traduce el nombre de un escenario a aristas bloqueadas / congestion."""
    if nombre == "Gradas Norte bloqueadas":
        bloqueadas = frozenset(aid for aid in grafo.aristas_por_id if aid.startswith("GRADAS-NORTE-"))
        return Escenario(nombre, bloqueadas, {})
    if nombre == "Gradas Sur bloqueadas":
        bloqueadas = frozenset(aid for aid in grafo.aristas_por_id if aid.startswith("GRADAS-SUR-"))
        return Escenario(nombre, bloqueadas, {})
    if nombre == "Salida A bloqueada":
        return Escenario(nombre, frozenset({ID_ARISTA_GRADAS_SUR_SALIDA_A}), {})
    if nombre == "Salida B bloqueada":
        return Escenario(nombre, frozenset({ID_ARISTA_GRADAS_NORTE_SALIDA_B}), {})
    if nombre == "Congestion en una salida":
        return Escenario(nombre, frozenset(), {ID_ARISTA_GRADAS_SUR_SALIDA_A: config_modelo["factor_congestion_demo"]})
    return Escenario("Normal", frozenset(), {})
