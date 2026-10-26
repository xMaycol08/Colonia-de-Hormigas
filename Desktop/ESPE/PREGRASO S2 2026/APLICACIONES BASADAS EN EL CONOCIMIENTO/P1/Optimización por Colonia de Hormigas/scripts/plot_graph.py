"""Dibuja el grafo de evacuacion provisional (Fase 1-bis) para validarlo.

Lee data/campus_graph.json y genera, con matplotlib:
- data/maps/validacion_modelo/grafo_sobre_plano_real.png: el esqueleto del
  modelo (pasillos, accesos a gradas, salidas, exterior) superpuesto sobre
  data/maps/plano_base_GH_anotado.jpeg, usando data/calibracion_plano.json.
- data/maps/validacion_modelo/planta_nivelX.png: un plano esquematico por
  nivel (PB, 1, 2, 3, 4) con las aulas rotuladas con sus nombres reales.

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
from PIL import Image

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "scripts"))

from validate_graph import cargar_json  # noqa: E402

GRAFO_PATH = RAIZ_PROYECTO / "data" / "campus_graph.json"
CALIBRACION_PATH = RAIZ_PROYECTO / "data" / "calibracion_plano.json"
SALIDA_DIR = RAIZ_PROYECTO / "data" / "maps"
SALIDA_VALIDACION_DIR = SALIDA_DIR / "validacion_modelo"

COLOR_POR_CONFIDENCE = {
    "verificado_en_campo": "#2e7d32",
    "medido_en_maps": "#ef6c00",
    "documento_oficial": "#1565c0",
    "blog_no_oficial": "#6a1b9a",
    "supuesto": "#c62828",
}
COLOR_DEFECTO = "#757575"


def color_de(confidence: str) -> str:
    return COLOR_POR_CONFIDENCE.get(confidence, COLOR_DEFECTO)


def indexar_nodos(nodos: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in nodos}


def marcar_provisional(ax: plt.Axes) -> None:
    ax.text(
        0.5, 0.5, "PROVISIONAL", transform=ax.transAxes, fontsize=40, color="gray",
        alpha=0.18, ha="center", va="center", rotation=30, zorder=10,
    )


def xy_a_pixel(x_m: float, y_m: float, calibracion: dict[str, Any]) -> tuple[float, float]:
    """Convierte x_m, y_m (local, origen Salida A) a pixel sobre la imagen calibrada."""
    control_a = calibracion["puntos_de_control"]["salida_A"]
    escala = calibracion["escala_px_por_m"]
    px = control_a["pixel_x"] + x_m * escala
    py = control_a["pixel_y"] - y_m * escala
    return px, py


def graficar_sobre_plano_real(grafo: dict[str, Any], calibracion: dict[str, Any]) -> Path:
    """Superpone el esqueleto del modelo (hub de un nivel + exterior) sobre el plano anotado."""
    nodos_por_id = indexar_nodos(grafo["nodos"])

    imagen = Image.open(RAIZ_PROYECTO / calibracion["imagen"])

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.imshow(imagen)
    ax.set_xlim(0, imagen.width)
    ax.set_ylim(imagen.height, 0)
    marcar_provisional(ax)

    # Solo se dibuja el nivel PB (los nodos hub son la MISMA posicion fisica en
    # todos los niveles; dibujar los 5 niveles encimaria los puntos). Las
    # secciones de gradas se anotan como 'PB-1-2-3-4' para indicar que llegan a
    # todos los niveles.
    ids_nivel_pb = {
        n["id"] for n in grafo["nodos"]
        if n["id"].endswith("-PB") or n["tipo"] in ("salida", "via_exterior", "punto_encuentro")
        or n["id"] in ("H-PB-OFICINAS_CC", "G-PB-LAB_BIOTEC")
    }

    aristas_dibujadas = [
        a for a in grafo["aristas"]
        if a["desde"] in ids_nivel_pb and a["hasta"] in ids_nivel_pb and a["tipo"] != "gradas"
    ]

    for a in aristas_dibujadas:
        n1, n2 = nodos_por_id[a["desde"]], nodos_por_id[a["hasta"]]
        if n1["x_m"] is None or n2["x_m"] is None:
            continue
        p1 = xy_a_pixel(n1["x_m"], n1["y_m"], calibracion)
        p2 = xy_a_pixel(n2["x_m"], n2["y_m"], calibracion)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#1565c0", linewidth=2.2, zorder=3)

    for nid in ids_nivel_pb:
        n = nodos_por_id[nid]
        if n["x_m"] is None:
            continue
        px, py = xy_a_pixel(n["x_m"], n["y_m"], calibracion)
        if n["tipo"] == "salida":
            ax.scatter(px, py, marker="x", s=260, color="#2e7d32", linewidth=4, zorder=6)
            ax.annotate(n["id"], (px, py), fontsize=9, color="white", weight="bold",
                        xytext=(8, 8), textcoords="offset points", zorder=7)
        elif n["tipo"] == "gradas":
            etiqueta = ("Gradas norte" if "NORTE" in n["id"] else "Gradas sur") + " (PB-1-2-3-4)"
            ax.scatter(px, py, marker="^", s=160, color="#f9a825", edgecolor="black", zorder=6)
            ax.annotate(etiqueta, (px, py), fontsize=7, color="white", weight="bold",
                        xytext=(8, -12), textcoords="offset points", zorder=7)
        elif n["tipo"] == "punto_encuentro":
            continue  # los PE quedan fuera del recorte de esta imagen
        elif n["tipo"] == "via_exterior":
            ax.scatter(px, py, marker="o", s=40, color="#9e9e9e", zorder=5)
        elif n["tipo"] == "pasillo":
            ax.scatter(px, py, marker="s", s=90, color="#1565c0", edgecolor="white", zorder=6)
        else:
            etiqueta_corta = n["id"].replace("-PB-", " ").replace("_", " ")
            ax.scatter(px, py, marker="D", s=70, color="#6a1b9a", edgecolor="white", zorder=6)
            ax.annotate(etiqueta_corta, (px, py), fontsize=6.5, color="white",
                        xytext=(6, -8), textcoords="offset points", zorder=7)

    elementos = [
        Line2D([0], [0], marker="x", color="w", markerfacecolor="#2e7d32", markeredgecolor="#2e7d32", markersize=12, label="Salida"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#f9a825", markeredgecolor="black", markersize=10, label="Acceso a seccion de gradas"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#1565c0", markeredgecolor="white", markersize=9, label="Pasillo (H, G o central)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#6a1b9a", markeredgecolor="white", markersize=8, label="Origen PB (oficinas/laboratorio)"),
        Line2D([0], [0], color="#1565c0", linewidth=2, label="Arista del modelo"),
    ]
    ax.legend(handles=elementos, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, framealpha=0.9)
    ax.set_title("Esqueleto del modelo sobre el plano real (PROVISIONAL)\nAccesos a gradas validos para los 5 niveles (PB,1,2,3,4)")
    ax.axis("off")

    SALIDA_VALIDACION_DIR.mkdir(parents=True, exist_ok=True)
    ruta_salida = SALIDA_VALIDACION_DIR / "grafo_sobre_plano_real.png"
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def graficar_nivel(grafo: dict[str, Any], nivel: str) -> Path:
    """Genera la vista esquematica de un nivel (PB o 1-4), con aulas rotuladas por su nombre real."""
    piso_num = 0 if nivel == "PB" else int(nivel)
    nodos_nivel = [
        n for n in grafo["nodos"]
        if n["piso"] == piso_num and n["bloque"] in ("H", "G", "compartido")
    ]
    ids_nivel = {n["id"] for n in nodos_nivel}
    nodos_por_id = indexar_nodos(nodos_nivel)
    aristas_nivel = [a for a in grafo["aristas"] if a["desde"] in ids_nivel and a["hasta"] in ids_nivel]

    fig, ax = plt.subplots(figsize=(10, 7))
    marcar_provisional(ax)

    for a in aristas_nivel:
        n1, n2 = nodos_por_id[a["desde"]], nodos_por_id[a["hasta"]]
        if n1["x_m"] is None or n2["x_m"] is None:
            continue
        estilo = "--" if a.get("techado") else "-"
        ax.plot([n1["x_m"], n2["x_m"]], [n1["y_m"], n2["y_m"]], linestyle=estilo, color="#9e9e9e", linewidth=0.9, zorder=1)

    marcador_por_tipo = {"aula": "o", "pasillo": "s", "gradas": "^"}
    color_por_tipo = {"aula": "#1565c0", "pasillo": "#6a1b9a", "gradas": "#f9a825"}
    tamano_por_tipo = {"aula": 70, "pasillo": 50, "gradas": 110}

    for n in nodos_nivel:
        if n["x_m"] is None:
            continue
        tipo = n["tipo"]
        ax.scatter(n["x_m"], n["y_m"], marker=marcador_por_tipo.get(tipo, "o"), s=tamano_por_tipo.get(tipo, 40),
                   color=color_por_tipo.get(tipo, "#757575"), edgecolor="black", linewidth=0.5, zorder=3)
        etiqueta = n["id"] if tipo == "aula" else n["id"].split("-")[0][:4]
        ax.annotate(etiqueta, (n["x_m"], n["y_m"]), fontsize=7, xytext=(4, 4), textcoords="offset points", zorder=4)

    elementos = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=color_por_tipo["aula"], markeredgecolor="black", markersize=9, label="Aula"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=color_por_tipo["pasillo"], markeredgecolor="black", markersize=9, label="Pasillo"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor=color_por_tipo["gradas"], markeredgecolor="black", markersize=10, label="Acceso a gradas"),
    ]
    ax.legend(handles=elementos, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, framealpha=0.9)
    ax.set_title(f"Nivel {nivel} (PROVISIONAL)\nLayout esquematico, no georreferenciado")
    ax.set_xlabel("x_m (esquematico)")
    ax.set_ylabel("y_m (esquematico)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.3, alpha=0.4)

    SALIDA_VALIDACION_DIR.mkdir(parents=True, exist_ok=True)
    ruta_salida = SALIDA_VALIDACION_DIR / f"planta_nivel{nivel}.png"
    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def main() -> int:
    grafo = cargar_json(GRAFO_PATH)
    calibracion = cargar_json(CALIBRACION_PATH)

    rutas = [graficar_sobre_plano_real(grafo, calibracion)]

    niveles = sorted({str(n["piso"]) if n["piso"] != 0 else "PB" for n in grafo["nodos"] if n["bloque"] in ("H", "G", "compartido")},
                      key=lambda v: -1 if v == "PB" else int(v))
    for nivel in niveles:
        rutas.append(graficar_nivel(grafo, nivel))

    print(f"Imagenes generadas ({len(rutas)}):")
    for ruta in rutas:
        print(f"  {ruta}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
