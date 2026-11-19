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
| Calidad automatizada: ruff, mypy y 85 tests (`python -m pytest -q` en `7e335ae`, 16/11/2026) en GitHub Actions (Python 3.12 y 3.15, con y sin dependencias de mundo) | `.github/workflows/ci.yml` |

---

## Resumen por mundo

| Mundo | Métrica principal | Base | Optimizado |
|---|---|---|---|
| Mínimo | Latidos de vida (media, 15 vidas) | 141 | **198** |
| Archivos | Latidos de vida (media, 12 vidas) | 223 | **270** |
| Archivos | Mordiscos tóxicos por vida | 7,2 | **2,2** |
| Snake (pitón) | Puntos por vida (media) | ~232 (10 vidas) | **916** (6 vidas) · máximo **1605** |
| Crafter | Logros por vida (protocolo aislado, 10 linajes × 3 generaciones, IC 95 %) | no medido | **9,30 ± 1,09** |
| Crafter | Latidos de vida (protocolo aislado, 10 linajes × 3 generaciones) | no medido | **233,7** |
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

### Crafter Score (protocolo oficial)

Evaluación con el protocolo oficial de Crafter: episodios de hasta 10 000 pasos, vista local oficial 9×7 en forma simbólica y media geométrica de las tasas de éxito de los 22 logros (presupuesto de 100 000 pasos). [Método y datos completos](../docs/MEDICION_OFICIAL.md).

```powershell
python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial --sin-herencia
```

| Condición | Score Crafter (IC 95 %) | Episodios | Pasos / episodio | Rendimiento (ms/paso) | Tiempo total (s) |
|---|---|---|---|---|---|
| **Suelo (`main` sin estrategias)** | **1,46 %** [1,38, 1,52] % | 401 | 249,4 | 13,79 ms | 1.379,2 s |
| **Techo `main` (con linaje)** | **20,26 %** [18,45, 21,69] % | 264 | 378,8 | 11,65 ms | 1.165,1 s |
| **`main` sin herencia** | **19,18 %** [17,74, 20,46] % | 278 | 359,7 | 12,06 ms | 1.205,8 s |
| **Techo C.3d (`feature/crafter-fase-c`)** | **20,58 %** [18,91, 21,88] % | 251 | 398,4 | 9,92 ms | 992,0 s |

#### Referencias

| Agente | Crafter Score | Entrenamiento | Nota |
|---|---|---|---|
| Humanos expertos | 50,5 ± 6,8 % | — | Hafner (2021) |
| SPRING (GPT-4) | 27,3 % | Ninguno (LLM preentrenado) | Wu et al. (2023); lee el artículo de Crafter |
| DreamerV2 | 10,0 ± 1,2 % | 1M de pasos | Hafner (2021) |
| PPO | 4,6 ± 0,3 % | 1M de pasos | Hafner (2021) |
| Aleatorio | 1,6 % | — | Hafner (2021) |

> **Resultados recientes de la literatura:** Un agente de RL con modelo del mundo obtiene alrededor de un 28 % con 1M de pasos en Craftax-classic, una reimplementación no idéntica (arXiv 2502.01591), y EMERALD llega al 58,1 % con 10M de pasos (arXiv 2507.04075).

#### Declaraciones del protocolo (sección 4.3 de `docs/FASE_GENERALIZACION_CRAFTER.md`)

- **Entrada simbólica:** IdA recibe una descripción simbólica de la vista local oficial (9×7), sin estado oculto. Toda la información es visible en la imagen.
- **Coordenadas absolutas:** IdA recibe del adaptador las coordenadas de su casilla. Un agente sin ellas podría obtenerlas por integración de trayecto (las acciones son deterministas y se observa si el movimiento tuvo efecto).
- **Noche:** IdA reduce el radio a 2 con luz < 0,3 (restricción propia, más estricta que la oficial, que solo añade ruido y oscurece la imagen).
- **Linaje:** Las vidas heredan proposiciones y registros. Se publican dos cifras: sin herencia (recién nacido sin legado, cero entrenamiento) y con linaje completo.
- **Perfil:** Se fija el perfil Equilibrado para la evaluación.

### Protocolos anteriores (logros por vida e historia)

**Cambios del mundo (adaptación biológica y supervivencia):**
- **Mapa cognitivo (hipocampo)**: si el individuo explora lejos para minar y reúne los materiales de una receta, navega de vuelta al taller (mesa, horno) en vez de quedar inmóvil en la oscuridad. En la versión medida aquí (11/11/2026) el mapa era propio del mundo (`self.hitos` en el adaptador de Crafter). Desde el PR #4 está en el Core: `PlanTecnologico` consulta la memoria del individuo con `ctx.memoria.donde_esta(clase)` y `ctx.memoria.ruta(origen, destino)` (`ida/core/memoria.py:404` y `:436`; uso en `ida/mundos/crafter.py:508-510`), y con `--sin-experiencia` no la consulta.
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

Medido el 11 de noviembre de 2026. **Medición retirada como cifra principal:** el comando no lleva `--tabula-rasa` ni fija el carácter, y el directorio `datos/crafter` se reutilizó entre ejecuciones (según [`docs/BENCHMARK_PERFILES_MUNDOS.md`](../docs/BENCHMARK_PERFILES_MUNDOS.md), §1.4). En ese caso cada semilla continúa el linaje de la anterior: muta el arquetipo del último individuo y hereda su legado (`ida/ejecutor.py` en `5c8ae1e`, líneas 52, 71 y 86); solo la primera parte de un arquetipo aleatorio (`Arquetipo.nuevo`). Las 10 vidas no eran independientes. Se conserva la tabla como registro; los porcentajes de mejora que se publicaron con ella (+26,5 % de vida, +19,8 % de logros) no se sostienen con este método.

**Protocolo aislado** (12 de noviembre de 2026, Windows, Python 3.15; detalle en [`docs/BENCHMARK_PERFILES_MUNDOS.md`](../docs/BENCHMARK_PERFILES_MUNDOS.md)): semillas 1 a 10, un directorio de datos limpio por semilla, 3 generaciones por linaje (30 vidas), 600 latidos máximos, carácter inicial fijo. Se promedia cada linaje y sobre los 10 linajes se calcula la media con IC 95 % ($t_{0,975,9} = 2,262$). Se ejecutó con `ida.ejecutor.ejecutar(..., tabula_rasa=True, arquetipo_inicial=...)`; el script de la batería no está en el repositorio.

| Perfil inicial | Logros `5c8ae1e` | Logros `25e1303` (= árbol de `main` actual) | Δ pareado | Latidos `5c8ae1e` / `25e1303` |
|---|---|---|---|---|
| Equilibrado (rasgos 0,50, `umbral_miedo` 0,60) | **9,30 ± 1,09** | 9,13 ± 1,42 | −0,17 ± 1,42 | 233,7 / 246,6 |
| Valiente | 10,30 ± 1,05 | 10,40 ± 1,04 | +0,10 ± 0,99 | 260,1 / 262,2 |
| Reactivo | 8,90 ± 1,23 | 8,57 ± 1,40 | −0,33 ± 0,49 | 228,1 / 234,7 |

La versión base (antes de la adaptación biológica) no se ha medido con este protocolo, así que no hay cifra de mejora aislada frente a ella. En las 30 vidas del perfil Equilibrado, el 100 % de las muertes son por hostiles de noche.

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
