# Decisiones de diseño - Fase 2 (algoritmos y agente)

Resumen de las decisiones que tuve que tomar fuera de lo pedido literalmente
en la tarea, y de un hallazgo importante sobre el comportamiento de ACO con
los valores por defecto.

> **Actualización Fase 2B:** el hallazgo de la sección siguiente quedó
> **resuelto**. Ver la sección "Fase 2B: correcciones aplicadas a ACO" más
> abajo para el diagnóstico de causa raíz, las tres correcciones aplicadas
> (poda de callejones, retroceso, heurística guiada tipo A*) y la malla de
> parámetros que llevó la tasa de éxito de ~0.01% a 100%.

## Hallazgo principal: ACO casi nunca converge con los valores por defecto sobre el grafo real

**Esto no es un bug** (verificado con pruebas manuales, ver abajo), pero es
importante reportarlo porque afecta directamente la tabla del smoke test.

Con `alfa=1.0`, `beta=3.0`, `Q=1.0`, `n_hormigas=30`, `n_iteraciones=100` y
`paciencia_estancamiento=25` (los valores pedidos explícitamente para
`data/config_aco.json`), la probabilidad de que **una sola hormiga** logre
construir un camino completo hasta un punto de encuentro, partiendo de
cualquier origen del grafo real (incluso desde el pasillo de planta baja,
justo al lado de una salida), es de aproximadamente **0.01% - 0.05%**.

**Por qué pasa esto (verificado, no es un bug):** en el grafo real
(`data/campus_graph.json`), cada aula es un nodo "hoja" (solo se conecta al
pasillo de su piso), así que cualquier hormiga que entre a un aula desde el
pasillo queda atrapada por la regla de "no repetir nodos" (tabú). Además,
el costo de una arista `gradas` (que ya incluye `factor_costo_gradas` y
`tramo_horizontal_gradas_m`, Fase 1) es mucho mayor que el costo de una
arista `plano` dentro del mismo piso (pasillo-aula o pasillo-gradas). Con
`beta=3`, la heurística `eta^beta` favorece fuertemente las aristas locales
baratas por sobre la arista larga que de verdad lleva a la salida, así que
las hormigas casi siempre se desvían hacia pasillos de otros pisos o aulas
en vez de seguir bajando por la escalera, hasta que un aula las atrapa. Con
`Q=1.0` y costos típicos de ruta ~150-200, cada hormiga exitosa aporta un
refuerzo de feromona diminuto (~0.005-0.01), así que aunque hubiera unas
pocas hormigas exitosas, no alcanza para "aprender" la ruta correcta dentro
de 100 iteraciones / 25 de paciencia.

**Verificación de que no es un bug del código:**
- Con el mismo código pero `n_iteraciones=600` y `paciencia_estancamiento=600`
  (solo como diagnóstico, sin tocar `data/config_aco.json`), ACO sí encontró
  una ruta desde `H-P1-AULA01` (éxito en la iteración 252, costo 212.58
  frente al óptimo de Dijkstra de 153.10 — una brecha razonable para una
  única solución encontrada, sin tiempo aún para refinarla más).
- Sobre el grafo pequeño de prueba (`tests/_grafo_prueba.py`), con una
  topología sin aulas-trampa, ACO converge al óptimo desde la primera
  iteración de forma consistente (ver `tests/test_aco.py`).

**Qué hice con este hallazgo (sin desviarme de lo pedido):**
- No cambié ningún valor de `data/config_aco.json`: son exactamente los
  pedidos en la tarea, "valores por defecto... se afinarán en Fase 3".
- `scripts/smoke_test.py` corre tal cual con esos valores y por eso su tabla
  muestra "sin ruta" en las 10 corridas de ACO (ver resultados mostrados al
  usuario). Esto es evidencia real y honesta, no un error de ejecución.
- Las pruebas de **mecanismo** de ACO (reproducibilidad, costo ≥ Dijkstra,
  bloqueos, warm start) usan el grafo pequeño hecho a mano de
  `tests/_grafo_prueba.py` en vez del grafo real, porque ahí el algoritmo sí
  puede ejercitarse de forma rápida y determinista (el enunciado ya pedía
  explícitamente un grafo pequeño hecho a mano para la prueba de Dijkstra;
  extendí el mismo criterio a las pruebas de ACO por la razón de arriba).
- La prueba 5 (Salida A bloqueada → ruta por Salida B) sí usa el grafo real,
  pero con **Dijkstra**, porque esa prueba verifica la topología/conectividad
  del grafo (que existe un camino alterno), no el comportamiento estocástico
  de ACO.

**Recomendación para Fase 3** (no implementada ahora, para no desviarme de
los valores pedidos): subir `paciencia_estancamiento` y/o `n_iteraciones`
considerablemente, y/o revisar `beta` (más bajo) y `Q` (más alto) para
facilitar el arranque ("bootstrap") de la feromona en grafos con muchos
nodos hoja como este.

## Otras decisiones de diseño

- **`src/grafo.py` (nuevo, no pedido explícitamente):** módulo compartido
  con la clase `Grafo` (carga de nodos/aristas, lista de adyacencia no
  dirigida, lookup de puntos de encuentro) y `cargar_configuracion()`. Evita
  duplicar esa lógica en `dijkstra.py`, `aco.py`, `agente.py` y
  `metricas.py`.
- **`src/__init__.py` agregado:** convierte `src/` en un paquete explícito.
  Los módulos igual se importan de forma "plana" (`from grafo import Grafo`,
  como ya hacían los scripts de fases anteriores con `scripts/`), insertando
  `src/` en `sys.path` desde cada consumidor, para mantener el mismo estilo
  del proyecto.
- **`intervalo_snapshot_feromona` agregado a `data/config_aco.json`:** no
  estaba en la lista original de parámetros, pero es necesario para cumplir
  literalmente "copias de la matriz de feromonas en iteraciones
  seleccionadas (para animar luego)". Se guarda una copia cada N iteraciones
  (configurable) más la primera y la última.
- **Congestión modelada fuera de `src/costos.py`:** la Tarea A define el
  costo sin mencionar congestión. En `src/agente.py`, `percibir()` guarda un
  diccionario de congestión por arista, y `decidir()` construye un `Grafo`
  "efectivo" con `distancia_m` escalada por ese factor antes de llamar a
  Dijkstra/ACO, en vez de modificar `costo_arista()`. Así `costos.py` sigue
  siendo la única fuente de verdad del costo base (distancia + penalización
  por techado), y la congestión queda como una capa aparte, propia del
  agente.
- **`nodos_expandidos` en Dijkstra:** se cuenta como el número de nodos que
  Dijkstra finaliza (saca de la cola de prioridad) hasta encontrar el primer
  punto de encuentro, que es la métrica estándar de "nodos expandidos" en
  búsqueda informada/no informada.
- **Instrucciones legibles (`actuar()`):** se generan con una heurística
  simple basada en el tipo de nodo (aula/pasillo/gradas/salida/punto de
  encuentro) y el cambio de piso entre gradas consecutivas (para decir
  "sube"/"baja"). No hay una especificación exacta de formato en la tarea
  más allá del ejemplo dado; se siguió ese estilo.
- **`poblacion_por_origen` y `origenes_representativos`:** se definieron en
  Fase 2 directamente en `data/config_modelo.json` (no en un archivo nuevo),
  porque la tarea los pide como una ampliación de ese mismo archivo
  ("Agrega a data/config_modelo.json...").

---

## Fase 2B: correcciones aplicadas a ACO

### Diagnóstico de causa raíz (recordatorio)

Con los parámetros originales (`beta=3.0`, `Q=1.0`, tabú estricto sin
retroceso), la probabilidad de que una hormiga llegara a un punto de
encuentro desde cualquier origen real era ~0.01%-0.05%: las aulas son
callejones sin salida que atrapan al tabú, y el costo de una arista `gradas`
es mucho mayor que el de una arista `plano` del mismo piso, así que
`beta=3` alejaba sistemáticamente a las hormigas de la ruta correcta.

### Correcciones aplicadas (sin tocar `src/costos.py`)

1. **Poda de callejones** (`podar_callejones()` en `src/aco.py`): antes de
   correr ACO se construye una vista del grafo (nunca se modifica
   `data/campus_graph.json`) sin los nodos de grado 1 que no sean el origen
   ni un punto de encuentro. En la práctica esto elimina todas las aulas
   excepto la de origen, que son exactamente los callejones que atrapaban a
   las hormigas. Podar hojas es seguro: un nodo hoja nunca puede estar en el
   camino óptimo entre otros dos nodos.
2. **Retroceso (backtracking)**: si una hormiga no tiene vecinos sin
   visitar, en vez de fallar de inmediato retrocede un paso (saca el último
   nodo de su pila, lo marca "muerto" solo para ella) y sigue intentando
   desde el nodo anterior. Solo falla si se queda sin opciones incluso
   habiendo vuelto al origen, o si supera `max_pasos_factor * numero_de_nodos`
   pasos (parámetro nuevo en `config_aco.json`, por defecto 4).
3. **Heurística guiada tipo A\***: `eta_ij = 1 / (costo_ij + h(j))`, con
   `h(j)` la distancia euclidiana (en `x_m`, `y_m`) de `j` al punto de
   encuentro más cercano, precalculada una sola vez por ejecución
   (`calcular_heuristica()`). Es la misma idea que la heurística admisible
   de A*: en vez de que la hormiga solo mire el costo del siguiente paso
   (miope), también mira qué tan cerca geométricamente la deja ese paso de
   una meta, igual que A* usa `f(n) = g(n) + h(n)` para guiar la búsqueda
   hacia el objetivo en vez de explorar a ciegas.

Con estas tres correcciones, incluso **sin cambiar ningún parámetro**
(`beta=3.0` original), la tasa de éxito pasó de ~0.01% a **100%** (10/10)
en los 10 orígenes representativos, y el costo mínimo de ACO igualó el
óptimo de Dijkstra en todas las corridas.

### Malla de afinación de parámetros (tarea 4)

Se corrió `scripts/afinar_aco.py`: 27 combinaciones (`beta` en {1.0, 2.0,
3.0}, `rho` en {0.1, 0.3, 0.5}, `n_hormigas` en {20, 30, 50}), sobre los 10
orígenes representativos, 10 corridas (semillas 0-9) por combinación — 2700
corridas en total, 658.3 s de cómputo. Detalle completo en
`results/malla_aco_20261025_175117.csv`.

**Resultado: las 27 combinaciones lograron 100.0% de tasa de éxito y 0.00%
de brecha promedio frente a Dijkstra.** Con las correcciones aplicadas, el
afinado de parámetros ya no es necesario para la correctitud (eso lo
resuelven la poda, el retroceso y la heurística); el único criterio de
desempate relevante fue el tiempo de cómputo.

| beta | rho | n_hormigas | tasa_exito % | brecha_promedio % | tiempo_promedio ms |
|---|---|---|---|---|---|
| **1.0** | **0.5** | **20** | **100.0** | **0.00** | **103.4** |
| 1.0 | 0.3 | 20 | 100.0 | 0.00 | 110.1 |
| 2.0 | 0.3 | 20 | 100.0 | 0.00 | 133.4 |
| 2.0 | 0.5 | 20 | 100.0 | 0.00 | 143.6 |
| 3.0 | 0.5 | 20 | 100.0 | 0.00 | 144.8 |
| 1.0 | 0.5 | 30 | 100.0 | 0.00 | 146.2 |
| 2.0 | 0.1 | 20 | 100.0 | 0.00 | 146.8 |
| 1.0 | 0.1 | 20 | 100.0 | 0.00 | 147.7 |
| 3.0 | 0.3 | 20 | 100.0 | 0.00 | 172.2 |
| 2.0 | 0.5 | 30 | 100.0 | 0.00 | 195.2 |
| 1.0 | 0.3 | 30 | 100.0 | 0.00 | 198.4 |
| 2.0 | 0.1 | 30 | 100.0 | 0.00 | 207.1 |
| 3.0 | 0.5 | 30 | 100.0 | 0.00 | 218.4 |
| 1.0 | 0.5 | 50 | 100.0 | 0.00 | 230.1 |
| 1.0 | 0.1 | 30 | 100.0 | 0.00 | 237.1 |
| 3.0 | 0.1 | 20 | 100.0 | 0.00 | 238.3 |
| 3.0 | 0.3 | 30 | 100.0 | 0.00 | 245.2 |
| 2.0 | 0.3 | 30 | 100.0 | 0.00 | 250.4 |
| 1.0 | 0.3 | 50 | 100.0 | 0.00 | 282.0 |
| 1.0 | 0.1 | 50 | 100.0 | 0.00 | 313.7 |
| 3.0 | 0.1 | 30 | 100.0 | 0.00 | 355.1 |
| 2.0 | 0.1 | 50 | 100.0 | 0.00 | 371.9 |
| 2.0 | 0.5 | 50 | 100.0 | 0.00 | 376.7 |
| 3.0 | 0.5 | 50 | 100.0 | 0.00 | 378.1 |
| 2.0 | 0.3 | 50 | 100.0 | 0.00 | 378.5 |
| 3.0 | 0.3 | 50 | 100.0 | 0.00 | 394.4 |
| 3.0 | 0.1 | 50 | 100.0 | 0.00 | 462.9 |

**Combinación elegida y aplicada en `data/config_aco.json`:** `beta=1.0`,
`rho=0.5`, `n_hormigas=20` (100.0% éxito, 0.00% brecha, 103.4 ms promedio —
la más rápida entre las 27, que estaban todas empatadas en éxito y brecha).

### Criterio de aceptación

**Cumplido.** Tasa de éxito = 100% >= 95% (criterio de la tarea), verificado
tanto en la malla completa (2700 corridas) como en una prueba automatizada
más liviana (`tests/test_aco_correcciones.py::test_tasa_de_exito_sobre_el_grafo_real_cumple_el_criterio_de_aceptacion`,
10 corridas/origen).
