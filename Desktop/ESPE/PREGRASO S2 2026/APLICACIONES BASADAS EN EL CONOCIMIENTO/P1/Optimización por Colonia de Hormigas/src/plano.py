"""Dibujo del grafo sobre el plano calibrado y en un esquema por niveles.

Compartido por scripts/generar_figuras.py y app/app.py.

- Plano calibrado: usa data/maps/plano_base_GH_anotado.jpeg con la calibracion
  de data/calibracion_plano.json (origen = Salida A, escala px/m). La imagen se
  recorta para quitar la barra de tareas de Windows y los controles de Google
  Maps, y se aclara para que las capas dibujadas se lean bien.
- Posicion en planta de un nodo: (x_m, y_m - altura_piso_m * piso). El grafo
  guarda y_m desplazada altura_piso_m por nivel; al quitar ese desplazamiento
  todos los niveles quedan superpuestos sobre la misma planta (supuesto del
  equipo: la distribucion de pasillos se repite en cada nivel).
- Esquema por niveles: disposicion propia para ver las feromonas de todos los
  niveles a la vez (no tiene escala).
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import numpy as np
from PIL import Image

from grafo import RAIZ_PROYECTO, Grafo, cargar_json

CALIBRACION_PATH = RAIZ_PROYECTO / "data" / "calibracion_plano.json"

# Recorte en pixeles (izquierda, arriba, derecha, abajo) de la captura: deja fuera la barra
# de tareas de Windows, la franja de derechos de Google Maps y los controles de la interfaz.
CAJA_RECORTE = (100, 0, 1420, 680)

COLORES_TIPO = {
    "aula": "#1f77b4",
    "pasillo": "#7b3fa0",
    "gradas": "#e08a00",
    "salida": "#2e7d32",
    "via_exterior": "#7f7f7f",
    "punto_encuentro": "#c62828",
}
MARCADORES_TIPO = {
    "aula": "o",
    "pasillo": "s",
    "gradas": "^",
    "salida": "X",
    "via_exterior": "D",
    "punto_encuentro": "*",
}
TAMANOS_TIPO = {"aula": 26, "pasillo": 34, "gradas": 52, "salida": 110, "via_exterior": 22, "punto_encuentro": 220}
ETIQUETAS_TIPO = {
    "aula": "Aula / origen",
    "pasillo": "Pasillo",
    "gradas": "Gradas",
    "salida": "Salida",
    "via_exterior": "Vía exterior",
    "punto_encuentro": "Punto de encuentro",
}

COLOR_DIJKSTRA = "#2e7d32"
COLOR_CLASICO = "#1f5fbf"
COLOR_GUIADO = "#d9730d"
COLOR_BLOQUEO = "#b71c1c"
COLORES_VARIANTE = {"Dijkstra": COLOR_DIJKSTRA, "ACO clasico": COLOR_CLASICO, "ACO guiado": COLOR_GUIADO}


@lru_cache(maxsize=1)
def calibracion() -> dict[str, Any]:
    cal = cargar_json(CALIBRACION_PATH)
    return {
        "escala_px_por_m": float(cal["escala_px_por_m"]),
        "origen_px": (float(cal["puntos_de_control"]["salida_A"]["pixel_x"]), float(cal["puntos_de_control"]["salida_A"]["pixel_y"])),
        "imagen": RAIZ_PROYECTO / cal["imagen"],
    }


def pixel_a_xy(px: float, py: float) -> tuple[float, float]:
    c = calibracion()
    ox, oy = c["origen_px"]
    return (px - ox) / c["escala_px_por_m"], -(py - oy) / c["escala_px_por_m"]


def extension_plano_m() -> tuple[float, float, float, float]:
    """(izquierda, derecha, abajo, arriba) en metros del recorte, para imshow(extent=...)."""
    izq, arr, der, aba = CAJA_RECORTE
    x0, y_arr = pixel_a_xy(izq, arr)
    x1, y_aba = pixel_a_xy(der, aba)
    return x0, x1, y_aba, y_arr


@lru_cache(maxsize=1)
def imagen_plano(aclarado: float = 0.45) -> np.ndarray:
    """Imagen recortada y aclarada (mezclada con blanco) como arreglo RGB."""
    imagen = Image.open(calibracion()["imagen"]).convert("RGB").crop(CAJA_RECORTE)
    arr = np.asarray(imagen, dtype=float) / 255.0
    return (arr * (1 - aclarado) + aclarado).clip(0, 1)


def posicion_planta(nodo: dict[str, Any], altura_piso_m: float) -> tuple[float, float]:
    piso = nodo["piso"] or 0
    return nodo["x_m"], nodo["y_m"] - altura_piso_m * piso


def posiciones_planta(grafo: Grafo, altura_piso_m: float) -> dict[str, tuple[float, float]]:
    return {nid: posicion_planta(n, altura_piso_m) for nid, n in grafo.nodos_por_id.items() if n["x_m"] is not None}


def fondo_plano(ax, con_imagen: bool = True) -> None:
    """Dibuja la imagen calibrada como fondo y ajusta los limites al recorte."""
    x0, x1, y0, y1 = extension_plano_m()
    if con_imagen:
        ax.imshow(imagen_plano(), extent=(x0, x1, y0, y1), origin="upper", zorder=0)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")


def dibujar_nodos_planta(ax, grafo: Grafo, pos: dict[str, tuple[float, float]], tipos: tuple[str, ...] = ("salida", "punto_encuentro", "gradas", "pasillo"), etiquetas: bool = True) -> None:
    """Dibuja nodos 'hub' (sin aulas) sobre la planta, con colores y marcadores por tipo."""
    vistos = set()
    for nid, nodo in grafo.nodos_por_id.items():
        if nodo["tipo"] not in tipos or nid not in pos:
            continue
        xy = pos[nid]
        if (nodo["tipo"], round(xy[0], 1), round(xy[1], 1)) in vistos:
            continue
        vistos.add((nodo["tipo"], round(xy[0], 1), round(xy[1], 1)))
        ax.scatter(*xy, marker=MARCADORES_TIPO[nodo["tipo"]], s=TAMANOS_TIPO[nodo["tipo"]], color=COLORES_TIPO[nodo["tipo"]],
                   edgecolor="white", linewidth=0.8, zorder=6)
        if etiquetas and nodo["tipo"] in ("salida", "punto_encuentro"):
            ax.annotate(nodo["id"].replace("SALIDA-", "Salida "), xy, xytext=(6, 5), textcoords="offset points", fontsize=8, fontweight="bold", zorder=7,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))


def leyenda_tipos(ax, tipos: tuple[str, ...] = ("aula", "pasillo", "gradas", "salida", "via_exterior", "punto_encuentro"), **kwargs) -> None:
    from matplotlib.lines import Line2D

    elementos = [
        Line2D([], [], marker=MARCADORES_TIPO[t], linestyle="", color=COLORES_TIPO[t], markeredgecolor="white",
               markersize=9 if t != "punto_encuentro" else 13, label=ETIQUETAS_TIPO[t])
        for t in tipos
    ]
    ax.legend(handles=elementos, fontsize=8, frameon=True, framealpha=0.9, **kwargs)


def segmentos_planta(camino: list[str], pos: dict[str, tuple[float, float]]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Segmentos de un camino proyectados en planta (se omiten los tramos verticales de longitud cero)."""
    segmentos = []
    for a, b in zip(camino, camino[1:]):
        pa, pb = pos[a], pos[b]
        if abs(pa[0] - pb[0]) < 1e-6 and abs(pa[1] - pb[1]) < 1e-6:
            continue
        segmentos.append((pa, pb))
    return segmentos


ESTILOS_RUTA = {
    "Dijkstra": dict(color=COLOR_DIJKSTRA, lw=7, alpha=0.45, ls="-"),
    "ACO guiado": dict(color=COLOR_GUIADO, lw=3.2, alpha=0.95, ls=(0, (1.2, 1.6))),
    "ACO clasico": dict(color=COLOR_CLASICO, lw=2.2, alpha=0.95, ls=(0, (5, 2.5))),
}


def dibujar_rutas_plano(ax, grafo: Grafo, pos: dict[str, tuple[float, float]], rutas: dict[str, list[str] | None], origen: str | None = None,
                        bloqueadas: frozenset[str] = frozenset(), etiquetas_nodos: bool = True) -> None:
    """Plano calibrado con las rutas (por variante), los nodos hub, el origen y los bloqueos."""
    fondo_plano(ax)
    ax.grid(False)
    for variante, camino in rutas.items():
        if not camino:
            continue
        for pa, pb in segmentos_planta(camino, pos):
            ax.plot([pa[0], pb[0]], [pa[1], pb[1]], zorder=4, solid_capstyle="round", **ESTILOS_RUTA[variante])
    dibujar_nodos_planta(ax, grafo, pos, tipos=("salida", "gradas", "pasillo"), etiquetas=etiquetas_nodos)
    vistos = set()
    for aid in bloqueadas:
        arista = grafo.aristas_por_id[aid]
        pa, pb = pos[arista["desde"]], pos[arista["hasta"]]
        centro = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        if (round(centro[0], 1), round(centro[1], 1)) in vistos:
            continue
        vistos.add((round(centro[0], 1), round(centro[1], 1)))
        ax.scatter(*centro, marker="x", s=150, color=COLOR_BLOQUEO, linewidth=3, zorder=9)
    if origen:
        ax.scatter(*pos[origen], marker="o", s=150, color=COLORES_TIPO["aula"], edgecolor="black", linewidth=1.5, zorder=8)
        ax.annotate(origen, pos[origen], xytext=(-8, 9), textcoords="offset points", fontsize=9, fontweight="bold", ha="right", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))


# --------------------------------------------------------------------------
# Esquema por niveles
# --------------------------------------------------------------------------

_NIVELES = {"PB": 0, "1": 1, "2": 2, "3": 3, "4": 4}
PASO_NIVEL = 17.0


def layout_esquematico(grafo: Grafo) -> dict[str, tuple[float, float]]:
    """Posiciones del esquema por niveles: PB abajo, nivel 4 arriba, salidas y exterior bajo PB."""
    pos: dict[str, tuple[float, float]] = {}
    for nid, nodo in grafo.nodos_por_id.items():
        m = re.fullmatch(r"([HG])(\d)0(\d)", nid)
        if m:
            bloque, nivel, k = m.group(1), int(m.group(2)), int(m.group(3))
            x = (-60 + (k - 1) * 5.0) if bloque == "H" else (36 + (k - 1) * 5.0)
            pos[nid] = (x, nivel * PASO_NIVEL + (k - 3) * 2.4)
            continue
        if nid == "H-PB-OFICINAS_CC":
            pos[nid] = (-42.0, 0.0)
            continue
        if nid == "G-PB-LAB_BIOTEC":
            pos[nid] = (52.0, 0.0)
            continue
        m = re.fullmatch(r"(PAS-H|PAS-G|PAS-CENTRAL|GRADAS-NORTE|GRADAS-SUR)-(PB|\d)", nid)
        if m:
            tipo, nivel = m.group(1), _NIVELES[m.group(2)]
            y0 = nivel * PASO_NIVEL
            x, dy = {"PAS-H": (-28.0, 2.0), "PAS-CENTRAL": (4.0, 0.0), "PAS-G": (30.0, 2.0), "GRADAS-SUR": (-10.0, -6.0), "GRADAS-NORTE": (18.0, -6.0)}[tipo]
            pos[nid] = (x, y0 + dy)
    exteriores = {
        "SALIDA-A": (-10.0, -17.0), "SALIDA-B": (18.0, -17.0),
        "camino_rutaprincipal3_pt1": (-2.0, -30.0), "camino_rutaprincipal3_pt2": (8.0, -42.0),
        "camino_rutatransversal1_pt1": (-34.0, -30.0), "PE-1": (-56.0, -42.0), "PE-3": (-28.0, -46.0), "PE-2": (46.0, -30.0),
    }
    pos.update({k: v for k, v in exteriores.items() if k in grafo.nodos_por_id})
    return pos


def dibujar_esquema(ax, grafo: Grafo, tau: dict[str, float] | None = None, tau_rango: tuple[float, float] | None = None,
                    camino: list[str] | None = None, bloqueadas: frozenset[str] = frozenset(), titulo: str | None = None,
                    etiquetas_nivel: bool = True, cmap: str = "YlOrRd") -> None:
    """Esquema por niveles con aristas coloreadas por feromona (si se entrega tau) y nodos por tipo."""
    import matplotlib.pyplot as plt

    pos = layout_esquematico(grafo)
    lo, hi = tau_rango if tau_rango else ((min(tau.values()), max(tau.values())) if tau else (0.0, 1.0))
    mapa = plt.get_cmap(cmap)
    for arista in grafo.aristas_por_id.values():
        a, b = arista["desde"], arista["hasta"]
        if a not in pos or b not in pos:
            continue
        xs, ys = [pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]]
        if arista["id"] in bloqueadas:
            ax.plot(xs, ys, color=COLOR_BLOQUEO, linestyle=":", linewidth=1.8, zorder=2)
            continue
        if tau is not None and arista["id"] in tau:
            f = (tau[arista["id"]] - lo) / (hi - lo) if hi > lo else 0.0
            f = min(max(f, 0.0), 1.0)
            ax.plot(xs, ys, color=mapa(0.12 + 0.88 * f), linewidth=0.7 + 3.6 * f, zorder=1 + f, solid_capstyle="round")
        else:
            ax.plot(xs, ys, color="#c7c7c7", linewidth=0.7, zorder=1)
    if camino:
        for a, b in zip(camino, camino[1:]):
            ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color="#111111", linewidth=1.3, linestyle=(0, (1, 1.6)), zorder=5)
    for nid, nodo in grafo.nodos_por_id.items():
        if nid not in pos:
            continue
        t = nodo["tipo"]
        ax.scatter(*pos[nid], marker=MARCADORES_TIPO[t], s=TAMANOS_TIPO[t] * 0.55, color=COLORES_TIPO[t], edgecolor="white", linewidth=0.5, zorder=6)
    if etiquetas_nivel:
        for nombre, nivel in _NIVELES.items():
            ax.text(-71, nivel * PASO_NIVEL, "PB" if nombre == "PB" else f"Nivel {nombre}", fontsize=8, ha="right", va="center", color="#444444")
        for nid in ("SALIDA-A", "SALIDA-B", "PE-1", "PE-2", "PE-3"):
            if nid in pos:
                ax.annotate(nid.replace("SALIDA-", "Salida "), pos[nid], xytext=(5, -9), textcoords="offset points", fontsize=7.5)
    ax.set_xlim(-76, 64)
    ax.set_ylim(-52, 4 * PASO_NIVEL + 12)
    ax.set_aspect("equal")
    ax.axis("off")
    if titulo:
        ax.set_title(titulo, fontsize=10)
