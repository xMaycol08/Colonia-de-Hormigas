"""App de evacuación de los bloques G y H (Streamlit, 4 pestañas).

Ejecutar con:
    streamlit run app/app.py

Solo llama a funciones de src/; no reimplementa algoritmos.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from aco import aco_iterativo, parametros_clasico  # noqa: E402
from agente import AgenteEvacuacion, EstadoPercibido  # noqa: E402
from benchmark import ejecutar_benchmark, resumir_benchmark  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from escenarios import ESCENARIOS_DISPONIBLES, ETIQUETA_ESCENARIO, ETIQUETA_VARIANTE, construir_escenario  # noqa: E402
from evacuacion import curva_acumulada, salida_de, simular_evacuacion  # noqa: E402
from grafo import CONFIG_ACO_PATH, CONFIG_MODELO_PATH, aplicar_congestion, cargar_configuracion, cargar_grafo  # noqa: E402
from metricas import tiempo_recorrido_ruta  # noqa: E402
from plano import COLORES_VARIANTE, dibujar_esquema, dibujar_rutas_plano, leyenda_tipos, posiciones_planta  # noqa: E402

RESULTS_DIR = RAIZ_PROYECTO / "results"
VARIANTES = {"ACO clásico": ("ACO clasico", "clasico"), "ACO guiado": ("ACO guiado", "guiado")}


@st.cache_resource
def cargar_datos():
    grafo = cargar_grafo()
    cm = cargar_configuracion(CONFIG_MODELO_PATH)
    ca = cargar_configuracion(CONFIG_ACO_PATH)
    return grafo, cm, ca


def config_variante(ca: dict, clave: str) -> dict:
    return parametros_clasico(ca) if clave == "clasico" else dict(ca)


def csv_guardado(nombre: str) -> pd.DataFrame | None:
    ruta = RESULTS_DIR / f"{nombre}.csv"
    return pd.read_csv(ruta) if ruta.exists() else None


def fmt_tiempo(s: float | None) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return "-"
    return f"{int(s // 60)} min {int(s % 60):02d} s"


def main() -> None:
    st.set_page_config(page_title="Evacuación G y H", layout="wide")
    st.title("Evacuación de los bloques G y H")

    grafo, cm, ca = cargar_datos()
    origenes = list(cm["poblacion_por_origen"])

    with st.sidebar:
        st.header("Parámetros")
        variante_ui = st.radio("Variante de ACO", list(VARIANTES))
        nombre_variante, clave_variante = VARIANTES[variante_ui]
        base = config_variante(ca, clave_variante)
        with st.form("parametros"):
            origen = st.selectbox("Origen", origenes, index=origenes.index("H403"))
            escenario_nombre = st.selectbox("Escenario", ESCENARIOS_DISPONIBLES, format_func=lambda n: ETIQUETA_ESCENARIO[n])
            alfa = st.slider("α (peso de la feromona)", 0.0, 5.0, float(base["alfa"]), 0.1, key=f"alfa_{clave_variante}")
            beta = st.slider("β (peso de la visibilidad)", 0.0, 5.0, float(base["beta"]), 0.1, key=f"beta_{clave_variante}")
            rho = st.slider("ρ (evaporación)", 0.05, 0.9, float(base["rho"]), 0.05, key=f"rho_{clave_variante}")
            n_hormigas = st.slider("Hormigas", 5, 100, int(base["n_hormigas"]), 5, key=f"hormigas_{clave_variante}")
            n_iteraciones = st.slider("Iteraciones (máximo)", 10, 300, int(base["n_iteraciones"]), 10, key=f"iter_{clave_variante}")
            pausa = st.slider("Pausa por iteración (s)", 0.0, 0.5, 0.05, 0.01)
            q_opciones = [0.1, 1.0, 10.0, 100.0, 1000.0]
            q_base = float(base["Q"]) if float(base["Q"]) in q_opciones else 1.0
            q_dep = st.select_slider("Q (constante de depósito)", q_opciones, value=q_base, key=f"q_{clave_variante}")
            ejecutar = st.form_submit_button("Ejecutar", type="primary")
        st.caption("Los cambios del formulario se aplican a todas las pestañas al pulsar Ejecutar.")

    config_aco = dict(base, alfa=alfa, beta=beta, rho=rho, n_hormigas=n_hormigas, n_iteraciones=n_iteraciones, Q=q_dep)
    escenario = construir_escenario(escenario_nombre, grafo, cm)
    grafo_esc = aplicar_congestion(grafo, escenario.congestion)
    params = dict(variante=clave_variante, origen=origen, escenario=escenario_nombre, alfa=alfa, beta=beta, rho=rho,
                  n_hormigas=n_hormigas, n_iteraciones=n_iteraciones, Q=q_dep)

    tab1, tab2, tab3, tab4 = st.tabs(["Simulación en vivo", "Comparación", "Benchmark", "Evacuación completa"])
    with tab1:
        pestana_vivo(grafo, grafo_esc, cm, config_aco, clave_variante, origen, escenario, pausa, ejecutar, params)
    with tab2:
        pestana_comparacion(grafo, grafo_esc, cm, config_aco, clave_variante, nombre_variante, origen, escenario)
    with tab3:
        pestana_benchmark(grafo, cm, ca, origenes)
    with tab4:
        pestana_evacuacion(grafo, cm, ca, escenario_nombre)


# --------------------------------------------------------------------------
# Pestaña 1
# --------------------------------------------------------------------------


def resumen_ruta(camino: list[str] | None) -> str:
    """Resumen legible de un camino: origen, tipo de tramo (pasillo, gradas) y nodos clave."""
    if not camino:
        return "sin ruta"
    etiquetas = []
    for i, nid in enumerate(camino):
        if i == 0:
            etq = nid
        elif nid.startswith("GRADAS-SUR"):
            etq = "gradas sur"
        elif nid.startswith("GRADAS-NORTE"):
            etq = "gradas norte"
        elif nid.startswith("PAS-"):
            etq = "pasillo"
        else:
            etq = nid
        if not etiquetas or etiquetas[-1] != etq:
            etiquetas.append(etq)
    return " → ".join(etiquetas)


AYUDA_CONTROLES = """
- **Origen**: nodo donde parte la persona (aula u oficina).
- **Escenario**: qué se bloquea (gradas, salidas) o se congestiona (la arista a la Salida A cuesta ×3).
- **Variante**: *clásico* (sin poda ni retroceso) o *guiado* (con poda, retroceso y heurística de distancia a la meta). Cada variante tiene sus propios valores base.
- **α**: peso de la feromona τ en la elección de cada paso. **β**: peso de la visibilidad η (1/costo en el clásico; 1/(costo + distancia a la meta) en el guiado). La visibilidad no tiene control propio: se calcula y β decide cuánto cuenta.
- **ρ**: fracción de feromona que se evapora cada iteración. **Q**: escala del depósito (cada hormiga suma Q ÷ costo del camino).
- **Hormigas**: recorridos por iteración. **Iteraciones**: máximo de rondas; el algoritmo se detiene antes si pasan 25 iteraciones seguidas sin mejorar (paciencia).
- **Pausa**: solo hace más lenta la animación; no cambia el resultado.
"""


def figura_vivo(grafo, cm, snap, origen, ruta_dijkstra, escenario, tau_rango, clave_ruta):
    pos = posiciones_planta(grafo, cm["altura_piso_m"])
    fig = plt.figure(figsize=(13, 5.6))
    ax1 = fig.add_axes((0.02, 0.05, 0.52, 0.88))
    ax2 = fig.add_axes((0.55, 0.02, 0.44, 0.92))
    dibujar_rutas_plano(ax1, grafo, pos, {"Dijkstra": ruta_dijkstra, clave_ruta: snap.mejor_camino_global}, origen=origen,
                        bloqueadas=escenario.aristas_bloqueadas, etiquetas_nodos=False)
    ax1.set_title("Plano (verde: Dijkstra; color: ACO; X roja: tramo bloqueado)", fontsize=9)
    leyenda_tipos(ax1, tipos=("aula", "pasillo", "gradas", "salida"), loc="upper left")
    dibujar_esquema(ax2, grafo, tau=snap.feromona, tau_rango=tau_rango, camino=snap.mejor_camino_global, bloqueadas=escenario.aristas_bloqueadas,
                    titulo="Feromona por nivel (amarillo: poca, rojo: mucha; punteado: mejor ruta)")
    return fig


def dibujar_vivo(grafo, cm, config_aco, res, historial, snap, contenedores) -> None:
    metricas, lienzo, curva = contenedores
    ref = res["ref"]
    with metricas.container():
        c = st.columns(5)
        c[0].metric("Iteración", snap.iteracion)
        c[1].metric("Mejor costo ACO", f"{snap.mejor_costo_global:.1f}" if snap.mejor_camino_global else "-")
        c[2].metric("Óptimo Dijkstra", f"{ref.costo:.1f}" if ref.tiene_ruta else "-")
        brecha = (snap.mejor_costo_global - ref.costo) / ref.costo * 100 if snap.mejor_camino_global and ref.tiene_ruta else None
        c[3].metric("Brecha", f"{brecha:.2f} %" if brecha is not None else "-")
        c[4].metric("Hormigas con ruta", f"{snap.hormigas_exitosas} de {int(config_aco['n_hormigas'])}")
    tau_vals = list(snap.feromona.values())
    fig = figura_vivo(grafo, cm, snap, res["params"]["origen"], ref.camino, res["escenario"],
                      (config_aco["tau_min"], max(max(tau_vals), config_aco["tau_min"] * 2)), VARIANTES_RUTA[res["params"]["variante"]])
    lienzo.pyplot(fig)
    plt.close(fig)
    if any(h[1] is not None for h in historial):
        curva.line_chart(pd.DataFrame({"mejor costo": [h[1] for h in historial]}, index=[h[0] for h in historial]))
    else:
        curva.empty()


def texto_conclusion(res, config_aco, nombre_variante) -> None:
    p, ref, final, historial = res["params"], res["ref"], res["final"], res["historial"]
    n_ejec = final.iteracion
    max_it = int(config_aco["n_iteraciones"])
    pac = int(config_aco["paciencia_estancamiento"])
    lanzadas = n_ejec * int(config_aco["n_hormigas"])
    exitosas = sum(h[2] for h in historial)
    if n_ejec >= max_it:
        motivo = f"se alcanzó el máximo de {max_it} iteraciones"
    else:
        if final.mejor_camino_global is None:
            motivo = (f"se detuvo en la iteración {n_ejec} de {max_it} por la regla de paciencia: {pac} iteraciones seguidas sin mejora "
                      "(sin ninguna ruta encontrada no hay mejora, así que se corta a las 25)")
        else:
            motivo = (f"se detuvo en la iteración {n_ejec} de {max_it} por la regla de paciencia: la mejor ruta apareció en la iteración "
                      f"{final.iteracion_mejor_global} y pasaron {pac} iteraciones sin mejorarla")
    st.subheader("Qué pasó")
    lineas = [f"**{nombre_variante}** desde **{p['origen']}**, escenario **{ETIQUETA_ESCENARIO[p['escenario']]}**: {motivo}.",
              f"De {lanzadas} hormigas lanzadas, {exitosas} llegaron a un punto de encuentro."]
    if final.mejor_camino_global is None:
        lineas.append("**Ninguna hormiga encontró ruta.** " + (
            "En el ACO clásico las hormigas entran a callejones (aulas, que solo tienen una conexión) y mueren porque esta variante no retrocede. "
            "Prueba el ACO guiado, o bájale β." if p["variante"] == "clasico" else "Revisa que el escenario no deje al origen sin salida."))
    else:
        brecha = (final.mejor_costo_global - ref.costo) / ref.costo * 100 if ref.tiene_ruta else None
        lineas.append(f"Mejor ruta de ACO: costo **{final.mejor_costo_global:.1f}**, hallada en la iteración **{final.iteracion_mejor_global}**, llega a **{final.punto_encuentro_global}**.")
        if brecha is not None:
            lineas.append("Coincide con el óptimo de Dijkstra." if brecha < 1e-6 else f"Es **{brecha:.2f} %** más cara que el óptimo de Dijkstra ({ref.costo:.1f}).")
        lineas.append("Ruta ACO: " + resumen_ruta(final.mejor_camino_global))
    lineas.append("Ruta Dijkstra: " + resumen_ruta(ref.camino) + f" (costo {ref.costo:.1f})" if ref.tiene_ruta else "Dijkstra: no hay ruta.")
    if res["escenario"].aristas_bloqueadas:
        lineas.append("Tramos bloqueados (X roja en el plano): " + ", ".join(sorted(res["escenario"].aristas_bloqueadas)) + ".")
    st.markdown("\n\n".join(lineas))
    if ref.camino and any(n.startswith("SALIDA-A") for n in ref.camino) and "SALIDA-B" in ref.camino:
        st.caption("La ruta pasa por la Salida A y sigue por el conector entre las dos salidas hasta la Salida B, de donde sale el camino al punto de encuentro PE-2; en el plano se dibuja como una línea que sube hacia la Salida B.")


def pestana_vivo(grafo, grafo_esc, cm, config_aco, clave_variante, origen, escenario, pausa, ejecutar, params) -> None:
    with st.expander("Qué es cada control"):
        st.markdown(AYUDA_CONTROLES)
    metricas = st.empty()
    lienzo = st.empty()
    curva = st.empty()
    nombre_variante = ETIQUETA_VARIANTE[VARIANTES_RUTA[clave_variante]]
    if ejecutar:
        ref = buscar_ruta(grafo_esc, origen, cm, escenario.aristas_bloqueadas)
        res = {"params": params, "ref": ref, "escenario": escenario, "historial": [], "final": None, "config": config_aco}
        paso = max(1, int(config_aco["n_iteraciones"]) // 25)
        for snap in aco_iterativo(grafo_esc, origen, cm, config_aco, escenario.aristas_bloqueadas, variante=clave_variante):
            res["historial"].append((snap.iteracion, snap.mejor_costo_global if snap.mejor_camino_global else None, snap.hormigas_exitosas))
            res["final"] = snap
            if snap.iteracion == 1 or snap.iteracion % paso == 0:
                dibujar_vivo(grafo, cm, config_aco, res, res["historial"], snap, (metricas, lienzo, curva))
                if pausa > 0:
                    time.sleep(pausa)
        if res["final"] is not None:
            dibujar_vivo(grafo, cm, config_aco, res, res["historial"], res["final"], (metricas, lienzo, curva))
            st.session_state["vivo"] = res
    res = st.session_state.get("vivo")
    if res is None:
        st.info("Elige los parámetros y pulsa Ejecutar.")
        return
    if not ejecutar:
        if res["params"] != params:
            st.warning("Esta simulación corresponde a otros parámetros (variante, origen, escenario o valores). Pulsa Ejecutar para actualizarla.")
        dibujar_vivo(grafo, cm, res["config"], res, res["historial"], res["final"], (metricas, lienzo, curva))
    texto_conclusion(res, res["config"], ETIQUETA_VARIANTE[VARIANTES_RUTA[res["params"]["variante"]]])


# --------------------------------------------------------------------------
# Pestaña 2
# --------------------------------------------------------------------------


def pestana_comparacion(grafo, grafo_esc, cm, config_aco, clave_variante, nombre_variante, origen, escenario) -> None:
    agente = AgenteEvacuacion(grafo, cm, config_aco, origen)
    agente.percibir(EstadoPercibido(aristas_bloqueadas=escenario.aristas_bloqueadas, congestion=escenario.congestion))
    decision = agente.decidir(comparar_con_dijkstra=True, usar_warm_start=False, semilla=int(config_aco["semilla"]), variante=clave_variante)
    aco, dij = decision.resultado_aco, decision.resultado_dijkstra

    t0 = time.perf_counter()
    for _ in range(20):
        buscar_ruta(grafo_esc, origen, cm, escenario.aristas_bloqueadas)
    t_dij = (time.perf_counter() - t0) / 20 * 1000

    def fila(nombre, costo, camino, t_ms, iteracion):
        if not camino:
            return {"Algoritmo": nombre, "Costo": "sin ruta", "Tiempo de cómputo (ms)": f"{t_ms:.2f}", "Iteración": "-", "Salida": "-", "Punto de encuentro": "-", "Recorrido": "-"}
        return {"Algoritmo": nombre, "Costo": f"{costo:.2f}", "Tiempo de cómputo (ms)": f"{t_ms:.2f}", "Iteración": str(iteracion),
                "Salida": salida_de(grafo, camino), "Punto de encuentro": camino[-1], "Recorrido": fmt_tiempo(tiempo_recorrido_ruta(grafo_esc, camino, cm))}

    tabla = pd.DataFrame([fila("Dijkstra", dij.costo, dij.camino, t_dij, "-"), fila(ETIQUETA_VARIANTE[nombre_variante], aco.mejor_costo, aco.mejor_camino, aco.tiempo_s * 1000, aco.iteracion_mejor_solucion)])
    izq, der = st.columns([1.2, 1])
    with izq:
        pos = posiciones_planta(grafo, cm["altura_piso_m"])
        fig, ax = plt.subplots(figsize=(9, 5.4))
        clave_ruta = VARIANTES_RUTA[clave_variante]
        dibujar_rutas_plano(ax, grafo, pos, {"Dijkstra": dij.camino, clave_ruta: aco.mejor_camino}, origen=origen, bloqueadas=escenario.aristas_bloqueadas)
        leyenda_tipos(ax, tipos=("aula", "pasillo", "gradas", "salida"), loc="upper right")
        st.pyplot(fig)
        plt.close(fig)
    with der:
        st.dataframe(tabla, hide_index=True, use_container_width=True)
        if aco.tiene_ruta and dij.tiene_ruta:
            st.metric("Brecha", f"{(aco.mejor_costo - dij.costo) / dij.costo * 100:.2f} %")
        st.caption("Ruta " + ETIQUETA_VARIANTE[nombre_variante] + ": " + (" > ".join(aco.mejor_camino) if aco.mejor_camino else "sin ruta"))
        st.caption("Ruta Dijkstra: " + " > ".join(dij.camino or []))
    if not aco.tiene_ruta:
        st.markdown(f"**Qué pasó:** {ETIQUETA_VARIANTE[nombre_variante]} no encontró ruta con esta semilla ({int(config_aco['semilla'])}); Dijkstra sí ({dij.costo:.1f}). "
                    "Prueba otra variante o cambia los parámetros.")
    elif aco.mejor_costo - dij.costo < 1e-6:
        st.markdown(f"**Qué pasó:** {ETIQUETA_VARIANTE[nombre_variante]} halló la misma ruta óptima que Dijkstra (costo {dij.costo:.1f}) en la iteración {aco.iteracion_mejor_solucion}, "
                    f"pero tardó {aco.tiempo_s * 1000:.1f} ms frente a {t_dij:.2f} ms de Dijkstra.")
    else:
        st.markdown(f"**Qué pasó:** {ETIQUETA_VARIANTE[nombre_variante]} halló una ruta {(aco.mejor_costo - dij.costo) / dij.costo * 100:.1f} % más cara que la óptima. "
                    f"Ruta ACO: {resumen_ruta(aco.mejor_camino)}. Ruta Dijkstra: {resumen_ruta(dij.camino)}.")


VARIANTES_RUTA = {"clasico": "ACO clasico", "guiado": "ACO guiado"}


# --------------------------------------------------------------------------
# Pestaña 3
# --------------------------------------------------------------------------

TABLAS_GUARDADAS = {
    "Resumen del benchmark": "resumen_benchmark",
    "Resumen por origen": "resumen_benchmark_por_origen",
    "Referencia Dijkstra": "resumen_dijkstra",
    "Adaptación (frío y warm start)": "resumen_adaptacion",
    "Adaptación: reducción": "resumen_adaptacion_reduccion",
    "Sensibilidad": "resumen_sensibilidad",
    "Evacuación completa": "evacuacion_completa",
    "Reparto por salida y punto de encuentro": "reparto_salidas_pe",
}


def pestana_benchmark(grafo, cm, ca, origenes) -> None:
    st.subheader("Resultados guardados")
    tabla = st.selectbox("Tabla", list(TABLAS_GUARDADAS))
    df = csv_guardado(TABLAS_GUARDADAS[tabla])
    if df is None:
        st.write("Sin resultados guardados.")
    else:
        st.dataframe(df, hide_index=True, use_container_width=True)

    figuras = sorted((RESULTS_DIR / "figuras").glob("*.png")) if (RESULTS_DIR / "figuras").exists() else []
    if figuras:
        nombre = st.selectbox("Figura", [f.name for f in figuras])
        st.image(str(RESULTS_DIR / "figuras" / nombre), use_container_width=True)
    gifs = sorted((RESULTS_DIR / "animaciones").glob("*.gif")) if (RESULTS_DIR / "animaciones").exists() else []
    if gifs:
        nombre_gif = st.selectbox("Animación", [g.name for g in gifs])
        st.image(str(RESULTS_DIR / "animaciones" / nombre_gif))

    st.subheader("Re-ejecutar")
    c1, c2, c3, c4 = st.columns(4)
    escenarios_sel = c1.multiselect("Escenarios", ESCENARIOS_DISPONIBLES, default=["Normal"], format_func=lambda n: ETIQUETA_ESCENARIO[n])
    origenes_sel = c2.multiselect("Orígenes", origenes, default=["H-PB-OFICINAS_CC", "H203", "H403"])
    variantes_sel = c3.multiselect("Variantes", list(VARIANTES), default=list(VARIANTES))
    n_corridas = c4.slider("Corridas", 1, 30, 5)
    if st.button("Re-ejecutar benchmark") and escenarios_sel and origenes_sel and variantes_sel:
        escenarios = [construir_escenario(n, grafo, cm) for n in escenarios_sel]
        partes = []
        with st.spinner("Ejecutando"):
            for nombre_ui in variantes_sel:
                nombre_variante, clave = VARIANTES[nombre_ui]
                df_v, _ = ejecutar_benchmark(grafo, origenes_sel, escenarios, cm, config_variante(ca, clave), n_corridas,
                                             guardar_csv=False, variante=clave, semilla_base=int(ca["semilla_base_experimentos"]))
                partes.append(df_v)
        df_nuevo = pd.concat(partes, ignore_index=True)
        st.dataframe(resumir_benchmark(df_nuevo), hide_index=True, use_container_width=True)
        fig, ax = plt.subplots(figsize=(9, 3.6))
        for i, (v, g) in enumerate(df_nuevo[df_nuevo["tiene_ruta"]].groupby("variante")):
            ax.boxplot(g["brecha_pct"], positions=[i], widths=0.5, patch_artist=True, boxprops=dict(facecolor=COLORES_VARIANTE[v], alpha=0.6))
        ax.set_xticks(range(df_nuevo["variante"].nunique()))
        ax.set_xticklabels(sorted(df_nuevo["variante"].unique()))
        ax.set_ylabel("Brecha (%)")
        st.pyplot(fig)
        plt.close(fig)


# --------------------------------------------------------------------------
# Pestaña 4
# --------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def rutas_evacuacion(escenario_nombre: str, algoritmo: str, semilla_base: int) -> dict[str, list[str] | None]:
    grafo, cm, ca = cargar_datos()
    esc = construir_escenario(escenario_nombre, grafo, cm)
    g = aplicar_congestion(grafo, esc.congestion)
    rutas = {}
    for origen in cm["poblacion_por_origen"]:
        if algoritmo == "Dijkstra":
            rutas[origen] = buscar_ruta(g, origen, cm, esc.aristas_bloqueadas).camino
        else:
            clave = VARIANTES[algoritmo][1]
            from aco import ejecutar_aco  # noqa: PLC0415

            for i in range(30):
                r = ejecutar_aco(g, origen, cm, config_variante(ca, clave), esc.aristas_bloqueadas, semilla=semilla_base + i, variante=clave)
                if r.tiene_ruta:
                    rutas[origen] = r.mejor_camino
                    break
            else:
                rutas[origen] = None
    return rutas


def pestana_evacuacion(grafo, cm, ca, escenario_nombre) -> None:
    algoritmo = st.radio("Algoritmo", ["Dijkstra", *VARIANTES], horizontal=True)
    g = aplicar_congestion(grafo, construir_escenario(escenario_nombre, grafo, cm).congestion)
    r = simular_evacuacion(g, rutas_evacuacion(escenario_nombre, algoritmo, int(ca["semilla_base_experimentos"])), cm)

    c = st.columns(4)
    c[0].metric("Primera persona", fmt_tiempo(r["primera_s"]))
    c[1].metric("Última persona", fmt_tiempo(r["ultima_s"]))
    c[2].metric("Personas con ruta", f"{len(r['llegadas'])} de {r['poblacion_total']}")
    c[3].metric("Sin ruta", r["sin_ruta"])

    izq, der = st.columns([1.5, 1])
    with izq:
        curva = curva_acumulada(r["llegadas"])
        fig, ax = plt.subplots(figsize=(8, 4))
        if curva:
            t, n = zip(*curva)
            ax.plot(t, n, color="#1f5fbf", lw=2)
            ax.axvline(r["primera_s"], color="#2e7d32", ls="--", lw=1)
            ax.axvline(r["ultima_s"], color="#b71c1c", ls="--", lw=1)
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Personas en el punto de encuentro")
        st.pyplot(fig)
        plt.close(fig)
    with der:
        st.dataframe(pd.DataFrame({"Salida": list(r["por_salida"]), "Personas": list(r["por_salida"].values())}), hide_index=True)
        st.dataframe(pd.DataFrame({"Punto de encuentro": list(r["por_pe"]), "Personas": list(r["por_pe"].values())}), hide_index=True)
    if r["primera_s"] is None:
        st.markdown("**Qué pasó:** con este algoritmo y escenario ningún origen encontró ruta.")
    else:
        sin = f" {r['sin_ruta']} personas no tienen ruta (su origen no encontró camino)." if r["sin_ruta"] else ""
        st.markdown(f"**Qué pasó:** con {algoritmo} la primera persona llega a los {fmt_tiempo(r['primera_s'])} y la última a los {fmt_tiempo(r['ultima_s'])} desde la alerta "
                    f"(60 s de reacción + recorrido + 1 s por cada persona siguiente del mismo origen).{sin} No se modelan colas.")


if __name__ == "__main__":
    main()
