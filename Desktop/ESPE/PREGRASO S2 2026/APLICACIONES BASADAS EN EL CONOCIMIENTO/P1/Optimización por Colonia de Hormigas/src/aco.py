"""Optimizacion por Colonia de Hormigas (ACO), variante MAX-MIN, para el grafo de evacuacion.

Cada hormiga parte de un origen y construye un camino sin repetir nodos
ACTIVOS en su recorrido (lista tabu) hasta llegar a CUALQUIER punto de
encuentro. Si queda sin vecinos validos, RETROCEDE un paso (en vez de morir
de inmediato) y marca ese nodo como muerto solo para ella; si no puede
retroceder mas (vuelve al origen sin opciones) o supera el limite de pasos,
la hormiga falla y no deposita feromona.

Correcciones aplicadas en la Fase 2B (ver docs/decisiones_fase2.md para el
diagnostico que las motivo):
1. Poda de callejones (`podar_callejones`): antes de correr ACO se
   construye una VISTA del grafo (no se modifica data/campus_graph.json)
   sin los nodos de grado 1 que no sean el origen ni un punto de encuentro
   (p. ej. las aulas, que son callejones sin salida para cualquier hormiga
   que no las use como origen).
2. Retroceso con limite de pasos (`max_pasos_factor` en config_aco.json).
3. Heuristica guiada (tipo A*): eta_ij = 1 / (costo_ij + h(j)), con h(j) la
   distancia euclidiana de j al punto de encuentro mas cercano (en x_m,
   y_m), precalculada una sola vez por ejecucion.

Todos los numeros (n_hormigas, n_iteraciones, alfa, beta, rho, Q,
tau_inicial, tau_min, tau_max, paciencia_estancamiento, semilla,
intervalo_snapshot_feromona, max_pasos_factor) vienen de
data/config_aco.json; ninguno esta escrito en este archivo. La funcion de
costo (src/costos.py) NO se modifico.
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterator

from costos import costo_arista
from grafo import Grafo

INFINITO = float("inf")


@dataclass
class IteracionACO:
    """Resumen (sin la matriz de feromona) de una iteracion del algoritmo."""

    iteracion: int
    mejor_costo_iteracion: float
    costo_promedio: float | None
    hormigas_exitosas: int


@dataclass
class SnapshotIteracionACO:
    """Lo que entrega aco_iterativo() al terminar cada iteracion (para animar en vivo)."""

    iteracion: int
    mejor_costo_iteracion: float
    mejor_camino_iteracion: list[str] | None
    costo_promedio: float | None
    hormigas_exitosas: int
    mejor_camino_global: list[str] | None
    mejor_costo_global: float
    punto_encuentro_global: str | None
    iteracion_mejor_global: int | None
    feromona: dict[str, float]
    nodos_podados: frozenset[str]


@dataclass
class ResultadoACO:
    """Resultado completo de una ejecucion de ACO (consume aco_iterativo hasta el final)."""

    mejor_camino: list[str] | None
    mejor_costo: float
    punto_encuentro: str | None
    historial: list[IteracionACO]
    iteracion_mejor_solucion: int | None
    tiempo_s: float
    feromona_final: dict[str, float]
    snapshots_feromona: dict[int, dict[str, float]]
    nodos_podados: frozenset[str]
    tiene_ruta: bool = field(init=False)

    def __post_init__(self) -> None:
        self.tiene_ruta = self.mejor_camino is not None


def podar_callejones(
    grafo: Grafo,
    protegidos: set[str],
    aristas_bloqueadas: frozenset[str] = frozenset(),
) -> tuple[Grafo, frozenset[str]]:
    """Construye una vista del grafo sin callejones sin salida (nodos de grado 1).

    Elimina iterativamente los nodos de grado 1 que no esten en 'protegidos'
    (tipicamente {origen} | puntos_de_encuentro), ignorando las aristas
    bloqueadas al calcular el grado (un nodo con una sola arista viva,
    aunque tenga otra bloqueada, cuenta como grado 1). Nunca modifica
    data/campus_graph.json: devuelve un nuevo objeto Grafo con solo los
    nodos/aristas que sobreviven, mas el conjunto de ids de nodos podados.

    Podar hojas es seguro: un nodo hoja nunca puede estar en el camino
    optimo entre otros dos nodos, asi que esto nunca desconecta al origen
    de un punto de encuentro alcanzable.
    """
    adyacencia: dict[str, set[str]] = {nodo_id: set() for nodo_id in grafo.nodos_por_id}
    for arista in grafo.aristas_por_id.values():
        if arista["id"] in aristas_bloqueadas:
            continue
        a, b = arista["desde"], arista["hasta"]
        adyacencia[a].add(b)
        adyacencia[b].add(a)

    grados = {nodo_id: len(vecinos) for nodo_id, vecinos in adyacencia.items()}
    cola = deque(nodo_id for nodo_id, grado in grados.items() if grado == 1 and nodo_id not in protegidos)
    podados: set[str] = set()

    while cola:
        nodo_id = cola.popleft()
        if nodo_id in podados or nodo_id in protegidos:
            continue
        podados.add(nodo_id)
        for vecino_id in list(adyacencia[nodo_id]):
            adyacencia[vecino_id].discard(nodo_id)
            adyacencia[nodo_id].discard(vecino_id)
            if vecino_id in podados:
                continue
            grados[vecino_id] = len(adyacencia[vecino_id])
            if grados[vecino_id] == 1 and vecino_id not in protegidos:
                cola.append(vecino_id)

    nodos_restantes = [n for nid, n in grafo.nodos_por_id.items() if nid not in podados]
    aristas_restantes = [
        a
        for a in grafo.aristas_por_id.values()
        if a["id"] not in aristas_bloqueadas and a["desde"] not in podados and a["hasta"] not in podados
    ]
    return Grafo(nodos_restantes, aristas_restantes), frozenset(podados)


def calcular_heuristica(grafo: Grafo) -> dict[str, float]:
    """Precalcula h(j) = distancia euclidiana (x_m, y_m) de cada nodo al punto de encuentro mas cercano.

    Es la misma idea que la heuristica admisible de A*: una estimacion de
    cuanto falta para llegar a una meta, sumada al costo real recorrido.
    Aqui se usa dentro de eta_ij = 1 / (costo_ij + h(j)) en vez de
    eta_ij = 1 / costo_ij, para que la probabilidad de transicion de ACO
    tambien prefiera vecinos que acercan geometricamente a un punto de
    encuentro, no solo vecinos con la arista local mas barata.
    """
    puntos_encuentro = [
        grafo.nodos_por_id[pid]
        for pid in grafo.ids_puntos_encuentro
        if pid in grafo.nodos_por_id
        and grafo.nodos_por_id[pid]["x_m"] is not None
        and grafo.nodos_por_id[pid]["y_m"] is not None
    ]

    heuristica: dict[str, float] = {}
    for nodo_id, nodo in grafo.nodos_por_id.items():
        if nodo["x_m"] is None or nodo["y_m"] is None or not puntos_encuentro:
            heuristica[nodo_id] = 0.0
            continue
        heuristica[nodo_id] = min(
            math.hypot(nodo["x_m"] - pe["x_m"], nodo["y_m"] - pe["y_m"]) for pe in puntos_encuentro
        )
    return heuristica


def _inicializar_feromona(
    grafo: Grafo,
    config_aco: dict[str, Any],
    feromona_inicial: dict[str, float] | None,
) -> dict[str, float]:
    """Inicializa la matriz de feromona (por id de arista) sobre la vista podada del grafo.

    Si se recibe feromona_inicial (warm start), se usa como punto de
    partida para las aristas que sigan existiendo en la vista; las aristas
    nuevas (o que no estaban en la ejecucion anterior) arrancan en
    tau_inicial. Las aristas bloqueadas ya no existen en 'grafo' (fueron
    excluidas por podar_callejones), asi que no hace falta anularlas aqui.
    """
    if feromona_inicial is not None:
        tau = {
            id_arista: feromona_inicial.get(id_arista, config_aco["tau_inicial"])
            for id_arista in grafo.aristas_por_id
        }
    else:
        tau = {id_arista: config_aco["tau_inicial"] for id_arista in grafo.aristas_por_id}
    return tau


def _elegir_vecino(
    candidatos: list[tuple[str, dict[str, Any]]],
    pesos: list[float],
    rng: random.Random,
) -> tuple[str, dict[str, Any]]:
    """Elige un vecino de forma ponderada; si todos los pesos son 0, elige uniformemente."""
    total = sum(pesos)
    if total <= 0:
        return rng.choice(candidatos)
    return rng.choices(candidatos, weights=pesos, k=1)[0]


def _construir_camino_hormiga(
    grafo: Grafo,
    origen: str,
    config_modelo: dict[str, Any],
    config_aco: dict[str, Any],
    tau: dict[str, float],
    heuristica: dict[str, float],
    rng: random.Random,
) -> tuple[list[str] | None, float, str | None]:
    """Construye el camino de una hormiga desde 'origen' hasta un punto de encuentro, con retroceso.

    Devuelve (camino, costo, punto_encuentro), o (None, inf, None) si la
    hormiga no logra llegar (se quedo sin opciones incluso retrocediendo
    hasta el origen, o supero el limite de pasos).
    """
    alfa = config_aco["alfa"]
    beta = config_aco["beta"]
    max_pasos = int(config_aco["max_pasos_factor"] * len(grafo.nodos_por_id))

    pila = [origen]
    activos = {origen}  # nodos actualmente en el camino (tabu mientras esten en la pila)
    muertos: set[str] = set()  # nodos descartados por esta hormiga (no se vuelven a intentar)
    costos_paso: list[float] = []

    pasos = 0
    while pasos < max_pasos:
        nodo_actual = pila[-1]

        if grafo.es_punto_encuentro(nodo_actual):
            return list(pila), sum(costos_paso), nodo_actual

        candidatos = [
            (vecino_id, arista)
            for vecino_id, arista in grafo.vecinos(nodo_actual)
            if vecino_id not in activos and vecino_id not in muertos
        ]

        if not candidatos:
            if len(pila) == 1:
                return None, INFINITO, None  # el origen mismo no tiene salida: fallo real
            nodo_muerto = pila.pop()
            activos.discard(nodo_muerto)
            muertos.add(nodo_muerto)
            if costos_paso:
                costos_paso.pop()
            pasos += 1
            continue

        pesos = []
        for vecino_id, arista in candidatos:
            costo_arco = costo_arista(arista, config_modelo)
            eta = 1.0 / (costo_arco + heuristica.get(vecino_id, 0.0))
            pesos.append((tau.get(arista["id"], 0.0) ** alfa) * (eta**beta))

        vecino_id, arista = _elegir_vecino(candidatos, pesos, rng)
        activos.add(vecino_id)
        pila.append(vecino_id)
        costos_paso.append(costo_arista(arista, config_modelo))
        pasos += 1

    return None, INFINITO, None  # excedio el limite de pasos


def _aristas_del_camino(grafo: Grafo, camino: list[str]) -> list[str]:
    """Devuelve los ids de las aristas usadas en un camino (lista de nodos consecutivos)."""
    ids_aristas = []
    for a, b in zip(camino, camino[1:]):
        for vecino_id, arista in grafo.vecinos(a):
            if vecino_id == b:
                ids_aristas.append(arista["id"])
                break
    return ids_aristas


def aco_iterativo(
    grafo: Grafo,
    origen: str,
    config_modelo: dict[str, Any],
    config_aco: dict[str, Any],
    aristas_bloqueadas: frozenset[str] = frozenset(),
    feromona_inicial: dict[str, float] | None = None,
    semilla: int | None = None,
) -> Iterator[SnapshotIteracionACO]:
    """Generador: corre ACO (MAX-MIN) y entrega un SnapshotIteracionACO al final de cada iteracion.

    Es el UNICO lugar donde vive la logica de ACO: ejecutar_aco() (abajo) y
    la pestana "Simulacion en vivo" de la app (app/app.py) consumen este
    mismo generador, sin duplicar codigo.
    """
    if origen not in grafo.nodos_por_id:
        raise KeyError(f"Nodo origen desconocido: '{origen}'")

    protegidos = {origen} | grafo.ids_puntos_encuentro
    vista, nodos_podados = podar_callejones(grafo, protegidos, aristas_bloqueadas)
    heuristica = calcular_heuristica(vista)

    semilla_efectiva = config_aco["semilla"] if semilla is None else semilla
    rng = random.Random(semilla_efectiva)

    tau = _inicializar_feromona(vista, config_aco, feromona_inicial)

    n_hormigas = int(config_aco["n_hormigas"])
    n_iteraciones = int(config_aco["n_iteraciones"])
    rho = config_aco["rho"]
    Q = config_aco["Q"]
    tau_min = config_aco["tau_min"]
    tau_max = config_aco["tau_max"]
    paciencia = int(config_aco["paciencia_estancamiento"])

    mejor_camino_global: list[str] | None = None
    mejor_costo_global = INFINITO
    mejor_pe_global: str | None = None
    iteracion_mejor_global: int | None = None
    iteraciones_sin_mejora = 0

    for iteracion in range(1, n_iteraciones + 1):
        resultados_hormigas = [
            _construir_camino_hormiga(vista, origen, config_modelo, config_aco, tau, heuristica, rng)
            for _ in range(n_hormigas)
        ]

        exitosas = [(camino, costo, pe) for camino, costo, pe in resultados_hormigas if camino is not None]

        for id_arista in tau:
            tau[id_arista] = max(tau_min, (1 - rho) * tau[id_arista])

        mejor_camino_iteracion: list[str] | None = None
        mejor_costo_iteracion = INFINITO
        mejor_pe_iteracion: str | None = None

        for camino, costo, pe in exitosas:
            ids_aristas = _aristas_del_camino(vista, camino)
            deposito = Q / costo if costo > 0 else Q
            for id_arista in ids_aristas:
                tau[id_arista] = min(tau_max, tau[id_arista] + deposito)
            if costo < mejor_costo_iteracion:
                mejor_costo_iteracion = costo
                mejor_camino_iteracion = camino
                mejor_pe_iteracion = pe

        if mejor_camino_iteracion is not None:
            ids_mejor = _aristas_del_camino(vista, mejor_camino_iteracion)
            deposito_extra = Q / mejor_costo_iteracion if mejor_costo_iteracion > 0 else Q
            for id_arista in ids_mejor:
                tau[id_arista] = min(tau_max, tau[id_arista] + deposito_extra)

        costo_promedio = (
            sum(costo for _camino, costo, _pe in exitosas) / len(exitosas) if exitosas else None
        )

        if mejor_costo_iteracion < mejor_costo_global:
            mejor_costo_global = mejor_costo_iteracion
            mejor_camino_global = mejor_camino_iteracion
            mejor_pe_global = mejor_pe_iteracion
            iteracion_mejor_global = iteracion
            iteraciones_sin_mejora = 0
        else:
            iteraciones_sin_mejora += 1

        yield SnapshotIteracionACO(
            iteracion=iteracion,
            mejor_costo_iteracion=mejor_costo_iteracion,
            mejor_camino_iteracion=mejor_camino_iteracion,
            costo_promedio=costo_promedio,
            hormigas_exitosas=len(exitosas),
            mejor_camino_global=mejor_camino_global,
            mejor_costo_global=mejor_costo_global,
            punto_encuentro_global=mejor_pe_global,
            iteracion_mejor_global=iteracion_mejor_global,
            feromona=dict(tau),
            nodos_podados=nodos_podados,
        )

        if iteraciones_sin_mejora >= paciencia:
            break


def ejecutar_aco(
    grafo: Grafo,
    origen: str,
    config_modelo: dict[str, Any],
    config_aco: dict[str, Any],
    aristas_bloqueadas: frozenset[str] = frozenset(),
    feromona_inicial: dict[str, float] | None = None,
    semilla: int | None = None,
) -> ResultadoACO:
    """Ejecuta ACO completo (consume aco_iterativo hasta el final) y arma el resultado agregado.

    No duplica la logica del algoritmo: toda la busqueda ocurre dentro de
    aco_iterativo(); esta funcion solo recolecta el historial y arma las
    copias de la matriz de feromona en las iteraciones seleccionadas
    (cada config_aco['intervalo_snapshot_feromona'], mas la primera y la
    ultima).
    """
    inicio = time.perf_counter()
    intervalo_snapshot = int(config_aco["intervalo_snapshot_feromona"])

    historial: list[IteracionACO] = []
    snapshots_feromona: dict[int, dict[str, float]] = {}
    ultimo: SnapshotIteracionACO | None = None

    for snap in aco_iterativo(
        grafo, origen, config_modelo, config_aco, aristas_bloqueadas, feromona_inicial, semilla
    ):
        historial.append(
            IteracionACO(
                iteracion=snap.iteracion,
                mejor_costo_iteracion=snap.mejor_costo_iteracion,
                costo_promedio=snap.costo_promedio,
                hormigas_exitosas=snap.hormigas_exitosas,
            )
        )
        if snap.iteracion == 1 or snap.iteracion % intervalo_snapshot == 0:
            snapshots_feromona[snap.iteracion] = snap.feromona
        ultimo = snap

    tiempo_s = time.perf_counter() - inicio

    if ultimo is None:
        # n_iteraciones == 0: caso limite, sin ninguna iteracion ejecutada.
        return ResultadoACO(
            mejor_camino=None,
            mejor_costo=INFINITO,
            punto_encuentro=None,
            historial=[],
            iteracion_mejor_solucion=None,
            tiempo_s=tiempo_s,
            feromona_final={},
            snapshots_feromona={},
            nodos_podados=frozenset(),
        )

    snapshots_feromona[ultimo.iteracion] = ultimo.feromona

    return ResultadoACO(
        mejor_camino=ultimo.mejor_camino_global,
        mejor_costo=ultimo.mejor_costo_global,
        punto_encuentro=ultimo.punto_encuentro_global,
        historial=historial,
        iteracion_mejor_solucion=ultimo.iteracion_mejor_global,
        tiempo_s=tiempo_s,
        feromona_final=ultimo.feromona,
        snapshots_feromona=snapshots_feromona,
        nodos_podados=ultimo.nodos_podados,
    )
