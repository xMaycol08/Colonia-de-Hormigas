# Reporte de observación exterior en Google Maps - Bloques G y H (Fase 0)

Fecha de recolección: 2026-10-25. Fuente: Google Maps (vista satélite), navegador
Google Chrome, sesión de solo lectura (sin inicio de sesión, sin guardar, editar
ni calificar nada en Maps, sin uso de APIs ni claves).

**Imágenes (c) Google — uso académico.**

## 0. Identificación del edificio

El usuario confirmó que el edificio de los bloques G y H está en **Ruta
Transversal 1, 171103 Sangolquí**, y que comparte el mismo complejo de
edificios con los bloques C y D (etiquetas "Bloque H - ESPE", "Bloque G -
ESPE", "Bloque C - ESPE" y "Bloque D - ESPE" aparecen una junto a otra en
Maps, sobre lo que visualmente es una sola estructura de techos conectados).
No se adivinó esta ubicación: se detuvo el proceso y se preguntó al usuario
antes de tomar cualquier coordenada (ver sección de supuestos).

## 1. Tabla de lo registrado

Todas las observaciones están en `data/raw/maps_observations.json`
(16 observaciones). Resumen por tipo:

| Tipo | Cantidad | IDs |
|---|---|---|
| esquina_edificio (Bloque H) | 5 | corner_h_01 .. corner_h_05 |
| esquina_edificio (Bloque G) | 4 | corner_g_01 .. corner_g_04 |
| salida (candidata, no confirmada) | 2 | salida_h_01, salida_g_01 |
| camino (Ruta Principal 3) | 2 | camino_rutaprincipal3_pt1, _pt2 |
| camino (Ruta Transversal 1) | 1 | camino_rutatransversal1_pt1 |
| area_abierta (candidata) | 1 | area_abierta_01 |
| riesgo (árboles) | 1 | riesgo_arboles_01 |

Capturas guardadas en `data/maps/`:
- `z20_ala_bloque_h_detalle.jpg` — ala del Bloque H, zoom cercano.
- `z20_alas_bloque_h_bloque_g_limpia.jpg` — alas de Bloque H y Bloque G juntas.
- `z19_contexto_campo_abierto_oeste.jpg` — vista amplia con el campo abierto
  candidato y el grupo de árboles de riesgo.

(Nota: se guardaron como `.jpg`, no `.png` como sugería la convención de
nombres pedida, porque es el formato real que produce la herramienta de
captura; el contenido y la nomenclatura `{zoom}_{descripcion}` se respetan.)

Distancias calculadas por haversine: `data/raw/maps_distances.csv` (ver
sección 4).

## 2. Lo que NO se pudo determinar

- **Interior del edificio** (pisos, aulas, gradas internas): Maps no muestra
  interiores, como se esperaba. Queda `pendiente` para la ficha de campo
  (`data/campo/FICHA_TRABAJO_DE_CAMPO.md`).
- **Salidas confirmadas**: no se pudo identificar con certeza ninguna puerta
  real desde la imagen satelital. Los dos puntos `salida_h_01` y `salida_g_01`
  son inferencias visuales a partir de patrones de pavimento/techo (un
  corredor oscuro entre H y C, y un tramo de pavimento más claro en el borde
  sureste de G), **no confirmaciones**.
- **Límite exacto entre las alas de G, H, C y D**: el complejo se ve como una
  sola estructura de techos conectados; las etiquetas de Maps marcan
  secciones, pero el techo no muestra una separación física clara en varios
  tramos (p. ej. entre el ala de "Bloque G" y la de "Bloque D" al norte).
  Los polígonos registrados son aproximaciones basadas en quiebres visibles
  del techo, no deslindes oficiales.
- **Cobertura de Street View**: se intentó (arrastrando el pegman y
  navegando directo a una URL de Street View sobre Anillo Vial ESPE, en
  -0.312402,-78.444673) y **no hay cobertura de Street View** en esta parte
  interior del campus (panorama vacío/negro). Por lo tanto no se pudo
  verificar visualmente gradas exteriores, corredores techados ni árboles
  desde nivel de calle; todo eso queda pendiente de visita física.
- **Postes y cables de energía eléctrica**: no son distinguibles desde la
  imagen satelital a este nivel de zoom. Solo se registró un riesgo por
  árboles (`riesgo_arboles_01`); postes/cables quedan `pendiente`.
- **Señalética de "punto de encuentro"**: no se encontró ninguna marcada en
  Maps (ni en el mapa base ni en Street View, por falta de cobertura). Los 14
  puntos de encuentro oficiales del campus Matriz (confirmados por la Guía de
  simulacros, no por Maps) no tienen ubicación geográfica conocida desde esta
  fuente.
- **Cobertura completa de los caminos**: solo se registraron 2 puntos en
  Ruta Principal 3 y 1 punto en Ruta Transversal 1, cerca del complejo
  G/H — no se cubrió toda su extensión cada 15 m como pedía la tarea
  completa, ni se tocaron Ruta Principal 1, Ruta Principal 2, Sendero 1,
  Sendero 2 ni el resto del Anillo Vial ESPE. Esta sesión se concentró en el
  entorno inmediato de G y H, a ritmo humano; el resto de la red de caminos
  del campus queda pendiente de una sesión de observación adicional.
- **Áreas abiertas candidatas**: solo se registró una (`area_abierta_01`),
  a unos 130 m de distancia del ala de Bloque H. No se verificó si coincide
  con alguno de los 14 puntos de encuentro oficiales.

## 3. Supuestos hechos

- Se asumió que las esquinas registradas para cada ala (H: 5 puntos, G: 4
  puntos) describen razonablemente el perímetro exterior visible en la
  imagen satelital, aproximando quiebres de techo como vértices del
  polígono. No es un levantamiento topográfico; es una lectura visual.
- Se asumió que la franja oscura y estrecha entre el ala de Bloque H y
  Bloque C corresponde a un corredor (posible corredor cubierto y/o salida),
  sin poder confirmar su función exacta desde satélite.
- Se asumió que el campo de césped al oeste del complejo (`area_abierta_01`)
  es un candidato razonable a zona de concentración por estar despejado de
  edificaciones, sin verificar si corresponde a un punto de encuentro oficial
  señalizado.

## 4. Distancias haversine y verificación cruzada

`data/raw/maps_distances.csv` (generado por `scripts/compute_maps_distances.py`,
que reutiliza `distancia_haversine_m` de `scripts/validate_graph.py`):

| camino | desde | hasta | distancia_m (haversine) |
|---|---|---|---|
| camino_rutaprincipal3 | camino_rutaprincipal3_pt1 | camino_rutaprincipal3_pt2 | 46.64 |

Solo se pudo calcular 1 tramo, porque Ruta Transversal 1 quedó con un único
punto registrado en esta sesión (no hay par consecutivo para calcular
distancia).

**Verificación manual con la herramienta "Measure distance" de Maps:** se
midió un tramo sobre Ruta Principal 3, entre un punto cercano a
`camino_rutaprincipal3_pt1` (-0.313250, -78.445148, muy próximo al punto
registrado) y un punto cercano a `camino_rutaprincipal3_pt2`. La herramienta
de Maps reportó **63.44 m**, frente a los **46.64 m** calculados por
haversine entre los puntos exactos guardados en el JSON.

La diferencia (~17 m) se debe a que los puntos usados para la medición manual
no son exactamente los mismos píxeles que los puntos guardados (la
herramienta "Measure distance" se clickeó por separado, a mano, y no cayó
exactamente sobre las mismas coordenadas que `camino_rutaprincipal3_pt1` y
`_pt2`), no a un error del cálculo haversine en sí. No se logró el
cross-check limpio de 3 tramos independientes que pedía la tarea completa,
porque solo había 1 tramo con 2 puntos consecutivos disponible esta sesión.
Se recomienda, en una próxima sesión, repetir la medición manual clickeando
exactamente sobre los mismos puntos ya guardados (usando sus coordenadas) en
vez de aproximarlos a ojo, para una comparación más limpia.

## 5. Error estimado

- **Lectura de coordenadas por clic derecho en imagen satelital** (zoom
  equivalente ~20-21, escala visible de 10-20 m en pantalla): error estimado
  de **±2 a 5 metros** por punto, combinando precisión del clic y posible
  error de georreferenciación de la imagen satelital de Maps (Airbus/Maxar
  Technologies, 2026).
- **Discrepancia observada en la verificación cruzada** (sección 4): ~17 m
  entre medición manual y cálculo haversine, atribuible principalmente a que
  los puntos clickeados no fueron idénticos entre ambos métodos, no al método
  de cálculo.
- Estos errores son aceptables para la Fase 0 (datos exploratorios, sujetos a
  verificación en campo) pero **no deben usarse como medida definitiva** de
  distancias para el grafo final; toda arista que use estos valores debe
  quedar marcada `confidence: "medido_en_maps"` y `status: "pendiente"` hasta
  que se verifique con medición física o GPS de campo, conforme al schema en
  `data/campus_graph.schema.json`.

## Siguiente paso sugerido (no ejecutado en esta sesión)

Completar la observación de Maps para los tramos de caminos restantes (Ruta
Principal 1/2, Sendero 1/2, resto de Ruta Principal 3 y Ruta Transversal 1,
y el Anillo Vial ESPE) y buscar más candidatas a área abierta, en una sesión
adicional de ritmo similar. Esta tarea se detiene aquí para validación del
usuario, sin construir el grafo (`campus_graph.*.json`) ni avanzar de fase.
