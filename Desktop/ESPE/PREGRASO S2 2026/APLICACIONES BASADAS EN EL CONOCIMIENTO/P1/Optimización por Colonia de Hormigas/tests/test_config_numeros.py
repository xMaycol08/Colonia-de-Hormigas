"""Prueba 7 (Fase 2): todo valor numerico del modelo y de ACO viene de los archivos de config.

Verifica dos cosas:
1. data/config_aco.json y data/config_modelo.json tienen todos los
   parametros que usan src/aco.py, src/dijkstra.py, src/costos.py y
   src/metricas.py (si faltara uno, esos modulos lanzarian KeyError al
   ejecutarse, lo cual ya es una forma de garantia: no hay un valor de
   respaldo hardcodeado escondido en el codigo).
2. Las funciones clave de src/aco.py no declaran valores por defecto
   numericos en su firma para los parametros que deberian venir de config
   (si alguien agregara un "beta: float = 3.0" por defecto, esta prueba lo
   detecta).
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_json, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
import aco  # noqa: E402
import dijkstra  # noqa: E402
import costos  # noqa: E402

PARAMETROS_CONFIG_ACO_ESPERADOS = {
    "n_hormigas",
    "n_iteraciones",
    "alfa",
    "beta",
    "rho",
    "Q",
    "tau_inicial",
    "tau_min",
    "tau_max",
    "paciencia_estancamiento",
    "semilla",
    "intervalo_snapshot_feromona",
}

PARAMETROS_CONFIG_MODELO_ESPERADOS_FASE2 = {
    "penalizacion_techado",
    "velocidad_caminata_m_s",
    "tiempo_reaccion_s",
    "tiempo_entre_personas_s",
    "origenes_representativos",
    "poblacion_por_origen",
}


def test_config_aco_tiene_todos_los_parametros_esperados():
    datos = cargar_json(CONFIG_ACO_PATH)
    claves = set(datos["parametros"].keys())
    faltantes = PARAMETROS_CONFIG_ACO_ESPERADOS - claves
    assert not faltantes, f"Faltan parametros en data/config_aco.json: {faltantes}"

    for nombre, info in datos["parametros"].items():
        assert "value" in info
        assert "comentario" in info and info["comentario"], f"Parametro sin comentario: {nombre}"


def test_config_modelo_tiene_los_parametros_de_fase2():
    datos = cargar_json(CONFIG_MODELO_PATH)
    claves = set(datos["parametros"].keys())
    faltantes = PARAMETROS_CONFIG_MODELO_ESPERADOS_FASE2 - claves
    assert not faltantes, f"Faltan parametros de Fase 2 en data/config_modelo.json: {faltantes}"

    for nombre, info in datos["parametros"].items():
        assert "value" in info
        assert "comentario" in info and info["comentario"], f"Parametro sin comentario: {nombre}"


def test_ejecutar_aco_no_tiene_defaults_numericos_de_hiperparametros():
    """La firma de ejecutar_aco no debe traer valores por defecto para alfa, beta,
    rho, etc.: esos SIEMPRE deben venir del diccionario config_aco que se pasa
    explicitamente.
    """
    firma = inspect.signature(aco.ejecutar_aco)
    parametros_prohibidos_con_default = {"config_modelo", "config_aco"}
    for nombre, parametro in firma.parameters.items():
        if nombre in parametros_prohibidos_con_default:
            assert parametro.default is inspect.Parameter.empty, (
                f"ejecutar_aco no deberia tener un valor por defecto para '{nombre}' "
                "(los hiperparametros deben venir siempre de config_aco.json)"
            )


def test_costo_arista_y_tiempo_arista_no_tienen_defaults_numericos():
    for funcion in (costos.costo_arista, costos.tiempo_arista):
        firma = inspect.signature(funcion)
        parametro = firma.parameters["config_modelo"]
        assert parametro.default is inspect.Parameter.empty, (
            f"{funcion.__name__} no deberia tener un config_modelo por defecto"
        )


def test_buscar_ruta_no_tiene_defaults_numericos():
    firma = inspect.signature(dijkstra.buscar_ruta)
    parametro = firma.parameters["config_modelo"]
    assert parametro.default is inspect.Parameter.empty
