"""Valida el grafo de evacuacion (bloques G y H) contra el schema y reglas de consistencia.

Uso:
    python scripts/validate_graph.py [ruta_al_json]

Si no se pasa ruta, usa data/campus_graph.template.json por defecto.

Esta herramienta pertenece a la Fase 0 (solo recoleccion y validacion de datos).
No calcula rutas optimas ni ejecuta ACO/Dijkstra; solo verifica que los datos
sean estructuralmente correctos y razonablemente consistentes.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import jsonschema

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = RAIZ_PROYECTO / "data" / "campus_graph.schema.json"
TEMPLATE_PATH = RAIZ_PROYECTO / "data" / "campus_graph.template.json"

TOLERANCIA_DISTANCIA = 0.25  # 25%
TIPOS_ORIGEN_CAMINO = {"aula", "pasillo", "gradas"}


class ResultadoValidacion:
    """Acumula errores graves y advertencias de una corrida de validacion."""

    def __init__(self) -> None:
        self.errores: list[str] = []
        self.advertencias: list[str] = []

    def error(self, mensaje: str) -> None:
        self.errores.append(mensaje)

    def advertencia(self, mensaje: str) -> None:
        self.advertencias.append(mensaje)

    @property
    def tiene_errores_graves(self) -> bool:
        return len(self.errores) > 0


def cargar_json(ruta: Path) -> dict[str, Any]:
    """Carga un archivo JSON desde disco."""
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def validar_contra_schema(datos: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Valida los datos contra el JSON Schema y devuelve una lista de mensajes de error."""
    validador = jsonschema.Draft7Validator(schema)
    errores = sorted(validador.iter_errors(datos), key=lambda e: list(e.path))
    mensajes = []
    for err in errores:
        ruta_campo = "/".join(str(p) for p in err.path) or "(raiz)"
        mensajes.append(f"{ruta_campo}: {err.message}")
    return mensajes


def calcular_porcentaje_pendientes(elementos: list[dict[str, Any]]) -> dict[str, float]:
    """Calcula el porcentaje de campos con status 'pendiente' sobre el total de campos."""
    if not elementos:
        return {"total_elementos": 0, "porcentaje_campos_pendientes": 0.0}

    total_campos = 0
    campos_pendientes = 0
    for elemento in elementos:
        for clave, valor in elemento.items():
            total_campos += 1
            if clave == "status" and valor == "pendiente":
                campos_pendientes += 1
            elif valor is None:
                campos_pendientes += 1

    porcentaje = (campos_pendientes / total_campos * 100) if total_campos else 0.0
    return {
        "total_elementos": len(elementos),
        "porcentaje_campos_pendientes": round(porcentaje, 1),
    }


def detectar_ids_duplicados(elementos: list[dict[str, Any]], nombre_tipo: str, resultado: ResultadoValidacion) -> None:
    """Detecta IDs duplicados dentro de una lista de elementos (nodos, aristas o puntos de encuentro)."""
    vistos: dict[str, int] = {}
    for elemento in elementos:
        id_elemento = elemento.get("id")
        vistos[id_elemento] = vistos.get(id_elemento, 0) + 1
    for id_elemento, cantidad in vistos.items():
        if cantidad > 1:
            resultado.error(f"ID duplicado en {nombre_tipo}: '{id_elemento}' aparece {cantidad} veces.")


def detectar_aristas_con_nodos_inexistentes(
    nodos: list[dict[str, Any]], aristas: list[dict[str, Any]], resultado: ResultadoValidacion
) -> None:
    """Detecta aristas cuyo 'desde' o 'hasta' no corresponde a ningun nodo existente."""
    ids_nodos = {n.get("id") for n in nodos}
    for arista in aristas:
        if arista.get("desde") not in ids_nodos:
            resultado.error(
                f"Arista '{arista.get('id')}' referencia un nodo origen inexistente: '{arista.get('desde')}'."
            )
        if arista.get("hasta") not in ids_nodos:
            resultado.error(
                f"Arista '{arista.get('id')}' referencia un nodo destino inexistente: '{arista.get('hasta')}'."
            )


def detectar_nodos_aislados(
    nodos: list[dict[str, Any]], aristas: list[dict[str, Any]], resultado: ResultadoValidacion
) -> None:
    """Detecta nodos que no aparecen como origen ni destino de ninguna arista."""
    ids_en_aristas = set()
    for arista in aristas:
        ids_en_aristas.add(arista.get("desde"))
        ids_en_aristas.add(arista.get("hasta"))

    for nodo in nodos:
        if nodo.get("id") not in ids_en_aristas:
            resultado.error(f"Nodo aislado (sin ninguna arista): '{nodo.get('id')}'.")


def construir_grafo_no_dirigido(aristas: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Construye un grafo no dirigido (lista de adyacencia) a partir de las aristas."""
    adyacencia: dict[str, set[str]] = {}
    for arista in aristas:
        desde, hasta = arista.get("desde"), arista.get("hasta")
        adyacencia.setdefault(desde, set()).add(hasta)
        adyacencia.setdefault(hasta, set()).add(desde)
    return adyacencia


def existe_camino(origen: str, destinos: set[str], adyacencia: dict[str, set[str]]) -> bool:
    """Busqueda en amplitud (BFS) para verificar si existe un camino de 'origen' a algun nodo en 'destinos'."""
    if origen in destinos:
        return True
    visitados = {origen}
    pendientes = [origen]
    while pendientes:
        actual = pendientes.pop()
        for vecino in adyacencia.get(actual, set()):
            if vecino in destinos:
                return True
            if vecino not in visitados:
                visitados.add(vecino)
                pendientes.append(vecino)
    return False


def verificar_caminos_a_punto_encuentro(
    nodos: list[dict[str, Any]], aristas: list[dict[str, Any]], resultado: ResultadoValidacion
) -> None:
    """Verifica que todo nodo tipo aula/pasillo/gradas tenga camino a algun nodo tipo punto_encuentro."""
    ids_puntos_encuentro = {n.get("id") for n in nodos if n.get("tipo") == "punto_encuentro"}
    adyacencia = construir_grafo_no_dirigido(aristas)

    if not ids_puntos_encuentro:
        resultado.error(
            "No existe ningun nodo con tipo='punto_encuentro' en la lista de nodos; "
            "no se puede verificar conectividad hacia puntos de encuentro."
        )
        return

    for nodo in nodos:
        if nodo.get("tipo") in TIPOS_ORIGEN_CAMINO:
            if not existe_camino(nodo.get("id"), ids_puntos_encuentro, adyacencia):
                resultado.error(
                    f"El nodo '{nodo.get('id')}' (tipo={nodo.get('tipo')}) no tiene camino "
                    "a ningun nodo tipo 'punto_encuentro'."
                )


def verificar_salidas_por_bloque(nodos: list[dict[str, Any]], resultado: ResultadoValidacion) -> None:
    """Verifica que los bloques G y H tengan cada uno al menos un nodo tipo 'salida'."""
    for bloque in ("G", "H"):
        tiene_salida = any(n.get("bloque") == bloque and n.get("tipo") == "salida" for n in nodos)
        if not tiene_salida:
            resultado.error(f"El bloque '{bloque}' no tiene ningun nodo tipo 'salida'.")


def distancia_haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia haversine en metros entre dos coordenadas geograficas."""
    radio_tierra_m = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radio_tierra_m * c


def verificar_distancias_contra_haversine(
    nodos: list[dict[str, Any]], aristas: list[dict[str, Any]], resultado: ResultadoValidacion
) -> None:
    """Compara distancia_m de cada arista contra la distancia haversine entre sus nodos.

    Tolerancia: 25%. Para aristas tipo 'gradas' solo se reporta si distancia_m es
    MENOR que la haversine (una escalera siempre recorre igual o mas distancia que
    la linea recta entre sus extremos).
    """
    nodos_por_id = {n.get("id"): n for n in nodos}

    for arista in aristas:
        distancia_declarada = arista.get("distancia_m")
        nodo_desde = nodos_por_id.get(arista.get("desde"))
        nodo_hasta = nodos_por_id.get(arista.get("hasta"))

        if distancia_declarada is None or nodo_desde is None or nodo_hasta is None:
            continue

        lat1, lon1 = nodo_desde.get("lat"), nodo_desde.get("lon")
        lat2, lon2 = nodo_hasta.get("lat"), nodo_hasta.get("lon")
        if None in (lat1, lon1, lat2, lon2):
            continue

        distancia_haversine = distancia_haversine_m(lat1, lon1, lat2, lon2)
        if distancia_haversine == 0:
            continue

        diferencia_relativa = abs(distancia_declarada - distancia_haversine) / distancia_haversine

        if arista.get("tipo") == "gradas":
            if distancia_declarada < distancia_haversine:
                resultado.advertencia(
                    f"Arista '{arista.get('id')}' (gradas): distancia_m={distancia_declarada} "
                    f"es menor que la haversine ({distancia_haversine:.1f} m); "
                    "una escalera deberia recorrer al menos la distancia en linea recta."
                )
            continue

        if diferencia_relativa > TOLERANCIA_DISTANCIA:
            resultado.advertencia(
                f"Arista '{arista.get('id')}': distancia_m={distancia_declarada} difiere "
                f"{diferencia_relativa * 100:.1f}% de la haversine ({distancia_haversine:.1f} m), "
                f"supera la tolerancia de {TOLERANCIA_DISTANCIA * 100:.0f}%."
            )


def validar(datos: dict[str, Any], schema: dict[str, Any]) -> tuple[ResultadoValidacion, dict[str, Any]]:
    """Ejecuta todas las validaciones y devuelve el resultado junto con un resumen de metricas."""
    resultado = ResultadoValidacion()

    errores_schema = validar_contra_schema(datos, schema)
    for mensaje in errores_schema:
        resultado.error(f"[schema] {mensaje}")

    nodos = datos.get("nodos", [])
    aristas = datos.get("aristas", [])
    puntos_encuentro = datos.get("puntos_encuentro", [])

    detectar_ids_duplicados(nodos, "nodos", resultado)
    detectar_ids_duplicados(aristas, "aristas", resultado)
    detectar_ids_duplicados(puntos_encuentro, "puntos_encuentro", resultado)

    detectar_aristas_con_nodos_inexistentes(nodos, aristas, resultado)
    detectar_nodos_aislados(nodos, aristas, resultado)
    verificar_caminos_a_punto_encuentro(nodos, aristas, resultado)
    verificar_salidas_por_bloque(nodos, resultado)
    verificar_distancias_contra_haversine(nodos, aristas, resultado)

    resumen = {
        "nodos": calcular_porcentaje_pendientes(nodos),
        "aristas": calcular_porcentaje_pendientes(aristas),
        "puntos_encuentro": calcular_porcentaje_pendientes(puntos_encuentro),
    }

    return resultado, resumen


def imprimir_reporte(resultado: ResultadoValidacion, resumen: dict[str, Any], ruta_datos: Path) -> None:
    """Imprime un reporte legible en consola."""
    print("=" * 70)
    print(f"Validacion de grafo de evacuacion: {ruta_datos}")
    print("=" * 70)

    print("\n-- Porcentaje de campos pendientes por tipo de elemento --")
    for tipo_elemento, datos_tipo in resumen.items():
        print(
            f"  {tipo_elemento}: {datos_tipo['total_elementos']} elemento(s), "
            f"{datos_tipo['porcentaje_campos_pendientes']}% de campos pendientes"
        )

    print(f"\n-- Errores graves ({len(resultado.errores)}) --")
    if not resultado.errores:
        print("  Ninguno.")
    for mensaje in resultado.errores:
        print(f"  [ERROR] {mensaje}")

    print(f"\n-- Advertencias ({len(resultado.advertencias)}) --")
    if not resultado.advertencias:
        print("  Ninguna.")
    for mensaje in resultado.advertencias:
        print(f"  [ADVERTENCIA] {mensaje}")

    print("\n" + "=" * 70)
    if resultado.tiene_errores_graves:
        print("RESULTADO: errores graves encontrados.")
    else:
        print("RESULTADO: sin errores graves.")
    print("=" * 70)


def main() -> int:
    """Punto de entrada del script. Devuelve el exit code del proceso."""
    ruta_datos = Path(sys.argv[1]) if len(sys.argv) > 1 else TEMPLATE_PATH

    schema = cargar_json(SCHEMA_PATH)
    datos = cargar_json(ruta_datos)

    resultado, resumen = validar(datos, schema)
    imprimir_reporte(resultado, resumen, ruta_datos)

    return 1 if resultado.tiene_errores_graves else 0


if __name__ == "__main__":
    sys.exit(main())
