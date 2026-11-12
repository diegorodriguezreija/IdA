# Investigación de Perfiles, Linajes y Fitness por Mundo

Estudio empírico multi-generacional comparando **`main`** (`5c8ae1e`) frente a **`feature/ajustes-cognitivos`** (`2e03175`, que integra las Fases 1, 2, 3, 4a, los ajustes en S2/S3 y la corrección de fitness en `archivos`).

---

## 1. Hallazgos Principales

1. **El carácter pesa mucho más que las diferencias entre ramas, y su óptimo depende del mundo.**
   - En **Mínimo**, el perfil **E. Reactivo** casi duplica la supervivencia del perfil **A. Equilibrado** (`365,90 ± 14,47` latidos frente a `171,57 ± 35,71` en `main`, intervalos al 95 % sin solapamiento).
   - En **Crafter**, la relación se invierte: **D. Valiente** alcanza la mayor puntuación (`10,30`–`10,40` logros) y **E. Reactivo** queda por debajo (`8,57`–`8,90` logros), porque huir pronto frena la recolección y el avance tecnológico.
   - Esta inversión entre mundos (análogo biológico al continuo audaz-tímido) refuerza la conveniencia de **poblaciones y selección natural** para que cada entorno seleccione el arquetipo adecuado sin tener que fijarlo a mano.
2. **Equivalencia estadística entre `main` y `feature/ajustes-cognitivos`.**
   - Con $N = 10$ linajes independientes por grupo, **todos los intervalos de confianza al 95 % de la diferencia pareada ($\Delta = \text{ajustes} - \text{main}$) incluyen el `0`** en `minimo`, `archivos` y `crafter` (y en `ajedrez` la invariancia es del 100 %). La migración del hipocampo desde `MundoCrafter.hitos` al Core no produce pérdida significativa de logros ni supervivencia.
3. **Resultado negativo en `Estudio` (`G_BibFija`) tras `cd2a8b7`: 0 % de lecturas completadas.**
   - Al bajar el arousal de `LEER` a `0,18` en [`Estudio`](../ida/sistemas/s3.py#L174-L348) y añadir el filtro de objetos visibles, se iniciaron `7` lecturas en `minimo` y `19` en `crafter`, pero **todas (`7/7` y `19/19`) quedaron interrumpidas** antes de terminar. Por eso `G_BibFija` en Crafter coincide exactamente al decimal con `A_Equilibrado`.
4. **Corrección del cálculo de fitness en `archivos`.**
   - Con la métrica anterior ([`calcular_fitness`](../ida/historico.py#L41-L48)), `F. Sin Exp.` puntuaba más alto que ningún otro grupo (`1089,55`) pese a morir en `142` latidos comiendo `9,25` tóxicos por vida. Tras distinguir `nutritivos` y `toxicos` en [`archivos.py`](../ida/mundos/archivos.py#L279-L280), su fitness cae a `297,45 ± 213,58` ($\Delta = -792,10 \pm 208,52$).

---

## 2. Metodología y Protocolo ($N = 10$ linajes)

- **Fecha:** 12 de noviembre de 2026 (Windows, Python 3.15).
- **Unidad muestral independiente:** $N = 10$ linajes independientes por grupo (semillas `1..10`), cada uno en un directorio temporal limpio (`tabula rasa`). Las generaciones sucesivas dentro de un mismo linaje heredan conocimiento y mutan su arquetipo (`mutar()`), por lo que **no** se cuentan como muestras independientes: primero se promedia cada linaje y sobre los $10$ linajes se calculan la media y el **IC 95 %** ($\bar{x} \pm 1,96 \cdot \text{SE}$).
- **Profundidad por linaje:**
  - `minimo` y `archivos`: `4` generaciones por linaje (`40` vidas/grupo, máx. `400` latidos/vida).
  - `crafter`: `3` generaciones por linaje (`30` vidas/grupo, máx. `600` latidos/vida).
  - *(Nota sobre `ajedrez` y los perfiles `B. Explorador` / `C. Prudente`: proceden de una exploración previa con $N = 3$ linajes y se marcan como provisionales en la §4).*
- **Nota sobre `snake`:** excluido de la batería automatizada por depender de navegador externo en tiempo real (`playsnake.org`). Con `duerme=False` y sin biblioteca activa, es conductualmente invariante respecto a `main`.

### Perfiles Evaluados (valores iniciales en G1)

| Prototipo | `apertura` | `responsabilidad` | `neuroticismo` | `extraversion` | `umbral_miedo` |
|---|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 0,50 | 0,50 | 0,50 | 0,50 | 0,60 |
| **D. Valiente** | 0,60 | 0,65 | 0,20 | 0,60 | 0,85 |
| **E. Reactivo** | 0,40 | 0,60 | 0,85 | 0,30 | 0,35 |
| **F. Sin Experiencia** | 0,50 | 0,50 | 0,50 | 0,50 | 0,60 |
| **G. Bib. Fija** *(solo `ajustes`)* | 0,50 | 0,50 | 0,50 | 0,50 | 0,60 |

---

## 3. Resultados con Intervalos de Confianza al 95 % ($N = 10$ linajes)

### 3.1 Mundo Mínimo (10 linajes × 4 generaciones)

| Grupo | Fitness `main` | Fitness `ajustes` | $\Delta$ Fitness pareado | Latidos `main` | Latidos `ajustes` | $\Delta$ Latidos pareado | Setas/vida (`main` / `ajustes`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 415,70 ± 75,47 | 420,15 ± 72,65 | +4,45 ± 11,79 | 171,57 ± 35,71 | 174,28 ± 34,16 | +2,70 ± 6,07 | 2,33 / 2,27 |
| **D. Valiente** | 623,15 ± 89,92 | 608,02 ± 83,06 | -15,12 ± 60,57 | 303,52 ± 32,60 | 312,77 ± 34,93 | +9,25 ± 23,82 | 3,33 / 3,45 |
| **E. Reactivo** | **780,77 ± 34,32** | **742,52 ± 56,47** | -38,25 ± 57,89 | **365,90 ± 14,47** | **355,52 ± 23,77** | -10,38 ± 25,14 | **1,68 / 1,70** |
| **F. Sin Exp.** | 472,25 ± 73,01 | 470,45 ± 73,51 | -1,80 ± 2,77 | 170,62 ± 26,32 | 169,57 ± 26,45 | -1,05 ± 1,42 | **7,53 / 7,47** |
| **G. Bib. Fija** | — | 409,95 ± 78,45 | — | — | 165,45 ± 31,83 | — | — / 2,10 |

- **Lecturas en `G. Bib. Fija`:** `7` iniciadas, **`0` completadas**, `7` interrumpidas.
- **Diferencia de carácter:** `E. Reactivo` casi duplica los latidos de `A. Equilibrado`; sin experiencia se ingieren ~3,5× más setas tóxicas (`7,5` frente a `1,7`–`2,3` por vida).

---

### 3.2 Mundo Archivos (10 linajes × 4 generaciones, fitness corregido)

| Grupo | Fitness `main` *(fórmula ant.)* | Fitness `ajustes` *(corregido)* | Latidos `main` | Latidos `ajustes` | $\Delta$ Latidos pareado | Nutritivos / Tóxicos (`ajustes`) |
|---|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 940,45 ± 158,46 | 924,25 ± 151,10 | 262,95 ± 24,47 | 260,88 ± 24,31 | -2,08 ± 3,51 | 11,65 ± 2,39 / 1,80 ± 0,31 |
| **D. Valiente** | 981,42 ± 153,13 | **960,40 ± 146,00** | 273,93 ± 20,25 | **272,07 ± 19,56** | -1,85 ± 3,82 | 11,93 ± 2,44 / 1,80 ± 0,27 |
| **E. Reactivo** | 934,92 ± 157,97 | 904,05 ± 99,72 | 263,68 ± 25,79 | 257,65 ± 19,79 | -6,03 ± 10,68 | 11,32 ± 1,69 / 1,77 ± 0,29 |
| **F. Sin Exp.** | 1089,55 ± 93,57 | **297,45 ± 213,58** | 142,05 ± 50,07 | 142,05 ± 50,07 | 0,00 ± 0,00 | 9,70 ± 1,64 / **9,25 ± 1,73** |

*(Nota: `main` ejecutó la fórmula anterior porque no incluye el commit `2e03175`; la comparación directa de supervivencia `ΔLatidos` entre ramas no muestra diferencias significativas).*

---

### 3.3 Crafter (10 linajes × 3 generaciones)

| Grupo | Fitness `main` | Fitness `ajustes` | $\Delta$ Fitness pareado | Logros `main` | Logros `ajustes` | $\Delta$ Logros pareado | Latidos `main` / `ajustes` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 9545,00 ± 957,40 | 9392,27 ± 1251,75 | -152,73 ± 1228,56 | 9,30 ± 0,94 | 9,13 ± 1,23 | -0,17 ± 1,23 | 233,73 / 246,57 |
| **D. Valiente** | **10573,57 ± 924,25** | **10676,20 ± 883,57** | +102,63 ± 875,26 | **10,30 ± 0,91** | **10,40 ± 0,90** | +0,10 ± 0,86 | 260,10 / 262,17 |
| **E. Reactivo** | 9138,63 ± 1086,03 | 8812,20 ± 1234,54 | -326,43 ± 432,90 | 8,90 ± 1,07 | 8,57 ± 1,21 | -0,33 ± 0,42 | 228,07 / 234,73 |
| **F. Sin Exp.** | 10164,57 ± 1008,03 | 9509,60 ± 1145,42 | -654,97 ± 680,26 | 9,90 ± 0,98 | 9,23 ± 1,12 | -0,67 ± 0,67 | 252,60 / 264,13 |
| **G. Bib. Fija** | — | 9392,27 ± 1251,75 | — | — | 9,13 ± 1,23 | — | — / 246,57 |

- **Lecturas en `G. Bib. Fija`:** `19` iniciadas, **`0` completadas**, `19` interrumpidas.
- **Análisis de causas de muerte (`A. Equilibrado` vs `F. Sin Exp.`, 30 vidas/grupo):**
  - `A. Equilibrado`: `main` (`22` zombi, `3` esqueleto, `5` hostil/noche) · `ajustes` (`19` zombi, `5` esqueleto, `6` hostil/noche).
  - `F. Sin Exp.`: `main` (`16` zombi, `5` esqueleto, `9` hostil/noche) · `ajustes` (`20` zombi, `2` esqueleto, `8` hostil/noche).
  - El **100 % de las muertes** (`120/120` en los cuatro grupos registrados) se debe a combate nocturno o daño hostil (`0` muertes por hambre o sed). Aunque `F. Sin Exp.` promedia `+17`–`+19` latidos más que `A. Equilibrado`, esa diferencia entra holgadamente en el margen de error (`±27`–`±36`), y en logros `F. Sin Exp.` queda igual o por debajo en `ajustes` (`9,23` vs `9,13`) y por debajo de `D. Valiente` (`10,40`). La experiencia no reduce el riesgo nocturno actual porque [`DefensaCrafter`](../ida/mundos/crafter.py#L348-L390) opera directamente sobre el estado somático y la escena sin depender de proposiciones aprendidas.

---

## 4. Datos Provisionales ($N = 3$ linajes) y Recomendación Provisional para la Antesala

Las pruebas previas con $N = 3$ linajes incluyeron además **B. Explorador**, **C. Prudente** y **Ajedrez**. Con $N = 3$, las diferencias pequeñas no son concluyentes (por ejemplo, en **Ajedrez** dificultad 1: `C. Prudente` obtuvo `12 V · 0 T · 0 D` frente a `11 V · 1 T · 0 D` de los demás, una sola partida de diferencia, con **100 % de invariancia** entre `main` y `ajustes`).

De forma **provisional** para la antesala web (hasta implementar selección natural sobre poblaciones):

- **Mínimo:** perfil **Reactivo** (`apertura=0,40, responsabilidad=0,60, neuroticismo=0,85, extraversion=0,30, umbral_miedo=0,35`), avalado por la diferencia clara con $N=10$ (`~356`–`366` latidos frente a `~172`–`174` del equilibrado).
- **Crafter:** perfil **Valiente** (`apertura=0,60, responsabilidad=0,65, neuroticismo=0,20, extraversion=0,60, umbral_miedo=0,85`), el único en superar los `10` logros medios en ambas ramas con $N=10$.
- **Archivos y Ajedrez:** mantener **Equilibrado** (o **Valiente** en Archivos) mientras no haya diferencias estadísticamente significativas entre perfiles.
