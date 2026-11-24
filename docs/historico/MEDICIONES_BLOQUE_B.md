# Mediciones del bloque B (reglas de la Onda)

Encargo en [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md); decisiones 7, 14, 15 y 18 de [`REDISENO_BASE.md`](REDISENO_BASE.md).

## B0. Consumo de atención antes del bloque B

- **Comando:** `python herramientas/consumo.py` (semillas 1 a 3, una vida de 400 latidos por semilla, directorio limpio, reloj de la Onda congelado).
- **Código:** `main` con el bloque A fusionado (`718f734`), sin cambios en `ida/`. Fecha: 16/11/2026, Windows 10, Python 3.15.1.
- **Unidad:** un latido despierto y un sistema. «Piezas»: piezas nuevas en `ev` o `acc`, con o sin coste. «Coste»: amplitud cobrada. «Arousal»: suma del arousal otorgado a esas piezas. «Ajeno»: suma de |Δ arousal| en piezas de `ev`/`acc` de otro sistema.

Mediana / percentil 95:

| Mundo (latidos) | Sistema | Piezas | Coste | Arousal | Ajeno |
|---|---|---|---|---|---|
| Mínimo (623) | S1 | 10 / 15 | 10 / 15 | 3,54 / 6,07 | 0 / 0 |
| | S2 | 12 / 19 | 8 / 13 | 3,62 / 6,22 | 0 / 0,10 |
| | S3 | 8 / 13 | 2 / 4 | 2,12 / 3,61 | 0 / 0,33 |
| | Total | 30 / 45 | 20 / 31 | 9,61 / 15,18 | 0 / 0,40 |
| Archivos (659) | S1 | 4 / 10 | 4 / 10 | 0,63 / 5,61 | 0 / 0 |
| | S2 | 5 / 11 | 4 / 8 | 0,73 / 4,60 | 0 / 0,08 |
| | S3 | 3 / 10 | 1 / 4 | 0,80 / 3,30 | 0,38 / 0,97 |
| | Total | 12 / 29 | 9 / 20 | 2,54 / 13,73 | 0,40 / 0,97 |
| Crafter (582) | S1 | 17 / 18 | 17 / 18 | 2,37 / 7,83 | 0 / 0 |
| | S2 | 21 / 22 | 14 / 15 | 3,83 / 6,65 | 0 / 0,08 |
| | S3 | 14 / 16 | 1 / 3 | 2,45 / 3,95 | 0 / 0 |
| | Total | 52 / 55 | 32 / 34 | 9,71 / 17,98 | 0 / 0,08 |
| Ajedrez (124) | S1 | 3 / 7 | 3 / 7 | 0,39 / 5,03 | 0 / 0 |
| | S2 | 0 / 6 | 0 / 4 | 0 / 1,84 | 0 / 0 |
| | S3 | 0 / 4 | 0 / 0 | 0 / 0,95 | 0 / 0 |
| | Total | 3 / 17 | 3 / 11 | 0,39 / 7,86 | 0 / 0 |

- Amplitud máxima por latido, mediana: mínimo 100, archivos 90, Crafter 106, ajedrez 120. Despierto, la fórmula del `Marcapasos` no baja de la mitad de la amplitud base (Crafter: 60).
- Guillotinas: 0 en los cuatro mundos.
- La diferencia entre «piezas» y «coste» son las emisiones a coste 0 de los sistemas: `Sujeto` (S2), `Agente` y `Predicado` (S3).

## Valores por defecto elegidos (B3)

- **Frecuencia y amplitud:** la fórmula anterior (`Soma.presupuesto`, ahora `Marcapasos.ritmo`).
- **Potencia = amplitud** (`Marcapasos.FUERZA_POR_PIEZA = 1`). Fuerza máxima por pieza = potencia / amplitud = 1: ninguna pieza ve recortado un arousal de 0 a 1. Con un factor menor, cualquier reflejo de arousal 1 quedaría recortado en todos los latidos.
- Con estos valores, en B0 el p95 del arousal otorgado por latido (8 a 18) queda muy por debajo de la potencia (50 a 120), y el p95 de piezas nuevas (17 a 55) por debajo de la amplitud: los recursos solo se agotan en latidos atípicos. Lo que cambia en las reglas con B3 es que `Sujeto`, `Agente` y `Predicado` pasan a pagar, que sustituir un candidato ya no cuesta amplitud y que modificar arousal cuesta potencia.

## Benchmark al final del bloque (B1 a B4)

- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F` y `python herramientas/benchmark.py comparar base.json nueva.json`.
- **Versiones:** base = `main` (`718f734`, bloque A); nueva = `feature/bloque-b` (`e194e1a`).
- **Protocolo** (el de [`BENCHMARK_PERFILES_MUNDOS.md`](../BENCHMARK_PERFILES_MUNDOS.md)): N = 10 linajes (semillas 1 a 10, directorio limpio por semilla); mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600. Grupos: perfiles Equilibrado, Valiente y Reactivo, y control sin experiencia (Equilibrado con `sin_experiencia`). Media por linaje; IC 95 % con t(0,975; 9) = 2,262; diferencia pareada por semilla. Reloj real. 1 320 vidas en total (660 por versión). Fecha: 16/11/2026, Windows 10, Python 3.15.1.

### Resultado

**Todas las métricas son idénticas en las dos versiones: Δ = 0,00 ± 0,00** en cada grupo y mundo (latidos, fitness, setas, nutritivos, tóxicos y logros).

| Mundo | Grupo | Métrica principal (base = nueva) |
|---|---|---|
| Mínimo | Equilibrado / Valiente / Reactivo / Sin experiencia | Latidos 174,28 ± 39,42 / 312,77 ± 40,31 / 355,52 ± 27,43 / 177,40 ± 33,40 |
| Archivos | Equilibrado / Valiente / Reactivo / Sin experiencia | Fitness 924,25 ± 174,38 / 960,40 ± 168,50 / 904,05 ± 115,09 / 280,60 ± 239,13 |
| Crafter | Equilibrado / Valiente / Reactivo / Sin experiencia | Logros 9,13 ± 1,42 / 10,40 ± 1,04 / 8,57 ± 1,40 / 9,40 ± 1,41 |

Las cifras base coinciden con las de `ajustes` en `BENCHMARK_PERFILES_MUNDOS.md` (mismo árbol más el bloque A, invariante).

### Indicadores nuevos (versión nueva)

| Mundo | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media por latido S1 / S2 / S3 (Equilibrado) |
|---|---|---|---|---|
| Mínimo | 40 799 | 0 | 0 | 3,45 / 3,53 / 2,38 |
| Archivos | 37 194 | 0 | 5 (1, 1, 3 y 0 por grupo) | 1,95 / 1,68 / 1,72 |
| Crafter | 30 190 | 0 | 0 | 2,42 / 2,69 / 1,88 |

La potencia media incluye los latidos dormido (sin gasto). El control sin experiencia gasta menos en S2 y S3 (mínimo: 3,02 / 2,20 / 0,94).

### Lectura

- Criterio de paso cumplido: sin pérdida; en Crafter, Δ = 0 frente al margen de −1 logro.
- Con los valores por defecto (potencia = amplitud), las reglas nuevas **no llegan a actuar** en la práctica: la amplitud no se agota, la potencia solo se queda corta en 5 de 37 194 latidos de archivos (sin efecto en las métricas por vida; las decisiones latido a latido no se han comparado) y la fuerza máxima por pieza es 1, así que nada se recorta. El cambio de B3 (que `Sujeto`, `Agente` y `Predicado` paguen) solo cuenta si se agota la amplitud.
- Por tanto, este benchmark no mide el efecto de una atención escasa: solo que las reglas nuevas, con holgura, no rompen nada. Que la atención limite de verdad depende de los valores del `Marcapasos`, cuyo ajuste adaptativo queda fuera de este bloque.
