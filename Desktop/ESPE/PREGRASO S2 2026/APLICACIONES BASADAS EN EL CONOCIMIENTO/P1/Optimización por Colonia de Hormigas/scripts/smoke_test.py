"""Verificacion rapida (smoke test) de Dijkstra y ACO sobre el grafo real.

NO es el experimento final de Fase 3: solo corre, para 2 origenes
representativos, Dijkstra una vez y ACO 5 veces cada uno, y muestra una
tabla pequena (costo, brecha %, tiempo en ms, iteracion de convergencia).

Todos los parametros (n_hormigas, n_iteraciones, etc.) se leen de
data/config_aco.json, tal como quedaron fijados en Fase 2; este script no
los modifica.

Uso:
    python scripts/smoke_test.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from aco import ejecutar_aco  # noqa: E402

N_REPETICIONES_ACO = 5
N_ORIGENES_SMOKE_TEST = 2


def formatear_costo(valor: float) -> str:
    """Formatea un costo, mostrando 'sin ruta' si es infinito."""
    return "sin ruta" if valor == float("inf") else f"{valor:.2f}"


def formatear_brecha(costo_aco: float, costo_dijkstra: float) -> str:
    """Formatea la brecha % de ACO frente a Dijkstra, o 'n/a' si alguno no tiene ruta."""
    if costo_aco == float("inf") or costo_dijkstra == float("inf"):
        return "n/a"
    return f"{(costo_aco - costo_dijkstra) / costo_dijkstra * 100:+.1f}%"


def main() -> int:
    """Punto de entrada del script."""
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    origenes = [o["id_nodo"] for o in config_modelo["origenes_representativos"][:N_ORIGENES_SMOKE_TEST]]

    filas = []

    for origen in origenes:
        inicio = time.perf_counter()
        resultado_dijkstra = buscar_ruta(grafo, origen, config_modelo)
        tiempo_dijkstra_ms = (time.perf_counter() - inicio) * 1000
        filas.append(
            {
                "origen": origen,
                "algoritmo": "Dijkstra",
                "repeticion": "-",
                "costo": resultado_dijkstra.costo,
                "brecha_pct": "-",
                "tiempo_ms": tiempo_dijkstra_ms,
                "iteracion_convergencia": "-",
            }
        )

        for repeticion in range(1, N_REPETICIONES_ACO + 1):
            resultado_aco = ejecutar_aco(grafo, origen, config_modelo, config_aco)
            filas.append(
                {
                    "origen": origen,
                    "algoritmo": "ACO",
                    "repeticion": repeticion,
                    "costo": resultado_aco.mejor_costo,
                    "brecha_pct": formatear_brecha(resultado_aco.mejor_costo, resultado_dijkstra.costo),
                    "tiempo_ms": resultado_aco.tiempo_s * 1000,
                    "iteracion_convergencia": (
                        resultado_aco.iteracion_mejor_solucion
                        if resultado_aco.iteracion_mejor_solucion is not None
                        else "-"
                    ),
                }
            )

    _imprimir_tabla(filas)
    return 0


def _imprimir_tabla(filas: list[dict]) -> None:
    """Imprime la tabla de resultados en formato de texto alineado."""
    encabezados = ["origen", "algoritmo", "rep.", "costo", "brecha %", "tiempo (ms)", "iter. convergencia"]
    anchos = [18, 9, 5, 10, 10, 12, 19]

    def fila_texto(valores: list[str]) -> str:
        return " | ".join(str(v).ljust(a) for v, a in zip(valores, anchos))

    print(fila_texto(encabezados))
    print("-+-".join("-" * a for a in anchos))
    for f in filas:
        print(
            fila_texto(
                [
                    f["origen"],
                    f["algoritmo"],
                    f["repeticion"],
                    formatear_costo(f["costo"]),
                    f["brecha_pct"],
                    f"{f['tiempo_ms']:.2f}",
                    f["iteracion_convergencia"],
                ]
            )
        )


if __name__ == "__main__":
    sys.exit(main())
