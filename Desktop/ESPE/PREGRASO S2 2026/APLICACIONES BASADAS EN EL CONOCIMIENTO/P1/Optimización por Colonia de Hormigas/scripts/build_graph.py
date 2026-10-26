"""Construye el grafo de evacuacion (Fase 1-bis): complejo G/H con 2 secciones de gradas
compartidas (norte, sur) y 2 salidas, segun la verdad de campo del equipo sobre
data/maps/plano_base_GH_anotado.jpeg.

Lee data/config_modelo.json (todos los numeros del modelo), data/posiciones_plano.json
(posiciones de pixel de los nodos 'hub' que se repiten en cada nivel) y
data/calibracion_plano.json (transformacion pixel -> metros/lat-lon), mas
data/raw/maps_observations.json (caminos exteriores y puntos de encuentro, Fase 0/1),
y genera data/campus_graph.json siguiendo data/campus_graph.schema.json.

No implementa ACO ni Dijkstra. Solo construye la estructura del grafo, con todos
los supuestos marcados como tales (confidence "supuesto", status "provisional").
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "scripts"))

from validate_graph import cargar_json, distancia_haversine_m  # noqa: E402

CONFIG_PATH = RAIZ_PROYECTO / "data" / "config_modelo.json"
POSICIONES_PATH = RAIZ_PROYECTO / "data" / "posiciones_plano.json"
CALIBRACION_PATH = RAIZ_PROYECTO / "data" / "calibracion_plano.json"
OBSERVACIONES_PATH = RAIZ_PROYECTO / "data" / "raw" / "maps_observations.json"
SALIDA_GRAFO_PATH = RAIZ_PROYECTO / "data" / "campus_graph.json"

# Coordenadas dadas por el equipo (Fase 1), re-verificadas en Fase 1-bis como
# las dos X de la captura anotada (ver data/calibracion_plano.json).
SALIDA_A = {"id": "SALIDA-A", "lat": -0.313162, "lon": -78.445291, "bloque": "H"}
SALIDA_B = {"id": "SALIDA-B", "lat": -0.312607, "lon": -78.445237, "bloque": "G"}

DISTANCIA_MAXIMA_SALIDA_GRADAS_M = 40.0


def cargar_configuracion() -> dict[str, Any]:
    """Carga config_modelo.json y devuelve un diccionario {parametro: valor}."""
    datos = cargar_json(CONFIG_PATH)
    return {nombre: info["value"] for nombre, info in datos["parametros"].items()}


def proyectar_xy(lat: float, lon: float, lat0: float, lon0: float) -> tuple[float, float]:
    """Proyecta lat/lon a metros locales (equirectangular), con origen en (lat0, lon0)."""
    metros_por_grado_lat = 110574.0
    metros_por_grado_lon = 111320.0 * math.cos(math.radians(lat0))
    x_m = (lon - lon0) * metros_por_grado_lon
    y_m = (lat - lat0) * metros_por_grado_lat
    return round(x_m, 2), round(y_m, 2)


def pixel_a_xy(px: float, py: float, calibracion: dict[str, Any]) -> tuple[float, float]:
    """Convierte un pixel del plano calibrado a metros locales (x_m, y_m), origen Salida A."""
    control_a = calibracion["puntos_de_control"]["salida_A"]
    escala = calibracion["escala_px_por_m"]
    x_m = (px - control_a["pixel_x"]) / escala
    y_m = -(py - control_a["pixel_y"]) / escala
    return round(x_m, 2), round(y_m, 2)


def nodo(
    id: str,
    nombre: str | None,
    tipo: str,
    bloque: str,
    piso: int | None,
    lat: float | None,
    lon: float | None,
    x_m: float | None,
    y_m: float | None,
    techado: bool | None,
    riesgo_caida: bool | None,
    capacidad_estimada_personas: int | None,
    source: str,
    confidence: str,
    status: str,
    notes: str | None,
) -> dict[str, Any]:
    """Construye un nodo con todos los campos requeridos por el schema."""
    return {
        "id": id,
        "nombre": nombre,
        "tipo": tipo,
        "bloque": bloque,
        "piso": piso,
        "lat": lat,
        "lon": lon,
        "x_m": x_m,
        "y_m": y_m,
        "techado": techado,
        "riesgo_caida": riesgo_caida,
        "capacidad_estimada_personas": capacidad_estimada_personas,
        "source": source,
        "confidence": confidence,
        "status": status,
        "notes": notes,
    }


def arista(
    id: str,
    desde: str,
    hasta: str,
    distancia_m: float | None,
    tipo: str,
    techado: bool | None,
    ancho_m: float | None,
    bloqueable: bool | None,
    source: str,
    confidence: str,
    status: str,
    notes: str | None,
) -> dict[str, Any]:
    """Construye una arista con todos los campos requeridos por el schema."""
    return {
        "id": id,
        "desde": desde,
        "hasta": hasta,
        "distancia_m": distancia_m,
        "tipo": tipo,
        "techado": techado,
        "ancho_m": ancho_m,
        "bloqueable": bloqueable,
        "source": source,
        "confidence": confidence,
        "status": status,
        "notes": notes,
    }


NOTA_INTERIOR = (
    "Dato interior PROVISIONAL (supuesto del equipo, Fase 1-bis). Reemplazar con "
    "verificacion de campo (ver docs/base_informe.md, seccion (c))."
)
SOURCE_PLANO = "data/posiciones_plano.json + data/calibracion_plano.json (Fase 1-bis)"
SOURCE_CONFIG = "data/config_modelo.json (supuesto del equipo, Fase 1-bis)"


def generar_nodos_exteriores(
    observaciones: list[dict[str, Any]], lat0: float, lon0: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Genera los nodos exteriores: Salida A, Salida B, caminos de Maps y puntos de encuentro."""
    nodos: list[dict[str, Any]] = []

    for salida in (SALIDA_A, SALIDA_B):
        x_m, y_m = proyectar_xy(salida["lat"], salida["lon"], lat0, lon0)
        nodos.append(
            nodo(
                id=salida["id"],
                nombre=f"{salida['id']} (bloques {'C y H' if salida['id'] == 'SALIDA-A' else 'G y D'})",
                tipo="salida",
                bloque=salida["bloque"],
                piso=0,
                lat=salida["lat"],
                lon=salida["lon"],
                x_m=x_m,
                y_m=y_m,
                techado=False,
                riesgo_caida=None,
                capacidad_estimada_personas=None,
                source="Coordenadas dadas por el equipo, confirmadas como las dos X de data/maps/plano_base_GH_anotado.jpeg",
                confidence="medido_en_maps",
                status="pendiente",
                notes="indicado por el equipo, por verificar en campo",
            )
        )

    for obs in observaciones:
        if obs["tipo"] != "camino":
            continue
        x_m, y_m = proyectar_xy(obs["lat"], obs["lon"], lat0, lon0)
        nodos.append(
            nodo(
                id=obs["id"],
                nombre=obs["descripcion"],
                tipo="via_exterior",
                bloque="exterior",
                piso=None,
                lat=obs["lat"],
                lon=obs["lon"],
                x_m=x_m,
                y_m=y_m,
                techado=False,
                riesgo_caida=None,
                capacidad_estimada_personas=None,
                source="data/raw/maps_observations.json",
                confidence=obs["confidence"],
                status="pendiente",
                notes=obs["notes"],
            )
        )

    ids_puntos_encuentro = ["area_abierta_01", "area_abierta_02", "area_abierta_03"]
    nombres_pe = {
        "area_abierta_01": "PE-1 (provisional)",
        "area_abierta_02": "PE-2 (provisional)",
        "area_abierta_03": "PE-3 (provisional)",
    }
    observaciones_por_id = {obs["id"]: obs for obs in observaciones}

    puntos_encuentro_detalle: list[dict[str, Any]] = []
    for id_obs in ids_puntos_encuentro:
        obs = observaciones_por_id[id_obs]
        x_m, y_m = proyectar_xy(obs["lat"], obs["lon"], lat0, lon0)
        id_pe = nombres_pe[id_obs].split(" ")[0]
        nodos.append(
            nodo(
                id=id_pe,
                nombre=nombres_pe[id_obs],
                tipo="punto_encuentro",
                bloque="exterior",
                piso=None,
                lat=obs["lat"],
                lon=obs["lon"],
                x_m=x_m,
                y_m=y_m,
                techado=False,
                riesgo_caida=False,
                capacidad_estimada_personas=None,
                source="data/raw/maps_observations.json",
                confidence="supuesto",
                status="provisional",
                notes=(
                    "Punto de encuentro PROVISIONAL, no es un punto de encuentro oficial "
                    "senalizado por la ESPE. Reemplazar cuando se verifique la senaletica real."
                ),
            )
        )
        puntos_encuentro_detalle.append(
            {
                "id": id_pe,
                "nombre_o_codigo_en_senaletica": None,
                "lat": obs["lat"],
                "lon": obs["lon"],
                "area_aprox_m2": None,
                "abierto_sin_edificaciones_cerca": True,
                "capacidad_estimada_personas": None,
                "source": "data/raw/maps_observations.json",
                "confidence": "supuesto",
                "status": "provisional",
                "notes": f"Provisional: area abierta candidata. Observacion original: {id_obs}.",
            }
        )

    return nodos, puntos_encuentro_detalle


def construir_arbol_expansion_minima(
    nodos_exteriores: list[dict[str, Any]],
) -> list[tuple[str, str, float]]:
    """Arbol de expansion minima (Prim) sobre los nodos exteriores, por distancia haversine."""
    if len(nodos_exteriores) < 2:
        return []

    pendientes = {n["id"]: n for n in nodos_exteriores}
    primer_id = nodos_exteriores[0]["id"]
    en_arbol = {primer_id}
    del pendientes[primer_id]

    aristas_mst: list[tuple[str, str, float]] = []
    nodos_por_id = {n["id"]: n for n in nodos_exteriores}

    while pendientes:
        mejor = None
        for id_en_arbol in en_arbol:
            n1 = nodos_por_id[id_en_arbol]
            for id_candidato, n2 in pendientes.items():
                d = distancia_haversine_m(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
                if mejor is None or d < mejor[0]:
                    mejor = (d, id_en_arbol, id_candidato)
        distancia, desde, hasta = mejor
        aristas_mst.append((desde, hasta, round(distancia, 2)))
        en_arbol.add(hasta)
        del pendientes[hasta]

    return aristas_mst


def generar_aristas_exteriores(nodos_exteriores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Genera las aristas exteriores (MST por distancia haversine) entre salidas, caminos y PE."""
    aristas: list[dict[str, Any]] = []
    mst = construir_arbol_expansion_minima(nodos_exteriores)
    for i, (desde, hasta, distancia) in enumerate(mst, start=1):
        aristas.append(
            arista(
                id=f"EXT-{i:02d}",
                desde=desde,
                hasta=hasta,
                distancia_m=distancia,
                tipo="plano",
                techado=False,
                ancho_m=None,
                bloqueable=False,
                source="Calculada: arbol de expansion minima por distancia haversine sobre data/raw/maps_observations.json",
                confidence="supuesto",
                status="provisional",
                notes="Conectividad exterior aproximada (no es el trazado real del camino).",
            )
        )
    return aristas


def generar_complejo_interior(
    config: dict[str, Any],
    posiciones: dict[str, Any],
    calibracion: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Genera los nodos/aristas del complejo interior: niveles, pasillos, gradas y aulas.

    Un solo complejo compartido por G y H (no un bloque por separado): 2 secciones
    de gradas (norte, sur) que llegan a todos los niveles, un nodo 'hub' de pasillo
    central por nivel que conecta el pasillo de H, el de G y los dos accesos a
    gradas, y 2 origenes en PB (oficinas CC en H, laboratorios de biotecnologia en G).
    """
    nodos: list[dict[str, Any]] = []
    aristas: list[dict[str, Any]] = []

    niveles: list[str] = config["niveles"]  # ["PB","1","2","3","4"]
    aulas_por_piso = int(config["aulas_por_piso"])
    altura_piso = config["altura_piso_m"]
    espaciado = config["espaciado_aula_m"]

    hub_px = posiciones["nodos_hub"]
    hub_xy_m = {nombre: pixel_a_xy(info["pixel_x"], info["pixel_y"], calibracion) for nombre, info in hub_px.items()}

    def id_pasillo(lado: str, nivel: str) -> str:
        return f"PAS-{lado}-{nivel}"

    def id_gradas(seccion: str, nivel: str) -> str:
        return f"GRADAS-{seccion}-{nivel}"

    ids_pasillo_central: dict[str, str] = {}
    ids_gradas_norte: dict[str, str] = {}
    ids_gradas_sur: dict[str, str] = {}

    for indice_nivel, nivel in enumerate(niveles):
        piso_num = 0 if nivel == "PB" else int(nivel)
        offset_visual_y = indice_nivel * altura_piso  # solo para separar niveles en la vista general

        # --- nodos hub de este nivel (pasillo H, pasillo G, pasillo central, 2 accesos a gradas) ---
        x_h, y_h = hub_xy_m["pasillo_H"]
        x_g, y_g = hub_xy_m["pasillo_G"]
        x_c, y_c = hub_xy_m["pasillo_central"]
        x_gn, y_gn = hub_xy_m["gradas_norte_acceso"]
        x_gs, y_gs = hub_xy_m["gradas_sur_acceso"]

        id_pas_h = id_pasillo("H", nivel)
        id_pas_g = id_pasillo("G", nivel)
        id_pas_c = id_pasillo("CENTRAL", nivel)
        id_gr_n = id_gradas("NORTE", nivel)
        id_gr_s = id_gradas("SUR", nivel)
        ids_pasillo_central[nivel] = id_pas_c
        ids_gradas_norte[nivel] = id_gr_n
        ids_gradas_sur[nivel] = id_gr_s

        nodos.append(
            nodo(id_pas_h, f"Pasillo H, nivel {nivel}", "pasillo", "H", piso_num, None, None,
                 x_h, y_h + offset_visual_y, True, False, None, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        nodos.append(
            nodo(id_pas_g, f"Pasillo G, nivel {nivel}", "pasillo", "G", piso_num, None, None,
                 x_g, y_g + offset_visual_y, True, False, None, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        nodos.append(
            nodo(id_pas_c, f"Pasillo central, nivel {nivel}", "pasillo", "compartido", piso_num, None, None,
                 x_c, y_c + offset_visual_y, True, False, None, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        nodos.append(
            nodo(id_gr_n, f"Acceso gradas norte, nivel {nivel}", "gradas", "compartido", piso_num, None, None,
                 x_gn, y_gn + offset_visual_y, True, False, None, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        nodos.append(
            nodo(id_gr_s, f"Acceso gradas sur, nivel {nivel}", "gradas", "compartido", piso_num, None, None,
                 x_gs, y_gs + offset_visual_y, True, False, None, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )

        # --- aristas horizontales del nivel: distancias leidas de la imagen calibrada ---
        def dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
            return round(math.hypot(p1[0] - p2[0], p1[1] - p2[1]), 2)

        aristas.append(
            arista(f"PAS-H-CENTRAL-{nivel}", id_pas_h, id_pas_c, dist((x_h, y_h), (x_c, y_c)), "plano",
                   True, config["ancho_pasillo_m"], True, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        aristas.append(
            arista(f"PAS-G-CENTRAL-{nivel}", id_pas_g, id_pas_c, dist((x_g, y_g), (x_c, y_c)), "plano",
                   True, config["ancho_pasillo_m"], True, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        aristas.append(
            arista(f"PAS-CENTRAL-GRADAS-NORTE-{nivel}", id_pas_c, id_gr_n, dist((x_c, y_c), (x_gn, y_gn)), "plano",
                   True, config["ancho_pasillo_m"], True, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )
        aristas.append(
            arista(f"PAS-CENTRAL-GRADAS-SUR-{nivel}", id_pas_c, id_gr_s, dist((x_c, y_c), (x_gs, y_gs)), "plano",
                   True, config["ancho_pasillo_m"], True, SOURCE_PLANO, "supuesto", "provisional", NOTA_INTERIOR)
        )

        # --- aulas de este nivel (PB no tiene aulas: ver origenes especiales abajo) ---
        if nivel != "PB":
            for lado, id_pas_lado, x_lado, y_lado in (("H", id_pas_h, x_h, y_h), ("G", id_pas_g, x_g, y_g)):
                for n in range(1, aulas_por_piso + 1):
                    id_aula = f"{lado}{piso_num}0{n}"
                    x_aula = x_lado + (n - (aulas_por_piso + 1) / 2) * espaciado
                    y_aula = y_lado + offset_visual_y + espaciado / 2
                    nodos.append(
                        nodo(id_aula, f"Aula {id_aula}", "aula", lado, piso_num, None, None,
                             round(x_aula, 2), round(y_aula, 2), True, False, None,
                             SOURCE_CONFIG, "supuesto", "provisional", NOTA_INTERIOR)
                    )
                    aristas.append(
                        arista(f"{id_aula}-PAS", id_aula, id_pas_lado, config["distancia_aula_a_pasillo_m"],
                               "plano", True, config["ancho_pasillo_m"], True, SOURCE_CONFIG,
                               "supuesto", "provisional", NOTA_INTERIOR)
                    )

    # --- origenes especiales de PB (oficinas CC en H, laboratorios biotecnologia en G) ---
    x_h, y_h = hub_xy_m["pasillo_H"]
    x_g, y_g = hub_xy_m["pasillo_G"]
    nodos.append(
        nodo("H-PB-OFICINAS_CC", "Oficinas Departamento de Ciencias de la Computacion (PB, lado H)",
             "aula", "H", 0, None, None, round(x_h - config["espaciado_aula_m"], 2), round(y_h + config["espaciado_aula_m"] / 2, 2),
             True, False, None, SOURCE_CONFIG, "supuesto", "provisional", NOTA_INTERIOR)
    )
    nodos.append(
        nodo("G-PB-LAB_BIOTEC", "Laboratorios de Biotecnologia / Ciencias de la Vida (PB, lado G)",
             "aula", "G", 0, None, None, round(x_g + config["espaciado_aula_m"], 2), round(y_g + config["espaciado_aula_m"] / 2, 2),
             True, False, None, SOURCE_CONFIG, "supuesto", "provisional", NOTA_INTERIOR)
    )
    aristas.append(
        arista("H-PB-OFICINAS_CC-PAS", "H-PB-OFICINAS_CC", id_pasillo("H", "PB"), config["distancia_aula_a_pasillo_m"],
               "plano", True, config["ancho_pasillo_m"], True, SOURCE_CONFIG, "supuesto", "provisional", NOTA_INTERIOR)
    )
    aristas.append(
        arista("G-PB-LAB_BIOTEC-PAS", "G-PB-LAB_BIOTEC", id_pasillo("G", "PB"), config["distancia_aula_a_pasillo_m"],
               "plano", True, config["ancho_pasillo_m"], True, SOURCE_CONFIG, "supuesto", "provisional", NOTA_INTERIOR)
    )

    # --- aristas verticales dentro de cada seccion de gradas (llegan a todos los niveles) ---
    distancia_gradas = altura_piso * config["factor_costo_gradas"] + config["tramo_horizontal_gradas_m"]
    for seccion, ids_por_nivel in (("NORTE", ids_gradas_norte), ("SUR", ids_gradas_sur)):
        for nivel_abajo, nivel_arriba in zip(niveles, niveles[1:]):
            aristas.append(
                arista(
                    f"GRADAS-{seccion}-{nivel_abajo}-{nivel_arriba}",
                    ids_por_nivel[nivel_arriba], ids_por_nivel[nivel_abajo],
                    round(distancia_gradas, 2), "gradas", True, config["ancho_gradas_m"], True,
                    SOURCE_CONFIG, "supuesto", "provisional", NOTA_INTERIOR,
                )
            )

    # --- PB conecta a Salida A (sur) y Salida B (norte) ---
    x_gn, y_gn = hub_xy_m["gradas_norte_acceso"]
    x_gs, y_gs = hub_xy_m["gradas_sur_acceso"]
    x_a, y_a = proyectar_xy(SALIDA_A["lat"], SALIDA_A["lon"], SALIDA_A["lat"], SALIDA_A["lon"])
    x_b, y_b = pixel_a_xy(
        calibracion["puntos_de_control"]["salida_B"]["pixel_x"],
        calibracion["puntos_de_control"]["salida_B"]["pixel_y"],
        calibracion,
    )
    distancia_sur_a = round(math.hypot(x_gs - x_a, y_gs - y_a), 2)
    distancia_norte_b = round(math.hypot(x_gn - x_b, y_gn - y_b), 2)

    aristas.append(
        arista("GRADAS-SUR-PB-SALIDA-A", ids_gradas_sur["PB"], "SALIDA-A", distancia_sur_a, "puerta",
               False, config["ancho_puerta_salida_m"], True, SOURCE_PLANO, "supuesto", "provisional",
               "Acceso a gradas sur en PB conecta a Salida A, al sur del complejo (ver captura anotada).")
    )
    aristas.append(
        arista("GRADAS-NORTE-PB-SALIDA-B", ids_gradas_norte["PB"], "SALIDA-B", distancia_norte_b, "puerta",
               False, config["ancho_puerta_salida_m"], True, SOURCE_PLANO, "supuesto", "provisional",
               "Acceso a gradas norte en PB conecta a Salida B, al norte del complejo (ver captura anotada).")
    )

    return nodos, aristas


def verificar_distancia_salidas_a_gradas(posiciones: dict[str, Any], calibracion: dict[str, Any]) -> list[str]:
    """Verifica que cada salida este a menos de 40 m de la seccion de gradas mas cercana (en PB).

    Reemplaza la verificacion de Fase 1 ('distancia a la esquina del bloque'),
    que ya no aplica: ahora las salidas estan al pie de una seccion de gradas,
    no pegadas a la fachada de un bloque especifico.
    """
    advertencias = []
    hub_px = posiciones["nodos_hub"]

    x_gn, y_gn = pixel_a_xy(hub_px["gradas_norte_acceso"]["pixel_x"], hub_px["gradas_norte_acceso"]["pixel_y"], calibracion)
    x_gs, y_gs = pixel_a_xy(hub_px["gradas_sur_acceso"]["pixel_x"], hub_px["gradas_sur_acceso"]["pixel_y"], calibracion)
    x_a, y_a = 0.0, 0.0  # Salida A es el origen
    x_b, y_b = pixel_a_xy(
        calibracion["puntos_de_control"]["salida_B"]["pixel_x"],
        calibracion["puntos_de_control"]["salida_B"]["pixel_y"],
        calibracion,
    )

    d_sur_a = math.hypot(x_gs - x_a, y_gs - y_a)
    d_norte_b = math.hypot(x_gn - x_b, y_gn - y_b)

    if d_sur_a > DISTANCIA_MAXIMA_SALIDA_GRADAS_M:
        advertencias.append(
            f"Salida A esta a {d_sur_a:.1f} m del acceso a gradas sur (umbral: {DISTANCIA_MAXIMA_SALIDA_GRADAS_M:.0f} m)."
        )
    if d_norte_b > DISTANCIA_MAXIMA_SALIDA_GRADAS_M:
        advertencias.append(
            f"Salida B esta a {d_norte_b:.1f} m del acceso a gradas norte (umbral: {DISTANCIA_MAXIMA_SALIDA_GRADAS_M:.0f} m)."
        )
    return advertencias


def construir_grafo() -> tuple[dict[str, Any], list[str]]:
    """Construye el diccionario completo del grafo de evacuacion y devuelve (grafo, advertencias)."""
    config = cargar_configuracion()
    posiciones = cargar_json(POSICIONES_PATH)
    calibracion = cargar_json(CALIBRACION_PATH)
    datos_observaciones = cargar_json(OBSERVACIONES_PATH)
    observaciones = datos_observaciones["observaciones"]

    advertencias = verificar_distancia_salidas_a_gradas(posiciones, calibracion)

    lat0, lon0 = SALIDA_A["lat"], SALIDA_A["lon"]

    nodos_exteriores, puntos_encuentro = generar_nodos_exteriores(observaciones, lat0, lon0)
    aristas_exteriores = generar_aristas_exteriores(nodos_exteriores)

    nodos_interior, aristas_interior = generar_complejo_interior(config, posiciones, calibracion)

    nodos = nodos_exteriores + nodos_interior
    aristas = aristas_exteriores + aristas_interior

    grafo = {
        "metadata": {
            "version": "0.2.0-fase1bis-provisional",
            "fecha_actualizacion": "2026-10-26",
            "origen_x_y_m": "SALIDA-A (lat -0.313162, lon -78.445291)",
            "notes": (
                "Grafo PROVISIONAL de Fase 1-bis: complejo unico G/H/C/D (solo G y H son "
                "origenes), 2 secciones de gradas compartidas (norte, sur) y 2 salidas. "
                "Reconstruido sobre data/maps/plano_base_GH_anotado.jpeg calibrada "
                "(data/calibracion_plano.json, data/posiciones_plano.json). "
                "Ver docs/base_informe.md, seccion (c) para lo que falta verificar en campo."
            ),
            "provisional": True,
        },
        "nodos": nodos,
        "aristas": aristas,
        "puntos_encuentro": puntos_encuentro,
    }

    return grafo, advertencias


def resumir(grafo: dict[str, Any], advertencias: list[str]) -> str:
    """Genera un resumen legible del grafo construido."""
    nodos = grafo["nodos"]
    aristas = grafo["aristas"]

    conteo_tipo_nodos: dict[str, int] = {}
    for n in nodos:
        conteo_tipo_nodos[n["tipo"]] = conteo_tipo_nodos.get(n["tipo"], 0) + 1

    lineas = [
        f"Nodos totales: {len(nodos)}",
        f"Aristas totales: {len(aristas)}",
        f"Puntos de encuentro: {len(grafo['puntos_encuentro'])}",
        "Nodos por tipo:",
    ]
    for tipo, cantidad in sorted(conteo_tipo_nodos.items()):
        lineas.append(f"  {tipo}: {cantidad}")

    lineas.append(f"Advertencias ({len(advertencias)}):")
    if not advertencias:
        lineas.append("  Ninguna.")
    for adv in advertencias:
        lineas.append(f"  [ADVERTENCIA] {adv}")

    return "\n".join(lineas)


def main() -> int:
    """Punto de entrada del script."""
    grafo, advertencias = construir_grafo()

    with SALIDA_GRAFO_PATH.open("w", encoding="utf-8") as archivo:
        json.dump(grafo, archivo, ensure_ascii=False, indent=2)

    print(f"Grafo escrito en: {SALIDA_GRAFO_PATH}")
    print(resumir(grafo, advertencias))

    return 0


if __name__ == "__main__":
    sys.exit(main())
