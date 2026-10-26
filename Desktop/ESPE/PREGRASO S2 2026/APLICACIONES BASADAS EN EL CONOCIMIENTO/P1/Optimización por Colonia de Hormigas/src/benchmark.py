"""Benchmark de Dijkstra vs ACO sobre varios origenes/escenarios (usado por app/app.py, pestana 3).

Vive en src/ (no en app/) para que sea importable y probable con pytest sin
necesidad de correr Streamlit, y para que la app no duplique esta logica.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from aco import ejecutar_aco
from dijkstra import buscar_ruta
from grafo import Grafo, aplicar_congestion

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RESULTS_DIR = RAIZ_PROYECTO / "results"


@dataclass
class Escenario:
    """Un escenario de bloqueo/congestion para el benchmark o la app."""

    nombre: str
    aristas_bloqueadas: frozenset[str]
    congestion: dict[str, float]


def ejecutar_benchmark(
    grafo: Grafo,
    origenes: list[str],
    escenarios: list[Escenario],
    config_modelo: dict[str, Any],
    config_aco: dict[str, Any],
    n_corridas: int,
    guardar_csv: bool = True,
) -> tuple[pd.DataFrame, Path | None]:
    """Corre Dijkstra (1 vez) y ACO (n_corridas veces, semillas 0..n_corridas-1)
    para cada combinacion (origen, escenario). Devuelve (df_corridas_individuales, ruta_csv).

    df_corridas_individuales tiene una fila por corrida de ACO, con columnas:
    origen, escenario, semilla, tiene_ruta, costo, costo_dijkstra, brecha_pct,
    tiempo_ms, iteracion_convergencia, tiempo_dijkstra_ms, nodos_expandidos_dijkstra.
    """
    filas = []

    for escenario in escenarios:
        for origen in origenes:
            resultado_dijkstra = buscar_ruta(
                grafo, origen, config_modelo, aristas_bloqueadas=escenario.aristas_bloqueadas
            )
            grafo_escenario = aplicar_congestion(grafo, escenario.congestion)

            for semilla in range(n_corridas):
                resultado_aco = ejecutar_aco(
                    grafo_escenario,
                    origen,
                    config_modelo,
                    config_aco,
                    aristas_bloqueadas=escenario.aristas_bloqueadas,
                    semilla=semilla,
                )

                brecha_pct = None
                if resultado_aco.tiene_ruta and resultado_dijkstra.tiene_ruta:
                    brecha_pct = (
                        (resultado_aco.mejor_costo - resultado_dijkstra.costo) / resultado_dijkstra.costo * 100
                    )

                filas.append(
                    {
                        "origen": origen,
                        "escenario": escenario.nombre,
                        "semilla": semilla,
                        "tiene_ruta": resultado_aco.tiene_ruta,
                        "costo": resultado_aco.mejor_costo,
                        "costo_dijkstra": resultado_dijkstra.costo,
                        "brecha_pct": brecha_pct,
                        "tiempo_ms": resultado_aco.tiempo_s * 1000,
                        "iteracion_convergencia": resultado_aco.iteracion_mejor_solucion,
                        "nodos_expandidos_dijkstra": resultado_dijkstra.nodos_expandidos,
                    }
                )

    df = pd.DataFrame(filas)

    ruta_csv = None
    if guardar_csv:
        RESULTS_DIR.mkdir(exist_ok=True)
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_csv = RESULTS_DIR / f"benchmark_{marca_tiempo}.csv"
        df.to_csv(ruta_csv, index=False)

    return df, ruta_csv


def resumir_benchmark(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega df_corridas_individuales por (origen, escenario): media/desv/min/max de costo,
    brecha promedio, tiempo promedio, tasa de exito e iteracion de convergencia promedio.
    """
    filas = []
    for (origen, escenario), grupo in df.groupby(["origen", "escenario"]):
        exitosas = grupo[grupo["tiene_ruta"]]
        filas.append(
            {
                "origen": origen,
                "escenario": escenario,
                "n_corridas": len(grupo),
                "tasa_exito_pct": len(exitosas) / len(grupo) * 100,
                "costo_medio": exitosas["costo"].mean() if not exitosas.empty else None,
                "costo_desv": exitosas["costo"].std() if len(exitosas) > 1 else None,
                "costo_min": exitosas["costo"].min() if not exitosas.empty else None,
                "costo_max": exitosas["costo"].max() if not exitosas.empty else None,
                "brecha_pct_media": exitosas["brecha_pct"].mean() if not exitosas.empty else None,
                "tiempo_ms_medio": grupo["tiempo_ms"].mean(),
                "iteracion_convergencia_media": exitosas["iteracion_convergencia"].mean()
                if not exitosas.empty
                else None,
            }
        )
    return pd.DataFrame(filas)


def barrido_sensibilidad(
    grafo: Grafo,
    origen: str,
    escenario: Escenario,
    config_modelo: dict[str, Any],
    config_aco: dict[str, Any],
    nombre_parametro: str,
    valores: list[float],
    n_corridas: int,
) -> pd.DataFrame:
    """Corre ACO variando UN parametro (alfa, beta, rho o n_hormigas) sobre una lista de valores,
    para un (origen, escenario) fijo. Devuelve una fila resumen por valor del parametro.
    """
    grafo_escenario = aplicar_congestion(grafo, escenario.congestion)
    filas = []

    for valor in valores:
        config_variante = dict(config_aco)
        config_variante[nombre_parametro] = valor

        resultado_dijkstra = buscar_ruta(
            grafo, origen, config_modelo, aristas_bloqueadas=escenario.aristas_bloqueadas
        )

        costos = []
        tiempos_ms = []
        exitos = 0
        for semilla in range(n_corridas):
            resultado = ejecutar_aco(
                grafo_escenario,
                origen,
                config_modelo,
                config_variante,
                aristas_bloqueadas=escenario.aristas_bloqueadas,
                semilla=semilla,
            )
            tiempos_ms.append(resultado.tiempo_s * 1000)
            if resultado.tiene_ruta:
                exitos += 1
                costos.append(resultado.mejor_costo)

        brecha_media = None
        if costos and resultado_dijkstra.tiene_ruta:
            brecha_media = sum(
                (c - resultado_dijkstra.costo) / resultado_dijkstra.costo * 100 for c in costos
            ) / len(costos)

        filas.append(
            {
                nombre_parametro: valor,
                "tasa_exito_pct": exitos / n_corridas * 100,
                "brecha_pct_media": brecha_media,
                "tiempo_ms_medio": sum(tiempos_ms) / len(tiempos_ms),
            }
        )

    return pd.DataFrame(filas)
