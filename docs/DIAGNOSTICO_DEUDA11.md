# Diagnóstico de la deuda 11: primera noche con 11a, 11b y 11c

Fecha: 22/11/2026. Rama `feature/deuda11`, código `1fac567`. Encargo: `docs/ENCARGO_DEUDA11_SITIO.md`. Es el diagnóstico previo a las mediciones de 100 000 pasos (sección 5 del encargo); no es una medición oficial.

## Comando

En serie, sin ningún otro proceso de IdA en la máquina, guillotina lógica:

```bash
.venv\Scripts\python.exe herramientas\diagnostico_paso3.py --pasos 10000 --semilla S --plazo-logico 40 [--mecanismos ...] --salida datos\diagnostico\deuda11\<condicion>_semillaS.json
.venv\Scripts\python.exe herramientas\diagnostico_paso3.py --resumir datos\diagnostico\deuda11\<condicion>_semilla3{1,2,3}.json
```

| Condición | `--mecanismos` |
|---|---|
| apagados | — |
| 11a | `factibilidad_temporal` |
| 11a+11b | `factibilidad_temporal filtro_orientacion` |
| 11a+11b+11c | `factibilidad_temporal filtro_orientacion material_mapa` |

Semillas 31, 32 y 33, 10 000 pasos cada una (vista oficial, sin herencia, manual estricto, sin estrategias propias). Resúmenes completos en `datos/diagnostico/deuda11/resumen_<condicion>.md`.

**Control:** «apagados» reproduce la referencia. Los 35 episodios completos de la semilla 31 y los 32 de la 32 tienen los mismos pasos que los primeros episodios de `base_v2_31.json` y `base_v2_32.json`.

## Tabla

| Métrica | Apagados | 11a | 11a+11b | 11a+11b+11c |
|---|---|---|---|---|
| Score por semilla (31 / 32 / 33) | 15,05 / 17,00 / 10,60 | 12,06 / 15,37 / 9,52 | 10,90 / 16,32 / 10,82 | 11,80 / 12,50 / 9,77 |
| Score total | 42,65 | 36,95 | 38,04 | 34,07 |
| Episodios | 112 | 123 | 123 | 129 |
| Pasos por episodio (media) | 267,9 | 243,9 | 243,9 | 232,6 |
| Episodios con `wake_up` | 21 | 8 | 9 | 6 |
| Latidos cortados (guillotina lógica) | 0 | 0 | 0 | 0 |
| Latidos de más de 100 ms de reloj; máximo | 0; 52,3 ms | 0; 60,2 ms | 0; 55,1 ms | 0; 76,8 ms |
| **Primera noche** | | | | |
| Muere antes de anochecer | 1 (0,9 %) | 2 (1,6 %) | 3 (2,4 %) | 7 (5,4 %) |
| No encuentra sitio | 57 (50,9 %) | 118 (95,9 %) | 115 (93,5 %) | 119 (92,2 %) |
| — de ellos, abandona el sitio antes de lo oscuro | — | 33 | 46 | 60 |
| No lo completa a tiempo | 34 (30,4 %) | 0 | 0 | 1 (0,8 %) |
| — falta tiempo / material / herramienta | 14 / 12 / 8 | — | — | 1 / 0 / 0 |
| Sale antes del amanecer | 4 (3,6 %) | 2 (1,6 %) | 4 (3,3 %) | 0 |
| Pasa la noche dentro | 13 (11,6 %) | 0 | 0 | 1 (0,8 %) |
| Latidos oscuros fuera antes de entrar (mediana; n) | 28; 17 | 4; 2 | 0; 4 | 57; 1 |
| **11a** | | | | |
| T_disponible al elegir sitio (mediana, p25-p75) | — | 37 (36-37) | 37 (36-37) | 37 (36-37) |
| Holgura al elegir (mediana, p25-p75) | — | 16 (7-25) | 15 (7-23) | 15 (9-23) |
| D* en el ocaso | — | 0,7 en 122 de 122 | 0,7 en 121 de 121 | 0,7 en 126 de 126 |
| Episodios con abandono | — | 36 (29,3 %) | 49 (39,8 %) | 64 (49,6 %) |
| Abandonos (de sitio / de requisitos) | — | 42 (27 / 15) | 57 (29 / 28) | 67 (22 / 45) |
| Latidos del ocaso al primer abandono (mediana) | — | 9 | 8 | 7 |
| Coste restante al abandonar (mediana; ≤ 3 pasos) | — | 14; 2 | 15; 2 | 16; 3 |
| **Cadena de herramientas** | | | | |
| Mesas por episodio (media) | 1,12 | 1,12 | 1,15 | 1,09 |
| Pico tras la mesa; latidos (mediana) | 77,9 %; 8 | 78,1 %; 8 | 79,0 %; 10 | 79,4 %; 7 |
| Espada tras la mesa; latidos (mediana) | 51,6 %; 16 | 52,4 %; 16 | 54,3 %; 29 | 46,7 %; 16 |

«Al elegir» es el primer latido desde el ocaso (luz < 0,5) con un sitio elegido, con plan o con requisitos.

## Lectura

1. **11a deja sin noches dentro.** «Pasa la noche dentro» cae de 13 a 0, y `wake_up` de 21 a 8 episodios. «No lo completa a tiempo» desaparece, pero no porque se completen: se convierte en «no encuentra sitio».
2. **La causa es D\* = 0,7.** En el ocaso D\* vale 0,7 en todos los episodios: el previo pesa 2, y sin herencia la primera noche es la primera observación, que no mueve la mediana. Un déficit de 0,7 es luz 0,3, justo el umbral de «oscuro». Así que T_disponible llega a 0 al empezar lo oscuro y todo sitio no terminado se abandona. Pero en «apagados» los 17 episodios que entran pasan una mediana de 28 latidos oscuros fuera antes de entrar: los refugios que funcionan se completan ya de noche. 11a prohíbe justo eso.
3. **La tendencia llega con retraso.** Es una media móvil de 50 latidos, así que en el ocaso subestima la velocidad a la que baja la luz. T_disponible sale de 37 latidos al elegir y la holgura de 15-16, pero los sitios se abandonan unos 8 latidos después, con 14-16 pasos aún por hacer. Pocos abandonos son de sitios casi terminados: entre 2 y 3 con ≤ 3 pasos (riesgo 2 del encargo).
4. **11b y 11c no compensan.** Con 11a, el filtro encuentra más sitios elegidos en la ventana (48 → 56 → 81), pero también más abandonos, y «muere antes de anochecer» sube de 2 a 3 y a 7. Con los tres, la Score total es la más baja (34,07).
5. **Coste de cálculo:** ningún latido pasa de 100 ms de reloj en ninguna condición. El máximo es 76,8 ms, con los tres interruptores. Con 11b basta el presupuesto de planes (`86629d3`), y 11c no necesita presupuesto propio en esta muestra.

**Criterio 3 del encargo** («muere antes de anochecer» no más que en la referencia): no lo cumple ninguna combinación (1 frente a 2, 3 y 7). La muestra es pequeña.

## Recomendación

No medir E1-E3 a 100 000 pasos tal como están: el diagnóstico anticipa que ninguna cumple el criterio 1. Lo que falla es la definición de D\*, no los subpasos 11b y 11c. Propuestas sin implementar, para que decida el autor:

- D\* debería ser el déficit en el que llega el **daño**, no el de la oscuridad. Una opción general es que el previo sea el máximo del déficit (D\* = 1, sin restricción hasta que se aprenda) o que pese menos que una observación.
- O separar las dos cosas: con el déficit ≥ D\*, dejar de iniciar sitios nuevos, pero mantener el sitio en curso mientras se pueda completar (T = ∞ para el sitio en curso).
- La tendencia para T_disponible podría usar una ventana más corta que la de la alostasis.

Cualquiera de las tres cambia el diseño de 11a, así que es una decisión del autor.

---

# Segunda ronda: 11a′ (22/11/2026)

Código `7a8cf4a` (11a′) y `3f54020` (herramienta). Mismo comando y mismas semillas; «apagados» es el de la primera ronda.

**Qué cambia en 11a′:**
- **D\*:** el previo pasa a 1,0 con peso 1, así que la primera observación de daño domina. La observación no cambia.
- **El sitio en curso no se abandona por tiempo:** solo, como antes, si se pierde o deja de poder completarse.
- **Dónde se aplica la factibilidad** (coste completo × 1,2 ≤ T_disponible): solo a empezar un sitio nuevo y a pedir material o herramientas.

**Regla de cierre, decidida antes de medir:** si ninguna combinación supera a «apagados» en la Score total de las 3 semillas y en las noches pasadas dentro, resultado negativo y se cierra.

| Métrica | Apagados | 11a′ | 11a′+11b | 11a′+11b+11c |
|---|---|---|---|---|
| Score por semilla (31 / 32 / 33) | 15,05 / 17,00 / 10,60 | 12,68 / 16,63 / 11,02 | 10,64 / 15,56 / 12,51 | 12,36 / 10,58 / 11,50 |
| **Score total** | **42,65** | 40,33 | 38,71 | 34,44 |
| Episodios | 112 | 117 | 121 | 126 |
| Pasos por episodio (media) | 267,9 | 256,4 | 247,9 | 238,1 |
| Episodios con `wake_up` | 21 | 16 | 13 | 11 |
| Latidos cortados (guillotina lógica) | 0 | 0 | 0 | 0 |
| Latidos de más de 100 ms de reloj; máximo | 0; 52,3 ms | 0; 74,0 ms | 4 (0, 3, 1); 504,7 ms | 0; 98,3 ms |
| **Primera noche** | | | | |
| Muere antes de anochecer | 1 | 2 | 4 | 7 |
| No encuentra sitio | 57 (50,9 %) | 89 (76,1 %) | 88 (72,7 %) | 93 (73,8 %) |
| No lo completa a tiempo | 34 (30,4 %) | 14 (12,0 %) | 17 (14,0 %) | 17 (13,5 %) |
| Sale antes del amanecer | 4 | 4 | 6 | 3 |
| **Pasa la noche dentro** | **13 (11,6 %)** | 5 (4,3 %) | 4 (3,3 %) | 4 (3,2 %) |
| Latidos oscuros fuera antes de entrar (mediana; n) | 28; 17 | 16; 9 | 12; 10 | 21; 7 |
| **11a′** | | | | |
| Sitios no empezados o peticiones no hechas por falta de tiempo: episodios (evaluaciones; sitio / requisitos) | — | 80 (530; 195 / 335) | 92 (855; 191 / 664) | 102 (1029; 185 / 844) |
| — de esos, antes de lo oscuro | — | 37 | 59 | 69 |
| «No encuentra sitio» con ese motivo | — | 35 | 55 | 66 |
| T_disponible al elegir (mediana, p25-p75) | — | 30 (15-80) | 37 (20-87) | 39 (22-86) |
| Holgura al elegir (mediana) | — | 16 | 15 | 18 |
| D\* en el ocaso = 1,0 (previo) / aprendido | — | 31 / 83 | 23 / 96 | 26 / 96 |
| Error de T_disponible: previsto − real hasta el primer daño (mediana, p25-p75; n) | — | 21 (−4-41); 26 | 23 (6-52); 38 | 23 (1-38); 57 |
| — previsto / real (medianas) | — | 36 / 24 | 39 / 20 | 37 / 18 |
| **Cadena de herramientas** | | | | |
| Pico tras la mesa | 77,9 % | 76,8 % | 76,5 % | 80,0 % |
| Espada tras la mesa | 51,6 % | 52,5 % | 52,0 % | 45,7 % |

«Real hasta el primer daño» es el número de latidos desde la elección hasta la primera bajada de salud dentro de la ventana de la primera noche, sea cual sea la causa. Los episodios sin daño en la ventana quedan fuera (censurados: 7, 7 y 8).

## Lectura

1. **No se cumple la regla de cierre.** Ninguna combinación supera a «apagados» ni en la Score total (40,33, 38,71 y 34,44, frente a 42,65) ni en las noches pasadas dentro (5, 4 y 4, frente a 13). Es un resultado negativo.
2. **11a′ recupera parte de lo que perdía 11a** (noches dentro: de 0 a 5; Score total: de 36,95 a 40,33), pero sigue por debajo. El 68-81 % de los episodios tiene al menos una evaluación sin empezar sitio o sin pedir material por falta de tiempo. En 35-66 de ellos la primera noche acaba en «no encuentra sitio» por ese motivo. Lo que se deja de hacer son sobre todo peticiones (requisitos).
3. **D\* se aprende antes de la primera noche** en 83-96 episodios, con valores de 0,52 a 0,74 en el ocaso. Es decir, el primer daño atribuido o el primer peligro por encima del umbral de miedo llegan ya con déficits de 0,5-0,7, a menudo de día o al empezar el ocaso.
4. **La estimación sobrestima el tiempo:** T_disponible al elegir vale una mediana de 36-39 latidos, y el primer daño llega a los 18-24. El error mediano es de 21-23 latidos. Aun así, restringir lo que se empieza o se pide empeora el resultado, así que una ventana más corta (T más pequeño) restringiría más. El diagnóstico no apoya probarla.
5. **Coste de cálculo:** con 11a′+11b, 4 latidos pasan de 100 ms de reloj (3 en la semilla 32 y 1 en la 33; máximo 504,7 ms). Con `--plazo-logico` no cambian el resultado, pero con el plazo de reloj por defecto se cortarían. En las otras dos condiciones no hay ninguno.

## Decisión

Se cierra la deuda 11 con resultado negativo, sin mediciones de 100 000 pasos (regla de cierre). Con los datos de las dos rondas, en la línea general de hoy no ayuda poner condiciones de tiempo a la búsqueda de sitio, ni recuperar el filtro de orientación o el material desde el mapa local. Sin ellas, Proteger completa más refugios, muchos ya de noche. El código de 11a′, 11b y 11c queda en `feature/deuda11` tras sus interruptores, apagados por defecto.
