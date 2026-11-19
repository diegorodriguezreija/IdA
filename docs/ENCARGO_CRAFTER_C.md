# Encargo C: Crafter, vivir muchos días (refugio flexible y huerto junto al agua)

Este encargo pertenece a la **fase de mejora de los mundos** (`AGENTS.md`). Léelo entero antes de tocar nada.

- **Rama:** `feature/crafter-fase-c` (base `f320ae3`, con C.0 y C.0b cerrados).
- **Referencia:** `datos/benchmarks/ref_c0.json` (commit `f2f1262`).
- **Se dan por leídos:**
  - `docs/DIAGNOSTICO_CRAFTER_C.md`, secciones 1 a 5;
  - las secciones 3 (mecánica) y 7 (lecciones) de `docs/ENCARGO_CRAFTER_NOCHE.md`.
- **Modelos:**
  - **Flash:** C.0c, C.2, C.3 y todos los benchmarks.
  - **Argon:** solo C.1 y C.4. Este encargo trae el diseño y el pseudocódigo para que Argon implemente y verifique, sin explorar ni rediseñar. Si Argon ve que algo del pseudocódigo no funciona, lo anota y propone el cambio mínimo; no rediseña por su cuenta.

---

## 1. Objetivo y datos de partida

**Objetivo:** vivir el mayor número de días posible y ser autosuficiente.
- El máximo de Crafter son 10 000 pasos, unos 33 días.
- Los logros raros (horno, herramientas de piedra, carbón, hierro) quedan aparcados.
- Los logros baratos no se pierden (lección 7).

**Referencia `ref_c0`** (120 vidas, 600 latidos):

| Causa de muerte | Vidas |
|---|---|
| Hambre y sed | 46 (27 + 19) |
| Zombi | 37 |
| Esqueleto | 16 |
| Viven | 21 |

**Diagnóstico** (semillas 11–30, sección 5 del diagnóstico):

| Supuesto | Resultado |
|---|---|
| S1, semilla 14 | Muere de sed **dentro** del refugio. `_conviene_salir` exige `presión × salud/9 ≥ riesgo`: cuanto más baja la salud, menos sale. Es una espiral hacia la muerte. Además, `dormir` propone `ESPERAR` con 1,0/1,0. |
| S1, semilla 18 | Muere de sed con agua a 2 casillas, separada por roca. `_paso_hacia`, si no alcanza el destino, devuelve el paso que reduce la distancia Manhattan, y eso lo deja en un fondo de saco. Va y viene entre 2 casillas durante más de 80 latidos. |
| S2, semillas 21, 26 y 27 | Más del 95 % de los candidatos se descartan por «sin roca para obtener piedra» (66 %) o «sin profundidad para 3» (31 %). La roca visible a 2–3 casillas habría servido colocando **1 a 3 piedras**. |
| S3, territorio | En **19/20 semillas** hay, a ≤ 25 de la salida (mediana 18), un sitio junto al agua con ≥ 6 de hierba y roca a ≤ 17 (mediana 6). Para el recinto con huerto de 4 plantas solo faltan **0 a 3 piedras** (mediana 2). |

**Consecuencia para el diseño:** casi siempre hay paredes naturales de sobra. **La cantera desaparece del encargo:** basta la piedra de cavar y la roca cercana.

---

## 2. Mecánica clave (Crafter 1.8.3, `e04542a`)

Complementa la sección 3 de `ENCARGO_CRAFTER_NOCHE.md`.

| Tema | Regla | Fuente |
|---|---|---|
| Ataque de zombi | Solo a distancia Manhattan ≤ 1 del jugador: **solo importan los vecinos en cruz de las casillas donde está el jugador**. | `objects.py:294-312` |
| Esqueletos | Solo dañan con flechas. La flecha va recta y la para la piedra, pero atraviesa el agua. | `objects.py:327-384` |
| Aparición | Esqueletos: solo en camino, en chunks con ≥ 6 casillas de camino, a ≥ 7 del jugador. Zombis: en hierba, a ≥ 6 del jugador. Vacas: en hierba, a ≥ 5 del jugador. | `env.py:141-180` |
| Radio activo | Solo se actualiza lo que está a < 18 del jugador, incluido el crecimiento de las plantas. | `env.py:87-89` |
| Plantas | Solo en hierba. Maduran con más de 300 actualizaciones. Mueren con un zombi, esqueleto o vaca en cruz. Comer una madura da +4 de comida. Ocupan su casilla. | `objects.py:188-192, 387-411` |
| Consumo | Comida −1 cada 26 pasos despierto (52 dormido). Agua −1 cada 21 (42 dormido). Una noche encerrado cuesta unos 5 de comida y 6 de agua. | `objects.py:133-148` |
| Orientación | Moverse hacia una casilla libre te mete en ella; hacia una bloqueada solo gira. Para actuar sobre una casilla **libre** C desde una vecina A hay que llegar a A **viniendo de P = 2A − C**. | `objects.py:174-177` |
| Colocar piedra | Sobre hierba, arena, camino, agua o lava, en la casilla a la que se mira. | `data.yaml:67` |

---

## 3. Piezas y orden

| Pieza | Modelo | Qué | Medición |
|---|---|---|---|
| C.0c | Flash | Arreglar los dos fallos de S1 | Arnés y benchmark rápido |
| C.1 | **Argon** | Recinto flexible (cavar y/o tapar) y primitiva de orientación | Arnés, semillas 31–50, rápido y completo |
| C.2 | Flash | Reservas antes de sellar (**solo si hace falta** tras C.1) | Arnés y rápido |
| C.3 | Flash | Línea base de horizonte largo | Arnés de 3000 latidos |
| C.3b | Flash | Patrulla de forrajeo (vacas que se reponen) | Arnés largo, arnés de 600 y rápido |
| C.4 | **Argon** | Huerto en bolsillos cerrados junto al recinto | Arnés largo, semillas 31–50 y completo |

**Reglas comunes:**
- Una hipótesis por pieza; un commit por cambio.
- **Como máximo 3 intentos por pieza.** Si no se confirma, `git revert` y se anota como resultado negativo.
- Se informa al cerrar cada pieza, antes de empezar la siguiente.

---

## 4. C.0c: fallos de S1 (Flash)

Dos commits, cada uno con su arnés (semillas 11–30) y su benchmark rápido (Equilibrado) frente a `ref_c0`.

### C.0c-1. Salir del refugio cuando el cuerpo lo exige

**Hipótesis:** la semilla 14 sale y bebe en lugar de morir dentro. En el arnés, ninguna muerte por sed o hambre ocurre dentro del refugio sellado.

**Base biológica:** forrajeo sensible al riesgo. Un animal en déficit acepta más riesgo cuanto más cerca está de morir.

En `_conviene_salir`, sustituir la capacidad por la urgencia:

```python
urgencia = 1.0 + (1.0 - _salud(ctx) / 9.0)      # de 1 (salud llena) a ~2 (a punto de morir)
return presion * urgencia >= self._riesgo_exterior(ctx, luz, pos)
```

En la fase `dormir`, la propuesta `ESPERAR` deja de ser 1,0/1,0 si hay presión interna:

```python
p = self._presion_interna(inv, self._agua_accesible_dentro(mina) is not None)
return Propuesta(Verbo.ESPERAR, "", 1.0 - 0.3 * p, 1.0 - 0.3 * p, "refugio: esperar al amanecer")
```

Actualiza los docstrings de las dos funciones.

### C.0c-2. No perseguir destinos inalcanzables

**Hipótesis:** la semilla 18 deja de ir y venir y bebe en otra agua alcanzable. Ninguna vida pasa más de 20 latidos alternando entre 2 casillas.

**`_paso_hacia`:**
- Si el BFS termina **sin alcanzar el destino y sin haber llegado al límite de profundidad** (es decir, el destino está cerrado por casillas conocidas no transitables), devuelve `None` en lugar del paso que reduce la distancia Manhattan.
- Si se cortó por profundidad (destino lejano), mantiene el comportamiento actual.
- Las casillas desconocidas siguen contando como transitables.

**`RefugioNocturno`:**
- Nuevo `self.inalcanzables: Dict[Pos, int]` (posición → latido), reiniciado en `_reiniciar_vida`.
- Cuando `_paso_hacia` devuelve `None` para un destino de agua o comida, se anota.
- `_abastecer` y la fase `provisiones` ignoran durante 50 latidos los destinos anotados y eligen el siguiente.

**Test:** un mapa sintético con agua detrás de roca y otra agua accesible más lejos; el individuo elige la accesible.

---

## 5. C.1: recinto flexible (Argon)

**Hipótesis:** si el refugio puede completarse **colocando piedra** donde falte pared, y no solo cavando 3 casillas de roca, las vidas selladas el día 1 pasan de **10/20 a ≥ 16/20** (arnés, semillas 11–30), sin perder `wake_up` dentro.

### 5.1 Geometría (se mantiene la actual para cambiar lo mínimo)

- Recinto `(e0, d)`:
  - `e0` es el acceso;
  - `e1` es la casilla del sello;
  - `e2` y `e3` son el interior.
- **Novedades:**
  1. Las casillas `e1`, `e2` y `e3` pueden ser **roca excavable** (se cava) **o transitable** (`grass`, `sand`, `path`; no se cava). Nunca agua, lava ni mesa.
  2. **Paredes que importan:** los laterales de `e2` y de `e3`, y el fondo `e3 + d`. **Se elimina la exigencia sobre los laterales de `e1`**: tras sellar, `e1` es piedra, y un zombi solo ataca desde una casilla en cruz con el jugador (`e2` o `e3`).
  3. **Pared que falta** = casilla de esas 5 que es transitable o desconocida. Si es transitable, cuenta como **piedra a colocar**; si es desconocida, el candidato no se evalúa todavía.
  4. **Factibilidad:** `piedras_a_colocar + 1 (sello) ≤ inv["stone"] + rocas_a_cavar(e1..e3)`.
  5. Se mantienen los rechazos de lava (radio 2) y de agua lateral con camino detrás (flechas).

### 5.2 Puntuación (sustituye a `_evaluar_candidato`)

```python
def _evaluar_recinto(self, e0, d, pos_actual, hogar_pos, piedra_inv) -> Optional[Tuple[float, int]]:
    # -> (puntuación, piedras_a_colocar) o None si no es factible
    e1, e2, e3 = e0 + d, e0 + 2d, e0 + 3d
    for ek in (e1, e2, e3):
        m = self.mapa.get(ek)
        if m is None or not (m in ROCA_EXCAVABLE or m in TRANSITABLES_JUGADOR):
            return None
    paredes = laterales(e2) + laterales(e3) + [e3 + d]
    colocar = 0
    for c in paredes:
        m = self.mapa.get(c)
        if m is None:
            return None
        if m in NO_TRANSITABLES_ZOMBI:
            if m == "water" and hay_camino_detras(c):   # regla actual de flechas
                return None
            continue
        if m in TRANSITABLES_JUGADOR:
            colocar += 1
        else:
            return None                                 # lava u otra cosa
    cavar = sum(1 for ek in (e1, e2, e3) if self.mapa.get(ek) in ROCA_EXCAVABLE)
    if colocar + 1 > piedra_inv + cavar:
        return None
    if lava_en_radio_2(e0..e3):
        return None
    coste_pasos = _dist(pos_actual, e0) + 3 * cavar + 4 * colocar + 4
    caminos = casillas "path" del mapa a <= 6 de e2 que no sean e1..e3   # riesgo de esqueletos
    p = 100 - 1.0 * coste_pasos - 2.0 * dist_agua(e0) + bono_agua_dentro(e2, e3) - 1.5 * caminos
    if es_recordada:           # igual que ahora (mina_recordada u hogar)
        p += 25
    return p, colocar
```

- `bono_agua_dentro` es el actual: 16 para `e2` y 12 para `e3`.
- El peso de `coste_pasos` sustituye al `3·dist_jugador + 2·rocas` actual: lo que se ordena es el **coste total en pasos**.

### 5.3 Búsqueda (sustituye a `_buscar_mejor_mina`)

Ojo con el coste: hoy se evalúan hasta 240 000 candidatos por vida. Con casillas transitables admitidas, el número crece. Por eso:

- Solo se evalúan accesos `e0` a ≤ 20 (Manhattan) del individuo.
- Se descarta pronto todo `(e0, d)` en el que ya falten más de 3 paredes, antes de recorrer el resto.
- Se mantiene la lógica actual de cambio (otra opción solo si supera a la actual en más de 10) y la paciencia de avance.
- Se mide el tiempo por latido antes y después. Debe quedar como mucho un 20 % por encima.

### 5.4 Nueva fase `tapar` (entre `cavar` y `cerrarse`)

- **Primitiva de orientación**, una función general reutilizable en C.4:

  ```python
  def _plan_mirar(self, pos, C) -> Optional[Tuple[Pos, Pos]]:
      """Devuelve (P, A): llegar a P y moverse a A deja al individuo en A mirando a C.
      A es vecina de C y transitable; P = 2A - C es transitable y conocida.
      Prefiere A dentro del recinto. None si no hay ninguna factible."""
  ```

  Si `C` está **bloqueada** (agua, planta, piedra), basta con estar en una vecina y «moverse» hacia `C`. No hace falta P.
- **Fase `tapar`:** mientras quede alguna pared que falta, elige la primera factible según `_plan_mirar`:
  - si el individuo está en `A` mirando a `C`: `USAR place_stone`;
  - si está en `P`: `MOVER` a `A`;
  - si no: `_paso_hacia(P)`.

  Si ninguna es factible, se descarta el recinto (`mina_actual = None`) y se anota para no volver a elegirlo.
- **Orden natural:** el fondo, desde dentro (`P = e2`, `A = e3`); después los laterales. `_plan_mirar` resuelve el resto.
- **Prioridad:** misma motivación que `cavar`.
- **Actualizar con las piedras a colocar** (unos 4 pasos cada una): `_coste_restante_pasos`, el margen de cierre y el paso a `cerrarse`, que solo ocurre cuando no falta ninguna pared.
- `_sellado`, `_agua_accesible_dentro` y la fase `dormir` no cambian.

### 5.5 Tests (mapas sintéticos, sin Crafter)

1. Roca con 3 casillas en línea: el mismo resultado que hoy.
2. Una casilla transitable en un lateral de `e2`, con 2 piedras en el inventario: es factible y se coloca 1 piedra.
3. Recinto en hierba junto al agua (como en S3), con 3 piedras: es factible y `_plan_mirar` encuentra un orden para todas las paredes.
4. No es factible sin piedra suficiente.
5. Lava a ≤ 2: se rechaza.

### 5.6 Medición

- **Arnés** (semillas 11–30):
  - vidas selladas el día 1;
  - paso del sellado;
  - piedras colocadas;
  - agua dentro;
  - comida y agua al salir;
  - muertes por causa;
  - tiempo por latido.
- **Validación** con las semillas 31–50: las vidas selladas el día 1 no caen más de 2 frente a las semillas 11–30 en proporción.
- **Benchmark rápido** frente a `ref_c0`.
- **Al cerrar, benchmark completo** (`c1_completo.json`).

---

## 6. C.2: reservas antes de sellar (Flash, condicional)

Solo si, tras C.1, el arnés sigue mostrando más de 3 de 20 muertes por hambre o sed.

**Hipótesis:** si la motivación de abastecerse antes de sellar crece cuando la comida y el agua no cubren unos 165 pasos encerrado (unas 6 de comida y 7 de agua, o agua dentro), esas muertes bajan sin que bajen las vidas selladas el día 1.

**Ajuste acotado:** la condición `falta_llenar_antes_de_cerrar` y el margen de `_anticipa_refugio`. Sin componentes nuevos.

---

## 7. C.3: línea base de horizonte largo (Flash)

- **Arnés:** semillas 11–20, 1 vida, **3000 latidos**, tras C.1 (y C.2 si se hizo).
- **Métricas:**
  - latido y causa de la muerte;
  - noches superadas;
  - comida y agua mínimas de cada día;
  - vacas comidas por día;
  - recinto usado cada noche (si repite sitio).
- **Contrasta S4:** una vez superada la noche, el límite es la comida.
- **Es la referencia de C.4.**

---

## 7b. C.3b: patrulla de forrajeo (Flash)

**Datos de C.3** (semillas 11–20, 3000 latidos):
- 0/10 vidas superan el latido 653;
- tras la primera salida, todas las que sobreviven al amanecer mueren de hambre (latidos 428–653);
- vacas comidas: 1–2 el día 0, ≤ 1 el día 1 y **0 el día 2**;
- recinto repetido el 75 % de las noches y distancia máxima al recinto < 18 el 89 % de los días.

**Mecánica** (`env.py:152-155`):
- En cada chunk con ≥ 30 de hierba y 0 vacas, aparece una con probabilidad 0,01 cada 10 pasos, de media una cada ~1000 pasos por chunk.
- Un área de campeo de radio 17 cubre unos 9 chunks: unas **2–3 vacas nuevas al día**, ≈ 12–18 de comida, si se encuentran.
- El individuo ve a radio 4 (`crafter.py:94`) y `_explorar_con_rumbo` evita para siempre las casillas ya visitadas (`self.visitadas` no caduca). Por eso, tras el día 1, o no vuelve a mirar cerca o se aleja.

**Paso 1 (diagnóstico, sin cambiar código).** En el arnés largo, cada 50 latidos:
- vacas que existen realmente a ≤ 17 del recinto (lectura del mundo, solo en la herramienta);
- vacas que el individuo ha percibido en esos 50 latidos.

Si existen y no las ve, sigue el paso 2. Si no existen, se anota y se salta a C.4.

**Paso 2 (cambio). Hipótesis:** si las casillas visitadas «caducan» y la búsqueda de comida patrulla dentro del área de campeo, el individuo encuentra las vacas que se reponen. Se espera que suban las vacas comidas del día 1 en adelante y los latidos medios en el arnés largo.
- `self.visitadas` pasa a `Dict[Pos, int]` (posición → último latido). Una casilla vuelve a contar como «no visitada» al cabo de 150 latidos.
- En `_abastecer` y `provisiones`, cuando no hay comida conocida, `_explorar_con_rumbo` solo propone casillas a ≤ 17 del recinto recordado (`mina_recordada`, e2), si existe.
- Sin componentes nuevos.

**Medición:**
- arnés largo (semillas 11–20, 3000 latidos) frente a `c3_largo.json`;
- arnés de 600 latidos (semillas 11–30);
- benchmark rápido.

---

## 8. C.4: huerto en bolsillos cerrados (Argon)

**Datos de C.3:** los recintos se eligen en roca; ninguno de 12 tiene hierba en los laterales del interior (tras `tapar`, los laterales son piedra). Así que el nicho dentro del recinto no se da por sí solo. Este diseño **no depende de la geometría del recinto**.

**Hipótesis:** con 3–4 plantas en **bolsillos cerrados** a ≤ 6 del recinto habitual, la comida deja de limitar. En el arnés largo, frente a C.3b:
- `eat_plant` ≥ 1 por día desde el día 2 en la mayoría de vidas;
- los latidos medios suben.

### 8.0 Ajuste tras C.3d: el huerto empieza el día 1 (prevalece sobre 8.3 donde choquen)

**Datos** (apartado 7 de `INFORME_C.md`; arnés largo, semillas 11–30):
- de 20 muertes, 10 ocurren el día 1, tras la primera noche, casi todas de hambre: comida 0 treinta latidos antes y agua llena;
- se sale del refugio con comida 1–2 hacia el latido 280–300 y se muere entre el 317 y el 509;
- la caza oportunista (C.3d) apenas cambia las vacas comidas en términos absolutos (12 → 13 de día), así que las vacas no bastan.

**Consecuencia:** una planta tarda más de 300 pasos en madurar. Si se planta el día 2, llega tarde para la mitad de las vidas. **Hay que plantar el día 1, antes de sellar, junto al refugio elegido**:
- plantada hacia el latido 110–150, madura hacia el 420–460, justo en la franja en que hoy se muere de hambre;
- el individuo duerme a ≤ 18, así que la planta crece toda la noche;
- los retoños ya se recogen el día 1 en el 100 % de las vidas (`collect_sapling` y `place_plant` 120/120), pero se plantan en campo abierto y las vacas se los comen.

**Cambios respecto a 8.1–8.3:**
1. **Bolsillo natural preferente:** una casilla de hierba a ≤ 6 de `e0` con **≥ 3 vecinos en cruz no transitables naturales** (roca, agua o árbol). El refugio suele estar en el borde roca–hierba, donde abundan. Cerrarlo solo cuesta **1 piedra**, la del acceso, y la da el propio cavado del refugio.
2. **Cuándo:** el día 1, en cuanto hay recinto elegido (`mina_actual`), **solo mientras el presupuesto de luz lo permita**. Se suman al coste de `_coste_restante_pasos` los pasos del bolsillo (≈ 6–8 por planta). Si el margen no alcanza, no se planta: el refugio manda (las selladas el día 1 no pueden bajar de 32/40).
3. **Primero 1–2 plantas el día 1;** el resto, hasta 4, los días siguientes con luz > 0,83 y saciado (8.3).
4. **Redirigir la siembra temprana:** `PlanTecnologico` sigue plantando en campo abierto por el logro `place_plant`; no se toca. Los retoños para el huerto se recogen aparte (8.3, condición 2).
5. **Cosecha:** como en 8.2. La motivación crece con el hambre y con la madurez esperada (latidos desde la plantación ≥ 300).

**Hipótesis de C.4 (sustituye a la anterior).** Arnés largo (semillas 11–30, 3000 latidos) frente a C.3d:
- `eat_plant` ≥ 1 en la mayoría de las vidas que pasan del latido 450;
- bajan las muertes por hambre del día 1 (hoy 10/20 vidas mueren el día 1);
- suben los latidos medios y la mediana;
- en el arnés de 600 (semillas 11–50), las selladas el día 1 se mantienen en ≥ 32/40.

### 8.1 Bolsillo

- **Bolsillo:** una casilla de hierba `B` con una planta y sus **4 vecinos en cruz no transitables**: agua, piedra, árbol, otra planta o pared del recinto. Ninguna criatura puede ponerse al lado, así que la planta no muere.
- **Fila de bolsillos junto al agua:** plantas contiguas (cada planta hace de pared de la de al lado), el agua por un lado, piedra por el otro y en los extremos. Por ejemplo, 3 plantas cuestan unas 5 piedras, menos si hay árboles o roca.
- **Planta madura:** el mundo la marca como nutritiva (`crafter.py:221`).

  ```
  ~  ~  ~  ~  ~
  #  P  P  P  #     P planta; # piedra o pared natural
     #  #  #        (para comer, se abre una # de abajo)
  ```

### 8.2 Ciclo de un bolsillo (usa `_plan_mirar` de C.1)

1. **Preparar:** cerrar con piedra los vecinos de `B` salvo uno, el de acceso `A`.
2. **Plantar:** llegar a `A` moviéndose hacia `B` → `place_plant`.
3. **Cerrar:** apartarse y colocar piedra en `A` (`_plan_mirar(A)`).
4. **Cosechar** (planta madura percibida):
   - picar la piedra de `A` (devuelve la piedra; `A` queda como camino);
   - entrar en `A` moviéndose hacia `B` → `COMER`;
   - salir y volver a colocar piedra en `A`.

   Son unos 8–10 pasos por cosecha. `A` es 1 casilla de camino por bolsillo.

### 8.3 Plan de S3, «asentarse»

Un `Plan` nuevo, con la estructura de `PlanTecnologico` y una intención nueva en el `Perfil` de Crafter. Solo avanza:
- con luz > 0,83 y comida y agua ≥ 5 (lección de B.2b y B.2d), salvo cosechar, que se permite siempre que haya luz;
- con un recinto recordado (`mina_recordada` o `memoria.hogar()`).

Condiciones, en orden de prioridad. Se hace la primera incumplida que sea factible (estigmergia; regla 4):
1. **Cosechar:** un bolsillo propio tiene la planta madura (la percibe al pasar) → ciclo de cosecha.
2. **Retoño:** si faltan plantas y no lleva retoño → `COGER` hierba a ≤ 6 del recinto (probabilidad 0,1 por intento).
3. **Piedra:** si lleva menos de 2 → picar la roca conocida más cercana que no sea pared del recinto ni de un bolsillo.
4. **Bolsillo:** elegir la casilla de hierba a ≤ 6 del recinto con más vecinos ya no transitables (preferir junto al agua y junto a plantas propias) y completar los pasos 1–3 de 8.2.
5. **Objetivo:** 4 plantas. Ampliar a 5–6 solo si el arnés largo lo pide.

Los bolsillos se guardan en el estado del plan: posición, acceso y latido de plantación (se reinicia al cosechar). Así se sabe cuándo volver aunque la planta madura no esté a la vista.

**Prioridad de cosecha:** la motivación crece de forma continua con el hambre y con la madurez esperada (latidos desde la plantación ≥ 300).

### 8.4 Riesgos que se miden (no se presuponen)

- Plantas destruidas (por causa), aunque el diseño debería dejarlas en 0.
- Plantas que no crecen porque el individuo está a ≥ 18 (ya se mide la distancia diaria).
- Coste de piedra: piedras colocadas y picadas por día.
- Que cuidar el huerto quite tiempo a comer, beber y sellar (selladas el día 1 en el arnés de 600).

### 8.5 Tests (mapas sintéticos)

1. Bolsillo con 3 paredes naturales: el ciclo completo (plantar, cerrar, cosechar y volver a cerrar) es factible con `_plan_mirar`.
2. Fila de 3 plantas junto al agua: orden factible.
3. Sin piedra: el plan pica roca antes de preparar el bolsillo.

### 8.6 Medición

- **Arnés largo** (semillas 11–20, 3000 latidos) frente a C.3b:
  - plantas colocadas, maduradas, comidas y destruidas;
  - comida y agua mínimas de cada día;
  - días vividos y causa de la muerte.
- **Arnés de 600 latidos** (semillas 11–30): selladas el día 1, que no deben bajar.
- **Validación** con las semillas 31–40 (largo).
- **Al cerrar, benchmark completo** (`c4_completo.json`).

---

## 9. Reglas

- **Ni `ida/core/` ni `ida/sistemas/`.** Si algo los necesita, se anota como pendiente con datos.
- **Regla 3:** nada de chunks, objetos fuera de la vista ni estado interno; las distancias son las percibidas.
- **Regla 4:** condiciones y motivaciones continuas, no secuencias.
- **E y F siguen apagados.**
- **Semillas:**
  - ajuste: 11–30;
  - validación: 31–50 (una vez en C.1 y otra en C.4);
  - benchmark: 1–10. Nunca se ajusta con estas.
- **Coste:**
  - nada de barridos de parámetros;
  - benchmark rápido (Equilibrado) en cada pieza;
  - **benchmark completo solo al cerrar C.1 y al cerrar C.4.**
- **En cada commit:** `pytest`, `ruff` y `mypy` en verde. Sin push.

## 10. Criterio de éxito del encargo

1. **Principal:**
   - en el arnés largo (C.4 frente a C.3), suben de forma significativa los días vividos;
   - en el benchmark de 600 latidos (frente a `ref_c0`), suben los latidos en ≥ 2 grupos.
2. **Salvaguarda:** el límite inferior del IC 95 % de Δ logros es ≥ −1,0 en todos los grupos.
3. **Ningún grupo empeora** de forma significativa en latidos ni en fitness.
4. **Cada pieza confirma su hipótesis.** No basta con que no empeore.

## 11. Entrega de cada pieza

1. **Resultado primero.** Si la hipótesis no se confirma, el titular lo dice.
2. **Tabla:** hipótesis, arnés (11–30), validación (31–50 si toca), benchmark (1–10) y decisión.
3. **Muertes por causa y logros por tipo** frente a la pieza anterior. Para cada logro que empeore, una explicación comprobada.
4. **Verificación de la base, con la salida literal:**
   ```bash
   git diff --stat main...HEAD -- ida/core ida/sistemas
   python -m pytest -q && ruff check ida tests herramientas && mypy ida
   ```
5. **Lo no verificado, marcado como tal.** Sin lenguaje enfático. El informe va en `docs/INFORME_C.md`.

## 12. Fuera de alcance

- Horno, herramientas de piedra, carbón, hierro y diamante.
- Canteras alejadas: S3 muestra que no hacen falta. Si C.4 muestra falta de piedra, se reabre con datos.
- `ida/core/`, `ida/sistemas/`, E y F.
- Otros mundos, y cambios en el protocolo del benchmark.
