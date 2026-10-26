# PEAS y clasificación del agente de evacuación

Este documento describe el agente implementado en `src/agente.py`
(`AgenteEvacuacion`), consistente con el modelo del grafo construido en
Fase 1 (`data/campus_graph.json`) y con el Protocolo de actuación ante
sismos citado en `docs/restricciones_oficiales.md`.

## PEAS

### Rendimiento (Performance)

El agente se evalúa por qué tan bien cumple el objetivo de evacuación
descrito en el Protocolo de sismo (`docs/restricciones_oficiales.md`,
secciones 1-5):

- **Llegar a un punto de encuentro** (cualquiera de los disponibles, no uno
  fijo) — condición de meta obligatoria.
- **Minimizar el costo de la ruta** (`src/costos.py`: distancia_m,
  penalizada si la arista es techada, siguiendo la recomendación del
  protocolo de alejarse de corredores cubiertos).
- **Evitar aristas bloqueadas** (gradas o salidas inutilizadas tras el
  sismo).
- **No quedarse sin solución silenciosamente**: si no hay ruta, debe
  reportarlo explícitamente en vez de fallar o colgarse (Tarea F, prueba 4).
- Medido indirectamente también por las métricas oficiales de la Guía de
  simulacros (tiempo de la primera y de la última persona en llegar al
  punto de encuentro, ver `src/metricas.py`).

### Entorno (Environment)

Los bloques G y H de la ESPE Matriz, representados como el grafo de
evacuación (`data/campus_graph.json`): aulas, pasillos, gradas, salidas,
vías exteriores y puntos de encuentro, con un conjunto de aristas que puede
quedar bloqueado (gradas o salidas colapsadas/obstruidas) y, opcionalmente,
congestionado (más personas en una misma arista).

### Actuadores (Actuators)

- `decidir()`: calcula una ruta (vía ACO, opcionalmente comparada con
  Dijkstra) desde el origen hasta algún punto de encuentro.
- `actuar()`: traduce esa ruta en instrucciones legibles paso a paso (p. ej.
  "Sale del Aula 01, piso 3, bloque H" → "Baja por Gradas 02" → "Sale por
  SALIDA-A" → "Llega a PE-1 (provisional)") y un tiempo estimado en
  segundos.

En un despliegue real estos "actuadores" serían, por ejemplo, señalización
dinámica, un altavoz o una app que muestra las instrucciones a la persona;
en esta fase el actuador es la lista de instrucciones en texto.

### Sensores (Sensors)

- `percibir(estado)`: recibe qué aristas están bloqueadas
  (`aristas_bloqueadas`, p. ej. por un equipo de evaluación estructural que
  reporta una escalera colapsada) y, opcionalmente, un mapa de congestión
  por arista (`congestion`, un factor que infla el costo efectivo de una
  arista con más gente de la esperada).

En un despliegue real estos sensores serían, por ejemplo, reportes de
brigadistas, cámaras o sensores de aforo; en esta fase son el diccionario
`EstadoPercibido` que recibe `percibir()`.

## Clasificación del entorno (7 propiedades)

| Propiedad | Clasificación | Justificación |
|---|---|---|
| **Observable** | Parcialmente observable | El agente solo conoce lo que se le reporta en `percibir()` (aristas bloqueadas, congestión); no tiene visión directa del edificio, y buena parte del grafo mismo es todavía "supuesto" (Fase 1), no verificado en campo. |
| **Determinista / Estocástico** | Estocástico | ACO muestrea vecinos con un generador aleatorio sembrado (`random.Random`); y el mundo real que el grafo modela (sismo, pánico, obstrucciones) es inherentemente impredecible, aunque el modelo de costos en sí sea determinista dado un `tau` fijo. |
| **Episódico / Secuencial** | Secuencial | Cada paso de la ruta (qué nodo visitar después) depende de las decisiones anteriores (lista tabú, feromona acumulada); no es una serie de decisiones independientes. |
| **Estático / Dinámico** | Dinámico | Entre una llamada a `percibir()` y la siguiente, el entorno puede cambiar (una escalera que se bloquea después de un sismo, congestión que aumenta); el agente debe poder volver a `decidir()` con el nuevo estado. |
| **Discreto / Continuo** | Discreto | El grafo tiene un número finito de nodos y aristas; las decisiones de la hormiga (qué vecino tomar) son sobre un conjunto discreto de opciones. |
| **Un solo agente / Multiagente** | Multiagente (cooperativo, no competitivo) | En la evacuación real hay muchas personas moviéndose a la vez (de ahí el modelo de congestión y las métricas de primera/última persona en `src/metricas.py`); el agente aquí modela a **una** persona u origen representativo dentro de ese entorno multiagente, sin competir por recursos con las demás (todas comparten la meta de evacuar). |
| **Conocido / Desconocido** | Parcialmente conocido | Las reglas del modelo (cómo se calcula el costo, qué hace ACO) son conocidas por el agente; pero varios datos del entorno mismo (el grafo interior completo, los puntos de encuentro reales) son supuestos pendientes de verificar en campo (ver `data/pendientes.md`), por lo que el conocimiento del entorno es incompleto. |

## Tipo de agente: basado en metas y en utilidad

El `AgenteEvacuacion` combina dos enfoques clásicos:

- **Basado en metas (goal-based):** la condición de éxito es binaria y
  explícita — llegar a **algún** nodo tipo `punto_encuentro` (no uno fijo:
  hay varias metas válidas). Tanto Dijkstra (`src/dijkstra.py`) como ACO
  (`src/aco.py`) se detienen en cuanto alcanzan cualquier nodo que cumpla
  esa condición. Esto es exactamente razonamiento basado en metas: el
  agente evalúa si una secuencia de acciones lo lleva a un estado meta, sin
  importar cuál punto de encuentro sea.

- **Basado en utilidad (utility-based):** entre todas las secuencias de
  acciones que cumplen la meta (llegar a un punto de encuentro), el agente
  no se conforma con cualquiera: busca **minimizar el costo** (`src/costos.py`),
  que funciona como una función de utilidad (negativa) combinando distancia
  y una penalización por estar techado (alineada con el Protocolo de
  sismo). ACO aproxima el óptimo de esa utilidad mediante búsqueda
  estocástica guiada por feromona y heurística (`1/costo`); Dijkstra la
  calcula exactamente. Que el agente prefiera una ruta más corta y menos
  techada sobre otra que también llega a un punto de encuentro, es
  precisamente razonamiento basado en utilidad: distingue "mejor" de
  simplemente "válido".

Esta combinación es consistente con el enfoque usado en Fase 1, donde el
grafo ya fue diseñado con una función de costo explícita
(`penalizacion_techado`, `factor_costo_gradas`) pensada para capturar no
solo "llegar" sino "llegar de la mejor forma posible" según el criterio del
Protocolo de sismo.
