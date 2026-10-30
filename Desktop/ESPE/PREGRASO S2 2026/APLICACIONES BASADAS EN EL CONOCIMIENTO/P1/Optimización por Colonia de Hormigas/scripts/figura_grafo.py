"""Figura del grafo real: esquema por niveles (75 nodos, 79 aristas) y posicion sobre el plano calibrado.

Uso:
    python scripts/figura_grafo.py

Escribe results/figuras/fig0_grafo_real.png (y fig0_grafo_niveles.png, solo el esquema).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import CONFIG_MODELO_PATH, cargar_configuracion, cargar_grafo  # noqa: E402
from plano import dibujar_esquema, dibujar_nodos_planta, fondo_plano, leyenda_tipos, posiciones_planta  # noqa: E402

SALIDA = RAIZ_PROYECTO / "results" / "figuras"


def main() -> None:
    grafo = cargar_grafo()
    cm = cargar_configuracion(CONFIG_MODELO_PATH)
    SALIDA.mkdir(parents=True, exist_ok=True)
    titulo = f"Grafo del complejo G y H: {len(grafo.nodos_por_id)} nodos y {len(grafo.aristas_por_id)} aristas"

    fig, ax = plt.subplots(figsize=(7.5, 8))
    dibujar_esquema(ax, grafo, titulo=titulo)
    leyenda_tipos(ax, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3)
    fig.savefig(SALIDA / "fig0_grafo_niveles.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.8), gridspec_kw={"width_ratios": [1, 1.05]})
    dibujar_esquema(ax1, grafo, titulo="Esquema por niveles (cada piso, sus aulas, pasillos y gradas)")
    leyenda_tipos(ax1, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3)
    pos = posiciones_planta(grafo, cm["altura_piso_m"])
    fondo_plano(ax2)
    ax2.grid(False)
    for arista in grafo.aristas_por_id.values():
        a, b = arista["desde"], arista["hasta"]
        if a in pos and b in pos:
            ax2.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color="#14324b", linewidth=0.8, alpha=0.7, zorder=2)
    dibujar_nodos_planta(ax2, grafo, pos, tipos=("aula", "pasillo", "gradas", "salida", "punto_encuentro"), etiquetas=False)
    ax2.set_title("Los mismos nodos sobre el plano calibrado (vista en planta, en metros)", fontsize=10)
    fig.suptitle(titulo, fontsize=13)
    fig.tight_layout()
    fig.savefig(SALIDA / "fig0_grafo_real.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
