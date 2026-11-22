# IdA: recuperar el diseño por Componentes y hoja de ruta

**Estado de partida:** `main` en `eaeadaa` (etiqueta `crafter-general-v4`), 22/11/2026.
**Para quién es:** cualquier persona o agente que continúe el proyecto. Reúne lo que hay que saber para retomarlo sin el historial de conversaciones.

> **Estado (22/11/2026, tarde).** La sección 0 está resuelta en [`DISENO_COMPONENTES.md`](DISENO_COMPONENTES.md), que también sustituye los pasos R1 a R7 por las fases A y B (sección 5 de ese documento). De este plan siguen vigentes el diagnóstico (secciones 1 a 4), R0, la validación (V1 a V3), las mejoras (M1 a M7, con M1 reformulado) y el método de trabajo (secciones 8 y 9).

---

## Antes de nada: aviso para quien continúe

Este documento lo escribió el asistente de diseño al final de una conversación muy larga. El 22/11/2026, revisándolo con el autor, se vio que **la desviación del diseño original es mayor de lo que se pensaba**: no solo dónde están las piezas, sino también algunos conceptos.
- Ejemplo: el asistente creía que Reaccionar debía ser solo general y que Actuar contenía programas motores; las dos ideas eran erróneas.
- **Lo primero no es la auditoría (R0), sino fijar con el autor los conceptos originales de IdA.** Hay que partir de su palabra y de `doc-repositorio/`, no de este documento ni del código actual.
- Las secciones 1.1, 1.2 y 4.2 recogen las aclaraciones del autor de ese día. El resto del documento (el diagnóstico de la sección 3 y los pasos R1–R7) es una **propuesta**, que se revisa una vez fijados los conceptos.
- Las preguntas pendientes están en la sección 0.

## 0. Conceptos que hay que fijar con el autor antes de empezar

### 0.1 Ya aclarado por el autor (22/11/2026)

- **IdA = Core + S1, S2 y S3**, con la Onda (frecuencia, amplitud, potencia) y la Experiencia (reactiva, activa, proactiva) como flujo. Eso es el núcleo real.
- **El Core (S0) solo tiene Sentir** (`Interocepcion`, `Exterocepcion`, `Propiocepcion`) **y Actuar.**
- **Dentro de cada módulo están los Componentes,** que se quitan y se ponen. Hay Componentes generales y Componentes propios de cada mundo, más parámetros de cada mundo para las constantes.
- **El reto:** separar lo biológicamente general de lo exclusivo de cada mundo. Las mecánicas de Crafter (cuadrícula 2D, casillas, cavar) están bien hechas, pero deben vivir en Componentes de Crafter, que solo se activan en Crafter.
- **Reaccionar:** las estrategias posibles como respuesta a lo sentido y lo interpretado. Por ejemplo, ante un peligro, huir o atacar; ante un recurso, tomarlo u omitirlo porque se está saciado. Pueden ser generales o propias de un mundo. No son procedimientos escritos a mano.
- **Actuar:** la aceptación de ejecutar una acción concreta de la estrategia decidida.
- **Lo aprendido, y cómo afecta a la conducta, es exclusivo de cada mundo.**

### 0.2 Preguntas abiertas (resolver con el autor antes de la auditoría)

1. **¿`Peticion` y `Anticipacion` pertenecen a Actuar?** La fase las añadió a Actuar en S1 y S2. Si Actuar es solo aceptar la ejecución:
   - anticipar parece Interpretar (lo que va a pasar);
   - pedir algo a otro sistema parece una respuesta de Reaccionar.
2. **¿Qué es la Memoria en el diseño?** No es un módulo ni un Componente. Hoy es una estructura compartida (`ida/core/memoria.py`) a la que la fase añadió requisitos de acción, qué satisface cada necesidad, el mapa local, el modelo del cuerpo, las transformaciones y las metas.
   - ¿Es la base de la Experiencia (reactiva, activa, proactiva)?
   - ¿O lo aprendido debería vivir en los Componentes que aprenden, con la Memoria solo como almacén?
   - ¿Cómo encaja aquí el legado entre generaciones dentro de un mismo mundo?
3. **¿Dónde va una percepción propia de un mundo?** Por ejemplo, el mapa local de Crafter: ¿como variante de `Exterocepcion` en el Core, o como Componente de Crafter en S1 · Sentir, junto a `Imagen`? Hipótesis: el Core da las sensaciones en bruto y Sentir las organiza. **Sin confirmar.**
4. **¿Dónde va el peligro aprendido?** Hoy es `ida/core/peligro.py` y se calcula antes de Sentir. Depende de las preguntas 2 y 3.
5. **¿Cómo se reparte la amplitud entre sistemas?** Hoy S1, S2 y S3 corren en orden y consumen la amplitud por turnos, así que S3 se queda sin sitio (M1). ¿Es intencionado que la supervivencia vaya primero y pueda dejar sin atención a la razón? ¿O el diseño preveía un reparto?
6. **¿Qué otros conceptos se han desviado?** Conviene repasar con el autor, Componente a Componente, la tabla de la sección 1.1 y los añadidos de la sección 2.3, comparándolos con su intención original antes de clasificar nada.

**Orden propuesto:**
1. resolver 0.2 con el autor;
2. actualizar `doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md` con lo resuelto, que es la fuente de verdad;
3. revisar las secciones 3 a 5 de este documento;
4. solo entonces, la auditoría (R0).

---

## Índice

1. Qué es IdA (lo esencial del diseño)
2. Dónde estamos: la fase de generalización en Crafter
3. El problema: cómo nos alejamos del diseño por Componentes
4. El objetivo y sus reglas
5. Plan de trabajo: la reorganización (R0 a R7)
6. Después de la reorganización: validar la generalidad (V1 a V3)
7. Después: seguir mejorando (M1 a M7)
8. Método de trabajo (cómo se mide, se decide y se fusiona)
9. Referencia rápida (ficheros, herramientas, cifras, etiquetas)

---

## 1. Qué es IdA

IdA es un **framework de agente autónomo bioinspirado**. Un núcleo genérico, inspirado en cómo resuelven los seres vivos el problema de seguir vivos, al que se conectan **mundos** como adaptadores: mínimo, archivos, Snake, Crafter y ajedrez. Documentación base:
- `doc-repositorio/01_FILOSOFIA_Y_BIOLOGIA.md`;
- `doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md` (la de referencia para este documento);
- `doc-repositorio/03_LOS_MUNDOS.md`;
- `doc-repositorio/04_GUIA_TECNICA_Y_PATRONES.md`.

### 1.1 El núcleo

**El Core** (a veces llamado S0) solo tiene dos módulos:
- **Sentir:** `Interocepcion` (las constantes vitales), `Propiocepcion` (dónde está y qué lleva), `Exterocepcion` (lo que percibe fuera) y `Ambiente` (condiciones del entorno, como la luz);
- **Actuar:** el `Tribunal` (elige una acción por latido) y los actuadores.

**Los tres sistemas cognitivos** tienen cada uno los módulos Sentir, Interpretar, Reaccionar y Actuar:

| Módulo | S1 · Supervivencia | S2 · Valor | S3 · Verdad |
|---|---|---|---|
| Sentir | `Imagen` | `Patron`, `Emocion` | `Comunicacion` |
| Interpretar | `Objeto`, `Supervivencia` | `Sujeto`, `Valor` | `Agente`, `Predicado`, `Proposicion`, `Sentencia`, `Logica`, `Creencia` |
| Reaccionar | `Reflejo`, `Impulso`, `Feedback`, `Estrategia` | `Exteriorizacion`, `Impulso`, `Feedback`, `Estrategia` | `Intencion`, `Impulso`, `Feedback`, `Estrategia` |
| Actuar | `Accion` | `Accion` | `Accion` |

**El flujo:**
- la **Onda** de cada latido, con su frecuencia (el plazo; si se pasa, corta la guillotina), su amplitud (cuántas piezas caben en la atención) y su potencia (cuánto arousal se puede dar o cambiar);
- la **Experiencia**, con sus dimensiones reactiva, activa y proactiva.

El orden de los sistemas es siempre S1 → S2 → S3.

### 1.2 Los Componentes

**Dentro de cada módulo están los Componentes: las piezas que se quitan y se ponen.** Unos son **generales** (todos los mundos) y otros son **propios de cada mundo** (los registra el mundo). Además, cada mundo tiene **parámetros** propios (`Perfil`) para fijar constantes acordes a su escala.

Lo dice el propio documento de arquitectura: *«las estrategias genéricas viven en `ida/sistemas`; las propias de cada mundo, en `ida/mundos/<mundo>` (`Mundo.estrategias_propias`)»*.

Otras reglas del diseño:
- **Propiedad:** cada Componente solo emite y modifica piezas de su tipo, a través de la Onda.
- **Acciones:** solo los Componentes `Accion` proponen acciones, y cada una lleva su origen (impulso y estrategia).

---

## 2. Dónde estamos: la fase de generalización en Crafter

### 2.1 Qué se buscaba

Crafter es un benchmark público (Hafner, 2021). Su métrica es la **Crafter Score**: la media geométrica de las tasas de éxito de 22 logros. Hasta la fase C, IdA jugaba a Crafter con **estrategias escritas para Crafter** (`RefugioNocturno`, `PlanTecnologico`, `DefensaArmada`, `CerrarDistancia`): un 19,2 %, que ya superaba a DreamerV2 (10,0 %). Pero esa cifra medía sobre todo lo que sabía el programador.

La fase de generalización (`docs/FASE_GENERALIZACION_CRAFTER.md`) buscaba que esa capacidad saliera de la base y no de la conducta escrita. El argumento de IdA no es la Score, sino **cero entrenamiento, conducta explicable y generalidad**.

### 2.2 Qué se consiguió, medido paso a paso

Protocolo oficial abreviado: 100 000 pasos, vista local 9×7, sin herencia y manual estricto. Semillas base 31 y 32.

| Hito | Score (semillas 31 / 32) | Qué aportó | Documento |
|---|---|---|---|
| Suelo: núcleo sin conducta de Crafter | 1,45 % | — | `docs/MEDICION_CIERRE_PASO0.md` |
| Pasos 2 y 5: manual declarativo y planificador | 8,81 % | Fabrica: mesa, pico, piedra, horno | `docs/MEDICION_PASO5_PASO0.md` |
| Paso 0b: aliestesia; arreglo del retoño | 11,29 / 11,05 % | Supera a DreamerV2 | `docs/MEDICION_CIERRE_PASO0.md` |
| Paso 3: proteger X (refugio general) | 12,82 / 13,58 % | Sobrevive a la noche (`wake_up` ×5) | `docs/MEDICION_CIERRE_PASO3.md` |
| Paso 6: defensa general | 14,04 / 15,45 % | Aprende que las flechas vienen de los esqueletos | `docs/MEDICION_PASO6.md` |
| Deuda 14: lote por estación | 14,83 / 15,98 % | Cadena de herramientas | `docs/MEDICION_DEUDA14.md` |
| 11c: material desde el mapa local | **15,86 / 17,34 %** | Busca lo que recuerda | `docs/MEDICION_MATERIAL_MAPA.md` |
| *Referencia: línea procedimental* | *19,18 %* | *Conducta escrita para Crafter* | etiqueta `crafter-procedimental-v1` |

**Retirados por resultado nulo o negativo** (documentados): la urgencia local en el Tribunal (0a), la alostasis de hambre y sed (3b), la factibilidad temporal de la deuda 11 (11a, en la rama `feature/deuda11` sin fusionar) y el aprovechamiento de estación (14.3).

**Referencias de la literatura** (Crafter Score, 1M de pasos salvo que se indique):
- humanos expertos, 50,5 %;
- SPRING (GPT-4 leyendo el artículo, sin entrenamiento), 27,3 %;
- DreamerV2, 10,0 %; PPO, 4,6 %; aleatorio, 1,6 %.

En la tabla del README de Crafter, IdA corresponde a la categoría **External Knowledge** (con las columnas «Uses» e «Interaction»).

### 2.3 Lo que la fase dejó en el código

Los sistemas, tal como están montados hoy (`ida/sistemas/s1.py:836`, `s2.py:453` y `s3.py:1026`), con lo que añadió la fase en negrita:

| Sistema y módulo | Componentes |
|---|---|
| S1 · Interpretar | `Objeto`, `Supervivencia`, **`Apetencia`**, **`Recinto`** |
| S1 · Reaccionar | `Reflejo`, `Impulso`, `Feedback`, `Estrategia`; en su catálogo, **`Afrontar`**, **`Proteger`**, **`SalirDelRecinto`** |
| S1 · Actuar | `Accion`, **`Peticion`**, `Anticipacion` (bloque F, anterior a la fase) |
| S2 · Actuar | `Accion`, **`Peticion`**, `Anticipacion` (bloque F, anterior a la fase) |
| S3 · Reaccionar | catálogo con **`PerseguirMetas`** (planificador, lote por estación, material desde el mapa) |
| **Core** | **`ida/core/peligro.py`** (peligro aprendido, que se calcula antes de Sentir) |
| **Memoria** (`ida/core/memoria.py`) | **requisitos de acción, `satisface` (aliestesia), mapa local, modelo del cuerpo (`aprender_cuerpo`), transformaciones, metas, manual** |

El adaptador de Crafter (`ida/mundos/crafter.py`) no tiene estrategias propias (`estrategias_propias()` vacío, vigilado por `test_crafter_no_escribe_conducta`).

---

## 3. El problema: cómo nos alejamos del diseño por Componentes

### 3.1 Qué pasó

El documento de la fase formuló así el «pilar 1»: *«el mundo solo percibe, actúa y declara hechos»*, con el criterio de aceptación de que `estrategias_propias()` de Crafter **quedara vacía**.

El problema de la fase C era real, pero se diagnosticó mal:
- **Lo malo no era que Crafter tuviera Componentes propios, ni siquiera estrategias propias.** Lo malo era que esas estrategias eran **procedimientos escritos a mano**: `RefugioNocturno` tenía fases, la hora del anochecer y sus motivos fijados de antemano, en lugar de responder a lo sentido y lo interpretado.
- **Se corrigió de más.** En lugar de «las estrategias de un mundo responden a lo sentido e interpretado, no siguen un guion», se estableció «el mundo no tiene Componentes».

Con eso, todo lo propio de la mecánica de Crafter que hacía falta (cuadrícula 2D, orientación, cavar, colocar, recintos) acabó en los **sistemas generales** y en el **Core**.

### 3.2 Los síntomas en el código

1. **Mecánica de Crafter en Componentes generales:** `Recinto` (`ida/sistemas/proteger.py`, 879 líneas) contiene la geometría de cuadrícula, los 4 vecinos, la orientación, el buscador de posturas («qué secuencia de MOVER me deja en A mirando a C»), cavar y cerrar accesos. Está registrado como Componente general de S1 · Interpretar.
2. **Activaciones condicionales para que no actúe en otros mundos:**
   - la aliestesia solo actúa si dos necesidades comparten rasgo (`Perfil.aliestesia`, propiedad calculada, `ida/core/mundo.py:139`);
   - el peligro aprendido solo se calcula si el mundo no da su propio `peligro`;
   - `Afrontar` solo actúa con ese peligro;
   - `Proteger` solo actúa si existe la necesidad `cobijo`.

   En el diseño de IdA, esto se resuelve con que **cada mundo registre los Componentes que le corresponden**.
3. **Cognición dentro del Core:** `ida/core/peligro.py` (428 líneas) aprende el daño, el alcance, los emisores y la eficacia, y calcula el peligro antes de Sentir. El Core debería tener solo Sentir y Actuar, más la Onda y la Experiencia.
4. **Supuestos de un cuerpo concreto dentro de `Memoria`:** el modelo del cuerpo (`aprender_cuerpo`: si avanza, si gira), la casilla de «delante» en los requisitos, y el mapa local métrico.
5. **Constantes de la escala de Crafter en Componentes generales.** Por ejemplo:
   - en `proteger.py`: `ALCANCE_SITIO` = 15, `CANDIDATOS_EXACTOS` = 6, `MAX_INTERIOR` = 3, `MAX_ESTADOS` = 6000 y `COSTE_SIN_SITIO`;
   - en `peligro.py`: `DANO_PREVIO` = 2/9 de la vitalidad, `MARGEN_LUGAR` = 3 y `GOLPES_PREVIO` = 10.

### 3.3 Por qué importa

- **Hemos demostrado que los otros mundos no se rompen** (`invariancia.py` da OK en mínimo, archivos y ajedrez en todos los pasos), **pero no que la base generalice**. Los mecanismos nuevos simplemente no se activan allí.
- **Cuando llegue un mundo nuevo,** no se podrá saber qué pieza le sirve y cuál no. Habrá que leer el código para descubrir qué supone cada una.
- **Contradice el principio biológico de IdA.** Un organismo tiene dinámicas generales (necesidades, anticipación, aprendizaje, valoración, decisión) y un cuerpo concreto con su forma de moverse y de actuar sobre su entorno. Un pez y un ratón comparten el miedo y el hambre, pero no la forma de esconderse.

---

## 4. El objetivo y sus reglas

### 4.1 Objetivo

**Devolver cada pieza a su sitio dentro del diseño por Componentes de IdA, sin perder ni una décima de la Score actual.** Es decir:
- el **núcleo** (Core, sistemas, Onda, Experiencia) solo contiene lo que es del núcleo;
- los **Componentes generales** (en `ida/sistemas`) contienen las dinámicas biológicamente generales;
- los **Componentes de Crafter** (en `ida/mundos/crafter/`) contienen la mecánica propia de Crafter, y solo se activan porque Crafter los registra;
- los **parámetros de Crafter** (su `Perfil`) fijan las constantes que dependen de su escala.

### 4.2 El pilar 1, bien formulado

> **Cada módulo puede tener Componentes generales y Componentes propios del mundo. Lo que no se admite en ningún módulo es un procedimiento escrito a mano que sustituya a la percepción y a la valoración.**

| Módulo | ¿Componentes propios del mundo? | Qué aportan |
|---|---|---|
| Sentir | Sí | Cómo se percibe ese entorno |
| Interpretar | Sí | Cómo se comprende: por ejemplo, qué recintos son posibles aquí y cuánto cuestan |
| Reaccionar | Sí | Qué respuestas existen en ese mundo ante lo sentido e interpretado (huir o atacar, tomar u omitir un recurso, cerrar un refugio). Cuál se toma lo decide el estado del organismo (necesidades, intensidad, peligro, saciedad) y el Tribunal, no un guion |
| Actuar | Sí, si hace falta | La aceptación de ejecutar una acción concreta de la estrategia decidida (`Accion` propone y el `Tribunal` del Core acepta una por latido). Las acciones concretas, como la secuencia de cavar, ir, orientarse y cerrar, las genera la estrategia en Reaccionar, no Actuar |

**Qué distingue una estrategia válida (general o de un mundo) de un procedimiento escrito:**
1. **Se activa por lo sentido e interpretado:** piezas de la Onda (impulsos, necesidades, interpretaciones). Nunca por el número de paso, el reloj del mundo ni una fase fijada de antemano.
2. **Puede omitirse:** según el estado, la respuesta puede no darse. Por ejemplo, un recurso se omite si el organismo está saciado.
3. **Compite en el Tribunal** con las demás propuestas, con la misma puntuación que cualquier otra.
4. **Sus umbrales son parámetros del mundo o se aprenden.** No hay números mágicos dentro de la estrategia.

Por ejemplo, `RefugioNocturno` incumplía los criterios 1 y 4 (la hora del anochecer y las fases fijas). `Afrontar` (huir o atacar según el daño esperado y la salud) los cumple todos.

**Lo aprendido es de cada mundo.** El mecanismo de aprender puede ser general, pero lo aprendido en un mundo (la memoria, el legado, el peligro aprendido, qué satisface cada necesidad) y cómo afecta a la conducta pertenecen a ese mundo:
- el mundo decide si se activa, registrando los Componentes que lo usan;
- lo aprendido nunca pasa de un mundo a otro.

### 4.3 Frontera entre lo general y lo del mundo

El criterio es **si valdría para cualquier organismo o depende de este mundo y de este cuerpo**:
- **General:** tengo necesidad de cobijo y anticipo que crece; este sitio cuesta tanto; luchar o huir; tomar u omitir según la saciedad; el mecanismo de aprender qué satisface cada necesidad; encadenar medios y fines; el mecanismo de aprender qué daña y desde dónde.
- **Del mundo:** cómo es aquí un sitio protegido (en Crafter, cavar y cerrar accesos en una cuadrícula); qué respuestas propias tiene este cuerpo; cómo se mueve (avanzar o girar); qué significa «delante» o «cerca»; a qué distancia se mide; qué mecanismos de aprendizaje se activan en este mundo.

En el lenguaje de Gibson: **el mundo ofrece afordancias y el organismo elige entre ellas.**

### 4.4 Condición innegociable: equivalencia exacta

Toda la reorganización es una **refactorización pura**. En cada paso:
- con `--plazo-logico 40`, el JSON de `evaluar_crafter.py` (3000 pasos, semillas 31 y 32) es **idéntico** al de `main`, ignorando `tiempo_segundos`, `ms_por_paso` y `plazo_logico`;
- `invariancia.py` da OK en los cuatro mundos;
- ruff, mypy y pytest en verde.

Al final de la reorganización, la medición completa de 100 000 pasos (semillas 31 y 32) debe repetir **campo a campo** `datos/evaluacion/mapa_31.json` y `mapa_32.json`.

---

## 5. Plan de trabajo: la reorganización

Cada paso va en su rama, con su PR y su comprobación de equivalencia. Ningún paso cambia la conducta.

### R0. Auditoría (sin cambiar código)

**Entregable:** `docs/AUDITORIA_COMPONENTES.md`, en una rama `docs/auditoria-componentes`.

Recorre todo lo que la fase añadió o cambió en `ida/core` e `ida/sistemas` (`git log crafter-procedimental-v1..main -- ida/core ida/sistemas`). Para cada clase, función y constante relevante:
- fichero y línea; qué hace, en una frase;
- en qué sistema y módulo está, y si es un Componente o algo fuera del modelo de Componentes (código en el Core, en `Memoria`, en `latido.py`…);
- **clasificación propuesta:** NÚCLEO, COMPONENTE GENERAL, COMPONENTE DE MUNDO o PARÁMETRO DE MUNDO, y por qué;
- en qué módulo debería vivir según la regla 4.2, y si la incumple;
- si está **mezclado** (una parte general y otra del mundo), cómo se partiría;
- supuestos sobre el mundo: cuadrícula, vecinos, orientación, «delante», inventario, estaciones, posiciones, día y noche, escala.

**Listas aparte:**
1. **Todas las activaciones condicionales e interruptores** que existen para que algo no actúe en otros mundos, y qué registro de Componentes de mundo los sustituiría. Incluye los interruptores de los bloques E y F en `MecanismosMemoria`, aunque sean anteriores a la fase.
2. **Todo lo cognitivo que esté en `ida/core`** (`peligro.py`, partes de `latido.py`, partes de `memoria.py`) y dónde debería ir.
3. **Las constantes que deberían ser parámetros del mundo,** y de qué propiedad del mundo derivarían (radio de visión, tamaño del mapa, vitalidad máxima…).
4. **Dependencias:** qué partes del núcleo leen hoy algo que pasaría a ser del mundo. Por ejemplo, el Core lee el `peligro` antes de que corra S1 para la saliencia, la alarma al dormir y el mapa.

**Al final:** un resumen de cuánto cae en cada categoría, y los riesgos de la reorganización.

#### Prompt para el agente de implementación (conversación nueva)

```text
Responde siempre en español.

Contexto: trabajas en IdA (repo diegorodriguezreija/IdA), un framework de agente autónomo
bioinspirado. Parte de main (etiqueta crafter-general-v4). Lee primero, en este orden:
1. doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md (el diseño: Core con Sentir y Actuar;
   S1, S2 y S3 con Sentir, Interpretar, Reaccionar y Actuar; Onda y Experiencia; Componentes
   generales en ida/sistemas y propios de cada mundo en ida/mundos/<mundo>).
2. docs/PLAN_COMPONENTES_Y_HOJA_DE_RUTA.md, secciones 3 y 4 (el problema y la regla:
   cualquier módulo puede tener Componentes generales y de mundo; ninguna estrategia puede
   ser un procedimiento escrito: se activa por lo sentido e interpretado, puede omitirse,
   compite en el Tribunal y sus umbrales son parámetros o aprendidos; lo aprendido y su
   efecto son de cada mundo; las constantes de escala son parámetros del mundo).
3. docs/FASE_GENERALIZACION_CRAFTER.md (qué se hizo en la fase y por qué).

Tarea: la auditoría R0 descrita en la sección 5 del plan. NO cambies código. Crea la rama
docs/auditoria-componentes y escribe docs/AUDITORIA_COMPONENTES.md.

Alcance: todo lo que añadió o cambió la fase en ida/core e ida/sistemas
(git log crafter-procedimental-v1..main -- ida/core ida/sistemas), más los interruptores
de MecanismosMemoria y las activaciones condicionales aunque sean anteriores.

Para cada clase, función y constante relevante, una fila con: fichero:línea; qué hace (una
frase); dónde vive hoy (sistema y módulo, o fuera del modelo de Componentes); clasificación
(NÚCLEO / COMPONENTE GENERAL / COMPONENTE DE MUNDO / PARÁMETRO DE MUNDO) y por qué; dónde
debería vivir según la regla; si está mezclada, cómo se partiría; qué supone sobre el mundo
(cuadrícula, vecinos, orientación, «delante», inventario, estaciones, día y noche, escala).
Para cada estrategia (general o no), indica además si cumple los cuatro criterios de 4.2.

Listas aparte: (1) activaciones condicionales e interruptores y el registro que los
sustituiría; (2) cognición dentro de ida/core; (3) constantes que deberían ser parámetros
del mundo y de qué propiedad del mundo derivarían; (4) dependencias: qué lee el núcleo que
pasaría a ser del mundo (p. ej., el peligro antes de Sentir para saliencia, alarma y mapa).
Termina con un resumen por categoría y los riesgos para la equivalencia exacta.

Reglas: cita siempre fichero:línea; si dudas de una clasificación, márcala como DUDA con los
argumentos de cada lado, no la fuerces. No ejecutes mediciones. Usa .venv\Scripts\python.exe
si necesitas ejecutar algo, no instales nada. Haz commit en tu rama y súbela; nunca push a main.
Al terminar, resume en 10 líneas lo más importante y las decisiones que necesitan al autor.
```

### R1. Diseño de la reorganización (a partir de R0)

**Entregable:** `docs/DISENO_COMPONENTES.md`. Decisiones a tomar:

1. **Cómo registra un mundo sus Componentes.** Generalizar `Mundo.estrategias_propias()` a un registro por sistema y módulo. Por ejemplo, `Mundo.componentes_propios() -> {"S1": {"Interpretar": [...], "Actuar": [...]}}`, Se permiten Componentes de mundo en los cuatro módulos, incluidas estrategias propias en Reaccionar, siempre que cumplan los criterios de 4.2.
2. **Estructura de ficheros del mundo:** `ida/mundos/crafter/` como paquete (adaptador, manual, componentes y parámetros).
3. **Componentes reutilizables por una familia de mundos** (por ejemplo, la cuadrícula 2D con orientación, que también usarían MiniGrid u otros): cómo se comparten sin que sean generales. Por ejemplo, en `ida/mundos/comun/cuadricula.py`, registrados por cada mundo que los use.
4. **El peligro:**
   - lo general (aprender daño, emisores y eficacia, por contingencia) va a un Componente de S1 · Interpretar, probablemente junto a `Supervivencia`;
   - lo del mundo (distancia, contacto, alcance en casillas) va a un Componente de mundo o a parámetros;
   - hay que decidir cómo leen el Core y la Onda el peligro (saliencia, alarma) si ya no se calcula antes de Sentir. Por ejemplo, del latido anterior (`ei`), como hacen otros sistemas.
5. **`Memoria`:** qué estructuras son memoria general (requisitos, `satisface`, metas, transformaciones, el mapa como «lugares y rutas») y cuáles son de un cuerpo concreto (el modelo de movimiento, la casilla de «delante», el mapa métrico). Cómo se separan sin romper la herencia (legado).
6. **`Recinto` y `Proteger`:**
   - `Proteger` (cuándo y por qué, con la intensidad anticipada del cobijo) queda general en S1 · Reaccionar;
   - `Recinto` (qué sitios son posibles y cuánto cuestan) pasa a ser un Componente de Crafter en S1 · Interpretar;
   - cómo se ejecuta en Crafter (cavar, ir, orientarse, cerrar) pasa a una estrategia de Crafter en S1 · Reaccionar, que propone las acciones concretas a `Accion`. Otra opción es que esa estrategia de Crafter sustituya del todo a `Proteger` general: hay que decidir cuál de las dos respeta mejor los criterios de 4.2;
   - la interfaz entre ellos es **una pieza de tipo «afordancia de protección»**, con su coste, confianza, requisitos y primera acción.
7. **Las activaciones condicionales** se sustituyen por registro: la aliestesia, el peligro aprendido, `Afrontar` y `Proteger` se activan porque Crafter registra lo que necesitan, no por una condición dentro del Componente. Como lo aprendido y su efecto son de cada mundo (4.2), los mundos que hoy no los usan siguen sin registrarlos, así que la reorganización no cambia su conducta. Si más adelante otro mundo los quiere, se decide en M3.
8. **Parámetros:** qué constantes pasan al `Perfil` de cada mundo y con qué valores por defecto. Los valores de Crafter deben ser los de hoy, para que la equivalencia se cumpla.
9. **El orden de los pasos R2-R6** y cómo se comprueba cada uno.

### R2. El registro de Componentes de mundo

Implementar el registro decidido en R1. Sin mover nada todavía: con el registro vacío, **todo idéntico**.

**Test nuevo:** un mundo de prueba registra un Componente en cada módulo (incluida una estrategia en Reaccionar). Se comprueba que se montan en su sistema y módulo, y que la estrategia compite en el Tribunal como las generales.

### R3. Sacar la cognición del Core

Mover lo general de `ida/core/peligro.py` a un Componente de S1 · Interpretar, y lo propio de Crafter a sus Componentes o parámetros. Equivalencia exacta.

### R4. La mecánica de Crafter, a Componentes de Crafter

Mover `Recinto`, el modelo del cuerpo, el buscador de posturas, «delante», el mapa métrico y lo demás que la auditoría clasifique como de mundo, a `ida/mundos/crafter/` (o a un módulo común de cuadrícula), registrados por Crafter. Equivalencia exacta.

### R5. Activaciones condicionales y parámetros

- Sustituir las activaciones condicionales por registro.
- Pasar las constantes de escala al `Perfil` de Crafter.

Equivalencia exacta.

### R6. El pilar 1, actualizado y vigilado

- `test_crafter_no_escribe_conducta` se sustituye por tests de los criterios de 4.2 que se puedan comprobar de forma automática. Por ejemplo: que las estrategias de un mundo no lean el número de paso ni el reloj del mundo, solo piezas de la Onda; y que sus constantes estén en el `Perfil`. El resto de criterios se revisa en cada PR.
- `test_pureza` se amplía: `ida/core` e `ida/sistemas` no importan nada de `ida/mundos`, y ningún Componente general menciona conceptos de un cuerpo concreto. Revisar qué se puede comprobar de forma automática.
- Actualizar `doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md` (tabla de Componentes, con los nuevos), `docs/FASE_GENERALIZACION_CRAFTER.md` (el pilar 1 reformulado) y `docs/INVENTARIO_CONOCIMIENTO_CRAFTER.md`.

### R7. Comprobación final de la reorganización

- **Medición completa:** 100 000 pasos, semillas 31 y 32, `--plazo-logico 40`. Debe repetir campo a campo `mapa_31.json` y `mapa_32.json`.
- **Benchmark completo de mínimo y archivos** frente a `ref_generalizacion`: idéntico.
- PR, fusión y etiqueta (`crafter-general-v5`, con la arquitectura recuperada).

---

## 6. Después de la reorganización: validar la generalidad

### V1. Semillas de validación nuevas

Todas las decisiones desde el paso 5 se han tomado mirando las semillas 31 y 32. Hay que medir `main` con **semillas nuevas** (por ejemplo, 41 y 42) para saber si las mejoras se mantienen o había sobreajuste. Las semillas reservadas para la evaluación final (1000–1009) siguen sin tocarse.

### V2. Batería de perturbaciones (pilar 3)

Cambios en el mundo, aplicados desde el arnés y nunca en el agente:
- una receta cambiada (por ejemplo, la mesa pide 3 de madera; el manual se actualiza con el hecho nuevo);
- un día un 50 % más corto o más largo;
- un mundo de 48×48 y otro de 96×96;
- agua escasa;
- la vista reducida a radio 3.

**Criterio:** IdA general conserva una fracción mayor de su Score que la línea procedimental (`crafter-procedimental-v1`). Detalle en la sección 7.3 de `FASE_GENERALIZACION_CRAFTER.md`.

### V3. Un segundo mundo con el mismo cuerpo

**La prueba de fuego de la reorganización:** un mundo nuevo de cuadrícula 2D, por ejemplo MiniGrid (llaves, puertas, lava, objetos, sin día ni noche), que reutilice los Componentes generales y los de cuadrícula. Solo se escribe su adaptador, su manual y sus parámetros. **Con cero ajustes** en los Componentes generales. Si funciona, la separación es real.

Conviene elegirlo según el mundo nuevo que se quiera abordar después: el que mejor lo anticipe.

---

## 7. Después: seguir mejorando

Por orden de prioridad propuesto. Cada uno con su encargo, sus criterios fijados antes de medir y su regla de cierre (sección 8).

### M1. La amplitud de S3 (economía de la atención)

- **Diagnóstico** (`docs/DIAGNOSTICO_DEUDA14.md` y `docs/MEDICION_MATERIAL_MAPA.md`): en los 50 latidos tras colocar la primera mesa, **el 28-33 % de las propuestas de S3 se rechazan por falta de amplitud**. S3 corre el último, y en esos latidos S1 gasta el doble de lo normal (23 frente a 12 piezas), así que S1 y S2 se comen toda la amplitud (44).
- **Por qué es importante:** es un límite de la base, no de Crafter. Probablemente afecta a todos los mundos.
- **Opciones a valorar en el diseño** (no decididas):
  - una reserva mínima de amplitud para cada sistema;
  - un reparto según la intensidad de los impulsos de cada sistema;
  - revisar por qué S1 gasta el doble cuando hay amenaza.

  Hay que leer antes `docs/CALIBRACION_ATENCION.md`.
- **Riesgo:** cambia la calibración de la atención en todos los mundos. Necesita el benchmark completo de mínimo y archivos además de Crafter.

### M2. Deuda 12: cuándo merece la pena luchar

`defeat_zombie` está en el 45-46 %, frente al 54 % de las estrategias escritas a mano, que atacaban siempre que había espada. `Afrontar` es más prudente: exige margen de salud. Puede mejorar en parte sola, ahora que hay espada más a menudo (deuda 14). Hay que revisar la estimación del daño esperado y la tasa de ataque aprendida.

### M3. Deuda 9 y el peligro en los demás mundos

Después de la reorganización, la aliestesia y el peligro aprendido se activan solo en los mundos que los registran (hoy, Crafter). Queda por decidir, mundo a mundo, si mínimo y archivos deben registrarlos en lugar de recibir su `peligro` ya calculado desde el adaptador. Esto es anterior a la fase, y también es pensar por el individuo. Registrarlos **cambia la conducta** de esos mundos: requiere un benchmark pareado de mínimo y archivos (N = 10), con el criterio de la sección e de `docs/PROPUESTA_PASO0.md`.

### M4. Deuda 15: tener el refugio antes de la noche

La deuda 11 mostró que el límite de la noche **no es cuándo perseguir un sitio, sino tener uno** (`docs/DIAGNOSTICO_DEUDA11.md`). Solo sobrevive a la noche entre uno de cada cuatro y uno de cada cinco episodios, frente a uno de cada dos en la línea procedimental. La idea a explorar es preparar el refugio de día, en calma, cerca de los recursos, y reutilizarlo como hogar.

### M5. Paso 4: el huerto

`eat_plant` sigue por debajo del 1 %, aunque se planta en dos de cada tres episodios. Hace falta proteger la planta (las criaturas la destruyen), recordar dónde está y volver cuando madura. Es «proteger X» con X = la planta. En la media geométrica, un logro que sale de casi cero pesa mucho.

### M6. Motivación sin lista de logros

Hoy `PerseguirMetas` toma sus metas de los 22 logros del manual. En un mundo sin lista de logros, IdA no tendría motor de progreso salvo la curiosidad. **Propuesta:** que la base genere metas propias (efectos nuevos, objetos nuevos), y que la lista del manual solo acelere.

### M7. Paso 7: la evaluación final

- 1M de pasos con las 10 semillas reservadas (1000–1009), unas 35 horas de máquina, en dos tandas;
- la batería de perturbaciones (V2);
- el benchmark completo de mínimo y archivos.

Informe con la Score sin herencia y con linaje, con su IC. **Opcional:** enviar a IdA a la tabla de clasificación de Crafter (categoría External Knowledge), mediante una PR al repositorio de Crafter, con las columnas «Uses» («scene description, Crafter paper») e «Interaction» (0) declaradas.

### Deudas menores (sin prisa)

- **Las líneas de comando antiguas** guardadas en `resumen_evaluacion.py` (con interruptores ya quitados) no funcionan si se relanzan.
- **Algunos informes antiguos** (`INFORME_C.md`, `MEDICION_WIP_C4.md`) citan el arnés de refugio borrado.
- **La rama `feature/deuda11`** queda como registro, sin fusionar.

---

## 8. Método de trabajo

### 8.1 Reparto de papeles

| Papel | Quién (hasta ahora) | Qué hace |
|---|---|---|
| Diseño | Claude (asistente de diseño) | Escribe los encargos: hipótesis, diseño, pseudocódigo, criterios y regla de cierre |
| Implementación | Opus 5.5 | Implementa, diagnostica y prueba. Informa de sus desviaciones del encargo y de los resultados negativos tal cual |
| Medición | Flash | Ejecuta las mediciones largas y genera los informes de medición. No interpreta |
| Autor | Diego Rodríguez Reija | Decide, abre las PR y fusiona |

**Lecciones aprendidas sobre los agentes:**
- **Flash ha llegado a inventar cifras** antes de que terminara un proceso (dos veces, al principio de la fase). Por eso, toda cifra debe salir de un fichero que exista, citado por su ruta. Quien revisa recalcula las Scores desde los JSON.
- **Pide siempre las respuestas en español.**
- **Una conversación nueva con un agente necesita un prompt con todo el contexto,** incluidas las rutas de los documentos.

### 8.2 Reglas del repositorio

- **Entorno:** usar siempre el entorno virtual del proyecto, `.venv\Scripts\python.exe` (Python 3.15). En esa máquina hay otro Python (3.11) que no debe usarse. En PowerShell no hace falta activarlo: se llama directamente.
- **No instalar paquetes** sin permiso del autor.
- **Nunca push a `main`:** cada trabajo va en su rama, con su PR y una fusión con commit de merge (no *squash*), para conservar la historia de cada paso.
- **Una etiqueta por cada cambio de conducta por defecto fusionado** (`crafter-general-vN`).
- **Mientras se mide, en la máquina no corre ningún otro proceso de IdA** (ni tests ni pruebas rápidas).

### 8.3 Cómo se mide

- **Protocolo oficial abreviado:** `python herramientas/evaluar_crafter.py --pasos 100000 --semilla S --vista oficial --sin-herencia --manual estricto --plazo-logico 40 --salida datos/evaluacion/<fichero>.json`. Unos 20-25 minutos por medición.
- **Guillotina lógica** (`--plazo-logico 40`): el plazo de cada latido se cuenta en operaciones, no en milisegundos. El resultado es idéntico aunque la máquina esté cargada (`docs/METODO_MEDICION.md`).
- **Comparación pareada:** con la misma semilla base, el episodio *k* ocurre en el mismo mundo en todas las condiciones. `resumen_evaluacion.py --pareada A B` compara episodio a episodio, y `--pareada-conjunta A1 B1 A2 B2` junta varias semillas con un bootstrap estratificado.
- **Los criterios usan la comparación conjunta de las semillas 31 y 32, y se fijan ANTES de medir.**
- **Las pruebas rápidas de 3000 pasos no sirven para decidir.** Solo comprueban que el código corre. Han engañado tres veces: en el 11c, la semilla 32 anunciaba −4,66 puntos y la medición dio +1,28.
- **La referencia actual** (`main`, `crafter-general-v4`) son `datos/evaluacion/mapa_31.json` y `mapa_32.json`. Repetir la referencia en una rama nueva debe dar el mismo JSON.

### 8.4 Cómo se decide

Cada encargo lleva:
1. la **hipótesis**, con los datos de diagnóstico que la sostienen;
2. un **diagnóstico antes de implementar,** cuando la causa no está clara. **Si los datos contradicen la hipótesis, se para y se propone, sin implementar**;
3. el diseño, como un cambio mínimo, con cada mecanismo nuevo tras un interruptor durante la implementación;
4. los **criterios de aceptación, escritos antes de medir**;
5. una **regla de cierre fijada de antemano:** si no se cumplen tras un diagnóstico y una ronda de implementación, se documenta como resultado negativo y se cierra. **No se encadenan rondas de ajustes sobre datos con ruido.**

**Regla de traslado:** cuando un mecanismo se queda, se quita su interruptor y se borra lo que sustituye. Las dos versiones nunca conviven al cerrar el paso.

### 8.5 Antes de fusionar

- ruff, mypy y pytest en verde, con el entorno del proyecto.
- `invariancia.py` OK en los cuatro mundos. Si Crafter cambia por diseño, la referencia (`datos/invariancia/referencia.json`) se regenera en un commit separado, con el motivo en el mensaje.
- README, README.en, `05_METRICAS_E_HITOS.md` y `CHANGELOG.md` actualizados con las cifras comprobadas en los JSON.
- La CI de GitHub en verde.

---

## 9. Referencia rápida

### Documentos clave

| Documento | Qué contiene |
|---|---|
| `doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md` | El diseño de IdA: Core, sistemas, módulos, Componentes, Onda, Experiencia |
| `docs/FASE_GENERALIZACION_CRAFTER.md` | El plan de la fase, los pilares y la tabla de resultados |
| `docs/DEUDA_TECNICA_CRAFTER.md` | Las deudas: estado y decisión de cada una |
| `docs/METODO_MEDICION.md` | Guillotina lógica, comparación pareada y criterios |
| `docs/INVENTARIO_CONOCIMIENTO_CRAFTER.md` | Qué sabe de Crafter el adaptador, y de dónde sale |
| `docs/ENCARGO_*.md` y `docs/MEDICION_*.md` | El encargo y la medición de cada paso, con su sección «Resultado» |
| `docs/DIAGNOSTICO_*.md` | Los diagnósticos (por qué falla algo) |

### Herramientas

| Herramienta | Para qué |
|---|---|
| `herramientas/evaluar_crafter.py` | Evaluación oficial de Crafter (`--plazo-logico`, `--verificar-determinismo`, `--mecanismos`, `--manual`) |
| `herramientas/resumen_evaluacion.py` | Tablas de los informes y comparaciones (`--pareada`, `--pareada-conjunta`) |
| `herramientas/invariancia.py` | Comprueba que la conducta no cambia en los cuatro mundos (`--referencia` la regenera) |
| `herramientas/benchmark.py` | Benchmark de perfiles en mínimo y archivos |
| `herramientas/verificar_manual.py` | Comprueba que cada cita del manual aparece literalmente en el artículo o el README de Crafter (las fuentes se descargan fuera del repositorio) |
| `herramientas/diagnostico_*.py` | Diagnósticos de primera noche, cadena de herramientas, «sin meta», Tribunal, etc. No cambian la conducta |

### Etiquetas

| Etiqueta | Qué es |
|---|---|
| `crafter-procedimental-v1` | Línea procedimental congelada (19,2 %) |
| `crafter-general-v1` | Paso 3 (12,8–13,6 %) |
| `crafter-general-v2` | Paso 6: el adaptador sin conducta propia (14,0–15,5 %) |
| `crafter-general-v3` | Deuda 14 (14,8–16,0 %) |
| `crafter-general-v4` | 11c: material desde el mapa (15,9–17,3 %). **Referencia actual** |

### Orden de trabajo propuesto

0. **Sección 0:** fijar los conceptos originales con el autor y actualizar `doc-repositorio/02`.
1. **R0 a R7:** reorganización por Componentes, con equivalencia exacta.
2. **V1 a V3:** validar la generalidad (semillas nuevas, perturbaciones y un segundo mundo).
3. **M1 a M7:** seguir mejorando (amplitud de S3, luchar, peligro en todos los mundos, refugio de día, huerto, metas propias y evaluación final).
