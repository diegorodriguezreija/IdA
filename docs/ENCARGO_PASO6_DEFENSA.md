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
