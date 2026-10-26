"""App interactiva de evacuacion (Fase 3): Streamlit, 4 pestanas.

Ejecutar con:
    streamlit run app/app.py

Esta app SOLO llama a funciones de src/ (dijkstra, aco, agente, metricas,
benchmark, grafo, costos); no reimplementa ningun algoritmo aqui, solo
visualizacion y orquestacion de la interfaz.
"""

from __future__ import annotations

import io
import sys
import time
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from PIL import Image

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import (  # noqa: E402
    Grafo,
    cargar_grafo,
    cargar_configuracion,
    aplicar_congestion,
    CONFIG_MODELO_PATH,
    CONFIG_ACO_PATH,
)
from dijkstra import buscar_ruta  # noqa: E402
from aco import aco_iterativo, ejecutar_aco  # noqa: E402
from agente import AgenteEvacuacion, EstadoPercibido, generar_instrucciones  # noqa: E402
from metricas import tiempo_recorrido_ruta, calcular_metricas_todos_los_origenes  # noqa: E402
from benchmark import ejecutar_benchmark, resumir_benchmark, barrido_sensibilidad, Escenario, RESULTS_DIR  # noqa: E402

ESCENARIOS_DISPONIBLES = [
    "Normal",
    "Gradas Norte bloqueadas",
    "Gradas Sur bloqueadas",
    "Salida A bloqueada",
    "Salida B bloqueada",
    "Congestion en una salida",
]

COLOR_ACO = "#1565c0"
COLOR_DIJKSTRA = "#2e7d32"
COLOR_BLOQUEADA = "#c62828"


# --------------------------------------------------------------------------
# Carga de datos (cacheada)
# --------------------------------------------------------------------------


@st.cache_resource
def cargar_datos():
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco_default = cargar_configuracion(CONFIG_ACO_PATH)
    return grafo, config_modelo, config_aco_default


ID_ARISTA_GRADAS_SUR_SALIDA_A = "GRADAS-SUR-PB-SALIDA-A"
ID_ARISTA_GRADAS_NORTE_SALIDA_B = "GRADAS-NORTE-PB-SALIDA-B"


def construir_escenario(nombre: str, grafo: Grafo, config_modelo: dict) -> Escenario:
    """Traduce el nombre de un escenario de la UI a aristas bloqueadas / congestion."""
    if nombre == "Gradas Norte bloqueadas":
        bloqueadas = frozenset(aid for aid in grafo.aristas_por_id if aid.startswith("GRADAS-NORTE-"))
        return Escenario(nombre, bloqueadas, {})
    if nombre == "Gradas Sur bloqueadas":
        bloqueadas = frozenset(aid for aid in grafo.aristas_por_id if aid.startswith("GRADAS-SUR-"))
        return Escenario(nombre, bloqueadas, {})
    if nombre == "Salida A bloqueada":
        return Escenario(nombre, frozenset({ID_ARISTA_GRADAS_SUR_SALIDA_A}), {})
    if nombre == "Salida B bloqueada":
        return Escenario(nombre, frozenset({ID_ARISTA_GRADAS_NORTE_SALIDA_B}), {})
    if nombre == "Congestion en una salida":
        return Escenario(nombre, frozenset(), {ID_ARISTA_GRADAS_SUR_SALIDA_A: config_modelo["factor_congestion_demo"]})
    return Escenario("Normal", frozenset(), {})


# --------------------------------------------------------------------------
# Dibujo del grafo
# --------------------------------------------------------------------------


def opciones_vista(config_modelo: dict) -> list[str]:
    niveles = config_modelo["niveles"]
    opciones = ["General"]
    for nivel in niveles:
        opciones.append(f"Nivel {nivel}")
    return opciones


def _nodos_y_aristas_para_vista(grafo: Grafo, vista: str):
    if vista == "General":
        nodos = list(grafo.nodos_por_id.values())
    else:
        nivel = vista.replace("Nivel ", "")
        piso = 0 if nivel == "PB" else int(nivel)
        nodos = [n for n in grafo.nodos_por_id.values() if n["bloque"] in ("H", "G", "compartido") and n["piso"] == piso]
        if piso == 0:
            nodos += [n for n in grafo.nodos_por_id.values() if n["tipo"] == "salida"]
    ids = {n["id"] for n in nodos}
    aristas = [a for a in grafo.aristas_por_id.values() if a["desde"] in ids and a["hasta"] in ids]
    return nodos, aristas


def _tramos_de_camino(camino: list[str] | None) -> list[tuple[str, str]]:
    if not camino:
        return []
    return list(zip(camino, camino[1:]))


def dibujar_grafo(
    grafo: Grafo,
    vista: str,
    tau: dict[str, float] | None = None,
    camino_aco: list[str] | None = None,
    camino_dijkstra: list[str] | None = None,
    aristas_bloqueadas: frozenset[str] = frozenset(),
    nodos_podados: frozenset[str] = frozenset(),
) -> plt.Figure:
    """Dibuja el grafo (o un piso) con feromona como mapa de calor, rutas resaltadas y bloqueos."""
    nodos, aristas = _nodos_y_aristas_para_vista(grafo, vista)

    fig, ax = plt.subplots(figsize=(8, 6.5))

    tau_vals = [v for k, v in (tau or {}).items()]
    tau_min_v, tau_max_v = (min(tau_vals), max(tau_vals)) if tau_vals else (0.0, 1.0)

    tramos_aco = set(_tramos_de_camino(camino_aco)) | set((b, a) for a, b in _tramos_de_camino(camino_aco))
    tramos_dij = set(_tramos_de_camino(camino_dijkstra)) | set((b, a) for a, b in _tramos_de_camino(camino_dijkstra))

    for arista in aristas:
        n1 = grafo.nodos_por_id[arista["desde"]]
        n2 = grafo.nodos_por_id[arista["hasta"]]
        if n1["x_m"] is None or n2["x_m"] is None:
            continue
        xs, ys = [n1["x_m"], n2["x_m"]], [n1["y_m"], n2["y_m"]]

        if arista["id"] in aristas_bloqueadas:
            ax.plot(xs, ys, color=COLOR_BLOQUEADA, linestyle=":", linewidth=2.2, zorder=2)
            continue

        if tau is not None and arista["id"] in tau:
            t = tau[arista["id"]]
            intensidad = (t - tau_min_v) / (tau_max_v - tau_min_v) if tau_max_v > tau_min_v else 0.3
            color = plt.cm.YlOrRd(0.25 + 0.75 * intensidad)
            ancho = 0.6 + 3.0 * intensidad
        else:
            color, ancho = "#c9c9c9", 0.6

        ax.plot(xs, ys, color=color, linewidth=ancho, zorder=1)

    if camino_dijkstra:
        for a, b in _tramos_de_camino(camino_dijkstra):
            n1, n2 = grafo.nodos_por_id.get(a), grafo.nodos_por_id.get(b)
            if not n1 or not n2 or n1["x_m"] is None or n2["x_m"] is None:
                continue
            ax.plot([n1["x_m"], n2["x_m"]], [n1["y_m"], n2["y_m"]], color=COLOR_DIJKSTRA, linestyle="--", linewidth=2.3, zorder=3)

    if camino_aco:
        for a, b in _tramos_de_camino(camino_aco):
            n1, n2 = grafo.nodos_por_id.get(a), grafo.nodos_por_id.get(b)
            if not n1 or not n2 or n1["x_m"] is None or n2["x_m"] is None:
                continue
            ax.plot([n1["x_m"], n2["x_m"]], [n1["y_m"], n2["y_m"]], color=COLOR_ACO, linewidth=2.8, zorder=4)

    for n in nodos:
        if n["x_m"] is None or n["y_m"] is None:
            continue
        if n["tipo"] == "punto_encuentro":
            ax.scatter(n["x_m"], n["y_m"], marker="*", s=260, color="gold", edgecolor="black", zorder=5)
            ax.annotate(n["nombre"], (n["x_m"], n["y_m"]), fontsize=7, xytext=(4, 4), textcoords="offset points", zorder=6)
        elif n["id"] in nodos_podados:
            ax.scatter(n["x_m"], n["y_m"], marker="x", s=15, color="#d0d0d0", zorder=1)
        elif n["tipo"] == "salida":
            ax.scatter(n["x_m"], n["y_m"], marker="s", s=80, color="#424242", zorder=5)
            ax.annotate(n["id"], (n["x_m"], n["y_m"]), fontsize=7, xytext=(4, 4), textcoords="offset points", zorder=6)
        else:
            ax.scatter(n["x_m"], n["y_m"], marker="o", s=22, color="#424242", zorder=4)

    ax.set_title(f"Vista: {vista}")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linewidth=0.3, alpha=0.4)
    fig.tight_layout()
    return fig


def figura_a_imagen(fig: plt.Figure) -> Image.Image:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title="Evacuacion G/H - ESPE", layout="wide")
    st.title("Simulador de evacuacion - Bloques G y H (ESPE Matriz)")

    grafo, config_modelo, config_aco_default = cargar_datos()
    origenes_todos = list(config_modelo["poblacion_por_origen"].keys())

    # ---------------- Barra lateral ----------------
    with st.sidebar:
        st.header("Controles")
        origen = st.selectbox("Origen", origenes_todos, index=0)
        escenario_nombre = st.selectbox("Escenario", ESCENARIOS_DISPONIBLES, index=0)

        st.markdown("### Parametros de ACO")
        alfa = st.slider("alfa", 0.1, 5.0, float(config_aco_default["alfa"]), 0.1)
        beta = st.slider("beta", 0.1, 5.0, float(config_aco_default["beta"]), 0.1)
        rho = st.slider("rho (evaporacion)", 0.05, 0.9, float(config_aco_default["rho"]), 0.05)
        n_hormigas = st.slider("n_hormigas", 5, 100, int(config_aco_default["n_hormigas"]), 5)
        n_iteraciones = st.slider("n_iteraciones", 10, 300, int(config_aco_default["n_iteraciones"]), 10)
        velocidad = st.slider("Velocidad de animacion (s de pausa por iteracion)", 0.0, 0.5, 0.05, 0.01)

        ejecutar = st.button("Ejecutar", type="primary")

    config_aco_actual = dict(config_aco_default)
    config_aco_actual.update({"alfa": alfa, "beta": beta, "rho": rho, "n_hormigas": n_hormigas, "n_iteraciones": n_iteraciones})
    st.session_state["config_aco_actual"] = config_aco_actual
    st.session_state["origen_actual"] = origen
    st.session_state["escenario_actual"] = escenario_nombre

    escenario = construir_escenario(escenario_nombre, grafo, config_modelo)
    grafo_escenario = aplicar_congestion(grafo, escenario.congestion)

    tab1, tab2, tab3, tab4 = st.tabs(["Simulacion en vivo", "Comparacion", "Benchmark", "Evacuacion completa"])

    with tab1:
        _pestana_simulacion_vivo(grafo_escenario, origen, escenario, config_modelo, config_aco_actual, velocidad, ejecutar)

    with tab2:
        _pestana_comparacion(grafo_escenario, origen, escenario, config_modelo, config_aco_actual)

    with tab3:
        _pestana_benchmark(grafo, origenes_todos, config_modelo, config_aco_actual)

    with tab4:
        _pestana_evacuacion_completa(grafo_escenario, escenario, config_modelo)


def _pestana_simulacion_vivo(grafo, origen, escenario, config_modelo, config_aco, velocidad, ejecutar) -> None:
    st.subheader("Simulacion en vivo de ACO")

    vista = st.selectbox("Vista del grafo", opciones_vista(config_modelo), key="vista_tab1")
    mostrar_dijkstra = st.checkbox("Superponer ruta optima de Dijkstra", value=True)

    placeholder_metricas = st.empty()
    placeholder_grafo = st.empty()
    placeholder_convergencia = st.empty()

    if ejecutar:
        resultado_dijkstra = buscar_ruta(grafo, origen, config_modelo, escenario.aristas_bloqueadas)
        historial = []
        frames = []

        for snap in aco_iterativo(grafo, origen, config_modelo, config_aco, escenario.aristas_bloqueadas):
            historial.append(snap)

            with placeholder_metricas.container():
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Iteracion", snap.iteracion)
                costo_txt = f"{snap.mejor_costo_global:.1f}" if snap.mejor_costo_global < float("inf") else "sin ruta"
                c2.metric("Mejor costo ACO", costo_txt)
                c3.metric("Optimo Dijkstra", f"{resultado_dijkstra.costo:.1f}" if resultado_dijkstra.tiene_ruta else "sin ruta")
                if resultado_dijkstra.tiene_ruta and snap.mejor_costo_global < float("inf"):
                    brecha = (snap.mejor_costo_global - resultado_dijkstra.costo) / resultado_dijkstra.costo * 100
                    c4.metric("Brecha %", f"{brecha:+.1f}%")
                else:
                    c4.metric("Brecha %", "n/a")
                c5.metric("Hormigas exitosas", f"{snap.hormigas_exitosas}")

            fig = dibujar_grafo(
                grafo, vista, tau=snap.feromona, camino_aco=snap.mejor_camino_global,
                camino_dijkstra=resultado_dijkstra.camino if mostrar_dijkstra else None,
                aristas_bloqueadas=escenario.aristas_bloqueadas, nodos_podados=snap.nodos_podados,
            )
            placeholder_grafo.pyplot(fig)
            frames.append(figura_a_imagen(fig))
            plt.close(fig)

            df_conv = pd.DataFrame(
                [
                    {
                        "iteracion": h.iteracion,
                        "mejor_costo": h.mejor_costo_global if h.mejor_costo_global < float("inf") else None,
                        "costo_promedio": h.costo_promedio,
                    }
                    for h in historial
                ]
            ).set_index("iteracion")
            placeholder_convergencia.line_chart(df_conv)

            if velocidad > 0:
                time.sleep(velocidad)

        st.session_state["tab1_historial"] = historial
        st.session_state["tab1_dijkstra"] = resultado_dijkstra
        st.session_state["tab1_frames"] = frames
        st.session_state["tab1_grafo_escenario"] = grafo
        st.session_state["tab1_escenario"] = escenario
        st.session_state["tab1_vista"] = vista

    elif "tab1_historial" in st.session_state:
        historial = st.session_state["tab1_historial"]
        resultado_dijkstra = st.session_state["tab1_dijkstra"]
        ultimo = historial[-1]

        with placeholder_metricas.container():
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Iteracion", ultimo.iteracion)
            c2.metric("Mejor costo ACO", f"{ultimo.mejor_costo_global:.1f}" if ultimo.mejor_costo_global < float("inf") else "sin ruta")
            c3.metric("Optimo Dijkstra", f"{resultado_dijkstra.costo:.1f}" if resultado_dijkstra.tiene_ruta else "sin ruta")
            if resultado_dijkstra.tiene_ruta and ultimo.mejor_costo_global < float("inf"):
                brecha = (ultimo.mejor_costo_global - resultado_dijkstra.costo) / resultado_dijkstra.costo * 100
                c4.metric("Brecha %", f"{brecha:+.1f}%")
            else:
                c4.metric("Brecha %", "n/a")
            c5.metric("Hormigas exitosas", f"{ultimo.hormigas_exitosas}")

        fig = dibujar_grafo(
            grafo, vista, tau=ultimo.feromona, camino_aco=ultimo.mejor_camino_global,
            camino_dijkstra=resultado_dijkstra.camino if mostrar_dijkstra else None,
            aristas_bloqueadas=escenario.aristas_bloqueadas, nodos_podados=ultimo.nodos_podados,
        )
        placeholder_grafo.pyplot(fig)
        plt.close(fig)

        df_conv = pd.DataFrame(
            [{"iteracion": h.iteracion, "mejor_costo": h.mejor_costo_global if h.mejor_costo_global < float("inf") else None, "costo_promedio": h.costo_promedio} for h in historial]
        ).set_index("iteracion")
        placeholder_convergencia.line_chart(df_conv)
    else:
        st.info("Ajusta los parametros en la barra lateral y presiona 'Ejecutar'.")

    st.markdown("### Exportar")
    col_gif, col_png = st.columns(2)
    with col_gif:
        if st.button("Exportar GIF de esta corrida"):
            frames = st.session_state.get("tab1_frames")
            if not frames:
                st.warning("Ejecuta una corrida primero.")
            else:
                RESULTS_DIR.mkdir(exist_ok=True)
                ruta_gif = RESULTS_DIR / f"aco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif"
                frames[0].save(ruta_gif, save_all=True, append_images=frames[1:], duration=150, loop=0)
                st.success(f"GIF guardado en {ruta_gif}")
    with col_png:
        if st.session_state.get("tab1_historial") and st.button("Guardar captura PNG actual"):
            ultimo = st.session_state["tab1_historial"][-1]
            fig = dibujar_grafo(
                grafo, vista, tau=ultimo.feromona, camino_aco=ultimo.mejor_camino_global,
                nodos_podados=ultimo.nodos_podados, aristas_bloqueadas=escenario.aristas_bloqueadas,
            )
            RESULTS_DIR.mkdir(exist_ok=True)
            ruta_png = RESULTS_DIR / f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            fig.savefig(ruta_png, dpi=150)
            plt.close(fig)
            st.success(f"Captura guardada en {ruta_png}")


def _pestana_comparacion(grafo, origen, escenario, config_modelo, config_aco) -> None:
    st.subheader(f"Comparacion Dijkstra vs ACO - origen: {origen}, escenario: {escenario.nombre}")

    t0 = time.perf_counter()
    resultado_dijkstra = buscar_ruta(grafo, origen, config_modelo, escenario.aristas_bloqueadas)
    tiempo_dijkstra_ms = (time.perf_counter() - t0) * 1000

    resultado_aco = ejecutar_aco(grafo, origen, config_modelo, config_aco, escenario.aristas_bloqueadas)

    def _fila(nombre, resultado, tiempo_ms, nodos_o_iter):
        if not resultado.tiene_ruta:
            return {
                "Algoritmo": nombre, "Costo": "sin ruta", "Tiempo caminata (s)": "-",
                "Tiempo computo (ms)": f"{tiempo_ms:.2f}", "Nodos expandidos / iteraciones": nodos_o_iter,
                "Brecha %": "n/a", "Punto de encuentro": "-",
            }
        tiempo_caminata = tiempo_recorrido_ruta(grafo, resultado.camino if nombre == "Dijkstra" else resultado.mejor_camino, config_modelo)
        brecha = "-"
        if nombre == "ACO" and resultado_dijkstra.tiene_ruta:
            brecha = f"{(resultado.mejor_costo - resultado_dijkstra.costo) / resultado_dijkstra.costo * 100:+.1f}%"
        return {
            "Algoritmo": nombre,
            "Costo": round(resultado.costo if nombre == "Dijkstra" else resultado.mejor_costo, 2),
            "Tiempo caminata (s)": round(tiempo_caminata, 1),
            "Tiempo computo (ms)": round(tiempo_ms, 2),
            "Nodos expandidos / iteraciones": nodos_o_iter,
            "Brecha %": brecha,
            "Punto de encuentro": resultado.punto_encuentro if nombre == "Dijkstra" else resultado.punto_encuentro,
        }

    tabla = pd.DataFrame(
        [
            _fila("Dijkstra", resultado_dijkstra, tiempo_dijkstra_ms, resultado_dijkstra.nodos_expandidos),
            _fila("ACO", resultado_aco, resultado_aco.tiempo_s * 1000, resultado_aco.iteracion_mejor_solucion),
        ]
    )
    st.dataframe(tabla, hide_index=True, width="stretch")

    st.markdown("### Instrucciones de ruta (agente)")
    if resultado_aco.tiene_ruta:
        for paso in generar_instrucciones(grafo, resultado_aco.mejor_camino):
            st.write(f"- {paso}")
        tiempo_total = tiempo_recorrido_ruta(grafo, resultado_aco.mejor_camino, config_modelo)
        st.caption(f"Tiempo estimado de caminata: {tiempo_total:.1f} s (sin incluir tiempo de reaccion)")
    else:
        st.warning("ACO no encontro ruta en esta corrida.")


def _pestana_benchmark(grafo, origenes_repr, config_modelo, config_aco_actual) -> None:
    st.subheader("Benchmark: Dijkstra vs ACO")

    origenes_sel = st.multiselect("Origenes", origenes_repr, default=origenes_repr[:2])
    escenarios_sel = st.multiselect("Escenarios", ESCENARIOS_DISPONIBLES, default=["Normal"])
    n_corridas = st.number_input("N corridas de ACO por combinacion", min_value=1, max_value=200, value=30)

    if st.button("Ejecutar benchmark"):
        if not origenes_sel or not escenarios_sel:
            st.warning("Selecciona al menos un origen y un escenario.")
        else:
            escenarios_obj = [construir_escenario(n, grafo, config_modelo) for n in escenarios_sel]
            with st.spinner("Corriendo benchmark..."):
                df, ruta_csv = ejecutar_benchmark(grafo, origenes_sel, escenarios_obj, config_modelo, config_aco_actual, n_corridas)
            st.session_state["benchmark_df"] = df
            st.session_state["benchmark_csv"] = ruta_csv
            st.success(f"Benchmark completo ({len(df)} corridas). Guardado en {ruta_csv}")

    if "benchmark_df" in st.session_state:
        df = st.session_state["benchmark_df"]
        resumen = resumir_benchmark(df)
        st.markdown("#### Resumen por origen/escenario")
        st.dataframe(resumen, hide_index=True, width="stretch")

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV de corridas individuales", csv_bytes, file_name="benchmark.csv", mime="text/csv")

        st.markdown("#### Distribucion de costos (ACO, corridas exitosas)")
        fig, ax = plt.subplots(figsize=(8, 4))
        grupos = df[df["tiene_ruta"]].groupby(["origen", "escenario"])
        etiquetas = []
        datos = []
        for (origen, escenario), grupo in grupos:
            etiquetas.append(f"{origen}\n{escenario}")
            datos.append(grupo["costo"].dropna().tolist())
        if datos:
            ax.boxplot(datos, tick_labels=etiquetas)
            ax.set_ylabel("Costo")
            plt.xticks(rotation=45, ha="right", fontsize=7)
            fig.tight_layout()
            st.pyplot(fig)
        plt.close(fig)

        st.markdown("#### Tiempo de computo: Dijkstra vs ACO (promedio por origen/escenario)")
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        resumen_tiempos = resumen.set_index(["origen", "escenario"])["tiempo_ms_medio"]
        resumen_tiempos.plot(kind="bar", ax=ax2, color=COLOR_ACO)
        ax2.set_ylabel("Tiempo ACO promedio (ms)")
        plt.xticks(rotation=45, ha="right", fontsize=7)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    st.markdown("### Barrido de sensibilidad (opcional)")
    parametro = st.selectbox("Parametro a variar", ["alfa", "beta", "rho", "n_hormigas"])
    valores_texto = st.text_input("Valores (separados por coma)", "1.0, 2.0, 3.0")
    if st.button("Ejecutar barrido"):
        try:
            valores = [float(v.strip()) for v in valores_texto.split(",") if v.strip()]
        except ValueError:
            st.error("Los valores deben ser numeros separados por coma.")
            valores = []
        if valores and origenes_sel and escenarios_sel:
            escenario_obj = construir_escenario(escenarios_sel[0], grafo, config_modelo)
            with st.spinner("Corriendo barrido..."):
                df_barrido = barrido_sensibilidad(
                    grafo, origenes_sel[0], escenario_obj, config_modelo, config_aco_actual, parametro, valores, n_corridas=10
                )
            st.dataframe(df_barrido, hide_index=True, width="stretch")

            fig3, (axa, axb) = plt.subplots(1, 2, figsize=(10, 4))
            axa.plot(df_barrido[parametro], df_barrido["brecha_pct_media"], marker="o")
            axa.set_xlabel(parametro)
            axa.set_ylabel("Brecha % media")
            axb.plot(df_barrido[parametro], df_barrido["tiempo_ms_medio"], marker="o", color="orange")
            axb.set_xlabel(parametro)
            axb.set_ylabel("Tiempo medio (ms)")
            fig3.tight_layout()
            st.pyplot(fig3)
            plt.close(fig3)
        elif not origenes_sel or not escenarios_sel:
            st.warning("Selecciona al menos un origen y un escenario arriba.")


def _pestana_evacuacion_completa(grafo, escenario, config_modelo) -> None:
    st.subheader(f"Evacuacion completa (42 origenes) - escenario: {escenario.nombre}")

    metricas_origenes = calcular_metricas_todos_los_origenes(grafo, config_modelo, escenario.aristas_bloqueadas)

    df = pd.DataFrame(
        [
            {
                "Origen": m.origen,
                "Poblacion": m.poblacion,
                "Tiene ruta": m.tiene_ruta,
                "1a persona (s)": round(m.tiempo_primera_persona_s, 1) if m.tiene_ruta else None,
                "Ultima persona (s)": round(m.tiempo_ultima_persona_s, 1) if m.tiene_ruta else None,
                "Punto de encuentro": m.punto_encuentro,
            }
            for m in metricas_origenes
        ]
    )
    st.dataframe(df, hide_index=True, width="stretch")

    if any(m.tiene_ruta for m in metricas_origenes):
        st.metric("Tiempo global hasta la PRIMERA persona (s)", f"{min(m.tiempo_primera_persona_s for m in metricas_origenes if m.tiene_ruta):.1f}")
        st.metric("Tiempo global hasta la ULTIMA persona (s)", f"{max(m.tiempo_ultima_persona_s for m in metricas_origenes if m.tiene_ruta):.1f}")

    st.markdown("### Uso de salidas (A vs B)")
    conteo_salida = {"SALIDA-A": 0, "SALIDA-B": 0, "sin ruta": 0}
    rutas_por_origen = {}
    for m in metricas_origenes:
        resultado = buscar_ruta(grafo, m.origen, config_modelo, escenario.aristas_bloqueadas)
        rutas_por_origen[m.origen] = resultado
        if not resultado.tiene_ruta:
            conteo_salida["sin ruta"] += m.poblacion
        elif "SALIDA-A" in resultado.camino:
            conteo_salida["SALIDA-A"] += m.poblacion
        elif "SALIDA-B" in resultado.camino:
            conteo_salida["SALIDA-B"] += m.poblacion

    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.bar(conteo_salida.keys(), conteo_salida.values(), color=["#1565c0", "#ef6c00", "#c62828"])
    ax.set_ylabel("Personas")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("### Animacion simple (posiciones a lo largo del tiempo)")
    tiempos_max = [m.tiempo_ultima_persona_s for m in metricas_origenes if m.tiene_ruta]
    if not tiempos_max:
        st.info("Ningun origen tiene ruta en este escenario.")
        return
    t_max = max(tiempos_max)

    col1, col2 = st.columns([3, 1])
    with col2:
        reproducir = st.button("Reproducir")
    with col1:
        t_actual = st.slider("Tiempo (s)", 0.0, float(t_max), 0.0, key="t_animacion")

    def _dibujar_posiciones(t: float) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(8, 6.5))
        for a in grafo.aristas_por_id.values():
            n1, n2 = grafo.nodos_por_id[a["desde"]], grafo.nodos_por_id[a["hasta"]]
            if n1["x_m"] is None or n2["x_m"] is None:
                continue
            ax.plot([n1["x_m"], n2["x_m"]], [n1["y_m"], n2["y_m"]], color="#dddddd", linewidth=0.5, zorder=1)
        for m in metricas_origenes:
            if not m.tiene_ruta:
                continue
            resultado = rutas_por_origen[m.origen]
            x, y = _posicion_en_tiempo(grafo, resultado.camino, config_modelo, config_modelo["tiempo_reaccion_s"], t)
            if x is not None:
                ax.scatter(x, y, s=80, color="#d81b60", zorder=5)
                ax.annotate(m.origen, (x, y), fontsize=6, xytext=(4, 4), textcoords="offset points")
        for n in grafo.nodos_por_id.values():
            if n["tipo"] == "punto_encuentro" and n["x_m"] is not None:
                ax.scatter(n["x_m"], n["y_m"], marker="*", s=260, color="gold", edgecolor="black", zorder=4)
        ax.set_title(f"t = {t:.1f} s")
        ax.set_aspect("equal", adjustable="datalim")
        fig.tight_layout()
        return fig

    placeholder_anim = st.empty()
    if reproducir:
        n_frames = 60
        for i in range(n_frames + 1):
            t = t_max * i / n_frames
            fig = _dibujar_posiciones(t)
            placeholder_anim.pyplot(fig)
            plt.close(fig)
            time.sleep(max(0.01, t_max / n_frames / 10))
    else:
        fig = _dibujar_posiciones(t_actual)
        placeholder_anim.pyplot(fig)
        plt.close(fig)


def _posicion_en_tiempo(grafo, camino, config_modelo, tiempo_reaccion_s, t):
    """Interpola la posicion (x_m, y_m) de una persona en el tiempo t, siguiendo 'camino'."""
    from costos import tiempo_arista

    if t <= tiempo_reaccion_s:
        n0 = grafo.nodos_por_id[camino[0]]
        return n0["x_m"], n0["y_m"]

    t_restante = t - tiempo_reaccion_s
    for a, b in zip(camino, camino[1:]):
        arista = next(ar for _v, ar in grafo.vecinos(a) if ar["desde"] in (a, b) and ar["hasta"] in (a, b))
        dt = tiempo_arista(arista, config_modelo)
        n1, n2 = grafo.nodos_por_id[a], grafo.nodos_por_id[b]
        if n1["x_m"] is None or n2["x_m"] is None:
            t_restante -= dt
            continue
        if t_restante <= dt:
            frac = t_restante / dt if dt > 0 else 1.0
            x = n1["x_m"] + (n2["x_m"] - n1["x_m"]) * frac
            y = n1["y_m"] + (n2["y_m"] - n1["y_m"]) * frac
            return x, y
        t_restante -= dt

    nf = grafo.nodos_por_id[camino[-1]]
    return nf["x_m"], nf["y_m"]


if __name__ == "__main__":
    main()
