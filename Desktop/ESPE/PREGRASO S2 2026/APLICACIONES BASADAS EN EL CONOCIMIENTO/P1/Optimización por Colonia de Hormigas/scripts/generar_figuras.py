"""Genera las figuras (PNG, 200 dpi) y las 2 animaciones (GIF) a partir de results/*.csv.

Uso:
    python scripts/generar_figuras.py

Lee los CSV que escribe scripts/correr_experimentos.py y el grafo calibrado;
escribe en results/figuras/ y results/animaciones/. No ajusta ni filtra
resultados: grafica lo que hay en los CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from PIL import Image

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from aco import aco_iterativo, parametros_clasico  # noqa: E402
from costos import tiempo_arista  # noqa: E402
from escenarios import ESCENARIOS_DISPONIBLES, ETIQUETA_ESCENARIO, ETIQUETA_VARIANTE, construir_escenario  # noqa: E402
from grafo import CONFIG_ACO_PATH, CONFIG_MODELO_PATH, aplicar_congestion, cargar_configuracion, cargar_grafo  # noqa: E402
from plano import (  # noqa: E402
    COLOR_CLASICO, COLOR_DIJKSTRA, COLOR_GUIADO, COLORES_TIPO, COLORES_VARIANTE, dibujar_esquema, dibujar_nodos_planta, dibujar_rutas_plano,
    extension_plano_m, fondo_plano, leyenda_tipos, posiciones_planta, segmentos_planta,
)

RESULTS = RAIZ_PROYECTO / "results"
FIGURAS = RESULTS / "figuras"
ANIMACIONES = RESULTS / "animaciones"
DPI = 200
V_DIJ, V_CLA, V_GUI = "Dijkstra", "ACO clasico", "ACO guiado"

plt.rcParams.update(
    {
        "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6, "legend.fontsize": 9, "figure.facecolor": "white",
        "axes.facecolor": "white", "savefig.facecolor": "white", "font.family": "DejaVu Sans",
    }
)


def guardar(fig, nombre: str) -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / nombre, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("figura:", nombre)


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / f"{nombre}.csv")


def esc(n: str) -> str:
    return ETIQUETA_ESCENARIO.get(n, n)


def primera_exitosa(df_bench: pd.DataFrame, variante: str, escenario: str, origen: str):
    sel = df_bench[(df_bench["variante"] == variante) & (df_bench["escenario"] == escenario) & (df_bench["origen"] == origen) & (df_bench["exito"])]
    return None if sel.empty else sel.sort_values("corrida").iloc[0]


# --------------------------------------------------------------------------
# 1. Plano calibrado con rutas
# --------------------------------------------------------------------------


def fig1_rutas(grafo, cm, df_bench, df_dij) -> None:
    pos = posiciones_planta(grafo, cm["altura_piso_m"])
    origenes = cargar_configuracion(CONFIG_ACO_PATH)["experimentos"]["origenes_figuras"]
    nombres_nivel = {"H-PB-OFICINAS_CC": "planta baja", "H203": "piso 2", "H403": "piso 4"}
    x0, x1, y0, y1 = extension_plano_m()
    fig, axes = plt.subplots(1, 3, figsize=(18, 4.6))
    for ax, origen in zip(axes, origenes):
        dij = df_dij[(df_dij["escenario"] == "Normal") & (df_dij["origen"] == origen)].iloc[0]
        rutas = [(V_DIJ, dij["ruta"].split(">"), None)]
        for v in (V_CLA, V_GUI):
            fila = primera_exitosa(df_bench, v, "Normal", origen)
            rutas.append((v, fila["ruta"].split(">") if fila is not None else None, None if fila is None else (fila["costo"], int(fila["semilla"]))))
        dibujar_rutas_plano(ax, grafo, pos, {v: c for v, c, _ in rutas}, origen=origen)
        destinos = []
        for variante, camino, _ in rutas:
            destinos.append(f"{ETIQUETA_VARIANTE[variante]}: {camino[-1] if camino else 'sin ruta'}")
        ax.set_title(f"Desde {origen} ({nombres_nivel[origen]})", fontsize=11)
        ax.text(0.02, 0.03, "\n".join(destinos) + "\n(la ruta continúa fuera del recorte hasta el punto de encuentro)", transform=ax.transAxes, fontsize=7.5, va="bottom",
                bbox=dict(boxstyle="round", fc="white", ec="#cccccc", alpha=0.9))
    elementos = [Line2D([], [], color=COLOR_DIJKSTRA, lw=7, alpha=0.45, label="Dijkstra (óptimo)"),
                 Line2D([], [], color=COLOR_CLASICO, lw=2.2, ls=(0, (5, 2.5)), label="ACO clásico"),
                 Line2D([], [], color=COLOR_GUIADO, lw=3.2, ls=(0, (1.2, 1.6)), label="ACO guiado")]
    axes[0].legend(handles=elementos, loc="upper left", fontsize=8.5, framealpha=0.92)
    leyenda_tipos(axes[2], tipos=("aula", "pasillo", "gradas", "salida"), loc="upper right")
    fig.suptitle("Rutas de evacuación sobre el plano calibrado (escenario Normal, primera corrida exitosa de ACO)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    guardar(fig, "fig1_rutas_plano_calibrado.png")


# --------------------------------------------------------------------------
# 2. Feromonas en 4 momentos (y datos para el GIF)
# --------------------------------------------------------------------------


def snapshots_clasico(grafo, cm, ca, df_bench, origen: str):
    fila = primera_exitosa(df_bench, V_CLA, "Normal", origen)
    semilla = int(fila["semilla"]) if fila is not None else int(ca["semilla_base_experimentos"])
    cfg = parametros_clasico(ca)
    snaps = list(aco_iterativo(grafo, origen, cm, cfg, semilla=semilla, variante="clasico"))
    return snaps, semilla


def fig2_feromonas(grafo, snaps, origen: str, semilla: int) -> None:
    n = len(snaps)
    primera = next((i for i, sn in enumerate(snaps, 1) if sn.hormigas_exitosas > 0), max(1, n // 2))
    momentos = sorted({1, primera, min(n, primera + 2), n})
    while len(momentos) < 4:
        momentos.append(momentos[-1])
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 11))
    for ax, it in zip(axes.ravel(), momentos):
        s = snaps[it - 1]
        lo, hi = min(s.feromona.values()), max(s.feromona.values())
        mejor = f"{s.mejor_costo_global:.1f}" if s.mejor_costo_global < float("inf") else "sin ruta"
        dibujar_esquema(ax, grafo, tau=s.feromona, tau_rango=(lo, hi), camino=s.mejor_camino_global,
                        titulo=f"Iteración {it} de {n}  |  mejor costo: {mejor}\nτ entre {lo:.3f} y {hi:.3f}")
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.025, pad=0.06, aspect=50)
    cb.set_label("Intensidad relativa de la feromona en cada panel (0 = mínimo, 1 = máximo de ese momento)")
    leyenda_tipos(axes[1, 0], loc="upper left", bbox_to_anchor=(0.0, 0.0), ncol=3)
    fig.suptitle(f"Evolución de la feromona, ACO clásico, origen {origen} (semilla {semilla}); línea punteada: mejor ruta", fontsize=12)
    guardar(fig, "fig2_mapa_calor_feromonas.png")


# --------------------------------------------------------------------------
# 3. Convergencia
# --------------------------------------------------------------------------


def fig3_convergencia(df_conv, df_dij) -> None:
    origenes = list(df_conv["origen"].unique())
    fig, axes = plt.subplots(1, len(origenes), figsize=(5.6 * len(origenes), 4.4), sharey=False)
    max_it = int(df_conv["iteracion"].max())
    for ax, origen in zip(np.atleast_1d(axes), origenes):
        opt = df_dij[(df_dij["escenario"] == "Normal") & (df_dij["origen"] == origen)]["costo"].iloc[0]
        for variante in (V_CLA, V_GUI):
            d = df_conv[(df_conv["variante"] == variante) & (df_conv["origen"] == origen)]
            mat = d.pivot(index="corrida", columns="iteracion", values="mejor_costo_global").reindex(columns=range(1, max_it + 1))
            mat = mat.ffill(axis=1)
            media, desv = mat.mean(axis=0, skipna=True), mat.std(axis=0, skipna=True)
            n_con = mat.notna().sum(axis=0)
            x = np.arange(1, max_it + 1)
            color = COLORES_VARIANTE[variante]
            ax.plot(x, media, color=color, lw=2, label=f"{ETIQUETA_VARIANTE[variante]} ({int(n_con.iloc[-1])} de {len(mat)} corridas con ruta)")
            ax.fill_between(x, media - desv.fillna(0), media + desv.fillna(0), color=color, alpha=0.2)
        ax.axhline(opt, color=COLOR_DIJKSTRA, ls="--", lw=1.6, label=f"Óptimo de Dijkstra ({opt:.1f})")
        ax.set_title(origen)
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Mejor costo acumulado (m equivalentes)")
        ax.legend(fontsize=7.5, loc="upper right")
    fig.suptitle("Convergencia: media ± 1 desviación estándar (escenario Normal); en cada iteración se promedian las corridas que ya hallaron ruta", fontsize=11)
    fig.tight_layout()
    guardar(fig, "fig3_convergencia.png")


# --------------------------------------------------------------------------
# 4. Costos, tiempos, exito y brecha por escenario
# --------------------------------------------------------------------------


def _posiciones_grupo(n_grupos: int, n_series: int, ancho: float = 0.8):
    paso = ancho / n_series
    return [np.arange(n_grupos) - ancho / 2 + paso * (i + 0.5) for i in range(n_series)], paso * 0.9


def fig4a_costos(df_bench, df_dij) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.2))
    series = [(V_DIJ, COLOR_DIJKSTRA), (V_CLA, COLOR_CLASICO), (V_GUI, COLOR_GUIADO)]
    xs, ancho = _posiciones_grupo(len(ESCENARIOS_DISPONIBLES), 3)
    for (variante, color), x in zip(series, xs):
        datos = []
        for e in ESCENARIOS_DISPONIBLES:
            if variante == V_DIJ:
                datos.append(df_dij[df_dij["escenario"] == e]["costo"].values)
            else:
                datos.append(df_bench[(df_bench["variante"] == variante) & (df_bench["escenario"] == e) & (df_bench["exito"])]["costo"].values)
        bp = ax.boxplot([d if len(d) else [np.nan] for d in datos], positions=x, widths=ancho, patch_artist=True, showfliers=True,
                        flierprops=dict(marker=".", markersize=2, alpha=0.3, markeredgecolor=color), medianprops=dict(color="black", lw=1.3))
        for caja in bp["boxes"]:
            caja.set(facecolor=color, alpha=0.55, edgecolor=color)
    ax.set_xticks(range(len(ESCENARIOS_DISPONIBLES)))
    ax.set_xticklabels([esc(e).replace(" ", "\n", 1) for e in ESCENARIOS_DISPONIBLES])
    ax.set_ylabel("Costo de la ruta (m equivalentes)")
    ax.set_title("Costo de las rutas por escenario (42 orígenes; ACO: corridas exitosas)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=c, alpha=0.55, label=ETIQUETA_VARIANTE[v]) for v, c in series], loc="upper left")
    fig.tight_layout()
    guardar(fig, "fig4a_costos_boxplot.png")


def fig4b_tiempos(df_bench, df_dij) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    xs, ancho = _posiciones_grupo(len(ESCENARIOS_DISPONIBLES), 3)
    series = [(V_DIJ, COLOR_DIJKSTRA), (V_CLA, COLOR_CLASICO), (V_GUI, COLOR_GUIADO)]
    for (variante, color), x in zip(series, xs):
        medias, desv = [], []
        for e in ESCENARIOS_DISPONIBLES:
            if variante == V_DIJ:
                t = df_dij[df_dij["escenario"] == e]["tiempo_s_mediana"] * 1000
            else:
                t = df_bench[(df_bench["variante"] == variante) & (df_bench["escenario"] == e)]["tiempo_s"] * 1000
            medias.append(t.mean())
            desv.append(t.std())
        ax.bar(x, medias, width=ancho, color=color, alpha=0.85, yerr=desv, capsize=2, label=ETIQUETA_VARIANTE[variante], error_kw=dict(lw=0.8))
    ax.set_yscale("log")
    ax.set_xticks(range(len(ESCENARIOS_DISPONIBLES)))
    ax.set_xticklabels([esc(e).replace(" ", "\n", 1) for e in ESCENARIOS_DISPONIBLES])
    ax.set_ylabel("Tiempo de cómputo por búsqueda (ms, escala log)")
    ax.set_title("Tiempo de cómputo por escenario (media ± desviación; Dijkstra: mediana de 30 repeticiones por origen)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    guardar(fig, "fig4b_tiempos_barras.png")


def fig4c_exito_brecha(df_bench) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    xs, ancho = _posiciones_grupo(len(ESCENARIOS_DISPONIBLES), 2)
    for (variante, color), x in zip([(V_CLA, COLOR_CLASICO), (V_GUI, COLOR_GUIADO)], xs):
        exito, brecha, bdesv = [], [], []
        for e in ESCENARIOS_DISPONIBLES:
            d = df_bench[(df_bench["variante"] == variante) & (df_bench["escenario"] == e)]
            exito.append(d["exito"].mean() * 100)
            b = d[d["exito"]]["brecha_pct"]
            brecha.append(b.mean())
            bdesv.append(b.std())
        axes[0].bar(x, exito, width=ancho, color=color, alpha=0.85, label=ETIQUETA_VARIANTE[variante])
        axes[1].bar(x, brecha, width=ancho, color=color, alpha=0.85, yerr=bdesv, capsize=2, error_kw=dict(lw=0.8), label=ETIQUETA_VARIANTE[variante])
    for ax, titulo, ylabel in ((axes[0], "Tasa de éxito (corridas con ruta)", "% de corridas"), (axes[1], "Brecha frente a Dijkstra (corridas exitosas)", "Brecha (%)")):
        ax.set_xticks(range(len(ESCENARIOS_DISPONIBLES)))
        ax.set_xticklabels([esc(e).replace(" ", "\n", 1) for e in ESCENARIOS_DISPONIBLES], fontsize=8)
        ax.set_title(titulo)
        ax.set_ylabel(ylabel)
    axes[0].set_ylim(0, 105)
    axes[0].legend(loc="lower right")
    fig.tight_layout()
    guardar(fig, "fig4c_exito_y_brecha.png")


# --------------------------------------------------------------------------
# 5. Sensibilidad
# --------------------------------------------------------------------------


def fig5_sensibilidad(df_sens) -> None:
    simbolo = {"alfa": "α (peso de la feromona)", "beta": "β (peso de la visibilidad)", "rho": "ρ (evaporación)", "n_hormigas": "Número de hormigas"}
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.4))
    for ax, parametro in zip(axes.ravel(), simbolo):
        d = df_sens[df_sens["parametro"] == parametro]
        grupos = []
        for valor, g in d.groupby("valor", sort=True):
            ok = g[g["exito"]]
            grupos.append((valor, ok["brecha_pct"].mean(), ok["brecha_pct"].std(), g["tiempo_s"].mean() * 1000, g["exito"].mean() * 100))
        v, b, bs, t, ex = (np.array(c, dtype=float) for c in zip(*grupos))
        ax.plot(v, b, "-o", color=COLOR_CLASICO, lw=2, label="Brecha media (%)")
        ax.fill_between(v, np.clip(np.nan_to_num(b - bs), 0, None), np.nan_to_num(b + bs), color=COLOR_CLASICO, alpha=0.2)
        for xi, bi, ei in zip(v, b, ex):
            ax.annotate(f"{ei:.0f}%", (xi, bi if not np.isnan(bi) else 0), xytext=(0, 8), textcoords="offset points", fontsize=7.5, ha="center", color="#333333")
        ax.set_xlabel(simbolo[parametro])
        ax.set_ylabel("Brecha media frente a Dijkstra (%)", color=COLOR_CLASICO)
        ax2 = ax.twinx()
        ax2.plot(v, t, "--s", color="#555555", lw=1.5, ms=4, label="Tiempo medio (ms)")
        ax2.set_ylabel("Tiempo medio (ms)", color="#555555")
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)
        ax.set_xticks(v)
    h = [Line2D([], [], color=COLOR_CLASICO, marker="o", label="Brecha media ± 1 desv. (corridas exitosas)"), Line2D([], [], color="#555555", ls="--", marker="s", label="Tiempo medio"),
         Line2D([], [], color="none", label="Rótulo sobre cada punto: tasa de éxito")]
    fig.legend(handles=h, loc="lower center", ncol=3, fontsize=9, frameon=False)
    fig.suptitle("Sensibilidad de ACO clásico (10 orígenes, escenario Normal, 30 corridas por valor)", fontsize=12)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    guardar(fig, "fig5_sensibilidad.png")


def fig5b_diagnostico_q(df_diag) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for beta, color, ls in ((0, "#1f5fbf", "-"), (2, "#8e44ad", "--")):
        g = df_diag[df_diag["beta"] == beta]
        qs, ex, br = [], [], []
        for q, gg in g.groupby("Q", sort=True):
            qs.append(q)
            ex.append(gg["exito"].mean() * 100)
            br.append(gg[gg["exito"]]["brecha_pct"].mean())
        axes[0].plot(qs, ex, ls, marker="o", color=color, label=f"β = {beta}")
        axes[1].plot(qs, br, ls, marker="o", color=color, label=f"β = {beta}")
    for ax, t, yl in ((axes[0], "Tasa de éxito", "% de corridas con ruta"), (axes[1], "Brecha media frente a Dijkstra", "Brecha (%)")):
        ax.set_xscale("log")
        ax.set_xlabel("Constante de depósito Q (escala log)")
        ax.set_ylabel(yl)
        ax.set_title(t)
        ax.legend()
    fig.suptitle("Diagnóstico complementario: efecto de Q en ACO clásico (10 orígenes, escenario Normal)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    guardar(fig, "fig5b_diagnostico_q.png")


# --------------------------------------------------------------------------
# 6. Adaptacion
# --------------------------------------------------------------------------


def fig6_adaptacion(df_adapt) -> None:
    escs = [e for e in ESCENARIOS_DISPONIBLES if e != "Normal"]
    combos = [(V_CLA, "frio", COLOR_CLASICO, 0.45, "ACO clásico, en frío"), (V_CLA, "warm_start", COLOR_CLASICO, 1.0, "ACO clásico, warm start"),
              (V_GUI, "frio", COLOR_GUIADO, 0.45, "ACO guiado, en frío"), (V_GUI, "warm_start", COLOR_GUIADO, 1.0, "ACO guiado, warm start")]
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
    xs, ancho = _posiciones_grupo(len(escs), 4, 0.84)
    for (variante, modo, color, alpha, etiqueta), x in zip(combos, xs):
        g = [df_adapt[(df_adapt["variante"] == variante) & (df_adapt["modo"] == modo) & (df_adapt["escenario"] == e)] for e in escs]
        axes[0].bar(x, [d[d["exito"]]["iteracion_convergencia"].mean() for d in g], width=ancho, color=color, alpha=alpha, label=etiqueta, edgecolor=color)
        axes[1].bar(x, [d["tiempo_s"].mean() * 1000 for d in g], width=ancho, color=color, alpha=alpha, edgecolor=color)
        axes[2].bar(x, [d["exito"].mean() * 100 for d in g], width=ancho, color=color, alpha=alpha, edgecolor=color)
    for ax, titulo in zip(axes, ("Iteración en que se halla la mejor ruta", "Tiempo de cómputo (ms)", "Tasa de éxito (%)")):
        ax.set_xticks(range(len(escs)))
        ax.set_xticklabels([esc(e).replace(" ", "\n", 1) for e in escs], fontsize=8)
        ax.set_title(titulo)
    axes[0].legend(fontsize=8)
    fig.suptitle("Adaptación a bloqueos y congestión: ACO en frío contra warm start (feromonas del escenario Normal)", fontsize=12)
    fig.tight_layout()
    guardar(fig, "fig6_adaptacion_frio_vs_warm.png")


# --------------------------------------------------------------------------
# 7. Evacuacion
# --------------------------------------------------------------------------


def fig7_evacuacion(df_curvas, df_evac) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharey=True)
    for ax, e in zip(axes.ravel(), ESCENARIOS_DISPONIBLES):
        for variante, ls, lw in ((V_DIJ, "-", 3.2), (V_CLA, "--", 2), (V_GUI, ":", 2.6)):
            c = df_curvas[(df_curvas["variante"] == variante) & (df_curvas["escenario"] == e)]
            if c.empty:
                continue
            ax.plot(c["tiempo_s"], c["acumulado"], color=COLORES_VARIANTE[variante], ls=ls, lw=lw, label=ETIQUETA_VARIANTE[variante])
            fila = df_evac[(df_evac["variante"] == variante) & (df_evac["escenario"] == e)].iloc[0]
            ax.scatter([fila["tiempo_primera_persona_s"]], [1], marker="v", color=COLORES_VARIANTE[variante], s=45, zorder=5)
            ax.scatter([fila["tiempo_ultima_persona_s"]], [fila["personas_con_ruta"]], marker="o", color=COLORES_VARIANTE[variante], s=45, zorder=5, edgecolor="black")
        ax.set_title(esc(e))
        ax.set_xlabel("Tiempo desde la alerta (s)")
    axes[0, 0].set_ylabel("Personas en el punto de encuentro")
    axes[1, 0].set_ylabel("Personas en el punto de encuentro")
    h = [Line2D([], [], color=COLORES_VARIANTE[v], ls=ls, lw=2, label=ETIQUETA_VARIANTE[v]) for v, ls in ((V_DIJ, "-"), (V_CLA, "--"), (V_GUI, ":"))]
    h += [Line2D([], [], marker="v", color="#555555", ls="", label="Primera persona"), Line2D([], [], marker="o", color="#555555", markeredgecolor="black", ls="", label="Última persona")]
    fig.legend(handles=h, loc="lower center", ncol=5, frameon=False)
    fig.suptitle("Evacuación completa: llegadas acumuladas (1020 personas; ACO: primera corrida exitosa por origen)", fontsize=12)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    guardar(fig, "fig7_evacuacion_acumulada.png")

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    variantes = (V_DIJ, V_CLA, V_GUI)
    xs, ancho = _posiciones_grupo(len(ESCENARIOS_DISPONIBLES), 3, 0.84)
    for variante, x in zip(variantes, xs):
        d = df_evac[df_evac["variante"] == variante].set_index("escenario").reindex(ESCENARIOS_DISPONIBLES)
        a = d["personas_salida_A"].values
        b = d["personas_salida_B"].values
        axes[0].bar(x, a, width=ancho, color=COLORES_VARIANTE[variante], alpha=0.5, edgecolor=COLORES_VARIANTE[variante], hatch="//", label=f"{ETIQUETA_VARIANTE[variante]}: Salida A")
        axes[0].bar(x, b, width=ancho, bottom=a, color=COLORES_VARIANTE[variante], alpha=0.95, label=f"{ETIQUETA_VARIANTE[variante]}: Salida B")
        bottom = np.zeros(len(ESCENARIOS_DISPONIBLES))
        for pe, tono in (("PE-1", 0.35), ("PE-2", 0.7), ("PE-3", 1.0)):
            v = d[f"personas_{pe}"].values
            axes[1].bar(x, v, width=ancho, bottom=bottom, color=COLORES_VARIANTE[variante], alpha=tono, edgecolor="white", lw=0.5)
            bottom += v
    for ax, titulo in zip(axes, ("Personas por salida", "Personas por punto de encuentro (tono claro a oscuro: PE-1, PE-2, PE-3)")):
        ax.set_xticks(range(len(ESCENARIOS_DISPONIBLES)))
        ax.set_xticklabels([esc(e).replace(" ", "\n", 1) for e in ESCENARIOS_DISPONIBLES], fontsize=8)
        ax.set_title(titulo)
        ax.set_ylabel("Personas")
        ax.set_ylim(0, 1100)
    axes[0].legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    fig.tight_layout()
    guardar(fig, "fig7b_personas_por_salida_y_pe.png")


# --------------------------------------------------------------------------
# Animaciones
# --------------------------------------------------------------------------


def _fig_a_imagen(fig) -> Image.Image:
    fig.canvas.draw()
    img = Image.frombuffer("RGBA", fig.canvas.get_width_height(), bytes(fig.canvas.buffer_rgba()), "raw", "RGBA", 0, 1).convert("RGB")
    return img


def _paleta_global(montaje: Image.Image) -> Image.Image:
    """Paleta de 256 colores: 184 de la imagen (foto del plano) + los colores del tema y del mapa de calor."""
    from matplotlib.colors import to_rgb

    base = montaje.quantize(colors=184, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    colores = list(base.getpalette()[: 184 * 3])
    tema = [*COLORES_TIPO.values(), COLOR_DIJKSTRA, COLOR_CLASICO, COLOR_GUIADO, "#b71c1c", "#111111", "#ffffff", "#bdbdbd", "#757575", "#c7c7c7", "#444444"]
    extra = [tuple(int(round(255 * c)) for c in to_rgb(t)) for t in tema]
    mapa = plt.get_cmap("YlOrRd")
    extra += [tuple(int(round(255 * c)) for c in mapa(v)[:3]) for v in np.linspace(0.12, 1.0, 72 - len(extra))]
    for rgb in extra:
        colores += list(rgb)
    colores += [0] * (768 - len(colores))
    paleta = Image.new("P", (1, 1))
    paleta.putpalette(colores[:768])
    return paleta


def _guardar_gif(frames: list[Image.Image], nombre: str, duracion_ms: int, max_mb: float = 15.0) -> None:
    """Guarda el GIF con una paleta global de 256 colores (sin parpadeo); reduce la resolucion si pasa de max_mb."""
    ANIMACIONES.mkdir(parents=True, exist_ok=True)
    ruta = ANIMACIONES / nombre
    escala = 1.0
    while True:
        tam = (int(frames[0].width * escala), int(frames[0].height * escala))
        redim = [f.resize(tam, Image.LANCZOS) for f in frames]
        muestra = redim[:: max(1, len(redim) // 8)]
        montaje = Image.new("RGB", (tam[0], tam[1] * len(muestra)))
        for i, m in enumerate(muestra):
            montaje.paste(m, (0, i * tam[1]))
        paleta = _paleta_global(montaje)
        pal = [f.quantize(palette=paleta, dither=Image.Dither.NONE) for f in redim]
        pal[0].save(ruta, save_all=True, append_images=pal[1:], duration=duracion_ms, loop=0, optimize=False, disposal=2)
        mb = ruta.stat().st_size / 1e6
        if mb <= max_mb:
            print(f"gif: {nombre} ({mb:.1f} MB, {len(frames)} fotogramas, {tam[0]}x{tam[1]})")
            return
        escala *= 0.85


def gif_feromonas(grafo, cm, snaps, df_dij, origen: str, semilla: int) -> None:
    pos = posiciones_planta(grafo, cm["altura_piso_m"])
    opt = df_dij[(df_dij["escenario"] == "Normal") & (df_dij["origen"] == origen)].iloc[0]
    camino_opt = opt["ruta"].split(">")
    fig = plt.figure(figsize=(12.5, 5.6), dpi=80)
    frames = []
    for s in snaps:
        fig.clf()
        ax1 = fig.add_axes((0.02, 0.06, 0.52, 0.84))
        ax2 = fig.add_axes((0.55, 0.02, 0.44, 0.9))
        fondo_plano(ax1)
        ax1.grid(False)
        for (pa, pb) in segmentos_planta(camino_opt, pos):
            ax1.plot([pa[0], pb[0]], [pa[1], pb[1]], color=COLOR_DIJKSTRA, lw=7, alpha=0.4, zorder=3)
        if s.mejor_camino_global:
            for (pa, pb) in segmentos_planta(s.mejor_camino_global, pos):
                ax1.plot([pa[0], pb[0]], [pa[1], pb[1]], color=COLOR_CLASICO, lw=2.6, zorder=4)
        dibujar_nodos_planta(ax1, grafo, pos, tipos=("salida", "gradas", "pasillo"), etiquetas=False)
        ax1.scatter(*pos[origen], marker="o", s=110, color=COLORES_TIPO["aula"], edgecolor="black", linewidth=1.4, zorder=8)
        ax1.set_title(f"Mejor ruta de ACO clásico desde {origen} (verde: óptimo de Dijkstra)", fontsize=9)
        mejor = f"{s.mejor_costo_global:.1f}" if s.mejor_costo_global < float("inf") else "sin ruta"
        lo, hi = min(s.feromona.values()), max(s.feromona.values())
        dibujar_esquema(ax2, grafo, tau=s.feromona, tau_rango=(lo, hi), camino=s.mejor_camino_global,
                        titulo=f"Iteración {s.iteracion}  |  mejor costo {mejor}  |  óptimo {opt['costo']:.1f}  |  hormigas con ruta: {s.hormigas_exitosas}\n"
                               f"color de la feromona relativo al cuadro: τ entre {lo:.3f} y {hi:.3f}")
        frames.append(_fig_a_imagen(fig))
    plt.close(fig)
    frames += [frames[-1]] * 6
    _guardar_gif(frames, "aco_feromonas.gif", 220)


def gif_evacuacion(grafo, cm, df_dij) -> None:
    pos = posiciones_planta(grafo, cm["altura_piso_m"])
    pob = cm["poblacion_por_origen"]
    t_reac, dt = cm["tiempo_reaccion_s"], cm["tiempo_entre_personas_s"]
    rutas = {}
    for fila in df_dij[df_dij["escenario"] == "Normal"].itertuples():
        camino = fila.ruta.split(">")
        tiempos = [0.0]
        for a, b in zip(camino, camino[1:]):
            arista = next(ar for v, ar in grafo.vecinos(a) if v == b)
            tiempos.append(tiempos[-1] + tiempo_arista(arista, cm))
        rutas[fila.origen] = (camino, np.array(tiempos))
    x0, x1, y0, y1 = extension_plano_m()
    t_max = max(t_reac + r[1][-1] + (pob[o] - 1) * dt for o, r in rutas.items())
    fig = plt.figure(figsize=(9.2, 7.4), dpi=80)
    ax = fig.add_axes((0.07, 0.07, 0.9, 0.84))
    frames = []
    color_bloque = {"H": "#1f77b4", "G": "#7b3fa0"}
    for t in np.arange(0, t_max + 6, 4.0):
        ax.cla()
        fondo_plano(ax)
        ax.set_ylim(y0, 142)
        ax.grid(False)
        for fila in df_dij[df_dij["escenario"] == "Normal"].itertuples():
            pass
        en_espera, en_ruta, llegadas = {}, {"H": [], "G": []}, 0
        for origen, (camino, tiempos) in rutas.items():
            bloque = grafo.nodos_por_id[origen]["bloque"]
            n_espera = 0
            xy_ruta = np.array([pos[n] for n in camino])
            for k in range(pob[origen]):
                s = t - (t_reac + k * dt)
                if s < 0:
                    n_espera += 1
                elif s >= tiempos[-1]:
                    llegadas += 1
                else:
                    i = int(np.searchsorted(tiempos, s, side="right") - 1)
                    f = (s - tiempos[i]) / (tiempos[i + 1] - tiempos[i]) if tiempos[i + 1] > tiempos[i] else 0.0
                    en_ruta[bloque].append(xy_ruta[i] + f * (xy_ruta[i + 1] - xy_ruta[i]))
            if n_espera:
                en_espera[origen] = n_espera
        for origen, n in en_espera.items():
            ax.scatter(*pos[origen], s=8 + 1.6 * n, color="#bdbdbd", edgecolor="#757575", linewidth=0.5, zorder=4)
        for bloque, pts in en_ruta.items():
            if pts:
                p = np.array(pts)
                ax.scatter(p[:, 0], p[:, 1], s=9, color=color_bloque[bloque], alpha=0.8, zorder=6)
        dibujar_nodos_planta(ax, grafo, pos, tipos=("salida", "punto_encuentro", "gradas", "pasillo"))
        en_mov = sum(len(p) for p in en_ruta.values())
        ax.set_title(f"Evacuación, escenario Normal (rutas de Dijkstra)  |  t = {int(t)} s\n"
                     f"en espera: {sum(en_espera.values())}   en movimiento: {en_mov}   en el punto de encuentro: {llegadas}", fontsize=10)
        h = [Line2D([], [], marker="o", ls="", color=color_bloque["H"], label="Origen bloque H"), Line2D([], [], marker="o", ls="", color=color_bloque["G"], label="Origen bloque G"),
             Line2D([], [], marker="o", ls="", color="#bdbdbd", markeredgecolor="#757575", label="En espera (tamaño = personas)")]
        ax.legend(handles=h, loc="upper left", fontsize=8, framealpha=0.9)
        frames.append(_fig_a_imagen(fig))
    plt.close(fig)
    frames += [frames[-1]] * 6
    _guardar_gif(frames, "evacuacion.gif", 140)


def main() -> int:
    grafo = cargar_grafo()
    cm = cargar_configuracion(CONFIG_MODELO_PATH)
    ca = cargar_configuracion(CONFIG_ACO_PATH)
    df_bench, df_dij, df_adapt = leer("benchmark_principal"), leer("dijkstra_referencia"), leer("adaptacion")
    df_sens, df_conv = leer("sensibilidad"), leer("convergencia")
    df_evac, df_curvas = leer("evacuacion_completa"), leer("evacuacion_curvas")

    fig1_rutas(grafo, cm, df_bench, df_dij)
    origen_fero = ca["experimentos"]["origen_feromonas"]
    snaps, semilla = snapshots_clasico(grafo, cm, ca, df_bench, origen_fero)
    fig2_feromonas(grafo, snaps, origen_fero, semilla)
    fig3_convergencia(df_conv, df_dij)
    fig4a_costos(df_bench, df_dij)
    fig4b_tiempos(df_bench, df_dij)
    fig4c_exito_brecha(df_bench)
    fig5_sensibilidad(df_sens)
    fig5b_diagnostico_q(leer("diagnostico_q"))
    fig6_adaptacion(df_adapt)
    fig7_evacuacion(df_curvas, df_evac)
    gif_feromonas(grafo, cm, snaps, df_dij, origen_fero, semilla)
    gif_evacuacion(grafo, cm, df_dij)
    return 0


if __name__ == "__main__":
    sys.exit(main())
