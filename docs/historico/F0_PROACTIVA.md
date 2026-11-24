# F0: inventario de la experiencia proactiva

Encargo: [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), «Encargo del bloque F». Diseño: [`REDISENO_BASE.md`](REDISENO_BASE.md), decisión 24 (Expectativa y Plan primero; Prospectiva e Imaginación después). Rama `feature/bloque-f` desde `feature/bloque-e`.

## Qué hay ya

| Pieza existente | Dónde | Qué hace hoy |
|---|---|---|
| Barrido `proactiva` | [`ida/nucleo/arquitectura.py`](../../ida/nucleo/arquitectura.py) (`BARRIDOS`, `Componente.proactiva`) | Tercer barrido de cada módulo, tras el reactivo y el activo. Ningún componente de S1, S2 ni S3 lo implementa: está vacío |
| `Memoria.proyectar` y `Expectativa` | [`ida/nucleo/memoria.py`](../../ida/nucleo/memoria.py) | El Core, tras actuar ([`latido.py`](../../ida/core/latido.py), paso 6), anota una sola expectativa: el balance medio recordado de (verbo, clase) de la acción ejecutada. No predice MOVER |
| Contraste y error de predicción | `Memoria.aprender` (dimensión proactiva) | Al latido siguiente compara balance esperado y obtenido: `rpe`; si el signo no coincide, sorpresa. Cuenta `aciertos` y `fallos` |
| Pieza `Sorpresa` | `Organismo._aprender` | El Core la percibe sin peaje (arousal 0,85) cuando hay sorpresa; además `rpe` mueve la dopamina de `Soma`. Abre episodio y rompe la calma |
| Feedback por error de predicción | `Feedback` de S3 ([`ida/s3/`](../../ida/s3/)) | Δ aciertos − Δ sorpresas: mérito de las estrategias de S3 |
| Feedback de S1 y S2 | `Feedback` de S1 (Δ déficits) y S2 (Δ placer, Δ estrés) | Mejora real entre latidos; no hay término de predicción |
| Cadenas de pasos | `recordar_comida` (S2) recalcula cada latido el siguiente salto (`memoria.ruta`); `PlanTecnologico` (S3, Crafter) recorre las recetas en orden y lleva su propio control de fallos | No hay tipo Plan: ni cadena explícita, ni progreso como parte completada, ni rehacer ante una expectativa fallida |

## En qué se convierte

| Paso | Mecanismo | Interruptor | Qué cambia |
|---|---|---|---|
| F1 | Expectativa | `Perfil.mecanismos.expectativa` | S1 y S2 implementan el barrido proactivo: con potencia de sobra dejan una pieza `Expectativa` (en `ef`, pasa a `ei` del latido siguiente) sobre su propuesta de mayor arousal. S1: cambio esperado de cada déficit; S2: valencia esperada. Lo esperado sale de un modelo de transiciones por (sistema, verbo, clase) aprendido de lo vivido (episódico); si la clase no tiene modelo, del concepto más parecido (E3) y, para S2, de la valencia del nodo del grafo (E2). Al empezar el latido siguiente el Core contrasta la expectativa con lo que llega si la acción ejecutada fue esa: actualiza el modelo, cuenta acierto o fallo (los mismos contadores que usa el feedback de S3), y con error alto emite la `Sorpresa` existente y sube el arousal de lo percibido de esa clase. El feedback de S1 y S2 suma el error de predicción con signo. `proyectar` y su `Expectativa` de balance se mantienen |
| F2 | Plan | `Perfil.mecanismos.plan` | Tipo `Plan` de estrategia: cadena de pasos guardada en la propia pieza `Estrategia` (`paso`), consumida paso a paso; progreso = parte completada; si la expectativa de un paso falla, se rehace una vez y, si vuelve a fallar, se agota. Se aplica a `recordar_comida` (ruta completa del mapa hasta donde se recuerda la comida, eligiendo destino también por la fuerza del nodo del grafo) y a `PlanTecnologico` (cadena de recetas pendientes) |

Con todos los interruptores de E y F apagados, la conducta es la de `base-v2.0` (`herramientas/invariancia.py`).

## Benchmark de E tal como está

El ajuste de E4 (reducción con *decay*, f0b3884) se midió solo en archivos. Medición en mínimo y Crafter: ver [`MEDICIONES_F.md`](MEDICIONES_F.md), sección «F0».
