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

## Registro de cambios

| Fecha | Cambio |
| --- | --- |
| 2026-11-16 | Creación del plan: preparación, encargo del bloque A, resumen de los bloques B a F. |
| 2026-11-16 | Preparación completada; base main en 7e335ae; paso A8 añadido (percepción de la luz, commit a7adb3f). |
| 2026-11-16 | Quitado el paso A8: la percepción de la luz se rescatará cuando un bloque la necesite. |
| 2026-11-16 | Bloque A hecho (feature/bloque-a, invariancia OK). Notas del bloque A para B y D. |
| 2026-11-16 | Encargo del bloque B (pasos B0 a B4). |
