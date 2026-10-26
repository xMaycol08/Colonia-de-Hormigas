# Restricciones oficiales para el modelo de evacuación (Fase 0)

Este documento resume **únicamente** lo que dicen los documentos oficiales de ESPE
disponibles en `docs/` y que afecta directamente al modelo de evacuación (grafo,
reglas de movimiento, puntos de encuentro, métricas). Cada afirmación cita el
documento y la página exacta. No se agrega ningún dato que los documentos no
contengan explícitamente.

Fuentes usadas:

- **Protocolo de actuación ante sismos**, código de documento `USIN-PRT-v1-2019-001`,
  código de proceso `ASI.2.1.001`, fecha 14-MAY-2019 (en adelante "Protocolo").
- **Guía para ejecución de simulacros**, código de documento `USIN-GS-v1-2019-013`,
  código de proceso `ASI.1.013`, fecha 25-sep-2019 (en adelante "Guía").
- Captura de pantalla de Google Maps del campus matriz ESPE Sangolquí
  (`data/maps/captura_google_maps_campus_matriz.png`).

## 1. Cuándo evacuar

- "Tan pronto la tierra deje de moverse, abandone su espacio vital y proceda a
  evacuar." (Protocolo, pág. 2, sección B "Después del sismo", punto 1).
- "Si se encuentra en la planta baja de una instalación y si la magnitud del sismo
  lo permite, evacue de inmediato sin esperar a que pase el sismo; pero si el
  movimiento es muy fuerte que no le permite salir; entonces ubíquese en su
  espacio vital adoptando la posición fetal." (Protocolo, pág. 2, punto 5).
- "Si se encuentra en alguno de los pisos altos de una edificación 'no' intente
  evacuar el inmueble durante el sismo." (Protocolo, pág. 1, "Durante el sismo",
  punto 2).

## 2. Hacia dónde dirigirse / qué evitar

- "Identifique la vía de evacuación que utilizará para llegar al punto de
  encuentro más cercano (en lo posible el desplazamiento debe ser a campo
  abierto, alejado de edificaciones, corredores cubiertos, árboles, postes,
  cables de energía eléctrica, etc.; que pueden caer por efecto del sismo)."
  (Protocolo, pág. 1, "Antes de que se produzca un sismo", punto 4).
- "Si está en la parte exterior de las instalaciones, aléjese de árboles,
  edificaciones, postes, cables de energía eléctrica y otros elementos que
  puedan caer; y diríjase hasta el punto de encuentro más cercano." (Protocolo,
  pág. 2, punto 6).
- "Diríjase por la vía de evacuación previamente seleccionada hacia el punto de
  encuentro." (Protocolo, pág. 2, punto 2).

## 3. Comportamiento durante la evacuación

- "Durante el desplazamiento de evacuación No corra, No grite y No empuje."
  (Protocolo, pág. 2, punto 3).
- "Mantenga la calma." (Protocolo, pág. 1, "Durante el sismo", punto 1).
- "Protéjase la cabeza con brazos y manos." (Protocolo, pág. 2, punto 4).
- En vehículos: "reduzca la velocidad, prenda las luces intermitentes y estacione
  el vehículo en un sitio seguro, nunca debajo de cables de energía eléctrica o
  cubiertas; no obstruya rampas de acceso de personas con discapacidad y
  señalética de seguridad." (Protocolo, pág. 2, punto 7). (No aplica directamente
  a peatones del grafo de evacuación, pero confirma que las rampas de
  discapacidad y la señalética no deben bloquearse).

## 4. Puntos de encuentro

- "En el punto de encuentro, verifique que su grupo de trabajo o estudio esté
  completo; y espere disposiciones de las autoridades de la institución."
  (Protocolo, pág. 2, punto 4).
- "En el campus Matriz se tiene definidos y señalados **14 puntos de encuentro**,
  por lo cual; como mínimo se debe tener 14 evaluadores del simulacro." (Guía,
  pág. 3, sección C.2.d).
- "Una vez que los miembros de la comunidad universitaria han evacuado y se han
  concentrado en los Puntos de Encuentro; es el evaluador quien les reúne y
  conduce una crítica puntual y constructiva." (Guía, pág. 7, sección F.1).
- "Si el simulacro es relacionado a sismos, deberá solicitar a los miembros de la
  comunidad universitaria que se encuentran en el Punto de Encuentro, que
  permanezcan reunidos hasta recibir disposiciones por parte de la máxima
  autoridad del campus." (Guía, pág. 7, sección F.1).
- El "Formato de verificación para evaluador de simulacro" (anexo de la Guía)
  confirma que el evaluador registra, por punto de encuentro: hora de inicio del
  simulacro, si hubo "organización" en el punto de encuentro, y si se "controló
  el ingreso y/o reingreso de personas a la institución durante la evacuación"
  (Guía, anexo "Formato de verificación para evaluador de simulacro",
  `USIN-FOR-v1-2019-012`, págs. 1-2).

## 5. Métricas oficiales de tiempo

El "Formato de verificación para evaluador de simulacro" (anexo de la Guía,
`USIN-FOR-v1-2019-012`, pág. 2, cuadro "Control de tiempos") define explícitamente
estos hitos de tiempo que deben registrarse por punto de encuentro:

- Activación de la alerta.
- Reacción y ubicación en el espacio vital (triángulo de vida).
- Salida de la primera persona (evacuación).
- Salida de la última persona (evacuación).
- **Llegada de la primera persona al punto de encuentro.**
- **Llegada de la última persona al punto de encuentro.**
- Crítica en el punto de encuentro.
- Retorno a las instalaciones.

Adicionalmente, el "Formato de evaluación para observador de simulacro"
(`USIN-FOR-v1-2019-011`, pág. 1) pide registrar:

- "Tiempo desde la emisión de la alerta, hasta la salida de la primera persona
  como parte de la evacuación."
- "Tiempo desde la emisión de la alerta, hasta la evacuación total del piso,
  edificio, área o lugar asignado."
- "Tiempo desde la emisión de la alerta, hasta la llegada de la última persona al
  punto de encuentro."

Y la sección de evaluación de la Guía (pág. 7, sección F.1) pide comparar:

- "Tiempo transcurrido desde la emisión de la alerta hasta que ha llegado la
  primera persona al punto de encuentro."
- "Tiempo transcurrido desde la emisión de la alerta hasta que ha llegado la
  última persona al punto de encuentro."
- "Comparación del tiempo utilizado en el presente ejercicio con el empleado en
  el anterior simulacro."

Estas son, por tanto, las métricas oficiales que el modelo de evacuación (y la
futura comparación ACO vs. Dijkstra) debería poder reproducir o aproximar: tiempo
de la primera persona en llegar al punto de encuentro y tiempo de la última
persona en llegar al punto de encuentro, medidos desde la emisión de la alerta.

## 6. Organización institucional del simulacro (contexto, no geometría)

- Debe existir, como mínimo, un evaluador por cada punto de encuentro (14 en
  Matriz), brigadistas, observadores y un puesto de primeros auxilios
  independiente del dispensario (Guía, pág. 5, sección 2.c).
- Tras la evacuación, "un equipo de especialistas estructurales, verificará la
  condición de las instalaciones" y la máxima autoridad decide, con base en ese
  criterio, si se retoman las actividades o se suspenden (Protocolo, pág. 2,
  puntos 5-6).

## 7. Captura de Google Maps

La captura disponible (`data/maps/captura_google_maps_campus_matriz.png`) solo
muestra:

- El pin general "Universidad de las Fuerzas Armadas ESPE" en Av. Gral.
  Rumiñahui S/N, Sangolquí (171103).
- Coordenadas aproximadas del centro del campus: lat -0.315344, lon -78.4478644
  (nivel de zoom de la vista, no una medición de campo).
- El contorno vial exterior del campus (Anillo Vial ESPE) y algunas vías
  colindantes (Av. General Rumiñahui, Guayas, Carchi, Pastaza, Loja).

No muestra la ubicación de los bloques G y H, ni de ningún punto de encuentro, ni
edificaciones internas etiquetadas. Cualquier coordenada de bloques G/H o de
puntos de encuentro debe obtenerse por medición directa (campo o Maps) y
marcarse con el `confidence` correspondiente ("medido_en_maps" o
"verificado_en_campo"), nunca inferirse de esta captura.

---

## Lo que los documentos NO dicen (y por tanto queda como `pendiente`)

Ninguno de los dos PDF ni la captura de Maps especifican:

- La **ubicación geográfica** (coordenadas, calle, patio) de ninguno de los 14
  puntos de encuentro del campus Matriz. Solo se confirma que existen y están
  señalizados (Guía, pág. 3).
- **Planos o croquis** de los bloques G y H (ni de ningún otro bloque): no hay
  planta arquitectónica, ni distribución de aulas.
- El **número de pisos** de los bloques G y H.
- La **ubicación, número o ancho de las gradas/escaleras** de los bloques G y H.
- Nombres o códigos de aulas específicas.
- Distancias en metros entre ningún par de puntos del campus.
- Qué bloques específicos tienen "riesgo de caída" (árboles, postes, cables,
  vidrios) cerca de sus salidas: el Protocolo da la regla general (alejarse de
  esos elementos) pero no un inventario por edificio.
- Capacidad de personas de ningún punto de encuentro ni de ninguna aula.

La Guía sí menciona que debe existir un "croquis de las vías de evacuación y la
ubicación de los diferentes puntos de encuentro" que se difunde a la comunidad
universitaria (Guía, pág. 4, incisos f y g), pero ese croquis en sí **no está
incluido** entre los documentos disponibles en `docs/`; su contenido no puede
darse por conocido y debe levantarse en campo (ver
`data/campo/FICHA_TRABAJO_DE_CAMPO.md`).
