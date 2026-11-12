# Investigación y Medición de Fitness por Perfiles y Mundos

Evaluación sistemática multi-generacional por *batches* comparando **`main`** (`5c8ae1e`) frente a **`feature/ajustes-cognitivos`** (`cd2a8b7`, que integra las Fases 1, 2, 3, 4a y los ajustes en S2/S3). El objetivo es determinar empíricamente qué prototipo de arquetipo (Big Five) obtiene mejor desempeño y fitness en cada mundo para poder proponer configuraciones recomendadas en la antesala web.

---

## 1. Metodología y Protocolo Experimental

- **Fecha de medición:** 12 de noviembre de 2026 (Windows, Python 3.15).
- **Aislamiento por semilla (*tabula rasa*):** cada pareja `(batch, semilla)` se ejecutó en un directorio temporal independiente (`tempfile.TemporaryDirectory()`), garantizando arranque desde cero sin contaminación entre semillas ni entre ramas.
- **Linajes multi-generacionales:** en cada semilla se encadenaron varias generaciones sucesivas para permitir la herencia cultural (`legado()` / `heredar()`) y la mutación de arquetipos (`mutar()`):
  - **`minimo`** y **`archivos`:** `3` semillas × `5` generaciones (`15` vidas por batch, límite `400` latidos/vida).
  - **`crafter`:** `3` semillas × `4` generaciones (`12` vidas por batch, límite `600` latidos/vida).
  - **`ajedrez`:** `3` semillas × `4` generaciones (`12` partidas por batch, límite `200` latidos/partida, dificultades `1` y `2`).
  - **`snake`:** excluido de la batería automatizada por depender de navegador externo en tiempo real (`playsnake.org`). Al tener `duerme=False` y ausencia de biblioteca activa por defecto, mantiene invariancia conductual respecto a `main`.
- **Cálculo de fitness:** fórmula oficial de [`calcular_fitness()`](file:///f:/code/IdA/ida/historico.py#L16-L51).

### Prototipos de Arquetipo Evaluados

| Prototipo | `apertura` | `responsabilidad` | `neuroticismo` | `extraversion` | `umbral_miedo` | Perfil conductual |
|---|---:|---:|---:|---:|---:|---|
| **A. Equilibrado** | 0,50 | 0,50 | 0,50 | 0,50 | 0,60 | Línea base neutra por defecto |
| **B. Explorador** | 0,85 | 0,30 | 0,35 | 0,70 | 0,70 | Alta curiosidad por lo nuevo, baja prudencia |
| **C. Prudente** | 0,30 | 0,85 | 0,55 | 0,40 | 0,50 | Alto peso epistémico de lo aprendido y cautela |
| **D. Valiente / Resiliente** | 0,60 | 0,65 | 0,20 | 0,60 | 0,85 | Resiste más tiempo antes de disparar reflejos de huida |
| **E. Reactivo / Cauteloso** | 0,40 | 0,60 | 0,85 | 0,30 | 0,35 | Alta sensibilidad al peligro; huye muy temprano |
| **F. Sin Experiencia** | 0,50 | 0,50 | 0,50 | 0,50 | 0,60 | Control ablativo (`sin_experiencia=True`) |
| **G. Bib. Fija** *(solo rama ajustes)* | 0,50 | 0,50 | 0,50 | 0,50 | 0,60 | `Equilibrado` + `BibliotecaFija` con datos del mundo |

---

## 2. Resumen Ejecutivo: Configuración Recomendada por Mundo (Antesala)

| Mundo | Prototipo Ganador | Fitness medio (`main` → `ajustes`) | Métrica clave del ganador | Por qué funciona mejor |
|---|---|---:|---|---|
| **Mínimo** | **E. Reactivo** | `780,40` → **`791,87`** | **387,87 latidos** · 24 setas en 15 vidas | El lobo es letal; huir en cuanto aparece (`umbral_miedo=0,35`, `neuroticismo=0,85`) casi duplica la supervivencia respecto al perfil equilibrado. |
| **Archivos** | **E. Reactivo** *(o **D. Valiente**)* | `1023,33` → **`1028,20`** | **274,87 latidos** · 15,07 comidos/vida | Evita amenazas tempranas sin frenar la recolección; `Prudencia` ya filtra bien los tóxicos independientemente del arquetipo. |
| **Crafter** | **D. Valiente** | `10 145,42` → **`10 403,25`** | **10,17 logros** (máx. 14) · 221,33 latidos | Un umbral de miedo alto (`0,85`) y bajo neuroticismo (`0,20`) evita el pánico prematuro y permite minar, fabricar y defenderse con espada. |
| **Ajedrez** | **C. Prudente** | `3022,17` → **`3022,17`** | **12 V · 0 T · 0 D (100 % victorias en d1)** | La alta responsabilidad (`0,85`) y baja apertura (`0,30`) consolidan líneas sólidas sin distracciones exploratorias. |

---

## 3. Resultados Detallados por Mundo

### 3.1 Mundo Mínimo (3 semillas × 5 generaciones = 15 vidas/batch, máx. 400 latidos)

| Batch | Fitness `main` | Fitness `ajustes` | Latidos `main` | Latidos `ajustes` | Bayas med. (`main` / `ajustes`) | Setas tot. (`main` / `ajustes`) | G1 → G5 (`ajustes`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 454,07 | 452,93 | 193,40 | 193,60 | 12,40 / 12,33 | 38 / 38 | 375,67 → 405,33 |
| **B. Explorador** | 398,20 | **416,53** | 184,87 | 183,53 | 9,93 / **11,00** | 44 / **39** | 217,00 → 503,33 |
| **C. Prudente** | 584,53 | 577,53 | 250,87 | **253,87** | 16,20 / 15,67 | 29 / 31 | 748,33 → 647,67 |
| **D. Valiente** | 650,60 | 620,87 | 321,93 | 319,53 | 15,60 / 14,20 | 50 / 52 | 645,33 → 757,00 |
| **E. Reactivo** | 780,40 | **791,87** | 366,07 | **387,87** | 20,33 / 19,80 | 23 / 24 | 823,33 → 704,33 |
| **F. Sin Exp.** | 471,53 | 471,53 | 169,20 | 169,20 | 13,07 / 13,07 | 123 / 123 | 488,67 → 437,00 |
| **G. Bib. Fija** | — | 447,20 | — | 190,53 | — / 12,27 | — / 34 | 400,67 → 386,00 |

- **Hallazgos clave:**
  - La experiencia y la herencia marcan una diferencia abismal en toxicidad: **123 setas tóxicas** comidas sin experiencia frente a **23–52** con memoria activa.
  - **`E. Reactivo`** domina por amplio margen (**+75 % de fitness** sobre `Equilibrado` y casi el límite completo de 400 latidos por vida).
  - En **`B. Explorador`**, `ajustes` mejora de `398,20` a `416,53` (pico máximo de `1095,0` frente a `885,0` en `main`) y el linaje crece claramente de G1 (`217,00`) a G5 (`503,33`).

---

### 3.2 Mundo Archivos (3 semillas × 5 generaciones = 15 vidas/batch, máx. 400 latidos)

| Batch | Fitness `main` | Fitness `ajustes` | Latidos `main` | Latidos `ajustes` | Comidos med. (`main` / `ajustes`) | G1 → G5 (`ajustes`) |
|---|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | 989,40 | 984,93 | 269,40 | 264,93 | 14,40 / 14,40 | 917,33 → 1008,00 |
| **B. Explorador** | 952,67 | **960,53** | 269,33 | 263,87 | 13,67 / **13,93** | 914,00 → 778,00 |
| **C. Prudente** | 983,93 | 976,20 | 270,60 | 262,87 | 14,27 / 14,27 | 918,33 → 1008,00 |
| **D. Valiente** | 1022,13 | 1021,53 | 272,13 | 271,53 | 15,00 / 15,00 | 1066,67 → 915,67 |
| **E. Reactivo** | 1023,33 | **1028,20** | 276,67 | 274,87 | 14,93 / **15,07** | 1013,00 → 1008,00 |
| **F. Sin Exp.** *(ver nota)* | 1182,73 | 1182,73 | 129,40 | 129,40 | 21,07 / 21,07 | 1153,33 → 1327,00 |

- **Hallazgos clave y nota metodológica:**
  - Entre perfiles con experiencia, **`E. Reactivo`** (`1028,20`) y **`D. Valiente`** (`1021,53`) encabezan la tabla con ~272–275 latidos medios y 15 recursos ingeridos por vida.
  - **Anomalía detectada en el cálculo de fitness de `archivos`:** `F. Sin Exp.` obtiene el mayor escalar (`1182,73`) pese a vivir **menos de la mitad** (`129,40` latidos frente a `274,87`), porque [`calcular_fitness()`](file:///f:/code/IdA/ida/historico.py#L41-L44) suma `total_comido * 50 + latidos` sin penalizar los alimentos tóxicos ingeridos. Se recomienda revisar esa fórmula en el futuro si se usa selección automática en `archivos`.
  - Entre `main` y `ajustes` las diferencias son mínimas (`±0,5 %`), con ligera ventaja de `ajustes` en `E. Reactivo` y `B. Explorador` y ligera desventaja en `A/C`.

---

### 3.3 Crafter (3 semillas × 4 generaciones = 12 vidas/batch, máx. 600 latidos)

| Batch | Fitness `main` | Fitness `ajustes` | Logros med. (`main` / `ajustes`) | Logros máx. (`main` / `ajustes`) | Latidos med. (`main` / `ajustes`) | G1 → G4 (`ajustes`) |
|---|---:|---:|---:|---:|---:|---:|
| **A. Equilibrado** | **9406,50** | 8559,25 | **9,17** / 8,33 | 12 / 12 | **226,75** / 213,00 | 8186,33 → 8199,00 |
| **B. Explorador** | 9747,58 | **9850,08** | 9,50 / **9,58** | 14 / 13 | 234,25 / **252,33** | 10310,33 → 8875,33 |
| **C. Prudente** | 9065,25 | 8978,17 | 8,83 / 8,75 | 12 / 12 | 218,75 / 215,25 | 8532,00 → 9202,67 |
| **D. Valiente** | 10145,42 | **10403,25** | 9,92 / **10,17** | 14 / 14 | 214,67 / **221,33** | 9184,67 → 9171,33 |
| **E. Reactivo** | 8493,08 | 8414,58 | 8,25 / 8,17 | 12 / 12 | 231,25 / **235,33** | 7540,67 → 8917,33 |
| **F. Sin Exp.** | 10116,08 | 9117,33 | 9,83 / 8,83 | 16 / 12 | 268,42 / **269,08** | 9660,00 → 9258,00 |
| **G. Bib. Fija** | — | 8559,25 | — / 8,33 | — / 12 | — / 213,00 | 8186,33 → 8199,00 |

- **Hallazgos clave:**
  - **Invertido respecto a `minimo`:** en Crafter, **`D. Valiente`** (`umbral_miedo=0,85`, `neuroticismo=0,20`) es el claro ganador en ambas ramas y mejora aún más en `ajustes` (**`10 403,25`** de fitness, **`10,17`** logros medios), mientras que `E. Reactivo` es el peor (`8414,58` / `8,17` logros) porque huye demasiado pronto y frena el avance tecnológico.
  - **`B. Explorador`** también sube en `ajustes` tanto en fitness (`9850,08`) como en supervivencia (`234,25` → `252,33` latidos).
  - En cambio, **`A. Equilibrado`** bajó en este protocolo de 4 generaciones respecto a `main` (`9,17` → `8,33` logros), señal de que la interacción entre el hipocampo genérico (`Orientacion` / `ruta`) y los ciclos de Crafter tiene margen de mejora en perfiles medios (precisamente lo que vas a observar cualitativamente).
  - **`G. Bib. Fija`** empata exactamente al decimal con `A. Equilibrado` (`8559,25` / `8,33` logros) tras el ajuste `cd2a8b7` de [`Estudio`](file:///f:/code/IdA/ida/sistemas/s3.py#L174-L348), confirmando que ya no penaliza los logros.

---

### 3.4 Ajedrez (3 semillas × 4 generaciones = 12 partidas/batch, máx. 200 latidos)

| Batch (dificultad) | Fitness `main` | Fitness `ajustes` | Resultado (`V / T / D`) | Latidos medios | G1 → G4 (`ajustes`) |
|---|---:|---:|---|---:|---:|
| **A. Equilibrado (d1)** | 2827,08 | 2827,08 | `11 / 1 / 0` | 27,08 | 2739,33 → 2946,67 |
| **B. Explorador (d1)** | 2716,92 | 2716,92 | `11 / 1 / 0` | 20,67 | 2739,33 → 2910,33 |
| **C. Prudente (d1)** | **3022,17** | **3022,17** | **`12 / 0 / 0`** | 26,75 | 2897,67 → 2981,67 |
| **D. Valiente (d1)** | 2611,00 | 2611,00 | `11 / 1 / 0` | 17,67 | 2538,00 → 2211,00 |
| **E. Reactivo (d1)** | 2911,58 | 2911,58 | `11 / 1 / 0` | 29,08 | 2503,67 → 3262,00 |
| **F. Sin Exp. (d1)** | 2827,08 | 2827,08 | `11 / 1 / 0` | 27,08 | 2739,33 → 2946,67 |
| **A. Equilibrado (d2)** | 1267,67 | 1267,67 | `3 / 6 / 3` | 35,58 | 1878,33 → 1619,67 |

- **Hallazgos clave:**
  - **Invariancia absoluta del 100 %** entre `main` y `feature/ajustes-cognitivos` en todas las 84 partidas por rama.
  - **`C. Prudente`** logra **100 % de victorias (`12/12`)** frente al nivel 1 y el mayor fitness medio (`3022,17`).
  - La experiencia entre partidas (`F. Sin Exp.` vs `A. Equilibrado`) no altera el resultado porque en ajedrez el aprendizaje episódico actual no modela posiciones de tablero, solo refuerza acciones genéricas.

---

## 4. Conclusiones para la Antesala y Próximos Pasos

1. **Perfiles recomendados listos para la antesala:** cada mundo tiene un perfil óptimo distinto y coherente con su ecología:
   - **Mínimo / Archivos:** `Reactivo` (`apertura=0,40, responsabilidad=0,60, neuroticismo=0,85, extraversion=0,30, umbral_miedo=0,35`).
   - **Crafter:** `Valiente` (`apertura=0,60, responsabilidad=0,65, neuroticismo=0,20, extraversion=0,60, umbral_miedo=0,85`).
   - **Ajedrez:** `Prudente` (`apertura=0,30, responsabilidad=0,85, neuroticismo=0,55, extraversion=0,40, umbral_miedo=0,50`).
2. **Estado comparativo de `feature/ajustes-cognitivos` frente a `main`:**
   - **Ajedrez:** invariancia perfecta (`100 %`).
   - **Mínimo / Archivos:** equivalencia práctica con ligera mejora en los mejores perfiles (`E. Reactivo`: `791,87` vs `780,40` en mínimo; `1028,20` vs `1023,33` en archivos).
   - **Crafter:** mejora en los dos perfiles superiores (`D. Valiente`: `10 403` vs `10 145`; `B. Explorador`: `9850` vs `9748`), pero retroceso en `A. Equilibrado` (`8559` vs `9406`) — punto clave a observar cualitativamente en tus pruebas manuales en Crafter.
3. **Mejora técnica recomendada aparte:** ajustar [`calcular_fitness()`](file:///f:/code/IdA/ida/historico.py#L41-L44) en `archivos` para ponderar supervivencia/alimentos sanos y no premiar la ingesta tóxica acelerada.
