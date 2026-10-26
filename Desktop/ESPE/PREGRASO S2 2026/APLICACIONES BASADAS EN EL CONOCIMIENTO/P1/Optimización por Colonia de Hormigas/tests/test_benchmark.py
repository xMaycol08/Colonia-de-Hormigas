"""Prueba (Fase 3): la funcion de benchmark corre con N pequeno y genera el CSV."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from grafo import cargar_grafo, cargar_configuracion, CONFIG_MODELO_PATH, CONFIG_ACO_PATH  # noqa: E402
from benchmark import ejecutar_benchmark, resumir_benchmark, barrido_sensibilidad, Escenario  # noqa: E402


def test_ejecutar_benchmark_con_n_pequeno_genera_csv(tmp_path, monkeypatch):
    import benchmark as benchmark_module

    monkeypatch.setattr(benchmark_module, "RESULTS_DIR", tmp_path)

    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    origen = config_modelo["origenes_representativos"][0]["id_nodo"]
    escenarios = [Escenario("Normal", frozenset(), {})]

    df, ruta_csv = ejecutar_benchmark(grafo, [origen], escenarios, config_modelo, config_aco, n_corridas=2)

    assert len(df) == 2
    assert set(df.columns) >= {"origen", "escenario", "semilla", "tiene_ruta", "costo", "tiempo_ms"}
    assert ruta_csv is not None
    assert ruta_csv.exists()
    assert ruta_csv.parent == tmp_path


def test_resumir_benchmark_agrega_por_origen_escenario():
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    origen = config_modelo["origenes_representativos"][0]["id_nodo"]
    escenarios = [Escenario("Normal", frozenset(), {})]

    df, _ruta = ejecutar_benchmark(grafo, [origen], escenarios, config_modelo, config_aco, n_corridas=3, guardar_csv=False)
    resumen = resumir_benchmark(df)

    assert len(resumen) == 1
    fila = resumen.iloc[0]
    assert fila["origen"] == origen
    assert fila["escenario"] == "Normal"
    assert fila["n_corridas"] == 3
    assert fila["tasa_exito_pct"] == 100.0


def test_barrido_sensibilidad_corre_con_pocos_valores():
    grafo = cargar_grafo()
    config_modelo = cargar_configuracion(CONFIG_MODELO_PATH)
    config_aco = cargar_configuracion(CONFIG_ACO_PATH)

    origen = config_modelo["origenes_representativos"][0]["id_nodo"]
    escenario = Escenario("Normal", frozenset(), {})

    df = barrido_sensibilidad(grafo, origen, escenario, config_modelo, config_aco, "beta", [1.0, 2.0], n_corridas=2)

    assert len(df) == 2
    assert list(df["beta"]) == [1.0, 2.0]
    assert "tasa_exito_pct" in df.columns
