"""Script de un solo uso para la auditoria de Fase 1-bis (Tarea G.2 / G.3).

1. Cuenta rutas simples distintas desde 5 origenes hacia cualquier punto de
   encuentro (con un tope, para no explotar combinatoriamente).
2. Corre ACO en 3 variantes sobre esos 5 origenes:
   (a) configuracion actual (poda + retroceso + heuristica guiada, beta=1.0)
   (b) sin heuristica guiada (beta=0, con poda + retroceso)
   (c) sin heuristica (beta=0) y con la lista tabu ORIGINAL (sin poda, sin
       retroceso): replica el algoritmo pre-Fase-2B solo para esta auditoria,
       no se reincorpora a src/aco.py.

No se guarda en results/ (es solo para armar docs/auditoria_fase2.md).

Uso:
    python scripts/auditoria_variantes.py
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_grafo, cargar_configuracion, Grafo, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
from costos import costo_arista  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from aco import ejecutar_aco  # noqa: E402

TOPE_RUTAS = 5000
N_CORRIDAS = 20
ORIGENES_AUDITORIA = ["H-PB-OFICINAS_CC", "H101", "H201", "H301", "H401"]


def contar_rutas_simples(grafo: Grafo, origen: str, tope: int) -> tuple[int, bool]:
    """Cuenta rutas simples (sin repetir nodos) desde origen hasta cualquier PE, con un tope.

    Devuelve (cantidad, se_corto): se_corto=True si se alcanzo el tope antes de
    agotar la busqueda (la cantidad real es >= tope).
    """
    contador = 0
    visitados = {origen}

    def dfs(nodo: str) -> bool:
        """Devuelve True si hay que detener la busqueda (tope alcanzado)."""
        nonlocal contador
        if grafo.es_punto_encuentro(nodo):
            contador += 1
            return contador >= tope
        for vecino_id, _arista in grafo.vecinos(nodo):
            if vecino_id in visitados:
                continue
            visitados.add(vecino_id)
            if dfs(vecino_id):
                visitados.discard(vecino_id)
                return True
            visitados.discard(vecino_id)
        return False

    se_corto = dfs(origen)
    return contador, se_corto


# ---------------------------------------------------------------------------
# Variante (c): algoritmo ORIGINAL pre-Fase-2B (sin poda, sin retroceso).
# Solo para esta auditoria; no modifica src/aco.py.
# ---------------------------------------------------------------------------


def _construir_camino_hormiga_original(grafo, origen, config_modelo, config_aco, tau, rng):
    alfa = config_aco["alfa"]
    beta = config_aco["beta"]
    nodo_actual = origen
    visitados = {origen}
    camino = [origen]
    costo_total = 0.0
    limite_pasos = len(grafo.nodos_por_id) + 1

    for _ in range(limite_pasos):
        if grafo.es_punto_encuentro(nodo_actual):
            return camino, costo_total, nodo_actual
        candidatos = [(v, a) for v, a in grafo.vecinos(nodo_actual) if v not in visitados]
        if not candidatos:
            return None, float("inf"), None
        pesos = []
        for v, a in candidatos:
            c = costo_arista(a, config_modelo)
            eta = 1.0 / c if c > 0 else float("inf")
            pesos.append((tau.get(a["id"], 0.0) ** alfa) * (eta**beta))
        total = sum(pesos)
        if total <= 0:
            v, a = rng.choice(candidatos)
        else:
            v, a = rng.choices(candidatos, weights=pesos, k=1)[0]
        visitados.add(v)
        camino.append(v)
        costo_total += costo_arista(a, config_modelo)
        nodo_actual = v
    return None, float("inf"), None


def ejecutar_aco_variante_c(grafo, origen, config_modelo, config_aco, semilla):
    """ACO sin poda de callejones y sin retroceso (algoritmo original), beta tomado de config_aco."""
    rng = random.Random(semilla)
    tau = {aid: config_aco["tau_inicial"] for aid in grafo.aristas_por_id}
    n_hormigas = int(config_aco["n_hormigas"])
    n_iteraciones = int(config_aco["n_iteraciones"])
    rho, Q = config_aco["rho"], config_aco["Q"]
    tau_min, tau_max = config_aco["tau_min"], config_aco["tau_max"]
    paciencia = int(config_aco["paciencia_estancamiento"])

    mejor_costo_global = float("inf")
    mejor_camino_global = None
    sin_mejora = 0
    inicio = time.perf_counter()

    for it in range(1, n_iteraciones + 1):
        resultados = [_construir_camino_hormiga_original(grafo, origen, config_modelo, config_aco, tau, rng) for _ in range(n_hormigas)]
        exitosas = [(c, co, pe) for c, co, pe in resultados if c is not None]
        for aid in tau:
            tau[aid] = max(tau_min, (1 - rho) * tau[aid])
        mejor_it = float("inf")
        camino_it = None
        for c, co, pe in exitosas:
            deposito = Q / co if co > 0 else Q
            for a, b in zip(c, c[1:]):
                for v, ar in grafo.vecinos(a):
                    if v == b:
                        tau[ar["id"]] = min(tau_max, tau[ar["id"]] + deposito)
                        break
            if co < mejor_it:
                mejor_it, camino_it = co, c
        if camino_it is not None:
            for a, b in zip(camino_it, camino_it[1:]):
                for v, ar in grafo.vecinos(a):
                    if v == b:
                        deposito = Q / mejor_it if mejor_it > 0 else Q
                        tau[ar["id"]] = min(tau_max, tau[ar["id"]] + deposito)
                        break
        if mejor_it < mejor_costo_global:
            mejor_costo_global, mejor_camino_global = mejor_it, camino_it
            sin_mejora = 0
        else:
            sin_mejora += 1
        if sin_mejora >= paciencia:
            break

    return mejor_camino_global, mejor_costo_global, time.perf_counter() - inicio


def main() -> int:
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    print("=== Conteo de rutas simples (tope = {}) ===".format(TOPE_RUTAS))
    for origen in ORIGENES_AUDITORIA:
        n, cortado = contar_rutas_simples(grafo, origen, TOPE_RUTAS)
        print(f"  {origen}: {n}{'+' if cortado else ''} rutas simples hacia algun PE")

    costos_dijkstra = {o: buscar_ruta(grafo, o, config_modelo).costo for o in ORIGENES_AUDITORIA}

    print("\n=== Variante (a): configuracion actual (poda + retroceso + heuristica) ===")
    _correr_variante_ab(grafo, config_modelo, config_aco, costos_dijkstra, usar_beta_cero=False)

    print("\n=== Variante (b): sin heuristica guiada (beta=0), con poda + retroceso ===")
    _correr_variante_ab(grafo, config_modelo, config_aco, costos_dijkstra, usar_beta_cero=True)

    print("\n=== Variante (c): sin heuristica (beta=0) y lista tabu ORIGINAL (sin poda, sin retroceso) ===")
    config_c = dict(config_aco)
    config_c["beta"] = 0.0
    for origen in ORIGENES_AUDITORIA:
        exitos, brechas, tiempos = 0, [], []
        for semilla in range(N_CORRIDAS):
            camino, costo, t = ejecutar_aco_variante_c(grafo, origen, config_modelo, config_c, semilla)
            tiempos.append(t * 1000)
            if camino is not None:
                exitos += 1
                brechas.append((costo - costos_dijkstra[origen]) / costos_dijkstra[origen] * 100)
        tasa = exitos / N_CORRIDAS * 100
        brecha_media = sum(brechas) / len(brechas) if brechas else float("nan")
        print(f"  {origen}: exito={tasa:.1f}% brecha_media={brecha_media:.2f}% tiempo_medio={sum(tiempos)/len(tiempos):.1f}ms")

    return 0


def _correr_variante_ab(grafo, config_modelo, config_aco_base, costos_dijkstra, usar_beta_cero: bool):
    config = dict(config_aco_base)
    if usar_beta_cero:
        config["beta"] = 0.0
    for origen in ORIGENES_AUDITORIA:
        exitos, brechas, tiempos = 0, [], []
        for semilla in range(N_CORRIDAS):
            r = ejecutar_aco(grafo, origen, config_modelo, config, semilla=semilla)
            tiempos.append(r.tiempo_s * 1000)
            if r.tiene_ruta:
                exitos += 1
                brechas.append((r.mejor_costo - costos_dijkstra[origen]) / costos_dijkstra[origen] * 100)
        tasa = exitos / N_CORRIDAS * 100
        brecha_media = sum(brechas) / len(brechas) if brechas else float("nan")
        print(f"  {origen}: exito={tasa:.1f}% brecha_media={brecha_media:.2f}% tiempo_medio={sum(tiempos)/len(tiempos):.1f}ms")


if __name__ == "__main__":
    sys.exit(main())
