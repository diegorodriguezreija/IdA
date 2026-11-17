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
