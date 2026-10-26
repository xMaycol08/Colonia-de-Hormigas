"""Pruebas de Fase 3: variante ACO clasico, no regresion del guiado y escenarios compartidos."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from aco import aco_iterativo, ejecutar_aco, parametros_clasico  # noqa: E402
from dijkstra import buscar_ruta  # noqa: E402
from escenarios import ESCENARIOS_DISPONIBLES, construir_escenario  # noqa: E402
from grafo import CONFIG_ACO_PATH, CONFIG_MODELO_PATH, aplicar_congestion, cargar_configuracion, cargar_grafo, cargar_json  # noqa: E402

GRAFO = cargar_grafo()
CM = cargar_configuracion(CONFIG_MODELO_PATH)
CA = cargar_configuracion(CONFIG_ACO_PATH)
CA_CLASICO = parametros_clasico(CA)

# Valores de referencia calculados con el src/aco.py anterior a Fase 3 (commit 5d73477).
REFERENCIA_GUIADO = [
    ("H403", 0, 223.36, 1, 26, "H403>PAS-H-4>PAS-CENTRAL-4>GRADAS-NORTE-4>GRADAS-NORTE-3>GRADAS-NORTE-2>GRADAS-NORTE-1>GRADAS-NORTE-PB>SALIDA-B>PE-2"),
    ("H203", 1, 192.16, 2, 27, "H203>PAS-H-2>PAS-CENTRAL-2>GRADAS-NORTE-2>GRADAS-NORTE-1>GRADAS-NORTE-PB>SALIDA-B>PE-2"),
    ("G-PB-LAB_BIOTEC", 2, 163.39, 1, 26, "G-PB-LAB_BIOTEC>PAS-G-PB>PAS-CENTRAL-PB>GRADAS-NORTE-PB>SALIDA-B>PE-2"),
    ("G301", 7, 210.19, 1, 26, "G301>PAS-G-3>PAS-CENTRAL-3>GRADAS-NORTE-3>GRADAS-NORTE-2>GRADAS-NORTE-1>GRADAS-NORTE-PB>SALIDA-B>PE-2"),
]


@pytest.mark.parametrize("origen,semilla,costo,iteracion,n_iter,ruta", REFERENCIA_GUIADO)
def test_guiado_no_cambia_respecto_a_la_version_anterior(origen, semilla, costo, iteracion, n_iter, ruta):
    r = ejecutar_aco(GRAFO, origen, CM, CA, semilla=semilla)
    assert r.mejor_costo == pytest.approx(costo, abs=1e-6)
    assert r.iteracion_mejor_solucion == iteracion
    assert len(r.historial) == n_iter
    assert ">".join(r.mejor_camino) == ruta


def test_guiado_es_la_variante_por_defecto():
    a = ejecutar_aco(GRAFO, "H301", CM, CA, semilla=5)
    b = ejecutar_aco(GRAFO, "H301", CM, CA, semilla=5, variante="guiado")
    assert a.mejor_camino == b.mejor_camino and a.mejor_costo == b.mejor_costo


def test_variante_desconocida_lanza_error():
    with pytest.raises(ValueError):
        ejecutar_aco(GRAFO, "H301", CM, CA, semilla=1, variante="otra")


def test_clasico_es_reproducible_con_la_misma_semilla():
    a = ejecutar_aco(GRAFO, "H401", CM, CA_CLASICO, semilla=11, variante="clasico")
    b = ejecutar_aco(GRAFO, "H401", CM, CA_CLASICO, semilla=11, variante="clasico")
    assert a.mejor_camino == b.mejor_camino
    assert a.mejor_costo == b.mejor_costo
    assert a.feromona_final == b.feromona_final


def test_clasico_no_poda_nodos():
    r = ejecutar_aco(GRAFO, "H201", CM, CA_CLASICO, semilla=1, variante="clasico")
    assert r.nodos_podados == frozenset()


def test_clasico_usa_parametros_de_la_seccion_clasico():
    assert CA_CLASICO["beta"] == 2.0
    assert CA_CLASICO["alfa"] == 1.0
    assert CA["beta"] == 1.0  # el guiado no se toca


@pytest.mark.parametrize("origen", ["H-PB-OFICINAS_CC", "H301", "G105", "G401"])
def test_costo_clasico_y_guiado_nunca_menor_que_dijkstra(origen):
    optimo = buscar_ruta(GRAFO, origen, CM).costo
    for variante, cfg in (("clasico", CA_CLASICO), ("guiado", CA)):
        for semilla in range(5):
            r = ejecutar_aco(GRAFO, origen, CM, cfg, semilla=semilla, variante=variante)
            if r.tiene_ruta:
                assert r.mejor_costo >= optimo - 1e-9


def test_clasico_respeta_aristas_bloqueadas():
    esc = construir_escenario("Gradas Norte bloqueadas", GRAFO, CM)
    cfg = dict(CA_CLASICO, beta=0.0)  # beta=0: asegura exito para ejercitar el mecanismo de bloqueo
    r = ejecutar_aco(GRAFO, "H201", CM, cfg, aristas_bloqueadas=esc.aristas_bloqueadas, semilla=3, variante="clasico")
    assert r.tiene_ruta
    assert not any(n.startswith("GRADAS-NORTE") for n in r.mejor_camino)
    assert "SALIDA-A" in r.mejor_camino


def test_clasico_soporta_warm_start_y_snapshots():
    cfg = dict(CA_CLASICO, beta=0.0)
    frio = ejecutar_aco(GRAFO, "H301", CM, cfg, semilla=2, variante="clasico")
    tibio = ejecutar_aco(GRAFO, "H301", CM, cfg, semilla=2, variante="clasico", feromona_inicial=frio.feromona_final)
    assert tibio.tiene_ruta
    assert 1 in frio.snapshots_feromona and len(frio.historial) in frio.snapshots_feromona
    primero = next(aco_iterativo(GRAFO, "H301", CM, cfg, semilla=2, variante="clasico"))
    assert primero.iteracion == 1 and primero.feromona


def test_seis_escenarios_y_sus_bloqueos():
    assert len(ESCENARIOS_DISPONIBLES) == 6
    normal = construir_escenario("Normal", GRAFO, CM)
    assert normal.aristas_bloqueadas == frozenset() and normal.congestion == {}
    norte = construir_escenario("Gradas Norte bloqueadas", GRAFO, CM)
    assert norte.aristas_bloqueadas and all(a.startswith("GRADAS-NORTE-") for a in norte.aristas_bloqueadas)
    sur = construir_escenario("Gradas Sur bloqueadas", GRAFO, CM)
    assert sur.aristas_bloqueadas and all(a.startswith("GRADAS-SUR-") for a in sur.aristas_bloqueadas)
    assert construir_escenario("Salida A bloqueada", GRAFO, CM).aristas_bloqueadas == frozenset({"GRADAS-SUR-PB-SALIDA-A"})
    assert construir_escenario("Salida B bloqueada", GRAFO, CM).aristas_bloqueadas == frozenset({"GRADAS-NORTE-PB-SALIDA-B"})
    cong = construir_escenario("Congestion en una salida", GRAFO, CM)
    assert cong.aristas_bloqueadas == frozenset()
    assert cong.congestion == {"GRADAS-SUR-PB-SALIDA-A": CM["factor_congestion_demo"]}


def test_todos_los_origenes_tienen_ruta_en_los_seis_escenarios():
    origenes = list(CM["poblacion_por_origen"])
    assert len(origenes) == 42
    for nombre in ESCENARIOS_DISPONIBLES:
        esc = construir_escenario(nombre, GRAFO, CM)
        g = aplicar_congestion(GRAFO, esc.congestion)
        for o in origenes:
            assert buscar_ruta(g, o, CM, esc.aristas_bloqueadas).tiene_ruta, (nombre, o)


def test_config_experimentos_presente():
    cfg = cargar_json(CONFIG_ACO_PATH)["parametros"]
    assert len(cfg["experimentos"]["value"]["origenes_sensibilidad"]) == 10
    assert set(cfg["experimentos"]["value"]["valores_sensibilidad"]) == {"alfa", "beta", "rho", "n_hormigas"}
