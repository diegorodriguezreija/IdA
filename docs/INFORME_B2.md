# Informe del paso B.2 (Crafter, refugio nocturno)

Rama `feature/crafter-refugio`. Encargo: [`ENCARGO_CRAFTER_NOCHE.md`](ENCARGO_CRAFTER_NOCHE.md), fase B. Punto de partida: B.1 (commit `82f025e`).

## Método

- **Ajuste:** `python herramientas/arnes_refugio_crafter.py --real --latidos 300` (semillas 11 a 30, 1 vida, perfil Equilibrado, motivación real, sin `dominante`).
- **Benchmark rápido:** `python herramientas/benchmark.py ejecutar --raiz . --mundo crafter --grupos Equilibrado --salida <x>.json` (semillas 1 a 10, 3 generaciones de 600 latidos, N = 10 linajes, pareado), comparado con `comparar` frente a `ref_crafter.json` y frente a `b1_completo.json`.
- **Referencia:** `ref_crafter.json` no estaba en el repositorio ni en el disco. Se regeneró el 2026-11-17 desde `main` (`f493865`, base de la rama) en un `git worktree`, con el `herramientas/benchmark.py` de esta rama (`--raiz <worktree de main>`, 4 grupos). Reproduce las cifras de B.1 citadas en el encargo: muertes por zombi 74 → 43, por hambre y sed 15 → 47, `place_furnace` −27 vidas y `wake_up` −22 vidas.
- **Criterio para mantener un cambio:** que no empeore de forma significativa frente a B.1 (IC 95 % del Δ pareado entero por debajo de 0 en latidos, fitness o logros). Si empeora, se revierte y se anota.
- Un latido no equivale a un paso de Crafter: interactuar con algo al que no se mira cuesta 2 pasos (`MundoCrafter._interactuar`). En el arnés, el latido 300 cae hacia el paso 305 a 340, es decir, al amanecer: el arnés ve la decisión de salida, pero apenas lo que pasa después.

## Línea base B.1 en el arnés (semillas 11 a 30, 300 latidos)

| Métrica | B.1 |
|---|---|
| Vidas selladas | 10/20 |
| Vivas en el latido 300 | 12/20 (muertes: zombi 7, esqueleto 1) |
| Salen del refugio | 10, luz media 0,38 |
| Comida y agua al salir | comida 1 a 4, agua 0 a 4 |
| Beben tras salir (antes del latido 300) | 4 de 10 |
| Daño recibido fuera tras salir | 35 puntos de salud en total |

Diagnóstico: salía con luz 0,30 a 0,43 (umbrales fijos de `_luz_salida`), con zombis aún presentes (el máximo por zona es 3,5 − 3·luz). Además, con luz < 0,5 `es_noche` seguía activo y la estrategia volvía a la fase de cavar en vez de buscar agua o comida.

## Registro de cambios

| Paso | Hipótesis | Cambio | Benchmark rápido (Equilibrado, Δ pareado) | Decisión |
|---|---|---|---|---|
| B.2a (mañana) | Las muertes por hambre y sed vienen de salir con luz 0,30 a 0,43 (zombis aún presentes) y de volver a cavar en vez de abastecerse. Si la salida la decide el estado y al salir se prioriza beber y comer, bajan sin perder `wake_up`. | Sustituye `_luz_salida` por `_conviene_salir`: sale si presión × capacidad ≥ riesgo. Presión = déficit cuadrático de la reserva más baja (el agua no cuenta con pared de agua dentro); capacidad = salud/9; riesgo = (0,83 − luz)/0,5 sin saturar, + 0,3 por hostil a ≤ 4. Mientras el sello sigue puesto, la decisión se revisa cada latido. Al salir, fase `abastecer` hasta que la luz vuelve a bajar: agua del mapa, comida percibida o vacas vistas hace ≤ 40 latidos, elegidas por distancia − 3 × déficit; se aparta de hostiles a ≤ 2 si no puede abatirlos; no persigue esqueletos. Arnés: vivas en el latido 300 de 12 a 13/20; luz media de salida de 0,38 a 0,56; daño fuera de 35 a 14. | Frente a B.1: latidos +56,37 ± 48,25; fitness +623,70 ± 354,88; logros +0,57 ± 0,32; noches +0,30 ± 0,26. Muertes (30 vidas): hambre 8 → 4, sed 5 → 5, zombi 8 → 6, esqueleto 5 → 7, vive 2 → 8. `wake_up` 18 → 21, `place_furnace` 5 → 5. Frente a la referencia: latidos +153,20 ± 61,17; logros +1,20 ± 0,97. | Se mantiene (mejora significativa frente a B.1 en latidos, fitness y logros). |
| B.2b (tarde) | De día, sin nada urgente, el refugio alterna con `alimentarse` y `plan_tecnologico` (vaivén). Una motivación baja y continua de «tener la mina localizada» (mejor con agua, galería cavada de día) adelanta la mina y la piedra sin quitar tiempo a comer, beber ni progresar. | Sustituye el corte «sin mina, comida y agua ≥ 6 → confianza 0,72» por confianza 0,50 + 0,18 × falta × saciedad (máx. 0,68, por debajo de `plan_tecnologico` 0,8 y de `alimentarse` con continuidad). Falta = 1 sin mina; con mina, 0,35 sin pared de agua + 0,65 × rocas por picar/3. Con mina sin terminar, la cava de día y la deja sin sellar (se recuerda en `mina_recordada`). Con galería lista sin agua, inspecciona vetas a ≤ 10 de la mina. Sin herramientas sigue en 0,28/0,52. Arnés: selladas 11/20 (antes 10), selladas con luz ≥ 0,5 6/20 (antes 8), vivas 13/20, logros medios 10,65 (antes 10,85). El latido en que se localiza la mina no cambió en ninguna semilla. Variante probada y descartada en el arnés: misma motivación también sin herramientas (vivas 10/20, logros 10,25). | Frente a B.1: latidos +37,70 ± 65,60; fitness +505,17 ± 702,26; logros +0,47 ± 0,65; noches +0,23 ± 0,36. Frente a B.2a: latidos −18,67 ± 59,40; logros −0,10 ± 0,64. Muertes (30 vidas): zombi 10 (B.2a 6), hambre 4, sed 4, esqueleto 6, vive 6 (B.2a 8). `wake_up` 20, `place_furnace` 6, `collect_coal` 11 (B.2a 9). Frente a la referencia: latidos +134,53 ± 84,64; logros +1,10 ± 1,08. | Se mantiene por la regla (no empeora de forma significativa frente a B.1), pero sin efecto demostrado: la hipótesis no se confirma y la estimación puntual es peor que B.2a. Candidato a revertir si el benchmark completo final lo señala. |
| B.2c (entrada segura) | Sellar con un hostil dentro de la galería lo encierra con el durmiente (7 de daño por golpe). Comprobarlo antes de sellar evita ese daño. | `_entrada_insegura` en la fase `cerrarse`: si hay un zombi o esqueleto percibido en e1 a e3 (distinto de la casilla propia), lo abate si está al lado y tiene espada con salud ≥ 4, o espera. Un hostil en e0 no impide sellar desde e2. Arnés (300 latidos): resultados idénticos a B.2b. En 20 vidas × 600 latidos la comprobación no se activa ninguna vez. | Idéntico a B.2b: Δ = 0,00 ± 0,00 en latidos, fitness, logros y noches; mismas muertes y logros. Frente a B.1: latidos +37,70 ± 65,60; logros +0,47 ± 0,65. | Se mantiene (no empeora), sin efecto medible: el caso no aparece en las semillas medidas. La defensa de hostiles adyacentes que ya existía al anochecer cubre los casos observados. |
| B.2d (progreso: acopio de piedra) | Hay pocas vidas con piedra para el horno (4) y el pico de piedra. Recoger en la mina la piedra del sello, el pico y el horno, sin abrir la galería, los recupera. Comprobación pedida: el sello no consume piedra de forma permanente. En las 11 vidas selladas (semillas 11 a 30, 600 latidos), la piedra al abrir es la del sello + 1, salvo la semilla 30 (1 → 1). | Fase `acopio`: con la galería cavada y sin ocaso próximo, si falta piedra (1 sello + 1 si no tiene pico de piedra + 4 si no ha visto un horno), pica la roca recordada más cercana a ≤ 5 de la entrada que no sea pared en cruz de e1 a e3 ni el fondo e4. El déficit de piedra entra en la motivación diurna continua (0,5 × déficit × saciedad). Diagnóstico (semillas 11 a 30, 600 latidos): vidas con ≥ 4 piedras de 6 a 7, horno de 2 a 4, pico de piedra 2 → 2. Arnés (300 latidos): sin cambios frente a B.2c. | Frente a B.1: latidos +23,30 ± 53,34; fitness +424,30 ± 588,84; logros +0,40 ± 0,55; noches +0,17 ± 0,30. Frente a B.2c: latidos −14,40 ± 20,88; logros −0,07 ± 0,15. Frente a B.2a: latidos −33,07 ± 52,27; logros −0,17 ± 0,52. Muertes (30 vidas): zombi 12, esqueleto 7, hambre 3, sed 3, vive 5. `place_furnace` 7 (B.2c 6, B.1 5), `wake_up` 19. Frente a la referencia: latidos +120,13 ± 78,97; logros +1,03 ± 1,06. | Se mantiene (no empeora de forma significativa frente a B.1). Desde B.2a, la estimación puntual de latidos baja en cada paso (400,6 → 382,0 → 382,0 → 367,6), sin que ningún Δ sea significativo. |
| B.2d-2 (progreso: plan sin bloqueo) | `plan_tecnologico.decidir` busca el recurso de la primera receta que no puede pagar y sale: si al pico de piedra le falta madera, nunca llega al horno aunque tenga 4 piedras (semilla 16: 7 piedras sin horno). Seguir con las recetas posteriores usa la piedra acopiada. | Si una receta no tiene recursos, se anota lo primero que falta y se sigue mirando si alguna receta posterior ya se puede hacer. Si ninguna, se busca lo anotado (igual que antes). Diagnóstico (semillas 11 a 30, 600 latidos): horno de 4 a 5. | Frente a B.2d: latidos +2,83 ± 4,75; fitness +102,87 ± 161,95; logros +0,10 ± 0,16. Frente a B.1: latidos +26,13 ± 55,27; fitness +527,17 ± 675,88; logros +0,50 ± 0,63. Frente a B.2a: latidos −30,23 ± 53,19. `place_furnace` 9 (B.2d 7, B.1 5). Muertes: zombi 13, esqueleto 6, hambre 3, sed 3, vive 5. Frente a la referencia: latidos +122,97 ± 79,53; logros +1,13 ± 1,01. | Se mantiene. |

## Benchmark completo final (1 de 2 permitidos; 4 grupos, N = 10, semillas 1 a 10, commit `b3f0e64`, 2026-11-17)

Comando: `python herramientas/benchmark.py ejecutar --raiz . --mundo crafter --salida b2_completo1.json`, comparado con `comparar` frente a `b1_completo.json` y frente a `ref_crafter.json`.

| Grupo | Métrica | Δ frente a B.1 | Δ frente a la referencia |
|---|---|---|---|
| Equilibrado | latidos | +18,37 ± 62,74 | +115,20 ± 90,32 |
| Equilibrado | fitness | +452,77 ± 749,16 | +1181,73 ± 1095,77 |
| Equilibrado | logros | +0,43 ± 0,69 | +1,07 ± 1,07 |
| Valiente | latidos | +31,80 ± 52,53 | +109,83 ± 85,77 |
| Valiente | fitness | +432,50 ± 798,34 | +909,13 ± 2142,04 |
| Valiente | logros | +0,40 ± 0,75 | +0,80 ± 2,08 |
| Reactivo | latidos | +2,97 ± 42,12 | +39,00 ± 55,96 |
| Reactivo | fitness | −98,10 ± 343,54 | +837,17 ± 1356,44 |
| Reactivo | logros | −0,10 ± 0,36 | +0,80 ± 1,32 |
| Sin experiencia | latidos | +17,90 ± 40,88 | +114,53 ± 40,67 |
| Sin experiencia | fitness | +318,23 ± 540,08 | +1448,10 ± 1248,60 |
| Sin experiencia | logros | +0,30 ± 0,51 | +1,33 ± 1,23 |

Muertes por causa (120 vidas), referencia → B.1 → B.2: zombi 74 → 43 → 52; hambre + sed 15 → 47 → 30; esqueleto 19 → 20 → 20; viven 3 → 5 → 17.
Las muertes por zombi antes del latido 300 pasan de 33 (B.1) a 36, y las del latido 300 en adelante de 10 a 16.

Logros por tipo (vidas), referencia → B.1 → B.2: `wake_up` 95 → 73 → 77; `place_furnace` 45 → 18 → 31; `make_stone_pickaxe` 17 → 9 → 3; `make_stone_sword` 6 → 5 → 0; `collect_drink` 93 → 90 → 92; `eat_cow` 67 → 62 → 64; `defeat_zombie` 64 → 56 → 66.
`plan_tecnologico` se ejecuta en el 13,4 % de los latidos en que está activa (B.1: 13,4 %).

### Lectura

- **Frente a B.1:** ningún grupo empeora de forma significativa; ningún Δ es significativo en ninguna dirección.
- **Objetivo de B.2a:** se cumple. Las muertes por hambre y sed bajan de 47 a 30 y `wake_up` sube de 73 a 77. El horno recupera 13 vidas (18 → 31).
- **Muertes por zombi:** suben de 43 a 52. En parte vienen de vidas que ahora sobreviven a la primera mañana y mueren en la segunda noche (10 → 16 a partir del latido 300).
- **Criterio de éxito del encargo frente a la referencia:**
  - Punto 1, se cumple: los latidos suben de forma significativa en Equilibrado, Valiente y Sin experiencia.
  - Punto 3, se cumple: ningún grupo empeora de forma significativa.
  - Punto 2, no se cumple en Valiente: el límite inferior del IC de Δ logros es 0,80 − 2,08 = −1,28, por debajo de −1,0. En B.1 era −1,66.
- **Pendiente:**
  - El pico y la espada de piedra bajan (9 → 3 y 5 → 0 vidas): les falta madera, que el refugio solo reúne para mesa, pico y espada de madera.
  - La caída de `wake_up` frente a la referencia (95 → 77) sigue sin explicar.
  - B.2b y B.2c no tienen efecto demostrado: B.2c no se activa en ninguna vida medida.
- **Presupuesto:** queda 1 de los 2 benchmarks completos sin usar.
