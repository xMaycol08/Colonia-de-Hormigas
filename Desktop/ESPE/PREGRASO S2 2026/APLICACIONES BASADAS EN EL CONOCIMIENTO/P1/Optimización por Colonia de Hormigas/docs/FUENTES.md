# Bitácora de fuentes

Registro de todas las fuentes de datos usadas o consideradas para el modelo de
evacuacion. Toda fuente nueva (visita de campo, foto, enlace) debe agregarse
aqui con su fecha.

| Fecha | Fuente | Tipo | Que dato aporta | Confiabilidad (`confidence`) |
|-------|--------|------|-------------------|-------------------------------|
| 2019-05-14 | Protocolo de actuacion ante sismos (USIN-PRT-v1-2019-001), Unidad de Seguridad Integrada ESPE | documento_oficial | Reglas de comportamiento ante sismo, criterios para elegir via de evacuacion (campo abierto, lejos de edificaciones/corredores cubiertos/arboles/postes/cables), que hacer en el punto de encuentro | documento_oficial |
| 2019-09-25 | Guia para ejecucion de simulacros (USIN-GS-v1-2019-013) y sus anexos (formatos de planificacion, guion, verificacion de evaluador y evaluacion de observador), Unidad de Seguridad Integrada ESPE | documento_oficial | Confirma 14 puntos de encuentro en campus Matriz; metricas oficiales de tiempo (llegada de primera y ultima persona al punto de encuentro); rol de evaluadores por punto de encuentro | documento_oficial |
| 2026-10-25 | Captura de pantalla de Google Maps, busqueda "University of the Armed Forces ESPE" | medido_en_maps | Ubicacion general del campus Matriz (pin, direccion Av. Gral. Rumiñahui S/N, Sangolqui) y coordenadas aproximadas del centroide del campus; NO ubica bloques G/H ni puntos de encuentro | medido_en_maps |
| (pendiente) | Blog no oficial "Cuerpitos ESPE" (bloques C-D-H-G) | blog_no_oficial | Posible referencia informal sobre ubicacion/distribucion de los bloques C, D, H, G; debe contrastarse en campo antes de usarse como dato del grafo | blog_no_oficial |
| (pendiente) | Ficha de trabajo de campo - bloque G (`data/campo/`) | verificado_en_campo | Pisos, aulas, escaleras, salidas, riesgos, senaletica y fotos del bloque G | verificado_en_campo |
| (pendiente) | Ficha de trabajo de campo - bloque H (`data/campo/`) | verificado_en_campo | Pisos, aulas, escaleras, salidas, riesgos, senaletica y fotos del bloque H | verificado_en_campo |

## Notas sobre el blog no oficial "Cuerpitos ESPE"

- Es una fuente no institucional; cualquier dato tomado de ahi debe marcarse
  siempre con `confidence: "blog_no_oficial"` en el grafo y debe contrastarse
  en campo antes de subir su nivel de confianza.
- Pendiente: registrar aqui la URL exacta y la fecha de consulta cuando se
  revise, y anotar especificamente que dato (si alguno) aporta sobre los
  bloques G y H.
