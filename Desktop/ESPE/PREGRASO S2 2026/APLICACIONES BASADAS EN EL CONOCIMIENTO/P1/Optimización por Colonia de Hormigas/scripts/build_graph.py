"""Construye el grafo de evacuacion provisional de los bloques G y H (Fase 1).

Lee data/config_modelo.json (todos los numeros del modelo) y
data/raw/maps_observations.json (coordenadas reales medidas en Maps en Fase 0/1),
y genera data/campus_graph.json siguiendo data/campus_graph.schema.json.

No implementa ACO ni Dijkstra. Solo construye la estructura de datos del grafo,
con todos los supuestos marcados como tales (confidence "supuesto", status
"provisional") segun las reglas de la Fase 1.

Uso:
    python scripts/build_graph.py
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
OBSERVACIONES_PATH = RAIZ_PROYECTO / "data" / "raw" / "maps_observations.json"
SALIDA_GRAFO_PATH = RAIZ_PROYECTO / "data" / "campus_graph.json"

# Datos dados por el equipo (no son numeros "del modelo" en el sentido de
# config_modelo.json: son coordenadas de campo, igual que las de
# maps_observations.json, asi que se tratan igual: fijas aqui como las demas
# coordenadas medidas, con su propio nivel de confianza).
SALIDA_A = {"id": "SALIDA-A", "lat": -0.313162, "lon": -78.445291, "bloque": "H"}
SALIDA_B = {"id": "SALIDA-B", "lat": -0.312607, "lon": -78.445237, "bloque": "G"}

DISTANCIA_MAXIMA_SALIDA_BLOQUE_M = 40.0


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


def generar_nodos_exteriores(
    observaciones: list[dict[str, Any]], lat0: float, lon0: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Genera los nodos exteriores: Salida A, Salida B, caminos de Maps y puntos de encuentro.

    Devuelve (nodos, puntos_encuentro_detalle). Los puntos de encuentro se
    agregan tanto a 'nodos' (tipo punto_encuentro, para la logica de caminos
    del grafo) como a una lista aparte con los campos extra del schema
    'puntos_encuentro' (area_aprox_m2, etc.).
    """
    nodos: list[dict[str, Any]] = []

    for salida in (SALIDA_A, SALIDA_B):
        x_m, y_m = proyectar_xy(salida["lat"], salida["lon"], lat0, lon0)
        nodos.append(
            nodo(
                id=salida["id"],
                nombre=f"{salida['id']} (bloques {'C y H' if salida['id'] == 'SALIDA-A' else 'G y D'})",
                tipo="salida",
                bloque=salida["bloque"],
                piso=1,
                lat=salida["lat"],
                lon=salida["lon"],
                x_m=x_m,
                y_m=y_m,
                techado=False,
                riesgo_caida=None,
                capacidad_estimada_personas=None,
                source="Coordenadas dadas por el equipo (Fase 1), leidas en Maps",
                confidence="medido_en_maps",
                status="pendiente",
                notes="indicado por el equipo, por verificar en campo",
            )
        )

    ids_caminos_usados: list[str] = []
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
        ids_caminos_usados.append(obs["id"])

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
        id_pe = nombres_pe[id_obs].split(" ")[0]  # "PE-1", "PE-2", "PE-3"
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
                    "senalizado por la ESPE. Los 14 puntos de encuentro reales del campus "
                    "Matriz (Guia de simulacros, USIN-GS-v1-2019-013) no tienen ubicacion "
                    "conocida (ver docs/restricciones_oficiales.md). Reemplazar cuando se "
                    "verifique la senaletica real en campo."
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
                "notes": (
                    "Provisional: area abierta candidata leida en Maps, sin confirmar que "
                    "corresponda a senaletica oficial de punto de encuentro. "
                    f"Observacion original: {id_obs}."
                ),
            }
        )

    return nodos, puntos_encuentro_detalle


def construir_arbol_expansion_minima(
    nodos_exteriores: list[dict[str, Any]],
) -> list[tuple[str, str, float]]:
    """Construye un arbol de expansion minima (Prim) sobre los nodos exteriores, usando haversine.

    Esta es una conectividad APROXIMADA: conecta cada nodo exterior con su
    vecino mas cercano hasta formar un unico componente conexo. No representa
    el trazado real de las rutas peatonales (Fase 0 solo cubrio una porcion
    pequena de los caminos del campus); es un supuesto de conectividad minima
    para que el grafo sea navegable mientras se completa el levantamiento.
    """
    if len(nodos_exteriores) < 2:
        return []

    pendientes = {n["id"]: n for n in nodos_exteriores}
    primer_id = nodos_exteriores[0]["id"]
    en_arbol = {primer_id}
    del pendientes[primer_id]

    aristas_mst: list[tuple[str, str, float]] = []
    nodos_por_id = {n["id"]: n for n in nodos_exteriores}

    while pendientes:
        mejor = None  # (distancia, desde, hasta)
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
                notes=(
                    "Conectividad exterior aproximada (no es el trazado real del camino); "
                    "la distancia_m si es haversine exacta entre los dos puntos medidos. "
                    "Pendiente verificar el trazado real en campo."
                ),
            )
        )
    return aristas


def generar_bloque_interior(
    letra_bloque: str,
    nodo_salida: dict[str, Any],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Genera los nodos y aristas interiores (aulas, pasillo, gradas) de un bloque, todos los pisos."""
    nodos: list[dict[str, Any]] = []
    aristas: list[dict[str, Any]] = []

    pisos = int(config["pisos_por_bloque"])
    n_escaleras = int(config["escaleras_por_bloque"])
    n_aulas = int(config["aulas_por_piso_por_bloque"])
    espaciado = config["espaciado_aula_m"]
    altura_piso = config["altura_piso_m"]

    base_x, base_y = nodo_salida["x_m"], nodo_salida["y_m"]

    ids_pasillo_por_piso: dict[int, str] = {}
    ids_gradas_por_piso: dict[int, list[str]] = {}

    notes_interior = (
        "Dato interior PROVISIONAL (supuesto del equipo, Fase 1). Google Maps no "
        "muestra interiores (ver docs/restricciones_oficiales.md); reemplazar con "
        "la ficha de campo (data/campo/FICHA_TRABAJO_DE_CAMPO.md)."
    )
    source_interior = "data/config_modelo.json (supuesto de equipo, Fase 1)"

    for piso in range(1, pisos + 1):
        y_piso = base_y + (piso - 1) * altura_piso

        id_pasillo = f"{letra_bloque}-P{piso}-PAS"
        ids_pasillo_por_piso[piso] = id_pasillo
        nodos.append(
            nodo(
                id=id_pasillo,
                nombre=f"Pasillo piso {piso}, bloque {letra_bloque}",
                tipo="pasillo",
                bloque=letra_bloque,
                piso=piso,
                lat=None,
                lon=None,
                x_m=base_x,
                y_m=y_piso,
                techado=True,
                riesgo_caida=False,
                capacidad_estimada_personas=None,
                source=source_interior,
                confidence="supuesto",
                status="provisional",
                notes=notes_interior,
            )
        )

        for i in range(1, n_aulas + 1):
            id_aula = f"{letra_bloque}-P{piso}-AULA{i:02d}"
            x_aula = base_x + (i - (n_aulas + 1) / 2) * espaciado
            y_aula = y_piso + espaciado / 2
            nodos.append(
                nodo(
                    id=id_aula,
                    nombre=f"Aula {i:02d}, piso {piso}, bloque {letra_bloque}",
                    tipo="aula",
                    bloque=letra_bloque,
                    piso=piso,
                    lat=None,
                    lon=None,
                    x_m=round(x_aula, 2),
                    y_m=round(y_aula, 2),
                    techado=True,
                    riesgo_caida=False,
                    capacidad_estimada_personas=None,
                    source=source_interior,
                    confidence="supuesto",
                    status="provisional",
                    notes=notes_interior,
                )
            )
            aristas.append(
                arista(
                    id=f"{letra_bloque}-P{piso}-A{id_aula[-2:]}-PAS",
                    desde=id_aula,
                    hasta=id_pasillo,
                    distancia_m=config["distancia_aula_a_pasillo_m"],
                    tipo="plano",
                    techado=True,
                    ancho_m=config["ancho_pasillo_m"],
                    bloqueable=False,
                    source=source_interior,
                    confidence="supuesto",
                    status="provisional",
                    notes=notes_interior,
                )
            )

        ids_gradas_piso = []
        for s in range(1, n_escaleras + 1):
            id_gradas = f"{letra_bloque}-P{piso}-GRADA{s:02d}"
            ids_gradas_piso.append(id_gradas)
            x_gradas = base_x + (s - (n_escaleras + 1) / 2) * (espaciado * 0.6)
            y_gradas = y_piso - espaciado / 2
            nodos.append(
                nodo(
                    id=id_gradas,
                    nombre=f"Gradas {s:02d}, piso {piso}, bloque {letra_bloque}",
                    tipo="gradas",
                    bloque=letra_bloque,
                    piso=piso,
                    lat=None,
                    lon=None,
                    x_m=round(x_gradas, 2),
                    y_m=round(y_gradas, 2),
                    techado=True,
                    riesgo_caida=False,
                    capacidad_estimada_personas=None,
                    source=source_interior,
                    confidence="supuesto",
                    status="provisional",
                    notes=notes_interior,
                )
            )
            aristas.append(
                arista(
                    id=f"{letra_bloque}-P{piso}-G{s:02d}-PAS",
                    desde=id_gradas,
                    hasta=id_pasillo,
                    distancia_m=config["distancia_gradas_a_pasillo_m"],
                    tipo="plano",
                    techado=True,
                    ancho_m=config["ancho_pasillo_m"],
                    bloqueable=False,
                    source=source_interior,
                    confidence="supuesto",
                    status="provisional",
                    notes=notes_interior,
                )
            )
        ids_gradas_por_piso[piso] = ids_gradas_piso

    for piso in range(2, pisos + 1):
        distancia_gradas = altura_piso * config["factor_costo_gradas"] + config["tramo_horizontal_gradas_m"]
        for s in range(1, n_escaleras + 1):
            id_arriba = ids_gradas_por_piso[piso][s - 1]
            id_abajo = ids_gradas_por_piso[piso - 1][s - 1]
            aristas.append(
                arista(
                    id=f"{letra_bloque}-GRADA{s:02d}-P{piso - 1}-P{piso}",
                    desde=id_arriba,
                    hasta=id_abajo,
                    distancia_m=round(distancia_gradas, 2),
                    tipo="gradas",
                    techado=True,
                    ancho_m=config["ancho_gradas_m"],
                    bloqueable=True,
                    source=source_interior,
                    confidence="supuesto",
                    status="provisional",
                    notes=notes_interior,
                )
            )

    id_pasillo_pb = ids_pasillo_por_piso[1]
    aristas.append(
        arista(
            id=f"{letra_bloque}-PB-SALIDA",
            desde=id_pasillo_pb,
            hasta=nodo_salida["id"],
            distancia_m=config["distancia_pasillo_a_salida_m"],
            tipo="puerta",
            techado=False,
            ancho_m=config["ancho_puerta_salida_m"],
            bloqueable=True,
            source=source_interior,
            confidence="supuesto",
            status="provisional",
            notes=notes_interior,
        )
    )

    return nodos, aristas


def verificar_distancia_salidas(
    observaciones: list[dict[str, Any]],
) -> list[str]:
    """Verifica que Salida A y Salida B esten a menos de 40 m del bloque correspondiente.

    Devuelve una lista de advertencias (no rechaza ninguna coordenada).
    """
    advertencias = []
    esquinas_h = [o for o in observaciones if o["id"].startswith("corner_h_")]
    esquinas_g = [o for o in observaciones if o["id"].startswith("corner_g_")]

    for salida, esquinas, letra in ((SALIDA_A, esquinas_h, "H"), (SALIDA_B, esquinas_g, "G")):
        distancias = [
            distancia_haversine_m(salida["lat"], salida["lon"], e["lat"], e["lon"]) for e in esquinas
        ]
        distancia_minima = min(distancias) if distancias else None
        if distancia_minima is None:
            advertencias.append(
                f"No hay esquinas registradas del bloque {letra} en maps_observations.json; "
                f"no se pudo verificar la distancia de {salida['id']}."
            )
        elif distancia_minima > DISTANCIA_MAXIMA_SALIDA_BLOQUE_M:
            advertencias.append(
                f"{salida['id']} esta a {distancia_minima:.1f} m de la esquina mas cercana "
                f"del bloque {letra} (umbral: {DISTANCIA_MAXIMA_SALIDA_BLOQUE_M:.0f} m). "
                "No se rechaza la coordenada; verificar en campo."
            )
    return advertencias


def construir_grafo() -> tuple[dict[str, Any], list[str]]:
    """Construye el diccionario completo del grafo de evacuacion y devuelve (grafo, advertencias)."""
    config = cargar_configuracion()
    datos_observaciones = cargar_json(OBSERVACIONES_PATH)
    observaciones = datos_observaciones["observaciones"]

    advertencias = verificar_distancia_salidas(observaciones)

    lat0, lon0 = SALIDA_A["lat"], SALIDA_A["lon"]

    nodos_exteriores, puntos_encuentro = generar_nodos_exteriores(observaciones, lat0, lon0)
    aristas_exteriores = generar_aristas_exteriores(nodos_exteriores)

    nodo_salida_a = next(n for n in nodos_exteriores if n["id"] == "SALIDA-A")
    nodo_salida_b = next(n for n in nodos_exteriores if n["id"] == "SALIDA-B")

    nodos_h, aristas_h = generar_bloque_interior("H", nodo_salida_a, config)
    nodos_g, aristas_g = generar_bloque_interior("G", nodo_salida_b, config)

    id_pasillo_pb_h = "H-P1-PAS"
    id_pasillo_pb_g = "G-P1-PAS"
    arista_conexion_h_g = arista(
        id="CONEXION-PB-H-G",
        desde=id_pasillo_pb_h,
        hasta=id_pasillo_pb_g,
        distancia_m=config["conexion_planta_baja_G_H_m"],
        tipo="plano",
        techado=True,
        ancho_m=config["ancho_pasillo_m"],
        bloqueable=False,
        source="data/config_modelo.json (dato dado por el equipo, Fase 1)",
        confidence="supuesto",
        status="provisional",
        notes=(
            "G y H comparten el mismo edificio: en planta baja se puede pasar de un "
            "bloque al otro y salir por cualquiera de las dos salidas. Distancia tomada "
            "tal cual del parametro conexion_planta_baja_G_H_m, no es haversine."
        ),
    )

    nodos = nodos_exteriores + nodos_h + nodos_g
    aristas = aristas_exteriores + aristas_h + aristas_g + [arista_conexion_h_g]

    grafo = {
        "metadata": {
            "version": "0.1.0-fase1-provisional",
            "fecha_actualizacion": "2026-10-25",
            "origen_x_y_m": "SALIDA-A (lat -0.313162, lon -78.445291)",
            "notes": (
                "Grafo PROVISIONAL de Fase 1 para los bloques G y H. Contiene supuestos "
                "de interior (pisos, aulas, gradas) y 3 puntos de encuentro provisionales "
                "no oficiales. Ver data/pendientes.md para lo que falta verificar en campo."
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

    conteo_confidence_nodos: dict[str, int] = {}
    for n in nodos:
        conteo_confidence_nodos[n["confidence"]] = conteo_confidence_nodos.get(n["confidence"], 0) + 1

    conteo_confidence_aristas: dict[str, int] = {}
    for a in aristas:
        conteo_confidence_aristas[a["confidence"]] = conteo_confidence_aristas.get(a["confidence"], 0) + 1

    lineas = [
        f"Nodos totales: {len(nodos)}",
        f"Aristas totales: {len(aristas)}",
        f"Puntos de encuentro: {len(grafo['puntos_encuentro'])}",
        "Nodos por confidence:",
    ]
    for conf, cantidad in sorted(conteo_confidence_nodos.items()):
        porcentaje = cantidad / len(nodos) * 100
        lineas.append(f"  {conf}: {cantidad} ({porcentaje:.1f}%)")
    lineas.append("Aristas por confidence:")
    for conf, cantidad in sorted(conteo_confidence_aristas.items()):
        porcentaje = cantidad / len(aristas) * 100
        lineas.append(f"  {conf}: {cantidad} ({porcentaje:.1f}%)")

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
