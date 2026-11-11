# 05. Métricas e Hitos 📊

Lo conseguido en cada mundo, con los comandos para repetirlo. Las cifras se publican tal como salieron, también las malas.

**Cómo se midió (9 y 10 de noviembre de 2026, Windows 10, Python 3.15.1).** Para cada mundo se comparan dos versiones del **código del mundo** sobre el mismo framework base: la **base** (el mundo recién conectado, antes de optimizarlo) y la **optimizada** (la publicada). Se usan las mismas semillas y generaciones en ambas. Solo cambia el código del mundo, sus sensores y sus componentes propios; `ida/core` e `ida/sistemas` no se tocan.

**Límites.** No es un estudio: hay de 6 a 15 vidas por versión. Las diferencias grandes son fiables; las pequeñas, no. Snake juega en una web en tiempo real y no es repetible.

---

## Hitos del framework base

| Hito | Dónde se ve |
|---|---|
| Un mismo núcleo, sin cambios, vive en cinco mundos muy distintos: web en tiempo real, disco, simulador 2D y tablero | `ida/core`, `ida/sistemas`, test de pureza |
| Guillotina cooperativa: con plazo 0 ms la cognición se corta y el Tribunal sigue decidiendo | `tests/test_organismo.py` |
| Repetible con semilla: mundo mínimo, archivos, Crafter y ajedrez (rival local) dan la misma vida con la misma semilla, también entre procesos | Tests y ejecuciones con distintos `PYTHONHASHSEED` |
| Conocimiento legible aprendido de la experiencia («la seta hace daño», «el agua nutre», «la pared hace daño») | Consola y panel |
| Trauma: la causa de una muerte queda demostrada y se hereda dentro del linaje | Snake, Crafter, mundo mínimo |
| La experiencia cambia decisiones, y se ve | Consola y panel («decisiones cambiadas por la experiencia») |
| Indicio de que la experiencia ayuda: en el mundo mínimo, sin experiencia se vive menos y se comen más setas tóxicas | Ver abajo |
| Telemetría en vivo sin dependencias: presupuesto del latido, reparto por sistema, memoria, carácter y conocimiento | `python -m ida --mundo X --ver` |
| Observabilidad estándar: cada latido es una traza de OpenTelemetry con sus fases (Jaeger) y hay métricas en Prometheus y Grafana, sin que el núcleo dependa de ello | `docker compose up --build` |
| Calidad automatizada: ruff, mypy y 64 tests en GitHub Actions (Python 3.12 y 3.15, con y sin dependencias de mundo) | `.github/workflows/ci.yml` |

---

## Resumen por mundo

| Mundo | Métrica principal | Base | Optimizado |
|---|---|---|---|
| Mínimo | Latidos de vida (media, 15 vidas) | 141 | **198** |
| Archivos | Latidos de vida (media, 12 vidas) | 223 | **270** |
| Archivos | Mordiscos tóxicos por vida | 7,2 | **2,2** |
| Snake (pitón) | Puntos por vida (media) | ~232 (10 vidas) | **916** (6 vidas) · máximo **1605** |
| Crafter | Logros por vida (media, 10 vidas) | 9,1 | **10,9** (máx. **16**) |
| Crafter | Latidos de vida (media, 10 vidas) | 208,6 | **263,8** (máx. **443**) |
| Ajedrez | Resultado contra la dificultad 1 (8 partidas) | 5 V · 3 T | **7 V · 1 T** |
| Ajedrez | Resultado contra la dificultad 2 (8 partidas) | 1 V · 5 T · 2 D | **3 V · 3 T · 2 D** |
| Ajedrez | Resultado contra la dificultad 3 (8 partidas) | 0 V · 1 T · 6 D | 0 V · 2 T · 5 D |

---

## Mundo mínimo

**Componente propio añadido:** `Defensa` (S1). Huir del lobo no sirve, porque persigue: si está al alcance y queda vitalidad, plantarle cara.

```powershell
python -m ida --mundo minimo --latidos 400 --generaciones 3 --semilla S --tabula-rasa   # S = 1..5
```

| | Base | Optimizado |
|---|---|---|
| Latidos de vida (media / mediana, 5 semillas × 3 generaciones) | 141 / 119 | **198 / 181** |

**Con y sin experiencia** (semilla 3, 4 vidas por grupo, versión base): con experiencia, 239 latidos de media y 9 setas tóxicas comidas en total; sin experiencia, 139 latidos y 29 setas. Es un indicio, no una demostración. El lobo sigue siendo la causa de muerte habitual.

## Archivos

**Componentes propios añadidos:**
- `Defensa` (S1): ataca al depredador de la carpeta.
- `Prudencia` (S3): frena lo que tiene indicios de daño aunque aún no esté demostrado; aplica neofobia (primero lo que se sabe que nutre); recuerda las carpetas donde solo había comida dañina y propone buscar en otra parte.

```powershell
python -m ida --mundo archivos --latidos 400 --generaciones 3 --semilla S --tabula-rasa   # S = 1..4
```

| | Base | Optimizado |
|---|---|---|
| Latidos de vida (media / mediana, 4 semillas × 3 generaciones) | 223 / 232 | **270 / 283** |
| Mordiscos a especies tóxicas por vida (media) | 7,2 (de 1 a 16) | **2,2** (de 1 a 3) |

**Hitos:** distingue por experiencia especies que tienen exactamente la misma apariencia de bytes; con la prudencia, cada especie tóxica se prueba una o dos veces y no más. Nunca toca nada fuera de su bioma.

## Snake (playsnake.org, nivel pitón)

**Cambios del mundo:** latido de **60 ms** (a 100 ms llegaba tarde a ritmo pitón); la causa de muerte proyecta la dirección hasta 3 casillas; pared y cuerpo solo se ofrecen como lugares si no queda ninguna casilla segura.

```powershell
python -m ida --mundo snake --latidos 1500 --generaciones 6 --tabula-rasa --opcion dificultad=piton
```

| | Base | Optimizado |
|---|---|---|
| Puntos por vida | 515, 25, 255, 230, 240 · 0, 210, 110, 225, 505 (media ~232) | 325, 875, 860, 410, 1420, 1605 (media **916**) |
| Latidos de vida | — | 104, 377, 335, 119, 534, 544 |
| Causas de muerte identificadas | muchas «desconocida» | **todas** (pared ×4, cuerpo ×2) |

La versión optimizada con el latido antiguo de 100 ms dio una media de 90 en 5 vidas: lo decisivo fue el ritmo. **Hitos:** juega en una web real en tiempo real; aprende y hereda «la pared hace daño» y «la comida nutre»; **1605 puntos** en nivel pitón.

## Crafter

**Cambios del mundo (adaptación biológica y supervivencia):**
- **Mapa cognitivo (hipocampo espacial `self.hitos`)**: recuerda la ubicación de infraestructuras clave (`mesa`, `horno`, `planta`, `agua`). Si el individuo explora lejos para minar y reúne los materiales de una receta, navega de vuelta al taller en vez de quedar inmóvil en la oscuridad.
- **Defensa armada activa (`DefensaCrafter` en S1)**: asimetría lucha/huida biológica. Con espada y salud $\ge 40\%$, el combate activo defensivo supera al reflejo pasivo de huida en esquinas (urgencia 0.96/0.88), abatiendo hostiles inmediatos y cerrando distancia contra esqueletos que disparan a 2-3 casillas.
- **Aliestesia de reparación**: si la salud cae por debajo de 7, el valor homeostático de hidratarse y alimentarse se multiplica por 1.3 para acelerar la regeneración celular nativa de Crafter.
- `PlanTecnologico` (S3) aprovecha logros al alcance y propone dormir en refugio seguro.
- Crafter es repetible con semilla: identificadores de criaturas estables y zonas con orden de inserción.

```powershell
python -m ida --mundo crafter --latidos 600 --semilla S   # S = 1..10
```

| Métrica | Base (`main`) | Adaptación Biológica |
|---|---|---|
| Logros por vida (10 semillas independientes) | 9, 5, 11, 11, 10, 12, 8, 8, 8, 9 (media 9,1) | 9, 10, 10, 10, 16, 13, 11, 8, 9, 13 (media **10,9**) |
| Latidos de vida (10 semillas independientes) | 180, 267, 286, 191, 244, 179, 190, 206, 158, 185 (media 208,6) | 177, 443, 431, 203, 274, 268, 258, 205, 187, 192 (media **263,8**) |
| Tasa de combate activo (`defeat_zombie`) | 0 % (0 / 10 vidas) | **70 %** (7 / 10 vidas) |
| Logro `make_stone_pickaxe` | 0 % (0 / 10 vidas) | **40 %** (4 / 10 vidas) |
| Máximo vital alcanzado | 286 latidos / 12 logros | **443 latidos / 16 logros** (alcanza horno, espada y pico de piedra) |

Medido el 11 de noviembre de 2026. La vida se alarga un **+26,5 %** de media y los logros suben un **+19,8 %**, transformando a IdA de presa pasiva a un organismo con memoria espacial y defensa armada efectiva.

## Ajedrez (rival local corregido)

**Cambios del mundo:** el sensor valora rematar con ventaja (con 3 o más de ventaja de material: jaque, quitar casillas al rey rival, avanzar peones y no repetir posición) y buscar tablas en desventaja (repetir posición vale).

```powershell
python -m ida --mundo ajedrez --latidos 200 --generaciones 2 --semilla S --tabula-rasa --opcion dificultad=N   # S = 1..4
```

| Rival | Base | Optimizado |
|---|---|---|
| Dificultad 1 (1 ply) | 5 V · 3 T · 0 D | **7 V · 1 T · 0 D** |
| Dificultad 2 (alfa-beta 2 ply) | 1 V · 5 T · 2 D | **3 V · 3 T · 2 D** |
| Dificultad 3 (alfa-beta 3 ply) | 0 V · 1 T · 6 D (1 sin terminar) | 0 V · 2 T · 5 D (1 sin terminar) |

**Hitos:** gana al rival de 2 ply con una mente genérica que solo ve una respuesta del rival por jugada. Contra el de 3 ply sigue perdiendo: le faltan combinaciones más largas. No se le darán ampliando el sensor, porque entonces jugaría el mundo y no IdA (ver [03, «El mundo percibe; IdA piensa»](03_LOS_MUNDOS.md)).
