# IdA — Fase de generalización en Crafter

Documento de partida de la fase. La primera parte es informativa: qué se quiere hacer, por qué, cómo se compara IdA con lo publicado y qué hay que cambiar para que la comparación sea justa. La segunda parte es el plan.

Fecha: 19/11/2026. Base: cierre de la fase C (`feature/crafter-fase-c`, C.3d; veredicto «cumplido en parte»).

---

# Parte I — Qué, por qué y en qué condiciones

## 1. Qué se quiere hacer

Durante las fases A, B y C, IdA ha mejorado en Crafter gracias a estrategias escritas para Crafter: `RefugioNocturno`, `DefensaArmada`, `CerrarDistancia` y `PlanTecnologico`, registradas en `MundoCrafter.estrategias_propias()`. Funcionan, pero cuanto más funcionan, menos se mide a IdA y más se mide el código del mundo. `RefugioNocturno` ya decide casi todo lo que pasa en una vida (deuda 1 de `DEUDA_TECNICA_CRAFTER.md`).

El objetivo de esta fase es **invertir esa tendencia**: trasladar a la base (S1, S2, S3, Tribunal y memoria) las capacidades generales que esas estrategias resolvían a mano, y vaciar el mundo hasta dejarlo como un adaptador que solo percibe, actúa y declara hechos. Al final, `estrategias_propias()` de Crafter devuelve `{}`.

Lo que se mide al final es si IdA, **sin entrenamiento previo y sin conducta escrita para Crafter**, juega a Crafter con un protocolo comparable al de la literatura, y si esa conducta resiste cambios en el mundo que harían fallar a un script.

## 2. Por qué

### 2.1 El argumento de IdA no es la puntuación

Cifras publicadas de la Crafter Score (media geométrica de las tasas de éxito de los 22 logros, con 1M de pasos):

| Agente | Crafter Score | Entrenamiento | Fuente |
|---|---|---|---|
| Humanos expertos | 50,5 ± 6,8 % | — | Hafner (2021), artículo original |
| EMERALD (modelo del mundo) | 58,1 % | 10M de pasos | [arXiv 2507.04075](https://arxiv.org/pdf/2507.04075v2) |
| Mejor agente RL con 1M de pasos (Craftax-classic) | 27,91 % | 1M de pasos | [arXiv 2502.01591](https://web3.arxiv.org/pdf/2502.01591) |
| SPRING (GPT-4 leyendo el artículo) | 27,3 % | Ninguno (LLM preentrenado) | [Resumen de SPRING](https://emsime.substack.com/p/gpt-4-outperforms-rl-algorithms-in-crafter-by-reading-paper-and-reasoning) |
| DreamerV2 | 10,0 ± 1,2 % | 1M de pasos | Hafner (2021) |
| PPO | 4,6 ± 0,3 % | 1M de pasos | Hafner (2021) |
| Aleatorio | 1,6 % | — | Hafner (2021) |

Notas:
- Craftax-classic es una reimplementación de Crafter en JAX; no es idéntica, aunque se usa como equivalente.
- Con 1M de pasos, el mejor agente de aprendizaje por refuerzo ya ronda el 28 %. **IdA no va a ganar en puntuación**, y tampoco lo necesita.

Lo que IdA puede aportar y casi ningún agente de la tabla tiene a la vez:

1. **Cero entrenamiento** (o un linaje declarado dentro del presupuesto): la primera vida ya juega razonablemente.
2. **Conducta explicable:** cada acción sale de una propuesta con verbo, objetivo, motivo, arousal y confianza, y de un Tribunal cuya decisión se puede leer.
3. **Generalidad:** la misma base juega en mínimo, archivos, ajedrez y Crafter, y debería resistir perturbaciones del mundo.
4. **Sin modelo de lenguaje:** SPRING razona con GPT-4; IdA razona con una arquitectura de unos pocos miles de líneas.

La tesis de la fase es esta: **una arquitectura cognitiva bioinspirada, sin entrenamiento y sin conducta específica del mundo, alcanza una puntuación del orden de la de los agentes de RL clásicos con 1M de pasos (DreamerV2, PPO), con conducta explicable que resiste perturbaciones.** Si además supera a DreamerV2, mejor; pero la puntuación es la evidencia de competencia, no el argumento.

### 2.2 Por qué ahora

- La fase C dejó claro el límite del enfoque actual: cada mejora de conducta añadía lógica al mundo (deudas 1 y 2) y el beneficio se reducía (criterio 1 de C sin cumplir).
- La causa de fondo está en la base: **la intensidad del impulso no llega al Tribunal** (deuda 2). Mientras no llegue, cada necesidad urgente obliga a escribir una estrategia del mundo que la imponga.
- Resolverlo en la base mejora a IdA en todos los mundos, no solo en Crafter.

## 3. Las reglas de Crafter y los cuatro pilares

### 3.1 Lo que Crafter exige formalmente

Crafter tiene pocas reglas formales, y conviene no atribuirle más:

- **Presupuesto:** 1M de pasos de entorno en total.
- **Episodios:** hasta 10 000 pasos o hasta la muerte; el mundo se regenera en cada episodio.
- **Puntuación:** para cada uno de los 22 logros, la tasa de éxito `s_i` (en %) es la fracción de episodios en que se consiguió al menos una vez, sobre **todos** los episodios dentro del presupuesto. La Crafter Score es `S = exp(media_i(ln(1 + s_i))) − 1`.
- **Observación oficial:** una imagen de 64×64 con una vista local de 9×7 casillas más 2 filas de inventario (`env.py:42-44`; 16 objetos de inventario en filas de 9). La recompensa es opcional y no forma parte de la puntuación.

### 3.2 Los cuatro pilares son un estándar propio

Los pilares no son reglas del ranking. Son **lo que IdA se exige para que la comparación sea justa** y para que el resultado diga algo sobre IdA y no sobre su programador. Así deben presentarse en cualquier publicación.

| Pilar | Qué exige | Cómo se comprueba (objetivamente) |
|---|---|---|
| 1. Frontera limpia | El mundo solo percibe, actúa y declara hechos; toda decisión está en la base | `estrategias_propias()` de Crafter devuelve `{}`; un test comprueba que ninguna clase de `ida/mundos/crafter.py` hereda de `Definicion`, `Plan` o `ConPropuestas` |
| 2. Declarativo, no procedimental | Lo que se le da a IdA son hechos («la piedra se pica con un pico de madera»), no secuencias («ve, pica, vuelve») | Principio de diseño, revisado en cada paso; **no es criterio de aceptación** porque la frontera entre pauta innata y guion es discutible. Lo deciden las pruebas de los pilares 1 y 3 |
| 3. Perturbación | La conducta resiste cambios del mundo que no se le han enseñado | Batería de perturbaciones (sección 7.3): IdA general pierde menos que el script de C.3d |
| 4. Protocolo honesto | Evaluación con el protocolo oficial, semillas nuevas y todo declarado | Comando de evaluación único y reproducible (paso −1); semillas de evaluación fijadas antes y nunca usadas para ajustar |

## 4. Qué hay que cambiar para que la comparación sea justa

Revisado sobre el código (`ida/mundos/crafter.py`) y el de Crafter 1.8.3.

### 4.1 Lo que ya está bien

- **El adaptador no lee estado oculto.** Solo usa salud, inventario, luz, materiales de la vista, criaturas y si la planta está madura. Todo eso se ve en la imagen oficial (la planta madura tiene su propia textura; la salud y el inventario están en las filas de inventario). No lee contadores de hambre, sed o fatiga, ni el crecimiento de la planta ni las reglas de aparición.
- **La recompensa no se usa.** IdA aprende de sus propias necesidades.
- **La memoria persistente no se relee entre ejecuciones** (`memoria.db` no se carga de vuelta; E0), así que no hay fuga de experiencia entre evaluaciones.

### 4.2 Lo que hay que cambiar

| # | Diferencia | Situación hoy | Cambio | Paso |
|---|---|---|---|---|
| 1 | **Duración del episodio** | `Env(seed=…, length=100000)` | `length=10000` en el protocolo oficial | −1 |
| 2 | **Vista** | Cuadrado de radio 4 (9×9; el comentario de la línea 6 dice «como la vista oficial de 9×9», y es erróneo) | Opción `vista="oficial"`: 9 de ancho × 7 de alto centrado en el jugador (radio 4 en x, 3 en y). Es la que se usa en la evaluación | −1 |
| 3 | **Episodios y presupuesto** | Cada vida reinicia el mundo con una semilla del arnés; el número de vidas lo fija el arnés | Bucle de evaluación: episodios sucesivos hasta sumar 1M de pasos; **los pasos de todas las vidas del linaje cuentan** | −1 |
| 4 | **Conocimiento previo** | Las estrategias de C usan hechos sacados de `objects.py` y `env.py` (maduración > 300, luz 0,83, chunks de 12×12, alcance de 18, umbrales de aparición) | Regla de procedencia del manual (sección 5). Lo que no venga del artículo o del README se aprende o se estima | 2 |
| 5 | **Conducta escrita para Crafter** | 4 estrategias propias | Se trasladan a la base y se borran (regla de traslado) | 0–6 |

### 4.3 Lo que se mantiene, pero se declara

| Ventaja o diferencia | Por qué es aceptable | Cómo se declara |
|---|---|---|
| **Entrada simbólica** (identidades de objetos, materiales por casilla, luz como número) en lugar de píxeles | Es la «liga simbólica»: SPRING también recibía la escena descrita en texto. Toda la información es visible en la imagen | «IdA recibe una descripción simbólica de la vista local oficial (9×7), sin estado oculto» |
| **Coordenadas absolutas** de la casilla propia | Se pueden obtener por integración de trayecto (las acciones son deterministas y se ve si el movimiento tuvo efecto). Es una capacidad biológica conocida | Declararlo. Opcional: expresarlas relativas a la casilla de nacimiento |
| **Noche:** IdA reduce el radio a 2 con luz < 0,3 | Es más restrictivo que el oficial (que solo añade ruido y oscurece la imagen) | Declararlo como restricción propia |
| **Linaje:** las vidas heredan proposiciones y registros | Es aprendizaje dentro del presupuesto, como el de un agente de RL | Publicar dos cifras: **primera vida** (cero entrenamiento) y **linaje completo** (1M de pasos) |
| **Perfil:** IdA tiene caracteres (Equilibrado, Valiente…) | Es un hiperparámetro | Se fija **uno** antes de evaluar (propuesta: Equilibrado) y se declara |

## 5. El manual declarativo y su regla de procedencia

IdA necesita saber qué hay en el mundo: qué se come, qué hace daño, qué se fabrica con qué. Un humano lo aprende leyendo las instrucciones; SPRING leía el artículo. El manual es el equivalente para IdA: **hechos**, no conducta.

**Regla de procedencia:** el manual solo puede contener lo que dicen **el artículo de Crafter (Hafner, 2021) y el README del repositorio oficial**. Es la misma fuente que usó SPRING, y así la comparación es de igual a igual.

| Entra en el manual (si lo dicen el artículo o el README) | No entra: se aprende o se estima |
|---|---|
| Recetas: qué material, herramienta y estación hace falta para cada objeto | Los 300 pasos de maduración de la planta |
| Qué se come y se bebe (vaca, agua, planta madura) | Cuánto daño hace cada criatura y con qué alcance |
| Que zombis y esqueletos son hostiles, y dónde viven (hierba de noche, cuevas) | Umbrales de aparición (luz 0,83, hierba ≥ 50 por chunk, caminos ≥ 6) |
| Que las necesidades bajan con el tiempo y se recuperan durmiendo, comiendo y bebiendo | Ritmos exactos de consumo (26/21 pasos) |
| Las 22 metas (logros) | Tamaño de los chunks y alcance de actualización de 18 casillas |

Cada hecho del manual llevará una referencia a la frase del artículo o del README de la que sale. Si no se encuentra la frase, el hecho no entra.

## 6. Ideas de diseño que guían la fase

- **Regla de traslado:** cada paso añade a la base y borra del mundo; **nunca conviven las dos versiones**. Si la versión de la base no alcanza a la del mundo, se mide, se acepta la pérdida o se mejora la base; no se deja la del mundo «por si acaso».
- **«Proteger X»:** refugio, huerto y defensa son el mismo impulso general aplicado a cosas distintas (a uno mismo, a una planta, a un recurso). La base biológica es la querencia por paredes y grietas. Formulación, corregida con lo aprendido en C.1:
  - X tiene **accesos** (casillas por las que puede llegar un peligro);
  - las acciones válidas son **cerrar un acceso** (colocar material) **o crear espacio protegido** (cavar en roca, donde las paredes ya existen; así nacieron la mayoría de los refugios de C.1);
  - el lugar se elige por el **coste de completar la protección**, con anticipación corta (1–2 pasos): el orden de cierre importa por la orientación, y una regla puramente voraz se bloquea a sí misma (`_orden_paredes_factible`);
  - sin geometría de Crafter escrita: «para sellarse desde dentro hacen falta 2 casillas interiores» debe salir de la anticipación, no de una regla.
- **La intensidad decide:** una necesidad urgente gana en el Tribunal por su intensidad, no porque una estrategia del mundo la imponga.

## 7. Cómo se decide si la fase ha funcionado

### 7.1 Expectativa de puntuación (escrita para no frustrarse a mitad de fase)

- El script actual (C.3d, todo escrito a mano) ronda el 23 % **con nuestro protocolo** (600 latidos, cuatro perfiles), que no es el oficial. Con el protocolo oficial puede dar otra cifra; el paso −1 la mide.
- Una versión general **caerá** respecto al script. Es razonable esperar un **10–15 % durante bastante tiempo**. Superar a DreamerV2 (10 %) sin entrenamiento ya sería un resultado defendible.

### 7.2 Criterios de aceptación de la fase

1. **Pilar 1:** `estrategias_propias()` de Crafter devuelve `{}` y el test de frontera pasa.
2. **Pilar 4:** evaluación oficial con semillas nuevas, primera vida y linaje, todo declarado (sección 4).
3. **Pilar 3:** en la batería de perturbaciones, IdA general conserva una fracción mayor de su puntuación que C.3d.
4. **Generalidad:** el benchmark de mínimo, archivos y ajedrez no empeora de forma significativa (pareado por semilla, N = 10, IC 95 %).
5. **Puntuación:** por encima del suelo medido en el paso −1, de forma significativa. Superar a DreamerV2 es objetivo deseable, no requisito.

### 7.3 Batería de perturbaciones (borrador; se cierra en el paso −1)

Cambios que se aplican **al mundo desde el arnés** (parámetros o parches de Crafter), nunca al agente. Si un cambio altera un hecho del manual (una receta), el manual se actualiza con el hecho nuevo; eso es legítimo, porque es declarativo.

| Perturbación | Qué pone a prueba |
|---|---|
| Mundo de 48×48 y de 96×96 | Que la conducta no dependa de distancias aprendidas |
| Día un 50 % más corto o más largo | Que la anticipación de la noche salga de la luz percibida, no de un reloj |
| Agua escasa (semillas con poca agua, o lagos reducidos) | Búsqueda y memoria de recursos |
| Una receta cambiada (p. ej. el pico de piedra pide 2 de piedra) | Que la tecnología salga del manual y no de una secuencia |
| Vista reducida a radio 3 | Robustez de la percepción |

---

# Parte II — El plan

Reparto de trabajo (el que funcionó en C.1): **yo escribo el diseño y el pseudocódigo de cada paso; Argon solo implementa; Flash mide.** Cada paso se cierra con su medición y su veredicto antes de empezar el siguiente.

**Los otros mundos son parte de la fase, no un control al final.** La base que se construye es la de todos los mundos, así que cada paso que toque `ida/core` o `ida/sistemas` se mide también en mínimo, archivos y ajedrez:

- **Durante el paso:** benchmark rápido (Equilibrado) en mínimo y archivos, e `invariancia.py` en ajedrez.
- **Al cerrar el paso:** benchmark completo (4 grupos, N = 10, pareado por semilla, IC 95 %) frente a `ref_generalizacion`.
- **Criterio de no inferioridad, declarado de antemano:** ninguna diferencia significativa en contra en la métrica principal de cada mundo (latidos y fitness en mínimo y archivos; muertes por hambre en archivos; logros en Crafter) y un coste por latido no más de un 10 % mayor. Si el paso mejora otro mundo, se anota como evidencia de generalidad.
- **Ajedrez:** la invariancia se exige solo donde el diseño del paso diga que la conducta no debe cambiar. Si debe cambiar, se mide su resultado frente al rival.
- **Snake** sigue fuera, porque depende de un navegador externo.

Semillas: ajuste 11–30, validación 31–50, benchmark 1–10 (como hasta ahora). **Evaluación oficial: semillas reservadas 1000–1009**, que nadie usa hasta el paso 7. En los pasos intermedios se mide con el protocolo oficial abreviado sobre las semillas de validación.

## Decisión previa: rama de partida

| Opción | A favor | En contra |
|---|---|---|
| **`main` (B.2lite)** | Menos código que borrar; la fase consiste precisamente en vaciar el mundo | Pierde el código de C.3d |
| **C.3d** | Techo más alto de partida | Más código que trasladar y borrar; Diego tiene motivos para no fusionarla aún |

**Recomendación:** partir de `main` y tratar C.3d como **conocimiento**, no como código: sus lecciones (cavar, orden de cierre, urgencia por salud, salida al amanecer) están en `ENCARGO_CRAFTER_C.md`, `INFORME_C.md` y `DEUDA_TECNICA_CRAFTER.md`, y pasan al diseño de «proteger X». C.3d se mide igualmente en el paso −1 como techo de referencia.

**Decisión (Diego, 19/11/2026):** se parte de `main`. De las ramas (`feature/crafter-fase-c`, `wip/c4-argon`, bloques E y F) solo se toma lo que sirva como inspiración, conocimiento o código reutilizable, y siempre pasando por la regla de traslado.

## Paso −1. Medir antes de construir (Flash)

**Objetivo:** tener el comando de evaluación oficial y las dos cifras que acotan la fase.

1. **Adaptador** (cambios que no alteran la conducta por defecto):
   - opción `vista="oficial"` (9 × 7) además de la actual;
   - opción `longitud` del episodio (10 000 en la evaluación).
2. **Comando** `herramientas/evaluar_crafter.py`:
   - un perfil, una semilla base, episodios sucesivos hasta 1M de pasos (opción `--pasos` para versiones abreviadas);
   - linaje continuo: una muerte pasa a la siguiente vida con su legado; un episodio que llega a 10 000 pasos también abre vida nueva, con legado pero sin causa de muerte;
   - salida: tasa de éxito de cada logro, Crafter Score, la misma puntuación limitada a la primera vida de cada semilla, pasos y episodios, causas de muerte y tiempo por paso;
   - IC 95 % de la Score por remuestreo de episodios.
3. **Mediciones**, con la vista oficial y el perfil Equilibrado:

| Medición | Qué es | Para qué |
|---|---|---|
| **Suelo** | `main` con `estrategias_propias()` vacías: adaptador y base solos | Cuánto sabe hacer IdA sin conducta de Crafter |
| **Techo `main`** | `main` (B.2lite) completo | Referencia de la rama de partida recomendada |
| **Techo C.3d** | `feature/crafter-fase-c` | Referencia del mejor script |

4. **Referencia de los otros mundos:** benchmark completo de `main` en mínimo y archivos (`herramientas/benchmark.py ejecutar`, 4 grupos, N = 10) y estado de `invariancia.py` en ajedrez. Se guarda como **`ref_generalizacion`**: es la línea base contra la que se compara cada paso que toque la base.

**Control del coste:** primero cronometrar 10 000 pasos e informar de la proyección a 1M **antes** de lanzar nada largo. Después, versión abreviada (100 000 pasos por medición). La de 1M solo si la abreviada es estable y el tiempo es razonable.

**No toca** `ida/core` ni `ida/sistemas`.

## Paso 0. La intensidad del impulso llega al Tribunal (diseño: yo; implementa: Argon)

**Hipótesis:** si la intensidad de una necesidad (su déficit y su urgencia) entra en la puntuación del Tribunal, la propuesta urgente gana sin que una estrategia del mundo la imponga; y sin urgencia, el Tribunal queda «en calma» y no cambia lo que hace hoy.

- Antes de tocar código: **documento de diseño** con la fórmula exacta, dónde entra la intensidad, qué pasa en cada mundo y por qué no debería cambiar la conducta donde no hay urgencia.
- Toca `ida/core`: es el único paso que cambia la base en todos los mundos, así que es el más arriesgado.
- **Criterio de aceptación:**
  - mínimo, archivos y ajedrez: benchmark completo no peor de forma significativa (pareado, N = 10, IC 95 %) e `invariancia.py` donde la conducta no deba cambiar;
  - Crafter: la medición abreviada no empeora; y al menos un apaño de urgencia del mundo se puede borrar (p. ej. la urgencia por salud de C.0c) sin pérdida.

## Paso 1. Memoria espacial que alguien use (diseño: yo; implementa: Argon)

El bloque E se midió como **no útil** (`VEREDICTO_E_F.md`): ninguna decisión usaba lo que solo E sabía, y costaba un 7–14 % de tiempo por latido. El veredicto ya apunta las causas probables. Por eso:

- este paso **no activa E entero**; activa solo lo que vayan a usar los pasos 3 y 4 (lugares con valor, recursos recordados, hogar), y lo diseña junto con esas decisiones;
- es el «mapa cognitivo compartido» de la deuda 1: un solo lugar donde la base guarda refugios, agua, plantas y peligros, en lugar de que cada estrategia lleve su propio registro;
- **criterio:** que una decisión del paso 3 o 4 dependa de él, y que el benchmark de los otros mundos no empeore (ni en resultado ni en tiempo por latido más de lo declarado).

## Paso 2. Manual declarativo (diseño: yo; implementa: Flash o Argon según tamaño)

- Formato del manual: hechos con referencia a su fuente (sección 5), cargados como proposiciones con confianza de autoridad (`c_aut`), que la experiencia puede confirmar o refutar.
- Sustituye los hechos de Crafter hoy repartidos por `crafter.py` (`constantes`, recetas dentro de `PlanTecnologico`).
- **Criterio:** auditoría de procedencia (cada hecho con su frase) y medición abreviada sin pérdida significativa.

## Paso 3. «Proteger X» en la base: el refugio (diseño: yo; implementa: Argon)

- Componente general de S1 que implementa «proteger X» (sección 6), con X = uno mismo.
- Sustituye a `RefugioNocturno`, que **se borra en el mismo paso** (regla de traslado).
- **Criterio:**
  - sellado del día 1 y muertes nocturnas medidos con el arnés de refugio sobre las semillas de validación, frente a C.3d y frente a `main`;
  - pérdida aceptable frente a C.3d: se declara antes de medir (propuesta: no más de 15 puntos de sellado del día 1);
  - en otros mundos, invariancia o mejora.

## Paso 4. Proteger X aplicado a los recursos: forrajeo y huerto (diseño: yo; implementa: Argon)

- El mismo componente con X = una planta o una fuente de comida: plantar donde la protección sea barata, recordar dónde, volver cuando madura. El periodo de maduración se **estima** con la experiencia (no está en el manual).
- Recoge la deuda 8 (huerto): nichos que dan al interior del refugio y se comen desde dentro; se planta desde el día 2.
- Es la respuesta al límite que dejó la fase C: el hambre en las vidas largas.
- **Criterio:** muertes por hambre en vidas largas (arnés `--latidos 3000`) por debajo de las de C.3d.

## Paso 5. Tecnología desde el manual (diseño: yo; implementa: Argon)

- `PlanTecnologico` se sustituye por un plan general de S3 que deriva la cadena de recetas del manual (lo que falta para lo siguiente que se puede fabricar), con el tipo `Plan` de F2 si aporta, y solo si aporta.
- **Criterio:** tasas de éxito de los logros tecnológicos no peores de forma significativa; perturbación «receta cambiada» superada sin tocar código.

## Paso 6. Defensa general (diseño: yo; implementa: Argon)

- `DefensaArmada` y `CerrarDistancia` se sustituyen por la respuesta general de S1 a un peligro (huir, enfrentarse o protegerse), con el daño y el alcance **estimados por la experiencia** y no escritos.
- Con este paso, `estrategias_propias()` de Crafter queda vacía.
- **Criterio:** muertes por criatura no peores de forma significativa frente al paso 5; test de frontera (pilar 1) en verde.

## Paso 7. Evaluación final (Flash)

- Protocolo oficial completo sobre las semillas reservadas 1000–1009: 1M de pasos por semilla, vista 9 × 7, perfil Equilibrado.
- Batería de perturbaciones (sección 7.3) para IdA general y para C.3d.
- Benchmark completo de mínimo, archivos y ajedrez.
- Informe con: Score del linaje y de la primera vida (con IC), tasas por logro, comparación con la tabla 2.1, resultado de las perturbaciones y la lista de declaraciones de la sección 4.3.

## Resumen del plan

| Paso | Qué | Quién | Toca la base | Borra del mundo |
|---|---|---|---|---|
| −1 | Protocolo oficial, suelo y techo | Flash | No | — |
| 0 | Intensidad del impulso en el Tribunal | Yo (diseño) + Argon | Sí (Tribunal) | Apaños de urgencia |
| 1 | Mapa cognitivo compartido | Yo + Argon | Sí (memoria) | Registros propios de las estrategias |
| 2 | Manual declarativo | Yo + Flash/Argon | Mínimo | `constantes` y recetas |
| 3 | Proteger X: refugio | Yo + Argon | Sí (S1) | `RefugioNocturno` |
| 4 | Proteger X: forrajeo y huerto | Yo + Argon | Sí (S1/S2) | — |
| 5 | Tecnología desde el manual | Yo + Argon | Sí (S3) | `PlanTecnologico` |
| 6 | Defensa general | Yo + Argon | Sí (S1) | `DefensaArmada`, `CerrarDistancia` |
| 7 | Evaluación final | Flash | No | — |

Reglas que siguen vigentes: nunca hacer push sin permiso; no hacer pruebas visuales mientras corre un benchmark; benchmarks rápidos antes que completos; cada cambio confirma su hipótesis con medición.
