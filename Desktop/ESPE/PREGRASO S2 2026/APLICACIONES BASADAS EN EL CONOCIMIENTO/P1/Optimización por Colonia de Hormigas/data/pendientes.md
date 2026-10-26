# Pendientes de campo - Fase 1-bis (grafo provisional, complejo G/H/C/D)

Lista de todo lo que hay que traer de campo para reemplazar cada supuesto del
grafo provisional (`data/campus_graph.json`). Para cada item se indica el
campo exacto a editar.

Despues de editar cualquier valor, volver a correr:

```bash
python scripts/build_graph.py
python scripts/validate_graph.py data/campus_graph.json
python scripts/plot_graph.py
```

## 1. Interpretacion pendiente de confirmar por el equipo

- **"El piso 1 es el nivel inmediatamente superior a PB"**: es la
  interpretacion usada para `niveles: ["PB","1","2","3","4"]` en
  `data/config_modelo.json`. El equipo la dio como interpretacion de
  trabajo (no confirmada explicitamente) sobre `plano_base_GH_anotado.jpeg`.

## 2. Parametros en `data/config_modelo.json`

| Supuesto actual | Campo a editar | De donde debe salir el dato real |
|---|---|---|
| `niveles: [PB,1,2,3,4]` | `parametros.niveles.value` | Confirmar en campo el numero real de niveles del complejo y si PB realmente no tiene aulas |
| `aulas_por_piso: 5` | `parametros.aulas_por_piso.value` | Contar aulas reales por piso en campo (plano arquitectonico si existe) |
| `secciones_de_gradas: 2` | `parametros.secciones_de_gradas.value` | Confirmado por el equipo sobre la captura anotada (2 zigzags rojos); verificar en campo que no haya una tercera seccion no visible desde el aire |
| `altura_piso_m: 3.2` | `parametros.altura_piso_m.value` | Medicion fisica o planos del edificio, si existen |
| `factor_costo_gradas: 2.0` | `parametros.factor_costo_gradas.value` | Justificar con una referencia de ingenieria de evacuacion (p. ej. NFPA 130, SFPE Handbook) o con tiempos medidos de descenso real en simulacro |
| `penalizacion_techado: 1.5` | `parametros.penalizacion_techado.value` | Definir un criterio cuantitativo (hoy es arbitrario) |
| `velocidad_caminata_m_s: 1.2` | `parametros.velocidad_caminata_m_s.value` | Justificar con una referencia (p. ej. SFPE Handbook) o con tiempos medidos en simulacro |
| `tiempo_reaccion_s: 60` | `parametros.tiempo_reaccion_s.value` | Medir en un simulacro real |
| `tiempo_entre_personas_s: 1.0` | `parametros.tiempo_entre_personas_s.value` | Reemplazar por un modelo de flujo peatonal real (basado en ancho_m del cuello de botella) |
| `tramo_horizontal_gradas_m: 4.0` | `parametros.tramo_horizontal_gradas_m.value` | Medir el recorrido horizontal real de las secciones de gradas norte/sur |
| `distancia_aula_a_pasillo_m: 3.0` | `parametros.distancia_aula_a_pasillo_m.value` | Medir en campo; unico tramo horizontal que sigue siendo constante (las aulas no son visibles en la foto satelital) |
| `ancho_pasillo_m: 2.0`, `ancho_gradas_m: 1.2`, `ancho_puerta_salida_m: 1.5` | `parametros.*.value` | Medicion fisica en campo |
| `espaciado_aula_m: 4.0` | `parametros.espaciado_aula_m.value` | Solo visualizacion esquematica; no requiere dato de campo |
| `poblacion_por_aula: 25`, `poblacion_PB_H_oficinas: 10`, `poblacion_PB_G_laboratorio: 10` | `parametros.*.value` + regenerar `poblacion_por_origen` | Conteo real de capacidad/ocupacion tipica por aula/oficina/laboratorio |

## 3. Posiciones sobre el plano (`data/posiciones_plano.json`)

Las posiciones de pixel de `pasillo_H`, `pasillo_G`, `pasillo_central`,
`gradas_norte_acceso` y `gradas_sur_acceso` se estimaron visualmente sobre
`data/maps/plano_base_GH_anotado.jpeg` (el area amarilla y los zigzags
rojos). Son **editables directamente en ese archivo**: si el equipo mide
mejor estos puntos (sobre la imagen o sobre un plano arquitectonico real),
basta con cambiar `pixel_x`/`pixel_y`; `scripts/build_graph.py` recalcula
las distancias horizontales automaticamente.

## 4. Coordenadas de Salida A / Salida B

| Dato | Donde esta | Que falta |
|---|---|---|
| Salida A: lat -0.313162, lon -78.445291 | Constante `SALIDA_A` en `scripts/build_graph.py` + `data/calibracion_plano.json` | Verificar en campo (GPS) la coordenada real. Confirmada visualmente como la X sur de la captura anotada (confidence `medido_en_maps`, no `verificado_en_campo`). |
| Salida B: lat -0.312607, lon -78.445237 | Idem | Igual que arriba, para la X norte. La calibracion por estos dos puntos se verifico contra la barra de escala de la captura con un error de 2.19% (ver `data/calibracion_plano.json`), aceptable; no hay advertencia de distancia pendiente (las dos salidas quedaron a menos de 40 m de su seccion de gradas correspondiente). |
| PE-1, PE-2, PE-3 (provisionales) | `data/raw/maps_observations.json`, ids `area_abierta_01/02/03` | Reemplazar por la ubicacion real de puntos de encuentro oficiales de la ESPE (14 en total en el campus Matriz). Verificar senaletica fisica. |

## 5. Conectividad exterior (aristas EXT-NN)

Las aristas exteriores se generan con un **arbol de expansion minima** sobre
los puntos conocidos (Salida A, Salida B, 3 puntos de camino de Fase 0, y
PE-1/2/3), no con el trazado real de las rutas peatonales. Falta completar
el levantamiento de Fase 0 en Google Maps para el resto de la red de
caminos del campus (ver `data/raw/maps_report.md`).

## 6. Datos interiores en general

Todo nodo tipo `aula`, `pasillo` o `gradas` tiene `confidence: "supuesto"` y
`status: "provisional"`, y `lat`/`lon` en `null` porque Google Maps no
muestra interiores. Falta un levantamiento de campo real (planta por
planta, aula por aula, de las dos secciones de gradas) para reemplazar
estos supuestos.

## 7. Riesgos no evaluados

Solo se registro un grupo de arboles como riesgo. Postes y cables de
energia electrica cerca de las salidas y rutas no se evaluaron (no
distinguibles desde la imagen satelital ni desde Street View, sin cobertura
en esta zona). Pendiente de verificar en campo.
