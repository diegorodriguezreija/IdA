# IdA — Marco teórico, puentes conceptuales y horizonte

> **Estado: horizonte exploratorio, no vinculante.** Orienta, pero no manda: el diseño vigente es [`DISENO_COMPONENTES.md`](DISENO_COMPONENTES.md) y la observabilidad, [`DISENO_OBSERVABILIDAD.md`](DISENO_OBSERVABILIDAD.md). Autor: Diego Rodríguez Reija. Revisado y anotado por el arquitecto el 28/11/2026; las notas añadidas en la revisión van marcadas con **[Nota de revisión]**. Complementa a [`VISION.md`](VISION.md).

> **Nota de alcance y humildad.** IdA es un prototipo personal de ingeniería de software y un framework modular de agentes autónomos. Las referencias a la neurociencia, la biología y la psicología ecológica que aparecen en este documento son **inspiración conceptual y analogías de diseño**, nunca una equivalencia matemática ni una afirmación de que IdA reproduzca procesos biológicos o cognitivos reales. Cuando el texto señala un parecido con una teoría establecida, señala también dónde IdA se separa de ella.

## 1. Dónde se sitúa IdA

Buena parte de la investigación actual en agentes autónomos se reparte entre dos extremos: el aprendizaje por refuerzo profundo (que aprende políticas desde cero optimizando una recompensa escalar tras millones de pasos) y los agentes basados en grandes modelos de lenguaje (que razonan en lenguaje natural con un coste computacional alto).

IdA explora un espacio distinto e híbrido: una **arquitectura cognitiva modular y simbólica**, sin entrenamiento previo masivo ni modelos de lenguaje, pero organizada alrededor de un **cuerpo** que se degrada, una economía de recursos finitos (la **Onda**) y un flujo de procesamiento en capas (**Core** y sistemas **S1, S2 y S3**).

Por esa doble raíz —homeostática en su motivación, simbólica y modular en su implementación—, IdA converge de forma parcial con tres marcos teóricos clásicos de las ciencias cognitivas: la **Inferencia Activa** de Karl Friston, la **homeostasis y los marcadores somáticos** de Antonio Damasio, y la **psicología ecológica** de J. J. Gibson, apoyándose en el plano técnico en ideas de las arquitecturas cognitivas clásicas (Soar, ACT-R). **[Nota de revisión]** Hay otros tres marcos con los que el parecido es todavía más literal: el **espacio de trabajo global** (Baars, Dehaene), la **competición entre afordancias** (Cisek) y el **sistema de búsqueda** de Panksepp (sección 2.5).

**[Nota de revisión] Sobre los nombres S1, S2 y S3.** Evocan el Sistema 1 y el Sistema 2 de Kahneman (2011), pero significan otra cosa: S1 es **supervivencia**, S2 es **valor** y S3 es **verdad**. No son «rápido frente a lento»: los tres trabajan en el mismo latido, en orden, sobre la misma Onda.

## 2. Puentes conceptuales y límites

### 2.1 Karl Friston: Principio de Energía Libre e Inferencia Activa

La teoría de Karl Friston propone que los sistemas vivos se mantienen organizados minimizando la *sorpresa* (formalizada mediante la Energía Libre Variacional) a través de un ciclo continuo de predicción, percepción y acción.

#### Dónde coincide IdA

* **La Manta de Markov (*Markov Blanket*):** En Friston, un organismo se define por la frontera estadística que separa sus estados internos de los externos, mediados solo por estados sensoriales y activos. En IdA, la frontera limpia del diseño (Pilar 1 y decisión D4) persigue ese mismo aislamiento en software: el adaptador solo percibe en bruto y ejecuta primitivas motoras, sin exponer el estado oculto del entorno ni pensar por el individuo.
  **[Nota de revisión]** Hoy la manta tiene agujeros: lugares donde el mundo calcula estados que deberían ser internos del organismo. Son B5 (Crafter elige a qué entidades atender), B7 (Crafter atribuye la causa del daño) y B8 (los demás mundos entregan rasgos ya valorados, como «nutritivo» o «peligroso»), en [`PENDIENTES.md`](PENDIENTES.md). Mientras sigan abiertos, este puente es una aspiración y no una descripción.

* **Homeostasis en lugar de recompensa externa:** La Inferencia Activa cuestiona la necesidad de una señal externa de `reward`; el organismo actúa para mantenerse dentro de los estados fisiológicos que espera ocupar. IdA ignora la recompensa numérica de entornos como Crafter y deriva su motivación de déficits internos (`Soma`, `Interocepcion` y aliestesia en `Apetencia`).
  **[Nota de revisión]** Con un matiz: en Crafter, S3 se orienta por la lista de los 22 logros que declara el manual (`PerseguirMetas`). No es una recompensa escalar, pero sí una meta externa. La motivación de S1 y S2 es homeostática; la de S3 en Crafter, todavía no (ver 3.1).

* **Ponderación por precisión (*Precision Weighting*):** En el marco predictivo, los sistemas neuromoduladores regulan la ganancia de las señales según la incertidumbre y el estado del organismo. En IdA, ese papel tiene su análogo en la **Regulación de la Onda** (frecuencia, amplitud y potencia) y en la **Preatención** (`Saliencia`), que modulan qué entra en el cuello de botella atencional antes de la cognición deliberada.
  **[Nota de revisión]** Conviene precisar los neuromoduladores. La noradrenalina del locus coeruleus se asocia sobre todo a la incertidumbre *inesperada*, y la acetilcolina, a la *esperada* (Yu y Dayan, 2005). En la Inferencia Activa, la precisión sobre las políticas (cuánto fiarse del plan) se atribuye a la **dopamina** (Friston et al., 2012). En IdA, hoy la dopamina se calcula pero no modula nada (B11), así que esa forma de precisión no existe todavía.

* **Valor pragmático frente a valor epistémico:** En Inferencia Activa, toda acción equilibra acercarse a lo que el cuerpo necesita (*valor pragmático*) y reducir la incertidumbre sobre el entorno (*valor epistémico*). En IdA esa tensión emerge de la competencia entre S1 (necesidades vitales y seguridad) y S2/S3 (exploración, novedad, `Estudio` y contraste de proposiciones).
  **[Nota de revisión]** La diferencia es estructural: en la Inferencia Activa los dos valores se suman dentro de una misma cantidad (la energía libre esperada de cada política); en IdA los aportan sistemas distintos, y el Tribunal compara sus propuestas en una escala común.

* **Predicción, copia eferente y sorpresa:** El uso de un modelo directo del cuerpo (`ModeloDirecto`), la generación de expectativas ligadas a la acción (`Anticipacion` como copia eferente) y la revisión del conocimiento cuando el resultado contradice lo esperado (`sorpresa`) se alinean con el núcleo del procesamiento predictivo.

#### Dónde se separa

* **Motor matemático:** Friston formula percepción, atención, emoción y acción como instancias de una única ecuación probabilística (inferencia bayesiana aproximada sobre un modelo generativo). IdA **no** implementa inferencia variacional ni minimiza energía libre; utiliza módulos diferenciados, piezas explícitas, reglas de plasticidad locales y un **Tribunal** que arbitra propuestas discretas.

* **Compromiso de ingeniería:** Esta separación sacrifica elegancia matemática unificada a cambio de explicabilidad directa (cada decisión se lee como una propuesta con motivo y puntuación) y un coste de ejecución de milisegundos por latido.

### 2.2 Antonio Damasio: Homeostasis y marcadores somáticos

El trabajo de Antonio Damasio sostiene que la razón no opera al margen del cuerpo: la regulación homeostática y las señales afectivas (los *marcadores somáticos*) acotan y orientan la toma de decisiones antes y durante la deliberación.

#### Dónde coincide IdA

* **El cuerpo como regulador de la razón:** En IdA, el estado del `Soma` (constantes vitales, estrés, placer y valencia) no es un dato decorativo; condiciona directamente la Regulación de la Onda y la fórmula del **Tribunal**, que pondera urgencia frente a confianza en función del estrés.
  **[Nota de revisión]** Esta ponderación por estrés se parece más al desplazamiento que produce el estrés agudo, de lo deliberado a lo reactivo o habitual (Arnsten, 2009; Schwabe y Wolf, 2009), que a los marcadores somáticos en sentido estricto.

* **Jerarquía de supervivencia bajo estrés:** La prioridad estricta **S1 → S2 → S3** sobre un fondo compartido de amplitud atencional (decisión D14) refleja la asimetría biológica del estrés agudo: cuando hay peligro o déficit grave, los circuitos de supervivencia consumen el presupuesto disponible y desplazan a la planificación de S3 (en línea también con los modelos de regulación prefrontal bajo estrés de Arnsten).

* **Valoración afectiva previa a la deliberación (S2):** S2 (`Valor`, emoción, aversión) permite descartar o priorizar opciones por su valencia aprendida sin necesidad de que S3 despliegue una cadena lógica completa en cada latido.
  **[Nota de revisión]** Este es el análogo más fiel de los marcadores somáticos: asociaciones **aprendidas** entre opciones y estados del cuerpo que sesgan la elección antes de razonar (Bechara, Damasio et al., 1997).

#### Dónde se separa

* **Ausencia de experiencia subjetiva:** En Damasio es central la distinción entre *emoción* (respuesta fisiológica observable) y *sentimiento* (experiencia consciente de ese estado). IdA solo modela variables numéricas operativas; los nombres como «estrés», «placer» o «ánimo» son etiquetas de diseño, no estados conscientes ni subjetivos.

* **[Nota de revisión] Un afecto todavía pobre.** En el afecto nuclear (Russell, 1980 y 2003), valencia y activación son dos ejes independientes. En IdA, hoy la activación es el propio estrés (B10): no existe la activación agradable, como la excitación al conseguir un logro. Hasta que B10 se resuelva, IdA tiene valencia, pero no un espacio afectivo de dos ejes.

### 2.3 J. J. Gibson: Psicología ecológica y afordancias

J. J. Gibson propuso entender la percepción no como la reconstrucción pasiva de una imagen del mundo, sino como la detección activa de **afordancias**: las posibilidades de acción que el entorno ofrece a un cuerpo concreto.

#### Dónde coincide IdA

* **Separación entre organismo y cuerpo:** La reorganización por Componentes (`DISENO_COMPONENTES.md`, decisión D10) separa el núcleo cognitivo de la familia de cuerpos (`ida/cuerpos/cuadricula/`, interfaz `Contexto.espacio`, capa motora y sinergias). Un pez y un ratón comparten el hambre y el miedo, pero no la forma de desplazarse ni de ocultarse.

* **Afordancias frente a guiones:** En el diseño actual de IdA, los Componentes propios de un mundo no imponen secuencias rígidas; interpretan qué ofrece el entorno en términos comprensibles para el organismo. Por ejemplo, `Recinto` en Crafter no «ordena» cavar, sino que emite una afordancia de protección (sitio, coste y requisitos) sobre la que el organismo decide en competencia con sus demás impulsos.

#### Dónde se separa

* **Representaciones internas:** La psicología ecológica ortodoxa de Gibson defiende la *percepción directa* y rechaza las representaciones mentales internas. IdA, en cambio, es explícitamente representacional: construye un mapa topológico y métrico, guarda proposiciones y creencias en `Memoria`, y planifica cadenas de requisitos en S3. En este punto, IdA se acerca más a una síntesis pragmática entre afordancias ecológicas y arquitecturas simbólicas clásicas (como Soar o ACT-R).

### 2.4 Resumen comparativo

| Marco teórico | Idea que inspira a IdA | Cómo aparece en IdA | Diferencia principal |
| ----- | ----- | ----- | ----- |
| **Friston** (Inferencia Activa) | Frontera organismo-mundo, homeostasis sin *reward*, precisión, valor epistémico y sorpresa | Frontera limpia (D4), `Soma`, Regulación de la Onda, `Anticipacion`, contraste por sorpresa | Sin modelo generativo bayesiano ni energía libre variacional; arbitraje por Tribunal. La frontera tiene aún agujeros (B5, B7, B8) y la dopamina no modula la precisión (B11) |
| **Damasio** (Marcadores somáticos) | El cuerpo y el afecto orientan y acotan la deliberación racional | `Soma`, S2 (`Valor` aprendido), prioridad S1 → S2 → S3; ponderación por estrés en el Tribunal (más cerca de Arnsten) | Variables operativas; sin consciencia ni sentimientos subjetivos; activación ligada al estrés (B10) |
| **Gibson** (Psicología ecológica) | El entorno ofrece posibilidades de acción dependientes del cuerpo | `Cuerpo` (`Contexto.espacio`), capa motora, afordancias (`Recinto`) | IdA sí usa representaciones internas explícitas (`Memoria`, mapa, creencias) |
| **Soar / ACT-R** (Cognitivo clásico) | Separación entre conocimiento declarativo, memoria y resolución de metas | Manual declarativo, `Requisito`, `PerseguirMetas` (medios y fines) | Regulado por cuerpo, estrés, atención finita y guillotina temporal |
| **Baars, Dehaene** (Espacio de trabajo global) | Un medio compartido y limitado donde los procesos especializados publican y leen | La Onda: capacidad limitada (amplitud), plazo (guillotina), sistemas que escriben y leen piezas | Sin «ignición» ni difusión todo o nada; el acceso es por orden S1 → S2 → S3 |
| **Cisek** (Competición entre afordancias) | Varias acciones posibles se preparan en paralelo y compiten hasta que una gana | Estrategias de S1, S2 y S3 que proponen acciones a la vez; el Tribunal resuelve, como los ganglios basales | La competición se resuelve una vez por latido, no de forma continua |
| **Panksepp** (Sistema BUSCAR) | La dopamina como motor de la exploración y la expectativa | Impulso exploratorio de S2 (`Explorar`), `Estudio` en S3 | La dopamina no modula todavía la exploración (B11) |

### 2.5 [Nota de revisión] Tres marcos más

* **El espacio de trabajo global (Baars, 1988; Dehaene, Kerszberg y Changeux, 1998; Dehaene y Changeux, 2011).** Propone que la cognición consciente es un espacio compartido, de capacidad limitada, donde procesos especializados compiten por publicar contenidos que todos los demás pueden leer. Es probablemente el puente más literal de la arquitectura: la **Onda** es ese espacio. La amplitud es su capacidad, la guillotina su límite temporal y las piezas sus contenidos. IdA se separa en que no tiene la «ignición» (la activación global, todo o nada) y en que el acceso sigue un orden fijo.

* **La competición entre afordancias (Cisek, 2007).** Une a Gibson con la selección de acción: el cerebro prepara en paralelo varias acciones posibles a partir de lo que ofrece el entorno, y estas compiten hasta que los ganglios basales resuelven (Redgrave, Prescott y Gurney, 1999). Es lo que hacen juntos `Recinto`, las estrategias y el **Tribunal**: varias propuestas a la vez y una ganadora.

* **El sistema BUSCAR de Panksepp (1998).** El circuito dopaminérgico mesolímbico como motor de la búsqueda, la exploración y la expectativa, distinto del placer de consumir. Es el fundamento biológico de la curiosidad de 3.1 y de los gustos de la Visión, y por eso B11 es su requisito.

## 3. Horizonte conceptual: líneas futuras para IdA

Las ideas anteriores no son solo una lectura retrospectiva de lo que ya existe; señalan líneas concretas de evolución que encajan con la hoja de ruta pendiente del proyecto.

### 3.1 Motivación intrínseca por reducción de incertidumbre (M6)

Hoy, el motor de progreso de S3 (`PerseguirMetas`) depende de una lista de metas declaradas en el manual (por ejemplo, los 22 logros de Crafter). En un mundo sin lista de logros, el organismo carece de dirección sostenida más allá de la exploración básica.

El enfoque predictivo ofrece una alternativa general sin necesidad de introducir inferencia bayesiana compleja: **tratar la reducción de incertidumbre como motor de progreso**.

* **Resolución natural del «problema del cuarto oscuro»:** Una objeción clásica a los agentes que solo evitan la sorpresa es que deberían quedarse inmóviles en un rincón seguro. En IdA, S1 impide esa parálisis: el desgaste metabólico convierte la inacción en una amenaza vital creciente.

* **Impulso epistémico en calma:** Cuando S1 está satisfecho, S2 y S3 pueden priorizar acciones que reduzcan el error de predicción propio:

  1. contrastar proposiciones que siguen en estado de hipótesis;
  2. interactuar con clases de objetos cuyos efectos aún son desconocidos;
  3. investigar situaciones donde `Anticipacion` (copia eferente) acaba de producir una **sorpresa** (discrepancia entre lo esperado y lo ocurrido).

* **Resultado esperado:** El «progreso» deja de definirse como tachar una lista externa y pasa a emerger de la reducción progresiva de incertidumbre sobre el entorno, compatible con cualquier mundo.

* **[Nota de revisión] Requisito y medida.** Hace falta una señal que valore la ganancia de información, y en biología esa señal pasa por el sistema dopaminérgico (Kang et al., 2009; Gruber, Gelman y Ranganath, 2014): B11 es requisito de M6. `Estudio` ya es una semilla. Medida propuesta: el saber ganado por unidad de tiempo, comparado con un explorador aleatorio en el mismo mundo.

### 3.2 Revisión de creencias y robustez ante perturbaciones

Si un mundo cambia sus reglas (por ejemplo, un material que dejaba pasar a un enemigo o un recurso que solo funciona en ciertas condiciones), un sistema que confía ciegamente en su manual falla igual que un script.

La arquitectura de IdA ya distingue la confianza empírica (`c_exp`) de la autoridad externa (`c_aut`). El paso siguiente es consolidar que la **sorpresa repetida** invalide hechos heredados o declarados y fuerce a S3 a buscar alternativas, verificándolo sistemáticamente mediante baterías de perturbaciones.

**[Nota de revisión]** Para verlo hace falta que el registro del latido diga la fuente de cada saber (`saber[].fuente`, que distinga manual y biblioteca) y lo que se olvida (el hecho `olvida`), hoy en la sección 15.8 de `DISENO_OBSERVABILIDAD.md`. Para medirlo, V2 (la batería de perturbaciones).

### 3.3 Desacoplamiento real del cuerpo y del espacio

Para confirmar que el núcleo no arrastra sesgos de cuadrícula 2D, el horizonte natural incluye enfrentar el mismo núcleo a tres tipos de entornos con cuerpos distintos:

1. **Otro mundo de cuadrícula** (p. ej., *MiniGrid* o *MiniHack*): reutilizando `ida/cuerpos/cuadricula/` con cero cambios en el núcleo, como prueba de que la separación de componentes es real (V3).
2. **Un mundo puramente topológico o textual** (p. ej., *TextWorld*): sin coordenadas ni geometría 2D, apoyado únicamente en el mapa topológico de `Memoria`, el manual y el planificador de S3. **[Nota de revisión]** Usaría la vía sin espacio métrico (`SIN_ESPACIO`) que existe desde C1.
3. **Un cuerpo continuo sencillo:** con velocidad, orientación continua e inercia, para validar si la capa motora, las sinergias y la guillotina de tiempo real escalan fuera de entornos discretos.

### 3.4 Cognición social y entornos multiagente

Actualmente S2 valora sobre todo objetos y lugares. Introducir entornos donde convivan varios individuos de IdA (con arquetipos distintos: cooperativos, prudentes u oportunistas) permitiría explorar el potencial completo de `Sujeto`, `Valor` y `Agente`: modelar la fiabilidad de otros individuos a partir de la experiencia y comprobar si emergen conductas de evitación, seguimiento o cooperación sin programarlas explícitamente.

**[Nota de revisión] Un solo mecanismo para fuentes y para otros individuos.** Para IdA, «otro individuo» y «una fuente de conocimiento» (una base local, internet, un LLM local, el humano; ver la sección 2.2 de la Visión) son lo mismo: **informantes con una fiabilidad que se aprende** al contrastar lo que dicen con la experiencia y con otros informantes. Diseñarlo una vez serviría al mundo de conocimiento y al multiagente.

## 4. Criterio de verificación

Cualquiera de estas direcciones futuras sigue sujeta a la misma regla que el resto del proyecto: **una idea biológicamente atractiva solo entra en el núcleo si demuestra utilidad medible**.

* Las hipótesis conceptuales exploratorias (como la motivación por reducción de incertidumbre frente a metas declaradas, o variantes del arbitraje) se contrastan primero frente a líneas base tradicionales o versiones de control en el **Laboratorio IdA**, con semillas fijadas de antemano y publicando también los resultados negativos.
* Solo lo que mejora de forma reproducible y respeta la pureza del núcleo (`test_pureza`, `test_conceptos` y criterio de no inferioridad D17) pasa a formar parte del framework base.

## Referencias citadas en la revisión

- Arnsten, A. F. T. (2009). Stress signalling pathways that impair prefrontal cortex structure and function. *Nature Reviews Neuroscience*, 10, 410–422.
- Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.
- Bechara, A., Damasio, H., Tranel, D. y Damasio, A. R. (1997). Deciding advantageously before knowing the advantageous strategy. *Science*, 275, 1293–1295.
- Cisek, P. (2007). Cortical mechanisms of action selection: the affordance competition hypothesis. *Philosophical Transactions of the Royal Society B*, 362, 1585–1599.
- Dehaene, S., Kerszberg, M. y Changeux, J.-P. (1998). A neuronal model of a global workspace in effortful cognitive tasks. *PNAS*, 95, 14529–14534.
- Dehaene, S. y Changeux, J.-P. (2011). Experimental and theoretical approaches to conscious processing. *Neuron*, 70, 200–227.
- Friston, K. et al. (2012). Dopamine, affordance and active inference. *PLoS Computational Biology*, 8, e1002327.
- Gruber, M. J., Gelman, B. D. y Ranganath, C. (2014). States of curiosity modulate hippocampus-dependent learning via the dopaminergic circuit. *Neuron*, 84, 486–496.
- Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
- Kang, M. J. et al. (2009). The wick in the candle of learning: epistemic curiosity activates reward circuitry and enhances memory. *Psychological Science*, 20, 963–973.
- Niv, Y., Daw, N. D., Joel, D. y Dayan, P. (2007). Tonic dopamine: opportunity costs and the control of response vigor. *Psychopharmacology*, 191, 507–520.
- Panksepp, J. (1998). *Affective Neuroscience*. Oxford University Press.
- Redgrave, P., Prescott, T. J. y Gurney, K. (1999). The basal ganglia: a vertebrate solution to the selection problem? *Neuroscience*, 89, 1009–1023.
- Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39, 1161–1178. Russell, J. A. (2003). Core affect and the psychological construction of emotion. *Psychological Review*, 110, 145–172.
- Schultz, W., Dayan, P. y Montague, P. R. (1997). A neural substrate of prediction and reward. *Science*, 275, 1593–1599.
- Schwabe, L. y Wolf, O. T. (2009). Stress prompts habit behavior in humans. *Journal of Neuroscience*, 29, 7191–7198.
- Yu, A. J. y Dayan, P. (2005). Uncertainty, neuromodulation, and attention. *Neuron*, 46, 681–692.
