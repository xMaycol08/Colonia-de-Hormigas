# Auditoría de ACO - Fase 1-bis (Tarea G)

Auditoría pedida antes de los experimentos finales, corrida sobre el grafo
**nuevo** (complejo G/H/C/D, 2 secciones de gradas, 2 salidas,
`data/campus_graph.json` reconstruido en esta misma fase). Script usado:
`scripts/auditoria_variantes.py` (de un solo uso, no se integra a `src/`).

## G.1 - ¿ACO usa Dijkstra?

Comando y resultado exactos:

```
$ grep -n -i "dijkstra" src/aco.py
$ echo $?
1
```

`grep` no encontró ninguna coincidencia (código de salida 1 = "no match") en
todo `src/aco.py`. Los únicos imports del archivo son:

```
from costos import costo_arista
from grafo import Grafo
```

**Confirmado: `src/aco.py` no importa ni llama a `src/dijkstra.py` de ninguna
forma.** Cuando `src/metricas.py` o `src/benchmark.py` calculan una "brecha %",
llaman a `dijkstra.buscar_ruta()` y a `aco.ejecutar_aco()` por separado, cada
uno sobre el mismo grafo, y comparan los dos resultados ya calculados; ACO en
ningún momento consulta el resultado de Dijkstra para construir su camino.

## G.2 y G.3 - ¿Por qué la malla anterior dio 100% de éxito y 0.00% de brecha en todas las combinaciones? ¿Sigue pasando con el grafo nuevo?

### Conteo de rutas simples (tope 5000), 5 orígenes de H

| Origen | Rutas simples hacia algún PE |
|---|---|
| H-PB-OFICINAS_CC | 30 |
| H101 | 48 |
| H201 | 72 |
| H301 | 96 |
| H401 | 96 |

Son cifras **pequeñas y manejables** (no miles ni millones): el grafo nuevo
(75 nodos, 79 aristas) es casi un árbol, con solo 5 ciclos independientes
(79 − 75 + 1 = 5), originados por la simetría gradas-norte/gradas-sur que
conecta el pasillo central de un nivel con el del nivel siguiente por dos
caminos distintos. Esto ya es una pista de por qué el problema es fácil para
ACO: hay pocas alternativas reales entre las que elegir.

### Las 3 variantes, 5 orígenes, 20 corridas cada una

| Variante | H-PB-OFICINAS_CC | H101 | H201 | H301 | H401 |
|---|---|---|---|---|---|
| **(a) Actual** (poda + retroceso + heurística, β=1.0) | 100% éxito, 0.00% brecha | 100%, 0.00% | 100%, 0.00% | 100%, 0.00% | 100%, 0.00% |
| **(b) Sin heurística** (β=0, con poda + retroceso) | 100%, 0.00% | 100%, 0.00% | 100%, 0.00% | 100%, 0.00% | 100%, 0.00% |
| **(c) Sin heurística y tabú original** (β=0, sin poda, sin retroceso) | 100%, 0.00% | 100%, 0.00% | 100%, 0.00% | **100%, 7.54%** | **100%, 5.80%** |

(Tiempos: todas las variantes entre 15 y 60 ms por corrida; sin diferencias
relevantes para esta pregunta.)

### Conclusión (respuesta directa a lo pedido)

**Sí, la brecha vuelve a ser 0.00% en las variantes (a) y (b) con el grafo
nuevo.** La poda de callejones por sí sola (sin heurística, variante b) ya
alcanza el óptimo de Dijkstra en el 100% de las corridas: el problema es
**trivial para ACO en este grafo** una vez que se eliminan las aulas como
callejones sin salida, porque el resultado es un grafo casi-árbol, pequeño
y con pocas rutas simples reales (30-96). En esas condiciones, la feromona
casi no tiene nada que "aprender" — cualquier búsqueda razonable converge al
óptimo casi de inmediato (de hecho, en todas las corridas de (a) y (b) la
convergencia fue en la iteración 1, igual que con la malla de 2700 corridas
del modelo anterior).

**La heurística guiada (tipo A*) NO es la que resuelve el problema por sí
sola**: la variante (b), que la quita por completo (β=0) pero conserva la
poda y el retroceso, sigue dando 0.00% de brecha. Es decir: **la poda de
callejones es la corrección que más pesa**; la heurística ayuda a que ACO
converja más rápido en grafos más grandes (como el de Fase 2, 158 nodos),
pero en este grafo reconstruido (75 nodos) ya no hace falta para llegar al
óptimo.

**Dónde sí importan los parámetros:** solo en la variante (c) — sin
heurística y con el mecanismo de tabú original (sin poda, sin retroceso) —
aparece una brecha real y distinta de cero (7.54% y 5.80% en los orígenes
más lejanos, H301 y H401). Ahí sí hay margen para que alfa, beta, rho y
n_hormigas cambien el resultado, porque el algoritmo ya no converge
trivialmente al óptimo en cada corrida.

**Recomendación para la Fase de experimentos (análisis de sensibilidad):**
usar la **variante (c)** — "ACO clásico": sin heurística guiada (beta se
varía libremente dentro de la malla de sensibilidad, partiendo de la idea
de que su efecto es distinto al de la variante con heurística) y sin poda
ni retroceso — como la configuración para el experimento de sensibilidad de
`scripts/correr_experimentos.py` (Fase 3/4), ya que es la única donde
alfa/beta/rho/n_hormigas tienen un efecto medible sobre la brecha. Usar la
variante (a) (la de producción, en `src/aco.py`) para el resto de
experimentos (benchmark principal, adaptación, evacuación completa), porque
es la que de verdad usará la app y el agente.

## G.4 - Resultados anteriores en `results/`

| Archivo | Por qué no sirve |
|---|---|
| `malla_aco_20261025_175117.csv` | Malla de 2700 corridas sobre el grafo **viejo** (8 escaleras por bloque, 6 aulas por piso, 1 salida por bloque) |
| `benchmark_20261025_180533.csv` | Benchmark de prueba de la app sobre el grafo viejo |
| `benchmark_20261025_215818.csv` | Benchmark de prueba de la app sobre el grafo viejo |
| `captura_20261025_181257.png` | Captura de la app mostrando el grafo viejo |

**Confirmado: ninguno de estos 4 archivos se usará en el informe final.**
Se generaron todos con el modelo incorrecto (anterior a la reconstrucción
de Fase 1-bis) y quedan pendientes de borrar en la limpieza final (Fase 3+4
de este proyecto, tarea de limpieza, Parte 4).

## G.5 - Procesos corriendo

Verificado con PowerShell (`Get-Process python,streamlit`): **no hay ningún
proceso de Python ni de Streamlit corriendo** al cierre de esta fase. El
servidor de Streamlit que se había quedado abierto en una sesión anterior
(puerto 8768) ya se había detenido antes de empezar esta tarea.
