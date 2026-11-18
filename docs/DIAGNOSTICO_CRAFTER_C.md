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
