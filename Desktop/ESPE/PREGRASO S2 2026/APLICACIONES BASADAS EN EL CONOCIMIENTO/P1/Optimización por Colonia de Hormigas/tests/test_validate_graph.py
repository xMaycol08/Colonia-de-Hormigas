"""Pruebas para scripts/validate_graph.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "scripts"))

import validate_graph as vg  # noqa: E402


def nodo_base(**overrides) -> dict:
    """Crea un nodo valido con valores por defecto, sobreescribibles por kwargs."""
    base = {
        "id": "N1",
        "nombre": "Nodo de prueba",
        "tipo": "aula",
        "bloque": "G",
        "piso": 1,
        "lat": -0.315300,
        "lon": -78.447800,
        "x_m": 0,
        "y_m": 0,
        "techado": True,
        "riesgo_caida": False,
        "capacidad_estimada_personas": 30,
        "source": "prueba",
        "confidence": "verificado_en_campo",
        "status": "completo",
        "notes": None,
    }
    base.update(overrides)
    return base


def arista_base(**overrides) -> dict:
    """Crea una arista valida con valores por defecto, sobreescribibles por kwargs."""
    base = {
        "id": "A1",
        "desde": "N1",
        "hasta": "N2",
        "distancia_m": 10.0,
        "tipo": "plano",
        "techado": True,
        "ancho_m": 1.5,
        "bloqueable": False,
        "source": "prueba",
        "confidence": "verificado_en_campo",
        "status": "completo",
        "notes": None,
    }
    base.update(overrides)
    return base


@pytest.fixture()
def schema() -> dict:
    return vg.cargar_json(vg.SCHEMA_PATH)


def test_la_plantilla_es_valida_contra_el_schema(schema):
    datos = vg.cargar_json(vg.TEMPLATE_PATH)
    errores = vg.validar_contra_schema(datos, schema)
    assert errores == []


def test_detecta_ids_duplicados():
    resultado = vg.ResultadoValidacion()
    nodos = [nodo_base(id="N1"), nodo_base(id="N1")]
    vg.detectar_ids_duplicados(nodos, "nodos", resultado)
    assert resultado.tiene_errores_graves
    assert "duplicado" in resultado.errores[0].lower()


def test_detecta_arista_con_nodo_inexistente():
    resultado = vg.ResultadoValidacion()
    nodos = [nodo_base(id="N1")]
    aristas = [arista_base(desde="N1", hasta="N_NO_EXISTE")]
    vg.detectar_aristas_con_nodos_inexistentes(nodos, aristas, resultado)
    assert resultado.tiene_errores_graves
    assert "N_NO_EXISTE" in resultado.errores[0]


def test_detecta_nodo_aislado():
    resultado = vg.ResultadoValidacion()
    nodos = [nodo_base(id="N1"), nodo_base(id="N2")]
    aristas = [arista_base(desde="N1", hasta="N1")]
    vg.detectar_nodos_aislados(nodos, aristas, resultado)
    assert resultado.tiene_errores_graves
    assert "N2" in resultado.errores[0]


def test_camino_a_punto_encuentro_existe():
    nodos = [
        nodo_base(id="AULA1", tipo="aula"),
        nodo_base(id="PASILLO1", tipo="pasillo"),
        nodo_base(id="PE1", tipo="punto_encuentro", bloque="exterior"),
    ]
    aristas = [
        arista_base(id="A1", desde="AULA1", hasta="PASILLO1"),
        arista_base(id="A2", desde="PASILLO1", hasta="PE1"),
    ]
    resultado = vg.ResultadoValidacion()
    vg.verificar_caminos_a_punto_encuentro(nodos, aristas, resultado)
    assert not resultado.tiene_errores_graves


def test_camino_a_punto_encuentro_faltante_genera_error():
    nodos = [
        nodo_base(id="AULA1", tipo="aula"),
        nodo_base(id="PE1", tipo="punto_encuentro", bloque="exterior"),
    ]
    aristas: list = []  # AULA1 no tiene ninguna arista hacia PE1
    resultado = vg.ResultadoValidacion()
    vg.verificar_caminos_a_punto_encuentro(nodos, aristas, resultado)
    assert resultado.tiene_errores_graves


def test_verifica_salida_por_bloque_falta_en_h():
    nodos = [
        nodo_base(id="SG1", tipo="salida", bloque="G"),
        nodo_base(id="AULAH1", tipo="aula", bloque="H"),
    ]
    resultado = vg.ResultadoValidacion()
    vg.verificar_salidas_por_bloque(nodos, resultado)
    assert resultado.tiene_errores_graves
    assert any("'H'" in e for e in resultado.errores)


def test_verifica_salida_por_bloque_ok():
    nodos = [
        nodo_base(id="SG1", tipo="salida", bloque="G"),
        nodo_base(id="SH1", tipo="salida", bloque="H"),
    ]
    resultado = vg.ResultadoValidacion()
    vg.verificar_salidas_por_bloque(nodos, resultado)
    assert not resultado.tiene_errores_graves


def test_distancia_haversine_coherente_no_genera_advertencia():
    # Dos puntos separados ~11.1 m en latitud (aprox 0.0001 grados ~ 11.1 m)
    nodos = [
        nodo_base(id="N1", lat=-0.315300, lon=-78.447800),
        nodo_base(id="N2", lat=-0.315400, lon=-78.447800),
    ]
    aristas = [arista_base(id="A1", desde="N1", hasta="N2", distancia_m=11.1, tipo="plano")]
    resultado = vg.ResultadoValidacion()
    vg.verificar_distancias_contra_haversine(nodos, aristas, resultado)
    assert resultado.advertencias == []


def test_distancia_haversine_incoherente_genera_advertencia():
    nodos = [
        nodo_base(id="N1", lat=-0.315300, lon=-78.447800),
        nodo_base(id="N2", lat=-0.315400, lon=-78.447800),
    ]
    # ~11.1 m reales, se declara 200 m -> excede 25% de tolerancia
    aristas = [arista_base(id="A1", desde="N1", hasta="N2", distancia_m=200.0, tipo="plano")]
    resultado = vg.ResultadoValidacion()
    vg.verificar_distancias_contra_haversine(nodos, aristas, resultado)
    assert len(resultado.advertencias) == 1


def test_gradas_permite_distancia_mayor_sin_advertencia():
    nodos = [
        nodo_base(id="N1", lat=-0.315300, lon=-78.447800),
        nodo_base(id="N2", lat=-0.315400, lon=-78.447800),
    ]
    aristas = [arista_base(id="A1", desde="N1", hasta="N2", distancia_m=50.0, tipo="gradas")]
    resultado = vg.ResultadoValidacion()
    vg.verificar_distancias_contra_haversine(nodos, aristas, resultado)
    assert resultado.advertencias == []


def test_gradas_con_distancia_menor_a_haversine_genera_advertencia():
    nodos = [
        nodo_base(id="N1", lat=-0.315300, lon=-78.447800),
        nodo_base(id="N2", lat=-0.315400, lon=-78.447800),
    ]
    aristas = [arista_base(id="A1", desde="N1", hasta="N2", distancia_m=1.0, tipo="gradas")]
    resultado = vg.ResultadoValidacion()
    vg.verificar_distancias_contra_haversine(nodos, aristas, resultado)
    assert len(resultado.advertencias) == 1


def test_calcular_porcentaje_pendientes_con_lista_vacia():
    resumen = vg.calcular_porcentaje_pendientes([])
    assert resumen["total_elementos"] == 0
    assert resumen["porcentaje_campos_pendientes"] == 0.0


def test_calcular_porcentaje_pendientes_cuenta_nulos_y_status():
    elementos = [
        {"id": "N1", "status": "pendiente", "lat": None, "lon": 1.0},
        {"id": "N2", "status": "completo", "lat": 1.0, "lon": 1.0},
    ]
    resumen = vg.calcular_porcentaje_pendientes(elementos)
    assert resumen["total_elementos"] == 2
    assert resumen["porcentaje_campos_pendientes"] > 0


def test_validar_plantilla_completa_no_lanza_excepciones(schema):
    datos = vg.cargar_json(vg.TEMPLATE_PATH)
    resultado, resumen = vg.validar(datos, schema)
    assert isinstance(resultado, vg.ResultadoValidacion)
    assert "nodos" in resumen
    assert "aristas" in resumen
    assert "puntos_encuentro" in resumen
