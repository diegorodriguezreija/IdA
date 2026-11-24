# Encargo del paso 6: la defensa general

Fase de generalización (`docs/FASE_GENERALIZACION_CRAFTER.md`), paso 6. Rama `feature/defensa` desde `main` (`84eff92`, etiqueta `crafter-general-v1`).

**Modelos:** diseño, este documento; implementación, Opus 5.5; mediciones, Flash.

---

## 1. Por qué y qué se espera

**Situación** (`docs/MEDICION_CIERRE_PASO3.md`):
- En la línea general (F1 y F2), el 68-70 % de los episodios acaban por zombis.
- `defeat_zombie` está en el 38 %, `defeat_skeleton` en el 0-0,5 % y la espada de madera en el 43-46 %.
- Con las dos estrategias de Crafter que quedan (F3), `defeat_zombie` sube al 54 %, y esas dos estrategias son lo único que impide cumplir el pilar 1:
  - **`DefensaArmada`:** con espada y salud ≥ 4, atacar al hostil pegado;
  - **`CerrarDistancia`:** con espada y salud ≥ 5, acercarse al esqueleto.
- Además, el diagnóstico de G3 mostró que IdA huye de las flechas en vez de enfrentarse a quien las dispara.

**Conocimiento de Crafter que sigue en el adaptador:**

| Dónde | Qué sabe | Por qué incumple los pilares |
|---|---|---|
| `observar`: `peligro = 0,8` (`PELIGRO_MANUAL`) | Cuánto peligro tiene cada clase | Es un número fijo; el daño real no se aprende |
| `observar`: peligro de las casillas, `0,8 · (1 − d/4)` | Hasta dónde llega el peligro | El alcance de 4 está escrito a mano |
| `_efecto`: causa del daño = esqueleto si está a ≤ 4, cualquier otro si está a ≤ 1 | Quién hace daño y desde dónde | El sensor atribuye con geometría de Crafter |
| `DefensaArmada`, `CerrarDistancia` | Cuándo luchar y cuándo acercarse | Conducta escrita para Crafter |

**Hipótesis:** si la base **aprende** cuánto daño hace cada cosa y desde qué distancia, de dónde salen los proyectiles y qué tan rápido derriba a cada amenaza según lo que lleva, entonces puede **valorar si luchar o huir** (*fight or flight*, por evaluación) y **pedir un arma** cuando la lucha le es desfavorable. Con eso:
- sube `defeat_zombie` hasta el nivel de F3, o por encima;
- aparece `defeat_skeleton`;
- bajan las muertes por zombi;
- se pueden borrar las dos estrategias. **`estrategias_propias()` de Crafter queda vacía: pilar 1 cumplido.**

**Expectativa, escrita antes de medir** (línea general, frente a F1 y F2):
- Score no peor, y mejor si es posible;
- `defeat_zombie` ≥ 50 % (F3: 54 %);
- `defeat_skeleton` > 2 %;
- la proporción de muertes por zombi baja de forma clara.

## 2. Conceptos generales (sin nombres de Crafter)

| Concepto | Qué es | De dónde sale |
|---|---|---|
| **Causa por contacto** | El daño se atribuye a la entidad peligrosa **en contacto**: adyacente, o un proyectil que llegó a la casilla propia. Sin geometría de alcance | Percepción (el adaptador solo dice qué tocaba) |
| **Daño aprendido** | Daño medio por contacto de cada clase (media móvil sobre `Efecto.causa` y la vitalidad perdida) | Experiencia; el manual (PELIGROSO) da un previo |
| **Emisor** | Clase X que «emite» la clase Y: una Y aparece junto a una X donde antes no estaba | Experiencia (contingencia, como la de la aliestesia) |
| **Alcance aprendido** | Distancia desde la que una clase puede hacer daño. Es 1 para lo que solo daña por contacto; para un emisor, la distancia recorrida por lo que emite | Experiencia |
| **Eficacia de ataque** | Golpes necesarios para derribar a cada clase, según lo que se lleva en el inventario (contingencia entre objeto llevado y golpes por derribo) | Experiencia |
| **Peligro efectivo** | `daño_esperado / salud_actual`, por la proximidad respecto al alcance | Calculado en la base |

## 3. Diseño

### 6a. Peligro aprendido (memoria y S1)

1. **Adaptador:** la causa del daño pasa a ser la entidad peligrosa **en contacto** (adyacente, o la flecha de la casilla). Hay que **comprobar en `crafter/objects.py`** cómo dañan las flechas y los esqueletos (si hay daño cuerpo a cuerpo y cuándo desaparece la flecha) para atribuir bien. Se quitan el umbral de 4 y la propagación del peligro a las casillas.
2. **Memoria:**
   - `daño[clase]` (media móvil) y `alcance[clase]`;
   - `emite[(X, Y)]`, por contingencia: P(aparece Y junto a X) frente a la línea base de que aparezca Y en cualquier sitio. Un emisor hereda el daño de lo que emite, con su alcance.
   - Todo pasa al legado con al menos 2 observaciones.
3. **S1:**
   - El rasgo `peligro` de una entidad pasa a calcularlo la base: `peligro = acotar(daño_esperado(clase) / salud · f(distancia, alcance))`.
   - Previo del manual (PELIGROSO): daño desconocido = 2 unidades de vitalidad sobre 9 (declarado), con peso 2, que la experiencia corrige.
   - El peligro de las casillas sale de lo mismo, con el alcance aprendido.
   - **Solo cuando el mundo da posiciones y no da su propio `peligro`.** En mínimo y archivos, el adaptador ya da `peligro`, así que esos mundos no cambian (invariancia). Que lo calcule la base en todos los mundos queda como deuda.

### 6b. Luchar o huir (S1, evaluación general)

Estrategia `Afrontar(Definicion)`, para el impulso de seguridad. La `Huir` actual se mantiene y compite en el Tribunal:

```python
def valorar(self, ctx, amenaza):
    golpes = eficacia.golpes_para_derribar(amenaza.clase, inventario)   # aprendido; previo alto si no hay datos
    exposicion = golpes + pasos_hasta_contacto(amenaza)                 # 0 pasos si ya está en contacto
    daño_recibido = daño_esperado(amenaza.clase) * exposicion * tasa_de_ataque_aprendida
    margen = salud - daño_recibido
    beneficio = peligro_que_elimina(amenaza) + (meta del manual pendiente para (ATACAR, clase))
    return margen, beneficio
# Propone ATACAR (en contacto) o MOVER hacia la amenaza (si su alcance > 1, acercarse acorta la exposición)
# solo si margen > reserva (declarada, p. ej. 3 de 9) y beneficio > 0.
# arousal = intensidad de seguridad; confianza = la de las estimaciones usadas.
```

- **Acercarse a un emisor** (el esqueleto) surge porque huir no reduce su alcance y derribarlo sí elimina la fuente. **No se escribe** «acercarse al esqueleto».
- **Sin datos de eficacia,** el previo es pesimista: muchos golpes, así que no lucha y huye. La primera lucha se da por defenderse (la `Defenderse` actual, cuando no hay salida), y de ahí se aprende.
- Las metas ATACAR del manual (`defeat_zombie` y `defeat_skeleton`) pasan a ser alcanzables: `PerseguirMetas` las sigue ignorando, pero `Afrontar` suma su beneficio cuando la evaluación es favorable.

### 6c. El arma como meta instrumental

- La memoria aprende, por contingencia, qué objetos del inventario reducen los golpes por derribo (con la espada, menos golpes).
- Cuando `Afrontar` evalúa una lucha como desfavorable, y existe un objeto que según lo aprendido la haría favorable, **pide ese objeto al planificador** con la intensidad de seguridad (`Definicion.pedir`, del paso 3).
- **Antes de la primera espada no hay datos.** La espada ya es meta del manual (M17) y el planificador la fabrica por sí mismo. La contingencia se aprende con el primer derribo con espada, y desde ahí se pide de forma instrumental.

### 6d. Borrar y cerrar

- Borrar `DefensaArmada`, `CerrarDistancia`, `PELIGRO_MANUAL`, la propagación del peligro a las casillas y el umbral de 4 en `_efecto`.
- `estrategias_propias()` de Crafter devuelve `{}`. Test de frontera: ninguna clase de `ida/mundos/crafter.py` hereda de `Definicion`, `Plan` ni `ConPropuestas`.
- Actualizar `docs/INVENTARIO_CONOCIMIENTO_CRAFTER.md`: debe quedar vacía la columna de «conducta escrita para Crafter».

## 4. Subpasos y medición

| Subpaso | Interruptor (durante la implementación) |
|---|---|
| 6a | `peligro_aprendido` |
| 6b | `afrontar` |
| 6c | `arma_instrumental` |
| 6d | Se quitan los interruptores de lo que se quede |

**Mediciones (Flash).** Protocolo abreviado: 100 000 pasos, vista 9×7, sin herencia y manual estricto; cada medición sola y con los latidos cortados registrados (≤ 10):
- **D1:** semilla 31, `--sin-estrategias-propias`, con 6a, frente a F1;
- **D2:** semilla 31, `--sin-estrategias-propias`, con 6a+6b+6c, frente a F1 y D1;
- **D3:** semilla 32, igual que D2, frente a F2;
- **D4, tras 6d:** semilla 31, sin `--sin-estrategias-propias` (ya no queda ninguna), frente a F3.

## 5. Criterios de aceptación

1. **Pilar 1:** `estrategias_propias()` de Crafter vacía, y el test de frontera en verde.
2. **Pilar 3 (sin escribir conducta):** ningún número de daño, alcance ni golpes escrito para Crafter. Los previos están declarados y son genéricos.
3. **Línea general (D2 y D3 frente a F1 y F2):** Score no peor de forma significativa; `defeat_zombie` ≥ 50 %; `defeat_skeleton` > 2 %; la proporción de muertes por zombi baja.
4. **D4 frente a F3:** no peor en más de 1 punto.
5. **Invariancia** OK en mínimo, archivos y ajedrez.
6. **Tests con un mundo de juguete:**
   - se aprende el daño por contacto;
   - se aprende un emisor y su alcance;
   - la eficacia depende del objeto llevado;
   - `Afrontar` lucha solo con margen y huye sin él;
   - se pide el arma de forma instrumental.

## 6. Riesgos

- **Luchar de más:** la reserva de salud y el previo pesimista lo evitan. Hay que vigilar las muertes por zombi con la salud baja.
- **Atribución por contacto con proyectiles rápidos:** si la flecha desaparece en el mismo paso en que daña, hay que atribuir a la flecha vista en el latido anterior junto a la casilla propia. Comprobarlo en `objects.py`.
- **Coste por latido:** la valoración es barata (una amenaza cada vez); hay que medirlo igualmente.
- **Que `Afrontar` pierda en el Tribunal frente a `Huir`:** las dos usan la intensidad de seguridad. Si pierde, se diagnostica antes de tocar constantes.

## Resultado

Mediciones oficiales en [`docs/MEDICION_PASO6.md`](MEDICION_PASO6.md) (rama `feature/defensa`, código `027062e`; 100 000 pasos, vista oficial, sin herencia, manual estricto, `--sin-estrategias-propias`; datos en `datos/evaluacion/`). Referencias F1, F2 y F3 en [`docs/MEDICION_CIERRE_PASO3.md`](MEDICION_CIERRE_PASO3.md).

| Condición | Score (%) [IC 95 %] | `defeat_zombie` (%) | `defeat_skeleton` (%) | Zombi + desgaste | Latidos cortados |
|---|---|---|---|---|---|
| F1: cierre del paso 3, semilla 31 | 12,82 [11,76, 13,79] | 38,42 | 0,53 | 272 (71,6 %) | 4 |
| D1: 6a, semilla 31 | 12,47 [11,52, 13,24] | 38,30 | 0,26 | 283 (72,8 %) | 0 |
| D2: 6a+6b+6c, semilla 31 | 14,04 [12,92, 15,06] | 40,21 | 7,83 | 272 (71,0 %) | 0 |
| F2: cierre del paso 3, semilla 32 | 13,58 [12,52, 14,47] | 37,63 | 0,00 | 275 (72,4 %) | 6 |
| D3: 6a+6b+6c, semilla 32 | 15,45 [14,18, 16,53] | 40,27 | 5,21 | 253 (69,3 %) | 0 |
| F3: cierre del paso 3, con `DefensaArmada` y `CerrarDistancia`, semilla 31 | 13,80 [12,65, 14,82] | 54,19 | 1,68 | — | 1 |

La causa de muerte no se cuenta igual en F y en D: en F el daño se atribuye por geometría (esqueleto a ≤ 4 casillas, el resto a ≤ 1); en D, por contacto en cada paso del entorno. Por eso las muertes por «esqueleto» pasan de 36 y 35 a 0 y las de «flecha» de 1 a 32, 27 y 27, y «desgaste» casi desaparece. Se compara «zombi + desgaste».

**Criterios de la sección 5:**

1. **Pilar 1: cumplido.** `estrategias_propias()` de Crafter devuelve `{}` y el test de frontera (`tests/test_defensa.py::test_crafter_no_escribe_conducta`) pasa.
2. **Pilar 3: cumplido.** No queda en `ida/mundos/crafter.py` ningún número de daño, alcance ni golpes. Los previos (2/9 de la vitalidad por golpe, 10 golpes por derribo, tasa 0,5) están en `ida/core/peligro.py` y no nombran ningún mundo.
3. **Línea general:**
   - Score no peor: cumplido. D1 −0,35 puntos frente a F1; D2 +1,22 frente a F1; D3 +1,87 frente a F2. En los tres casos los intervalos se solapan.
   - `defeat_skeleton` > 2 %: cumplido (7,83 % y 5,21 %, frente a 0,53 % y 0,00 %).
   - `defeat_zombie` ≥ 50 %: **no cumplido** (40,21 % y 40,27 %; F3 llegaba al 54,19 %).
   - Proporción de muertes por zombi + desgaste: baja 0,6 puntos en D2 y 3,1 en D3; en la práctica no cambia.
4. **D4 frente a F3:** pendiente. D2, sin estrategias propias, ya da 14,04 % frente al 13,80 % de F3, con los intervalos solapados.
5. **Invariancia:** OK en mínimo, archivos y ajedrez, con los interruptores apagados y encendidos y tras el 6d.
6. **Tests con un mundo de juguete:** en `tests/test_defensa.py`, todos en verde.

**Lectura del criterio no cumplido.** `Afrontar` es más prudente que `DefensaArmada`:

- `DefensaArmada` atacaba a cualquier zombi o esqueleto adyacente si llevaba espada y tenía salud ≥ 4.
- `Afrontar` solo lucha si el margen estimado (salud menos daño por golpe × exposición × tasa, todo aprendido) supera la reserva de 3/9. Sin datos de derribos usa el previo pesimista de 10 golpes.
- Lucha menos y abate menos zombis (40 % frente a 54 %), pero muere lo mismo por zombi que sin luchar y gana en Score por los esqueletos.
- Afinar cuándo merece la pena luchar queda como deuda ([`docs/DEUDA_TECNICA_CRAFTER.md`](DEUDA_TECNICA_CRAFTER.md), punto 12).

### 6d: `DefensaArmada` y `CerrarDistancia` borradas, mecanismos siempre activos

Se aprobó a la vista de D2. Se borran `DefensaArmada`, `CerrarDistancia` y lo que solo usaban ellas, `PELIGRO_MANUAL`, el peligro de las casillas y la atribución del daño por geometría. Se quitan los interruptores `peligro_aprendido`, `afrontar` y `arma_instrumental`. La base calcula el peligro solo si el mundo no da el suyo, así que mínimo, archivos y ajedrez no cambian (invariancia OK).

**Conducta sin cambios.** `evaluar_crafter.py --pasos 3000 --semilla 31 --vista oficial --sin-herencia --manual estricto` produce el mismo JSON con el código de `027062e` (con los tres interruptores y `--sin-estrategias-propias`) que con el del 6d (sin opciones). Solo cambian los tiempos y los dos campos que registran las opciones (`mecanismos`, `sin_estrategias_propias`). Ficheros en `datos/diagnostico/paso6/`.
