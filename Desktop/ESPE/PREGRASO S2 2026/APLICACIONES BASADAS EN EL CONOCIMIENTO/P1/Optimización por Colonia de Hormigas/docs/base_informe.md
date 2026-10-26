# Base del informe

Documento de trabajo con todo lo necesario para redactar el informe. Las tablas numéricas de la sección (g) se copiaron programáticamente de los CSV de `results/` (corrida del 2026-10-26, semilla base 1000). Los nombres de escenarios y variantes se muestran con tildes; en los CSV figuran sin tilde.

## (a) Problema y objetivo

**Enunciado de la actividad (texto oficial):** "Problema a solucionar: guiar a los miembros de la comunidad universitaria que se encuentran en los bloques G y H, para salir a un punto de evacuación o punto de encuentro en caso de ocurrir un desastre natural. Aplique un algoritmo de búsqueda, aplicar de preferencia el agente de búsqueda seleccionado. Preparar un informe académico de la práctica realizada con las pruebas realizadas y conclusiones. Elabore una presentación del trabajo para que presenten 2 minutos cada integrante del grupo de trabajo. Debe subir dos archivos (informe y presentación)."

**Objetivo del trabajo:** modelar la evacuación de los bloques G y H del campus Matriz de la ESPE (Sangolquí) como un problema de búsqueda sobre un grafo, resolverlo con un algoritmo inspirado en la naturaleza (Optimización por Colonia de Hormigas, ACO; Dorigo y Stützle, 2004) dentro de un agente basado en metas y utilidad (Russell y Norvig, 2021, cap. 2), compararlo con Dijkstra como referencia exacta y medir calidad de la ruta, tiempo de cómputo, adaptación a bloqueos y tiempos de evacuación (primera y última persona en llegar al punto de encuentro, las métricas de la guía oficial de simulacros).

## (b) Fuentes y restricciones oficiales

Documentos oficiales usados (ambos son escaneos de la Unidad de Seguridad Integrada de la ESPE; las páginas se verificaron abriendo los PDF de `docs/`):

- **Protocolo de actuación ante sismos**, código `USIN-PRT-v1-2019-001`, proceso `ASI.2.1.001`, 14-MAY-2019, 2 páginas.
- **Guía metodológica para ejecución de simulacros**, código `USIN-GS-v1-2019-013`, proceso `ASI.1.013`, 25-sep-2019, 22 páginas (incluye los anexos de formatos).

| Restricción o dato | Documento | Página y apartado | Cómo se usa en el modelo |
|---|---|---|---|
| Evacuar tan pronto la tierra deje de moverse | Protocolo | pág. 2, "Después del sismo", punto 1 | La evacuación se simula desde la emisión de la alerta, con un tiempo de reacción (supuesto) |
| En planta baja, evacuar de inmediato si la magnitud lo permite | Protocolo | pág. 2, "Durante el sismo", punto 5 | Contexto; los orígenes de planta baja son los más cercanos a la salida |
| En pisos altos, no intentar evacuar durante el sismo | Protocolo | pág. 1, "Durante el sismo", punto 2 | Contexto; el modelo parte del momento en que cesa el movimiento |
| Vía de evacuación hacia el punto de encuentro más cercano, en lo posible a campo abierto, alejado de edificaciones, corredores cubiertos, árboles, postes y cables | Protocolo | pág. 1, "Antes de que se produzca un sismo", punto 4 | Penalización de tramos techados (1.5, supuesto) en la función de costo; meta = cualquier punto de encuentro |
| Si está en el exterior, alejarse de árboles, edificaciones, postes y cables y dirigirse al punto de encuentro más cercano | Protocolo | pág. 2, "Durante el sismo", punto 6 | Las vías exteriores llevan al punto de encuentro |
| Dirigirse por la vía de evacuación previamente seleccionada | Protocolo | pág. 2, "Después del sismo", punto 2 | El agente calcula la ruta antes de actuar |
| No correr, no gritar, no empujar | Protocolo | pág. 2, "Después del sismo", punto 3 | Velocidad de caminata (1.2 m/s, supuesto), sin carrera |
| En el punto de encuentro, verificar el grupo y esperar disposiciones | Protocolo | pág. 2, "Después del sismo", punto 4 | El punto de encuentro es el estado meta |
| Especialistas estructurales verifican las instalaciones; la máxima autoridad decide | Protocolo | pág. 2, "Después del sismo", puntos 5 y 6 | Origen de los escenarios de bloqueo (gradas o salida inutilizadas) |
| El campus Matriz tiene 14 puntos de encuentro definidos y señalados (mínimo 14 evaluadores) | Guía | pág. 3, inciso d) | Sus ubicaciones NO figuran en los documentos: se usan 3 puntos hipotéticos |
| Se difunde el croquis de vías de evacuación y ubicación de los puntos de encuentro | Guía | pág. 4, incisos f) y g) | El croquis no está entre los documentos disponibles |
| Tiempo hasta la llegada de la primera y de la última persona al punto de encuentro (evaluación del simulacro) | Guía | pág. 7 (apartado de evaluación) | Métricas oficiales reproducidas por el modelo de evacuación |
| Los evaluadores permanecen en cada punto de encuentro y los evacuados esperan disposiciones de la máxima autoridad | Guía | pág. 7 | Contexto |
| Control de tiempos: llegada de la primera y de la última persona al punto de encuentro | Guía, anexo "Formato de verificación para evaluador de simulacro" (`USIN-FOR-v1-2019-012`) | pág. 2 del formato (pág. 16 del PDF), cuadro "Control de tiempos" | Define los hitos de tiempo medidos |
| Tiempo desde la alerta hasta la salida de la primera persona, hasta la evacuación total y hasta la llegada de la última persona | Guía, anexo "Formato de evaluación para observador de simulacro" (`USIN-FOR-v1-2019-011`) | pág. 1 del formato (pág. 17 del PDF) | Define las métricas de evaluación |

**Lo que los documentos no dicen** (y por eso se modeló con supuestos): ubicación de ninguno de los 14 puntos de encuentro; planos o croquis de los bloques G y H; número de pisos, aulas o gradas; distancias entre puntos del campus; inventario de riesgos de caída por edificio; capacidad de los puntos de encuentro o de las aulas.

**Otras fuentes:** capturas de Google Maps (vista satélite, Sangolquí) de las que se tomaron las coordenadas de las dos salidas y de áreas abiertas candidatas a punto de encuentro; la captura anotada por el equipo (`data/maps/plano_base_GH_anotado.jpeg`), con las dos salidas marcadas con una X verde, usada para calibrar el plano; y la verdad de campo declarada por el equipo (distribución del complejo, dos secciones de gradas, dos salidas, niveles y aulas). El blog no oficial "Cuerpitos ESPE" figuró en la bitácora de fuentes como pendiente de consulta y no se usó para ningún dato.

## (c) Edificio modelado

Los bloques C, D, G y H forman un solo complejo con pasillos conectados alrededor de un patio central (campus Matriz, Sangolquí, Ruta Transversal 1). Solo G y H son orígenes; C y D son de paso. G y H son laboratorios, con planta baja (PB, sin numeración, administrativa: oficinas de Ciencias de la Computación en H y laboratorios de Biotecnología en G) y pisos 1 a 4 con 5 aulas cada uno (H101-H105 ... H401-H405 y G101-G105 ... G401-G405). Total: 40 aulas + 2 nodos de PB = **42 orígenes**. Hay solo **dos secciones de gradas** compartidas por todo el complejo (norte y sur) y solo **dos salidas**: Salida A al sur (lado C/H) y Salida B al norte (lado G/D); cualquiera puede salir por cualquiera.

**Grafo resultante:** 75 nodos y 79 aristas: 42 orígenes (aulas y PB), 15 pasillos (H, G y central en 5 niveles), 10 nodos de gradas (2 secciones x 5 niveles), 2 salidas, 3 vías exteriores y 3 puntos de encuentro. Costo de una arista = distancia en metros (las gradas incluyen el factor de costo de gradas) multiplicada por la penalización de techado si corresponde; tiempo = costo / velocidad de caminata.

### Tabla MEDIDO frente a SUPUESTO

Clasificación: **MEDIDO** = tomado de Google Maps o calculado a partir de esas coordenadas; **DATO DEL EQUIPO** = declarado por el equipo como verdad de campo, sin medición instrumental independiente; **SUPUESTO** = valor adoptado sin medición.

| Elemento | Valor | Clasificación | Fuente o nota |
|---|---|---|---|
| Salida A (sur, lado C/H) | lat -0.313162, lon -78.445291 | MEDIDO | Google Maps (X sur de la captura anotada) |
| Salida B (norte, lado G/D) | lat -0.312607, lon -78.445237 | MEDIDO | Google Maps (X norte de la captura anotada) |
| Distancia entre las salidas | 61.7 m | MEDIDO | Calculada con esas coordenadas |
| Escala del plano | 6.948 px/m (error 2.19 % frente a la barra de 10 m = 71 px) | MEDIDO | Calibración con las dos X; verificada con la barra de escala de la captura |
| Conectividad C-D-G-H en un solo complejo | pasillos alrededor de un patio central | DATO DEL EQUIPO | Observación del equipo |
| Niveles y aulas | PB + 4 pisos; 5 aulas por piso; 42 orígenes | DATO DEL EQUIPO | Nomenclatura H101...H405 y G101...G405 |
| Secciones de gradas y salidas | 2 secciones (norte y sur) y 2 salidas, compartidas | DATO DEL EQUIPO | Observación del equipo |
| Misma distribución de pasillos en todos los niveles | sí | SUPUESTO | Confirmado por el equipo como supuesto de trabajo |
| Posición de pasillos y accesos a gradas sobre el plano | data/posiciones_plano.json | SUPUESTO | Estimada visualmente sobre el plano calibrado; las distancias horizontales se calculan con la escala medida |
| Población por aula | 25 personas | SUPUESTO | Sin conteo real |
| Población de PB | 10 (oficinas H) y 10 (laboratorio G) | SUPUESTO | Sin conteo real |
| Velocidad de caminata | 1.2 m/s | SUPUESTO | Valor de referencia |
| Tiempo de reacción | 60 s | SUPUESTO | No medido en simulacro |
| Intervalo entre personas de un mismo origen | 1.0 s | SUPUESTO | Sustituye a un modelo de flujo peatonal |
| Altura de piso | 3.2 m | SUPUESTO | No medida |
| Factor de costo de gradas | 2.0 | SUPUESTO | Sin referencia de ingeniería de evacuación aplicada |
| Penalización de tramo techado | 1.5 | SUPUESTO | Criterio cuantitativo arbitrario |
| Tramo horizontal de gradas | 4.0 m | SUPUESTO | No medido |
| Distancia aula-pasillo | 3.0 m | SUPUESTO | Las aulas no son visibles en la foto satelital |
| Factor de congestión del escenario de congestión | 3.0 | SUPUESTO | Valor de demostración |
| Puntos de encuentro PE-1, PE-2, PE-3 | áreas abiertas leídas en Google Maps | SUPUESTO | Hipotéticos: la ubicación real de los 14 puntos oficiales no se conoce |
| Aristas exteriores | árbol de expansión mínima sobre los puntos conocidos | SUPUESTO | No es el trazado real de los caminos |

### Limitaciones del modelo

- **Puntos de encuentro hipotéticos.** Los tres puntos son áreas abiertas leídas en Google Maps, no los puntos señalizados de la ESPE.
- **PE-1 y PE-3 quedan lejos de la Salida A** (unos 200 m por la red exterior), mientras que PE-2 está a unos 82 m de la Salida B. Por eso, en el escenario Normal todos los orígenes salen por la Salida B y llegan a PE-2 (ver sección (g), tabla de reparto).
- **Aristas exteriores en línea recta que cruzan edificios**, porque se generaron con un árbol de expansión mínima y no con el trazado real de los caminos.
- **La arista Salida A a Salida B (62 m) atraviesa el complejo** (es la distancia en línea recta entre las dos X) y permite pasar de una salida a la otra sin rodear el edificio. Los escenarios "Salida A bloqueada" y "Salida B bloqueada" bloquean solo la arista de gradas de planta baja hacia esa salida; la arista exterior entre salidas sigue disponible.
- **Sin modelo de colas ni de capacidad:** la evacuación completa no representa embotellamientos en gradas ni en las salidas; el tiempo de la última persona es el de la fila indiscriminada de cada origen (1 s entre personas).
- **Distribución idéntica en todos los niveles** (supuesto) y posiciones de pasillos estimadas visualmente.
- **Escala del plano** con un error de 2.19 % respecto de la barra de escala; las dos X medidas difieren en menos de 2 m del grafo.
- **Por verificar en campo** (según la bitácora de pendientes): número real de niveles y de aulas, las dos secciones de gradas (que no exista una tercera), coordenadas GPS de las salidas, ubicación de los puntos de encuentro oficiales, riesgos de caída (postes, cables, árboles) cerca de las salidas y rutas.

## (d) PEAS, propiedades del entorno y tipo de agente

El agente (`src/agente.py`, `AgenteEvacuacion`) sigue el ciclo percibir, decidir y actuar.

| PEAS | Descripción |
|---|---|
| **Rendimiento** | Llegar a un punto de encuentro (cualquiera de los disponibles); minimizar el costo de la ruta (distancia con penalización de tramos techados); evitar aristas bloqueadas; reportar explícitamente cuando no hay ruta; tiempos de la primera y de la última persona en llegar al punto de encuentro (métricas de la guía de simulacros) |
| **Entorno** | El complejo G/H (con C y D de paso) representado como grafo de 75 nodos y 79 aristas: 42 orígenes, pasillos, 2 secciones de gradas, 2 salidas, vías exteriores y 3 puntos de encuentro; con aristas que pueden quedar bloqueadas o congestionadas |
| **Actuadores** | `decidir()` calcula la ruta (ACO, opcionalmente contrastada con Dijkstra); `actuar()` la traduce a instrucciones paso a paso y a un tiempo estimado |
| **Sensores** | `percibir()` recibe las aristas bloqueadas y un mapa de congestión por arista (`EstadoPercibido`) |

**Siete propiedades del entorno** (Russell y Norvig, 2021, cap. 2):

| Propiedad | Clasificación | Justificación |
|---|---|---|
| Observable | Parcialmente observable | El agente solo conoce lo que le reporta `percibir()` (bloqueos y congestión); no ve el edificio y parte del grafo es supuesto |
| Determinista / estocástico | Estocástico | ACO muestrea vecinos con un generador aleatorio sembrado; el mundo real (sismo, pánico, obstrucciones) es impredecible |
| Episódico / secuencial | Secuencial | Cada paso de la ruta depende de los anteriores (lista tabú, feromona acumulada) |
| Estático / dinámico | Dinámico | Entre dos llamadas a `percibir()` pueden aparecer bloqueos o congestión; el agente vuelve a decidir |
| Discreto / continuo | Discreto | Número finito de nodos y aristas; decisiones sobre un conjunto discreto de vecinos |
| Un agente / multiagente | Multiagente (cooperativo) | En la evacuación real hay muchas personas; el agente modela a una persona u origen sin competir con las demás |
| Conocido / desconocido | Parcialmente conocido | Las reglas del modelo (costos, ACO) son conocidas; varios datos del entorno (interior, puntos de encuentro reales) son supuestos |

### Delimitación del agente

Para evitar ambigüedades, esto es exactamente lo que el agente es, hace y no hace en este trabajo (`src/agente.py`, `AgenteEvacuacion`):

| Aspecto | Delimitación |
|---|---|
| Qué es | Un agente que planifica la ruta de **una persona** que parte de **un origen** (una de las 42 aulas u orígenes de PB). Se crea con el grafo, los parámetros del modelo, los parámetros de ACO y el origen |
| Qué percibe (entrada) | Un `EstadoPercibido` con dos datos: las aristas bloqueadas (por ejemplo, una sección de gradas o el acceso a una salida) y un factor de congestión por arista. No percibe nada más: no ve personas, humo, réplicas ni el estado real del edificio |
| Qué decide | La ruta del origen hacia **algún** punto de encuentro (cualquiera de los 3). La decisión la toma **ACO**; por defecto la variante guiada, y la variante clásica si se le indica. Si ya decidió antes, reutiliza la feromona anterior (warm start) para volver a decidir con el nuevo estado |
| Papel de Dijkstra | Solo de referencia: se puede calcular para comparar y medir la brecha, pero **no interviene en la decisión del agente**. `src/aco.py` no lo llama (comprobado en la auditoría) |
| Qué hace (salida) | Devuelve la ruta como lista de nodos, sus instrucciones paso a paso en texto y el tiempo estimado de recorrido (costo / velocidad de caminata). Si no hay ruta, `actuar()` lanza un error explícito (`ValueError`) en lugar de devolver algo inválido |
| Meta (prueba de meta) | Llegar a un nodo de tipo punto de encuentro. Meta binaria y con varias soluciones válidas |
| Utilidad | Menor costo de ruta (distancia, con el factor de gradas y la penalización de tramos techados). Es lo que optimiza ACO y lo que calcula exacto Dijkstra |
| Cuándo actúa | Después de que cesa el movimiento (Protocolo, pág. 2, "Después del sismo", punto 1). El modelo no simula el sismo ni el tiempo de protección en el espacio vital |
| Alcance del entorno | Solo el grafo del complejo G/H (75 nodos, 79 aristas) y la red exterior hasta los 3 puntos de encuentro hipotéticos. Fuera de ese grafo el agente no sabe nada |
| Qué NO es ni hace | No simula a las 1020 personas como 1020 agentes que interactúan: la evacuación completa calcula la ruta de cada origen y suma los tiempos con un modelo simple, sin colas, sin capacidad de gradas o salidas y sin interacción entre personas. No aprende entre simulacros. No decide por el punto de encuentro "real" de la ESPE, porque se desconoce. No coordina a las personas entre sí |
| Cómo se evaluó | Calidad de la ruta frente al óptimo de Dijkstra, tiempo de cómputo, tasa de éxito, adaptación a bloqueos (frío contra warm start), y tiempos de la primera y de la última persona en llegar al punto de encuentro (métricas de la guía de simulacros) |

**Tipo de agente: basado en metas y en utilidad.** Basado en metas porque el éxito es llegar a *algún* punto de encuentro (varias metas válidas); basado en utilidad porque, entre todas las rutas que cumplen la meta, busca la de menor costo, que actúa como utilidad negativa (distancia más penalización de tramos techados, alineada con el Protocolo). Dijkstra calcula el óptimo exacto; ACO lo aproxima por búsqueda estocástica guiada por feromona.

## (e) Optimización por Colonia de Hormigas

Cada hormiga parte de un origen y construye un camino, sin repetir nodos (lista tabú), hasta llegar a cualquier punto de encuentro. Variante MAX-MIN.

**Probabilidad de transición** del nodo i al nodo j (entre los vecinos j no visitados):

```
p_ij = (tau_ij^alfa * eta_ij^beta) / suma_k (tau_ik^alfa * eta_ik^beta)
```

- ACO clásico: `eta_ij = 1 / c_ij` (c_ij = costo de la arista).
- ACO guiado: `eta_ij = 1 / (c_ij + h_j)`, con `h_j` la distancia euclidiana del nodo j al punto de encuentro más cercano (idea de la heurística de A*).

**Evaporación y refuerzo** por iteración:

```
tau_ij <- max(tau_min, (1 - rho) * tau_ij)
tau_ij <- min(tau_max, tau_ij + Q / L_k)   para cada arista (i,j) del camino de cada hormiga k con ruta (L_k = costo del camino)
tau_ij <- min(tau_max, tau_ij + Q / L_mejor)  refuerzo adicional del mejor camino de la iteración
```

Criterio de parada: `n_iteraciones` o `paciencia_estancamiento` iteraciones consecutivas sin mejorar el mejor costo global.

**Parámetros finales** (de `data/config_aco.json`; la variante clásica los declara en su sección propia, a priori y sin ajustarlos a los resultados):

| Parámetro | ACO clásico | ACO guiado |
|---|---|---|
| Hormigas por iteración | 20 | 20 |
| Iteraciones máximas | 100 | 100 |
| alfa | 1.0 | 1.0 |
| beta | 2.0 | 1.0 |
| rho | 0.5 | 0.5 |
| Q | 1.0 | 1.0 |
| tau inicial | 1.0 | 1.0 |
| tau mínimo | 0.01 | 0.01 |
| tau máximo | 10.0 | 10.0 |
| Paciencia (iteraciones sin mejora) | 25 | 25 |
| Poda de callejones | no | sí |
| Retroceso | no (la hormiga atrapada se descarta) | sí (límite de pasos = 4 x nodos) |
| Visibilidad eta | 1 / c | 1 / (c + h) |

La variante clásica usa beta = 2.0 porque es el valor estándar de la literatura (Dorigo y Stützle, 2004); la auditoría había usado beta = 0 (sin visibilidad alguna). Ese valor se fijó antes de correr los experimentos y no se cambió después de ver los resultados.

**Correcciones aplicadas al ACO original (variante guiada):**

1. *Poda de callejones*: antes de correr ACO se construye una vista del grafo (sin modificar el archivo de datos) sin los nodos de grado 1 que no sean el origen ni un punto de encuentro (en la práctica, todas las aulas menos la de origen). Un nodo hoja nunca está en el camino óptimo entre otros dos nodos.
2. *Retroceso con límite de pasos*: si una hormiga no tiene vecinos sin visitar, retrocede un paso y marca ese nodo como muerto solo para ella; falla únicamente si vuelve al origen sin opciones o supera `max_pasos_factor x nodos` pasos.
3. *Heurística guiada tipo A\**: `eta = 1 / (c + h)`.

Diagnóstico que las motivó (con el modelo anterior del edificio, ya descartado): con el tabú original, beta = 3 y Q = 1, una hormiga llegaba a un punto de encuentro con probabilidad de apenas 0.01 % a 0.05 %, porque las aulas son callejones que atrapan al tabú y el costo de las gradas es mucho mayor que el de los tramos planos. Los números de ese modelo anterior no se usan en este informe.

## (f) Auditoría de ACO

Pedida antes de los experimentos finales y corrida sobre el grafo definitivo (75 nodos, 79 aristas).

**G.1. ¿ACO usa Dijkstra?** No. `grep -n -i "dijkstra" src/aco.py` no encontró ninguna coincidencia (código de salida 1). Los únicos imports de `src/aco.py` son `costos` y `grafo`. Las brechas se calculan en `src/metricas.py` y `src/benchmark.py`, que llaman a Dijkstra y a ACO por separado y comparan los resultados ya calculados.

**G.2. Rutas simples** (hacia algún punto de encuentro, tope 5000), 5 orígenes de H:

| Origen | Rutas simples |
|---|---|
| H-PB-OFICINAS_CC | 30 |
| H101 | 48 |
| H201 | 72 |
| H301 | 96 |
| H401 | 96 |

El grafo es casi un árbol (79 - 75 + 1 = 5 ciclos independientes), con pocas alternativas reales entre las que elegir.

**G.3. Tres variantes de ACO, 5 orígenes de H, 20 corridas cada una** (éxito / brecha frente a Dijkstra):

| Variante | H-PB-OFICINAS_CC | H101 | H201 | H301 | H401 |
|---|---|---|---|---|---|
| (a) Actual: poda + retroceso + heurística, beta = 1 | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % |
| (b) Sin heurística (beta = 0), con poda y retroceso | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % |
| (c) Sin heurística (beta = 0), tabú original (sin poda ni retroceso) | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 0.00 % | 100 % / 7.54 % | 100 % / 5.80 % |

Tiempos de la auditoría: entre 15 y 60 ms por corrida en todas las variantes (reportado solo como rango).

**Conclusión de la auditoría.** La poda de callejones por sí sola (variante b, sin heurística) ya alcanza el óptimo en todas las corridas; la heurística no es la que resuelve el problema. Solo la variante (c) muestra una brecha distinta de cero. Por eso se eligió la variante (c) como **"ACO clásico"** y la variante (a) como **"ACO guiado"**, y se corren ambas en los experimentos.

**Reservas de la auditoría:** solo se probaron 5 orígenes, todos de H; 20 corridas por origen; la variante (c) se probó únicamente con beta = 0; los tiempos se reportaron como rango. Los experimentos oficiales de la sección (g) cubren los 42 orígenes, 30 corridas y ambas variantes.

## (g) Metodología y tablas numéricas

### Metodología

- Escenarios (6): Normal; gradas norte bloqueadas (todas las aristas de la sección norte); gradas sur bloqueadas; Salida A bloqueada; Salida B bloqueada; congestión en una salida (la arista de gradas de PB hacia la Salida A multiplica su distancia por 3.0).
- Benchmark principal: 6 escenarios x 42 orígenes x 30 corridas x 2 variantes de ACO = 15120 corridas. Semilla de la corrida i = 1000 + i (la misma para ambas variantes). Dijkstra: costo y ruta una vez por origen y escenario sobre el grafo del escenario (con bloqueos y congestión); su tiempo es la mediana de 30 repeticiones.
- Adaptación: para los 5 escenarios distintos de Normal, ACO en frío (las mismas corridas del benchmark) contra ACO con warm start (feromonas finales del escenario Normal del mismo origen, variante y semilla).
- Sensibilidad (solo ACO clásico): un factor a la vez (alfa, beta, rho, n_hormigas; 5 valores cada uno), 10 orígenes representativos, escenario Normal, 30 corridas por combinación.
- Diagnóstico complementario (no estaba en el plan original): efecto de la constante de depósito Q (1, 10, 100, 1000) con beta = 0 y beta = 2, ACO clásico, mismos 10 orígenes; se agregó para explicar por qué alfa y rho no producen efecto.
- Evacuación completa: población de `data/config_modelo.json` (1020 personas). Primera persona de un origen = tiempo de reacción + tiempo de recorrido de su ruta; la persona k de ese origen llega 1 s x k después. Para ACO se usa la ruta de la primera corrida exitosa de cada origen; si ninguna de las 30 corridas tuvo ruta, esas personas se cuentan como sin ruta. Sin colas ni capacidad.
- Prueba de cordura: en cada corrida exitosa, costo de ACO >= costo de Dijkstra - 1e-9 sobre el mismo grafo del escenario. Corridas exitosas verificadas: 20077; violaciones: 0; resultado: aprobada.
- Ejecución: 7.35 min en total (estimación previa 8.89 min), secuencial. Reducción de corridas aplicada: ninguna. Python 3.13.17; librerías: pandas 3.0.5, numpy 2.5.3, matplotlib 3.11.2, streamlit 1.66.1, PIL 12.3.0; plataforma: Linux-6.18.44-fc-v165-x86_64-with-glibc2.39.

### Tabla g.1 Dijkstra (referencia): costo medio y tiempo por escenario

| Escenario | Costo medio (42 orígenes) | Tiempo medio (ms) |
|---|---|---|
| Normal | 199.318 | 0.093 |
| Gradas norte bloqueadas | 245.913 | 0.079 |
| Gradas sur bloqueadas | 199.318 | 0.076 |
| Salida A bloqueada | 199.318 | 0.079 |
| Salida B bloqueada | 245.913 | 0.080 |
| Congestión en una salida | 199.318 | 0.089 |

### Tabla g.2 Benchmark principal por variante y escenario (30 corridas x 42 orígenes)

Éxito = corridas con ruta; costo, brecha e iteración de convergencia se calculan sobre las corridas exitosas.

| Variante | Escenario | Corridas | Éxito (%) | Costo medio | Desv. | Mín. | Máx. | Brecha media (%) | Brecha máx. (%) | Corridas óptimas (%) | Tiempo medio (ms) | Desv. tiempo (ms) | Iteración de convergencia |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACO clásico | Normal | 1260 | 21.83 | 218.14 | 59.74 | 160.96 | 375.64 | 14.17 | 95.48 | 15.48 | 5.54 | 2.17 | 12.03 |
| ACO clásico | Gradas norte bloqueadas | 1260 | 11.11 | 247.62 | 37.45 | 207.56 | 300.67 | 6.41 | 27.89 | 8.33 | 4.96 | 1.46 | 8.66 |
| ACO clásico | Gradas sur bloqueadas | 1260 | 15.08 | 193.54 | 48.13 | 160.96 | 380.83 | 5.07 | 96.92 | 14.29 | 5.23 | 1.86 | 8.95 |
| ACO clásico | Salida A bloqueada | 1260 | 21.43 | 224.33 | 72.01 | 160.96 | 500.23 | 17.09 | 157.07 | 14.68 | 5.53 | 2.23 | 12.03 |
| ACO clásico | Salida B bloqueada | 1260 | 13.49 | 256.29 | 44.77 | 207.56 | 358.99 | 8.39 | 50.36 | 9.52 | 5.55 | 2.55 | 11.74 |
| ACO clásico | Congestión en una salida | 1260 | 20.24 | 216.24 | 60.10 | 160.96 | 381.26 | 12.83 | 98.41 | 14.68 | 5.87 | 2.26 | 12.00 |
| ACO guiado | Normal | 1260 | 100.00 | 199.32 | 18.99 | 160.96 | 225.79 | 0.00 | 0.00 | 100.00 | 24.05 | 4.83 | 1.43 |
| ACO guiado | Gradas norte bloqueadas | 1260 | 100.00 | 245.91 | 18.99 | 207.56 | 272.38 | 0.00 | 0.00 | 100.00 | 15.16 | 2.43 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | 1260 | 100.00 | 199.32 | 18.99 | 160.96 | 225.79 | 0.00 | 0.00 | 100.00 | 13.42 | 2.91 | 1.00 |
| ACO guiado | Salida A bloqueada | 1260 | 100.00 | 199.32 | 18.99 | 160.96 | 225.79 | 0.00 | 0.00 | 100.00 | 24.48 | 5.50 | 1.16 |
| ACO guiado | Salida B bloqueada | 1260 | 100.00 | 245.91 | 18.99 | 207.56 | 272.38 | 0.00 | 0.00 | 100.00 | 29.60 | 5.71 | 1.67 |
| ACO guiado | Congestión en una salida | 1260 | 100.00 | 199.32 | 18.99 | 160.96 | 225.79 | 0.00 | 0.00 | 100.00 | 24.15 | 4.93 | 1.43 |

### Tabla g.3 Adaptación: ACO en frío contra warm start

| Variante | Escenario | Conv. frío | Conv. warm | Reducción conv. (%) | Iter. ejec. frío | Iter. ejec. warm | Reducción iter. ejec. (%) | Tiempo frío (ms) | Tiempo warm (ms) | Reducción tiempo (%) | Éxito frío (%) | Éxito warm (%) | Brecha frío (%) | Brecha warm (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACO clásico | Gradas norte bloqueadas | 8.66 | 9.20 | -6.18 | 25.96 | 26.02 | -0.23 | 4.96 | 5.48 | -10.50 | 11.11 | 11.11 | 6.41 | 6.41 |
| ACO clásico | Gradas sur bloqueadas | 8.95 | 8.58 | 4.12 | 26.35 | 26.29 | 0.21 | 5.23 | 5.32 | -1.84 | 15.08 | 15.08 | 5.07 | 5.07 |
| ACO clásico | Salida A bloqueada | 12.03 | 11.81 | 1.76 | 27.58 | 27.53 | 0.16 | 5.53 | 5.30 | 4.22 | 21.43 | 21.43 | 17.09 | 17.09 |
| ACO clásico | Salida B bloqueada | 11.74 | 12.46 | -6.17 | 26.58 | 26.68 | -0.37 | 5.55 | 5.53 | 0.27 | 13.49 | 13.49 | 8.39 | 8.39 |
| ACO clásico | Congestión en una salida | 12.00 | 11.82 | 1.44 | 27.43 | 27.39 | 0.13 | 5.87 | 5.52 | 6.00 | 20.24 | 20.24 | 12.83 | 12.83 |
| ACO guiado | Gradas norte bloqueadas | 1.00 | 1.00 | 0.00 | 26.00 | 26.00 | 0.00 | 15.16 | 14.52 | 4.21 | 100.00 | 100.00 | 0.00 | 0.00 |
| ACO guiado | Gradas sur bloqueadas | 1.00 | 1.00 | 0.00 | 26.00 | 26.00 | 0.00 | 13.42 | 13.11 | 2.35 | 100.00 | 100.00 | 0.00 | 0.00 |
| ACO guiado | Salida A bloqueada | 1.16 | 1.00 | 13.70 | 26.16 | 26.00 | 0.61 | 24.48 | 18.63 | 23.90 | 100.00 | 100.00 | 0.00 | 0.00 |
| ACO guiado | Salida B bloqueada | 1.67 | 5.04 | -202.52 | 26.67 | 30.04 | -12.66 | 29.60 | 30.87 | -4.29 | 100.00 | 100.00 | 0.00 | 0.00 |
| ACO guiado | Congestión en una salida | 1.43 | 1.00 | 30.00 | 26.43 | 26.00 | 1.62 | 24.15 | 19.24 | 20.35 | 100.00 | 100.00 | 0.00 | 0.00 |

### Tabla g.4 Adaptación: detalle por variante, escenario y modo

| Variante | Escenario | Modo | Corridas | Éxito (%) | Costo medio | Brecha media (%) | Tiempo medio (ms) | Iteración de convergencia | Iteraciones ejecutadas |
|---|---|---|---|---|---|---|---|---|---|
| ACO clásico | Gradas norte bloqueadas | frio | 1260 | 11.11 | 247.62 | 6.41 | 4.96 | 8.66 | 25.96 |
| ACO clásico | Gradas sur bloqueadas | frio | 1260 | 15.08 | 193.54 | 5.07 | 5.23 | 8.95 | 26.35 |
| ACO clásico | Salida A bloqueada | frio | 1260 | 21.43 | 224.33 | 17.09 | 5.53 | 12.03 | 27.58 |
| ACO clásico | Salida B bloqueada | frio | 1260 | 13.49 | 256.29 | 8.39 | 5.55 | 11.74 | 26.58 |
| ACO clásico | Congestión en una salida | frio | 1260 | 20.24 | 216.24 | 12.83 | 5.87 | 12.00 | 27.43 |
| ACO guiado | Gradas norte bloqueadas | frio | 1260 | 100.00 | 245.91 | 0.00 | 15.16 | 1.00 | 26.00 |
| ACO guiado | Gradas sur bloqueadas | frio | 1260 | 100.00 | 199.32 | 0.00 | 13.42 | 1.00 | 26.00 |
| ACO guiado | Salida A bloqueada | frio | 1260 | 100.00 | 199.32 | 0.00 | 24.48 | 1.16 | 26.16 |
| ACO guiado | Salida B bloqueada | frio | 1260 | 100.00 | 245.91 | 0.00 | 29.60 | 1.67 | 26.67 |
| ACO guiado | Congestión en una salida | frio | 1260 | 100.00 | 199.32 | 0.00 | 24.15 | 1.43 | 26.43 |
| ACO clásico | Gradas norte bloqueadas | warm_start | 1260 | 11.11 | 247.62 | 6.41 | 5.48 | 9.20 | 26.02 |
| ACO clásico | Gradas sur bloqueadas | warm_start | 1260 | 15.08 | 193.54 | 5.07 | 5.32 | 8.58 | 26.29 |
| ACO clásico | Salida A bloqueada | warm_start | 1260 | 21.43 | 224.33 | 17.09 | 5.30 | 11.81 | 27.53 |
| ACO clásico | Salida B bloqueada | warm_start | 1260 | 13.49 | 256.29 | 8.39 | 5.53 | 12.46 | 26.68 |
| ACO clásico | Congestión en una salida | warm_start | 1260 | 20.24 | 216.24 | 12.83 | 5.52 | 11.82 | 27.39 |
| ACO guiado | Gradas norte bloqueadas | warm_start | 1260 | 100.00 | 245.91 | 0.00 | 14.52 | 1.00 | 26.00 |
| ACO guiado | Gradas sur bloqueadas | warm_start | 1260 | 100.00 | 199.32 | 0.00 | 13.11 | 1.00 | 26.00 |
| ACO guiado | Salida A bloqueada | warm_start | 1260 | 100.00 | 199.32 | 0.00 | 18.63 | 1.00 | 26.00 |
| ACO guiado | Salida B bloqueada | warm_start | 1260 | 100.00 | 245.91 | 0.00 | 30.87 | 5.04 | 30.04 |
| ACO guiado | Congestión en una salida | warm_start | 1260 | 100.00 | 199.32 | 0.00 | 19.24 | 1.00 | 26.00 |

### Tabla g.5 Sensibilidad de ACO clásico (10 orígenes, escenario Normal)

| Parámetro | Valor | Corridas | Éxito (%) | Brecha media (%) | Brecha máx. (%) | Corridas óptimas (%) | Tiempo medio (ms) | Iteración de convergencia |
|---|---|---|---|---|---|---|---|---|
| alfa | 0.00 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.59 | 7.59 |
| alfa | 0.50 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.62 | 7.55 |
| alfa | 1.00 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.95 | 7.58 |
| alfa | 2.00 | 300.00 | 34.33 | 7.13 | 95.48 | 29.33 | 6.57 | 7.63 |
| alfa | 3.00 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.67 | 7.45 |
| beta | 0.00 | 300.00 | 99.33 | 1.92 | 65.36 | 92.00 | 11.60 | 9.94 |
| beta | 1.00 | 300.00 | 76.33 | 13.99 | 159.91 | 56.00 | 8.43 | 11.99 |
| beta | 2.00 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.54 | 7.58 |
| beta | 3.00 | 300.00 | 21.00 | 1.34 | 42.45 | 20.33 | 6.10 | 4.98 |
| beta | 5.00 | 300.00 | 14.33 | 3.12 | 67.62 | 13.67 | 5.95 | 11.30 |
| rho | 0.10 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 7.09 | 7.60 |
| rho | 0.30 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.73 | 7.56 |
| rho | 0.50 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.47 | 7.58 |
| rho | 0.70 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.76 | 7.53 |
| rho | 0.90 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.67 | 7.51 |
| n_hormigas | 5.00 | 300.00 | 22.33 | 2.78 | 95.48 | 21.33 | 2.27 | 8.15 |
| n_hormigas | 10.00 | 300.00 | 26.67 | 5.24 | 95.48 | 24.00 | 3.44 | 6.58 |
| n_hormigas | 20.00 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.76 | 7.58 |
| n_hormigas | 30.00 | 300.00 | 39.33 | 5.19 | 95.48 | 35.33 | 9.33 | 8.41 |
| n_hormigas | 50.00 | 300.00 | 51.33 | 8.19 | 95.48 | 43.33 | 17.16 | 8.71 |

### Tabla g.6 Diagnóstico complementario: constante de depósito Q (ACO clásico)

| Q | beta | Corridas | Éxito (%) | Brecha media (%) | Brecha máx. (%) | Corridas óptimas (%) | Tiempo medio (ms) | Iteración de convergencia |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 300.00 | 99.33 | 1.92 | 65.36 | 92.00 | 10.47 | 9.94 |
| 1 | 2 | 300.00 | 34.33 | 7.57 | 95.48 | 29.00 | 6.34 | 7.58 |
| 10 | 0 | 300.00 | 99.33 | 3.85 | 46.32 | 82.67 | 17.90 | 6.46 |
| 10 | 2 | 300.00 | 34.33 | 6.90 | 95.48 | 29.67 | 6.64 | 8.12 |
| 100 | 0 | 300.00 | 99.33 | 11.93 | 103.92 | 68.33 | 20.39 | 6.53 |
| 100 | 2 | 300.00 | 34.33 | 13.56 | 95.48 | 25.00 | 8.34 | 6.99 |
| 1000 | 0 | 300.00 | 99.33 | 16.34 | 130.77 | 64.33 | 24.65 | 6.22 |
| 1000 | 2 | 300.00 | 34.33 | 13.71 | 95.48 | 25.00 | 8.72 | 7.85 |

### Tabla g.7 Evacuación completa (1020 personas)

Tiempos en segundos desde la emisión de la alerta.

| Variante | Escenario | Con ruta | Sin ruta | Primera (s) | Última (s) | Salida A | Salida B | PE-1 | PE-2 | PE-3 |
|---|---|---|---|---|---|---|---|---|---|---|
| Dijkstra | Normal | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| Dijkstra | Gradas norte bloqueadas | 1020 | 0 | 233.0 | 311.0 | 1020 | 0 | 0 | 1020 | 0 |
| Dijkstra | Gradas sur bloqueadas | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| Dijkstra | Salida A bloqueada | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| Dijkstra | Salida B bloqueada | 1020 | 0 | 233.0 | 311.0 | 1020 | 0 | 0 | 1020 | 0 |
| Dijkstra | Congestión en una salida | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| ACO clásico | Normal | 1020 | 0 | 194.1 | 383.2 | 125 | 895 | 125 | 895 | 0 |
| ACO clásico | Gradas norte bloqueadas | 770 | 250 | 233.0 | 334.6 | 770 | 0 | 125 | 395 | 250 |
| ACO clásico | Gradas sur bloqueadas | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| ACO clásico | Salida A bloqueada | 1020 | 0 | 194.1 | 500.9 | 0 | 1020 | 125 | 895 | 0 |
| ACO clásico | Salida B bloqueada | 895 | 125 | 233.0 | 383.2 | 895 | 0 | 250 | 645 | 0 |
| ACO clásico | Congestión en una salida | 1020 | 0 | 194.1 | 401.7 | 125 | 895 | 125 | 895 | 0 |
| ACO guiado | Normal | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| ACO guiado | Gradas norte bloqueadas | 1020 | 0 | 233.0 | 311.0 | 1020 | 0 | 0 | 1020 | 0 |
| ACO guiado | Gradas sur bloqueadas | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| ACO guiado | Salida A bloqueada | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |
| ACO guiado | Salida B bloqueada | 1020 | 0 | 233.0 | 311.0 | 1020 | 0 | 0 | 1020 | 0 |
| ACO guiado | Congestión en una salida | 1020 | 0 | 194.1 | 272.2 | 0 | 1020 | 0 | 1020 | 0 |

### Tabla g.8 Reparto de orígenes por salida y punto de encuentro (42 orígenes)

| Variante | Escenario | Orígenes con ruta | % por Salida A | % por Salida B | PE-1 | PE-2 | PE-3 |
|---|---|---|---|---|---|---|---|
| Dijkstra | Normal | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| Dijkstra | Gradas norte bloqueadas | 42 | 100.0 | 0.0 | 0 | 42 | 0 |
| Dijkstra | Gradas sur bloqueadas | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| Dijkstra | Salida A bloqueada | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| Dijkstra | Salida B bloqueada | 42 | 100.0 | 0.0 | 0 | 42 | 0 |
| Dijkstra | Congestión en una salida | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| ACO clásico | Normal | 42 | 11.9 | 88.1 | 5 | 37 | 0 |
| ACO clásico | Gradas norte bloqueadas | 32 | 76.2 | 0.0 | 5 | 17 | 10 |
| ACO clásico | Gradas sur bloqueadas | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| ACO clásico | Salida A bloqueada | 42 | 0.0 | 100.0 | 5 | 37 | 0 |
| ACO clásico | Salida B bloqueada | 37 | 88.1 | 0.0 | 10 | 27 | 0 |
| ACO clásico | Congestión en una salida | 42 | 11.9 | 88.1 | 5 | 37 | 0 |
| ACO guiado | Normal | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| ACO guiado | Gradas norte bloqueadas | 42 | 100.0 | 0.0 | 0 | 42 | 0 |
| ACO guiado | Gradas sur bloqueadas | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| ACO guiado | Salida A bloqueada | 42 | 0.0 | 100.0 | 0 | 42 | 0 |
| ACO guiado | Salida B bloqueada | 42 | 100.0 | 0.0 | 0 | 42 | 0 |
| ACO guiado | Congestión en una salida | 42 | 0.0 | 100.0 | 0 | 42 | 0 |

### Tabla g.9 Prueba de cordura

```
Prueba de cordura: costo_ACO >= costo_Dijkstra - 1e-9 sobre el grafo de cada escenario
Corridas exitosas verificadas: 20077
Violaciones: 0
Resultado: APROBADA
```

### Tabla g.10 Resumen por origen (42 orígenes x 6 escenarios x 2 variantes)

| Variante | Escenario | Origen | Éxito (%) | Brecha media (%) | Tiempo medio (ms) | Iteración de convergencia |
|---|---|---|---|---|---|---|
| ACO clásico | Normal | H-PB-OFICINAS_CC | 100.00 | 0.00 | 13.25 | 2.53 |
| ACO clásico | Normal | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 12.47 | 2.43 |
| ACO clásico | Normal | H101 | 26.67 | 0.00 | 5.11 | 16.38 |
| ACO clásico | Normal | H102 | 26.67 | 0.00 | 5.16 | 16.38 |
| ACO clásico | Normal | H103 | 26.67 | 0.00 | 5.43 | 16.38 |
| ACO clásico | Normal | H104 | 26.67 | 0.00 | 5.24 | 16.38 |
| ACO clásico | Normal | H105 | 26.67 | 0.00 | 5.27 | 16.38 |
| ACO clásico | Normal | H201 | 26.67 | 45.36 | 5.15 | 12.62 |
| ACO clásico | Normal | H202 | 26.67 | 45.36 | 5.05 | 12.62 |
| ACO clásico | Normal | H203 | 26.67 | 45.36 | 5.07 | 12.62 |
| ACO clásico | Normal | H204 | 26.67 | 45.36 | 5.47 | 12.62 |
| ACO clásico | Normal | H205 | 26.67 | 45.36 | 5.34 | 12.62 |
| ACO clásico | Normal | H301 | 16.67 | 16.98 | 5.04 | 13.20 |
| ACO clásico | Normal | H302 | 16.67 | 16.98 | 5.08 | 13.20 |
| ACO clásico | Normal | H303 | 16.67 | 16.98 | 5.27 | 13.20 |
| ACO clásico | Normal | H304 | 16.67 | 16.98 | 5.09 | 13.20 |
| ACO clásico | Normal | H305 | 16.67 | 16.98 | 5.10 | 13.20 |
| ACO clásico | Normal | H401 | 16.67 | 14.85 | 5.18 | 18.60 |
| ACO clásico | Normal | H402 | 16.67 | 14.85 | 5.15 | 18.60 |
| ACO clásico | Normal | H403 | 16.67 | 14.85 | 5.46 | 18.60 |
| ACO clásico | Normal | H404 | 16.67 | 14.85 | 5.05 | 18.60 |
| ACO clásico | Normal | H405 | 16.67 | 14.85 | 5.22 | 18.60 |
| ACO clásico | Normal | G101 | 16.67 | 0.00 | 4.92 | 14.40 |
| ACO clásico | Normal | G102 | 16.67 | 0.00 | 5.16 | 14.40 |
| ACO clásico | Normal | G103 | 16.67 | 0.00 | 4.90 | 14.40 |
| ACO clásico | Normal | G104 | 16.67 | 0.00 | 5.51 | 14.40 |
| ACO clásico | Normal | G105 | 16.67 | 0.00 | 6.14 | 14.40 |
| ACO clásico | Normal | G201 | 20.00 | 16.64 | 5.02 | 12.00 |
| ACO clásico | Normal | G202 | 20.00 | 16.64 | 5.16 | 12.00 |
| ACO clásico | Normal | G203 | 20.00 | 16.64 | 5.99 | 12.00 |
| ACO clásico | Normal | G204 | 20.00 | 16.64 | 5.11 | 12.00 |
| ACO clásico | Normal | G205 | 20.00 | 16.64 | 5.15 | 12.00 |
| ACO clásico | Normal | G301 | 10.00 | 27.97 | 5.52 | 14.67 |
| ACO clásico | Normal | G302 | 10.00 | 27.97 | 5.25 | 14.67 |
| ACO clásico | Normal | G303 | 10.00 | 27.97 | 4.69 | 14.67 |
| ACO clásico | Normal | G304 | 10.00 | 27.97 | 4.74 | 14.67 |
| ACO clásico | Normal | G305 | 10.00 | 27.97 | 5.02 | 14.67 |
| ACO clásico | Normal | G401 | 10.00 | 24.48 | 4.98 | 17.67 |
| ACO clásico | Normal | G402 | 10.00 | 24.48 | 4.74 | 17.67 |
| ACO clásico | Normal | G403 | 10.00 | 24.48 | 4.90 | 17.67 |
| ACO clásico | Normal | G404 | 10.00 | 24.48 | 5.55 | 17.67 |
| ACO clásico | Normal | G405 | 10.00 | 24.48 | 4.67 | 17.67 |
| ACO clásico | Gradas norte bloqueadas | H-PB-OFICINAS_CC | 100.00 | 0.00 | 9.10 | 3.77 |
| ACO clásico | Gradas norte bloqueadas | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 10.45 | 4.17 |
| ACO clásico | Gradas norte bloqueadas | H101 | 6.67 | 13.95 | 5.07 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | H102 | 6.67 | 13.95 | 4.74 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | H103 | 6.67 | 13.95 | 4.34 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | H104 | 6.67 | 13.95 | 4.68 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | H105 | 6.67 | 13.95 | 4.58 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | H201 | 13.33 | 18.68 | 4.85 | 8.00 |
| ACO clásico | Gradas norte bloqueadas | H202 | 13.33 | 18.68 | 5.52 | 8.00 |
| ACO clásico | Gradas norte bloqueadas | H203 | 13.33 | 18.68 | 4.42 | 8.00 |
| ACO clásico | Gradas norte bloqueadas | H204 | 13.33 | 18.68 | 4.47 | 8.00 |
| ACO clásico | Gradas norte bloqueadas | H205 | 13.33 | 18.68 | 4.43 | 8.00 |
| ACO clásico | Gradas norte bloqueadas | H301 | 0.00 | - | 4.82 | - |
| ACO clásico | Gradas norte bloqueadas | H302 | 0.00 | - | 4.94 | - |
| ACO clásico | Gradas norte bloqueadas | H303 | 0.00 | - | 4.50 | - |
| ACO clásico | Gradas norte bloqueadas | H304 | 0.00 | - | 4.61 | - |
| ACO clásico | Gradas norte bloqueadas | H305 | 0.00 | - | 5.19 | - |
| ACO clásico | Gradas norte bloqueadas | H401 | 13.33 | 0.00 | 4.72 | 11.00 |
| ACO clásico | Gradas norte bloqueadas | H402 | 13.33 | 0.00 | 4.80 | 11.00 |
| ACO clásico | Gradas norte bloqueadas | H403 | 13.33 | 0.00 | 4.73 | 11.00 |
| ACO clásico | Gradas norte bloqueadas | H404 | 13.33 | 0.00 | 4.66 | 11.00 |
| ACO clásico | Gradas norte bloqueadas | H405 | 13.33 | 0.00 | 4.71 | 11.00 |
| ACO clásico | Gradas norte bloqueadas | G101 | 3.33 | 27.59 | 4.53 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | G102 | 3.33 | 27.59 | 4.98 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | G103 | 3.33 | 27.59 | 4.94 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | G104 | 3.33 | 27.59 | 4.46 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | G105 | 3.33 | 27.59 | 4.41 | 19.00 |
| ACO clásico | Gradas norte bloqueadas | G201 | 6.67 | 24.66 | 4.50 | 10.00 |
| ACO clásico | Gradas norte bloqueadas | G202 | 6.67 | 24.66 | 4.53 | 10.00 |
| ACO clásico | Gradas norte bloqueadas | G203 | 6.67 | 24.66 | 4.54 | 10.00 |
| ACO clásico | Gradas norte bloqueadas | G204 | 6.67 | 24.66 | 4.46 | 10.00 |
| ACO clásico | Gradas norte bloqueadas | G205 | 6.67 | 24.66 | 4.51 | 10.00 |
| ACO clásico | Gradas norte bloqueadas | G301 | 0.00 | - | 4.42 | - |
| ACO clásico | Gradas norte bloqueadas | G302 | 0.00 | - | 5.12 | - |
| ACO clásico | Gradas norte bloqueadas | G303 | 0.00 | - | 5.50 | - |
| ACO clásico | Gradas norte bloqueadas | G304 | 0.00 | - | 4.60 | - |
| ACO clásico | Gradas norte bloqueadas | G305 | 0.00 | - | 4.64 | - |
| ACO clásico | Gradas norte bloqueadas | G401 | 10.00 | 0.00 | 5.36 | 14.00 |
| ACO clásico | Gradas norte bloqueadas | G402 | 10.00 | 0.00 | 4.58 | 14.00 |
| ACO clásico | Gradas norte bloqueadas | G403 | 10.00 | 0.00 | 4.50 | 14.00 |
| ACO clásico | Gradas norte bloqueadas | G404 | 10.00 | 0.00 | 4.77 | 14.00 |
| ACO clásico | Gradas norte bloqueadas | G405 | 10.00 | 0.00 | 4.65 | 14.00 |
| ACO clásico | Gradas sur bloqueadas | H-PB-OFICINAS_CC | 100.00 | 0.00 | 10.03 | 2.03 |
| ACO clásico | Gradas sur bloqueadas | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 12.37 | 2.30 |
| ACO clásico | Gradas sur bloqueadas | H101 | 20.00 | 0.00 | 4.76 | 12.17 |
| ACO clásico | Gradas sur bloqueadas | H102 | 20.00 | 0.00 | 4.83 | 12.17 |
| ACO clásico | Gradas sur bloqueadas | H103 | 20.00 | 0.00 | 4.65 | 12.17 |
| ACO clásico | Gradas sur bloqueadas | H104 | 20.00 | 0.00 | 4.81 | 12.17 |
| ACO clásico | Gradas sur bloqueadas | H105 | 20.00 | 0.00 | 4.64 | 12.17 |
| ACO clásico | Gradas sur bloqueadas | H201 | 13.33 | 24.23 | 4.53 | 12.25 |
| ACO clásico | Gradas sur bloqueadas | H202 | 13.33 | 24.23 | 4.47 | 12.25 |
| ACO clásico | Gradas sur bloqueadas | H203 | 13.33 | 24.23 | 4.54 | 12.25 |
| ACO clásico | Gradas sur bloqueadas | H204 | 13.33 | 24.23 | 4.74 | 12.25 |
| ACO clásico | Gradas sur bloqueadas | H205 | 13.33 | 24.23 | 5.44 | 12.25 |
| ACO clásico | Gradas sur bloqueadas | H301 | 13.33 | 0.00 | 6.41 | 14.75 |
| ACO clásico | Gradas sur bloqueadas | H302 | 13.33 | 0.00 | 6.77 | 14.75 |
| ACO clásico | Gradas sur bloqueadas | H303 | 13.33 | 0.00 | 5.25 | 14.75 |
| ACO clásico | Gradas sur bloqueadas | H304 | 13.33 | 0.00 | 4.68 | 14.75 |
| ACO clásico | Gradas sur bloqueadas | H305 | 13.33 | 0.00 | 4.86 | 14.75 |
| ACO clásico | Gradas sur bloqueadas | H401 | 6.67 | 0.00 | 4.88 | 16.50 |
| ACO clásico | Gradas sur bloqueadas | H402 | 6.67 | 0.00 | 4.55 | 16.50 |
| ACO clásico | Gradas sur bloqueadas | H403 | 6.67 | 0.00 | 4.67 | 16.50 |
| ACO clásico | Gradas sur bloqueadas | H404 | 6.67 | 0.00 | 4.56 | 16.50 |
| ACO clásico | Gradas sur bloqueadas | H405 | 6.67 | 0.00 | 4.53 | 16.50 |
| ACO clásico | Gradas sur bloqueadas | G101 | 13.33 | 0.00 | 4.46 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G102 | 13.33 | 0.00 | 4.56 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G103 | 13.33 | 0.00 | 4.48 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G104 | 13.33 | 0.00 | 5.38 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G105 | 13.33 | 0.00 | 4.91 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G201 | 13.33 | 23.93 | 4.92 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G202 | 13.33 | 23.93 | 4.95 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G203 | 13.33 | 23.93 | 5.04 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G204 | 13.33 | 23.93 | 5.04 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G205 | 13.33 | 23.93 | 4.88 | 8.75 |
| ACO clásico | Gradas sur bloqueadas | G301 | 3.33 | 0.00 | 6.65 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G302 | 3.33 | 0.00 | 4.52 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G303 | 3.33 | 0.00 | 4.68 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G304 | 3.33 | 0.00 | 4.59 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G305 | 3.33 | 0.00 | 4.65 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G401 | 3.33 | 0.00 | 4.84 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G402 | 3.33 | 0.00 | 4.63 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G403 | 3.33 | 0.00 | 5.24 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G404 | 3.33 | 0.00 | 5.49 | 15.00 |
| ACO clásico | Gradas sur bloqueadas | G405 | 3.33 | 0.00 | 4.55 | 15.00 |
| ACO clásico | Salida A bloqueada | H-PB-OFICINAS_CC | 100.00 | 0.00 | 12.97 | 1.83 |
| ACO clásico | Salida A bloqueada | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 13.05 | 2.07 |
| ACO clásico | Salida A bloqueada | H101 | 26.67 | 0.00 | 5.29 | 16.38 |
| ACO clásico | Salida A bloqueada | H102 | 26.67 | 0.00 | 6.77 | 16.38 |
| ACO clásico | Salida A bloqueada | H103 | 26.67 | 0.00 | 5.36 | 16.38 |
| ACO clásico | Salida A bloqueada | H104 | 26.67 | 0.00 | 5.15 | 16.38 |
| ACO clásico | Salida A bloqueada | H105 | 26.67 | 0.00 | 5.31 | 16.38 |
| ACO clásico | Salida A bloqueada | H201 | 16.67 | 59.92 | 5.08 | 17.00 |
| ACO clásico | Salida A bloqueada | H202 | 16.67 | 59.92 | 5.03 | 17.00 |
| ACO clásico | Salida A bloqueada | H203 | 16.67 | 59.92 | 5.05 | 17.00 |
| ACO clásico | Salida A bloqueada | H204 | 16.67 | 59.92 | 5.21 | 17.00 |
| ACO clásico | Salida A bloqueada | H205 | 16.67 | 59.92 | 5.18 | 17.00 |
| ACO clásico | Salida A bloqueada | H301 | 20.00 | 18.72 | 4.99 | 11.50 |
| ACO clásico | Salida A bloqueada | H302 | 20.00 | 18.72 | 6.55 | 11.50 |
| ACO clásico | Salida A bloqueada | H303 | 20.00 | 18.72 | 5.02 | 11.50 |
| ACO clásico | Salida A bloqueada | H304 | 20.00 | 18.72 | 4.93 | 11.50 |
| ACO clásico | Salida A bloqueada | H305 | 20.00 | 18.72 | 5.61 | 11.50 |
| ACO clásico | Salida A bloqueada | H401 | 16.67 | 10.21 | 5.25 | 18.80 |
| ACO clásico | Salida A bloqueada | H402 | 16.67 | 10.21 | 5.31 | 18.80 |
| ACO clásico | Salida A bloqueada | H403 | 16.67 | 10.21 | 5.36 | 18.80 |
| ACO clásico | Salida A bloqueada | H404 | 16.67 | 10.21 | 5.13 | 18.80 |
| ACO clásico | Salida A bloqueada | H405 | 16.67 | 10.21 | 5.10 | 18.80 |
| ACO clásico | Salida A bloqueada | G101 | 16.67 | 0.00 | 5.07 | 14.40 |
| ACO clásico | Salida A bloqueada | G102 | 16.67 | 0.00 | 5.65 | 14.40 |
| ACO clásico | Salida A bloqueada | G103 | 16.67 | 0.00 | 5.11 | 14.40 |
| ACO clásico | Salida A bloqueada | G104 | 16.67 | 0.00 | 4.87 | 14.40 |
| ACO clásico | Salida A bloqueada | G105 | 16.67 | 0.00 | 4.99 | 14.40 |
| ACO clásico | Salida A bloqueada | G201 | 20.00 | 49.68 | 4.97 | 12.33 |
| ACO clásico | Salida A bloqueada | G202 | 20.00 | 49.68 | 4.94 | 12.33 |
| ACO clásico | Salida A bloqueada | G203 | 20.00 | 49.68 | 4.96 | 12.33 |
| ACO clásico | Salida A bloqueada | G204 | 20.00 | 49.68 | 5.45 | 12.33 |
| ACO clásico | Salida A bloqueada | G205 | 20.00 | 49.68 | 5.11 | 12.33 |
| ACO clásico | Salida A bloqueada | G301 | 13.33 | 27.76 | 4.71 | 11.75 |
| ACO clásico | Salida A bloqueada | G302 | 13.33 | 27.76 | 5.07 | 11.75 |
| ACO clásico | Salida A bloqueada | G303 | 13.33 | 27.76 | 4.79 | 11.75 |
| ACO clásico | Salida A bloqueada | G304 | 13.33 | 27.76 | 4.57 | 11.75 |
| ACO clásico | Salida A bloqueada | G305 | 13.33 | 27.76 | 4.78 | 11.75 |
| ACO clásico | Salida A bloqueada | G401 | 10.00 | 16.83 | 5.18 | 18.00 |
| ACO clásico | Salida A bloqueada | G402 | 10.00 | 16.83 | 4.44 | 18.00 |
| ACO clásico | Salida A bloqueada | G403 | 10.00 | 16.83 | 4.65 | 18.00 |
| ACO clásico | Salida A bloqueada | G404 | 10.00 | 16.83 | 4.72 | 18.00 |
| ACO clásico | Salida A bloqueada | G405 | 10.00 | 16.83 | 5.51 | 18.00 |
| ACO clásico | Salida B bloqueada | H-PB-OFICINAS_CC | 100.00 | 0.00 | 14.12 | 4.70 |
| ACO clásico | Salida B bloqueada | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 15.12 | 4.97 |
| ACO clásico | Salida B bloqueada | H101 | 10.00 | 17.96 | 4.68 | 13.67 |
| ACO clásico | Salida B bloqueada | H102 | 10.00 | 17.96 | 5.54 | 13.67 |
| ACO clásico | Salida B bloqueada | H103 | 10.00 | 17.96 | 7.25 | 13.67 |
| ACO clásico | Salida B bloqueada | H104 | 10.00 | 17.96 | 4.99 | 13.67 |
| ACO clásico | Salida B bloqueada | H105 | 10.00 | 17.96 | 4.75 | 13.67 |
| ACO clásico | Salida B bloqueada | H201 | 16.67 | 20.04 | 4.90 | 15.80 |
| ACO clásico | Salida B bloqueada | H202 | 16.67 | 20.04 | 5.01 | 15.80 |
| ACO clásico | Salida B bloqueada | H203 | 16.67 | 20.04 | 5.13 | 15.80 |
| ACO clásico | Salida B bloqueada | H204 | 16.67 | 20.04 | 5.06 | 15.80 |
| ACO clásico | Salida B bloqueada | H205 | 16.67 | 20.04 | 4.96 | 15.80 |
| ACO clásico | Salida B bloqueada | H301 | 6.67 | 17.53 | 4.79 | 23.50 |
| ACO clásico | Salida B bloqueada | H302 | 6.67 | 17.53 | 4.77 | 23.50 |
| ACO clásico | Salida B bloqueada | H303 | 6.67 | 17.53 | 4.73 | 23.50 |
| ACO clásico | Salida B bloqueada | H304 | 6.67 | 17.53 | 4.76 | 23.50 |
| ACO clásico | Salida B bloqueada | H305 | 6.67 | 17.53 | 4.70 | 23.50 |
| ACO clásico | Salida B bloqueada | H401 | 16.67 | 4.41 | 4.81 | 11.60 |
| ACO clásico | Salida B bloqueada | H402 | 16.67 | 4.41 | 4.82 | 11.60 |
| ACO clásico | Salida B bloqueada | H403 | 16.67 | 4.41 | 4.96 | 11.60 |
| ACO clásico | Salida B bloqueada | H404 | 16.67 | 4.41 | 5.01 | 11.60 |
| ACO clásico | Salida B bloqueada | H405 | 16.67 | 4.41 | 4.90 | 11.60 |
| ACO clásico | Salida B bloqueada | G101 | 3.33 | 27.59 | 4.61 | 18.00 |
| ACO clásico | Salida B bloqueada | G102 | 3.33 | 27.59 | 4.65 | 18.00 |
| ACO clásico | Salida B bloqueada | G103 | 3.33 | 27.59 | 4.72 | 18.00 |
| ACO clásico | Salida B bloqueada | G104 | 3.33 | 27.59 | 4.59 | 18.00 |
| ACO clásico | Salida B bloqueada | G105 | 3.33 | 27.59 | 4.54 | 18.00 |
| ACO clásico | Salida B bloqueada | G201 | 6.67 | 12.33 | 4.74 | 21.00 |
| ACO clásico | Salida B bloqueada | G202 | 6.67 | 12.33 | 4.87 | 21.00 |
| ACO clásico | Salida B bloqueada | G203 | 6.67 | 12.33 | 6.96 | 21.00 |
| ACO clásico | Salida B bloqueada | G204 | 6.67 | 12.33 | 4.87 | 21.00 |
| ACO clásico | Salida B bloqueada | G205 | 6.67 | 12.33 | 4.85 | 21.00 |
| ACO clásico | Salida B bloqueada | G301 | 0.00 | - | 4.59 | - |
| ACO clásico | Salida B bloqueada | G302 | 0.00 | - | 4.44 | - |
| ACO clásico | Salida B bloqueada | G303 | 0.00 | - | 4.74 | - |
| ACO clásico | Salida B bloqueada | G304 | 0.00 | - | 5.16 | - |
| ACO clásico | Salida B bloqueada | G305 | 0.00 | - | 5.91 | - |
| ACO clásico | Salida B bloqueada | G401 | 13.33 | 5.46 | 6.00 | 14.00 |
| ACO clásico | Salida B bloqueada | G402 | 13.33 | 5.46 | 4.63 | 14.00 |
| ACO clásico | Salida B bloqueada | G403 | 13.33 | 5.46 | 6.04 | 14.00 |
| ACO clásico | Salida B bloqueada | G404 | 13.33 | 5.46 | 6.99 | 14.00 |
| ACO clásico | Salida B bloqueada | G405 | 13.33 | 5.46 | 5.34 | 14.00 |
| ACO clásico | Congestión en una salida | H-PB-OFICINAS_CC | 100.00 | 0.00 | 12.12 | 1.70 |
| ACO clásico | Congestión en una salida | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 13.01 | 1.77 |
| ACO clásico | Congestión en una salida | H101 | 26.67 | 0.00 | 5.39 | 16.38 |
| ACO clásico | Congestión en una salida | H102 | 26.67 | 0.00 | 5.53 | 16.38 |
| ACO clásico | Congestión en una salida | H103 | 26.67 | 0.00 | 5.49 | 16.38 |
| ACO clásico | Congestión en una salida | H104 | 26.67 | 0.00 | 6.38 | 16.38 |
| ACO clásico | Congestión en una salida | H105 | 26.67 | 0.00 | 6.54 | 16.38 |
| ACO clásico | Congestión en una salida | H201 | 16.67 | 49.39 | 7.02 | 12.80 |
| ACO clásico | Congestión en una salida | H202 | 16.67 | 49.39 | 5.28 | 12.80 |
| ACO clásico | Congestión en una salida | H203 | 16.67 | 49.39 | 4.88 | 12.80 |
| ACO clásico | Congestión en una salida | H204 | 16.67 | 49.39 | 5.12 | 12.80 |
| ACO clásico | Congestión en una salida | H205 | 16.67 | 49.39 | 4.85 | 12.80 |
| ACO clásico | Congestión en una salida | H301 | 16.67 | 16.98 | 4.87 | 13.20 |
| ACO clásico | Congestión en una salida | H302 | 16.67 | 16.98 | 4.86 | 13.20 |
| ACO clásico | Congestión en una salida | H303 | 16.67 | 16.98 | 4.82 | 13.20 |
| ACO clásico | Congestión en una salida | H304 | 16.67 | 16.98 | 5.49 | 13.20 |
| ACO clásico | Congestión en una salida | H305 | 16.67 | 16.98 | 7.01 | 13.20 |
| ACO clásico | Congestión en una salida | H401 | 20.00 | 18.29 | 5.79 | 20.17 |
| ACO clásico | Congestión en una salida | H402 | 20.00 | 18.29 | 5.46 | 20.17 |
| ACO clásico | Congestión en una salida | H403 | 20.00 | 18.29 | 5.86 | 20.17 |
| ACO clásico | Congestión en una salida | H404 | 20.00 | 18.29 | 5.35 | 20.17 |
| ACO clásico | Congestión en una salida | H405 | 20.00 | 18.29 | 6.03 | 20.17 |
| ACO clásico | Congestión en una salida | G101 | 16.67 | 0.00 | 6.94 | 14.40 |
| ACO clásico | Congestión en una salida | G102 | 16.67 | 0.00 | 6.26 | 14.40 |
| ACO clásico | Congestión en una salida | G103 | 16.67 | 0.00 | 6.98 | 14.40 |
| ACO clásico | Congestión en una salida | G104 | 16.67 | 0.00 | 5.85 | 14.40 |
| ACO clásico | Congestión en una salida | G105 | 16.67 | 0.00 | 6.52 | 14.40 |
| ACO clásico | Congestión en una salida | G201 | 13.33 | 11.33 | 5.18 | 10.00 |
| ACO clásico | Congestión en una salida | G202 | 13.33 | 11.33 | 4.84 | 10.00 |
| ACO clásico | Congestión en una salida | G203 | 13.33 | 11.33 | 4.77 | 10.00 |
| ACO clásico | Congestión en una salida | G204 | 13.33 | 11.33 | 4.63 | 10.00 |
| ACO clásico | Congestión en una salida | G205 | 13.33 | 11.33 | 5.85 | 10.00 |
| ACO clásico | Congestión en una salida | G301 | 10.00 | 27.97 | 5.45 | 14.67 |
| ACO clásico | Congestión en una salida | G302 | 10.00 | 27.97 | 4.85 | 14.67 |
| ACO clásico | Congestión en una salida | G303 | 10.00 | 27.97 | 4.92 | 14.67 |
| ACO clásico | Congestión en una salida | G304 | 10.00 | 27.97 | 4.82 | 14.67 |
| ACO clásico | Congestión en una salida | G305 | 10.00 | 27.97 | 4.87 | 14.67 |
| ACO clásico | Congestión en una salida | G401 | 10.00 | 27.77 | 5.41 | 17.67 |
| ACO clásico | Congestión en una salida | G402 | 10.00 | 27.77 | 5.72 | 17.67 |
| ACO clásico | Congestión en una salida | G403 | 10.00 | 27.77 | 5.37 | 17.67 |
| ACO clásico | Congestión en una salida | G404 | 10.00 | 27.77 | 5.21 | 17.67 |
| ACO clásico | Congestión en una salida | G405 | 10.00 | 27.77 | 4.97 | 17.67 |
| ACO guiado | Normal | H-PB-OFICINAS_CC | 100.00 | 0.00 | 15.32 | 1.03 |
| ACO guiado | Normal | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 15.18 | 1.03 |
| ACO guiado | Normal | H101 | 100.00 | 0.00 | 19.06 | 1.17 |
| ACO guiado | Normal | H102 | 100.00 | 0.00 | 19.64 | 1.17 |
| ACO guiado | Normal | H103 | 100.00 | 0.00 | 20.22 | 1.17 |
| ACO guiado | Normal | H104 | 100.00 | 0.00 | 21.08 | 1.17 |
| ACO guiado | Normal | H105 | 100.00 | 0.00 | 20.26 | 1.17 |
| ACO guiado | Normal | H201 | 100.00 | 0.00 | 24.04 | 1.37 |
| ACO guiado | Normal | H202 | 100.00 | 0.00 | 24.61 | 1.37 |
| ACO guiado | Normal | H203 | 100.00 | 0.00 | 23.00 | 1.37 |
| ACO guiado | Normal | H204 | 100.00 | 0.00 | 22.16 | 1.37 |
| ACO guiado | Normal | H205 | 100.00 | 0.00 | 22.70 | 1.37 |
| ACO guiado | Normal | H301 | 100.00 | 0.00 | 27.30 | 1.70 |
| ACO guiado | Normal | H302 | 100.00 | 0.00 | 26.20 | 1.70 |
| ACO guiado | Normal | H303 | 100.00 | 0.00 | 27.06 | 1.70 |
| ACO guiado | Normal | H304 | 100.00 | 0.00 | 26.24 | 1.70 |
| ACO guiado | Normal | H305 | 100.00 | 0.00 | 27.07 | 1.70 |
| ACO guiado | Normal | H401 | 100.00 | 0.00 | 30.27 | 1.57 |
| ACO guiado | Normal | H402 | 100.00 | 0.00 | 26.02 | 1.57 |
| ACO guiado | Normal | H403 | 100.00 | 0.00 | 26.10 | 1.57 |
| ACO guiado | Normal | H404 | 100.00 | 0.00 | 30.64 | 1.57 |
| ACO guiado | Normal | H405 | 100.00 | 0.00 | 25.66 | 1.57 |
| ACO guiado | Normal | G101 | 100.00 | 0.00 | 20.60 | 1.17 |
| ACO guiado | Normal | G102 | 100.00 | 0.00 | 19.81 | 1.17 |
| ACO guiado | Normal | G103 | 100.00 | 0.00 | 22.29 | 1.17 |
| ACO guiado | Normal | G104 | 100.00 | 0.00 | 19.08 | 1.17 |
| ACO guiado | Normal | G105 | 100.00 | 0.00 | 19.42 | 1.17 |
| ACO guiado | Normal | G201 | 100.00 | 0.00 | 22.76 | 1.37 |
| ACO guiado | Normal | G202 | 100.00 | 0.00 | 23.62 | 1.37 |
| ACO guiado | Normal | G203 | 100.00 | 0.00 | 22.98 | 1.37 |
| ACO guiado | Normal | G204 | 100.00 | 0.00 | 22.87 | 1.37 |
| ACO guiado | Normal | G205 | 100.00 | 0.00 | 25.25 | 1.37 |
| ACO guiado | Normal | G301 | 100.00 | 0.00 | 26.18 | 1.70 |
| ACO guiado | Normal | G302 | 100.00 | 0.00 | 27.67 | 1.70 |
| ACO guiado | Normal | G303 | 100.00 | 0.00 | 27.98 | 1.70 |
| ACO guiado | Normal | G304 | 100.00 | 0.00 | 27.25 | 1.70 |
| ACO guiado | Normal | G305 | 100.00 | 0.00 | 29.08 | 1.70 |
| ACO guiado | Normal | G401 | 100.00 | 0.00 | 27.18 | 1.57 |
| ACO guiado | Normal | G402 | 100.00 | 0.00 | 27.34 | 1.57 |
| ACO guiado | Normal | G403 | 100.00 | 0.00 | 25.59 | 1.57 |
| ACO guiado | Normal | G404 | 100.00 | 0.00 | 26.81 | 1.57 |
| ACO guiado | Normal | G405 | 100.00 | 0.00 | 26.48 | 1.57 |
| ACO guiado | Gradas norte bloqueadas | H-PB-OFICINAS_CC | 100.00 | 0.00 | 10.77 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 11.50 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H101 | 100.00 | 0.00 | 14.37 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H102 | 100.00 | 0.00 | 12.89 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H103 | 100.00 | 0.00 | 16.51 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H104 | 100.00 | 0.00 | 12.56 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H105 | 100.00 | 0.00 | 14.72 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H201 | 100.00 | 0.00 | 14.31 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H202 | 100.00 | 0.00 | 16.44 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H203 | 100.00 | 0.00 | 16.10 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H204 | 100.00 | 0.00 | 14.97 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H205 | 100.00 | 0.00 | 14.74 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H301 | 100.00 | 0.00 | 15.43 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H302 | 100.00 | 0.00 | 15.09 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H303 | 100.00 | 0.00 | 15.19 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H304 | 100.00 | 0.00 | 15.33 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H305 | 100.00 | 0.00 | 15.26 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H401 | 100.00 | 0.00 | 16.97 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H402 | 100.00 | 0.00 | 16.59 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H403 | 100.00 | 0.00 | 16.68 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H404 | 100.00 | 0.00 | 16.72 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | H405 | 100.00 | 0.00 | 17.17 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G101 | 100.00 | 0.00 | 12.44 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G102 | 100.00 | 0.00 | 12.63 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G103 | 100.00 | 0.00 | 12.36 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G104 | 100.00 | 0.00 | 13.00 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G105 | 100.00 | 0.00 | 14.63 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G201 | 100.00 | 0.00 | 13.54 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G202 | 100.00 | 0.00 | 14.35 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G203 | 100.00 | 0.00 | 14.93 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G204 | 100.00 | 0.00 | 15.25 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G205 | 100.00 | 0.00 | 14.56 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G301 | 100.00 | 0.00 | 15.84 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G302 | 100.00 | 0.00 | 17.17 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G303 | 100.00 | 0.00 | 16.59 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G304 | 100.00 | 0.00 | 16.84 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G305 | 100.00 | 0.00 | 16.34 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G401 | 100.00 | 0.00 | 18.69 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G402 | 100.00 | 0.00 | 16.85 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G403 | 100.00 | 0.00 | 16.73 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G404 | 100.00 | 0.00 | 16.76 | 1.00 |
| ACO guiado | Gradas norte bloqueadas | G405 | 100.00 | 0.00 | 16.79 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H-PB-OFICINAS_CC | 100.00 | 0.00 | 8.95 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 8.99 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H101 | 100.00 | 0.00 | 10.63 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H102 | 100.00 | 0.00 | 11.35 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H103 | 100.00 | 0.00 | 13.66 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H104 | 100.00 | 0.00 | 11.48 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H105 | 100.00 | 0.00 | 10.52 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H201 | 100.00 | 0.00 | 12.18 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H202 | 100.00 | 0.00 | 12.52 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H203 | 100.00 | 0.00 | 12.12 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H204 | 100.00 | 0.00 | 14.38 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H205 | 100.00 | 0.00 | 12.28 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H301 | 100.00 | 0.00 | 13.75 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H302 | 100.00 | 0.00 | 14.36 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H303 | 100.00 | 0.00 | 14.26 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H304 | 100.00 | 0.00 | 14.03 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H305 | 100.00 | 0.00 | 15.25 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H401 | 100.00 | 0.00 | 18.18 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H402 | 100.00 | 0.00 | 19.40 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H403 | 100.00 | 0.00 | 15.50 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H404 | 100.00 | 0.00 | 15.00 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | H405 | 100.00 | 0.00 | 15.53 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G101 | 100.00 | 0.00 | 10.51 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G102 | 100.00 | 0.00 | 10.42 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G103 | 100.00 | 0.00 | 10.45 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G104 | 100.00 | 0.00 | 10.38 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G105 | 100.00 | 0.00 | 10.38 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G201 | 100.00 | 0.00 | 12.48 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G202 | 100.00 | 0.00 | 12.89 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G203 | 100.00 | 0.00 | 14.77 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G204 | 100.00 | 0.00 | 12.10 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G205 | 100.00 | 0.00 | 12.01 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G301 | 100.00 | 0.00 | 14.43 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G302 | 100.00 | 0.00 | 14.73 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G303 | 100.00 | 0.00 | 14.68 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G304 | 100.00 | 0.00 | 13.36 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G305 | 100.00 | 0.00 | 14.43 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G401 | 100.00 | 0.00 | 17.73 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G402 | 100.00 | 0.00 | 15.80 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G403 | 100.00 | 0.00 | 15.71 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G404 | 100.00 | 0.00 | 16.02 | 1.00 |
| ACO guiado | Gradas sur bloqueadas | G405 | 100.00 | 0.00 | 16.25 | 1.00 |
| ACO guiado | Salida A bloqueada | H-PB-OFICINAS_CC | 100.00 | 0.00 | 14.87 | 1.00 |
| ACO guiado | Salida A bloqueada | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 16.45 | 1.00 |
| ACO guiado | Salida A bloqueada | H101 | 100.00 | 0.00 | 21.57 | 1.00 |
| ACO guiado | Salida A bloqueada | H102 | 100.00 | 0.00 | 20.88 | 1.00 |
| ACO guiado | Salida A bloqueada | H103 | 100.00 | 0.00 | 19.62 | 1.00 |
| ACO guiado | Salida A bloqueada | H104 | 100.00 | 0.00 | 19.44 | 1.00 |
| ACO guiado | Salida A bloqueada | H105 | 100.00 | 0.00 | 20.70 | 1.00 |
| ACO guiado | Salida A bloqueada | H201 | 100.00 | 0.00 | 24.05 | 1.10 |
| ACO guiado | Salida A bloqueada | H202 | 100.00 | 0.00 | 26.83 | 1.10 |
| ACO guiado | Salida A bloqueada | H203 | 100.00 | 0.00 | 23.96 | 1.10 |
| ACO guiado | Salida A bloqueada | H204 | 100.00 | 0.00 | 23.88 | 1.10 |
| ACO guiado | Salida A bloqueada | H205 | 100.00 | 0.00 | 22.90 | 1.10 |
| ACO guiado | Salida A bloqueada | H301 | 100.00 | 0.00 | 26.89 | 1.23 |
| ACO guiado | Salida A bloqueada | H302 | 100.00 | 0.00 | 26.81 | 1.23 |
| ACO guiado | Salida A bloqueada | H303 | 100.00 | 0.00 | 26.49 | 1.23 |
| ACO guiado | Salida A bloqueada | H304 | 100.00 | 0.00 | 28.40 | 1.23 |
| ACO guiado | Salida A bloqueada | H305 | 100.00 | 0.00 | 27.75 | 1.23 |
| ACO guiado | Salida A bloqueada | H401 | 100.00 | 0.00 | 26.66 | 1.33 |
| ACO guiado | Salida A bloqueada | H402 | 100.00 | 0.00 | 29.98 | 1.33 |
| ACO guiado | Salida A bloqueada | H403 | 100.00 | 0.00 | 27.55 | 1.33 |
| ACO guiado | Salida A bloqueada | H404 | 100.00 | 0.00 | 28.51 | 1.33 |
| ACO guiado | Salida A bloqueada | H405 | 100.00 | 0.00 | 25.05 | 1.33 |
| ACO guiado | Salida A bloqueada | G101 | 100.00 | 0.00 | 21.11 | 1.00 |
| ACO guiado | Salida A bloqueada | G102 | 100.00 | 0.00 | 20.35 | 1.00 |
| ACO guiado | Salida A bloqueada | G103 | 100.00 | 0.00 | 26.10 | 1.00 |
| ACO guiado | Salida A bloqueada | G104 | 100.00 | 0.00 | 24.07 | 1.00 |
| ACO guiado | Salida A bloqueada | G105 | 100.00 | 0.00 | 19.25 | 1.00 |
| ACO guiado | Salida A bloqueada | G201 | 100.00 | 0.00 | 21.85 | 1.10 |
| ACO guiado | Salida A bloqueada | G202 | 100.00 | 0.00 | 22.35 | 1.10 |
| ACO guiado | Salida A bloqueada | G203 | 100.00 | 0.00 | 21.41 | 1.10 |
| ACO guiado | Salida A bloqueada | G204 | 100.00 | 0.00 | 21.80 | 1.10 |
| ACO guiado | Salida A bloqueada | G205 | 100.00 | 0.00 | 22.08 | 1.10 |
| ACO guiado | Salida A bloqueada | G301 | 100.00 | 0.00 | 25.09 | 1.23 |
| ACO guiado | Salida A bloqueada | G302 | 100.00 | 0.00 | 26.18 | 1.23 |
| ACO guiado | Salida A bloqueada | G303 | 100.00 | 0.00 | 27.73 | 1.23 |
| ACO guiado | Salida A bloqueada | G304 | 100.00 | 0.00 | 26.71 | 1.23 |
| ACO guiado | Salida A bloqueada | G305 | 100.00 | 0.00 | 27.60 | 1.23 |
| ACO guiado | Salida A bloqueada | G401 | 100.00 | 0.00 | 31.16 | 1.33 |
| ACO guiado | Salida A bloqueada | G402 | 100.00 | 0.00 | 33.59 | 1.33 |
| ACO guiado | Salida A bloqueada | G403 | 100.00 | 0.00 | 26.14 | 1.33 |
| ACO guiado | Salida A bloqueada | G404 | 100.00 | 0.00 | 27.76 | 1.33 |
| ACO guiado | Salida A bloqueada | G405 | 100.00 | 0.00 | 26.76 | 1.33 |
| ACO guiado | Salida B bloqueada | H-PB-OFICINAS_CC | 100.00 | 0.00 | 20.12 | 1.00 |
| ACO guiado | Salida B bloqueada | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 19.18 | 1.00 |
| ACO guiado | Salida B bloqueada | H101 | 100.00 | 0.00 | 25.17 | 1.07 |
| ACO guiado | Salida B bloqueada | H102 | 100.00 | 0.00 | 25.66 | 1.07 |
| ACO guiado | Salida B bloqueada | H103 | 100.00 | 0.00 | 25.63 | 1.07 |
| ACO guiado | Salida B bloqueada | H104 | 100.00 | 0.00 | 27.29 | 1.07 |
| ACO guiado | Salida B bloqueada | H105 | 100.00 | 0.00 | 27.97 | 1.07 |
| ACO guiado | Salida B bloqueada | H201 | 100.00 | 0.00 | 30.80 | 1.43 |
| ACO guiado | Salida B bloqueada | H202 | 100.00 | 0.00 | 27.69 | 1.43 |
| ACO guiado | Salida B bloqueada | H203 | 100.00 | 0.00 | 34.14 | 1.43 |
| ACO guiado | Salida B bloqueada | H204 | 100.00 | 0.00 | 30.76 | 1.43 |
| ACO guiado | Salida B bloqueada | H205 | 100.00 | 0.00 | 34.22 | 1.43 |
| ACO guiado | Salida B bloqueada | H301 | 100.00 | 0.00 | 34.78 | 2.33 |
| ACO guiado | Salida B bloqueada | H302 | 100.00 | 0.00 | 29.54 | 2.33 |
| ACO guiado | Salida B bloqueada | H303 | 100.00 | 0.00 | 30.48 | 2.33 |
| ACO guiado | Salida B bloqueada | H304 | 100.00 | 0.00 | 34.50 | 2.33 |
| ACO guiado | Salida B bloqueada | H305 | 100.00 | 0.00 | 35.68 | 2.33 |
| ACO guiado | Salida B bloqueada | H401 | 100.00 | 0.00 | 31.57 | 1.97 |
| ACO guiado | Salida B bloqueada | H402 | 100.00 | 0.00 | 31.67 | 1.97 |
| ACO guiado | Salida B bloqueada | H403 | 100.00 | 0.00 | 34.17 | 1.97 |
| ACO guiado | Salida B bloqueada | H404 | 100.00 | 0.00 | 31.37 | 1.97 |
| ACO guiado | Salida B bloqueada | H405 | 100.00 | 0.00 | 30.23 | 1.97 |
| ACO guiado | Salida B bloqueada | G101 | 100.00 | 0.00 | 26.59 | 1.07 |
| ACO guiado | Salida B bloqueada | G102 | 100.00 | 0.00 | 25.48 | 1.07 |
| ACO guiado | Salida B bloqueada | G103 | 100.00 | 0.00 | 27.14 | 1.07 |
| ACO guiado | Salida B bloqueada | G104 | 100.00 | 0.00 | 24.93 | 1.07 |
| ACO guiado | Salida B bloqueada | G105 | 100.00 | 0.00 | 24.81 | 1.07 |
| ACO guiado | Salida B bloqueada | G201 | 100.00 | 0.00 | 32.11 | 1.43 |
| ACO guiado | Salida B bloqueada | G202 | 100.00 | 0.00 | 29.86 | 1.43 |
| ACO guiado | Salida B bloqueada | G203 | 100.00 | 0.00 | 29.71 | 1.43 |
| ACO guiado | Salida B bloqueada | G204 | 100.00 | 0.00 | 32.08 | 1.43 |
| ACO guiado | Salida B bloqueada | G205 | 100.00 | 0.00 | 27.31 | 1.43 |
| ACO guiado | Salida B bloqueada | G301 | 100.00 | 0.00 | 31.15 | 2.33 |
| ACO guiado | Salida B bloqueada | G302 | 100.00 | 0.00 | 30.09 | 2.33 |
| ACO guiado | Salida B bloqueada | G303 | 100.00 | 0.00 | 31.36 | 2.33 |
| ACO guiado | Salida B bloqueada | G304 | 100.00 | 0.00 | 33.37 | 2.33 |
| ACO guiado | Salida B bloqueada | G305 | 100.00 | 0.00 | 31.47 | 2.33 |
| ACO guiado | Salida B bloqueada | G401 | 100.00 | 0.00 | 29.89 | 1.97 |
| ACO guiado | Salida B bloqueada | G402 | 100.00 | 0.00 | 30.38 | 1.97 |
| ACO guiado | Salida B bloqueada | G403 | 100.00 | 0.00 | 30.60 | 1.97 |
| ACO guiado | Salida B bloqueada | G404 | 100.00 | 0.00 | 32.48 | 1.97 |
| ACO guiado | Salida B bloqueada | G405 | 100.00 | 0.00 | 29.74 | 1.97 |
| ACO guiado | Congestión en una salida | H-PB-OFICINAS_CC | 100.00 | 0.00 | 14.45 | 1.00 |
| ACO guiado | Congestión en una salida | G-PB-LAB_BIOTEC | 100.00 | 0.00 | 15.91 | 1.00 |
| ACO guiado | Congestión en una salida | H101 | 100.00 | 0.00 | 19.66 | 1.17 |
| ACO guiado | Congestión en una salida | H102 | 100.00 | 0.00 | 19.01 | 1.17 |
| ACO guiado | Congestión en una salida | H103 | 100.00 | 0.00 | 18.98 | 1.17 |
| ACO guiado | Congestión en una salida | H104 | 100.00 | 0.00 | 18.84 | 1.17 |
| ACO guiado | Congestión en una salida | H105 | 100.00 | 0.00 | 21.18 | 1.17 |
| ACO guiado | Congestión en una salida | H201 | 100.00 | 0.00 | 23.80 | 1.23 |
| ACO guiado | Congestión en una salida | H202 | 100.00 | 0.00 | 22.81 | 1.23 |
| ACO guiado | Congestión en una salida | H203 | 100.00 | 0.00 | 24.07 | 1.23 |
| ACO guiado | Congestión en una salida | H204 | 100.00 | 0.00 | 23.67 | 1.23 |
| ACO guiado | Congestión en una salida | H205 | 100.00 | 0.00 | 25.78 | 1.23 |
| ACO guiado | Congestión en una salida | H301 | 100.00 | 0.00 | 27.98 | 1.67 |
| ACO guiado | Congestión en una salida | H302 | 100.00 | 0.00 | 25.66 | 1.67 |
| ACO guiado | Congestión en una salida | H303 | 100.00 | 0.00 | 26.35 | 1.67 |
| ACO guiado | Congestión en una salida | H304 | 100.00 | 0.00 | 27.40 | 1.67 |
| ACO guiado | Congestión en una salida | H305 | 100.00 | 0.00 | 27.69 | 1.67 |
| ACO guiado | Congestión en una salida | H401 | 100.00 | 0.00 | 26.59 | 1.73 |
| ACO guiado | Congestión en una salida | H402 | 100.00 | 0.00 | 27.89 | 1.73 |
| ACO guiado | Congestión en una salida | H403 | 100.00 | 0.00 | 26.47 | 1.73 |
| ACO guiado | Congestión en una salida | H404 | 100.00 | 0.00 | 26.18 | 1.73 |
| ACO guiado | Congestión en una salida | H405 | 100.00 | 0.00 | 26.50 | 1.73 |
| ACO guiado | Congestión en una salida | G101 | 100.00 | 0.00 | 19.65 | 1.17 |
| ACO guiado | Congestión en una salida | G102 | 100.00 | 0.00 | 21.86 | 1.17 |
| ACO guiado | Congestión en una salida | G103 | 100.00 | 0.00 | 21.73 | 1.17 |
| ACO guiado | Congestión en una salida | G104 | 100.00 | 0.00 | 22.60 | 1.17 |
| ACO guiado | Congestión en una salida | G105 | 100.00 | 0.00 | 19.64 | 1.17 |
| ACO guiado | Congestión en una salida | G201 | 100.00 | 0.00 | 25.02 | 1.23 |
| ACO guiado | Congestión en una salida | G202 | 100.00 | 0.00 | 27.80 | 1.23 |
| ACO guiado | Congestión en una salida | G203 | 100.00 | 0.00 | 23.85 | 1.23 |
| ACO guiado | Congestión en una salida | G204 | 100.00 | 0.00 | 22.40 | 1.23 |
| ACO guiado | Congestión en una salida | G205 | 100.00 | 0.00 | 22.64 | 1.23 |
| ACO guiado | Congestión en una salida | G301 | 100.00 | 0.00 | 28.21 | 1.67 |
| ACO guiado | Congestión en una salida | G302 | 100.00 | 0.00 | 29.87 | 1.67 |
| ACO guiado | Congestión en una salida | G303 | 100.00 | 0.00 | 24.93 | 1.67 |
| ACO guiado | Congestión en una salida | G304 | 100.00 | 0.00 | 24.90 | 1.67 |
| ACO guiado | Congestión en una salida | G305 | 100.00 | 0.00 | 24.85 | 1.67 |
| ACO guiado | Congestión en una salida | G401 | 100.00 | 0.00 | 27.69 | 1.73 |
| ACO guiado | Congestión en una salida | G402 | 100.00 | 0.00 | 25.53 | 1.73 |
| ACO guiado | Congestión en una salida | G403 | 100.00 | 0.00 | 30.49 | 1.73 |
| ACO guiado | Congestión en una salida | G404 | 100.00 | 0.00 | 26.19 | 1.73 |
| ACO guiado | Congestión en una salida | G405 | 100.00 | 0.00 | 27.50 | 1.73 |

## (h) Figuras y animaciones

Todas en `results/`. Figuras PNG a 200 dpi, en español; colores por tipo de nodo (aula, pasillo, gradas, salida, vía exterior, punto de encuentro).

| Archivo | Qué muestra |
|---|---|
| `figuras/fig1_rutas_plano_calibrado.png` | Plano calibrado con la ruta de Dijkstra y las de ACO clásico y ACO guiado desde H-PB-OFICINAS_CC (PB), H203 (piso 2) y H403 (piso 4), escenario Normal |
| `figuras/fig2_mapa_calor_feromonas.png` | Esquema por niveles con la feromona de cada arista en cuatro momentos de una corrida de ACO clásico desde H403 (intensidad relativa a cada cuadro) |
| `figuras/fig3_convergencia.png` | Mejor costo acumulado por iteración (media y desviación sobre 30 corridas) de ambas variantes, con la línea del óptimo de Dijkstra, para tres orígenes |
| `figuras/fig4a_costos_boxplot.png` | Diagrama de cajas de los costos de las rutas por escenario (Dijkstra, ACO clásico, ACO guiado) |
| `figuras/fig4b_tiempos_barras.png` | Tiempo de cómputo por escenario y algoritmo (escala logarítmica) |
| `figuras/fig4c_exito_y_brecha.png` | Tasa de éxito y brecha media frente a Dijkstra por escenario y variante |
| `figuras/fig5_sensibilidad.png` | Sensibilidad de alfa, beta, rho y número de hormigas (ACO clásico): brecha media con banda, tiempo medio y tasa de éxito |
| `figuras/fig5b_diagnostico_q.png` | Diagnóstico complementario: efecto de la constante de depósito Q sobre el éxito y la brecha |
| `figuras/fig6_adaptacion_frio_vs_warm.png` | Adaptación a bloqueos y congestión: ACO en frío contra warm start (iteración de convergencia, tiempo y éxito) |
| `figuras/fig7_evacuacion_acumulada.png` | Llegadas acumuladas al punto de encuentro por escenario, con marcas de la primera y la última persona |
| `figuras/fig7b_personas_por_salida_y_pe.png` | Personas por salida y por punto de encuentro, por escenario y algoritmo |
| `animaciones/aco_feromonas.gif` | Evolución de la feromona y de la mejor ruta, iteración por iteración (ACO clásico desde H403): plano calibrado a la izquierda y esquema por niveles a la derecha |
| `animaciones/evacuacion.gif` | Personas avanzando por las rutas de Dijkstra hacia las salidas y el punto de encuentro sobre el plano calibrado (escenario Normal) |

## (i) Hallazgos principales

1. **ACO guiado iguala a Dijkstra en todo el benchmark.** En 7560 corridas (6 escenarios x 42 orígenes x 30), ACO guiado tuvo 100 % de éxito y brecha de 0.00 %. Converge en la iteración 1.0 a 1.7 en promedio: la poda de callejones, el retroceso y la heurística resuelven el problema casi sin que las feromonas intervengan (ver también la auditoría, variante b).

2. **ACO guiado es unas 264 veces más lento que Dijkstra en este grafo.** Su tiempo medio por búsqueda es de 13.4 a 29.6 ms según el escenario, frente a 0.076 a 0.093 ms de Dijkstra (mediana por origen); el ACO clásico necesita 5.0 a 5.9 ms (unas 66 veces). En un grafo de 75 nodos casi sin ciclos, el óptimo exacto se obtiene de inmediato.

3. **ACO clásico (beta = 2, fijado a priori) rinde mal: éxito de 11.1 % a 21.8 % y brecha media de 5.1 % a 17.1 % sobre las corridas exitosas (máximo 157 %).** Sin poda ni retroceso, las aulas atrapan a las hormigas, y con beta = 2 la visibilidad local favorece justo esas aristas cortas. Es la configuración declarada antes de correr y se reporta tal cual.

4. **En la sensibilidad, beta es el parámetro que más pesa: con beta = 0 el éxito es 99.3 % y la brecha media 1.92 %; con beta = 2 es 34.3 % y 7.57 %.** Alfa y rho no producen cambios en el éxito (alfa: 34.3 % a 34.3 %; rho: 34.3 % a 34.3 %), señal de que con Q = 1 la feromona casi no interviene. Una explicación coherente con los números (no probada de forma independiente): cada hormiga deposita Q/costo, es decir unos 0.004 a 0.006 con costos de 160 a 250, menos que tau_min = 0.01, y la evaporación borra ese rastro en pocas iteraciones. El diagnóstico de Q muestra que la feromona sí empieza a intervenir cuando Q es grande, pero para mal: con beta = 0 la brecha media pasa de 1.92 % (Q = 1) a 16.34 % (Q = 1000) y las corridas óptimas bajan de 92 % a 64 %, mientras el éxito se mantiene en 99.3 %: un depósito grande fija pronto una ruta no óptima. Más hormigas elevan el éxito del clásico (22.3 % con 5 hormigas, 51.3 % con 50) pero también el tiempo (2.3 a 17.2 ms).

5. **El warm start no aporta una ventaja sistemática.** Para ACO guiado reduce el tiempo de cómputo entre -4 % y 24 % según el escenario (más de 15 % solo en Salida A bloqueada, Congestión en una salida), y la iteración de convergencia, que ya es 1.0 a 1.7 en frío, no mejora; en Salida B bloqueada empeora (de 1.67 a 5.04), porque las feromonas del escenario Normal apuntan a la ruta que ahora está bloqueada. Para el clásico, la variación de la iteración de convergencia va de -6.2 % a 4.1 % de reducción y la del tiempo de -10.5 % a 6.0 %, sin cambio en éxito ni brecha. El aporte de ACO frente a bloqueos, por tanto, no se distingue del de una búsqueda en frío.

6. **Solo dos de los cinco escenarios modificados cambian la ruta óptima.** Con gradas norte o Salida B bloqueadas, el costo medio de Dijkstra sube de 199.3 a 245.9 (23 %) y el tiempo de la primera y de la última persona pasa de 194 s y 272 s a 233 s y 311 s, porque todos pasan a la Salida A. Gradas sur bloqueadas, Salida A bloqueada y congestión en la Salida A no alteran nada, porque en el modelo nadie usa esas rutas.

7. **Evacuación completa (1020 personas), escenario Normal, rutas óptimas: la primera persona llega a los 194 s y la última a los 272 s.** 42 de los 42 orígenes salen por la Salida B y llegan a PE-2; con ACO clásico la última persona llega a los 383 s porque algunas rutas son mucho peores. Este reparto es consecuencia de los puntos de encuentro hipotéticos, de la arista entre salidas y de que no hay modelo de colas; no debe leerse como una predicción del campus real.

8. **Prueba de cordura aprobada.** 20077 corridas exitosas verificadas (benchmark, adaptación, sensibilidad y diagnóstico), ninguna con costo menor al de Dijkstra.

## (j) Requisito de la actividad y evidencia

| Requisito de la actividad | Evidencia |
|---|---|
| Guiar a los miembros de la comunidad en los bloques G y H hacia un punto de encuentro | Grafo de 75 nodos con los 42 orígenes de G y H, 2 salidas y 3 puntos de encuentro (`data/campus_graph.json`); rutas en la figura 1 y en la tabla g.7 |
| Aplicar un algoritmo de búsqueda | Dijkstra (`src/dijkstra.py`) y ACO en dos variantes (`src/aco.py`); tablas g.1 a g.6 |
| De preferencia, el agente de búsqueda seleccionado | `AgenteEvacuacion` (percibir, decidir, actuar), basado en metas y utilidad; sección (d); pestaña "Comparación" de la app |
| Informe académico con las pruebas realizadas | Sección (g): benchmark, adaptación, sensibilidad, diagnóstico de Q, evacuación completa y prueba de cordura; pruebas automáticas en `tests/` |
| Conclusiones | Sección (i), hallazgos con números |
| Presentación de 2 minutos por integrante | Se redactará a partir de esta base (figuras y GIF de la sección (h)) |
| Subir dos archivos (informe y presentación) | Pendiente: informe y presentación se elaboran a partir de este documento |
| Animaciones de la ejecución (objetivo del equipo) | `results/animaciones/aco_feromonas.gif` y `evacuacion.gif`; pestaña "Simulación en vivo" de la app |
| Restricciones oficiales (sismo) | Sección (b), con documento y página |
