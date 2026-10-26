"""La app arranca y sus pestanas corren sin excepciones (streamlit.testing)."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app" / "app.py")


def test_app_arranca_con_cuatro_pestanas():
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Simulación en vivo", "Comparación", "Benchmark", "Evacuación completa"]


def test_app_simulacion_en_vivo_y_variante_clasica():
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.sidebar.radio[0].set_value("ACO clásico").run()
    at.sidebar.slider[4].set_value(10)   # iteraciones
    at.sidebar.slider[5].set_value(0.0)  # pausa
    at.sidebar.button[0].click().run()
    assert not at.exception


def test_app_escenarios_y_evacuacion_sin_excepciones():
    at = AppTest.from_file(APP, default_timeout=180).run()
    for i in range(len(at.sidebar.selectbox[1].options)):
        at.sidebar.selectbox[1].select_index(i).run()
        assert not at.exception, i


def test_app_benchmark_reejecutar_no_toca_resultados_oficiales():
    resultados = Path(__file__).resolve().parent.parent / "results"
    antes = {p.name: p.stat().st_mtime for p in resultados.glob("*.csv")}
    at = AppTest.from_file(APP, default_timeout=180).run()
    for b in at.button:
        if b.label == "Re-ejecutar benchmark":
            b.click()
    at.run()
    assert not at.exception
    assert antes == {p.name: p.stat().st_mtime for p in resultados.glob("*.csv")}
