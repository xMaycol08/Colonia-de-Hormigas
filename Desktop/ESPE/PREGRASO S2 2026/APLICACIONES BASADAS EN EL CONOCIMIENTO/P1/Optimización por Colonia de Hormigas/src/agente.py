"""Agente de evacuacion: ciclo percibir -> decidir -> actuar.

Ver docs/agente_peas.md para el analisis PEAS completo y la clasificacion
del entorno y del tipo de agente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aco import ejecutar_aco, ResultadoACO
from costos import tiempo_arista
from dijkstra import buscar_ruta, ResultadoDijkstra
from grafo import Grafo, aplicar_congestion


@dataclass
class EstadoPercibido:
    """Lo que el agente perceibe del entorno en un instante dado."""

    aristas_bloqueadas: frozenset[str] = frozenset()
    congestion: dict[str, float] = field(default_factory=dict)  # id_arista -> factor multiplicativo >= 1.0


@dataclass
class DecisionAgente:
    """Resultado de decidir(): lo que el agente planea hacer."""

    resultado_aco: ResultadoACO
    resultado_dijkstra: ResultadoDijkstra | None


class AgenteEvacuacion:
    """Agente que guia a una persona desde un origen hasta un punto de encuentro.

    Ciclo de vida tipico:
        agente = AgenteEvacuacion(grafo, config_modelo, config_aco, origen)
        agente.percibir(EstadoPercibido(aristas_bloqueadas=frozenset({"H-PB-SALIDA"})))
        decision = agente.decidir(comparar_con_dijkstra=True)
        instrucciones, tiempo_s = agente.actuar()
    """

    def __init__(
        self,
        grafo: Grafo,
        config_modelo: dict[str, Any],
        config_aco: dict[str, Any],
        origen: str,
    ) -> None:
        self.grafo = grafo
        self.config_modelo = config_modelo
        self.config_aco = config_aco
        self.origen = origen

        self.estado = EstadoPercibido()
        self._feromona_previa: dict[str, float] | None = None
        self._ultima_decision: DecisionAgente | None = None

    def percibir(self, estado: EstadoPercibido) -> None:
        """Actualiza el estado percibido del entorno (aristas bloqueadas y congestion)."""
        self.estado = estado

    def _grafo_con_congestion(self) -> Grafo:
        """Devuelve un Grafo cuyas aristas tienen distancia_m escalada por congestion.

        La congestion no es parte de costos.costo_arista() (Tarea A la define
        sin congestion); el agente modela la congestion inflando la
        distancia_m efectiva de las aristas congestionadas antes de llamar a
        Dijkstra/ACO (grafo.aplicar_congestion). Decision de diseno de la
        Fase 2: ver docs/decisiones_fase2.md.
        """
        return aplicar_congestion(self.grafo, self.estado.congestion)

    def decidir(
        self,
        comparar_con_dijkstra: bool = False,
        usar_warm_start: bool = True,
        semilla: int | None = None,
    ) -> DecisionAgente:
        """Decide la ruta a seguir: corre ACO (con warm start si hay una solucion previa).

        Si comparar_con_dijkstra=True, tambien corre Dijkstra para contraste
        (no se usa para decidir, solo informativo / para metricas).
        """
        grafo_efectivo = self._grafo_con_congestion()

        feromona_inicial = self._feromona_previa if usar_warm_start else None

        resultado_aco = ejecutar_aco(
            grafo_efectivo,
            self.origen,
            self.config_modelo,
            self.config_aco,
            aristas_bloqueadas=self.estado.aristas_bloqueadas,
            feromona_inicial=feromona_inicial,
            semilla=semilla,
        )
        self._feromona_previa = resultado_aco.feromona_final

        resultado_dijkstra = None
        if comparar_con_dijkstra:
            resultado_dijkstra = buscar_ruta(
                grafo_efectivo,
                self.origen,
                self.config_modelo,
                aristas_bloqueadas=self.estado.aristas_bloqueadas,
            )

        self._ultima_decision = DecisionAgente(resultado_aco=resultado_aco, resultado_dijkstra=resultado_dijkstra)
        return self._ultima_decision

    def actuar(self) -> tuple[list[str], float]:
        """Devuelve (instrucciones legibles, tiempo_estimado_s) de la ultima decision.

        Lanza RuntimeError si aun no se llamo a decidir(), o ValueError si la
        ultima decision no encontro ruta.
        """
        if self._ultima_decision is None:
            raise RuntimeError("Llama a decidir() antes de actuar().")

        resultado = self._ultima_decision.resultado_aco
        if not resultado.tiene_ruta:
            raise ValueError("No hay ruta disponible (todas las salidas relevantes estan bloqueadas).")

        instrucciones = generar_instrucciones(self.grafo, resultado.mejor_camino)
        tiempo_total_s = sum(
            tiempo_arista(arista, self.config_modelo)
            for arista in _aristas_en_orden(self.grafo, resultado.mejor_camino)
        )
        return instrucciones, tiempo_total_s


def _aristas_en_orden(grafo: Grafo, camino: list[str]) -> list[dict[str, Any]]:
    """Devuelve la lista de aristas (en orden) recorridas por un camino de nodos."""
    aristas = []
    for a, b in zip(camino, camino[1:]):
        for vecino_id, arista in grafo.vecinos(a):
            if vecino_id == b:
                aristas.append(arista)
                break
    return aristas


def generar_instrucciones(grafo: Grafo, camino: list[str]) -> list[str]:
    """Convierte una secuencia de nodos en instrucciones legibles para una persona.

    Ejemplo: "Piso 3, bloque H -> baja por escalera 2 -> Salida A -> PE-1 (provisional)".
    """
    pasos: list[str] = []
    nodo_anterior = None

    for nodo_id in camino:
        nodo = grafo.nodos_por_id[nodo_id]
        tipo = nodo["tipo"]

        if tipo == "aula":
            pasos.append(f"Sale del {nodo['nombre']}")
        elif tipo == "pasillo":
            if nodo_anterior is None or grafo.nodos_por_id[nodo_anterior]["tipo"] != "pasillo":
                pasos.append(f"Camina por el pasillo del piso {nodo['piso']}, bloque {nodo['bloque']}")
        elif tipo == "gradas":
            nombre_escalera = nodo["nombre"]
            if nodo_anterior is not None and grafo.nodos_por_id[nodo_anterior]["tipo"] == "gradas":
                piso_anterior = grafo.nodos_por_id[nodo_anterior]["piso"]
                direccion = "baja" if nodo["piso"] < piso_anterior else "sube"
                pasos.append(f"{direccion.capitalize()} por {nombre_escalera}")
            else:
                pasos.append(f"Toma {nombre_escalera}")
        elif tipo == "salida":
            pasos.append(f"Sale por {nodo['id']}")
        elif tipo == "via_exterior":
            pasos.append(f"Camina por {nodo['nombre']}")
        elif tipo == "punto_encuentro":
            pasos.append(f"Llega a {nodo['nombre']}")

        nodo_anterior = nodo_id

    return pasos
