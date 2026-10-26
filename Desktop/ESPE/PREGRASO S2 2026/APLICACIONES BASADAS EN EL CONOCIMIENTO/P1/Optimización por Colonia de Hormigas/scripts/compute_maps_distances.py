"""Calcula distancias haversine entre puntos consecutivos de cada camino observado en Maps.

Lee data/raw/maps_observations.json, agrupa los puntos tipo 'camino' por nombre
de ruta (segun su descripcion) en el orden en que fueron registrados, y escribe
data/raw/maps_distances.csv con la distancia haversine entre cada par consecutivo.

Uso:
    python scripts/compute_maps_distances.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "scripts"))

from validate_graph import distancia_haversine_m  # noqa: E402

OBSERVACIONES_PATH = RAIZ_PROYECTO / "data" / "raw" / "maps_observations.json"
SALIDA_CSV_PATH = RAIZ_PROYECTO / "data" / "raw" / "maps_distances.csv"


def nombre_camino(observacion: dict) -> str:
    """Extrae el nombre del camino (Ruta Principal 3, Ruta Transversal 1, etc.) desde el id."""
    id_obs = observacion["id"]
    return id_obs.rsplit("_pt", 1)[0]


def agrupar_puntos_de_camino(observaciones: list[dict]) -> dict[str, list[dict]]:
    """Agrupa las observaciones tipo 'camino' por nombre de ruta, en orden de aparicion."""
    grupos: dict[str, list[dict]] = {}
    for obs in observaciones:
        if obs.get("tipo") != "camino":
            continue
        grupos.setdefault(nombre_camino(obs), []).append(obs)
    return grupos


def calcular_distancias(grupos: dict[str, list[dict]]) -> list[dict]:
    """Calcula la distancia haversine entre cada par consecutivo de puntos de cada camino."""
    filas = []
    for camino, puntos in grupos.items():
        for actual, siguiente in zip(puntos, puntos[1:]):
            distancia = distancia_haversine_m(
                actual["lat"], actual["lon"], siguiente["lat"], siguiente["lon"]
            )
            filas.append(
                {
                    "camino": camino,
                    "desde_id": actual["id"],
                    "hasta_id": siguiente["id"],
                    "distancia_m": round(distancia, 2),
                }
            )
    return filas


def escribir_csv(filas: list[dict], ruta_salida: Path) -> None:
    """Escribe las distancias calculadas en un archivo CSV."""
    with ruta_salida.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=["camino", "desde_id", "hasta_id", "distancia_m"])
        escritor.writeheader()
        escritor.writerows(filas)


def main() -> int:
    """Punto de entrada del script."""
    with OBSERVACIONES_PATH.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    grupos = agrupar_puntos_de_camino(datos["observaciones"])
    filas = calcular_distancias(grupos)
    escribir_csv(filas, SALIDA_CSV_PATH)

    print(f"Caminos procesados: {len(grupos)}")
    for camino, puntos in grupos.items():
        print(f"  {camino}: {len(puntos)} punto(s) registrado(s)")
    print(f"Distancias calculadas: {len(filas)}")
    print(f"Escrito en: {SALIDA_CSV_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
