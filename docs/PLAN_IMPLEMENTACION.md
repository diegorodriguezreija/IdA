# IdA — Plan de implementación del rediseño

Nov 16, 2026 · @Diego

El rediseño de la base se implementa en seis bloques, de lo más claro y menos invasivo a lo más rompedor. Cada bloque es un encargo cerrado para el agente, con el borrador completo como referencia.

## Orden de los bloques

&#91;embedded content: orden de los bloques · preparación y A a F, con sus condiciones de paso\]

No se empieza un bloque sin que el anterior cumpla su condición de paso. Si un bloque empeora la conducta, se analiza antes de seguir y se publica el resultado.

## Preparación antes del bloque A

Cinco pasos, en este orden, antes de dar el primer encargo al agente.

- [x] **Corregir las métricas públicas.** El README y `05_METRICAS_E_HITOS.md` siguen diciendo 10,9 logros en Crafter. Con el protocolo aislado, `main` da 9,30. Explicar el cambio en el CHANGELOG.
- [x] **Fusionar `feature/ajustes-cognitivos` en `main`.** Será la rama base: saca el mapa de Crafter del mundo y lo lleva al Core, corrige el control sin experiencia y el fitness de Archivos, e incluye el protocolo de benchmark. No hay diferencias detectadas frente a `main`.
- [x] **Pausar la Fase 5 v2.** Sus impulsos (cobijo) y estrategias (anidar) se reharán en el bloque C con el nuevo modelo. Solo se rescata la percepción de la luz, que no cambia la conducta.
- [x] **Exportar el borrador del rediseño a `docs/REDISENO_BASE.md`.** Es la referencia fija del agente para todos los bloques: el contexto completo, aunque cada encargo implemente solo una parte.
- [x] **Actualizar `AGENTS.md`** para que remita a `docs/REDISENO_BASE.md` y a este plan. La regla de no tocar `ida/core/` ni `ida/sistemas/` se mantiene, con el permiso que conceda cada encargo para su bloque.

Estado (16/11/2026): preparación hecha en la rama `prep/rediseno-base`. `feature/ajustes-cognitivos` ya estaba fusionada (`main` = `7e335ae`). En `main` actual, Crafter da 9,13 ± 1,42 logros (9,30 en `5c8ae1e`; diferencia no significativa). Las dos ramas de la Fase 5 (`feature/fase5-ciclo-y-refugio` y `feature/fase5-ritmo-y-vaiven`) quedan pausadas; de ellas solo se rescata el commit `a7adb3f` (percepción de la luz) cuando un bloque la necesite (la anticipación de la noche o las estrategias de refugio); no entra en el bloque A.

## Encargo del bloque A: renombres y refactors sin cambio de conducta

**Estado (16/11/2026): hecho** en `feature/bloque-a`, desde `main` en `069c5d5`. Siete pasos, todos con la misma conducta en los cuatro mundos (misma decisión por latido, mismas constantes vitales, misma puntuación). Nueva herramienta `herramientas/invariancia.py`, que congela el reloj de la Onda solo dentro de la herramienta. `Marcapasos` quedó como atributo sustituible de `Organismo`, no como componente, porque se ejecuta antes de que exista la Onda. Pendiente: actualizar nombres en la documentación y abrir el PR.

**Objetivo:** dejar el código con los nombres y la estructura del rediseño sin que IdA se comporte distinto. Cada paso debe dar la misma conducta con la misma semilla.

**Referencia:** `docs/REDISENO_BASE.md` (decisiones 1, 3, 8, 9, 12, 14 y 15). La rama base es \`main\` en \`7e335ae\`. Las rutas y líneas de abajo son de un `main` (`5c8ae1e`); verifícalas con `grep` en la rama base.

### Permiso

Se autoriza modificar `ida/core/` e `ida/sistemas/` **solo** para los pasos de este bloque, con un commit por paso y su justificación. Nada de `push` sin permiso.

### Pasos (un commit cada uno)

| Paso | Cambio | Decisión | Archivos afectados (en `main`) | Cuidado |
| --- | --- | --- | --- | --- |
| A1 | `Escena` pasa a `Exterocepcion`: componente y canal | 1 | `core/sentidos.py`, `core/latido.py`, `core/pieza.py`, `sistemas/comun.py`, `s1.py`, `s3.py`, `mundos/minimo.py`, `archivos.py`, `crafter.py`, `tests/test_core.py` | También en los componentes propios de los mundos |
| A2 | Pieza y canal `Ejecucion` pasan a `Accion` | 3 | `core/arquitectura.py`, `latido.py`, `sentidos.py`, `s1.py`, `s2.py`, `s3.py`, `mundos/archivos.py`, `crafter.py`, `consola.py`, `tests/test_core.py`, `test_organismo.py` | La dimensión `acc` de la Onda no cambia de nombre |
| A3 | `ImpulsoS1/S2/S3` pasan a `Impulso` en cada módulo | 14 | `s1.py`, `s2.py`, `s3.py` | Cambian etiquetas en `entradas` y en los tiempos por componente |
| A4 | Nuevo componente `Objeto`, primero de S1·Interpretar, que emite las piezas `Objeto` que hoy emite `Imagen` | 8 | `s1.py` (hoy en `Imagen.reactiva`, líneas 46-48) | Mismo coste por pieza (hoy 1), mismo orden de emisión y mismo límite `MAX_OBJETOS` |
| A5 | Nuevo componente `Emocion` en S2·Sentir, después de `Patron`: emite el estado afectivo de `Soma` como pieza | 9 | `s2.py` | Coste 0 en este bloque; ningún componente la consume todavía |
| A6 | `PredicadoProposicion` se divide en `Predicado` (pasada reactiva) y `Proposicion` (pasada activa) | 12 | `s3.py` | Mismas entradas (`Agente`) en los dos, en la misma posición del módulo, para que la secuencia de emisiones no cambie |
| A7 | La lógica de `Soma.presupuesto` pasa a un componente `Marcapasos` del Core, que devuelve frecuencia y amplitud | 15 | `core/soma.py`, `latido.py`, `tests/test_core.py` | Misma fórmula. La potencia no se añade hasta el bloque B |

### Fuera de alcance

- Todo lo de los bloques B a F, aunque esté en `docs/REDISENO_BASE.md`.
- Cualquier cambio de conducta: costes, reglas de la Onda, eliminar `Curiosidad`, `Hogar` o las defensas, cambiar `Comportamiento`.
- Añadir `Creencia`, `Intencion`, `Estrategia` o la etapa Actuar.

### Verificación en cada paso

```bash
python -m pytest -q
ruff check ida tests
mypy ida
```

- **Invariancia de conducta** en `minimo`, `archivos`, `crafter` y `ajedrez`, semillas 1 a 3, 400 latidos, antes y después del paso. Se compara la **secuencia de decisiones** (verbo y objetivo en cada latido), las constantes vitales y la puntuación final, no la salida completa: los renombres cambian etiquetas y la salida incluye tiempos.
- `tests/test_pureza.py` no se relaja.

### Entrega

- Un commit por paso, con el resultado de la invariancia en el mensaje.
- Lista de nombres cambiados (para panel, telemetría y documentación).
- **Datos guardados:** si `datos/` o los linajes guardan nombres de tipos de pieza, indicar si hace falta migrarlos o empezar de cero.
- Si algún paso no puede ser invariante, detenerse y explicar por qué, sin seguir con el siguiente.

## Encargo del bloque B: reglas de la Onda

**Estado (16/11/2026): hecho** en `feature/bloque-b`. Benchmark idéntico a `main` (Δ = 0,00 en todo; 660 vidas por versión). Con potencia = amplitud y la amplitud por defecto, la atención casi nunca escasea: 0 latidos con el plazo agotado y 5 de 37 194 con S3 sin recursos (Archivos). Se acepta como infraestructura; **la calibración de la escasez se hace después del bloque C**, porque C cambia lo que se emite. Mediciones en `docs/MEDICIONES_BLOQUE_B.md`; nuevas herramientas `herramientas/benchmark.py` y `herramientas/consumo.py`. Corrección al encargo: el componente de S2 que emitía gratis era `Sujeto`, no `Patron`.

**Objetivo:** que la Onda haga cumplir la propiedad de las piezas y gestione la atención con frecuencia, amplitud y potencia. Los pasos B1 y B2 no deben cambiar la conducta; B3 y B4 la cambian a propósito y se miden al final.

**Referencia:** `docs/REDISENO_BASE.md`, decisiones 7, 14, 15 y 18. Base: `main` con el bloque A fusionado.

### Permiso

Se autoriza modificar `ida/core/` e `ida/sistemas/` **solo** para los pasos de este bloque, con un commit por paso. Nada de `push` sin permiso.

### Pasos (un commit cada uno)

| Paso | Cambio | Decisión | ¿Cambia la conducta? | Cuidado |
| --- | --- | --- | --- | --- |
| B0 | Medir el consumo actual por latido y por sistema: piezas emitidas, coste de atención, suma de arousal otorgado y cambios de arousal en piezas ajenas. Sin tocar `ida/` | 15 | No | Base para fijar los valores por defecto de B3 |
| B1 | La Onda hace cumplir la propiedad: emitir o modificar solo piezas del tipo del componente, mediante operaciones de la Onda que dejan constancia en el *audit*. Modificar ya no es mutar la pieza directamente | 14 | No | Excepciones **transitorias**, listadas y registradas, hasta el bloque C: cualquier componente puede proponer `Accion`, y `Impulso` puede modular el arousal de `Accion`. El Core queda exento |
| B2 | Metadatos de la pieza: *decay* y *audit* (creación, actualización, origen y registro de cambios, con tamaño acotado) en todas; *fitness* y *cost* opcionales | 7 | No | Nada los consume todavía |
| B3 | Potencia en la Onda y nuevo sentido de la amplitud. `Marcapasos` devuelve frecuencia, amplitud y potencia. Cada pieza nueva en lo percibido o propuesto cuesta 1 de amplitud; otorgar o cambiar arousal cuesta potencia, en proporción al cambio, al subir y al bajar. El cambio máximo por pieza es potencia / amplitud. Dentro de los sistemas, nada gratis | 15, 18 | Sí | Pasan a pagar las emisiones con coste 0 (`Patron`, `Agente`, `Predicado`). Escribir solo en el estado final (`registrar`) sigue sin coste, porque no es atención. Valores por defecto a partir de B0, documentados |
| B4 | Agotar amplitud o potencia ya no corta el latido: la operación se rechaza y el sistema sigue. Solo el plazo (frecuencia) devuelve la Onda al Core. Los recursos pasan de sistema a sistema en orden (S1, S2, S3) | 18 | Sí | Sin amplitud no se añaden piezas; sin potencia no se cambia arousal; lo demás sigue |

### Fuera de alcance

- Quitar las excepciones transitorias de B1 (es del bloque C, cuando existan `Estrategia` y `Accion` como componentes).
- Que `Emocion` entre en lo percibido.
- Cualquier algoritmo adaptativo del `Marcapasos` más allá de los valores por defecto.
- Todo lo de los bloques C a F.

### Verificación

- **B1 y B2:** `pytest -q -x` y `herramientas/invariancia.py` en cada paso; deben dar OK.
- **B3 y B4:** `pytest -q -x` en cada paso. La invariancia fallará a propósito: no hace falta ejecutarla.
- **Al final del bloque, una sola vez:** `ruff` y `mypy`, y el benchmark con el protocolo de `docs/BENCHMARK_PERFILES_MUNDOS.md` (N = 10 linajes, t de Student, pareado) en `minimo`, `archivos` y `crafter`, perfiles Equilibrado, Valiente y Reactivo más el control sin experiencia, frente a `main`.
- **Criterio de paso:** sin pérdida significativa; en Crafter, no inferioridad con margen de −1 logro. Si empeora, analizar la causa antes de ajustar nada; los únicos ajustes permitidos son los valores por defecto del `Marcapasos`, documentados.

### Entrega

- Resultado de B0: consumo típico (mediana y percentil 95) por sistema y valores por defecto elegidos.
- Lista de excepciones transitorias de B1 y dónde se usan.
- Tabla del benchmark con intervalos de confianza y diferencias pareadas.
- **Indicadores nuevos:** latidos con el plazo agotado, latidos en los que S3 se quedó sin amplitud o potencia, y potencia media gastada por sistema.
- Si B3 o B4 empeoran la conducta, detenerse tras el benchmark y explicar la causa, sin seguir ajustando.

## Encargo del bloque C: el nuevo bucle

**Objetivo:** que IdA decida con impulsos, estrategias y acciones en lugar de con componentes que proponen acciones directamente. Es el bloque más grande, así que se divide en cuatro partes. **Cada parte es un encargo propio, con su benchmark, y no se empieza la siguiente sin aceptar la anterior.**

**Referencia:** `docs/REDISENO_BASE.md`, decisiones 3 a 6, 10, 11, 13, 16, 17 y 23. Base: `main` con los bloques A y B fusionados.

**Criterio del autor (16/11/2026):** hasta llegar al bloque E, una pérdida ligera de fitness es aceptable. La prioridad es completar el diseño base; el margen se recuperará después, mejorando los componentes propios de cada mundo. Las pérdidas se miden y se publican igualmente.

**Estrategias con fases:** buscar y consumir son fases de una misma estrategia (por ejemplo, alimentarse: buscar, acercarse, comer), no estrategias que compiten. A lo sumo son acciones distintas dentro de la misma máquina de estados. La regla de "ceder ante otra estrategia con mejor valor" que añadió el agente en C1.5 se revisa con esto; si se mantiene, debe exigir un margen claro (histéresis).

| Parte | Contenido | ¿Cambia la conducta? |
| --- | --- | --- |
| C0 | Inventario y propuesta de correspondencia. Sin código. **Se detiene para que el autor la apruebe** | No |
| C1 | Infraestructura del bucle y S1 completo | Sí |
| C2 | S2: impulsos propios, estrategias de valor, modulación sobre piezas `Impulso` | Sí |
| C3 | S3: `Intencion`, estrategias de conocimiento, control según certeza; se quitan las excepciones transitorias del bloque B | Sí |

### C0: inventario y correspondencia (sin código)

Entregar una tabla con **cada componente actual de Reaccionar en S1, S2 y S3, y cada componente propio de los mundos**, y en qué se convierte en el nuevo modelo:

- **impulso** (qué necesidad expresa y cómo se mide su intensidad cruda);
- **estrategia** (de qué sistema, para qué impulso, genérica o propia de un mundo);
- **reflejo** (estrategia innata corta ante un cambio brusco);
- **modulación** (qué impulsos sube o baja);
- o **desaparece**, con el motivo.

Incluir al menos `Reflejo`, los tres `Impulso`, `Curiosidad`, `Hogar`, `Orientacion`, `Comportamiento`, `Estudio`, `Exteriorizacion`, las defensas de los mundos, `PlanTecnologico` y `Prudencia`, y los candidatos que propone el Core (`_candidato_core`). Añadir la señal de **feedback** propuesta para cada sistema y los riesgos que se vean. **Detenerse aquí.**

### C1: infraestructura del bucle y S1

| Paso | Cambio | Decisión |
| --- | --- | --- |
| C1.1 | Tipo de pieza `Estrategia` en el Core: impulso de origen, valor inicial, objetivo, progreso, agotamiento, esfuerzo, latido de inicio y estado de la máquina. El Core conserva las estrategias activas entre latidos | 4, 16 |
| C1.2 | Etapa Actuar en cada sistema con un componente `Accion` que traduce la estrategia activa en una acción. La acción lleva su origen (impulso y estrategia) | 3, 17 |
| C1.3 | Feedback por sistema; en S1, si bajan los déficits del cuerpo | 5 |
| C1.4 | Regla inicial del `Tribunal`: arousal ya modulado + plus por estrategia activa, 0,1 × (1 − agotamiento); empate, azar | 4, 23 |
| C1.5 | S1 según la tabla aprobada en C0: `Impulso` emite piezas `Impulso` y deja de proponer acciones; `Estrategia` elige, mantiene y abandona estrategias; `Reflejo` solo ante cambios bruscos, como estrategia corta de máxima prioridad; las defensas de los mundos pasan a estrategias de S1 de su mundo | 6, 16, 17 |
| C1.6 | El Core escribe con autor (`_candidato_core`, `Sorpresa`) y `percibir` devuelve `None` si la pieza se rechaza | 14 |

**Detalles de C1:**

- **Progreso** medido sobre la intensidad cruda de la necesidad, no sobre el arousal modulado. La prioridad de la estrategia se apaga de forma gradual al acercarse al objetivo.
- **Agotamiento:** unos latidos de gracia (parámetro del `Perfil`); después crece con tiempo y esfuerzo si el ritmo de progreso es menor que el esperado. En C1, el ritmo esperado es un valor por defecto.
- **Elección de estrategia:** valor aprendido por estrategia e impulso, solo durante la vida (la memoria duradera es del bloque E); mérito por feedback, fuerza del aprendizaje por arousal; la apertura del arquetipo regula cuánto se prueba una estrategia distinta.
- **Vocabulario:** se mantiene el enum `Verbo` actual. Pasar el vocabulario exterior a cada mundo queda para después.
- **S2 y S3 siguen como hoy** en C1, con las excepciones transitorias del bloque B.

**Verificación de C1:** `pytest -q -x` por paso; al final, `ruff`, `mypy` y el benchmark (N = 10, pareado) frente a `main`. **Criterio de paso:** sin pérdida significativa; en Crafter, no inferioridad con margen de −1 logro. Si hay pérdida, detenerse y analizar la causa (por ejemplo, qué estrategias se abandonan antes de tiempo) antes de ajustar.

**Entrega de C1:** tabla del benchmark; latidos por estrategia y abandonos por agotamiento; cuántas veces gana el plus por estrategia activa; cuántas veces interrumpe un reflejo.

### Estado de C1 (16/11/2026)

Primer benchmark: Crafter mejora (Equilibrado +1,30 logros; Reactivo +1,63, significativo) y Archivos mejora el fitness (+170 a +193). Pérdidas en Mínimo y Archivos por más tóxicos comidos: S1 ofrecía una sola acción por necesidad y los frenos de S2 y S3 se quedaban sin alternativa. Correcciones aplicadas: `alimentarse` como una sola estrategia con fases (buscar → acercarse → comer) que elige el objeto por `Valor` y por lo demostrado, y se abstiene si solo hay algo dañino; sustitución con margen 0,2; umbral del reflejo escalado por `umbral_miedo`; `seguir_en_movimiento` como estrategia de S1. Diagnóstico rápido: setas comidas por Valiente en Mínimo, 10 (frente a 43 en `main`). Benchmark final: aceptado. Mínimo mejora en latidos (Equilibrado +172,5 ± 43,4; Reactivo +31,1 ± 28,6) y baja las setas en los tres perfiles; Archivos mejora latidos (+32 a +47), fitness (+322 a +405) y nutritivos (+6 a +7), con una pérdida ligera en tóxicos (+0,33 a +0,40 por vida); Crafter cumple la no inferioridad (+0,70 a +1,33 logros, sin significación). A vigilar: 3 de 10 vidas del Valiente en Mínimo murieron sin causa registrada.

### C2 y C3, en un solo encargo

Se juntan para ahorrar un benchmark: C1 ya adelantó la elección del objeto por `Valor` y lo demostrado, así que C2 y C3 son sobre todo trasladar componentes que ya funcionan al modelo nuevo. Se sigue la tabla aprobada en `docs/C0_CORRESPONDENCIA.md`.

| Paso | Cambio | Decisión |
| --- | --- | --- |
| C2.1 | S2: `Impulso` emite sus impulsos propios (Exploración: apertura × novedad) y deja de modular `Accion`, porque el "no comas esto" ya lo resuelve la elección del objeto | 10, 14 |
| C2.2 | S2: `Estrategia` con las estrategias de valor según el C0 (`Curiosidad`, `Hogar` y `Orientacion` dejan de ser componentes). Refugiarse elige el refugio que valora | 10 |
| C2.3 | Feedback de S2: placer y estrés | 5 |
| C3.1 | S3: `Intencion` (Saber y las intenciones que el C0 asigne) | 11 |
| C3.2 | S3: `Estrategia` con `Comportamiento`, `Estudio`, `PlanTecnologico` (Crafter) y `Prudencia` (Archivos) según el C0. `PlanTecnologico` deja de leer el estado interno del mundo y usa la percepción (regla 3) | 11, 13 |
| C3.3 | S3: `Impulso` como control gradual según la certeza, solo sobre piezas `Impulso` | 13 |
| C3.4 | Feedback de S3: error de predicción | 5 |
| C3.5 | Se quitan las dos excepciones de `EXCEPCIONES_TRANSITORIAS`: solo los componentes `Accion` proponen acciones y nadie modula piezas `Accion` ajenas | 14 |

**Fuera de alcance:** bloques D a F; pasar el vocabulario exterior a cada mundo; calibrar la escasez de atención (se hace después del bloque C).

**Verificación:** `pytest -q -x` por paso; al final, `ruff`, `mypy` y un solo benchmark (N = 10, pareado) frente a `main`. **Criterio:** hasta el bloque E, una pérdida ligera es aceptable; se mide y se publica. Informe: solo la tabla resumen y si se cumple el criterio; análisis detallado solo si no se cumple.

## Bloques B a F

Se detallan como encargo cuando termine el anterior. A partir del bloque B la conducta cambia a propósito, así que cada bloque se mide con el protocolo de `docs/BENCHMARK_PERFILES_MUNDOS.md` (N = 10 linajes, t de Student, comparación pareada) frente al bloque anterior y frente al control sin memoria.

| Bloque | Contenido | Decisiones | Claridad | Invasivo | Riesgo principal |
| --- | --- | --- | --- | --- | --- |
| B. Reglas de la Onda | Propiedad de piezas por tipo; metadatos *decay* y *audit*; potencia; coste proporcional al cambio, nada gratis en los sistemas; prioridad por orden de sistema | 7, 14, 15, 18 | Alta | Medio | Quitar la modulación gratis de `Impulso` en S2 cambia la conducta; con menos presupuesto, S3 puede quedarse sin turno |
| C. El nuevo bucle | Etapa Actuar en cada sistema; `Estrategia` con progreso y agotamiento; `Accion`; feedback por sistema; reflejo solo ante cambios bruscos; regla inicial del `Tribunal`; defensas, `Curiosidad` y `Hogar` pasan a impulsos y estrategias; `Intencion` y control de S3 | 3 a 6, 10, 11, 13, 16, 17, 23 | Media | Alto | Sustituye cómo decide IdA hoy. Conviene dividirlo en sub-bloques (por ejemplo, primero S1 y después S2 y S3) |
| D. Relaciones más ricas | Habituación en `Supervivencia`; dimensiones de `Valor`; `Creencia` con fuentes | 8, 9, 12 | Media | Medio | Hay que concretar sus datos antes |
| E. Memoria | Guardado día y noche; instancias y conceptos; reducción nocturna y repaso; recuperación; herencia configurable | 19 a 22 | Media-baja | Alto | El fitness puede empeorar. Cada mecanismo se activa y desactiva por separado y se introduce de uno en uno |
| F. Experiencia proactiva | Primero Expectativa y Plan; después Prospectiva e Imaginación | 24 | Baja | Medio | Solo está planteada; necesita diseño antes de encargarse |

**Notas del bloque A para los siguientes:**

- **B:** emisiones con coste 0 que pasarán a pagar: `Patron`, `Agente`, `Predicado`; `Exteriorizacion` y `Emocion` escriben a coste cero solo en el estado final.
- **B:** decidir si `Emocion` entra en lo percibido. Si entra, cambia la tensión y la apertura de episodios, porque `latido.py` recorre esos canales (líneas 233, 249 y 257 en la rama del bloque A).
- **B:** al añadir la potencia, `Marcapasos` puede seguir como está o recibir los indicadores de cada sistema.
- **D:** `Soma` no calcula una valencia explícita, y la decisión 9 la necesita. Hoy `Emocion` emite el estrés como arousal, y el afecto y el placer en la carga.
- `memoria.db` guarda filas antiguas con el tipo `Escena`; no afecta a la conducta (la tabla no se lee).

**Notas del bloque B para los siguientes:**

- **C:** quitar las dos excepciones transitorias de `EXCEPCIONES_TRANSITORIAS` (`ida/core/onda.py`): cualquier componente propone `Accion`, y `Impulso` modula arousal y confianza de `Accion` (hoy en `S2.Impulso`, `S3.Impulso` y `Prudencia`).
- **C:** el Core escribe piezas sin autor (`_candidato_core` y la pieza `Sorpresa`); `Componente.percibir` devuelve la pieza aunque se haya rechazado.
- **Después de C:** barrido pequeño del `Marcapasos` (dos o tres niveles de amplitud y potencia, Crafter y Mínimo) para comprobar que la atención escasa estrecha el foco con peligro sin hundir el fitness.

## Registro de cambios

| Fecha | Cambio |
| --- | --- |
| 2026-11-16 | Creación del plan: preparación, encargo del bloque A, resumen de los bloques B a F. |
| 2026-11-16 | Preparación completada; base main en 7e335ae; paso A8 añadido (percepción de la luz, commit a7adb3f). |
| 2026-11-16 | Quitado el paso A8: la percepción de la luz se rescatará cuando un bloque la necesite. |
| 2026-11-16 | Bloque A hecho (feature/bloque-a, invariancia OK). Notas del bloque A para B y D. |
| 2026-11-16 | Encargo del bloque B (pasos B0 a B4). |
| 2026-11-16 | Bloque B hecho (feature/bloque-b, sin diferencias en el benchmark). Calibración de la escasez aplazada a después de C. Notas del bloque B para C. |
| 2026-11-16 | Encargo del bloque C: partes C0 a C3; C0 y C1 detallados. |
| 2026-11-16 | Bloque C: criterio de pérdida ligera aceptable hasta E; estrategias con fases (buscar y consumir en la misma estrategia). |
| 2026-11-16 | Estado de C1 tras correcciones; C2 y C3 en un solo encargo. |
| 2026-11-16 | C1 aceptado tras el benchmark final. Lanzados C2 y C3. |
