"""Dibuja el grafo de evacuacion provisional (bloques G y H) en coordenadas locales.

Lee data/campus_graph.json y genera, con matplotlib:
- data/maps/grafo_provisional.png: vista general (exterior + interior, en x_m/y_m).
- data/maps/planta_{bloque}_piso{N}.png: una vista por cada piso de G y de H.

Todas las figuras llevan la marca "PROVISIONAL" porque el grafo contiene
supuestos (ver data/config_modelo.json y data/pendientes.md).

Uso:
    python scripts/plot_graph.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "scripts"))

from validate_graph import cargar_json  # noqa: E402

GRAFO_PATH = RAIZ_PROYECTO / "data" / "campus_graph.json"
SALIDA_DIR = RAIZ_PROYECTO / "data" / "maps"

COLOR_POR_CONFIDENCE = {
    "verificado_en_campo": "#2e7d32",  # verde
    "medido_en_maps": "#ef6c00",  # naranja
    "documento_oficial": "#1565c0",  # azul (no esperado en este grafo, por si acaso)
    "blog_no_oficial": "#6a1b9a",  # morado (no esperado en este grafo, por si acaso)
    "supuesto": "#c62828",  # rojo
}
COLOR_DEFECTO = "#757575"


def color_de(confidence: str) -> str:
    """Devuelve el color asociado a un nivel de confidence."""
    return COLOR_POR_CONFIDENCE.get(confidence, COLOR_DEFECTO)


def indexar_nodos(nodos: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Indexa los nodos por id para busqueda rapida."""
    return {n["id"]: n for n in nodos}


def marcar_provisional(ax: plt.Axes) -> None:
    """Agrega la marca de agua 'PROVISIONAL' a un eje."""
    ax.text(
        0.5,
        0.5,
        "PROVISIONAL",
        transform=ax.transAxes,
        fontsize=40,
        color="gray",
        alpha=0.15,
        ha="center",
        va="center",
        rotation=30,
        zorder=0,
    )


def dibujar_leyenda(ax: plt.Axes) -> None:
    """Dibuja la leyenda comun de confidence, tipo de arista y punto de encuentro."""
    elementos = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["verificado_en_campo"], markersize=9, label="confidence: verificado_en_campo"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["medido_en_maps"], markersize=9, label="confidence: medido_en_maps"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["supuesto"], markersize=9, label="confidence: supuesto"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="black", markeredgecolor="black", markersize=14, label="punto de encuentro (PE)"),
        Line2D([0], [0], color="black", linestyle="-", label="arista no techada"),
        Line2D([0], [0], color="black", linestyle="--", label="arista techada"),
    ]
    ax.legend(handles=elementos, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, framealpha=0.9)


def dibujar_aristas(ax: plt.Axes, aristas: list[dict[str, Any]], nodos_por_id: dict[str, dict[str, Any]]) -> None:
    """Dibuja las aristas del grafo como lineas entre nodos, con estilo segun techado."""
    for a in aristas:
        n1 = nodos_por_id.get(a["desde"])
        n2 = nodos_por_id.get(a["hasta"])
        if n1 is None or n2 is None:
            continue
        if n1["x_m"] is None or n2["x_m"] is None:
            continue
        estilo = "--" if a.get("techado") else "-"
        ax.plot(
            [n1["x_m"], n2["x_m"]],
            [n1["y_m"], n2["y_m"]],
            linestyle=estilo,
            color="#9e9e9e",
            linewidth=0.8,
            zorder=1,
        )


def dibujar_nodos(ax: plt.Axes, nodos: list[dict[str, Any]]) -> None:
    """Dibuja los nodos del grafo, coloreados por confidence y con marcador especial para PE."""
    for n in nodos:
        if n["x_m"] is None or n["y_m"] is None:
            continue
        color = color_de(n["confidence"])
        if n["tipo"] == "punto_encuentro":
            ax.scatter(n["x_m"], n["y_m"], marker="*", s=220, color=color, edgecolor="black", zorder=3)
            ax.annotate(n["nombre"], (n["x_m"], n["y_m"]), fontsize=7, xytext=(4, 4), textcoords="offset points", zorder=4)
        elif n["tipo"] == "salida":
            ax.scatter(n["x_m"], n["y_m"], marker="s", s=90, color=color, edgecolor="black", zorder=3)
            ax.annotate(n["id"], (n["x_m"], n["y_m"]), fontsize=7, xytext=(4, 4), textcoords="offset points", zorder=4)
        else:
            ax.scatter(n["x_m"], n["y_m"], marker="o", s=18, color=color, zorder=2)


def graficar_vista_general(grafo: dict[str, Any]) -> Path:
    """Genera la vista general del grafo (exterior + interior) en x_m/y_m."""
    nodos_por_id = indexar_nodos(grafo["nodos"])

    fig, ax = plt.subplots(figsize=(12, 10))
    marcar_provisional(ax)
    dibujar_aristas(ax, grafo["aristas"], nodos_por_id)
    dibujar_nodos(ax, grafo["nodos"])
    dibujar_leyenda(ax)

    ax.set_title("Grafo de evacuacion - bloques G y H (Fase 1, PROVISIONAL)\nOrigen: SALIDA-A")
    ax.set_xlabel("x_m (metros, local)")
    ax.set_ylabel("y_m (metros, local)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.3, alpha=0.4)

    ruta_salida = SALIDA_DIR / "grafo_provisional.png"
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def graficar_piso(grafo: dict[str, Any], bloque: str, piso: int) -> Path:
    """Genera la vista de un piso de un bloque (aulas, pasillo, gradas)."""
    nodos_piso = [n for n in grafo["nodos"] if n["bloque"] == bloque and n["piso"] == piso]
    ids_piso = {n["id"] for n in nodos_piso}

    if piso == 1:
        nodos_piso = nodos_piso + [n for n in grafo["nodos"] if n["tipo"] == "salida" and n["bloque"] == bloque]
        ids_piso = {n["id"] for n in nodos_piso}

    nodos_por_id = indexar_nodos(nodos_piso)
    aristas_piso = [
        a for a in grafo["aristas"]
        if a["desde"] in ids_piso and a["hasta"] in ids_piso
    ]

    fig, ax = plt.subplots(figsize=(9, 7))
    marcar_provisional(ax)
    dibujar_aristas(ax, aristas_piso, nodos_por_id)

    for n in nodos_piso:
        if n["x_m"] is None or n["y_m"] is None:
            continue
        color = color_de(n["confidence"])
        marcador = {"aula": "o", "pasillo": "s", "gradas": "^", "salida": "D"}.get(n["tipo"], "o")
        tamano = {"aula": 60, "pasillo": 40, "gradas": 80, "salida": 110}.get(n["tipo"], 40)
        ax.scatter(n["x_m"], n["y_m"], marker=marcador, s=tamano, color=color, edgecolor="black", linewidth=0.5, zorder=3)
        etiqueta = n["id"].split("-")[-1]
        ax.annotate(etiqueta, (n["x_m"], n["y_m"]), fontsize=7, xytext=(3, 3), textcoords="offset points", zorder=4)

    elementos = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["supuesto"], markeredgecolor="black", markersize=9, label="aula"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["supuesto"], markeredgecolor="black", markersize=9, label="pasillo"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["supuesto"], markeredgecolor="black", markersize=9, label="gradas"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=COLOR_POR_CONFIDENCE["medido_en_maps"], markeredgecolor="black", markersize=9, label="salida"),
    ]
    ax.legend(handles=elementos, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, framealpha=0.9)

    ax.set_title(f"Bloque {bloque}, piso {piso} (Fase 1, PROVISIONAL)\nLayout esquematico, no georreferenciado")
    ax.set_xlabel("x_m (esquematico)")
    ax.set_ylabel("y_m (esquematico)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.3, alpha=0.4)

    ruta_salida = SALIDA_DIR / f"planta_{bloque}_piso{piso}.png"
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def main() -> int:
    """Punto de entrada del script."""
    grafo = cargar_json(GRAFO_PATH)

    rutas_generadas = [graficar_vista_general(grafo)]

    pisos_h = sorted({n["piso"] for n in grafo["nodos"] if n["bloque"] == "H" and n["piso"] is not None})
    pisos_g = sorted({n["piso"] for n in grafo["nodos"] if n["bloque"] == "G" and n["piso"] is not None})

    for piso in pisos_h:
        rutas_generadas.append(graficar_piso(grafo, "H", piso))
    for piso in pisos_g:
        rutas_generadas.append(graficar_piso(grafo, "G", piso))

    print(f"Imagenes generadas ({len(rutas_generadas)}):")
    for ruta in rutas_generadas:
        print(f"  {ruta}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
