# IdA — Plan de implementación del rediseño

Nov 16, 2026 · @Diego

El rediseño de la base se implementa en seis bloques, de lo más claro y menos invasivo a lo más rompedor. Cada bloque es un encargo cerrado para el agente, con el borrador completo como referencia.

## Orden de los bloques

&#91;embedded content: orden de los bloques · preparación y A a F, con sus condiciones de paso\]

No se empieza un bloque sin que el anterior cumpla su condición de paso. Si un bloque empeora la conducta, se analiza antes de seguir y se publica el resultado.

## Preparación antes del bloque A

Cinco pasos, en este orden, antes de dar el primer encargo al agente. **Hecha el 16/11/2026** en la rama `prep/rediseno-base`, sin integrar todavía en `main`.

- [x] **Corregir las métricas públicas.** El README y `05_METRICAS_E_HITOS.md` decían 10,9 logros en Crafter. Con el protocolo aislado, `5c8ae1e` da 9,30 ± 1,09 y `25e1303` (mismo árbol que `7e335ae`) da 9,13 ± 1,42 (diferencia pareada −0,17 ± 1,42). Cambio explicado en el CHANGELOG (`d1af17a`). Además, `05_METRICAS_E_HITOS.md` pasa de 64 a 85 tests y deja de describir `self.hitos` (`de6b01d`).
- [x] **Fusionar `feature/ajustes-cognitivos` en `main`.** Ya estaba fusionada por el PR #4: `main` está en `7e335ae`, con el mismo árbol que `25e1303`. En `7e335ae`, pytest da 85 passed, ruff no da errores y mypy no encuentra problemas en 38 ficheros (Python 3.15.1, 16/11/2026).
- [x] **Pausar la Fase 5.** `feature/fase5-ciclo-y-refugio` y `feature/fase5-ritmo-y-vaiven` quedan pausadas y, en principio, descartadas. Sus impulsos (cobijo) y estrategias (anidar, refugio) se reharán en el bloque C con el nuevo modelo. No se rescata nada, tampoco la percepción de la luz (`a7adb3f`).
- [x] **Exportar el borrador del rediseño a `docs/REDISENO_BASE.md`.** Es la referencia fija del agente para todos los bloques: el contexto completo, aunque cada encargo implemente solo una parte (`4934fb9`).
- [x] **Actualizar `AGENTS.md`** para que remita a `docs/REDISENO_BASE.md` y a este plan. La regla de no tocar `ida/core/` ni `ida/sistemas/` se mantiene, con el permiso que conceda cada encargo para su bloque (`80850dc`).

## Encargo del bloque A: renombres y refactors sin cambio de conducta

**Objetivo:** dejar el código con los nombres y la estructura del rediseño sin que IdA se comporte distinto. Cada paso debe dar la misma conducta con la misma semilla.

**Referencia:** `docs/REDISENO_BASE.md` (decisiones 1, 3, 8, 9, 12, 14 y 15). **Rama base:** `main` en `7e335ae`. Las rutas y líneas de abajo están comprobadas en ese commit el 16/11/2026; verifícalas de nuevo con `grep` antes de cada paso.

### Permiso

Se autoriza modificar `ida/core/` e `ida/sistemas/` **solo** para los pasos de este bloque, con un commit por paso y su justificación. Nada de `push` sin permiso.

### Pasos (un commit cada uno)

| Paso | Cambio | Decisión | Archivos afectados (en `7e335ae`) | Cuidado |
| --- | --- | --- | --- | --- |
| A1 | `Escena` pasa a `Exterocepcion`: componente y canal | 1 | `core/sentidos.py`, `core/latido.py`, `core/pieza.py`, `sistemas/comun.py`, `s1.py`, `s3.py`, `mundos/minimo.py`, `archivos.py`, `crafter.py`, `tests/test_core.py` | También en los componentes propios de los mundos |
| A2 | Pieza y canal `Ejecucion` pasan a `Accion` | 3 | `core/arquitectura.py`, `latido.py`, `onda.py`, `pieza.py`, `sentidos.py`, `s1.py`, `s2.py`, `s3.py`, `mundos/archivos.py`, `crafter.py`, `consola.py`, `tests/test_core.py`, `test_organismo.py`, `test_biblioteca.py` | La dimensión `acc` de la Onda no cambia de nombre |
| A3 | `ImpulsoS1/S2/S3` pasan a `Impulso` en cada módulo | 14 | `s1.py`, `s2.py`, `s3.py` | Cambian etiquetas en `entradas` y en los tiempos por componente |
| A4 | Nuevo componente `Objeto`, primero de S1·Interpretar, que emite las piezas `Objeto` que hoy emite `Imagen` | 8 | `s1.py` (hoy en `Imagen.reactiva`, líneas 43-46) | Mismo coste por pieza (hoy 1), mismo orden de emisión y mismo límite `MAX_OBJETOS` |
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

## Bloques B a F

Se detallan como encargo cuando termine el anterior. A partir del bloque B la conducta cambia a propósito, así que cada bloque se mide con el protocolo de `docs/BENCHMARK_PERFILES_MUNDOS.md` (N = 10 linajes, t de Student, comparación pareada) frente al bloque anterior y frente al control sin memoria.

| Bloque | Contenido | Decisiones | Claridad | Invasivo | Riesgo principal |
| --- | --- | --- | --- | --- | --- |
| B. Reglas de la Onda | Propiedad de piezas por tipo; metadatos *decay* y *audit*; potencia; coste proporcional al cambio, nada gratis en los sistemas; prioridad por orden de sistema | 7, 14, 15, 18 | Alta | Medio | Quitar la modulación gratis de `Impulso` en S2 cambia la conducta; con menos presupuesto, S3 puede quedarse sin turno |
| C. El nuevo bucle | Etapa Actuar en cada sistema; `Estrategia` con progreso y agotamiento; `Accion`; feedback por sistema; reflejo solo ante cambios bruscos; regla inicial del `Tribunal`; defensas, `Curiosidad` y `Hogar` pasan a impulsos y estrategias; `Intencion` y control de S3 | 3 a 6, 10, 11, 13, 16, 17, 23 | Media | Alto | Sustituye cómo decide IdA hoy. Conviene dividirlo en sub-bloques (por ejemplo, primero S1 y después S2 y S3) |
| D. Relaciones más ricas | Habituación en `Supervivencia`; dimensiones de `Valor`; `Creencia` con fuentes | 8, 9, 12 | Media | Medio | Hay que concretar sus datos antes |
| E. Memoria | Guardado día y noche; instancias y conceptos; reducción nocturna y repaso; recuperación; herencia configurable | 19 a 22 | Media-baja | Alto | El fitness puede empeorar. Cada mecanismo se activa y desactiva por separado y se introduce de uno en uno |
| F. Experiencia proactiva | Primero Expectativa y Plan; después Prospectiva e Imaginación | 24 | Baja | Medio | Solo está planteada; necesita diseño antes de encargarse |

## Registro de cambios

| Fecha | Cambio |
| --- | --- |
| 2026-11-16 | Creación del plan: preparación, encargo del bloque A, resumen de los bloques B a F. |
| 2026-11-16 | Preparación hecha en `prep/rediseno-base`. Rama base: `main` en `7e335ae`. Las dos ramas de la Fase 5 quedan descartadas, sin rescatar la luz. Rutas del bloque A comprobadas en `7e335ae` (A2 suma `onda.py`, `pieza.py` y `test_biblioteca.py`; A4 pasa a las líneas 43-46). |
