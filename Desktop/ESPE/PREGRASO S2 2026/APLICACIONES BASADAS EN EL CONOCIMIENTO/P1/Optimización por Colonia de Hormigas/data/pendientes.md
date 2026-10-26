# Pendientes de campo - Fase 1 (grafo provisional)

Lista de todo lo que hay que traer de campo para reemplazar cada supuesto del
grafo provisional (`data/campus_graph.json`). Para cada item se indica el
campo exacto a editar en `data/config_modelo.json` (o el archivo que
corresponda) y, si existe, la seccion de
`data/campo/FICHA_TRABAJO_DE_CAMPO.md` donde se recoge ese dato.

Despues de editar cualquier valor, volver a correr:

```bash
python scripts/build_graph.py
python scripts/validate_graph.py data/campus_graph.json
python scripts/plot_graph.py
```

## 1. Parametros en `data/config_modelo.json`

| Supuesto actual | Campo a editar | De donde debe salir el dato real |
|---|---|---|
| `pisos_por_bloque: 5` (igual para G y H) | `parametros.pisos_por_bloque.value` | Ficha de campo, seccion 1 (contar pisos reales de cada bloque; si G y H tienen distinto numero de pisos, el modelo actual no lo soporta y habria que separar el parametro por bloque en una proxima iteracion) |
| `escaleras_por_bloque: 8` (igual para G y H) | `parametros.escaleras_por_bloque.value` | Ficha de campo, seccion 3 (contar escaleras reales por bloque; si G y H tienen numero distinto, igual que arriba, separar el parametro) |
| `aulas_por_piso_por_bloque: 6` | `parametros.aulas_por_piso_por_bloque.value` | Ficha de campo, seccion 2 (contar aulas reales por piso; si varia por piso, el modelo actual asume el mismo numero en todos los pisos, pendiente de mejorar) |
| `altura_piso_m: 3.2` | `parametros.altura_piso_m.value` | Medicion fisica o planos del edificio, si existen |
| `factor_costo_gradas: 2.0` | `parametros.factor_costo_gradas.value` | Justificar con una referencia de ingenieria de evacuacion (p. ej. NFPA 130, SFPE Handbook) o con tiempos medidos de descenso real en simulacro |
| `penalizacion_techado: 1.5` | `parametros.penalizacion_techado.value` | Definir un criterio cuantitativo (hoy es arbitrario); revisar si el protocolo institucional da una base numerica |
| `conexion_planta_baja_G_H_m: 62` | `parametros.conexion_planta_baja_G_H_m.value` | Medir en campo el recorrido interior real entre la planta baja de H y la de G (hoy es una aproximacion dada por el equipo, basada en la distancia exterior entre Salida A y Salida B) |
| `velocidad_caminata_m_s: 1.2` | `parametros.velocidad_caminata_m_s.value` | Justificar con una referencia (p. ej. SFPE Handbook of Fire Protection Engineering) o con tiempos medidos en simulacro |
| `tramo_horizontal_gradas_m: 4.0` | `parametros.tramo_horizontal_gradas_m.value` | Medir el recorrido horizontal real de un tramo de escalera (incluye descansos) |
| `distancia_pasillo_a_salida_m: 5.0` | `parametros.distancia_pasillo_a_salida_m.value` | Medir en campo desde el pasillo de planta baja hasta cada puerta de salida |
| `distancia_aula_a_pasillo_m: 3.0` | `parametros.distancia_aula_a_pasillo_m.value` | Medir en campo (puede variar por aula; el modelo actual asume un valor unico) |
| `distancia_gradas_a_pasillo_m: 2.0` | `parametros.distancia_gradas_a_pasillo_m.value` | Medir en campo |
| `ancho_pasillo_m: 2.0` | `parametros.ancho_pasillo_m.value` | Ficha de campo, seccion 6 |
| `ancho_gradas_m: 1.2` | `parametros.ancho_gradas_m.value` | Ficha de campo, seccion 3 |
| `ancho_puerta_salida_m: 1.5` | `parametros.ancho_puerta_salida_m.value` | Ficha de campo, seccion 4 |
| `espaciado_aula_m: 4.0` | `parametros.espaciado_aula_m.value` | Solo afecta la visualizacion esquematica (`scripts/plot_graph.py`); no requiere dato de campo, pero puede ajustarse para que los diagramas por piso sean mas legibles |
| `longitud_paso_m: 0.75` | `parametros.longitud_paso_m.value` | Ya tomado de la ficha de campo (seccion 9); no se usa todavia en `build_graph.py` |

## 2. Coordenadas fuera de `config_modelo.json`

| Supuesto actual | Donde esta | Que falta |
|---|---|---|
| Salida A: lat -0.313162, lon -78.445291 | Constante `SALIDA_A` en `scripts/build_graph.py` | Verificar en campo (GPS o medicion) la coordenada real de la puerta de salida de los bloques C/H. El equipo la dio como lectura de Maps, no esta verificada. |
| Salida B: lat -0.312607, lon -78.445237 | Constante `SALIDA_B` en `scripts/build_graph.py` | Igual que arriba, para la puerta de salida de los bloques G/D. **Advertencia del validador:** `SALIDA-B` quedo a 48.2 m de la esquina mas cercana del Bloque G segun `maps_observations.json` (umbral de la tarea: 40 m). No se rechazo la coordenada, pero esto sugiere revisar la coordenada de Salida B o las esquinas de G registradas en Fase 0 con prioridad. |
| PE-1, PE-2, PE-3 (provisionales) | `data/raw/maps_observations.json`, ids `area_abierta_01`, `area_abierta_02`, `area_abierta_03` | Reemplazar por la ubicacion real de puntos de encuentro oficiales de la ESPE (14 en total en el campus Matriz, segun la Guia de simulacros, pero su ubicacion no esta documentada; ver `docs/restricciones_oficiales.md`). Verificar senaletica fisica (texto exacto del letrero) y foto, segun `data/campo/FICHA_TRABAJO_DE_CAMPO.md` seccion 8. Despues de verificar, actualizar `generar_nodos_exteriores()` en `scripts/build_graph.py` para usar los ids/nombres reales en vez de "PE-1/2/3 (provisional)". |

## 3. Conectividad exterior (aristas EXT-01 .. EXT-07)

Las aristas exteriores del grafo (`data/campus_graph.json`, aristas con id
`EXT-NN`) se generaron con un **arbol de expansion minima** sobre los puntos
conocidos (Salida A, Salida B, los 3 puntos de camino de Fase 0, y PE-1/2/3),
no con el trazado real de las rutas peatonales. Falta:

- Completar el levantamiento de Fase 0 en Google Maps para Ruta Principal 1,
  Ruta Principal 2, Sendero 1, Sendero 2 y el resto de Ruta Principal 3 /
  Ruta Transversal 1 / Anillo Vial ESPE (ver `data/raw/maps_report.md`,
  seccion "Lo que NO se pudo determinar").
- Verificar en campo el trazado real entre Salida A/B y cada punto de
  encuentro real (una vez que se conozcan los 14 puntos oficiales).
- Una vez con esos datos, `generar_aristas_exteriores()` en
  `scripts/build_graph.py` deberia reemplazarse por aristas que sigan el
  trazado real en vez del arbol de expansion minima.

## 4. Datos interiores en general

Todo nodo tipo `aula`, `pasillo` o `gradas` en `data/campus_graph.json` tiene
`confidence: "supuesto"` y `status: "provisional"`, y `lat`/`lon` en `null`
porque Google Maps no muestra interiores. La unica forma de completarlos es
con la ficha de campo (`data/campo/FICHA_TRABAJO_DE_CAMPO.md`), levantando
piso por piso, aula por aula y escalera por escalera de los bloques G y H.
Cuando se tenga ese levantamiento, la logica de `generar_bloque_interior()`
en `scripts/build_graph.py` debe reemplazarse por una que lea directamente
los datos reales (por piso, no un numero uniforme para todos los pisos).

## 5. Riesgos no evaluados

`maps_observations.json` solo registra un grupo de arboles como riesgo
(`riesgo_arboles_01`). Postes y cables de energia electrica cerca de las
salidas y rutas (pedidos explicitamente por el Protocolo de sismo, ver
`docs/restricciones_oficiales.md`) no se evaluaron porque no son distinguibles
desde la imagen satelital ni desde Street View (sin cobertura en esta zona).
Esto debe completarse en campo (ficha de campo, seccion 7) antes de que el
campo `riesgo_caida` de los nodos exteriores se considere confiable.
