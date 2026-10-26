"""Modelo de evacuacion completa (compartido por scripts/correr_experimentos.py y app/app.py).

Es el mismo modelo simplificado de src/metricas.py, extendido a todos los
origenes a la vez. Sin colas ni capacidad de salidas (limitacion declarada):

    primera persona de un origen = tiempo_reaccion_s + tiempo de recorrido de su ruta
    la persona k (0, 1, ...) de ese origen llega tiempo_entre_personas_s * k despues

Las metricas oficiales de la guia de simulacros son el tiempo hasta la
PRIMERA y hasta la ULTIMA persona en llegar a un punto de encuentro.
Todos los numeros salen de data/config_modelo.json.
"""

from __future__ import annotations

import bisect
import math
from typing import Any

from grafo import Grafo
from metricas import tiempo_recorrido_ruta


def salida_de(grafo: Grafo, camino: list[str] | None) -> str | None:
    """Primer nodo de tipo 'salida' del camino (o None)."""
    for nodo in camino or []:
        if grafo.nodos_por_id[nodo]["tipo"] == "salida":
            return nodo
    return None


def simular_evacuacion(grafo_escenario: Grafo, rutas: dict[str, list[str] | None], config_modelo: dict[str, Any]) -> dict[str, Any]:
    """Calcula las metricas de evacuacion dado un camino por origen (None = sin ruta)."""
    pob = config_modelo["poblacion_por_origen"]
    t_reaccion = config_modelo["tiempo_reaccion_s"]
    dt = config_modelo["tiempo_entre_personas_s"]
    pes = sorted(grafo_escenario.ids_puntos_encuentro)

    llegadas: list[float] = []
    por_salida: dict[str, int] = {}
    por_pe = {pe: 0 for pe in pes}
    origenes_salida: dict[str, int] = {}
    origenes_pe = {pe: 0 for pe in pes}
    sin_ruta = 0
    origenes_con_ruta = 0
    for origen, poblacion in pob.items():
        camino = rutas.get(origen)
        if not camino:
            sin_ruta += poblacion
            continue
        origenes_con_ruta += 1
        t0 = t_reaccion + tiempo_recorrido_ruta(grafo_escenario, camino, config_modelo)
        llegadas.extend(t0 + k * dt for k in range(poblacion))
        salida = salida_de(grafo_escenario, camino)
        por_salida[salida] = por_salida.get(salida, 0) + poblacion
        origenes_salida[salida] = origenes_salida.get(salida, 0) + 1
        por_pe[camino[-1]] += poblacion
        origenes_pe[camino[-1]] += 1
    llegadas.sort()
    return {
        "llegadas": llegadas,
        "primera_s": llegadas[0] if llegadas else None,
        "ultima_s": llegadas[-1] if llegadas else None,
        "poblacion_total": sum(pob.values()),
        "sin_ruta": sin_ruta,
        "por_salida": por_salida,
        "por_pe": por_pe,
        "origenes_total": len(pob),
        "origenes_con_ruta": origenes_con_ruta,
        "origenes_salida": origenes_salida,
        "origenes_pe": origenes_pe,
    }


def curva_acumulada(llegadas: list[float]) -> list[tuple[int, int]]:
    """[(t, personas llegadas hasta t)] con paso de 1 s, desde 0 hasta la ultima llegada."""
    if not llegadas:
        return []
    return [(t, bisect.bisect_right(llegadas, t)) for t in range(0, int(math.ceil(llegadas[-1])) + 1)]
