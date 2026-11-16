# Mediciones del bloque E: memoria

Encargo: [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), «Encargo del bloque E: memoria». Diseño: [`REDISENO_BASE.md`](REDISENO_BASE.md), decisiones 7 y 19 a 22. Inventario de partida: [`E0_MEMORIA.md`](E0_MEMORIA.md).

- **Rama:** `feature/bloque-e` desde `base-v2.0`. Un commit por paso (E1 a E7), más el tope de Creencias, la activación por defecto y el ajuste de archivos.
- **Fecha:** 16/11/2026, Windows 10, Python 3.15.1. Reloj real.
- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F [--grupos ...] [--mecanismos ...] [--tasa-herencia T]` y `... comparar base.json nueva.json`. Protocolo de [`BENCHMARK_PERFILES_MUNDOS.md`](BENCHMARK_PERFILES_MUNDOS.md): N = 10 linajes (semillas 1 a 10, directorio limpio); mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600. Media por linaje; Δ = nueva − base, pareado por semilla, con IC 95 % (t(0,975; 9) = 2,262).
- **Por paso:** `pytest -q -x` y `herramientas/invariancia.py` (interruptores forzados a apagado): OK en los cuatro mundos en todos los pasos.

## Interruptores

Todos en `Perfil.mecanismos` (`MecanismosMemoria`, [`ida/core/mundo.py`](../ida/core/mundo.py)). `Perfil()` los tiene apagados y entonces IdA se comporta como `base-v2.0` (invariancia). `MEMORIA_E` agrupa los seis aceptados.

| Paso | Interruptor | Mecanismo | Commit |
|---|---|---|---|
| E1 | `buffer` | búfer diurno de 256 piezas por puntuación (arousal + feedback) y episodio del día | e56a9c7 |
| E2 | `consolidacion` | al dormir (o al final de la vida, sin sueño): búfer → grafo semántico (nodos tipo:clase, relaciones por coincidencia); almacén de 30 días | 8a10bed |
| E3 | `conceptos` | prototipo por clase (media de rasgos de sus instancias), id estable `cN`; 500 instancias | f12f698 |
| E4 | `reduccion` | de noche: grafo ×0,9 y poda < 0,05; c_exp de hipótesis no demostradas ×0,95 y poda < 0,15 (sustituye al olvido de hipótesis por antigüedad) | c3668c4 |
| E5 | `evocacion` | componente `Recuerdo` (S2·Sentir): con ≥ 25 % de potencia libre trae como piezas lo peligroso demostrado de lo visible y, con hambre, lo que se cree nutritivo; `Valor` y `recordar_comida` leen esas piezas; lo traído se reconsolida | 6ee5506 |
| E6 | `repaso` | en calma, con ≥ 50 % de potencia libre y sin recuerdos evocados: trae lo reciente de más fuerza y lo refuerza (nodo ×1,1; hipótesis de su clase +0,02) | 06c3c26 |
| E7 | `tasa_herencia` | fracción del legado que se hereda (proposiciones de más confianza, registros con más experiencias); 1,0 = como antes | 5f1d3fe |
| — | — | tope de 64 Creencias por latido (prioridad: clases a la vista o recordadas, luego confianza) | e13f91c |

## Benchmark acumulado por mecanismo

Crafter y mínimo; Equilibrado y control sin experiencia; N = 10. Cada fila compara con la configuración anterior. «Apagado» = `--mecanismos ninguno` en el código de E1. El control sin experiencia da idéntico en todas las filas: sin experiencia los mecanismos no actúan.

| Paso | Crafter Equilibrado (Δ logros; Δ latidos) | Mínimo Equilibrado (Δ latidos; Δ fitness) | Decisión |
|---|---|---|---|
| E1+E2 (apagado → E1+E2) | 0,00 ± 0,00; 0,00 ± 0,00 | +0,80 ± 1,81; +3,30 ± 7,46 | activados: sin cambio de conducta |
| E3 (→ +conceptos) | 0,00 ± 0,00; 0,00 ± 0,00 | +0,68 ± 1,53; +10,18 ± 23,02 | activado: sin cambio significativo |
| E4 (→ +reducción) | 0,00 ± 0,00; +0,53 ± 4,57 | −1,82 ± 4,13; −5,33 ± 12,05 | activado en Crafter y mínimo; apagado en archivos (ver abajo) |
| E5 (→ +evocación) | 0,00 ± 0,00; −8,47 ± 19,15 | 0,00 ± 0,00; 0,00 ± 0,00 | activado: sin cambio significativo |
| E6 (→ +repaso) | −0,23 ± 0,48; +11,03 ± 27,11 | −2,50 ± 9,47; −3,50 ± 24,37 | activado: sin cambio significativo |
| E7 (tasa 1,0 → 0,5, información) | +0,30 ± 0,53; −5,17 ± 36,38 | −15,10 ± 26,54; −43,98 ± 92,68; setas +0,12 ± 0,09 | se queda en 1,0 (por defecto) |

E7 a 0,5 en mínimo: con menos herencia se comen más setas (+0,12 ± 0,09, significativo), lo esperado al heredar la mitad de lo demostrado.

## Archivos: diagnóstico de E4

Archivos no entraba en el benchmark por mecanismo. En el benchmark final con E1 a E6 empeora de forma significativa: tóxicos Equilibrado +0,28 ± 0,23 y Reactivo +0,15 ± 0,13; latidos Reactivo −6,58 ± 5,61 y Valiente −10,72 ± 10,06. Diagnóstico (Equilibrado, Valiente y Reactivo; N = 10; frente a `base-v2.0`):

| Configuración | Δ tóxicos Equilibrado / Valiente / Reactivo | Δ latidos Equilibrado / Valiente / Reactivo |
|---|---|---|
| E1 a E6 | +0,28 ± 0,23 / +0,07 ± 0,17 / +0,15 ± 0,13 | −2,17 ± 6,59 / −10,72 ± 10,06 / −6,58 ± 5,61 |
| sin E5 | +0,20 ± 0,14 / +0,07 ± 0,17 / +0,15 ± 0,13 | −2,50 ± 6,67 / −10,82 ± 10,10 / −6,60 ± 5,61 |
| sin E4 (configuración final) | −0,03 ± 0,13 / −0,07 ± 0,12 / −0,05 ± 0,11 | +0,82 ± 5,03 / −9,50 ± 9,99 / −3,30 ± 4,45 |

Decisión: E4 apagado en archivos (d9c9f0e). Causa probable, no verificada más allá de esta medición: la reducción de c_exp (×0,95 por noche) debilita las hipótesis «es tóxico» aún no demostradas y el individuo vuelve a comer esos ficheros. No se ajustó el parámetro (quedaba un ajuste permitido; ver pendientes).

## Benchmark final frente a la referencia

Configuración final: mínimo y Crafter con `MEMORIA_E`; archivos con `MEMORIA_E` sin reducción; ajedrez y snake sin mecanismos (memoria ligera, sin sueño). Base = `base-v2.0` (56f45b7) medida de nuevo en la misma máquina y sesión; nueva = 86138bb (mínimo, Crafter) y la fila «sin E4» de arriba (archivos, d9c9f0e; el control sin experiencia es idéntico por construcción). Los valores base coinciden con [`REFERENCIA_BASE.md`](REFERENCIA_BASE.md).

| Mundo | Métrica | Grupo | Base | Final | Δ |
|---|---|---|---|---|---|
| Mínimo | latidos | Equilibrado | 387,90 ± 15,52 | 383,57 ± 18,18 | −4,33 ± 7,98 |
| | | Valiente | 350,80 ± 47,06 | 346,80 ± 45,53 | −4,00 ± 9,41 |
| | | Reactivo | 383,82 ± 13,29 | 390,93 ± 9,09 | +7,10 ± 12,93 |
| | | Sin experiencia | 157,07 ± 42,90 | 157,07 ± 42,90 | 0,00 |
| | setas | Equilibrado | 1,00 ± 0,08 | 1,00 ± 0,08 | 0,00 |
| | | Valiente | 1,02 ± 0,06 | 1,05 ± 0,08 | +0,03 ± 0,06 |
| | | Reactivo | 1,02 ± 0,06 | 1,02 ± 0,06 | 0,00 |
| Crafter | logros | Equilibrado | 9,87 ± 1,47 | 9,63 ± 1,87 | −0,23 ± 0,48 |
| | | Valiente | 10,67 ± 1,66 | 10,10 ± 1,73 | −0,57 ± 0,60 |
| | | Reactivo | 9,37 ± 1,46 | 9,27 ± 1,72 | −0,10 ± 0,52 |
| | | Sin experiencia | 9,67 ± 1,40 | 9,67 ± 1,40 | 0,00 |
| | latidos | Equilibrado | 247,43 ± 37,93 | 250,53 ± 35,01 | +3,10 ± 36,80 |
| | | Valiente | 252,50 ± 65,72 | 257,87 ± 55,28 | +5,37 ± 24,55 |
| | | Reactivo | 282,00 ± 44,07 | 276,63 ± 44,25 | −5,37 ± 48,14 |
| Archivos | fitness | Equilibrado | 1788,55 ± 263,63 | 1810,20 ± 276,16 | +21,65 ± 23,31 |
| | | Valiente | 1851,90 ± 241,39 | 1795,40 ± 280,45 | −56,50 ± 67,57 |
| | | Reactivo | 1824,70 ± 241,19 | 1830,60 ± 282,41 | +5,90 ± 54,08 |
| | tóxicos | Equilibrado | 2,25 ± 0,32 | 2,23 ± 0,33 | −0,03 ± 0,13 |
| | | Valiente | 2,35 ± 0,31 | 2,27 ± 0,30 | −0,07 ± 0,12 |
| | | Reactivo | 2,27 ± 0,33 | 2,23 ± 0,33 | −0,05 ± 0,11 |

Ninguna diferencia es significativa (todos los IC incluyen el 0). Crafter muestra una tendencia negativa en logros en los tres perfiles con experiencia (−0,10 a −0,57), sin llegar a serlo; Valiente es el caso más cercano (−0,57 ± 0,60). En ningún mundo hay mejora significativa: la memoria del bloque E, tal como está, no cambia el fitness.

### Muertes por causa (vidas de los 10 linajes; base → final)

| Mundo | Grupo | Cambios |
|---|---|---|
| Mínimo (40 vidas) | Equilibrado | lobo 2 → 4; hambre 4 → 4; viven 34 → 32 |
| | Valiente | lobo 10 → 11; hambre 2 → 3; viven 28 → 26 |
| | Reactivo | lobo 6 → 4; hambre 1 → 1; viven 33 → 35 |
| Crafter (30 vidas) | Equilibrado | zombi 22 → 22; esqueleto 3 → 2; flecha 1 → 0; hambre 1 → 2; desgaste 1 → 2; sed 2 → 2 |
| | Reactivo | zombi 15 → 13; sed 5 → 4; hambre 2 → 3; viven 1 → 2 |
| Archivos (40 vidas), con E1 a E6 | Equilibrado / Valiente / Reactivo | hambre 12 → 14 / 12 → 15 / 12 → 14 |
| Archivos, sin E4 (final) | Equilibrado / Valiente / Reactivo | hambre 12 → 13 / 12 → 16 / 12 → 13 |

Sin experiencia: idéntico en los tres mundos. Valiente en Crafter y el resto de filas: tabla completa con `comparar`.

### Coste de atención

La evocación y el repaso consumen potencia de S2 que antes quedaba libre (Equilibrado, configuración final): potencia media S2 por latido en archivos 1,42 → 1,97, en mínimo 2,59 → 2,79, en Crafter 2,68 → 2,72; latidos con S3 sin amplitud o potencia, archivos 223 → 452, mínimo 217 → 248, Crafter 1620 → 1742. El plazo agotado sigue en 0. Es la causa probable de que la evocación no mejore: lo que antes se leía gratis de la memoria ahora compite por atención con S3.

## Rendimiento: ms por latido

Código final (d9c9f0e), Equilibrado, N = 10, en serie y en la misma sesión: `--mecanismos ninguno` frente a la configuración por defecto de cada mundo. ms totales del latido (`onda.notas["ms_total"]`) / latidos.

| Mundo | Apagado | Con memoria | Δ |
|---|---|---|---|
| Mínimo | 1,25 | 1,37 | +0,12 (+10 %) |
| Archivos (sin E4) | 1,56 | 1,67 | +0,11 (+7 %) |
| Crafter | 3,65 | 3,87 | +0,22 (+6 %) |

El trabajo pesado (consolidación del día, reducción, poda) ocurre al dormirse, fuera del latido. Dentro del latido quedan el marcado del búfer (heap acotado a 256), la instancia del concepto por objeto, la evocación (proporcional a lo visible y a las proposiciones nutritivas) y el repaso (2 nodos). La emisión de Creencias queda acotada a 64 por latido. El ruido entre ejecuciones con conducta idéntica llegó a ±0,5 ms en Crafter cuando la máquina tenía otra carga (control sin experiencia: 4,04, 3,91 y 3,52 ms en tres ejecuciones), por eso esta tabla se midió aparte.

## Decisiones tomadas sin consultar

1. **Grafo, conceptos y días solo en RAM.** No se persisten en `memoria.db`; viven lo que dura la vida (el legado sigue siendo lo demostrado y los registros). Persistirlos es un paso posterior.
2. **Alcance de E4.** La reducción proporcional actúa sobre el grafo y sobre las hipótesis (c_exp); registros, mapa, `donde` y lo demostrado siguen sus reglas de antes. Con reducción se omite el olvido de hipótesis por antigüedad (lo sustituye).
3. **Reconsolidación** = refresco de la proposición (no envejece) y entrada en el búfer diurno con su arousal; no reescribe la confianza.
4. **`recordar_comida`** sigue usando `memoria.ruta` y `olvidar_donde` para navegar; con evocación solo cambia de dónde salen los candidatos (piezas `Recuerdo`).
5. **Repaso solo en calma** (afecto CALMA) para no repasar en estados negativos (rumiación); umbral de potencia libre 50 %, más alto que el de evocación (25 %), para que el repaso no compita con ella.
6. **Mundos con mecanismos:** solo los de memoria completa y sueño (mínimo, Crafter, archivos). Ajedrez y snake no los declaran: sin sueño la consolidación ocurriría solo al final de la partida y su memoria es ligera.
7. **E4 apagado en archivos** sin probar un ajuste del parámetro (ver diagnóstico).
8. **Tope de Creencias = 64**: por debajo no cambia nada (invariancia OK); con más proposiciones, prioridad a lo presente.
9. **ms por latido con reloj real**, en la misma máquina, en serie y sin otra carga; `base-v2.0` no registra ms, así que el «antes» se mide en el código final con `--mecanismos ninguno`.

## Pendiente

- Ajuste de E4 para archivos (por ejemplo, no reducir hipótesis de daño o reducir menos); queda un ajuste permitido.
- Persistir grafo y conceptos en `memoria.db` si un bloque posterior los usa entre vidas.
- Ningún mecanismo mejora el fitness: la evocación sustituye lecturas directas de memoria por piezas con coste de atención; aprovechar el grafo (relaciones, valencia) en estrategias o impulsos es trabajo de bloques posteriores.
