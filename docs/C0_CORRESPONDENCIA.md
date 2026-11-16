# C0 — Inventario y correspondencia con el nuevo bucle

Parte C0 del encargo del bloque C ([`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md)). Referencia: decisiones 3 a 6, 10, 11, 13, 16, 17 y 23 de [`REDISENO_BASE.md`](REDISENO_BASE.md). Base: `main` en `b3a6ed6` (bloques A y B). **Propuesta para aprobar; sin código.** Las rutas y líneas son de `b3a6ed6`.

## 1. Cómo se decide hoy

- Cada componente de Reaccionar mira el estado y **propone acciones directamente** (`Componente.proponer` → `acc["Accion"]`). No hay impulsos ni estrategias como piezas que duren varios latidos; la «continuidad» sale de que las mismas condiciones vuelven a proponer lo mismo.
- `S2.Impulso`, `S3.Impulso` y `Prudencia` modulan arousal y confianza de esas acciones (excepción transitoria `impulso_modula_accion` del bloque B).
- El `Tribunal` (`ida/core/sentidos.py:58`) puntúa `base = arousal × estrés + confianza × (1 − estrés)`, más un sesgo de experiencia (`peso_experiencia`); empate (≤ 0,02) al azar; y **acecha** (no ejecuta) un ganador con confianza < 0,35 si no es urgente.

Mundos con componentes propios: mínimo, archivos y Crafter. Snake y ajedrez no tienen (`componentes_propios` no definido).

## 2. Impulsos que se proponen

Un impulso nace del estado sentido e interpretado y no se elige (decisión 2). Su **intensidad cruda** mide la necesidad y es la base del progreso de sus estrategias (decisión 16); el arousal de la pieza `Impulso` es esa intensidad, que S2 y S3 modulan después.

| Impulso | Sistema | Necesidad | Intensidad cruda (hoy ya calculada) | Objetivo (por debajo, se apaga) | Sustituye a |
|---|---|---|---|---|---|
| **Seguridad** | S1 | Evitar daño | `alarma.carga["peligro"]` = 1 − Π(1 − amenaza) de `Supervivencia` (`s1.py:70-95`) | `arquetipo.umbral_miedo` (ejemplo de la decisión 16) | Las condiciones de `Reflejo`, `Defensa`, `DefensaCrafter` y la parte de peligro de `Hogar` |
| **Alimentación** | S1 | Comer | `soma.hambre()` = (70 − alimentación) / 70 (`soma.py:39`); el apetito basal (`apetito`) sigue como factor de arousal | 0 (alimentación ≥ 70) | Las condiciones de `S1.Impulso` y de `Orientacion` |
| **Descanso** | S1 | Dormir | `soma.cansancio()` = (60 − min(energía, descanso)) / 60 (`soma.py:43`) | 0 | La parte de cansancio de `Hogar` y `_candidato_core(DORMIR)` |
| **Exploración** | S2 | Lo nuevo (decisión 10: `Curiosidad` pasa a impulso) | apertura × máx. `novedad` de los lugares y objetos a la vista | 0 (nada nuevo) | `Curiosidad` |
| **Saber** (intención) | S3 | Reducir la incertidumbre: contrastar hipótesis | fracción de proposiciones en hipótesis relevantes a la vista; hoy lo aproxima la elección de `Estudio` | 0 | `Estudio` |

Notas:
- **Seguridad** usa un nivel (peligro), no un cambio. El cambio brusco es del reflejo (sección 4).
- **Descanso** pasa a S1 (es del cuerpo); «volver al hogar a descansar» es una estrategia de S2 para ese impulso (decisión 10).
- **Saber** es una *intención* de S3, no un impulso (decisión 11). En C1 no cambia (S3 sigue como hoy).

## 3. Tabla de correspondencia

Leyenda del destino: **I** impulso, **E** estrategia, **R** reflejo, **M** modulación, **D** desaparece. «Genérica» = la definen los sistemas para cualquier mundo; «propia» = la define un mundo (decisión 3: las estrategias pueden ser del mundo; el impulso es genérico).

### S1 · Reaccionar

| Componente actual | Qué hace hoy | Destino | Correspondencia propuesta |
|---|---|---|---|
| `Reflejo` (`s1.py:97`) | Si peligro ≥ `umbral_miedo`: huir al lugar menos peligroso (MOVER) o, sin salida y con la amenaza al alcance, defenderse (ATACAR). Arousal 0,75–1,0 | **R** + **E** | Se parte en dos. (1) **Reflejo** innato de S1 solo ante un **salto brusco** del peligro entre `ei` y `ev` (alarma del latido anterior frente a la actual): «sobresalto / empezar a huir», 2-3 latidos fijos, prioridad máxima, se agota solo (decisión 6). (2) Para el peligro sostenido, **estrategias genéricas de S1 del impulso Seguridad**: «huir al lugar más seguro» (MOVER) y «defenderse acorralado» (ATACAR con la amenaza al alcance y sin salida) |
| `Impulso` (`s1.py:118`) | Comer lo comestible al alcance (COMER); acercarse al lugar más nutritivo (MOVER); si el mundo no deja esperar y nadie propone, «el mal menor» (MOVER) | **I** + **E** | Emite la pieza `Impulso` **Alimentación** (y Seguridad y Descanso, sección 2) y deja de proponer. Estrategias genéricas de S1 para Alimentación: «comer lo que está al alcance» (consumatoria, COMER) y «acercarse a la comida visible» (apetitiva, MOVER). El «mal menor» pasa a una estrategia genérica de S1 «seguir en movimiento», solo en mundos sin ESPERAR (hoy Snake); ver riesgo 6 |
| `Defensa` (mínimo, `minimo.py:178`) | Lobo al alcance y vitalidad ≥ 30: ATACAR (arousal 1,0) | **E propia** | Estrategia de S1 del mundo mínimo para **Seguridad**: «plantar cara al depredador» (el lobo persigue: huir no sirve). Condición de elegibilidad: agente peligroso al alcance y vitalidad ≥ 30 |
| `Defensa` (archivos, `archivos.py:296`) | Depredador de la carpeta al alcance y vitalidad ≥ 30: ATACAR | **E propia** | Igual que la anterior, estrategia de S1 del mundo de archivos para **Seguridad** |
| `DefensaCrafter` (`crafter.py:348`) | Con espada y salud ≥ 4: ATACAR al zombi/esqueleto adyacente (0,96 u 0,88); con espada y salud ≥ 5: MOVER para acortar distancia a un esqueleto a 2-3 casillas (0,82) | **E propia** ×2 | Dos estrategias de S1 de Crafter para **Seguridad**: «defensa armada» (abatir adyacente) y «cerrar distancia a esqueleto». Elegibilidad: espada y salud. Ver riesgo 5 (lee el inventario y la salud del mundo, no lo percibido) |

### S2 · Reaccionar

| Componente actual | Qué hace hoy | Destino | Correspondencia propuesta |
|---|---|---|---|
| `Exteriorizacion` (`s2.py:94`) | Registra en `ef` el afecto y el placer (sin coste, sin acción) | **R de S2** (se queda) | Es el reflejo de S2 (decisión 10): expresión involuntaria. No propone ni cambia. Sin efecto hasta que haya varios individuos |
| `Impulso` (`s2.py:102`) | Sube o baja el arousal de **cada acción** según la valencia de su objetivo (±0,15 × valencia) | **M** (C2) | Modulación de S2 sobre piezas **`Impulso`** (decisión 14): sube o baja la intensidad de Alimentación, Seguridad, Descanso y Exploración según el valor de los sujetos presentes, y añade los impulsos propios de S2. La valoración **por objeto** pasa a la elección de parámetros de la estrategia (ver riesgo 4) |
| `Curiosidad` (`s2.py:117`) | Sin peligro (< 0,3) ni hambre (< 0,6): MOVER al lugar más nuevo (con `valor_lugar` del replay) y COGER el objeto útil al alcance. Arousal bajo (0,15–0,5) | **I** + **E** | Impulso **Exploración** (S2). Estrategias genéricas de S2: «explorar lo nuevo» (MOVER, con `valor_lugar`) e «investigar lo útil» (COGER). Las inhibiciones de hoy (peligro, hambre) dejan de ser `if`: salen de que Seguridad y Alimentación tienen más arousal (decisión 4) |
| `Hogar` (`s2.py:148`) | Con cansancio ≥ 0,4 o peligro ≥ 0,4, volver al hogar (vista o ruta del hipocampo); con cansancio ≥ 0,6 y calma, DORMIR | **E** ×2 (D como componente) | Desaparece como componente (decisión 10). Estrategias de S2: «volver al hogar» (para Descanso y Seguridad; refugio valorado, ruta del hipocampo) y «descansar en el hogar» (Descanso). S1 tiene su propia «dormir donde se esté» (para Descanso, sin hogar) |
| `Orientacion` (`s2.py:182`) | Con hambre ≥ 0,35, sin peligro y sin comida a la vista: MOVER por la ruta del hipocampo hacia donde se vio una clase nutritiva (confianza ≥ 0,55); olvida el lugar si llega y no está | **E** | Estrategia genérica de S2 «recordar dónde hubo comida» para el impulso **Alimentación** (ejemplo de la decisión 3). Su progreso es la bajada del hambre; el olvido al llegar sin hallar es un fallo que suma agotamiento |

### S3 · Reaccionar

| Componente actual | Qué hace hoy | Destino | Correspondencia propuesta |
|---|---|---|---|
| `Comportamiento` (`s3.py:128`) | Traduce la conclusión de `Logica` (EVITAR, COMER, COGER) en una acción con la confianza de lo demostrado | **E** (C3) | Pasa a `S3.Estrategia` (decisión 14, antes «ProcedimientoS3»): estrategias de conocimiento «evitar lo que se sabe peligroso» (Seguridad), «comer lo que se sabe nutritivo» (Alimentación) y «coger lo que se sabe útil». Ligadas a la `Intencion` de S3. En C1 no cambia |
| `Impulso` (`s3.py:157`) | Freno prefrontal: si la acción va contra lo demostrado (acercarse a lo peligroso, comer lo que no alimenta), arousal × 0,4 y confianza × 0,5 | **M** (C3) | Control de S3 (decisión 13): modulación **gradual según la certeza** sobre piezas `Impulso` y sobre la elección de estrategia. El freno sobre un objeto concreto pasa a ser una restricción de parámetros de la estrategia (ver riesgo 4) |
| `Estudio` (`s3.py:180`) | Lectura de la biblioteca en calma: propone LEER (0,28), sostiene la atención latido a latido (inercia 0,32 → 0,57), cooldown de 15 latidos, cede ante alarma | **E** | Estrategia genérica de S3 «estudiar» para la intención **Saber**. Ya tiene progreso (latidos dedicados, L0 = 4, L1 = 2) y agotamiento (interrupción, cooldown): es la estrategia más parecida al modelo nuevo. Su inercia atencional se sustituye por el plus por estrategia activa (decisiones 4 y 23) |
| `PlanTecnologico` (Crafter, `crafter.py:396`) | Árbol de recetas: logros oportunistas (minerales, retoño, plantar), dormir de día con energía ≤ 6, colocar/fabricar (USAR), ir a la mesa u horno por el hipocampo, buscar el material que falta | **E propia** (varias) | Estrategias de S3 de Crafter (decisión 11): «plan tecnológico» (el plan como secuencia de pasos hacia la intención «progresar», decisión 13), «logros al alcance» y «retoño». «Dormir de día para afrontar la noche» es anticipación: pertenece a la prospectiva (decisión 24, bloque F); mientras tanto, estrategia de Crafter para **Descanso**. Ver riesgo 5 |
| `Prudencia` (archivos, `archivos.py:315`) | Frena COMER con indicios de daño (aunque sea hipótesis) y la neofobia; recuerda carpetas con solo veneno, frena volver y propone otra carpeta | **M propia** + **E propia** | Modulación de S3 del mundo de archivos, gradual según la confianza (encaja con la decisión 13) sobre Alimentación y la elección de objeto; y estrategia de S3 del mundo «buscar comida en otra carpeta» para **Alimentación**, con su memoria de carpetas malas como estado de la estrategia |

### Core

| Origen | Qué hace hoy | Destino | Correspondencia propuesta |
|---|---|---|---|
| `_candidato_core(DORMIR, "agotamiento")` (`latido.py:144`) | Si min(energía, descanso) ≤ 5: candidato DORMIR con arousal 1,0 | **I** (o se queda) | Opción A (propuesta): desaparece; el impulso **Descanso** llega a arousal ≈ 1 con cansancio extremo y gana por arousal (decisión 4). Opción B: se queda como límite fisiológico del Core. **A decidir por el autor** (riesgo 3) |
| `_candidato_core(DORMIR o ESPERAR, "sigue dormido")` (`latido.py:228`) | Mientras duerme, mantiene el sueño | **Se queda** | Es parálisis del sueño, no una decisión: los sistemas no corren dormidos. Sigue en el Core; en C1.6 pasa a escribir con autor |
| `Tribunal`: ESPERAR sin candidatos; ACECHAR | Sin candidatos, ESPERAR; con poca confianza y sin urgencia, ACECHAR | **Se queda** (revisar) | «No actuar también es una opción» (decisión 3). El acecho no está en la regla inicial del Tribunal (decisión 23): ver riesgo 1 |

## 4. Reflejos

| Reflejo | Disparo (cambio brusco del Sentir) | Duración | Acción |
|---|---|---|---|
| S1 «sobresalto / empezar a huir» | Δ peligro (alarma de `ev` − alarma de `ei`) ≥ umbral, por ejemplo 0,4 (parámetro del `Perfil`, a calibrar en C1) | 2-3 latidos fijos | MOVER al lugar más seguro; si no hay salida y la amenaza está al alcance, ATACAR |
| S2 `Exteriorizacion` | Siempre (expresión involuntaria) | 1 latido | Ninguna (solo `ef`) |

## 5. Feedback por sistema

| Sistema | Meta | Señal propuesta (por latido) | Datos que ya existen |
|---|---|---|---|
| S1 | Supervivencia | Bajada de los déficits del cuerpo: −Δ(hambre + cansancio + peligro + (100 − vitalidad)/100), y por impulso, la bajada de su intensidad cruda (es el progreso de sus estrategias) | `soma.hambre()`, `soma.cansancio()`, `alarma.peligro`, `soma.vitalidad` |
| S2 | Valor | Mejora del placer y de la valencia: Δ placer − Δ estrés; por impulso propio (Exploración), la bajada de la novedad pendiente | `soma.placer`, `soma.estres`, pieza `Emocion` (A5). `Soma` no tiene valencia explícita (nota del bloque A para D) |
| S3 | Verdad | Bajada del error de predicción: −\|rpe\| medio y tasa de sorpresas (`Memoria.aprender` → `ap.rpe`, `ap.sorpresa`); para Saber, hipótesis contrastadas | `memoria.aciertos`, `memoria.fallos`, `ap.rpe` |

## 6. Riesgos

1. **Regla del Tribunal.** Hoy, en calma, manda la **confianza** (`base = arousal × estrés + confianza × (1 − estrés)`), hay sesgo de experiencia y acecho. La regla inicial de la decisión 23 puntúa solo por arousal + plus. Cambiarla a la vez que todo C1 mezcla dos efectos. **Propuesta:** en C1.4 mantener la `base` actual y añadir solo el plus por estrategia activa; probar la regla solo-arousal en un paso aparte y medido.
2. **Reflejo solo ante cambios bruscos.** Hoy el reflejo salta por **nivel** de peligro (≥ `umbral_miedo`) y en Crafter el 100 % de las muertes son nocturnas por hostiles (`BENCHMARK_PERFILES_MUNDOS.md`). Si el peligro sostenido queda solo en manos de estrategias con plus y agotamiento, la huida puede llegar tarde o abandonarse. Las estrategias de Seguridad deben tener arousal alto y no agotarse mientras el peligro siga alto.
3. **Necesidades críticas frente al plus** (cuestión abierta del borrador). Con plus 0,1 × (1 − agotamiento), una necesidad crítica debe superar a la estrategia activa: Descanso con agotamiento extremo, hambre crítica (hoy `alimentación ≤ 15` fuerza alarma 0,9 y urgencia en el Tribunal) y Seguridad. Comprobar en C1 que los arousales llegan cerca de 1 (decisión 4).
4. **Valoración y frenos por objeto.** `S2.Impulso`, `S3.Impulso` y `Prudencia` actúan sobre **una acción concreta** (este objeto vale, este se sabe peligroso). Si la modulación pasa a piezas `Impulso` (decisión 14), «comer» sube o baja entero y se pierde el «no comas *esto*». Hace falta que las estrategias elijan el objeto leyendo `Valor` y lo demostrado (leer es libre, decisión 22). Afecta a C2 y C3; conviene fijarlo antes de C2.
5. **El mundo percibe; IdA piensa (regla 3 de `AGENTS.md`).** `DefensaCrafter` lee `mundo.inventario()` y `jugador.health`; `PlanTecnologico` lee `env._world` (casillas, luz) y la posición del jugador. Como estrategias propias de Crafter pueden conocer su vocabulario, pero deberían leer lo **percibido** (Interocepción, Propiocepción, Exterocepción). Mover esas lecturas a la percepción cambia el sensor de Crafter; propuesta: hacerlo en C1 solo para lo que usa `DefensaCrafter` (espada, salud) y dejar `PlanTecnologico` para C3. La percepción de la luz (`a7adb3f`) encaja aquí.
6. **Mundos sin ESPERAR y de un paso.** Snake no admite esperar y hoy depende del «mal menor»; no se puede medir con el protocolo (web en tiempo real). En ajedrez cada latido es una jugada y no hay componentes propios: la persistencia de una estrategia puede no aportar. El benchmark de C1 no cubre ninguno de los dos; propongo al menos la invariancia de que siguen funcionando (partidas completas) y una vida de Snake manual.
7. **Control sin experiencia.** El valor aprendido por estrategia (C1, detalle de elección) es experiencia. Con `sin_experiencia`, propongo elegir estrategia sin ese valor (innato fijo) para que el control siga limpio.
8. **Coste de atención.** Cada latido añade piezas `Impulso` (3-5) y `Estrategia` (las activas). Con los márgenes de B0 (p95 de 17 a 55 piezas frente a una amplitud de 50 a 120) cabe, pero aumenta la diferencia con la calibración aplazada tras C.

## 7. Decisiones que pido al autor

1. ¿Se aprueban los cinco impulsos de la sección 2 (y que Descanso sea de S1)?
2. `_candidato_core(DORMIR)` por agotamiento: ¿opción A (impulso Descanso) u opción B (límite del Core)?
3. Regla del Tribunal en C1: ¿mantener la `base` actual + plus (propuesta) o pasar ya a solo arousal + plus?
4. Umbral del reflejo por cambio brusco: ¿parámetro del `Perfil` con valor inicial 0,4, a medir en C1?
5. Riesgo 5: ¿se mueve a la percepción lo que usa `DefensaCrafter` dentro de C1?
6. Riesgo 4: ¿se adelanta a C1 el mecanismo de «la estrategia elige objeto leyendo `Valor` y lo demostrado», o se deja para C2?
