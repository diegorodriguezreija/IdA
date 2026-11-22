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
