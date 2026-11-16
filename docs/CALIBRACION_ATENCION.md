# Calibración de la escasez de atención

Antes de la mejora de los mundos ([`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), «Antes de la mejora de mundos»); decisiones 15 y 18 de [`REDISENO_BASE.md`](REDISENO_BASE.md). Objetivo: que una atención escasa estreche el foco con peligro sin hundir el fitness. Fecha: 16/11/2026, Windows 10, Python 3.15.1. Código: `main` con el bloque D (`0b0bf37`).

## Consumo medido tras los bloques C y D

`python herramientas/consumo.py --mundos crafter minimo` (semillas 1 a 3, una vida de 400 latidos, reloj de la Onda congelado). Piezas nuevas en `ev` y `acc` por latido despierto, sumando S1, S2 y S3 (mediana / percentil 95):

| Mundo | Latidos despiertos | Piezas | Arousal otorgado | Amplitud base del perfil |
|---|---|---|---|---|
| Crafter | 784 | 47 / 54 | 5,92 / 13,98 | 120 |
| Mínimo | 1 137 | 21 / 43 | 7,09 / 13,43 | 100 |

## Barrido del Marcapasos

`python herramientas/benchmark.py ejecutar --raiz . --mundo M --amplitud A --grupos Equilibrado --salida F`, perfil Equilibrado, N = 10 linajes (semillas 1 a 10), protocolo de [`BENCHMARK_PERFILES_MUNDOS.md`](BENCHMARK_PERFILES_MUNDOS.md), potencia = amplitud. Cada nivel se compara, pareado por semilla, con la amplitud actual. «S3 sin recursos»: latidos despiertos en que S3 se queda sin amplitud o potencia, con peligro (indicador de peligro de `Soma` ≥ 0,3) y en calma.

| Mundo | Amplitud | Δ (IC 95 %) | S3 sin recursos con peligro / en calma | Muertes (zombi o lobo / hambre o sed) | Cumple |
|---|---|---|---|---|---|
| Crafter | 120 (actual) | — | 0,0 % / 0,0 % | 20 / 2 | — |
| Crafter | 54 (p95) | logros −0,47 ± 0,84 | 29,8 % / 22,7 % | 21 / 3 | sí |
| Crafter | 47 (mediana) | **logros −2,43 ± 1,25** | 46,3 % / 38,8 % | 24 / 2 | no: pérdida significativa |
| Mínimo | 100 (actual) | — | 0,0 % / 0,0 % | 2 / 5 | — |
| Mínimo | 43 (p95) | latidos +2,65 ± 5,99 | 3,6 % / 1,3 % | 2 / 4 | sí |
| Mínimo | 21 (mediana) | latidos −3,02 ± 18,89; setas +0,15 ± 0,15 | 45,3 % / 33,9 % | 2 / 5 | sí (setas en el límite) |

## Valor elegido

`Marcapasos.FACTOR_AMPLITUD = 0,45`: la amplitud pasa a ser 0,45 × la amplitud base del perfil (Crafter 54, mínimo 45), con potencia = amplitud.

- Es un valor para todos los mundos, así que se expresa como fracción de la amplitud base. El nivel más escaso que cumple en los dos mundos medidos es el p95 (54 / 120 = 0,45 en Crafter; 43 / 100 = 0,43 en el mínimo). La mediana del mínimo (0,21) también cumple, pero la de Crafter (0,39) pierde de forma significativa.
- En los dos niveles elegidos, S3 se queda sin recursos más a menudo con peligro que en calma (foco estrecho con peligro).
- Archivos no se midió en el barrido: su comportamiento con este valor queda en la referencia congelada ([`REFERENCIA_BASE.md`](REFERENCIA_BASE.md)).
