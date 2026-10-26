# Evacuación de los bloques G y H (ESPE, campus Matriz)

Proyecto de la materia Aplicaciones Basadas en el Conocimiento (ESPE). Modela la evacuación de los bloques G y H como un problema de búsqueda sobre un grafo y compara dos algoritmos para encontrar la ruta hacia un punto de encuentro:

- **Dijkstra**, como referencia exacta.
- **Optimización por Colonia de Hormigas (ACO)**, en dos variantes: *clásico* (sin poda, sin retroceso, visibilidad 1/costo) y *guiado* (con poda de callejones, retroceso y heurística tipo A*).

Un agente de evacuación (percibir, decidir, actuar) usa estos algoritmos. Una app en Streamlit permite simular, comparar y revisar los resultados.

El detalle del modelo, las fuentes oficiales, las tablas de resultados y los hallazgos están en [`docs/base_informe.md`](docs/base_informe.md).

## Estructura

```
app/app.py                       App de Streamlit (4 pestañas)
src/
  grafo.py, costos.py            Carga del grafo y función de costo
  dijkstra.py, aco.py            Algoritmos de búsqueda (ACO con variante="clasico" | "guiado")
  agente.py                      Agente de evacuación (percibir, decidir, actuar)
  escenarios.py                  Los 6 escenarios de bloqueo y congestión
  metricas.py, evacuacion.py     Tiempos de primera y última persona, evacuación completa
  benchmark.py                   Benchmark reutilizable (lo usa la app)
  plano.py                       Dibujo sobre el plano calibrado y esquema por niveles
scripts/
  correr_experimentos.py         Experimentos oficiales -> results/*.csv
  generar_figuras.py             Figuras y GIF -> results/figuras, results/animaciones
  build_graph.py                 Construye data/campus_graph.json desde los JSON de configuración
  validate_graph.py              Valida el grafo contra su esquema y reglas de consistencia
data/
  campus_graph.json              Grafo de evacuación (75 nodos, 79 aristas)
  config_modelo.json             Parámetros del modelo (población, velocidad, costos, orígenes)
  config_aco.json                Parámetros de ACO y del plan de experimentos
  calibracion_plano.json         Calibración píxel-metro del plano
  posiciones_plano.json          Posición de pasillos y gradas sobre el plano
  maps/plano_base_GH_anotado.jpeg  Plano calibrado usado como fondo
  raw/maps_observations.json     Observaciones de Google Maps usadas por build_graph.py
docs/                            Documentos oficiales (PDF) y base_informe.md
results/                         CSV, figuras, animaciones, cordura.txt, metadatos.json
tests/                           Pruebas automáticas (pytest)
```

Ningún número del modelo ni de ACO está escrito en el código: todos salen de `data/config_modelo.json` y `data/config_aco.json`.

## Instalación

Requiere Python 3.10 o superior.

```bash
pip install -r requirements.txt
```

## Ejecución

Pruebas:

```bash
python -m pytest
```

Experimentos oficiales (unos 8 minutos; escribe en `results/`, secuencial para que los tiempos sean comparables):

```bash
python scripts/correr_experimentos.py
python scripts/correr_experimentos.py --estimar     # solo estima el tiempo
```

Figuras y animaciones (leen los CSV de `results/`):

```bash
python scripts/generar_figuras.py
```

App:

```bash
streamlit run app/app.py
```

Regenerar y validar el grafo (solo si se editan los JSON de configuración o `data/posiciones_plano.json`; sobrescribe `data/campus_graph.json`):

```bash
python scripts/build_graph.py
python scripts/validate_graph.py data/campus_graph.json
```
