# Encargo de la deuda 14: la cadena de herramientas

Deuda 14 de `docs/DEUDA_TECNICA_CRAFTER.md`. Rama `feature/deuda14` desde `main`. Medición pareada contra `base_v2_31.json` y `base_v2_32.json` (`docs/METODO_MEDICION.md`).

**Modelos:** diseño, este documento; implementación y diagnóstico, Opus 5.5; mediciones, Flash.

---

## 1. El problema, con datos

| Logro | Línea general (`base_v2`) | Línea procedimental (`crafter-procedimental-v1`) |
|---|---|---|
| `place_table` | 84-87 % | 97-99 % |
| `make_wood_pickaxe` | 62-72 % | 95-96 % |
| `make_wood_sword` | 43-47 % | 92 % |
| `make_stone_pickaxe` | 7-10 % | 8-9 % |

Lo que ya se sabe (`docs/DIAGNOSTICO_PASO3.md` y `docs/DIAGNOSTICO_DEUDA11.md`):
- de los episodios con mesa, el 78-79 % fabrica el pico (mediana: 8 latidos después) y solo el 47-54 % la espada (16 latidos después);
- el planificador propone la espada en el 8,6 % de los latidos. Por delante van el pico, la hierba, el horno, la piedra y la vaca;
- las mesas repetidas ya se corrigieron: ahora son 1,1 por episodio.

**Hipótesis:**
- el planificador **elige una meta cada vez** y **se aleja de la mesa** antes de terminar lo barato que hay junto a ella;
- **no reúne de una vez la madera** para todo lo que necesita esa mesa;
- volver después cuesta pasos, y muchas veces el individuo muere antes de volver.

La línea procedimental lo resolvía con una fase escrita: «madera → mesa → herramientas».

La espada importa doble: es un logro, y además hace la lucha más eficaz (deuda 12).

## 2. Diseño

### 14.0 Plazo declarado por cada mundo (base, pequeño)

- `Mundo` declara su ritmo: **por turnos** (el mundo espera a que el individuo decida) o **en tiempo real**. Y con eso, el plazo base del latido. Por defecto, el valor de hoy (100 ms), así que ningún mundo cambia si no lo declara.
- **Crafter lo declara por turnos**, con un plazo generoso (propuesta: 1000 ms). Snake mantiene el suyo. Mínimo, archivos y ajedrez no declaran nada en este paso.
- El marcapasos sigue modulando el plazo con el peligro, igual que ahora. `--plazo-logico OPS` escala con el plazo nuevo.
- **Comprobación:** en Crafter, con el plazo nuevo, el humo de 3000 pasos da el mismo JSON (si con 100 ms no se cortaba nada). Invariancia OK en mínimo, archivos y ajedrez.
- **Consecuencia:** desde aquí, en Crafter **no hace falta ningún presupuesto de cálculo para caber en 100 ms**. Solo hay que vigilar que una medición de 100 000 pasos tarde menos de 30 minutos.

### 14.1 Diagnóstico antes de cambiar nada

Con 3 semillas × 10 000 pasos, `--plazo-logico 40`, en serie. Para los episodios con mesa pero sin pico o sin espada:
1. **Madera en el inventario** en los latidos en que la mesa está al alcance: distribución, y cuántas veces había 0.
2. **La meta que perseguía el planificador** en los 50 latidos siguientes a colocar la mesa, y la distancia a la mesa en esos latidos.
3. **Quién ganó el Tribunal** cuando la mesa estaba al alcance, había madera y no se fabricó.
4. **Cuántos episodios mueren** antes de volver a la mesa, y cuántos latidos pasan entre la mesa y la muerte.

**Si los datos contradicen las hipótesis, PARA** y propón qué cambiar, sin implementar.

### 14.2 Planificar en lote lo que comparte una estación (S3, general)

Cuando el planificador elige una meta cuyo requisito incluye «cerca de X», también **reúne las demás metas pendientes que necesitan la misma X y que no requieren nada más que no se pueda conseguir**. Planifica el lote:

```
lote = {m in metas pendientes : X in requiere_cerca(m) y resolver(m) no necesita otra estación}
material_lote = suma de requiere_inventario(m) para m en lote (con las cantidades aprendidas)
coste_lote = coste(conseguir material_lote) + coste(ir a X o colocarla) + len(lote)
coste_por_meta = coste_lote / len(lote)
```

- El lote se elige si su coste por meta es menor que el de la meta suelta más barata.
- Mientras el lote está en curso, la propuesta es el primer paso: **conseguir todo el material antes de ir a la estación**, igual que ya hace la regla de «primero lo que se lleva».
- Es general: vale para cualquier mundo con estaciones, como un taller o una fragua.

### 14.3 Aprovechar la estación mientras está al alcance (S3, general)

Si una estación está al alcance y hay metas pendientes que necesitan esa estación y se pueden hacer **ya**, porque se tiene el material, su coste incluye **lo que costaría volver más tarde**:

```
ahorro(m) = coste_si_se_aleja(m) − coste_ahora(m)    # coste_si_se_aleja: ida y vuelta a la estación recordada
prioridad(m) = − coste_ahora(m) + ahorro(m)
```

Es el coste de oportunidad. En la práctica: **«ya que estoy junto a la mesa, hago la espada»**. Sin nombres ni secuencias de Crafter.

### 14.4 Lo que no se toca

- `Proteger`, `Afrontar` y el Tribunal.
- Que huir gane cuando hay peligro (39 % de los latidos sin pico) es correcto, porque sobrevivir va primero.
- No se escribe ninguna fase de «herramientas primero».

Cada subpaso (14.2 y 14.3) va tras su interruptor (`lote_estacion` y `aprovechar_estacion`). El 14.0 no lleva interruptor: es un parámetro declarado.

## 3. Mediciones (Flash)

Con `--plazo-logico 40`, 100 000 pasos, vista 9×7, sin herencia y manual estricto, con las semillas 31 y 32. Cada condición se compara de forma pareada con `base_v2`:

| Medición | Qué | Frente a |
|---|---|---|
| K0 | Solo 14.0 | `base_v2` (debe ser idéntica si no se cortaba nada; si no, se explica) |
| K1 | 14.0 + `lote_estacion` | K0 y `base_v2` |
| K2 | 14.0 + los dos interruptores | K1 y `base_v2` |

## 4. Criterios de aceptación (escritos antes de medir)

Para la combinación que se quede, frente a `base_v2`, con la comparación pareada:
1. **`make_wood_sword`:** diferencia > 0 en las dos semillas, y con un IC que excluye el 0 en al menos una.
2. **`make_wood_pickaxe`:** diferencia ≥ 0 en las dos semillas.
3. **Score:** diferencia > 0 en las dos semillas, y con un IC que excluye el 0 en al menos una.
4. **Otros mundos:** invariancia OK en mínimo, archivos y ajedrez.
5. **Tests con un mundo de juguete:**
   - se elige un lote cuando comparte estación;
   - se reúne el material antes de ir;
   - junto a la estación se hace lo pendiente que ya se puede hacer.

**Regla de cierre, fijada de antemano:** si tras el diagnóstico y una ronda de implementación ninguna combinación cumple los criterios 1 y 3, se documenta como resultado negativo y se cierra.

## 5. Riesgos

- **Acopiar demasiado y quedarse sin tiempo de día:** el lote solo incluye metas con requisitos conseguibles, y su coste lo pondera. Hay que vigilar `wake_up` y las muertes por zombi en la comparación pareada.
- **Que el lote compita con `Proteger` al anochecer:** el Tribunal decide, como ahora. Si `Proteger` pierde más que antes, se diagnostica.
- **Coste de cálculo con el plazo generoso:** hay que medir el tiempo total por medición.

---

## Resultado (22/11/2026): 14.2 cumplido en parte; 14.3 retirado

**Decisión del autor:** se queda 14.2 (`lote_estacion`) como «cumplido en parte» y siempre activo; 14.3 se retira.

**Medición:** K1 (14.0 + `lote_estacion`), `docs/MEDICION_DEUDA14.md` (commit `b99a2be`; código `6f7078f`). 100 000 pasos, vista oficial, sin herencia, manual estricto, `--plazo-logico 40`, semillas 31 y 32, 0 latidos cortados. Comparación pareada con `base_v2` (`resumen_evaluacion.py --pareada`, 2000 réplicas). K0 (solo 14.0) y K2 (los dos interruptores) no se midieron: el humo de 3000 pasos de 14.0 dio el mismo JSON que `main`, y en el diagnóstico K2 salió igual que K1 o por debajo (`docs/DIAGNOSTICO_DEUDA14.md`).

| Medida (K1 − `base_v2`, pp) | Semilla 31 (382 pares) | Semilla 32 (365 pares) |
|---|---|---|
| Score | +0,76 [−0,09; 1,57] | +0,57 [−0,30; 1,43] |
| `make_wood_sword` | **+5,50 [1,83; 9,42]** | **+7,12 [3,01; 11,23]** |
| `make_wood_pickaxe` | +1,31 [−1,57; 4,19] | −0,27 [−3,01; 2,74] |
| `make_stone_pickaxe` | **+3,40 [1,31; 5,76]** | **+3,29 [0,27; 6,58]** |
| `make_stone_sword` | **+3,66 [1,57; 6,02]** | **+4,11 [1,37; 7,12]** |
| `collect_drink` | **−3,40 [−6,28; −0,79]** | 0,00 [−2,47; 2,47] |
| `eat_cow` | −2,36 [−4,97; 0,26] | −2,19 [−5,21; 0,82] |
| `wake_up` | −2,09 [−5,76; 1,31] | −0,55 [−4,11; 3,01] |
| `defeat_zombie` | +3,66 [−0,52; 8,12] | +2,74 [−1,92; 7,40] |

En negrita, los IC que excluyen el 0. Score de K1: 14,83 y 15,98 (`base_v2`: 14,04 y 15,45).

**Criterios (sección 4):**
1. **Espada: cumplido.** Diferencia > 0 en las dos semillas y el IC excluye el 0 en las dos.
2. **Pico: no cumplido en la semilla 32** (−0,27, con un IC que incluye el 0). En la 31, +1,31.
3. **Score: cumplido en dirección, no en significación.** Diferencia > 0 en las dos semillas (+0,76 y +0,57), pero ningún IC excluye el 0.
4. **Otros mundos: cumplido.** Invariancia OK en mínimo, archivos y ajedrez, con el interruptor encendido y, tras quitarlo, con 14.2 siempre activo.
5. **Tests de juguete: cumplido para 14.2** (se elige el lote, se reúne el material antes de ir; `tests/test_deuda14.py`). El tercero («junto a la estación se hace lo pendiente») era de 14.3 y se retira con él.

La regla de cierre (criterios 1 y 3) no se cumple al pie de la letra: el 3 falla en significación.

**Análisis conjunto de las dos semillas, NO previsto de antemano** (`resumen_evaluacion.py --pareada-conjunta`, bootstrap pareado estratificado por semilla, 747 pares; `datos/diagnostico/deuda14/conjunta_K1_base_v2.md`):
- Score: +0,64 [0,04; 1,29], el IC excluye el 0. El autor citó [0,04; 1,24] con otro cálculo; con este método el extremo superior es 1,29.
- `make_wood_sword` +6,29 [3,48; 8,97], `make_stone_pickaxe` +3,35 [1,47; 5,35], `make_stone_sword` +3,88 [2,14; 5,76] y `defeat_zombie` +3,21 [0,13; 6,43] excluyen el 0.
- `eat_cow` −2,28 [−4,15; −0,40] también lo excluye, en contra. `collect_drink` −1,74 [−3,61; 0,00] queda en el límite.

Como no estaba fijado antes de medir, este análisis no cuenta para el criterio 3; se publica como lectura complementaria.

**Coste:** el lote cuesta tiempo de forrajeo. `collect_drink` baja 3,40 puntos en la semilla 31 (IC que excluye el 0) y `eat_cow` baja en las dos (−2,36 y −2,19), significativo solo en el conjunto. Es el riesgo 1 de la sección 5 (acopiar demasiado). `wake_up` baja en las dos semillas sin significación, y las muertes por zombi suben de 271 a 278 y de 253 a 276 episodios (`docs/MEDICION_DEUDA14.md`, sección 3).

**Retirada de 14.3:** en el diagnóstico de 3 × 10 000 pasos, 14.2+14.3 dio exactamente lo mismo que 14.2 en las semillas 31 y 33, y 0,17 puntos menos de Score en la 32. Con un lote en curso, la situación que trata 14.3 es rara. Se borran el código (`PerseguirMetas._ahorro`), el interruptor `aprovechar_estacion` y su test (commit `53e2436`).

**14.2 siempre activo:** se quita el interruptor `lote_estacion`. El humo de 3000 pasos (semilla 31) da el mismo JSON que con el interruptor encendido antes del cambio, y la invariancia da OK en mínimo, archivos y ajedrez. En Crafter la conducta cambia, como debe, y se regenera `datos/invariancia/referencia.json` (solo cambian `crafter:2` y `crafter:3`).
