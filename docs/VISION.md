# IdA — Visión a largo plazo: subjetividad, lenguaje y cuerpo físico

> **Estado: horizonte exploratorio, no vinculante.** Es una mezcla de visión y lluvia de ideas del autor (Diego Rodríguez Reija), no un plan aprobado. Orienta, pero no manda: el diseño vigente es [`DISENO_COMPONENTES.md`](DISENO_COMPONENTES.md) y la observabilidad, [`DISENO_OBSERVABILIDAD.md`](DISENO_OBSERVABILIDAD.md). El arquitecto añadió el 28/11/2026 la sección 7, con las implicaciones para el trabajo inmediato.

> **Nota de alcance y humildad.** Este documento complementa [`MARCO_TEORICO.md`](MARCO_TEORICO.md) y describe una visión exploratoria a medio y largo plazo, no capacidades actuales de IdA. Hablar de «subjetividad», «gustos», «aburrimiento» o «comunicación» refiere aquí a dinámicas funcionales implementables en software (valoración diferencial, saciedad de novedad, contraste de creencias), nunca a experiencia consciente ni a equivalencia con seres vivos.

## 1. En qué se diferencia IdA de los LLMs actuales

Para que el proyecto mantenga su identidad al entrar en terrenos de lenguaje y conocimiento, conviene fijar con claridad qué no es IdA. Un gran modelo de lenguaje (LLM) es una herramienta extraordinaria para procesar y generar texto, pero parte de un paradigma opuesto al de un organismo autónomo:

| Dimensión | LLM actual (paradigma asistente) | IdA (paradigma organismo) |
|---|---|---|
| Activación | Pasivo: solo existe cuando recibe un prompt externo. | Activo: tiene un latido continuo y actúa por iniciativa propia. |
| Motivación | Optimizado para ser útil y complacer al usuario en cualquier tema. | Regulado por su Soma, su Arquetipo, sus intereses (S2) y su incertidumbre (S3). |
| Subjetividad y aburrimiento | Sin gustos propios ni saciedad; responde con el mismo tono a cualquier pregunta. | Dos individuos con distinto carácter o linaje valoran el mismo tema de forma distinta; un tema que ya no sorprende pierde interés. |
| Epistemología | Conocimiento implícito y estadístico en pesos congelados; difícil de auditar o refutar en vivo. | Proposiciones explícitas con origen trazable (c_exp empírica frente a c_aut de autoridad), revisables ante contradicción. |
| Continuidad | Memoria limitada a la ventana de contexto o a recuperación externa (RAG). | Historia vital continua, consolidación y transmisión parcial al linaje. |
| Tiempo real | Genera tokens sin noción nativa de urgencia física. | Guillotina cooperativa: si el plazo vence, el cuerpo actúa con lo que tiene. |

El objetivo de IdA no es competir con un LLM en amplitud enciclopédica ni en fluidez verbal, sino explorar algo que los LLMs no tienen por diseño: un agente con cuerpo, historia, criterio propio e iniciativa.

## 2. El mundo de adquisición de conocimiento y los gustos propios

Hoy IdA ya cuenta con una base embrionaria para el conocimiento externo: el puerto hexagonal Biblioteca, el verbo LEER, la atención sostenida de Estudio y la distinción entre evidencia empírica (c_exp) y autoridad (c_aut). El siguiente salto es concebir un mundo epistémico donde el entorno no sea una cuadrícula física, sino un espacio de temas, fuentes e interlocutores.

### 2.1 Subjetividad sin programarla a mano

En lugar de obligar a IdA a aprender un temario fijo, el interés por unos temas u otros puede emerger de mecanismos ya presentes en la arquitectura:

- **Sesgo heredado:** el Arquetipo (apertura, responsabilidad, neuroticismo...) y el legado del linaje predisponen a prestar más atención a ciertos patrones o ámbitos.
- **Sesgo experiencial (S2):** los temas asociados a resoluciones satisfactorias de incertidumbre o a interacciones valiosas ganan Valor en S2; los que generan contradicciones estériles o no aportan nada nuevo pierden peso.
- **Saciedad y aburrimiento:** cuando un tema deja de reducir incertidumbre o de generar sorpresa, su saliencia cae de forma natural y el individuo cambia de foco por iniciativa propia.

### 2.2 Fuentes múltiples con distinta fiabilidad

En este mundo, IdA podría consultar distintas fuentes —bases locales, internet, un LLM local o el propio usuario humano— tratándolas a todas bajo la misma regla: ninguna fuente es verdad absoluta. Cada fuente tendría una fiabilidad inicial que IdA ajusta con la experiencia al detectar coherencias o contradicciones entre ellas. Preguntar al humano dejaría de ser un paso obligado y pasaría a ser una decisión de S3 cuando necesita resolver una duda o contrastar dos versiones opuestas.

## 3. El lenguaje como códec, no como cerebro

El mayor riesgo al conectar IdA con el lenguaje natural es que acabe convirtiéndose en un wrapper de un LLM y pierda su arquitectura cognitiva. Para evitarlo, se establece una frontera estricta inspirada en el Pilar 1:

- **El lenguaje interno es de IdA:** las creencias, dudas, valoraciones e intenciones viven como piezas y proposiciones estructuradas dentro del núcleo.
- **El LLM pequeño actúa solo como códec lingüístico:** su único papel —análogo en lo funcional a las áreas del lenguaje (Broca / Wernicke)— es decodificar lenguaje humano a proposiciones estructuradas que entren por S3 · Sentir · Comunicacion, y codificar una intención comunicativa de IdA en una frase comprensible para el humano.
- **El «qué decir» y el «por qué decirlo» son 100 % de IdA:** el códec nunca decide qué preguntar, si estar de acuerdo ni de qué tema hablar. Si IdA no tiene nada que preguntar o no le interesa la conversación, no habla.

## 4. El horizonte físico: IdA en un cuerpo real (Raspberry Pi)

El destino natural a largo plazo de esta arquitectura no es un videojuego, sino un cuerpo físico autónomo: por ejemplo, una Raspberry Pi montada sobre un chasis móvil (smart car kit) con cámara, sensores básicos y una estación de carga.

En un entorno físico real, las piezas que en simulación parecen abstracciones cobran sentido literal:

| Pieza de IdA | Equivalente físico en el robot |
|---|---|
| Interocepcion y Soma | Nivel real de batería, temperatura de CPU, estado de carga. |
| Recurso vital y Hogar | Base de carga eléctrica a la que debe aprender a regresar antes de agotarse. |
| Exterocepcion | Cámara + detección ligera local (p. ej., objetos conocidos o marcadores visuales) traducida a piezas en bruto. |
| `ida/cuerpos/robot/` | Nueva familia de cuerpos con primitivas motoras físicas (avanzar, girar, detenerse, acoplarse). |
| Guillotina cooperativa | Seguro de tiempo real: impide que el robot siga avanzando contra un obstáculo por quedarse pensando en S3. |
| Códec lingüístico + S2/S3 | Capacidad de acercarse al humano y hablarle para expresar una duda real, pedir ayuda o comentar algo que le llama la atención. |

Además, el coste computacional actual del núcleo de IdA (del orden de unos pocos milisegundos por latido en Python) hace viable que el cerebro cognitivo corra directamente en una Raspberry Pi sin depender de la nube.

## 5. Escalera de progreso deseado

Para llegar a ese horizonte sin perder el rigor ingenieril ni disparar la complejidad antes de tiempo, el camino natural sigue una progresión por capas:

1. **Cierre del ciclo actual (corto plazo):** completar la línea de observabilidad (Fase T), cerrar las brechas de la Fase B en Crafter (B5, B7, B1) y completar la validación independiente (V1, V2, M7) para consolidar la posición en External Knowledge.
2. **Validación en nuevos mundos discretos (medio plazo):** conectar MiniGrid (prueba de reutilización de `ida/cuerpos/cuadricula/` sin tocar el núcleo, V3) y TextWorld (demostrar que el núcleo funciona sin cuadrícula 2D).
3. **Motor epistémico y mundo de conocimiento (medio-largo plazo):** abordar M6 (motivación por reducción de incertidumbre) y construir el primer mundo de adquisición de conocimiento con gustos propios y códec lingüístico.
4. **Cuerpo continuo en simulación (largo plazo):** crear `ida/cuerpos/continuo/` (velocidad, ángulo, inercia, batería y base de carga en 2D) para resolver la capa motora y los reflejos físicos antes de tocar hardware.
5. **Encarnación física en Raspberry Pi (horizonte final):** conectar el mismo núcleo a sensores reales, cámara, motores y estación de carga, integrando la comunicación por voz/texto con el humano.

## 6. Dudas abiertas y retos a tratar en el futuro

Esta hoja de ruta abre preguntas difíciles que no tienen respuesta trivial y que conviene dejar registradas para investigarlas con método cuando llegue su turno:

1. **El problema del anclaje simbólico (Symbol Grounding):** Si IdA aprende una proposición leyendo texto («el agua daña la electrónica» o «una taza suele estar en la cocina»), ¿cómo conecta ese símbolo abstracto de S3 con lo que detecta su cámara física en Exterocepcion sin cablear un diccionario manual gigante?
2. **Contaminación del códec lingüístico:** Los LLMs locales están entrenados para ser serviciales, completar información que no se les pidió y suavizar contradicciones. ¿Cómo diseñar el códec para garantizar que traduce con fidelidad estricta y no inyecta sesgos, alucinaciones ni «personalidad de asistente» en las proposiciones de IdA?
3. **Punto de partida del mundo de conocimiento:** ¿Conviene empezar con un entorno cerrado y controlado (solo diálogo con el humano y una base local de hechos con contradicciones diseñadas para probar a S3), o exponer a IdA desde el inicio a fuentes abiertas y ruidosas como internet?
4. **Equilibrio entre profundidad y dispersión (gestión del aburrimiento):** Si la novedad decae demasiado rápido, IdA saltará de tema en tema sin consolidar nada; si decae demasiado lento, se quedará atrapado indefinidamente en un único asunto. ¿Cómo calibrar la saciedad epistémica para que emerja un ritmo sano de estudio y cambio de interés?
5. **Evaluación científica de la subjetividad:** En Crafter existe una Score objetiva. En un mundo de intereses propios y diálogo, ¿qué métricas permiten distinguir entre un agente que realmente desarrolla criterio, coherencia y curiosidad útil, frente a otro que simplemente divaga de forma aleatoria?
6. **Cuellos de botella físicos en Raspberry Pi:**
   - *Percepción frente a latido:* ejecutar visión por computador en la Pi puede tardar mucho más que el latido cognitivo; hará falta desacoplar la frecuencia de cámara de la frecuencia del organismo.
   - *Seguridad física fuera de la cognición:* además de la guillotina cooperativa, un robot real necesita reflejos de bajo nivel (p. ej., sensor de distancia/choque) que puedan frenar motores por debajo del ciclo cognitivo.
   - *Acoplamiento a la carga:* encontrar la estación y acoplarse físicamente es uno de los problemas clásicos más duros de la robótica casera; habrá que decidir qué parte resuelve el cuerpo (`ida/cuerpos/robot/`, como primitiva o sinergia motora) y qué parte decide el organismo.

## 7. Implicaciones para el trabajo inmediato (nota del arquitecto, 28/11/2026)

Lo que esta visión cambia de lo que viene ahora, sin comprometer nada más allá:

1. **«El mundo no piensa por el organismo» es requisito, no pulcritud.** Una cámara real no entrega rasgos ya valorados ni recorta lo que ve. B5, B7 y B8 con C7b ([`PENDIENTES.md`](PENDIENTES.md)) son el ensayo general de la encarnación. El trabajo de C1 (el cuerpo define el espacio, `Contexto.espacio`) es lo que permitirá `ida/cuerpos/continuo/` sin tocar el núcleo.
2. **B11 (la dopamina no modula nada) es la semilla de la subjetividad.** El aburrimiento y los gustos de la sección 2.1 salen de una dopamina que funcione: un tema deja de interesar cuando deja de producir errores de predicción, y la curiosidad sigue la reducción esperada de incertidumbre. B10 (activación separada del estrés) también: sin activación agradable no hay «interés». Las dos suben de prioridad en la fase B.
3. **Las fuentes con fiabilidad (2.2) necesitan telemetría que falta:** que el registro del latido diga la fuente de cada saber (`saber[].fuente`) y lo que se olvida (hecho `olvida`), en la sección 15.8 de `DISENO_OBSERVABILIDAD.md`. Conviene hacerlo antes de cualquier mundo de conocimiento.
4. **Una regla comprobable para el códec (duda 2):** en los tests, el códec debe poder sustituirse por un traductor determinista sin que cambie qué decide IdA preguntar, creer o decir. Si cambia, el LLM está contaminando el núcleo. Es el mismo espíritu que la equivalencia y la invariancia.
5. **Fuentes y otros individuos, un solo mecanismo:** para IdA, una fuente de conocimiento y otro individuo (sección 3.4 del Marco teórico) son lo mismo: informantes con una fiabilidad que se aprende.
6. **El robot tiene la arquitectura a favor:** el reflejo por debajo de la cognición encaja con D9 y D10 (la seguridad y las sinergias viven en el cuerpo, `ida/cuerpos/robot/`); el latido con plazo y guillotina ya separa pensar de actuar a tiempo; desacoplar la cámara del latido es la misma idea que la Onda copiada del latido anterior.
7. **Medir la subjetividad (duda 5):** hay criterio si la variación entre individuos (por carácter y linaje) es mayor que la de un mismo individuo en el tiempo; hay curiosidad útil si el saber ganado por unidad de estudio supera al de un explorador aleatorio en el mismo mundo. Ambas cosas se pueden medir con el Laboratorio, las grabaciones y D17.
