# Investigación de Perfiles, Linajes y Fitness por Mundo

Estudio empírico multi-generacional comparando **`main`** (`5c8ae1e`) frente a **`feature/ajustes-cognitivos`** (Fases 1, 2, 3, 4a, ajustes S2/S3, corrección de fitness en `archivos`, aislamiento de `sin_experiencia` e inercia atencional en `Estudio`).

---

## 1. Hallazgos Principales

1. **El carácter pesa mucho más que las diferencias entre ramas, y su óptimo depende del mundo.**
   - En **Mínimo**, el perfil **E. Reactivo** casi duplica la supervivencia del perfil **A. Equilibrado** (`365,90 ± 16,70` latidos frente a `171,57 ± 41,21` en `main`, intervalos al 95 % sin solapamiento).
   - En **Crafter**, la relación se invierte: **D. Valiente** alcanza la mayor puntuación (`10,30`–`10,40` logros) y **E. Reactivo** queda por debajo (`8,57`–`8,90` logros), porque huir pronto frena la recolección y el avance tecnológico.
   - Esta inversión entre mundos (análogo biológico al continuo audaz-tímido) respalda usar **poblaciones y selección natural** para que cada entorno seleccione el arquetipo adecuado sin configurarlo a mano.
2. **Sin diferencias detectadas entre `main` y `feature/ajustes-cognitivos`.**
   - Con $N = 10$ linajes independientes por grupo e intervalos al 95 % con $t_{0,975, 9} = 2,262$, **todos los intervalos de la diferencia pareada ($\Delta = \text{ajustes} - \text{main}$) incluyen el `0`** en `minimo`, `archivos` y `crafter` (y en `ajedrez` la invariancia es del 100 %).
   - *Evaluación TOST (margen declarado `±1,0` logro en Crafter):* `D. Valiente` queda en `[-0,89, +1,09]` (cumple no inferioridad por encima de `-1,0`, roza `+1,09` arriba); `A. Equilibrado` queda en `[-1,59, +1,26]` (no permite declarar equivalencia estricta dentro de `±1,0` logro con $N = 10$, solo ausencia de diferencia detectada).
3. **Atención sostenida en `Estudio` (Fase 4a):**
   - Con el arousal anterior (`0,18`), `Curiosidad` interrumpía el **100 %** de las lecturas (`0/7` en Mínimo y `0/19` en Crafter).
   - Al dotar a [`Estudio`](../ida/sistemas/s3.py#L174-L348) de **inercia atencional progresiva** (`arousal 0,32 → 0,57` y `confianza 0,65 → 0,85` durante la lectura, cediendo ante alarmas o reflejos de S1), las lecturas completadas suben a **`22/56` (39,3 %)** en Mínimo y **`30/55` (54,5 %)** en Crafter (`9,53 ± 1,47` logros).
4. **Límites detectados en el diseño actual:**
   - **Control `sin_experiencia`:** en Crafter (`main`), `MundoCrafter.hitos` seguía activo aunque `sin_experiencia=True`; además, en `ajustes` se ha cerrado [`Organismo`](../ida/core/latido.py#L285-L300) y [`Estudio`](../ida/sistemas/s3.py#L187-L188) para que con `con_experiencia=False` no se ejecute consolidación, `recordar_lugar` ni lectura.
   - **Muertes nocturnas en Crafter:** el 100 % de las muertes registradas (`120/120`) se deben a hostiles/noche; la experiencia no las reduce porque [`DefensaCrafter`](../ida/mundos/crafter.py#L348-L390) actúa solo sobre el estado somático y la escena actual.
   - **Discrepancia con métricas públicas previas:** bajo este protocolo aislado (*tabula rasa*, perfil `Equilibrado`), `main` obtiene `9,30 ± 1,09` logros en Crafter frente a los `10,9` publicados en [`README.md`](../README.md) y [`05_METRICAS_E_HITOS.md`](../doc-repositorio/05_METRICAS_E_HITOS.md) (medidos con `Arquetipo.nuevo` y reutilizando directorio entre ejecuciones); conviene revisar y alinear esa cifra pública tras tus pruebas.

---

## 2. Metodología y Protocolo ($N = 10$ linajes)

- **Fecha:** 12 de noviembre de 2026 (Windows, Python 3.15).
- **Unidad muestral independiente:** $N = 10$ linajes independientes por grupo (semillas `1..10`, directorio limpio por semilla). Se promedia primero cada linaje y sobre los $10$ linajes se calculan media e **IC 95 % con $t$ de Student ($t_{0,975, 9} = 2,262$)**.
- **Profundidad por linaje:** `4` generaciones en `minimo` y `archivos` (`40` vidas/grupo, máx. `400` latidos); `3` generaciones en `crafter` (`30` vidas/grupo, máx. `600` latidos).
- **Nota sobre `snake`:** excluido por depender de navegador externo en tiempo real (`playsnake.org`).

---

## 3. Resultados con IC 95 % ($t_{0,975,9} = 2,262$, $N = 10$ linajes)

### 3.1 Mundo Mínimo (10 linajes × 4 generaciones)

| Grupo | Fitness `main` | Fitness `ajustes` | $\Delta$ Fitness pareado | Latidos `main` | Latidos `ajustes` | $\Delta$ Latidos pareado | Setas/vida (`main` / `ajustes`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 415,70 ± 87,10 | 420,15 ± 83,84 | +4,45 ± 13,61 | 171,57 ± 41,21 | 174,28 ± 39,42 | +2,70 ± 7,01 | 2,33 / 2,27 |
| **D. Valiente** | 623,15 ± 103,78 | 608,02 ± 95,86 | -15,12 ± 69,90 | 303,52 ± 37,63 | 312,77 ± 40,31 | +9,25 ± 27,49 | 3,33 / 3,45 |
| **E. Reactivo** | **780,77 ± 39,61** | **742,52 ± 65,17** | -38,25 ± 66,81 | **365,90 ± 16,70** | **355,52 ± 27,43** | -10,38 ± 29,02 | **1,68 / 1,70** |
| **F. Sin Exp.** | 472,25 ± 84,26 | 470,45 ± 84,83 | -1,80 ± 3,20 | 170,62 ± 30,37 | 169,57 ± 30,53 | -1,05 ± 1,64 | 7,53 / 7,47 |
| **G. Bib. Fija** *(inercia)* | — | 382,18 ± 67,52 | — | — | 163,30 ± 26,33 | — | — / 2,27 |

- **Lecturas en `G. Bib. Fija`:** `56` iniciadas, **`22` completadas (39,3 %)**, `34` interrumpidas.

---

### 3.2 Mundo Archivos (10 linajes × 4 generaciones)

*(La fórmula de fitness de `archivos` se corrigió en [`calcular_fitness`](../ida/historico.py#L41-L48) para penalizar tóxicos; como `main` usaba la fórmula antigua, no se compara su columna de fitness y se comparan solo métricas físicas y el fitness corregido en `ajustes`).*

| Grupo | Latidos `main` | Latidos `ajustes` | $\Delta$ Latidos pareado | Nutritivos / vida (`ajustes`) | Tóxicos / vida (`ajustes`) | Fitness corregido (`ajustes`) |
|---|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 262,95 ± 28,25 | 260,88 ± 28,05 | -2,08 ± 4,05 | 11,65 ± 2,76 | 1,80 ± 0,36 | 924,25 ± 174,38 |
| **D. Valiente** | **273,93 ± 23,37** | **272,07 ± 22,58** | -1,85 ± 4,40 | **11,93 ± 2,82** | 1,80 ± 0,31 | **960,40 ± 168,50** |
| **E. Reactivo** | 263,68 ± 29,77 | 257,65 ± 22,84 | -6,03 ± 12,33 | 11,32 ± 1,95 | **1,77 ± 0,33** | 904,05 ± 115,09 |
| **F. Sin Exp.** | 142,05 ± 57,78 | 142,05 ± 57,78 | 0,00 ± 0,00 | 9,70 ± 1,90 | **9,25 ± 1,99** | **297,45 ± 246,49** |

---

### 3.3 Crafter (10 linajes × 3 generaciones)

| Grupo | Fitness `main` | Fitness `ajustes` | $\Delta$ Fitness pareado | Logros `main` | Logros `ajustes` | $\Delta$ Logros pareado | Latidos `main` / `ajustes` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 9545,00 ± 1104,92 | 9392,27 ± 1444,62 | -152,73 ± 1417,86 | 9,30 ± 1,09 | 9,13 ± 1,42 | -0,17 ± 1,42 | 233,73 / 246,57 |
| **D. Valiente** | **10573,57 ± 1066,66** | **10676,20 ± 1019,71** | +102,63 ± 1010,13 | **10,30 ± 1,05** | **10,40 ± 1,04** | +0,10 ± 0,99 | 260,10 / 262,17 |
| **E. Reactivo** | 9138,63 ± 1253,37 | 8812,20 ± 1424,76 | -326,43 ± 499,60 | 8,90 ± 1,23 | 8,57 ± 1,40 | -0,33 ± 0,49 | 228,07 / 234,73 |
| **F. Sin Exp.** | 10164,57 ± 1163,35 | 9509,60 ± 1321,91 | -654,97 ± 785,08 | 9,90 ± 1,13 | 9,23 ± 1,29 | -0,67 ± 0,77 | 252,60 / 264,13 |
| **G. Bib. Fija** *(inercia)* | — | 9781,73 ± 1484,68 | — | — | 9,53 ± 1,47 | — | — / 236,23 |

- **Lecturas en `G. Bib. Fija`:** `55` iniciadas, **`30` completadas (54,5 %)**, `25` interrumpidas.
- **Causas de muerte (`A. Equilibrado` vs `F. Sin Exp.`, 30 vidas/grupo):** `100 %` combate/hostiles nocturnos (`A`: `22 zombi, 3 esqueleto, 5 hostil/noche` en `main` y `19, 5, 6` en `ajustes`; `F`: `16, 5, 9` en `main` y `20, 2, 8` en `ajustes`). `0` muertes por hambre o sed.

---

## 4. Datos Provisionales ($N = 3$) y Recomendación Provisional para la Antesala

Las pruebas previas con $N = 3$ linajes incluyeron **B. Explorador**, **C. Prudente** y **Ajedrez** (donde `ajustes` mantuvo **100 % de invariancia** frente a `main` en las 84 partidas por rama, con `12-0-0` en `C. Prudente` frente a `11-1-0` en los demás: una sola partida de diferencia, no concluyente).

De forma **provisional** para la antesala web (hasta incorporar poblaciones con selección natural):

- **Mínimo:** **Reactivo** (`apertura=0,40, responsabilidad=0,60, neuroticismo=0,85, extraversion=0,30, umbral_miedo=0,35`).
- **Crafter:** **Valiente** (`apertura=0,60, responsabilidad=0,65, neuroticismo=0,20, extraversion=0,60, umbral_miedo=0,85`).
- **Archivos y Ajedrez:** **Equilibrado** (sin diferencias significativas entre perfiles en $N = 10$ / $N = 3$).
