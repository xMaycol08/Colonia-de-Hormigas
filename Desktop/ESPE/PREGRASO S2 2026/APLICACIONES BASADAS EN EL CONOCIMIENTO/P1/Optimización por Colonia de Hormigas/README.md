# Evacuacion bloques G y H - ESPE Matriz (Sangolqui)

Proyecto academico (ESPE, Aplicaciones Basadas en el Conocimiento). Simula la
evacuacion de los bloques G y H del campus Matriz ante un sismo: Dijkstra y
Optimizacion por Colonia de Hormigas (ACO) sobre un grafo de evacuacion, un
agente de evacuacion (percibir -> decidir -> actuar), y una app interactiva
en Streamlit.

Regla general del proyecto, vigente en todas las fases: **ningun dato del
campus se inventa.** Todo dato desconocido se guarda como `null` con
`status: "pendiente"` o `"provisional"`, cada elemento del grafo registra su
`source`, `confidence` y `notes`, y **ningun numero del modelo vive en el
codigo**: todos estan en `data/config_modelo.json` y `data/config_aco.json`.

## Estado del proyecto

- **Fase 0** (`docs/restricciones_oficiales.md`, `data/raw/`): recoleccion y
  validacion de datos del campus (documentos oficiales + observacion en
  Google Maps).
- **Fase 1** (`scripts/build_graph.py`): construccion del grafo de evacuacion
  provisional (`data/campus_graph.json`) a partir de `data/config_modelo.json`.
- **Fase 2 / 2B** (`src/`): Dijkstra, ACO (con poda de callejones, retroceso
  y heuristica guiada) y el agente de evacuacion. Ver
  `docs/decisiones_fase2.md` para el diagnostico y las correcciones
  aplicadas a ACO, y `docs/agente_peas.md` para el analisis PEAS del agente.
- **Fase 3** (`app/app.py`): app interactiva en Streamlit (simulacion en
  vivo, comparacion, benchmark, evacuacion completa).

## Estructura del proyecto

```
docs/                           Documentos oficiales y su analisis
  restricciones_oficiales.md    Lo que SI y NO dicen los documentos oficiales
  FUENTES.md                    Bitacora de fuentes de datos
  *.pdf, *.png                  Documentos fuente originales

data/
  campus_graph.schema.json      JSON Schema del grafo de evacuacion
  campus_graph.template.json    Plantilla con 1 nodo y 1 arista de EJEMPLO
  raw/                          Datos crudos sin procesar (vacio por ahora)
  maps/                         Capturas y datos derivados de mapas
  campo/                        Fichas y resultados del trabajo de campo
    FICHA_TRABAJO_DE_CAMPO.md   Plantilla imprimible para levantar bloques G y H

  config_modelo.json             Parametros del modelo (interior, poblacion, origenes)
  config_aco.json                 Parametros de ACO (afinados en Fase 2B)
  campus_graph.json               Grafo de evacuacion generado (Fase 1)
  pendientes.md                   Que falta verificar en campo, y donde editarlo

scripts/
  validate_graph.py             Validador del grafo (schema + reglas de consistencia)
  build_graph.py                 Construye data/campus_graph.json (Fase 1)
  plot_graph.py                   Dibuja el grafo y las plantas por piso
  afinar_aco.py                   Malla de parametros de ACO (Fase 2B)
  smoke_test.py                   Verificacion rapida de Dijkstra/ACO

src/
  grafo.py, costos.py             Carga del grafo y funcion de costo
  dijkstra.py, aco.py             Algoritmos de busqueda de ruta
  agente.py                       AgenteEvacuacion (percibir/decidir/actuar)
  metricas.py, benchmark.py       Metricas de evacuacion y utilidades de benchmark

app/
  app.py                          App interactiva en Streamlit (4 pestanas)

results/                          CSV/PNG/GIF generados por la app y los benchmarks

tests/                             Pruebas pytest de todas las fases
```

## Modelo de datos (resumen)

El grafo vive en un unico archivo JSON con tres listas: `nodos`, `aristas` y
`puntos_encuentro`. El detalle completo de campos esta en
`data/campus_graph.schema.json`; la plantilla de ejemplo (no real) esta en
`data/campus_graph.template.json`.

- **Nodo**: id, nombre, tipo (aula | pasillo | gradas | salida | via_exterior |
  interseccion | punto_encuentro), bloque (G | H | exterior), piso, lat, lon,
  x_m, y_m, techado, riesgo_caida, capacidad_estimada_personas, source,
  confidence, status, notes.
- **Arista**: id, desde, hasta, distancia_m, tipo (plano | gradas | rampa |
  puerta), techado, ancho_m, bloqueable, source, confidence, status, notes.
- **Punto de encuentro**: id, nombre_o_codigo_en_senaletica, lat, lon,
  area_aprox_m2, abierto_sin_edificaciones_cerca,
  capacidad_estimada_personas, source, confidence, status, notes.

`confidence` solo puede ser uno de: `verificado_en_campo`, `medido_en_maps`,
`documento_oficial`, `blog_no_oficial`, `supuesto`.

## Como ejecutar el validador

```bash
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Validar la plantilla de ejemplo (por defecto):
python scripts/validate_graph.py

# Validar un archivo de datos especifico:
python scripts/validate_graph.py data/mi_grafo.json

# Correr las pruebas:
pytest
```

El validador:

- Valida el JSON contra `data/campus_graph.schema.json`.
- Reporta el porcentaje de campos `pendiente` por tipo de elemento.
- Detecta nodos aislados, IDs duplicados y aristas que referencian nodos
  inexistentes.
- Verifica que todo nodo tipo aula/pasillo/gradas tenga camino a algun nodo
  tipo `punto_encuentro`.
- Verifica que los bloques G y H tengan cada uno al menos un nodo tipo
  `salida`.
- Compara `distancia_m` de cada arista contra la distancia haversine entre sus
  nodos (tolerancia 25%; para aristas tipo `gradas` solo advierte si
  `distancia_m` es menor que la haversine).
- Termina con exit code distinto de 0 si hay errores graves.

## Criterios de aceptacion de la Fase 0

1. Los bloques G y H tienen cada uno sus salidas y gradas verificadas en campo
   (ver `data/campo/FICHA_TRABAJO_DE_CAMPO.md`).
2. Hay al menos 3 puntos de encuentro cercanos a G/H ubicados con coordenadas
   (de los 14 puntos de encuentro oficiales del campus Matriz, segun la Guia
   de simulacros USIN-GS-v1-2019-013, pag. 3).
3. Todo nodo de aula o piso (tipo aula/pasillo/gradas) tiene camino a algun
   punto de encuentro en el grafo.
4. El validador (`scripts/validate_graph.py`) termina sin errores graves sobre
   el archivo de datos final de la fase, y los `pendiente` restantes quedan
   listados en el reporte.

La Fase 0 se considera cerrada cuando estos cuatro criterios se cumplen sobre
un archivo de datos real (no la plantilla de ejemplo).

## Como ejecutar

```bash
# 1. Crear entorno e instalar dependencias
python -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. (Si hace falta regenerar el grafo) construir data/campus_graph.json
python scripts/build_graph.py
python scripts/validate_graph.py data/campus_graph.json
python scripts/plot_graph.py

# 3. Correr las pruebas
pytest

# 4. Verificacion rapida de Dijkstra/ACO (no es el benchmark completo)
python scripts/smoke_test.py

# 5. Lanzar la app interactiva
streamlit run app/app.py
```

La app abre en `http://localhost:8501`. Desde la barra lateral se elige el
origen, el escenario (bloqueos/congestion) y los parametros de ACO; el boton
"Ejecutar" corre la simulacion en vivo (pestana "Simulacion en vivo"). Las
pestanas "Comparacion", "Benchmark" y "Evacuacion completa" reutilizan el
origen/escenario elegido en la barra lateral. Los CSV, PNG y GIF que se
generan desde la app quedan en `results/`.

Para repetir la malla de afinacion de parametros de ACO (Fase 2B, tarda
varios minutos):

```bash
python scripts/afinar_aco.py
```
