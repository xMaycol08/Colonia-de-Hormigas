"""Pruebas del modulo de dibujo (calibracion del plano y esquema por niveles)."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from grafo import CONFIG_MODELO_PATH, cargar_configuracion, cargar_grafo  # noqa: E402
from plano import (  # noqa: E402
    calibracion, dibujar_esquema, dibujar_rutas_plano, extension_plano_m, imagen_plano, layout_esquematico, pixel_a_xy, posiciones_planta,
)

GRAFO = cargar_grafo()
CM = cargar_configuracion(CONFIG_MODELO_PATH)


def test_origen_de_la_calibracion_es_la_salida_a():
    ox, oy = calibracion()["origen_px"]
    assert pixel_a_xy(ox, oy) == (0.0, 0.0)


def test_salida_b_cae_donde_esta_su_x_en_la_imagen():
    cal = calibracion()
    px = cal["origen_px"][0] + GRAFO.nodos_por_id["SALIDA-B"]["x_m"] * cal["escala_px_por_m"]
    py = cal["origen_px"][1] - GRAFO.nodos_por_id["SALIDA-B"]["y_m"] * cal["escala_px_por_m"]
    assert abs(px - 924.5) < 12 and abs(py - 51.4) < 12  # dentro de ~1.7 m de la X norte (error de calibracion 2.2 %)


def test_recorte_deja_fuera_barra_de_tareas_y_ambas_salidas_dentro():
    x0, x1, y0, y1 = extension_plano_m()
    for nid in ("SALIDA-A", "SALIDA-B"):
        n = GRAFO.nodos_por_id[nid]
        assert x0 < n["x_m"] < x1 and y0 < n["y_m"] < y1
    assert imagen_plano().shape[0] <= 680


def test_planta_superpone_todos_los_niveles():
    pos = posiciones_planta(GRAFO, CM["altura_piso_m"])
    for lado in ("H", "G", "CENTRAL"):
        base = pos["PAS-%s-PB" % lado]
        for nivel in "1234":
            x, y = pos["PAS-%s-%s" % (lado, nivel)]
            assert abs(x - base[0]) < 1e-6 and abs(y - base[1]) < 1e-6


def test_esquema_ubica_todos_los_nodos_sin_solaparse():
    pos = layout_esquematico(GRAFO)
    assert set(pos) == set(GRAFO.nodos_por_id)
    assert len({(round(x, 2), round(y, 2)) for x, y in pos.values()}) == len(pos)


def test_funciones_de_dibujo_corren():
    fig, (a, b) = plt.subplots(1, 2)
    pos = posiciones_planta(GRAFO, CM["altura_piso_m"])
    dibujar_rutas_plano(a, GRAFO, pos, {"Dijkstra": ["H403", "PAS-H-4"]}, origen="H403", bloqueadas=frozenset({"GRADAS-NORTE-PB-SALIDA-B"}))
    dibujar_esquema(b, GRAFO, tau={a_id: 1.0 for a_id in GRAFO.aristas_por_id})
    plt.close(fig)
