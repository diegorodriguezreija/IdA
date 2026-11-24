# Mediciones del bloque F: experiencia proactiva (Expectativa y Plan)

Encargo: [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), «Encargo del bloque F». Diseño: [`REDISENO_BASE.md`](REDISENO_BASE.md), decisión 24. Inventario: [`F0_PROACTIVA.md`](F0_PROACTIVA.md). Bloque E: [`MEDICIONES_E.md`](MEDICIONES_E.md). Veredicto: [`VEREDICTO_E_F.md`](VEREDICTO_E_F.md).

- **Rama:** `feature/bloque-f` desde `feature/bloque-e`. Commits: 5a8eb10 (plan), F0 (inventario), 827a6a5 (F1), 0c9c117 (F2), 1e0e4d2 (activación por defecto).
- **Fecha:** 16/11/2026, Windows 10, Python 3.15.1. Reloj real; un solo benchmark a la vez.
- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F [--grupos ...] [--mecanismos ...]` y `... comparar base.json nueva.json`. Protocolo de [`BENCHMARK_PERFILES_MUNDOS.md`](../BENCHMARK_PERFILES_MUNDOS.md): N = 10 linajes (semillas 1 a 10, directorio limpio); mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600. Δ = nueva − base, pareado por semilla, IC 95 % (t(0,975; 9) = 2,262). «Significativo» = el IC no incluye el 0.
- **Por paso:** `pytest -q -x` y `herramientas/invariancia.py` (todos los interruptores de E y F forzados a apagado): OK en los cuatro mundos en todos los pasos. Al final: 153 tests, `ruff` y `mypy` sin avisos.

## Interruptores

En `Perfil.mecanismos` (`MecanismosMemoria`), apagados por defecto en `Perfil()`. `MEMORIA_EF` = `MEMORIA_E` + `expectativa` + `plan`; lo declaran mínimo, Crafter y archivos. Ajedrez y snake, sin mecanismos.

| Paso | Interruptor | Qué hace |
|---|---|---|
| F1 | `expectativa` | Componente `Anticipacion` (S1 y S2, etapa Actuar, barrido proactivo): con ≥ 25 % de potencia libre deja en `ef` lo que espera si se ejecuta su propuesta de mayor arousal (S1: cambio de cada déficit; S2: valencia). Fuente: modelo de transiciones (sistema, verbo, clase) aprendido de lo vivido; si no, el concepto de E3 más parecido (distancia media de rasgos ≤ 0,2); para S2, la valencia del nodo del grafo de E2. El Core la contrasta al latido siguiente si se ejecutó esa acción: aprende la transición, cuenta acierto o fallo (contadores del feedback de S3) y, con error ≥ 0,1, emite la `Sorpresa` (por sistema) y sube el arousal de lo percibido de esa clase (+0,2 × error). El feedback de S1 y S2 suma 0,5 × el error de predicción con signo |
| F2 | `plan` | Tipo `Plan` (`ida/core/estrategia.py`): cadena de pasos en el estado de la estrategia, consumida paso a paso; progreso = parte completada; si la expectativa del paso falla, se rehace una vez y, si vuelve a fallar, la estrategia se agota. `recordar_comida`: ruta completa del mapa (`Memoria.camino`) más «encontrar»; destino desempatado por la fuerza del nodo del grafo; falla fuera de la ruta, sin la puerta esperada o al llegar y no encontrar la comida. `PlanTecnologico`: recetas pendientes; falla la que ha fallado tres veces |

## F0: E tal como está (ajuste de E4 con *decay*) en mínimo y Crafter

El ajuste se había medido solo en archivos. Equilibrado y sin experiencia, N = 10; frente a E antes del ajuste (86138bb):

| Mundo | Métrica | Δ Equilibrado | Δ sin experiencia |
|---|---|---|---|
| Mínimo | latidos / fitness / setas | 0,00 / 0,00 / 0,00 (idéntico) | 0,00 |
| Crafter | logros | −0,03 ± 0,08 | 0,00 |
| Crafter | latidos | −0,03 ± 0,08 | 0,00 |

El ajuste no cambia nada medible en mínimo ni en Crafter. E queda como estaba.

## Benchmark por mecanismo

Mínimo y Crafter; Equilibrado y sin experiencia; N = 10; cada fila frente a la anterior. Sin experiencia: idéntico en todas (sin experiencia los mecanismos no actúan).

| Paso | Mínimo Equilibrado (Δ latidos; Δ fitness; Δ setas) | Crafter Equilibrado (Δ logros; Δ latidos) | Decisión |
|---|---|---|---|
| F1 (E → E + expectativa) | −1,07 ± 14,30; +16,55 ± 40,54; +0,03 ± 0,06 | −0,10 ± 0,30; −7,43 ± 17,74 | activado: sin cambio significativo |
| F2 (→ + plan) | 0,00; 0,00; 0,00 (idéntico) | 0,00 ± 0,00; +0,33 ± 0,75 | activado: sin cambio significativo |

F2 da las mismas decisiones que antes: la ruta completa del plan coincide con el siguiente salto que `recordar_comida` recalculaba en cada latido, y la cadena de recetas es el mismo orden que `PlanTecnologico` ya recorría. En una vida de comprobación (semillas 1 a 3) los planes se activan y avanzan (`recordar_comida` hasta el paso 5 en mínimo, `PlanTecnologico` hasta el 7 en Crafter) y no llegan a fallar. Es un cambio de estructura sin efecto en la conducta medida.

No se usó el intento de ajuste de ningún mecanismo (ninguno empeoró).

## Veredicto: tres comparaciones frente a `base-v2.0`

Base = `base-v2.0` medida en la misma máquina el mismo día (sus valores coinciden con [`REFERENCIA_BASE.md`](REFERENCIA_BASE.md)). Configuración final, código 1e0e4d2. a) solo E = `--mecanismos buffer consolidacion conceptos reduccion evocacion repaso`; b) E + F = configuración por defecto (`MEMORIA_EF`); c) = b frente a a. Sin experiencia: Δ = 0 en todo (omitido).

| Mundo | Métrica | Perfil | a) solo E − base | b) E + F − base | c) F sobre E |
|---|---|---|---|---|---|
| Mínimo | latidos | Equilibrado | −4,33 ± 7,98 | −5,40 ± 10,69 | −1,07 ± 14,30 |
| | | Valiente | −4,00 ± 9,41 | +9,12 ± 21,45 | +13,12 ± 22,61 |
| | | Reactivo | +7,10 ± 12,93 | −2,90 ± 15,71 | −10,00 ± 27,03 |
| | setas | Equilibrado | 0,00 ± 0,00 | +0,03 ± 0,06 | +0,03 ± 0,06 |
| | | Valiente | +0,03 ± 0,06 | +0,05 ± 0,08 | +0,03 ± 0,06 |
| | | Reactivo | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| Archivos | fitness | Equilibrado | +19,50 ± 36,50 | −50,70 ± 94,47 | −70,20 ± 98,45 |
| | | Valiente | −52,15 ± 68,94 | −45,90 ± 79,76 | +6,25 ± 45,06 |
| | | Reactivo | −13,00 ± 41,56 | −10,90 ± 56,48 | +2,10 ± 55,22 |
| | tóxicos | Equilibrado | −0,05 ± 0,14 | +0,03 ± 0,06 | +0,07 ± 0,12 |
| | | Valiente | −0,07 ± 0,12 | −0,03 ± 0,06 | +0,05 ± 0,11 |
| | | Reactivo | −0,05 ± 0,11 | 0,00 ± 0,00 | +0,05 ± 0,11 |
| Crafter | logros | Equilibrado | −0,27 ± 0,49 | −0,37 ± 0,51 | −0,10 ± 0,30 |
| | | Valiente | −0,57 ± 0,60 | **−0,77 ± 0,73** | −0,20 ± 0,38 |
| | | Reactivo | −0,10 ± 0,52 | −0,33 ± 0,37 | −0,23 ± 0,45 |
| | latidos | Equilibrado | +3,07 ± 36,82 | −4,03 ± 32,48 | −7,10 ± 17,29 |
| | | Valiente | +5,37 ± 24,55 | +8,60 ± 19,70 | +3,23 ± 10,83 |
| | | Reactivo | −5,37 ± 48,14 | −3,43 ± 36,51 | +1,93 ± 31,99 |

- **Ninguna mejora significativa** en ningún mundo, perfil ni comparación.
- **Un empeoramiento significativo:** Crafter Valiente, logros con E + F frente a la base (−0,77 ± 0,73). Con solo E, −0,57 ± 0,60 (no significativo). En Crafter los nueve Δ de logros de las tres comparaciones son negativos.
- **F sobre E:** nada significativo; en Crafter, los tres logros negativos (−0,10 a −0,23).

### Muertes por causa (vidas de los 10 linajes; base → E + F; entre paréntesis, solo E)

| Mundo | Perfil | Cambios |
|---|---|---|
| Mínimo (40 vidas) | Equilibrado | hambre 4 → 3 (4); lobo 2 → 4 (4); viven 34 → 33 (32) |
| | Valiente | hambre 2 → 3 (3); lobo 10 → 8 (11); viven 28 → 29 (26) |
| | Reactivo | hambre 1 → 3 (1); lobo 6 → 5 (4); viven 33 → 32 (35) |
| Archivos (40 vidas) | Equilibrado | hambre 12 → 15 (13); depredador 5 → 4 (5); viven 23 → 21 (22) |
| | Valiente | hambre 12 → 15 (16); depredador 1 → 1 (1); viven 27 → 24 (23) |
| | Reactivo | hambre 12 → 15 (13); depredador 3 → 0 (4); viven 25 → 25 (23) |
| Crafter (30 vidas) | Equilibrado | zombi 22 → 20 (22); esqueleto 3 → 3 (2); hambre 1 → 3 (2); desgaste 1 → 2 (2); sed 2 → 2; flecha 1 → 0 |
| | Valiente | zombi 18 → 19 (20); esqueleto 5 → 4; desgaste 4 → 3; hambre 0 → 1; sed 2 → 2; viven 1 → 1 (0) |
| | Reactivo | zombi 15 → 14 (13); sed 5 → 5 (4); hambre 2 → 2 (3); desgaste 1 → 2; viven 1 → 1 (2) |

Lo más repetido: en archivos, 3 muertes más por hambre en cada perfil con E + F (12 → 15). Sin experiencia: idéntico en los tres mundos.

## Milisegundos por latido

Equilibrado, N = 10, código 1e0e4d2, en serie: todo apagado (`--mecanismos ninguno`), solo E y E + F. ms totales del latido / latidos.

| Mundo | Todo apagado | Solo E | E + F | Δ E + F frente a apagado |
|---|---|---|---|---|
| Mínimo | 1,17 | 1,32 | 1,33 | +0,16 (+14 %) |
| Archivos | 1,55 | 1,70 | 1,73 | +0,18 (+12 %) |
| Crafter | 3,66 | 3,82 | 3,90 | +0,24 (+7 %) |

F añade 0,01 a 0,08 ms por latido sobre E. Dentro del latido: una expectativa por sistema (búsqueda de concepto parecido acotada a las clases del modelo de ese verbo) y su contraste; el plan se construye al activarse la estrategia (BFS completo una vez) y no en cada latido. El modelo de transiciones está acotado a 1000 entradas.

## Decisiones tomadas sin consultar

1. **La expectativa va condicionada a la propuesta del propio sistema** (la de mayor arousal), porque el barrido proactivo corre antes de que decida el Tribunal. Se contrasta solo si esa acción fue la ejecutada, como la `Expectativa` de balance que ya existía.
2. **Fuente de lo esperado:** un modelo de transiciones (sistema, verbo, clase) aprendido de lo vivido (media con peso máximo de 10 experiencias), con el concepto parecido y el grafo como respaldo. El borrador decía «a partir del grafo, los conceptos y los episodios»; el grafo de E2 no guarda cambios de necesidades, así que solo sirve de respaldo para la valencia de S2.
3. **Variables:** S1, el déficit de cada necesidad que declara el mundo (sin seguridad, que S1 calcula después de que el Core contraste); S2, placer / 100 y estrés, con valencia = Δ placer − Δ estrés, la misma fórmula que su feedback.
4. **Umbral de sorpresa 0,1** y subida de arousal de +0,2 × error a lo percibido de la clase; peso del error de predicción en el feedback, 0,5. Sin calibrar.
5. **Unificación con lo existente:** la `Sorpresa` es la misma pieza (ahora con `sistema`); los aciertos y fallos de las expectativas suman a los contadores que lee el feedback de S3; `Memoria.proyectar` y su expectativa de balance se mantienen.
6. **El Core sube el arousal de las piezas de exterocepción sin autor** (la vía que la Onda reserva al Core); con `AutorCore` la propiedad por tipo lo impedía.
7. **`Plan` vive en `ida/core/estrategia.py`** como tipo genérico de `Definicion`, usable por cualquier sistema. `recordar_comida` sigue en S2 (el borrador sitúa el Plan sobre todo en S3).
8. **Un plan fallido se agota aunque la estrategia no sea agotable** (`PlanTecnologico`): es la regla del borrador («si una expectativa del plan falla, se rehace o la estrategia se agota»).
9. **`PlanTecnologico` construye la cadena con las recetas** (reglas fijas del mundo) y lo ya hecho; el mapa lo usa en los pasos para volver a la mesa o al horno. No usa el grafo semántico.
10. **La base de las comparaciones** es `base-v2.0` medida de nuevo en esta máquina el mismo día (ficheros del bloque E), no las cifras escritas de `REFERENCIA_BASE.md`, para poder parear por semilla; los valores coinciden.

## Pendiente

- Prospectiva e Imaginación (decisión 24), fuera de este encargo.
- Calibrar los umbrales y pesos de F1 (punto 4) si se sigue por este camino.
