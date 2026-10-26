# src/

Codigo del modelo de busqueda y del agente de evacuacion (Fase 2).

- `grafo.py`: carga de `data/campus_graph.json` y de los archivos de config; clase `Grafo` (adyacencia no dirigida).
- `costos.py`: funcion de costo y tiempo de una arista (unica, usada por todos los algoritmos).
- `dijkstra.py`: Dijkstra multi-objetivo (origen -> cualquier punto de encuentro).
- `aco.py`: Optimizacion por Colonia de Hormigas (variante MAX-MIN).
- `agente.py`: `AgenteEvacuacion` (percibir -> decidir -> actuar). Ver `docs/agente_peas.md`.
- `metricas.py`: tiempos de primera/ultima persona por origen, y brecha ACO vs. Dijkstra.
