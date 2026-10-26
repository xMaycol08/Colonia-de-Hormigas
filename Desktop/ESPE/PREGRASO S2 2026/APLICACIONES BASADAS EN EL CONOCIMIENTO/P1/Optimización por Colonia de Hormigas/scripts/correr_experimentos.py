"""Experimentos oficiales (Fase 3): benchmark, adaptacion, sensibilidad, convergencia y evacuacion.

Corre, con semillas fijas y de forma secuencial (los tiempos son comparables):

1. Benchmark principal: 6 escenarios x 42 origenes x N corridas x 2 variantes de ACO
   ("ACO clasico" y "ACO guiado"), mas Dijkstra por origen y escenario.
2. Adaptacion: ACO en frio contra warm start (feromonas finales del escenario
   Normal), 5 escenarios con bloqueo/congestion, ambas variantes.
3. Sensibilidad de alfa, beta, rho y n_hormigas (solo ACO clasico).
4. Convergencia por iteracion (origenes de las figuras, escenario Normal).
5. Evacuacion completa (primera y ultima persona, personas por salida y por punto de encuentro).
6. Prueba de cordura: ningun costo de ACO menor al de Dijkstra (tolerancia 1e-9).

Todos los numeros viven en data/config_aco.json y data/config_modelo.json.

Uso:
    python scripts/correr_experimentos.py                 # corrida oficial -> results/
    python scripts/correr_experimentos.py --estimar       # solo estima el tiempo
    python scripts/correr_experimentos.py --corridas 2 --salida /ruta/tmp   # prueba rapida
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from aco import ejecutar_aco, parametros_clasico  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from escenarios import ESCENARIOS_DISPONIBLES, construir_escenario  # noqa: E402
from grafo import (  # noqa: E402
    CONFIG_ACO_PATH,
    CONFIG_MODELO_PATH,
    aplicar_congestion,
    cargar_configuracion,
    cargar_grafo,
)
from evacuacion import curva_acumulada, salida_de, simular_evacuacion  # noqa: E402

TOLERANCIA_CORDURA = 1e-9
V_CLASICO = "ACO clasico"
V_GUIADO = "ACO guiado"
V_DIJKSTRA = "Dijkstra"
VARIANTES_ACO = {V_CLASICO: "clasico", V_GUIADO: "guiado"}
ESCENARIOS_CON_CAMBIO = [e for e in ESCENARIOS_DISPONIBLES if e != "Normal"]


class ErrorCordura(RuntimeError):
    """Un costo de ACO resulto menor al de Dijkstra: es un bug."""


class Contexto:
    """Datos compartidos por todos los experimentos."""

    def __init__(self, n_corridas: int | None = None, n_sens: int | None = None):
        self.grafo = cargar_grafo()
        self.cm = cargar_configuracion(CONFIG_MODELO_PATH)
        self.ca = cargar_configuracion(CONFIG_ACO_PATH)
        self.exp = self.ca["experimentos"]
        self.semilla_base = int(self.ca["semilla_base_experimentos"])
        self.n_bench = n_corridas or int(self.exp["n_corridas_benchmark"])
        self.n_adapt = n_corridas or int(self.exp["n_corridas_adaptacion"])
        self.n_sens = n_sens or n_corridas or int(self.exp["n_corridas_sensibilidad"])
        self.n_rep_dijkstra = int(self.exp["repeticiones_tiempo_dijkstra"])
        self.origenes = list(self.cm["poblacion_por_origen"])
        self.cfg_variante = {V_CLASICO: parametros_clasico(self.ca), V_GUIADO: self.ca}
        self.escenarios = {n: construir_escenario(n, self.grafo, self.cm) for n in ESCENARIOS_DISPONIBLES}
        self.grafo_esc = {n: aplicar_congestion(self.grafo, e.congestion) for n, e in self.escenarios.items()}
        self.cordura_verificadas = 0
        self.cordura_violaciones: list[str] = []
        self.ref: dict[tuple[str, str], dict] = {}  # (escenario, origen) -> referencia de Dijkstra

    def semillas(self, n: int) -> list[int]:
        return [self.semilla_base + i for i in range(n)]


def _salida_de(grafo, camino):
    return salida_de(grafo, camino)


def _log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


# --------------------------------------------------------------------------
# Dijkstra (referencia)
# --------------------------------------------------------------------------


def correr_dijkstra(ctx: Contexto) -> pd.DataFrame:
    filas = []
    for nombre, esc in ctx.escenarios.items():
        g = ctx.grafo_esc[nombre]
        for origen in ctx.origenes:
            tiempos = []
            for _ in range(ctx.n_rep_dijkstra):
                t0 = time.perf_counter()
                r = buscar_ruta(g, origen, ctx.cm, esc.aristas_bloqueadas)
                tiempos.append((time.perf_counter() - t0) * 1000)
            ctx.ref[(nombre, origen)] = {"costo": r.costo, "camino": r.camino}
            filas.append(
                {
                    "variante": V_DIJKSTRA,
                    "escenario": nombre,
                    "origen": origen,
                    "tiene_ruta": r.tiene_ruta,
                    "costo": r.costo,
                    "tiempo_s_mediana": statistics.median(tiempos) / 1000,
                    "nodos_expandidos": r.nodos_expandidos,
                    "punto_encuentro": r.punto_encuentro,
                    "salida": _salida_de(ctx.grafo, r.camino),
                    "ruta": ">".join(r.camino) if r.camino else "",
                }
            )
    return pd.DataFrame(filas)


def _verificar_cordura(ctx: Contexto, contexto_txt: str, escenario: str, origen: str, semilla: int, costo: float) -> None:
    ctx.cordura_verificadas += 1
    optimo = ctx.ref[(escenario, origen)]["costo"]
    if costo < optimo - TOLERANCIA_CORDURA:
        msg = f"{contexto_txt}: escenario={escenario} origen={origen} semilla={semilla} costo_ACO={costo!r} costo_Dijkstra={optimo!r}"
        ctx.cordura_violaciones.append(msg)
        raise ErrorCordura(msg)


# --------------------------------------------------------------------------
# Benchmark principal y adaptacion
# --------------------------------------------------------------------------


def _fila_corrida(ctx: Contexto, variante: str, escenario: str, origen: str, corrida: int, semilla: int, r, extra: dict | None = None) -> dict:
    optimo = ctx.ref[(escenario, origen)]["costo"]
    brecha = (r.mejor_costo - optimo) / optimo * 100 if r.tiene_ruta else None
    fila = {
        "variante": variante,
        "escenario": escenario,
        "origen": origen,
        "corrida": corrida,
        "semilla": semilla,
        "exito": r.tiene_ruta,
        "costo": r.mejor_costo if r.tiene_ruta else None,
        "costo_dijkstra": optimo,
        "brecha_pct": brecha,
        "tiempo_s": r.tiempo_s,
        "iteracion_convergencia": r.iteracion_mejor_solucion if r.tiene_ruta else None,
        "iteraciones_ejecutadas": len(r.historial),
        "punto_encuentro": r.punto_encuentro,
        "salida": _salida_de(ctx.grafo, r.mejor_camino),
        "ruta": ">".join(r.mejor_camino) if r.mejor_camino else "",
    }
    if extra:
        fila.update(extra)
    return fila


def correr_benchmark(ctx: Contexto) -> tuple[pd.DataFrame, dict]:
    """Benchmark principal. Devuelve (df, feromonas_normal) para el warm start de la adaptacion."""
    filas = []
    feromonas_normal: dict[tuple[str, str, int], dict[str, float]] = {}
    semillas = ctx.semillas(ctx.n_bench)
    for variante, clave in VARIANTES_ACO.items():
        cfg = ctx.cfg_variante[variante]
        for nombre, esc in ctx.escenarios.items():
            g = ctx.grafo_esc[nombre]
            _log(f"benchmark: {variante} / {nombre}")
            for origen in ctx.origenes:
                for i, semilla in enumerate(semillas):
                    r = ejecutar_aco(g, origen, ctx.cm, cfg, esc.aristas_bloqueadas, semilla=semilla, variante=clave)
                    if r.tiene_ruta:
                        _verificar_cordura(ctx, "benchmark", nombre, origen, semilla, r.mejor_costo)
                    filas.append(_fila_corrida(ctx, variante, nombre, origen, i, semilla, r))
                    if nombre == "Normal":
                        feromonas_normal[(variante, origen, semilla)] = r.feromona_final
    return pd.DataFrame(filas), feromonas_normal


def correr_adaptacion(ctx: Contexto, df_bench: pd.DataFrame, feromonas_normal: dict) -> pd.DataFrame:
    """Frio (copiado del benchmark, misma semilla) contra warm start con feromonas del escenario Normal."""
    filas = []
    semillas = ctx.semillas(ctx.n_adapt)
    set_sem = set(semillas)
    frio = df_bench[(df_bench["escenario"] != "Normal") & (df_bench["semilla"].isin(set_sem))].copy()
    frio["modo"] = "frio"
    filas.append(frio)
    calientes = []
    for variante, clave in VARIANTES_ACO.items():
        cfg = ctx.cfg_variante[variante]
        for nombre in ESCENARIOS_CON_CAMBIO:
            esc = ctx.escenarios[nombre]
            g = ctx.grafo_esc[nombre]
            _log(f"adaptacion (warm start): {variante} / {nombre}")
            for origen in ctx.origenes:
                for i, semilla in enumerate(semillas):
                    r = ejecutar_aco(
                        g, origen, ctx.cm, cfg, esc.aristas_bloqueadas,
                        feromona_inicial=feromonas_normal[(variante, origen, semilla)], semilla=semilla, variante=clave,
                    )
                    if r.tiene_ruta:
                        _verificar_cordura(ctx, "adaptacion (warm start)", nombre, origen, semilla, r.mejor_costo)
                    calientes.append(_fila_corrida(ctx, variante, nombre, origen, i, semilla, r, {"modo": "warm_start"}))
    filas.append(pd.DataFrame(calientes))
    df = pd.concat(filas, ignore_index=True)
    cols = ["variante", "escenario", "modo"] + [c for c in df.columns if c not in ("variante", "escenario", "modo")]
    return df[cols]


# --------------------------------------------------------------------------
# Sensibilidad (solo ACO clasico)
# --------------------------------------------------------------------------


def correr_sensibilidad(ctx: Contexto) -> pd.DataFrame:
    filas = []
    semillas = ctx.semillas(ctx.n_sens)
    esc = ctx.escenarios["Normal"]
    g = ctx.grafo_esc["Normal"]
    for parametro, valores in ctx.exp["valores_sensibilidad"].items():
        for valor in valores:
            cfg = dict(ctx.cfg_variante[V_CLASICO])
            cfg[parametro] = int(valor) if parametro == "n_hormigas" else float(valor)
            _log(f"sensibilidad: {parametro}={valor}")
            for origen in ctx.exp["origenes_sensibilidad"]:
                for i, semilla in enumerate(semillas):
                    r = ejecutar_aco(g, origen, ctx.cm, cfg, esc.aristas_bloqueadas, semilla=semilla, variante="clasico")
                    if r.tiene_ruta:
                        _verificar_cordura(ctx, f"sensibilidad {parametro}={valor}", "Normal", origen, semilla, r.mejor_costo)
                    filas.append(_fila_corrida(ctx, V_CLASICO, "Normal", origen, i, semilla, r, {"parametro": parametro, "valor": valor}))
    df = pd.DataFrame(filas)
    cols = ["variante", "parametro", "valor"] + [c for c in df.columns if c not in ("variante", "parametro", "valor")]
    return df[cols]


# --------------------------------------------------------------------------
# Diagnostico complementario: escala del deposito de feromona (Q)
# --------------------------------------------------------------------------


def correr_diagnostico_q(ctx: Contexto) -> pd.DataFrame:
    """Complementario: Q (y beta) sobre ACO clasico, escenario Normal, 10 origenes de sensibilidad."""
    filas = []
    n = int(ctx.exp["n_corridas_diagnostico_q"]) if ctx.n_sens == int(ctx.exp["n_corridas_sensibilidad"]) else ctx.n_sens
    esc = ctx.escenarios["Normal"]
    g = ctx.grafo_esc["Normal"]
    for q in ctx.exp["diagnostico_q"]["Q"]:
        for beta in ctx.exp["diagnostico_q"]["beta"]:
            cfg = dict(ctx.cfg_variante[V_CLASICO], Q=float(q), beta=float(beta))
            _log(f"diagnostico Q={q} beta={beta}")
            for origen in ctx.exp["origenes_sensibilidad"]:
                for i, semilla in enumerate(ctx.semillas(n)):
                    r = ejecutar_aco(g, origen, ctx.cm, cfg, esc.aristas_bloqueadas, semilla=semilla, variante="clasico")
                    if r.tiene_ruta:
                        _verificar_cordura(ctx, f"diagnostico Q={q} beta={beta}", "Normal", origen, semilla, r.mejor_costo)
                    filas.append(_fila_corrida(ctx, V_CLASICO, "Normal", origen, i, semilla, r, {"Q": q, "beta": beta}))
    df = pd.DataFrame(filas)
    cols = ["variante", "Q", "beta"] + [c for c in df.columns if c not in ("variante", "Q", "beta")]
    return df[cols]


# --------------------------------------------------------------------------
# Convergencia por iteracion
# --------------------------------------------------------------------------


def correr_convergencia(ctx: Contexto) -> pd.DataFrame:
    filas = []
    g = ctx.grafo_esc["Normal"]
    esc = ctx.escenarios["Normal"]
    for variante, clave in VARIANTES_ACO.items():
        cfg = ctx.cfg_variante[variante]
        for origen in ctx.exp["origenes_figuras"]:
            for i, semilla in enumerate(ctx.semillas(ctx.n_bench)):
                r = ejecutar_aco(g, origen, ctx.cm, cfg, esc.aristas_bloqueadas, semilla=semilla, variante=clave)
                mejor = math.inf
                for h in r.historial:
                    mejor = min(mejor, h.mejor_costo_iteracion)
                    filas.append(
                        {
                            "variante": variante, "origen": origen, "corrida": i, "semilla": semilla,
                            "iteracion": h.iteracion, "mejor_costo_global": mejor if mejor < math.inf else None,
                        }
                    )
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------
# Evacuacion completa
# --------------------------------------------------------------------------


def _rutas_por_algoritmo(ctx: Contexto, df_dij: pd.DataFrame, df_bench: pd.DataFrame) -> dict:
    """(algoritmo, escenario, origen) -> camino. ACO usa la primera corrida exitosa (orden de semilla)."""
    rutas = {}
    for fila in df_dij.itertuples():
        rutas[(V_DIJKSTRA, fila.escenario, fila.origen)] = fila.ruta.split(">") if fila.ruta else None
    exitosas = df_bench[df_bench["exito"]].sort_values("corrida")
    primeras = exitosas.groupby(["variante", "escenario", "origen"], sort=False).first()
    for (variante, escenario, origen), fila in primeras.iterrows():
        rutas[(variante, escenario, origen)] = fila["ruta"].split(">")
    return rutas


def correr_evacuacion(ctx: Contexto, df_dij: pd.DataFrame, df_bench: pd.DataFrame):
    """Modelo de src/evacuacion.py (sin colas ni capacidad), con la ruta de cada algoritmo."""
    rutas = _rutas_por_algoritmo(ctx, df_dij, df_bench)
    pes = sorted(ctx.grafo.ids_puntos_encuentro)
    resumen, reparto, curvas = [], [], []
    for algoritmo in (V_DIJKSTRA, V_CLASICO, V_GUIADO):
        for escenario in ESCENARIOS_DISPONIBLES:
            por_origen = {o: rutas.get((algoritmo, escenario, o)) for o in ctx.origenes}
            r = simular_evacuacion(ctx.grafo_esc[escenario], por_origen, ctx.cm)
            resumen.append(
                {
                    "variante": algoritmo, "escenario": escenario,
                    "poblacion_total": r["poblacion_total"], "personas_con_ruta": len(r["llegadas"]), "personas_sin_ruta": r["sin_ruta"],
                    "tiempo_primera_persona_s": r["primera_s"], "tiempo_ultima_persona_s": r["ultima_s"],
                    "personas_salida_A": r["por_salida"].get("SALIDA-A", 0), "personas_salida_B": r["por_salida"].get("SALIDA-B", 0),
                    **{f"personas_{pe}": r["por_pe"][pe] for pe in pes},
                }
            )
            reparto.append(
                {
                    "variante": algoritmo, "escenario": escenario, "origenes_con_ruta": r["origenes_con_ruta"],
                    "pct_origenes_salida_A": r["origenes_salida"].get("SALIDA-A", 0) / r["origenes_total"] * 100,
                    "pct_origenes_salida_B": r["origenes_salida"].get("SALIDA-B", 0) / r["origenes_total"] * 100,
                    **{f"origenes_{pe}": r["origenes_pe"][pe] for pe in pes},
                }
            )
            for t, acumulado in curva_acumulada(r["llegadas"]):
                curvas.append({"variante": algoritmo, "escenario": escenario, "tiempo_s": t, "acumulado": acumulado})
    return pd.DataFrame(resumen), pd.DataFrame(reparto), pd.DataFrame(curvas)


# --------------------------------------------------------------------------
# Tablas resumen
# --------------------------------------------------------------------------


def _agrega(grupo: pd.DataFrame) -> pd.Series:
    ok = grupo[grupo["exito"]]
    return pd.Series(
        {
            "n_corridas": len(grupo),
            "tasa_exito_pct": len(ok) / len(grupo) * 100,
            "costo_medio": ok["costo"].mean(),
            "costo_desv": ok["costo"].std(),
            "costo_min": ok["costo"].min(),
            "costo_max": ok["costo"].max(),
            "brecha_pct_media": ok["brecha_pct"].mean(),
            "brecha_pct_max": ok["brecha_pct"].max(),
            "pct_corridas_optimas": (ok["brecha_pct"].abs() < 1e-9).sum() / len(grupo) * 100,
            "tiempo_ms_medio": grupo["tiempo_s"].mean() * 1000,
            "tiempo_ms_desv": grupo["tiempo_s"].std() * 1000,
            "iteracion_convergencia_media": ok["iteracion_convergencia"].mean(),
        }
    )


def tablas_resumen(df_bench, df_dij, df_adapt, df_sens, df_diag) -> dict[str, pd.DataFrame]:
    out = {}
    out["resumen_benchmark"] = df_bench.groupby(["variante", "escenario"], sort=False).apply(_agrega, include_groups=False).reset_index()
    out["resumen_benchmark_por_origen"] = df_bench.groupby(["variante", "escenario", "origen"], sort=False).apply(_agrega, include_groups=False).reset_index()
    d = df_dij.groupby("escenario", sort=False).agg(costo_medio=("costo", "mean"), tiempo_ms_medio=("tiempo_s_mediana", lambda s: s.mean() * 1000)).reset_index()
    d.insert(0, "variante", V_DIJKSTRA)
    out["resumen_dijkstra"] = d
    ad = df_adapt.groupby(["variante", "escenario", "modo"], sort=False).apply(_agrega, include_groups=False).reset_index()
    iters = df_adapt.groupby(["variante", "escenario", "modo"], sort=False)["iteraciones_ejecutadas"].mean().reset_index(name="iteraciones_ejecutadas_media")
    ad = ad.merge(iters, on=["variante", "escenario", "modo"])
    out["resumen_adaptacion"] = ad
    filas = []
    for (v, e), g in ad.groupby(["variante", "escenario"], sort=False):
        f = g[g["modo"] == "frio"].iloc[0]
        w = g[g["modo"] == "warm_start"].iloc[0]
        red = lambda a, b: (a - b) / a * 100 if a and not math.isnan(a) and a != 0 else None  # noqa: E731
        filas.append(
            {
                "variante": v, "escenario": e,
                "iteracion_convergencia_frio": f["iteracion_convergencia_media"], "iteracion_convergencia_warm": w["iteracion_convergencia_media"],
                "reduccion_iteracion_convergencia_pct": red(f["iteracion_convergencia_media"], w["iteracion_convergencia_media"]),
                "iteraciones_ejecutadas_frio": f["iteraciones_ejecutadas_media"], "iteraciones_ejecutadas_warm": w["iteraciones_ejecutadas_media"],
                "reduccion_iteraciones_ejecutadas_pct": red(f["iteraciones_ejecutadas_media"], w["iteraciones_ejecutadas_media"]),
                "tiempo_ms_frio": f["tiempo_ms_medio"], "tiempo_ms_warm": w["tiempo_ms_medio"],
                "reduccion_tiempo_pct": red(f["tiempo_ms_medio"], w["tiempo_ms_medio"]),
                "tasa_exito_frio_pct": f["tasa_exito_pct"], "tasa_exito_warm_pct": w["tasa_exito_pct"],
                "brecha_pct_frio": f["brecha_pct_media"], "brecha_pct_warm": w["brecha_pct_media"],
            }
        )
    out["resumen_adaptacion_reduccion"] = pd.DataFrame(filas)
    out["resumen_sensibilidad"] = df_sens.groupby(["variante", "parametro", "valor"], sort=False).apply(_agrega, include_groups=False).reset_index()
    out["resumen_diagnostico_q"] = df_diag.groupby(["variante", "Q", "beta"], sort=False).apply(_agrega, include_groups=False).reset_index()
    return out


# --------------------------------------------------------------------------
# Estimacion de tiempo
# --------------------------------------------------------------------------


def estimar(ctx: Contexto, origen: str = "H301") -> dict:
    """Mide 1 origen x 1 escenario (Normal) x 30 corridas por variante y extrapola el plan completo."""
    esc = ctx.escenarios["Normal"]
    g = ctx.grafo_esc["Normal"]
    t_run = {}
    for variante, clave in VARIANTES_ACO.items():
        t0 = time.perf_counter()
        for semilla in ctx.semillas(30):
            ejecutar_aco(g, origen, ctx.cm, ctx.cfg_variante[variante], esc.aristas_bloqueadas, semilla=semilla, variante=clave)
        t_run[variante] = (time.perf_counter() - t0) / 30
    n_esc = len(ESCENARIOS_DISPONIBLES)
    n_or = len(ctx.origenes)
    bench = sum(n_esc * n_or * ctx.n_bench * t for t in t_run.values())
    adapt = sum(len(ESCENARIOS_CON_CAMBIO) * n_or * ctx.n_adapt * t for t in t_run.values())
    conv = sum(len(ctx.exp["origenes_figuras"]) * ctx.n_bench * t for t in t_run.values())
    n_comb = sum(len(v) for v in ctx.exp["valores_sensibilidad"].values()) * len(ctx.exp["origenes_sensibilidad"])
    sens = n_comb * ctx.n_sens * t_run[V_CLASICO]
    total = bench + adapt + conv + sens
    return {"seg_por_corrida": t_run, "seg_benchmark": bench, "seg_adaptacion": adapt, "seg_convergencia": conv,
            "seg_sensibilidad": sens, "seg_total": total, "n_combinaciones_sensibilidad": n_comb}


def _version(modulo: str) -> str:
    try:
        return __import__(modulo).__version__
    except Exception:  # noqa: BLE001
        return "desconocida"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimar", action="store_true", help="solo estima el tiempo total")
    ap.add_argument("--corridas", type=int, default=None, help="corridas por experimento (solo pruebas rapidas)")
    ap.add_argument("--salida", type=Path, default=None, help="carpeta de salida (por defecto results/)")
    args = ap.parse_args()

    ctx = Contexto(n_corridas=args.corridas)
    oficial = args.salida is None and args.corridas is None
    destino = args.salida or (RAIZ_PROYECTO / "results")
    tope_s = float(ctx.exp["tope_minutos_plan"]) * 60

    est = estimar(ctx)
    _log(f"tiempo por corrida (s): {est['seg_por_corrida']}")
    _log(f"estimacion total: {est['seg_total'] / 60:.1f} min (benchmark {est['seg_benchmark'] / 60:.1f}, "
         f"adaptacion {est['seg_adaptacion'] / 60:.1f}, sensibilidad {est['seg_sensibilidad'] / 60:.1f})")
    reduccion = None
    if est["seg_total"] > tope_s:
        fijo = est["seg_total"] - est["seg_sensibilidad"]
        por_corrida = est["seg_sensibilidad"] / ctx.n_sens
        n_nuevo = max(1, int((tope_s - fijo) / por_corrida)) if tope_s > fijo else 1
        reduccion = {"experimento": "sensibilidad", "corridas_originales": ctx.n_sens, "corridas_usadas": n_nuevo,
                     "motivo": f"tiempo estimado {est['seg_total'] / 60:.1f} min > tope {tope_s / 60:.0f} min"}
        ctx.n_sens = n_nuevo
        _log(f"REDUCCION: sensibilidad pasa de {reduccion['corridas_originales']} a {n_nuevo} corridas")
    if args.estimar:
        return 0

    destino.mkdir(parents=True, exist_ok=True)
    if oficial:
        for viejo in list(destino.glob("*")):
            if viejo.is_file():
                viejo.unlink()

    inicio = time.perf_counter()
    try:
        df_dij = correr_dijkstra(ctx)
        df_bench, feromonas_normal = correr_benchmark(ctx)
        df_adapt = correr_adaptacion(ctx, df_bench, feromonas_normal)
        df_sens = correr_sensibilidad(ctx)
        df_conv = correr_convergencia(ctx)
        df_diag = correr_diagnostico_q(ctx)
    except ErrorCordura as e:
        (destino / "cordura.txt").write_text(f"FALLA DE CORDURA (posible bug)\n{e}\n", encoding="utf-8")
        _log(f"FALLA DE CORDURA: {e}")
        return 2
    df_evac, df_reparto, df_curvas = correr_evacuacion(ctx, df_dij, df_bench)
    tablas = tablas_resumen(df_bench, df_dij, df_adapt, df_sens, df_diag)
    duracion = time.perf_counter() - inicio

    archivos = {
        "benchmark_principal": df_bench, "dijkstra_referencia": df_dij, "adaptacion": df_adapt, "sensibilidad": df_sens,
        "diagnostico_q": df_diag, "convergencia": df_conv, "evacuacion_completa": df_evac, "evacuacion_curvas": df_curvas, "reparto_salidas_pe": df_reparto,
        **tablas,
    }
    for nombre, df in archivos.items():
        assert "variante" in df.columns, nombre
        df.to_csv(destino / f"{nombre}.csv", index=False)

    (destino / "cordura.txt").write_text(
        "Prueba de cordura: costo_ACO >= costo_Dijkstra - 1e-9 sobre el grafo de cada escenario\n"
        f"Corridas exitosas verificadas: {ctx.cordura_verificadas}\n"
        f"Violaciones: {len(ctx.cordura_violaciones)}\n"
        "Resultado: APROBADA\n",
        encoding="utf-8",
    )
    meta = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version, "plataforma": platform.platform(), "cpu": platform.processor() or platform.machine(),
        "librerias": {m: _version(m) for m in ("pandas", "numpy", "matplotlib", "streamlit", "PIL")},
        "semilla_base": ctx.semilla_base,
        "corridas": {"benchmark": ctx.n_bench, "adaptacion": ctx.n_adapt, "sensibilidad": ctx.n_sens,
                     "repeticiones_tiempo_dijkstra": ctx.n_rep_dijkstra},
        "origenes": len(ctx.origenes), "escenarios": ESCENARIOS_DISPONIBLES,
        "reduccion_aplicada": reduccion, "estimacion_previa_min": round(est["seg_total"] / 60, 2),
        "duracion_real_min": round(duracion / 60, 2), "corridas_verificadas_cordura": ctx.cordura_verificadas,
        "oficial": oficial,
    }
    (destino / "metadatos.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"listo en {duracion / 60:.1f} min; cordura: {ctx.cordura_verificadas} corridas verificadas, 0 violaciones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
