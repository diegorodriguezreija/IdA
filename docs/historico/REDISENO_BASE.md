# IdA — Borrador de rediseño de la base

Nov 15, 2026 · @Diego

## Propósito

Este borrador recoge el replanteamiento de la base de IdA (Core y sistemas S1, S2, S3), la parte que `AGENTS.md` protege frente a cambios del agente. Cerrado el 15/11/2026 con 24 decisiones; nada está implementado todavía. Siguiente paso: ordenar la implementación de lo más claro y menos invasivo a lo más rompedor, en un documento aparte.

Punto de partida: la rama `main` pública (`5c8ae1e`). Las ramas de las fases 1 a 5 no están publicadas, así que sus componentes (`Orientacion`, `Estudio`, `Anidar`) no aparecen en el mapa actual.

## Decisiones tomadas

### 1. `Escena` pasa a llamarse `Exterocepcion`

Se renombran el componente y el canal, igual que ya ocurre con `Interocepcion`. Core·Sentir queda con la tríada clásica de los sentidos: interocepción (el cuerpo por dentro), propiocepción (la posición del cuerpo) y exterocepción (el mundo de fuera).

- Motivo: "Escena" sugiere una representación ya integrada, y esa integración la hace `Imagen` en S1.
- Alcance: todos los `ev("Escena")` del Core, de los sistemas y de los componentes propios de los mundos, además de tests y documentación. Es un cambio mecánico.

### 2. Separar la pulsión (qué) del procedimiento (cómo)

Un impulso nace del sentir y no se puede cambiar: es lo que hay. La estrategia para satisfacerlo sí se puede variar si no funciona. Hoy IdA no separa ambas cosas: `ImpulsoS1` detecta la necesidad y propone la acción a la vez.

- Base biológica: la distinción de la etología entre conducta apetitiva (búsqueda flexible y aprendida) y consumatoria (el acto fijo).
- Primer paso: un componente `Procedimiento` en S1·Reaccionar, que sustituye a los componentes de defensa propios de cada mundo (`Defensa`, `DefensaCrafter`).
- Este cambio de nivel (pulsión e interpretación primero, estrategia después) se aplicará probablemente a los tres sistemas, S2 incluido. Se irá concretando sistema a sistema.

### 3. Cuatro niveles: impulso, estrategia, acción, decisión

| Nivel | Dónde | Qué es | Ejemplo |
| --- | --- | --- | --- |
| Impulso | Reaccionar de cada sistema | El porqué; nace del estado interno sentido e interpretado. No se elige. | Alimentación |
| Estrategia | Reaccionar de cada sistema | El cómo, en abstracto. Dura varios latidos, tiene progreso y se agota. | Explorar, recordar dónde hubo comida |
| Acción | Actuar de cada sistema (nuevo) | Candidato concreto con verbo genérico y parámetros. | Desplazar a un lugar |
| Decisión | Core·Actuar | El `Tribunal` elige una acción y el `Actuador` la ejecuta. | — |

- **Actuar en cada sistema.** S1, S2 y S3 ganan la etapa Actuar (ya prevista en `ETAPAS`, sin uso hoy), que traduce la estrategia activa en candidatos de acción.
- **`Ejecucion` pasa a llamarse `Accion`** (la pieza candidata y su canal).
- **Las estrategias son propias de cada mundo; en el Core solo existe el nombre.** Sin conocer el mundo no se puede definir cómo explorar: el Core declara "explorar" sin parámetros ni funcionamiento, y cada mundo lo concreta (en Crafter, por ejemplo, explorar en círculos o en línea recta). El impulso, en cambio, sí es genérico.
- **Las acciones son genéricas**, porque al final el Core ejecuta un verbo que conocen todos los mundos.
- **Una estrategia tiene progreso y agotamiento.** Para un mismo impulso se puede pasar de una estrategia a otra cuando la actual se agota. Pendiente de concretar.
- **No actuar también es una opción:** el componente puede aprovechar el latido para recuperar recuerdos (pasada activa). El mundo sigue avanzando mientras tanto (`ESPERAR`).
- **La acción ganadora lleva su origen** (impulso y estrategia), para que solo aprenda la estrategia que se ejecutó de verdad.

### 4. Continuidad: la estrategia activa tiene prioridad

El `Tribunal` da prioridad a las acciones cuya estrategia está activa, para mantener la coherencia en el tiempo. La continuidad solo se rompe de dos formas:

- **Brusca:** un reflejo (decisión 6).
- **Calmada:** la estrategia acumula agotamiento sin progreso y se abandona.

**Tipo de pieza `Estrategia` en el Core.** El Core define el tipo (como `Accion`) con sus atributos obligatorios: progreso, agotamiento y la referencia a su impulso. Cada sistema produce sus estrategias desde sus propios componentes, en Reaccionar. El Core no necesita etapas propias de Interpretar o Reaccionar: definir el tipo no es pensar. Lo que sí hace el Core es conservar las estrategias activas de un latido al siguiente (como ya conserva la memoria rápida) y dárselas al `Tribunal`.

**Otra necesidad que crece poco a poco no necesita un mecanismo aparte.** Su arousal sube hasta superar al de la estrategia activa, incluido el plus por estar activa. Condiciones para que funcione:

- el plus por estar activa es acotado y se suma, nunca multiplica;
- el arousal de un impulso crece con la urgencia hasta valores cercanos a 1.

### 5. Un indicador de progreso por sistema

Cada sistema mide su propio progreso según su meta, y esa señal alimenta el progreso y el agotamiento de sus estrategias. Se llama feedback; no *fitness*, que ya usa `calcular_fitness` para el linaje.

| Sistema | Meta | Señal de progreso propuesta |
| --- | --- | --- |
| S1 | Supervivencia | Bajan los déficits del cuerpo |
| S2 | Valor | Mejora el placer o la valencia |
| S3 | Verdad | Baja el error de predicción |

`Soma` ya calcula buena parte de estas señales.

### 6. El reflejo solo ante cambios bruscos del Sentir

Un reflejo se activa solo ante un cambio drástico entre el estado inicial y el final del Sentir. Es una estrategia innata, corta y de duración fija (orientarse, sobresaltarse, empezar a huir), con la prioridad más alta. Se agota sola a los pocos latidos y después decide el resto.

### 7. Metadatos de las piezas

| Metadato | Qué guarda | Función | Alcance |
| --- | --- | --- | --- |
| Arousal | Intensidad, de 0 a 1 | Fuerza e importancia del recuerdo | Todas las piezas (ya existe) |
| Trust | Certeza o fiabilidad, de 0 a 1 | Cuánto confiar antes de actuar | Todas las piezas (hoy `confianza`) |
| Decay | Tasa de caducidad | Cuánto dura la vigencia del dato; unifica el olvido hoy repartido por `Memoria` | Todas las piezas (nuevo) |
| Audit | Creación, actualización, origen, registro | Rastrear el origen y corregir errores | Todas las piezas (hoy `creada`, `actualizada`, `sistema`, `entradas`) |
| Fitness | Éxito o fracaso (+/−) | Si el comportamiento se repite o se evita | Solo tipos que pueden tener éxito o fracaso (nuevo) |
| Cost | Gasto energético o riesgo estimado | Si vale la pena ejecutar; unificar con el coste de atención al percibir | Solo tipos que se ejecutan o se perciben con coste (nuevo) |

- **La saliencia queda fuera de la pieza:** se calcula al consultar, según la necesidad del momento.
- **Progreso y agotamiento no son metadatos generales**, sino estado de una estrategia. Tampoco equivalen al decay: el decay es olvido con el tiempo; el agotamiento, esfuerzo sin resultado.

### 8. Objeto como entidad propia en S1·Interpretar

Nuevo componente `Objeto`, entre `Imagen` y `Supervivencia`. Hoy el tipo de pieza ya existe, pero lo fabrica `Imagen` en su propio código (`s1.py:46`).

- **Imagen** es el instante sentido: paisaje, olor, tacto.
- **Objeto** es una entidad propia, no una relación: un cuerpo que se distingue dentro de la Imagen. Guarda su **prototipo**, la sección de la Imagen que lo representa. Ese prototipo es lo que permitirá reconocerlo (el mismo de antes, o de qué clase es), y conecta con el tema de memoria.
- **Supervivencia** sí es una relación: la de cada objeto con la supervivencia.

**Quién puede ser Sujeto o Agente:**

|  | Sujeto (S2) | Agente (S3) |
| --- | --- | --- |
| Imagen | Sí: un lugar, un ambiente, el viento o una ola tienen valor | No: provocan cosas, pero sin intención |
| Objeto | Sí | Sí: la agencia se atribuye a cuerpos con intención |

Una Imagen puede llevar a S3 a suponer un agente que no se ve (algo ahí cruje), como hipótesis.

**Entidades y papeles.** Imagen y Objeto son *entidades* (S1). Sujeto y Agente son *papeles* que una entidad toma: se toma como Sujeto en S2 para valorarla y como Agente en S3 para atribuirle intención. Todo Sujeto es una Imagen o un Objeto; no al revés.

**Habituación dentro de Supervivencia.** Además de recursos y peligros, hay neutros. Un neutro con trust bajo es desconocido (cautela o curiosidad). Un neutro con trust alto es la habituación: ya sé que no pasa nada.

### 9. S2: Emoción en Sentir y Valor como única relación

- **`Emocion`, nuevo en S2·Sentir, después de `Patron`.** Es el estado afectivo interno (valencia y arousal) sentido por el individuo. Se activa con la Interocepción y con `Patron`: un patrón reconocido dispara la emoción antes de interpretar (la vía rápida del miedo, por la amígdala). Usa el Valor del latido anterior. Hoy lo calcula `Soma` y solo lo saca `Exteriorizacion`.
- **`Valor` es la única relación de S2**, como Supervivencia en S1: lo que vale cada Sujeto para mí.

| Dimensión de Valor | Pregunta sobre el Sujeto |
| --- | --- |
| Motivacional | ¿Qué motivación tiene para mí? |
| Potencia | ¿Qué fuerza tiene, está cansado? (no *energética*, para no confundirla con mi energía) |
| Sentimental | ¿A qué sentimiento lo asocio? |
| Social | ¿Es dominante, un igual, está por debajo de mí? |

Mi propio estado energético no es una dimensión de Valor: es del cuerpo (S1 e Interocepción).

### 10. S2·Reaccionar, paralelo a S1

| Componente | Papel | Equivalente en S1 |
| --- | --- | --- |
| `Exteriorizacion` | Reflejo de S2: la expresión emocional es involuntaria. Tendrá efecto cuando haya varios individuos. | `Reflejo` |
| `ImpulsoS2` | Modula los impulsos compartidos con S1 según su criterio y añade los propios. | `ImpulsoS1` |
| `ProcedimientoS2` | Produce las estrategias de S2 (piezas `Estrategia`). | `ProcedimientoS1` |

- **Mismo nombre en todos los sistemas**, con sufijo: `ImpulsoS1`, `ProcedimientoS2`… Todos los procedimientos producen piezas `Estrategia`, cada uno con el criterio de su sistema. Se descartaron *Afrontamiento* y *Tendencia*.
- **`Curiosidad` deja de ser un componente** y pasa a ser un impulso de S2: explorar en general, u observar e investigar un Objeto nuevo (saber más).
- **`Hogar` deja de ser un componente.** Refugiarse es una estrategia que comparten S1 y S2, cada uno con su criterio: S1 elige el sitio protegido más cercano ante peligro o agotamiento (un animal simple duerme donde le pilla); S2 elige el refugio que valora, su hogar (un animal complejo).

### 11. Dos niveles en S3: Intención y ProcedimientoS3

|  | Qué (por qué actuar) | Cómo (estrategia) |
| --- | --- | --- |
| S1 | `ImpulsoS1` | `ProcedimientoS1` |
| S2 | `ImpulsoS2` | `ProcedimientoS2` |
| S3 | `Intencion` | `ProcedimientoS3` (hoy `Comportamiento`) |

- **Intención** es el *qué* deliberado: lo que S3 se propone a partir de lo que sabe, frente al impulso, que surge. Se descartaron *Conducta* y *Comportamiento* por ser casi sinónimos.
- **S2 arbitra valorando, no proponiendo.** `ImpulsoS2` modula los candidatos de S1 y S3 según el valor. S2 no tiene niveles deliberados propios: lo convertiría en un S3 pequeño.
- Los componentes de S3 propios de un mundo (`PlanTecnologico`, `Prudencia`) pasarían a ser estrategias de `ProcedimientoS3` en ese mundo.

### 12. S3·Interpretar: de lo pensable a la creencia

Orden: Agente → Predicado → Proposición → Sentencia → Lógica → Creencia. `PredicadoProposicion` se divide en dos.

| Componente | Qué es | Ejemplo |
| --- | --- | --- |
| `Predicado` | Esquema de lo pensable: un verbo con huecos sin llenar. Lo que puedo llegar a imaginar. | *comer (agente, paciente, lugar)* |
| `Proposicion` | El predicado con los huecos llenos por entidades del contexto actual. Ya puede ser verdadera o falsa. | *la vaca de ahí alimenta* |
| `Sentencia` | Un agente expresa una proposición con una modalidad: afirma, niega, duda, desea. Lo que dice otro es una sentencia, no una verdad. | *la biblioteca afirma que la seta daña* |
| `Logica` | Combina proposiciones y sentencias para obtener otras nuevas. | — |
| `Creencia` (nuevo) | Lo que el individuo sostiene como cierto, con su trust y sus fuentes. Cierra el círculo: representar, generar, consolidar. | — |

- **Huecos con papeles semánticos** (agente, paciente, instrumento, lugar, tiempo), no sintácticos (CD, CI, CCL): los sintácticos dependen del idioma; S3 piensa conceptos.
- **Fuentes de una creencia:** experiencia propia, herencia, autoridad (dogmas) y **afectiva**, creencias que nacen de S2 y se vuelven relato (razonamiento motivado). Cada una con su peso; todas refutables.
- **Creencia y Verdad:** la creencia es lo que sostengo; la verdad, la meta de S3, es lo que busco.
- **S3·Sentir** se queda con `Comunicacion`. Observar lo que hacen otros (imitación) iría en Interpretar, dentro de `Agente`.

### 13. S3·Reaccionar: Intención, ProcedimientoS3 y después el control

Orden: `Intencion` → `ProcedimientoS3` → `ImpulsoS3`. S3 forma primero su intención y su estrategia; con eso, `ImpulsoS3` decide cuánto intervenir sobre los impulsos de los otros sistemas.

- **Con certeza alta**, sube los impulsos que encajan con su línea de pensamiento y baja los que no. **Sin nada claro**, no toca los impulsos de los otros sistemas.
- **Gradual, no un interruptor:** la fuerza de la modulación es proporcional a la certeza (el trust de sus creencias e intenciones). Así no hay saltos bruscos de conducta en torno a un umbral. Es el control de arriba abajo de la corteza prefrontal.
- **El plan no es un componente:** es el tipo de estrategia propio de S3 (una secuencia de pasos hacia una intención). Lo produce `ProcedimientoS3` apoyándose en la pasada proactiva (las expectativas).

### 14. Cada componente solo produce y modifica piezas de su tipo

- **La Onda lo hace cumplir.** Las piezas solo se crean o modifican mediante operaciones de la Onda, que comprueban que el tipo del componente coincide con el de la pieza y dejan constancia en el metadato *audit*. Hoy no se cumple: `ImpulsoS2` modifica el arousal de candidatos de `Ejecucion` que no produjo (`s2.py:92-96`).
- **El nombre del componente es el tipo de pieza que posee, sin sufijo por sistema.** `Impulso` y `Estrategia` existen en cada sistema y se distinguen por su sistema (`S1.Impulso`, `S3.Estrategia`). Todos los `Impulso` pueden modificar piezas `Impulso` de cualquier sistema.
- **Sustituye nombres de las decisiones 10, 11 y 13:** `ImpulsoS1/S2/S3` pasan a `Impulso`; `ProcedimientoS1/S2/S3` pasan a `Estrategia`, el componente que produce piezas `Estrategia`.
- **Consecuencia:** la modulación de S2 y S3 se hace sobre piezas `Impulso`, no sobre las acciones.

### 15. Atención: frecuencia, amplitud y potencia

| Propiedad de la Onda | Qué es | Hoy |
| --- | --- | --- |
| Frecuencia | Plazo del latido | Igual; se acorta hasta un 30 % con peligro |
| Potencia (nueva) | Recurso total de atención del latido | Lo hace la amplitud, escalada por la energía |
| Amplitud | Anchura del foco: cuántas piezas se atienden | Nuevo significado |

- **Fuerza por pieza = potencia / amplitud:** lo máximo que un componente puede cambiar una pieza en el latido. Foco ancho, mucho a la vista y cambios suaves (calma, exploración). Foco estrecho, poco a la vista y cambios fuertes (peligro, visión de túnel). Base: el modelo de la lente de zoom de Eriksen y el estrechamiento de la atención con el estrés (Easterbrook).
- **Modificar cuesta, en proporción al tamaño del cambio.** Hoy modificar no cuesta nada. Así la gradualidad sale sola: un cambio brusco consume tanta atención que no queda para tocar otras piezas.
- **Nada gratis dentro de los sistemas.** Solo el Core queda exento. Hoy `Patron`, `Agente` y `Predicado` emiten con coste 0.
- **Marcapasos:** el Core crea la Onda con un componente sustituible que recibe los indicadores (el cuerpo y el progreso de cada sistema) y devuelve frecuencia, amplitud y potencia. Por ahora, valores fijos o casi fijos; el algoritmo se decidirá más adelante sin tocar el resto. Hoy esa lógica está en `Soma.presupuesto`.

### 16. Progreso y agotamiento de una estrategia

Una estrategia nace de un impulso: una necesidad que se quiere resolver. **La medida del progreso es la propia necesidad.**

| Dato en la pieza `Estrategia` | Qué es |
| --- | --- |
| Impulso | Referencia al impulso que la originó |
| Valor inicial | Intensidad cruda de la necesidad al empezar |
| Objetivo | Umbral por debajo del cual la necesidad desaparece (p. ej. `umbral_miedo` del arquetipo) |
| Progreso | Cuánto se ha avanzado del valor inicial hacia el objetivo |
| Agotamiento | Crece con tiempo y esfuerzo cuando el progreso es lento; baja cuando es bueno |
| Esfuerzo, latido de inicio | Para el cálculo del agotamiento |
| Estado | Paso actual de la máquina de estados (decisión 17) |

- **Lo calcula y lo actualiza el componente `Estrategia`** de su sistema, dueño de la pieza.
- **Intensidad cruda, no arousal.** S2 y S3 modulan el arousal del impulso; medir sobre él fingiría progreso.
- **Sin cambios bruscos al llegar al objetivo.** La prioridad de la estrategia se apaga de forma gradual al acercarse, en función de varias variables (progreso, agotamiento, objetivo), no de un umbral único.
- **Agotamiento según el teorema del valor marginal** (Charnov): un animal deja una zona de comida cuando su ritmo de ganancia cae por debajo del esperado. Los primeros latidos son de gracia; después, el agotamiento crece si el ritmo de progreso es menor que el esperado. El ritmo esperado de cada estrategia se aprende (conecta con la memoria).

### 17. Estrategia como máquina de estados

- Cada estrategia es un algoritmo determinista: con las variables actuales (y quizá las iniciales) devuelve el siguiente paso, dentro del vocabulario común de acciones. Es un *patrón de acción* en sentido etológico. Hay varias formas de lograr lo mismo: varias formas de huir, explorar, alimentarse, observar, recolectar o construir refugio.
- **En Actuar, un componente `Accion`** (dueño de las piezas `Accion`) toma la estrategia activa de su sistema y emite la acción. Si supera el `Tribunal`, el Core la ejecuta mediante la función del sistema que corresponde a ese verbo y sus parámetros permitidos.
- **Las acciones sobre el exterior dependen del mundo conectado:** la mayoría se definen en el mundo, y la estrategia (también del mundo) traduce sus parámetros. El Core no sabe de coordenadas.

### 18. Recursos de la Onda: prioridad por orden de sistema

- Frecuencia (tiempo máximo para devolver la Onda al Core), amplitud (número máximo de piezas distintas) y potencia (arousal máximo que se puede otorgar) son **máximos que pasan de sistema a sistema**. S1 tiene prioridad sobre S2, y S2 sobre S3: S1 usa lo que necesite, y los demás tienen turno cuando S1 se sacia con los latidos.
- **Cada operación sobre la Onda actualiza lo consumido.** Si se acaba la frecuencia, la Onda vuelve al Core; sin amplitud, no se añaden piezas; sin potencia, no se puede cambiar arousal.
- **Cambiar arousal cuesta potencia, tanto subirlo como bajarlo.** Inhibir también cuesta.
- **Estrés crónico:** S3 puede quedarse sin turno durante mucho tiempo (las noches de Crafter). Es realista (el estrés crónico apaga la corteza prefrontal) y se acepta: el individuo deberá reflexionar de día sobre los miedos de la noche. Sustituye a la cuestión del reparto de la potencia.

## Mapa de componentes

&#91;embedded content: mapa de componentes propuesto · Core y S1–S3\]

Cada latido: Core·Sentir, aprender, S1, S2 y S3 (o dormir), Core·Actuar y cierre. Un componente solo se ejecuta si hay piezas de alguna de sus entradas; los que pone "siempre" no declaran entradas. Solo el `Tribunal` decide: los demás proponen o modulan candidatos.

## Memoria

La memoria se introduce con cuidado: en versiones anteriores, individuos sin memoria lo hicieron mejor. **Cada mecanismo se puede activar y desactivar por separado y se introduce de uno en uno**, comparando siempre contra el control sin memoria (ya disponible como casilla en la antesala). Un mecanismo que no se justifique en los experimentos se apaga sin desmontar nada.

### 19. Guardado: de día se marca, de noche se persiste

- **De día**, el Core marca candidatos a guardar y los puntúa por arousal y progreso, de cada pieza y de cada conjunto de ondas. Van a un **búfer de tamaño fijo**, al que solo se añade (barato, en memoria).
- **De noche**, se persiste y organiza lo mejor puntuado: los episodios (secuencia de ondas) y su integración en el grafo semántico, que es la parte cara (fusionar y reindexar). Un mismo recuerdo puede quedar guardado en un día tranquilo y quedar fuera en un día cargado: compiten por consolidarse.
- **Mundos sin sueño** (hoy Snake y Ajedrez): necesitan otro momento de consolidación, como ratos de calma o el final de una partida. En algunos mundos quizá no tengan sentido ni el sueño ni la memoria, y baste con la reproducción y el linaje.

### 20. Instancias y conceptos

- Se guardan ambos: el concepto (*vaca*), que se mantiene y actualiza, y cada instancia (*esta vaca*).
- **La abstracción la hace el componente dueño del tipo.** `Objeto` crea y mantiene el concepto como un prototipo que se va promediando a partir de las instancias.
- **Ids estables y sin significado**; la etiqueta legible va como metadato. Un id como *vaca\_peligrosa* deja de ser verdad si el individuo aprende que no lo es.

### 21. Mantenimiento: reducción nocturna y repaso

- **Homeostasis sináptica durante el sueño** (Tononi y Cirelli): cada noche se reducen todas las fuerzas en proporción. Se mantienen las diferencias relativas y se poda lo que cae por debajo de un umbral. Resuelve a la vez la sinergia sin freno y la poda por poco uso.
- **Sin repaso, se olvida.** El arousal protege un recuerdo intenso solo al principio. Para que se interiorice, el individuo lo repasa en las horas o días siguientes, en calma y con la memoria activa casi vacía: los componentes traen a la dimensión activa piezas o episodios recientes de alto arousal, y así los refrescan. Es la reflexión de día sobre los miedos de la noche (decisión 18).
- **Riesgo de rumiación:** repasar lo negativo sube su arousal. Lo frenan la reducción nocturna y que repasar solo sea posible en calma y con potencia de sobra.

### 22. Recuperación, memoria única, reconsolidación y herencia

- **Recuperar siempre desde una pieza evocadora** que trae recuerdos semánticos y episódicos a la dimensión activa. La hacen los componentes, con el tiempo que les sobra tras la pasada reactiva. **Las piezas internas también evocan:** el hambre (un `Impulso`) puede traer dónde había comida sin nada a la vista.
- **Una sola memoria.** Cada sistema consulta por sus parámetros, y puede traer piezas relacionadas que no gestiona; así ayuda a los demás de forma pasiva. Leer cualquier tipo es libre; modificar, solo el dueño.
- **Reconsolidación:** un recuerdo recuperado vuelve a ser modificable por su dueño, y los cambios se persisten de noche.
- **Herencia:** pasa la memoria ancestral (dotación innata) y una fracción de lo aprendido por el individuo, configurable por experimento. Biológicamente sería casi 0; para experimentar con pocas generaciones se sube.

## Acciones, elección de estrategia y Tribunal

### 23. Vocabulario, mérito y regla inicial del Tribunal

- **Vocabulario de acciones.** En la versión base, sin mundo, solo acciones internas: esperar, dormir, recordar o reflexionar. El vocabulario exterior lo define cada mundo por completo. El Core aporta solo el mecanismo: la pieza `Accion` (verbo y parámetros) y las funciones que registra cada mundo.
- **Cambiar de estrategia** es poco frecuente cuando una funciona, y depende sobre todo del arquetipo (por ejemplo, más apertura, más exploración).
- **Mérito:** el feedback decide cuánto mérito hay (cuánto progresó el impulso); se lo lleva la estrategia que estaba activa, más la reciente que la antigua; el arousal decide con qué fuerza se aprende. Un éxito intenso se recuerda mejor, pero no se premia a una estrategia que no contribuyó.
- **Regla inicial del Tribunal, a probar al implementar:** puntuación = arousal ya modulado + plus por estrategia activa, acotado y que baja con el agotamiento (p. ej. 0,1 × (1 − agotamiento)). Empate: decide el azar.
- **El plan de migración del código** queda fuera de este borrador. Primera idea del autor: hasta la memoria (componentes y Onda), en una única rama.

## Experiencia proactiva

### 24. Cuatro dimensiones proactivas

Igual que la experiencia reactiva tiene cuatro dimensiones (ei, ev, acc, ef) y la activa dos (semántica y episódica), la proactiva tiene cuatro, de más barata a más cara:

| Dimensión | Qué es | Horizonte | Sobre todo en | Cómo vuelve a lo reactivo |
| --- | --- | --- | --- | --- |
| Expectativa | Predicción de lo que va a llegar | Siguiente latido | Todos (S1: lo que sentiré; S2: lo que me hará sentir) | Se compara con lo que entra; la sorpresa da arousal y feedback |
| Prospectiva | Algo que hacer cuando ocurra cierta cosa (*al anochecer, al refugio*) | Hasta que se cumpla la condición | S2 y S3 | Al cumplirse, entra como pieza evocadora |
| Plan | Cadena de pasos hacia una intención | Medio plazo | S3 | Lo consume `Estrategia` paso a paso |
| Imaginación | Ensayar escenarios sin ejecutarlos (*¿y si…?*) | Libre | S3, solo en calma y con potencia de sobra | Se puede guardar, marcado como imaginado y con trust bajo |

- **Base:** el procesamiento predictivo (el cerebro aprende y atiende sobre todo al error de predicción) y la memoria prospectiva de la psicología.
- **La prospectiva resuelve la anticipación de la noche:** basta con un recordatorio que se dispara solo, sin prever cada latido.
- **Lo imaginado va marcado como tal**, para no confundirlo con lo vivido.
- **Orden de implementación:** primero Expectativa y Plan; después Prospectiva e Imaginación.

## Cuestiones abiertas

- [ ] **Tamaño del plus por estar activa.** Debe ser menor que la diferencia entre el arousal de una necesidad crítica y el de una estrategia tranquila; si no, una sed crítica no gana (fallo de la Fase 5).
- [ ] **Repertorio de estrategias.** Propuesta: una lista fija e innata por sistema y mundo, y se aprende cuál usar. Inventar estrategias nuevas, más adelante y en S3.
- [ ] **Qué estrategias corresponden a cada sistema.** Propuesta: S1, patrones innatos o habituales (buscar, huir, quedarse quieto); S2, por valor (volver al hogar, buscar refugio); S3, por conocimiento (planes como la cadena de recetas de `PlanTecnologico`).
- [ ] **Coste.** Una etapa más por sistema consume presupuesto, y S1 debe seguir siendo rápido. Que la estrategia persista entre latidos lo reduce.

* [ ] **Foco voluntario.** ¿Puede S3 estrechar el foco a voluntad (concentrarse), o solo lo fija el cuerpo? Propuesta: empezar solo con el cuerpo.

## Registro de cambios

| Fecha | Cambio |
| --- | --- |
| 2026-11-15 | Creación del borrador: mapa de `main`, renombrar `Escena`, separar pulsión y procedimiento, `Procedimiento` en S1. |
| 2026-11-15 | Decisión 3: niveles impulso, estrategia, acción y decisión; Actuar en cada sistema; Ejecucion pasa a Accion; estrategias propias de cada mundo. Cuestiones abiertas actualizadas. |
| 2026-11-15 | Decisiones 4 a 7: continuidad de la estrategia activa, progreso por sistema, reflejo ante cambios bruscos, metadatos de las piezas. Dos cuestiones nuevas: dónde garantizar progreso y agotamiento, e interrupción por otra necesidad. |
| 2026-11-15 | Decisión 4 ampliada: tipo de pieza Estrategia en el Core sin etapas nuevas; la interrupción por otra necesidad se resuelve por arousal. Nueva cuestión: tamaño del plus. |
| 2026-11-15 | Decisión 8: Objeto como entidad propia con prototipo en S1·Interpretar; Imagen y Objeto pueden ser Sujeto; solo Objeto puede ser Agente. Mapa actualizado. |
| 2026-11-15 | Entidades y papeles; habituación en Supervivencia. Decisión 9: Emoción en S2·Sentir; Valor como única relación con cuatro dimensiones. Mapa actualizado. |
| 2026-11-15 | Decisión 10: S2·Reaccionar con Exteriorizacion, ImpulsoS2 y ProcedimientoS2; Curiosidad pasa a impulso y Hogar a estrategia compartida. Mapa actualizado. |
| 2026-11-15 | Decisiones 11 y 12: Intención y ProcedimientoS3; S3·Interpretar con Predicado, Proposición, Sentencia, Lógica y Creencia. Nueva cuestión: el freno de S3. Mapa actualizado. |
| 2026-11-15 | Decisión 13: S3·Reaccionar con Intencion, ProcedimientoS3 e ImpulsoS3 como control gradual según la certeza. Cerrada la cuestión del freno; abierta la del nombre de ImpulsoS3. |
| 2026-11-15 | Decisiones 14 y 15: propiedad de las piezas por tipo; Impulso y Estrategia sin sufijo; frecuencia, amplitud y potencia; coste proporcional al cambio; Marcapasos. Mapa con nombres sin sufijo. |
| 2026-11-15 | Nueva sección de memoria: propuesta inicial del autor y dudas del revisor. |
| 2026-11-15 | Decisiones 16 a 18: progreso y agotamiento en la pieza Estrategia; estrategia como máquina de estados con componente Accion; recursos de la Onda por prioridad de sistema. Cerradas las cuestiones de medición del progreso y reparto de la potencia. |
| 2026-11-15 | Memoria: decisiones 19 a 22 (guardado día/noche, instancias y conceptos, reducción nocturna y repaso, recuperación, memoria única, reconsolidación y herencia). Sustituye la propuesta inicial y sus dudas. |
| 2026-11-15 | Decisión 23: vocabulario de acciones, mérito y regla inicial del Tribunal. El indicador por sistema se llama feedback. Nueva sección de siguientes temas. |
| 2026-11-15 | Decisión 24: cuatro dimensiones proactivas. Borrador cerrado. |
