# Diagnóstico de Crafter para la Fase C

Documento de diagnóstico previo a la Fase C del encargo de refugio nocturno en Crafter (`docs/ENCARGO_CRAFTER_NOCHE.md`).
Medición realizada en la rama `feature/crafter-fase-c` sobre las semillas 11 a 30 (1 vida por semilla, 600 latidos, perfil Equilibrado, arnés real sin motivación dominante). Tiempo total de ejecución: 76,80 s.

---

## 1. Reglas de Crafter 1.8.3 (citadas con archivo y línea)

### Aparición y desaparición de esqueletos
- **Aparición (`crafter/env.py`, líneas 148–151 y 157–174):** En cada chunk (12×12), `_balance_object` comprueba el material `'path'` con probabilidad de spawn `0.1` (`span_dist=7`). La función objetivo (`lambda num, space: (0 if space < 6 else 1, 2)`) exige al menos 6 casillas de `'path'` en el chunk (`space >= 6`) para fijar un objetivo de 1 a 2 esqueletos; si hay menos de 6 casillas de `'path'`, el objetivo es 0 y no aparece ninguno. La aparición requiere que la casilla esté vacía y a distancia Manhattan $\ge 7$ del jugador. La luz no interviene en la aparición de esqueletos (a diferencia de los zombis, cuya tasa es `3.5 - 3 * light`).
- **Desaparición (`crafter/env.py`, líneas 175–179):** Solo ocurre si el número de criaturas del tipo supera `target_max` (es decir, $> 2$) con probabilidad `0.1`, a distancia $\ge 7$ del jugador. Como el tope es 2, rara vez desaparecen.
- **Origen del `'path'` (`crafter/worldgen.py`, líneas 35–42; `crafter/data.yaml`, líneas 59–62):** Los caminos naturales los genera `worldgen` en cuevas y túneles horizontales/verticales. Picar piedra, carbón o hierro (`collect: stone/coal/iron`) deja `'path'` (`leaves: path`), convirtiendo las galerías artificiales del jugador en casillas de camino elegibles para spawn de esqueletos si alcanzan $\ge 6$ casillas en el chunk.
- **Ataque y proyectiles (`crafter/objects.py`, líneas 330–352 y 374–385):** Si el jugador está a distancia $\le 3$, el esqueleto retrocede (`-toward(player)`). Si la distancia es $\le 5$, dispara una flecha con probabilidad 0,5 (`reload = 4`). La flecha avanza 1 casilla/paso (`Arrow.walkable` incluye tierra, arena, camino, agua y lava; la roca la detiene). Si impacta al jugador, inflige 2 de daño (`obj.health -= 2`, línea 377). Si impacta contra mesa o celda de horno, destruye la estructura convirtiéndola en `'path'` (líneas 381–382).

### Cuándo se despierta el jugador (`wake_up`)
- **Despertar natural (`crafter/objects.py`, líneas 103–108):** Ocurre de forma exclusiva cuando `self.inventory['energy'] >= constants.items['energy']['max']` (valor máximo 9, `data.yaml`, línea 50). Solo en ese instante se ejecuta `self.sleeping = False` y se incrementa `self.achievements['wake_up'] += 1`.
- **Regeneración de energía al dormir (`crafter/objects.py`, líneas 142–148):** Durmiendo, `_fatigue` decrece 1 punto por paso; cada 11 pasos durmiendo (`_fatigue < -10`), `energy += 1`.
- **Despertar prematuro por daño (`crafter/objects.py`, líneas 131 y 169–173):** El método `_wake_up_when_hurt` evalúa si `self.health < self._last_health`. En caso afirmativo, fuerza de inmediato `self.sleeping = False` sin otorgar el logro `wake_up`. Esto se activa tanto por ataques externos (zombi o flecha) como por inanición o sed (`_degen_or_regen_health`, líneas 153–167: si `food == 0` o `drink == 0`, `_recover` decrece y resta 1 de salud cada 15–16 pasos despierto o cada 30–32 pasos dormido).

### Requisitos de `place_furnace`, `make_stone_pickaxe` y `make_stone_sword`
- **Horno (`place_furnace`, `crafter/data.yaml`, línea 69; `crafter/objects.py`, líneas 231–250):** Requiere `{stone: 4}` en el inventario. Se coloca en la casilla a la que mira el jugador (`target`), que debe tener material `grass`, `sand` o `path` y estar desocupada (`world[target][1] is None`).
- **Pico de piedra (`make_stone_pickaxe`, `crafter/data.yaml`, línea 74; `crafter/objects.py`, líneas 251–262):** Requiere `{wood: 1, stone: 1}` y tener una `table` a distancia Chebyshev $\le 1$ (`nearby(pos, 1)`).
- **Espada de piedra (`make_stone_sword`, `crafter/data.yaml`, línea 77; `crafter/objects.py`, líneas 251–262):** Requiere `{wood: 1, stone: 1}` y tener una `table` a distancia Chebyshev $\le 1$ (`nearby(pos, 1)`).

### Cómo crece y se come una planta (`sapling` → planta madura)
- **Colocación (`place_plant`, `crafter/data.yaml`, línea 70; `crafter/objects.py`, línea 248):** Gasta `{sapling: 1}`, solo puede ubicarse sobre `grass` y en casilla vacía.
- **Crecimiento y maduración (`crafter/objects.py`, líneas 387–404):** Inicializa con `health = 1` y `grown = 0`. Cada paso dentro del radio activo incrementa `grown += 1`. Se considera madura (`ripe`) si y solo si `grown > 300` (línea 403).
- **Destrucción por criaturas (`crafter/objects.py`, líneas 407–411):** En cada paso revisa sus 4 vecinos ortogonales (`all_dirs`). Si cualquiera de ellos contiene una instancia de `Zombie`, `Skeleton` o `Cow`, se aplica `self.health -= 1`. Como su salud es 1, la planta es destruida instantáneamente (`world.remove(self)`).
- **Destrucción por flechas (`crafter/objects.py`, línea 377):** Una flecha que impacta en la casilla de la planta le resta 2 de salud y la destruye.
- **Consumo (`crafter/objects.py`, líneas 188–192):** Requiere que el jugador ejecute `'do'` mirando hacia la casilla de la planta (`_do_object`). Si `obj.ripe` es `True`, suma `food += 4`, reinicia `grown = 0` y suma `achievements['eat_plant'] += 1`. Si no está madura (`not obj.ripe`), `'do'` no produce ningún efecto.

---

## 2. Tablas de datos recogidos (Semillas 11 a 30)

### A. Muertes por esqueleto y reclasificación de causas

- **Muertes según la atribución de Crafter (`ida/mundos/crafter.py:338–341`):** 16 muertes en total (zombi: 6, esqueleto: 4, sed: 2, hambre: 2, desgaste: 2; 4 vidas sobrevivieron).
- **Muertes reclasificadas (fuente real del daño fatal y vitales):** zombi: 6, esqueleto/flecha: 4, sed: 3, hambre: 3.
- **Muertes etiquetadas erróneamente por Crafter:**
  - **Falsos positivos de esqueleto (2 vidas):**
    - Semilla 23: etiquetada como «esqueleto»; muerte real por **hambre** en el paso 327 (salud 1 → 0 por `food = 0`, mientras un esqueleto estaba a distancia 4).
    - Semilla 27: etiquetada como «esqueleto»; muerte real por **sed** en el paso 320 (salud 1 → 0 por `drink = 0`, con un esqueleto a distancia 4).
  - **Falsos negativos de esqueleto (2 vidas):**
    - Semilla 13: etiquetada como «desgaste» (paso 507); muerte real por **flecha** de esqueleto (el esqueleto disparó a distancia 5, superando el radio $\le 4$ del clasificador).
    - Semilla 22: etiquetada como «desgaste» (paso 331); muerte real por **flecha** de esqueleto (disparo a distancia 5 fuera del radio $\le 4$).

#### Detalle de cada muerte REAL por esqueleto o flecha

| Semilla | Paso | Luz | ¿Dormía? | Estrategia latido | Fase refugio | Ubicación jugador | Dist. mina a túnel natural | 'Path' creados r=6 | Origen esqueleto atacante |
|---|---|---|---|---|---|---|---|---|---|
| 12 | 177 | 0,167 | No | refugio_nocturno | elegir_mina | superficie/exterior | N/A | 0 | camino natural |
| 13 | 507 | 0,001 | No | sobresalto | elegir_mina | de camino a la mina elegida | 2 | 3 | camino natural |
| 17 | 348 | 0,998 | No | refugio_nocturno | abastecer | en un túnel natural | 0 | 3 | camino natural |
| 22 | 331 | 0,973 | No | huir | elegir_mina | dentro del refugio | 0 | 1 | camino natural |

*Nota sobre origen del esqueleto:* en los 4 casos reales, el esqueleto generador apareció en casillas de camino natural preexistentes desde `worldgen`, nunca en una casilla excavada por el jugador.

---

### B. wake_up y noches

- **Total de vidas que llegaron a dormir:** 13 de 20 (65,0 %). Las 7 vidas restantes murieron al anochecer al aire libre antes de entrar a un refugio.
- **Vidas con logro `wake_up`:** 11 de 20 (55,0 %).
- **Total sesiones de sueño:** 48 sesiones (43 terminaron en despertar natural con energía 9, 2 interrumpidas por sed, 2 por hambre, 1 por flecha).

| Semilla | Noche / Evento | ¿Durmió? | Pasos (inicio–fin) | Luz (inicio–fin) | Cómo terminó | Energía fin | ¿En refugio? | 4 vecinos no transitables | Refugio sellado |
|---|---|---|---|---|---|---|---|---|---|
| 11 | Día 1 (s1) | Sí | 131–176 | 0,69–0,18 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 11 | Noche 1 (s2) | Sí | 207–218 | 0,00–0,01 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 11 | Noche 1 (s3) | Sí | 249–260 | 0,23–0,35 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 11 | Día 2 (s4) | Sí | 430–486 | 0,70–0,09 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 11 | Noche 2 (s5) | Sí | 517–528 | 0,01–0,05 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 11 | Noche 2 (s6) | Sí | 560–572 | 0,35–0,49 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 12 | Noche 1 | No | — | — | Murió antes de dormir (esqueleto, latido 170) | — | No | — | No |
| 13 | Día 1 (s1) | Sí | 125–169 | 0,75–0,25 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 13 | Noche 1 (s2) | Sí | 200–211 | 0,02–0,00 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 13 | Noche 1 (s3) | Sí | 242–253 | 0,16–0,27 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 13 | Día 1 (s4) | Sí | 284–295 | 0,64–0,75 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 14 | Día 1 (s1) | Sí | 133–178 | 0,67–0,16 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 14 | Noche 1 (s2) | Sí | 209–220 | 0,00–0,02 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 14 | Noche 1 (s3) | Sí | 251–262 | 0,25–0,37 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 14 | Día 1 (s4) | Sí | 293–304 | 0,73–0,83 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 15 | Noche 1 | No | — | — | Murió antes de dormir (zombi, latido 169) | — | No | — | No |
| 16 | Día 1 (s1) | Sí | 131–176 | 0,69–0,18 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 16 | Noche 1 (s2) | Sí | 207–218 | 0,00–0,01 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 16 | Noche 1 (s3) | Sí | 249–260 | 0,23–0,35 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 16 | Día 2 (s4) | Sí | 425–481 | 0,75–0,13 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 16 | Noche 2 (s5) | Sí | 512–523 | 0,00–0,03 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 16 | Noche 2 (s6) | Sí | 554–565 | 0,28–0,41 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 16 | Día 2 (s7) | Sí | 599–611 | 0,79–0,88 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 17 | Día 1 (s1) | Sí | 133–178 | 0,67–0,16 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 17 | Noche 1 (s2) | Sí | 209–220 | 0,00–0,02 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 17 | Noche 1 (s3) | Sí | 251–262 | 0,25–0,37 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 18 | Noche 1 (s1) | Sí | 182–238 | 0,12–0,12 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Día 1 (s1) | Sí | 124–158 | 0,76–0,37 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Noche 1 (s2) | Sí | 189–200 | 0,07–0,02 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Noche 1 (s3) | Sí | 231–242 | 0,07–0,16 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Día 1 (s4) | Sí | 273–277 | 0,51–0,55 | dano (sed) | 8 | Sí | 3/4 | Sí |
| 19 | Día 1 (s5) | Sí | 278–284 | 0,57–0,64 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Día 2 (s6) | Sí | 315–326 | 0,91–0,96 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Día 2 (s7) | Sí | 433–467 | 0,67–0,27 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Noche 2 (s8) | Sí | 498–509 | 0,02–0,00 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Noche 2 (s9) | Sí | 540–551 | 0,14–0,25 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 19 | Día 2 (s10) | Sí | 582–593 | 0,61–0,73 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 20 | Noche 1 | No | — | — | Murió antes de dormir (zombi, latido 169) | — | No | — | No |
| 21 | Noche 1 | No | — | — | Murió antes de dormir (zombi, latido 264) | — | No | — | No |
| 22 | Noche 1 (s1) | Sí | 153–198 | 0,43–0,02 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 22 | Noche 1 (s2) | Sí | 229–240 | 0,06–0,14 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 23 | Día 1 (s1) | Sí | 285–311 | 0,65–0,88 | dano (hambre) | 2 | Sí | 2/4 | No |
| 24 | Noche 1 | No | — | — | Murió antes de dormir (zombi, latido 189) | — | No | — | No |
| 25 | Noche 1 | No | — | — | Murió antes de dormir (zombi, latido 206) | — | No | — | No |
| 26 | Día 1 (s1) | Sí | 280–379 | 0,59–0,99 | despertar_natural (energia >= 9) | 9 | No | 0/4 | Sí |
| 27 | Día 1 (s1) | Sí | 280–288 | 0,59–0,68 | dano (flecha) | 0 | No | 0/4 | No |
| 27 | Día 1 (s2) | Sí | 289–304 | 0,69–0,83 | dano (sed) | 2 | No | 0/4 | No |
| 28 | Día 1 (s1) | Sí | 144–189 | 0,54–0,07 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 28 | Noche 1 (s2) | Sí | 220–231 | 0,02–0,07 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 28 | Noche 1 (s3) | Sí | 262–273 | 0,37–0,51 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 28 | Noche 2 (s4) | Sí | 504–574 | 0,01–0,52 | dano (hambre) | 8 | Sí | 3/4 | Sí |
| 29 | Noche 1 | No | — | — | Murió antes de dormir (zombi, latido 210) | — | No | — | No |
| 30 | Día 1 (s1) | Sí | 142–187 | 0,57–0,08 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 30 | Noche 1 (s2) | Sí | 218–229 | 0,01–0,06 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |
| 30 | Noche 1 (s3) | Sí | 260–271 | 0,35–0,48 | despertar_natural (energia >= 9) | 9 | Sí | 3/4 | Sí |

*Nota sobre vecinos no transitables:* Las 44 sesiones de refugio tienen 3 vecinos no transitables (`stone`/`water`) y 1 transitable (`path`), correspondiente a la galería interior excavada (`e3` detrás del jugador). Al estar la entrada sellada con roca (`e1`), la galería es completamente hermética frente al exterior.

---

### C. Horno y herramientas de piedra al atardecer (luz < 0,5)

En todas las vidas el primer atardecer (luz $< 0,5$) se alcanzó en el paso 148 (luz = 0,495).

| Semilla | Paso | Luz | Madera | Piedra | Mesa dist $\le 1$ con piedra $\ge 1$ alguna vez | Falta Horno | Falta Pico Piedra | Falta Espada Piedra |
|---|---|---|---|---|---|---|---|---|
| 11 | 148 | 0,495 | 0 | 2 | Sí | piedra < 4 (2/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 12 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 13 | 148 | 0,495 | 0 | 2 | No | piedra < 4 (2/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 14 | 148 | 0,495 | 0 | 2 | Sí | piedra < 4 (2/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 15 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 16 | 148 | 0,495 | 0 | 2 | No | piedra < 4 (2/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 17 | 148 | 0,495 | 1 | 2 | No | piedra < 4 (2/4) | sin mesa a dist $\le 1$ | sin mesa a dist $\le 1$ |
| 18 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 19 | 148 | 0,495 | 0 | 1 | Sí | piedra < 4 (1/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 20 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 21 | 148 | 0,495 | 0 | 1 | Sí | piedra < 4 (1/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 22 | 148 | 0,495 | 0 | 2 | No | piedra < 4 (2/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 23 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 24 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 25 | 148 | 0,495 | 1 | 2 | No | piedra < 4 (2/4) | sin mesa a dist $\le 1$ | sin mesa a dist $\le 1$ |
| 26 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 27 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 28 | 148 | 0,495 | 0 | 3 | No | piedra < 4 (3/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |
| 29 | 148 | 0,495 | 0 | 0 | No | piedra < 4 (0/4) | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), piedra < 1 (0/1), sin mesa a dist $\le 1$ |
| 30 | 148 | 0,495 | 0 | 1 | No | piedra < 4 (1/4) | madera < 1 (0/1), sin mesa a dist $\le 1$ | madera < 1 (0/1), sin mesa a dist $\le 1$ |

---

### D. Plantas (`place_plant`)

- **Vidas que colocaron planta:** 20 de 20 (100,0 %).
- **Total plantas colocadas:** 20 (todas en los primeros 48 pasos: media paso 19,3).
- **Destruidas:** 15 de 20 (75,0 %): 12 por vacas (`Cow`) y 3 por zombis (`Zombie`).
- **No maduraron por fin/muerte de la vida:** 4 de 20 (semillas 22, 23, 25, 29).
- **Llegaron a madurar (`grown > 300`):** 1 de 20 (5,0 %, semilla 26, maduró en el paso 334).
- **Agente pasó cerca estando madura:** 0 de 1 (0,0 %).

| Semilla | Paso plantada | Dist. refugio | ¿Maduró? | Paso maduración | ¿Destruida? | Paso destruida | Causa destrucción | Agente cerca madura |
|---|---|---|---|---|---|---|---|---|
| 11 | 5 | Sin mina aún | No | — | Sí | 130 | Cow | No |
| 12 | 4 | Sin mina aún | No | — | Sí | 39 | Cow | No |
| 13 | 10 | Sin mina aún | No | — | Sí | 24 | Zombie | No |
| 14 | 14 | Sin mina aún | No | — | Sí | 16 | Cow | No |
| 15 | 48 | Sin mina aún | No | — | Sí | 65 | Cow | No |
| 16 | 26 | Sin mina aún | No | — | Sí | 195 | Zombie | No |
| 17 | 4 | Sin mina aún | No | — | Sí | 42 | Cow | No |
| 18 | 14 | Sin mina aún | No | — | Sí | 172 | Cow | No |
| 19 | 14 | Sin mina aún | No | — | Sí | 213 | Cow | No |
| 20 | 12 | Sin mina aún | No | — | Sí | 27 | Cow | No |
| 21 | 9 | Sin mina aún | No | — | Sí | 18 | Cow | No |
| 22 | 26 | Sin mina aún | No | — | No | — | — | No |
| 23 | 6 | Sin mina aún | No | — | No | — | — | No |
| 24 | 45 | Sin mina aún | No | — | Sí | 106 | Cow | No |
| 25 | 24 | Sin mina aún | No | — | No | — | — | No |
| 26 | 30 | Sin mina aún | Sí | 334 | No | — | — | No |
| 27 | 9 | Sin mina aún | No | — | Sí | 26 | Cow | No |
| 28 | 5 | Sin mina aún | No | — | Sí | 307 | Zombie | No |
| 29 | 44 | Sin mina aún | No | — | No | — | — | No |
| 30 | 46 | Sin mina aún | No | — | Sí | 47 | Cow | No |

---

## 3. Resumen de las causas principales (ordenadas por número de casos)

1. **Plantas (`eat_plant ≈ 0`):** En 20 de 20 vidas (100 %) se planta de inmediato (`pasos 4–48`) sobre hierba en la zona de inicio; en 15 de 20 casos (75 %) son destruidas antes de madurar (12 por vacas errantes que las pisan al estar en hierba y 3 por zombis). En la única vida en que maduró (semilla 26, paso 334), el agente estaba lejos en la roca y nunca volvió.
2. **Horno (`place_furnace` bajo):** En 20 de 20 vidas (100 %) faltaba piedra al atardecer (`piedra < 4`, media de 1,05 piedras). El individuo cava solo 3 casillas para la galería del refugio y consume 1 para sellar, por lo que nunca reúne las 4 piedras necesarias antes de la noche.
3. **Herramientas de piedra:** Al atardecer, en 20 de 20 vidas (100 %) no había mesa de trabajo a distancia $\le 1$, y en 18 de 20 (90 %) faltaba madera (`madera = 0`). La mesa inicial queda abandonada en la zona de árboles mientras el agente se desplaza hacia la roca.
4. **`wake_up` (caída frente a referencia):** En 7 de 20 vidas (35 %) el individuo nunca durmió porque murió al aire libre antes de completar el refugio (6 por zombi, 1 por esqueleto). En las 13 vidas que durmieron dentro del refugio sellado, el 89,6 % de las sesiones (43 de 48) alcanzaron el despertar natural con energía 9.
5. **Muertes por esqueleto:** De 4 muertes atribuidas a esqueleto por Crafter, 2 eran falsos positivos (sed y hambre mal etiquetadas por proximidad). Las 4 muertes reales por esqueleto se debieron a individuos sorprendidos en el exterior o al salir del refugio por esqueletos generados en caminos naturales de cuevas (`worldgen`), nunca en casillas excavadas por el agente.


---

## 4. Ampliación del diagnóstico: Primera noche y reservas

### E. Primera noche (todas las vidas)

#### Fases de `RefugioNocturno` en la primera noche y momento de sellado
Cada celda indica el paso de inicio de la fase y su duración acumulada en pasos durante el primer ciclo día/noche (hasta el paso 300 o fin de la vida).

| Semilla | Madera (ini/dur) | Herram. (ini/dur) | Provis. (ini/dur) | Elegir mina (ini/dur) | Cavar (ini/dur) | Cerrarse (ini/dur) | Dormir (ini/dur) | Paso sello |
|---|---|---|---|---|---|---|---|---|
| 11 | p. 3 (17 p) | p. 20 (1 p) | p. 23 (73 p) | p. 21 (25 p) | p. 114 (10 p) | p. 129 (3 p) | p. 132 (150 p) | 130 |
| 12 | p. 3 (39 p) | p. 42 (3 p) | p. 45 (34 p) | p. 69 (99 p) | — | — | — | nunca |
| 13 | p. 3 (67 p) | p. 70 (7 p) | p. 77 (10 p) | p. 87 (31 p) | p. 118 (5 p) | p. 123 (3 p) | p. 126 (171 p) | 124 |
| 14 | p. 3 (89 p) | p. 92 (2 p) | p. 125 (3 p) | p. 94 (21 p) | p. 112 (11 p) | p. 123 (5 p) | p. 134 (167 p) | 132 |
| 15 | p. 3 (110 p) | p. 88 (5 p) | — | p. 118 (74 p) | — | — | — | nunca |
| 16 | p. 3 (102 p) | p. 98 (3 p) | p. 108 (8 p) | p. 116 (6 p) | p. 122 (7 p) | p. 129 (3 p) | p. 132 (154 p) | 130 |
| 17 | p. 3 (40 p) | p. 43 (6 p) | p. 49 (18 p) | p. 51 (59 p) | p. 126 (5 p) | p. 131 (3 p) | p. 134 (144 p) | 132 |
| 18 | p. 3 (82 p) | p. 85 (17 p) | p. 102 (5 p) | p. 107 (68 p) | p. 175 (5 p) | p. 180 (3 p) | p. 183 (81 p) | 181 |
| 19 | p. 3 (101 p) | p. 104 (7 p) | — | p. 111 (4 p) | p. 115 (7 p) | p. 122 (3 p) | p. 125 (176 p) | 123 |
| 20 | p. 3 (28 p) | p. 31 (5 p) | p. 41 (38 p) | p. 36 (103 p) | — | — | — | nunca |
| 21 | p. 3 (28 p) | p. 31 (61 p) | p. 92 (12 p) | p. 104 (171 p) | — | — | — | nunca |
| 22 | p. 3 (85 p) | p. 88 (4 p) | p. 92 (9 p) | p. 97 (45 p) | p. 146 (5 p) | p. 151 (3 p) | p. 154 (109 p) | 152 |
| 23 | p. 3 (24 p) | p. 27 (3 p) | p. 30 (90 p) | p. 33 (171 p) | p. 265 (5 p) | p. 270 (5 p) | — | nunca |
| 24 | p. 3 (82 p) | p. 85 (7 p) | p. 92 (7 p) | p. 99 (109 p) | — | — | — | nunca |
| 25 | p. 3 (37 p) | p. 40 (1 p) | p. 101 (6 p) | p. 41 (175 p) | — | — | — | nunca |
| 26 | p. 3 (96 p) | p. 88 (5 p) | p. 104 (11 p) | p. 106 (186 p) | — | — | — | nunca |
| 27 | p. 3 (116 p) | p. 92 (5 p) | p. 275 (26 p) | p. 124 (151 p) | — | — | — | nunca |
| 28 | p. 3 (22 p) | p. 25 (5 p) | p. 30 (29 p) | p. 31 (62 p) | p. 121 (21 p) | p. 142 (3 p) | p. 145 (145 p) | 143 |
| 29 | p. 3 (65 p) | p. 68 (1 p) | p. 69 (21 p) | p. 74 (139 p) | — | — | — | nunca |
| 30 | p. 3 (65 p) | p. 68 (4 p) | p. 72 (15 p) | p. 87 (45 p) | p. 132 (5 p) | p. 137 (4 p) | p. 141 (133 p) | 138 |

#### Elección de mina, entorno del chunk y vidas sin dormir
- La aparición de zombis en un chunk de 12×12 requiere $\ge 50$ casillas de hierba (`crafter/env.py`, línea 147: `0 if space < 50 else 3.5 - 3 * light`).
- Para las vidas que no llegaron a dormir, se indica la fase de RefugioNocturno en curso al morir y la cuenta de estrategias ganadoras en el Tribunal durante los últimos 20 latidos.

| Semilla | Dist. piedra visible al inicio de `elegir_mina` | Dist. a mina finalmente elegida | Hierba en chunk mina (12×12) | ¿Llegó a dormir? | Fase al morir (si no durmió) | Estrategias ganadoras en Tribunal (últimos 20 latidos) |
|---|---|---|---|---|---|---|
| 11 | 2 casillas | 4 casillas | 99 casillas ($\ge 50$) | Sí | — | — |
| 12 | Ninguna visible | Sin mina | Sin mina | No | elegir_mina | refugio_nocturno: 12, huir: 8 |
| 13 | Ninguna visible | 16 casillas | 50 casillas ($\ge 50$) | Sí | — | — |
| 14 | 2 casillas | 4 casillas | 90 casillas ($\ge 50$) | Sí | — | — |
| 15 | 12 casillas | Sin mina | Sin mina | No | elegir_mina | huir: 12, sobresalto: 6, refugio_nocturno: 1, alimentarse: 1 |
| 16 | 2 casillas | 19 casillas | 56 casillas ($\ge 50$) | Sí | — | — |
| 17 | 9 casillas | 26 casillas | 13 casillas ($< 50$) | Sí | — | — |
| 18 | 4 casillas | 15 casillas | 74 casillas ($\ge 50$) | Sí | — | — |
| 19 | 1 casilla | 1 casilla | 134 casillas ($\ge 50$) | Sí | — | — |
| 20 | 18 casillas | Sin mina | Sin mina | No | elegir_mina | refugio_nocturno: 14, huir: 5, sobresalto: 1 |
| 21 | 2 casillas | Sin mina | Sin mina | No | elegir_mina | huir: 14, refugio_nocturno: 3, sobresalto: 2, defenderse: 1 |
| 22 | Ninguna visible | 22 casillas | 11 casillas ($< 50$) | Sí | — | — |
| 23 | 6 casillas | 32 casillas | 1 casilla ($< 50$) | Sí (día 1) | — | — |
| 24 | Ninguna visible | Sin mina | Sin mina | No | elegir_mina | huir: 9, refugio_nocturno: 7, sobresalto: 3, defenderse: 1 |
| 25 | 6 casillas | Sin mina | Sin mina | No | elegir_mina | sobresalto: 11, refugio_nocturno: 7, huir: 2 |
| 26 | 2 casillas | 5 casillas | 20 casillas ($< 50$) | Sí (día 1) | — | — |
| 27 | 3 casillas | Sin mina | Sin mina | Sí (día 1) | — | — |
| 28 | 17 casillas | 24 casillas | 45 casillas ($< 50$) | Sí | — | — |
| 29 | 9 casillas | Sin mina | Sin mina | No | elegir_mina | refugio_nocturno: 8, huir: 7, sobresalto: 5 |
| 30 | 1 casilla | 7 casillas | 32 casillas ($< 50$) | Sí | — | — |

---

### F. Reservas (vidas que duermen al menos una vez)

A continuación se detallan las 13 vidas que llegaron a dormir. Se registran las reservas de comida y agua al sellar y al salir del refugio, la distancia Manhattan mínima de la mina al agua más cercana en el mapa, y para las muertes por hambre o sed, el tramo temporal transcurrido desde la salida hasta el fallecimiento y la estrategia dominante en ese intervalo.

| Semilla | Comida/Agua al sellar | Comida/Agua al salir | Dist. mina a agua | Causa de muerte real | Pasos salida → muerte | Estrategia dominante tras salir |
|---|---|---|---|---|---|---|
| 11 | 8 / 5 | 3 / 0 | 3 casillas | Sobrevive (600 latidos) | — | — |
| 13 | 8 / 7 | 2 / 1 | 8 casillas | flecha (paso 507) | Murió por flecha | — |
| 14 | 4 / 3 | No salió (murió dentro) | 10 casillas | sed (paso 337) | 0 pasos (murió dentro) | refugio_nocturno (fase dormir) |
| 16 | 4 / 9 | 0 / 2 | 1 casilla | Sobrevive (600 latidos) | — | — |
| 17 | 6 / 8 | 2 / 3 | 3 casillas | flecha (paso 348) | Murió por flecha | — |
| 18 | 3 / 4 | 0 / 0 | 2 casillas | sed (paso 407) | 132 pasos | refugio_nocturno (abastecer, 84/104 L) |
| 19 | 5 / 5 | 0 / 0 | 10 casillas | Sobrevive (600 latidos) | — | — |
| 22 | 4 / 7 | 0 / 3 | 1 casilla | flecha (paso 331) | Murió por flecha | — |
| 23 | No selló | Durmió fuera (p. 285) | 3 casillas | hambre (paso 327) | No selló (murió fuera) | — |
| 26 | No selló | Durmió fuera (p. 280) | 1 casilla | hambre (paso 562) | No selló (murió fuera) | — |
| 27 | No selló | Durmió fuera (p. 280) | Sin mina | sed (paso 320) | No selló (murió fuera) | — |
| 28 | 6 / 8 | 1 / 2 | 7 casillas | Sobrevive (600 latidos) | — | — |
| 30 | 4 / 7 | 0 / 9 (bebió dentro) | 1 casilla | hambre (paso 415) | 140 pasos | refugio_nocturno (abastecer, 72/92 L) |
