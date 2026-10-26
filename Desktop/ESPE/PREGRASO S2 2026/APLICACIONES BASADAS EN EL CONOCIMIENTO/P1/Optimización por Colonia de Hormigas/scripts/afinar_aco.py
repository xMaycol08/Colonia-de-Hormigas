"""Malla de afinacion de parametros de ACO (Fase 2B, tarea 4).

Prueba beta en {1.0, 2.0, 3.0}, rho en {0.1, 0.3, 0.5} y n_hormigas en
{20, 30, 50} (27 combinaciones), sobre los 10 origenes representativos de
data/config_modelo.json, con 10 corridas (semillas 0..9) por combinacion.

Elige la combinacion con mayor tasa de exito; entre empates, menor brecha
promedio frente a Dijkstra; entre empates, menor tiempo promedio.

Escribe la tabla completa en Markdown a stdout (se copia a mano a
docs/decisiones_fase2.md) y deja el detalle en
results/malla_aco_<fecha_hora>.csv.

Uso:
    python scripts/afinar_aco.py
"""

from __future__ import annotations

import csv
import itertools
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from aco import ejecutar_aco  # noqa: E402

RESULTS_DIR = RAIZ_PROYECTO / "results"

VALORES_BETA = [1.0, 2.0, 3.0]
VALORES_RHO = [0.1, 0.3, 0.5]
VALORES_N_HORMIGAS = [20, 30, 50]
N_CORRIDAS_POR_ORIGEN = 10


def main() -> int:
    """Punto de entrada del script."""
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco_base = cargar_configuracion(CONFIG_ACO_PATH)

    origenes = [o["id_nodo"] for o in config_modelo["origenes_representativos"]]
    costos_dijkstra = {o: buscar_ruta(grafo, o, config_modelo).costo for o in origenes}

    RESULTS_DIR.mkdir(exist_ok=True)
    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_csv = RESULTS_DIR / f"malla_aco_{marca_tiempo}.csv"

    filas_csv = []
    resumen_combinaciones = []

    combinaciones = list(itertools.product(VALORES_BETA, VALORES_RHO, VALORES_N_HORMIGAS))
    inicio_total = time.perf_counter()

    for i, (beta, rho, n_hormigas) in enumerate(combinaciones, start=1):
        config_aco = dict(config_aco_base)
        config_aco["beta"] = beta
        config_aco["rho"] = rho
        config_aco["n_hormigas"] = n_hormigas

        exitos = 0
        total_corridas = 0
        brechas = []
        tiempos_ms = []

        for origen in origenes:
            costo_dijkstra = costos_dijkstra[origen]
            for semilla in range(N_CORRIDAS_POR_ORIGEN):
                resultado = ejecutar_aco(grafo, origen, config_modelo, config_aco, semilla=semilla)
                total_corridas += 1
                tiempos_ms.append(resultado.tiempo_s * 1000)
                if resultado.tiene_ruta:
                    exitos += 1
                    brecha = (resultado.mejor_costo - costo_dijkstra) / costo_dijkstra * 100
                    brechas.append(brecha)

                filas_csv.append(
                    {
                        "beta": beta,
                        "rho": rho,
                        "n_hormigas": n_hormigas,
                        "origen": origen,
                        "semilla": semilla,
                        "tiene_ruta": resultado.tiene_ruta,
                        "costo": resultado.mejor_costo,
                        "costo_dijkstra": costo_dijkstra,
                        "tiempo_ms": resultado.tiempo_s * 1000,
                    }
                )

        tasa_exito = exitos / total_corridas * 100
        brecha_promedio = sum(brechas) / len(brechas) if brechas else float("inf")
        tiempo_promedio_ms = sum(tiempos_ms) / len(tiempos_ms)

        resumen_combinaciones.append(
            {
                "beta": beta,
                "rho": rho,
                "n_hormigas": n_hormigas,
                "tasa_exito_pct": tasa_exito,
                "brecha_promedio_pct": brecha_promedio,
                "tiempo_promedio_ms": tiempo_promedio_ms,
            }
        )

        print(
            f"[{i}/{len(combinaciones)}] beta={beta} rho={rho} n_hormigas={n_hormigas} "
            f"-> exito={tasa_exito:.1f}% brecha={brecha_promedio:.2f}% tiempo={tiempo_promedio_ms:.1f}ms",
            file=sys.stderr,
        )

    tiempo_total_s = time.perf_counter() - inicio_total

    with ruta_csv.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas_csv[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas_csv)

    resumen_ordenado = sorted(
        resumen_combinaciones,
        key=lambda r: (-r["tasa_exito_pct"], r["brecha_promedio_pct"], r["tiempo_promedio_ms"]),
    )
    mejor = resumen_ordenado[0]

    print(f"\nTiempo total de la malla: {tiempo_total_s:.1f} s")
    print(f"Detalle completo (2700 corridas) guardado en: {ruta_csv}\n")

    print("| beta | rho | n_hormigas | tasa_exito % | brecha_promedio % | tiempo_promedio ms |")
    print("|---|---|---|---|---|---|")
    for r in resumen_ordenado:
        print(
            f"| {r['beta']} | {r['rho']} | {r['n_hormigas']} | {r['tasa_exito_pct']:.1f} "
            f"| {r['brecha_promedio_pct']:.2f} | {r['tiempo_promedio_ms']:.1f} |"
        )

    print(
        f"\nCombinacion elegida: beta={mejor['beta']}, rho={mejor['rho']}, "
        f"n_hormigas={mejor['n_hormigas']} "
        f"(exito={mejor['tasa_exito_pct']:.1f}%, brecha={mejor['brecha_promedio_pct']:.2f}%, "
        f"tiempo={mejor['tiempo_promedio_ms']:.1f} ms)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
