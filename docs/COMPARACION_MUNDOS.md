# Comparación de mundos: main frente a reorg/componentes

Comparación sistemática entre `main` (`eaeadaa`, etiqueta `crafter-general-v4`) y la reorganización por Componentes (`74e6a6a`, etiqueta `reorg-a8`), previa a la decisión de fusión.

Entorno: `.venv\Scripts\python.exe` en Windows.

---

## 1. Snake: entorno no determinista (no comparable latido a latido)

Snake juega en la web real `playsnake.org` a través del navegador en tiempo real, por lo que **no es determinista**: dos ejecuciones sucesivas sobre la misma versión (`main` frente a `main`) tampoco producen el mismo resultado, y el propio [`BENCHMARK_PERFILES_MUNDOS.md`](BENCHMARK_PERFILES_MUNDOS.md) ya lo excluye por esta razón.

Por tanto, las diferencias de puntuación observadas (por ejemplo, 435 frente a 45 puntos en la semilla 1) no comparan versiones ni reflejan cambios de conducta debidos a la reorganización, sino la variabilidad inherente al entorno de red y navegador en tiempo real. La tabla latido a latido queda descartada como **no comparable**.

Para comparar Snake se requiere una metodología estadística agregada (N partidas de cada versión con `main` frente a `main` como control de ruido); remitimos a [`PENDIENTES.md`](PENDIENTES.md) («Snake»). No se debe ejecutar Snake para pruebas de invariancia determinista.

---

## 2. Mínimo, archivos y ajedrez: conducta latido a latido

> **Nota sobre la invariancia de archivos:** la referencia guardada de invariancia de archivos depende de la plataforma y falla en Linux también con `main` (ver [`PENDIENTES.md`](PENDIENTES.md), punto C5). En el entorno Windows de referencia pasa de forma idéntica. Resuelto en C5 (25/11/2026).

### Comandos ejecutados

En `F:\code\IdA` (`reorg/componentes`, commit `74e6a6a`):

```powershell
.venv\Scripts\python.exe herramientas/invariancia.py
```

Extracción de puntuaciones en ambas copias:

```powershell
& F:\code\IdA\.venv\Scripts\python.exe $env:TEMP\ida_main\herramientas\invariancia.py --referencia --mundos minimo archivos ajedrez
& F:\code\IdA\.venv\Scripts\python.exe $env:TEMP\ida_reorg\herramientas\invariancia.py --referencia --mundos minimo archivos ajedrez
```

### Salida de `herramientas/invariancia.py`

```
minimo: OK
archivos: OK
crafter: OK
ajedrez: OK
```

### Puntuaciones finales

#### Copia `main` (`eaeadaa`)
- `minimo:1`: `{'bayas': 21, 'setas': 1}` (400 latidos)
- `minimo:2`: `{'bayas': 21, 'setas': 1}` (400 latidos)
- `minimo:3`: `{'bayas': 26, 'setas': 1}` (400 latidos)
- `archivos:1`: `{'comido': {'Boletus_edulis': 3, 'Conium_maculatum': 1, 'Vaccinium_myrtillus': 6, 'brote': 15, 'Amanita_phalloides': 1, 'Atropa_belladonna': 1, 'Taraxacum_officinale': 6}, 'nutritivos': 30, 'toxicos': 3}` (400 latidos)
- `archivos:2`: `{'comido': {'brote': 8, 'Amanita_phalloides': 1, 'Atropa_belladonna': 1, 'Vaccinium_myrtillus': 3, 'Conium_maculatum': 1}, 'nutritivos': 11, 'toxicos': 3}` (240 latidos)
- `archivos:3`: `{'comido': {'Atropa_belladonna': 1, 'Boletus_edulis': 2, 'Taraxacum_officinale': 1, 'Amanita_phalloides': 1, 'Conium_maculatum': 1, 'Vaccinium_myrtillus': 3, 'brote': 3}, 'nutritivos': 9, 'toxicos': 3}` (218 latidos)
- `ajedrez:1`: `{'resultado': 'VICTORIA', 'jugadas': 65, 'material': [23.3, 3.2]}` (65 latidos)
- `ajedrez:2`: `{'resultado': 'DERROTA', 'jugadas': 36, 'material': [5.0, 11.3]}` (36 latidos)
- `ajedrez:3`: `{'resultado': 'VICTORIA', 'jugadas': 64, 'material': [22.0, 1.0]}` (64 latidos)

#### Copia `reorg` (`74e6a6a`)
- `minimo:1`: `{'bayas': 21, 'setas': 1}` (400 latidos)
- `minimo:2`: `{'bayas': 21, 'setas': 1}` (400 latidos)
- `minimo:3`: `{'bayas': 26, 'setas': 1}` (400 latidos)
- `archivos:1`: `{'comido': {'Boletus_edulis': 3, 'Conium_maculatum': 1, 'Vaccinium_myrtillus': 6, 'brote': 15, 'Amanita_phalloides': 1, 'Atropa_belladonna': 1, 'Taraxacum_officinale': 6}, 'nutritivos': 30, 'toxicos': 3}` (400 latidos)
- `archivos:2`: `{'comido': {'brote': 8, 'Amanita_phalloides': 1, 'Atropa_belladonna': 1, 'Vaccinium_myrtillus': 3, 'Conium_maculatum': 1}, 'nutritivos': 11, 'toxicos': 3}` (240 latidos)
- `archivos:3`: `{'comido': {'Atropa_belladonna': 1, 'Boletus_edulis': 2, 'Taraxacum_officinale': 1, 'Amanita_phalloides': 1, 'Conium_maculatum': 1, 'Vaccinium_myrtillus': 3, 'brote': 3}, 'nutritivos': 9, 'toxicos': 3}` (218 latidos)
- `ajedrez:1`: `{'resultado': 'VICTORIA', 'jugadas': 65, 'material': [23.3, 3.2]}` (65 latidos)
- `ajedrez:2`: `{'resultado': 'DERROTA', 'jugadas': 36, 'material': [5.0, 11.3]}` (36 latidos)
- `ajedrez:3`: `{'resultado': 'VICTORIA', 'jugadas': 64, 'material': [22.0, 1.0]}` (64 latidos)

---

## 3. Mínimo y archivos: benchmark de perfiles (reloj real, N = 10)

Orden alternado de ejecuciones: `main`, `reorg`, `reorg`, `main`.

### Comandos ejecutados y duraciones

1. Mínimo Main (duración: 77.70 s):
   ```powershell
   & F:\code\IdA\.venv\Scripts\python.exe F:\code\IdA\herramientas\benchmark.py ejecutar --raiz $env:TEMP\ida_main --mundo minimo --salida $env:TEMP\bench_main_minimo.json
   ```
2. Mínimo Reorg (duración: 116.20 s):
   ```powershell
   & F:\code\IdA\.venv\Scripts\python.exe F:\code\IdA\herramientas\benchmark.py ejecutar --raiz $env:TEMP\ida_reorg --mundo minimo --salida $env:TEMP\bench_reorg_minimo.json
   ```
3. Archivos Reorg (duración: 267.58 s):
   ```powershell
   & F:\code\IdA\.venv\Scripts\python.exe F:\code\IdA\herramientas\benchmark.py ejecutar --raiz $env:TEMP\ida_reorg --mundo archivos --salida $env:TEMP\bench_reorg_archivos.json
   ```
4. Archivos Main (duración: 258.32 s):
   ```powershell
   & F:\code\IdA\.venv\Scripts\python.exe F:\code\IdA\herramientas\benchmark.py ejecutar --raiz $env:TEMP\ida_main --mundo archivos --salida $env:TEMP\bench_main_archivos.json
   ```

Comparaciones:
```powershell
& F:\code\IdA\.venv\Scripts\python.exe F:\code\IdA\herramientas\benchmark.py comparar $env:TEMP\bench_main_minimo.json $env:TEMP\bench_reorg_minimo.json
& F:\code\IdA\.venv\Scripts\python.exe F:\code\IdA\herramientas\benchmark.py comparar $env:TEMP\bench_main_archivos.json $env:TEMP\bench_reorg_archivos.json
```

### Salida completa de `comparar` para Mínimo

```markdown
### minimo (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 387.90 ± 15.52 | 387.90 ± 15.52 | 0.00 ± 0.00 |
| Equilibrado | fitness | 786.90 ± 45.71 | 786.90 ± 45.71 | 0.00 ± 0.00 |
| Equilibrado | setas | 1.00 ± 0.08 | 1.00 ± 0.08 | 0.00 ± 0.00 |
| Valiente | latidos | 350.80 ± 47.06 | 350.80 ± 47.06 | 0.00 ± 0.00 |
| Valiente | fitness | 761.92 ± 104.56 | 761.92 ± 104.56 | 0.00 ± 0.00 |
| Valiente | setas | 1.02 ± 0.06 | 1.02 ± 0.06 | 0.00 ± 0.00 |
| Reactivo | latidos | 383.82 ± 13.29 | 383.82 ± 13.29 | 0.00 ± 0.00 |
| Reactivo | fitness | 785.45 ± 52.08 | 785.45 ± 52.08 | 0.00 ± 0.00 |
| Reactivo | setas | 1.02 ± 0.06 | 1.02 ± 0.06 | 0.00 ± 0.00 |
| Sin experiencia | latidos | 157.07 ± 42.90 | 157.07 ± 42.90 | 0.00 ± 0.00 |
| Sin experiencia | fitness | 421.70 ± 106.66 | 421.70 ± 106.66 | 0.00 ± 0.00 |
| Sin experiencia | setas | 8.22 ± 0.60 | 8.22 ± 0.60 | 0.00 ± 0.00 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido | ms por latido |
|---|---|---|---|---|---|---|
| Equilibrado | base | 15516 | 0 | 217 | 2.64 / 2.59 / 1.80 | 1.37 |
| Equilibrado | nueva | 15516 | 0 | 217 | 2.64 / 2.59 / 1.80 | 1.35 |
| Valiente | base | 14032 | 0 | 129 | 2.24 / 2.48 / 1.79 | 1.27 |
| Valiente | nueva | 14032 | 1 | 129 | 2.24 / 2.48 / 1.79 | 2.35 |
| Reactivo | base | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 | 1.34 |
| Reactivo | nueva | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 | 2.18 |
| Sin experiencia | base | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 | 1.02 |
| Sin experiencia | nueva | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 | 1.60 |

| Grupo | Versión | S3 sin recursos con peligro | S3 sin recursos en calma |
|---|---|---|---|
| Equilibrado | base | 2.3 % de 7453 | 0.6 % de 7341 |
| Equilibrado | nueva | 2.3 % de 7453 | 0.6 % de 7341 |
| Valiente | base | 2.0 % de 4152 | 0.5 % de 9308 |
| Valiente | nueva | 2.0 % de 4152 | 0.5 % de 9308 |
| Reactivo | base | 1.8 % de 7047 | 0.6 % de 7630 |
| Reactivo | nueva | 1.8 % de 7047 | 0.6 % de 7630 |
| Sin experiencia | base | 1.1 % de 2078 | 0.3 % de 4141 |
| Sin experiencia | nueva | 1.1 % de 2078 | 0.3 % de 4141 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | hambre | 4 | 4 |
| Equilibrado | lobo | 2 | 2 |
| Equilibrado | vive | 34 | 34 |
| Valiente | hambre | 2 | 2 |
| Valiente | lobo | 10 | 10 |
| Valiente | vive | 28 | 28 |
| Reactivo | hambre | 1 | 1 |
| Reactivo | lobo | 6 | 6 |
| Reactivo | vive | 33 | 33 |
| Sin experiencia | desgaste | 18 | 18 |
| Sin experiencia | lobo | 21 | 21 |
| Sin experiencia | vive | 1 | 1 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 15516 | 363 | 861 | 769 | 81 |
| Valiente | 14032 | 654 | 160 | 141 | 8 |
| Reactivo | 15353 | 332 | 1609 | 1518 | 95 |
| Sin experiencia | 6283 | 135 | 86 | 79 | 0 |

| Estrategia (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| estudiar | 33249 | 0 | 0 |
| explorar | 26258 | 11757 | 380 |
| alimentarse | 26048 | 15689 | 281 |
| refugiarse | 13268 | 4061 | 5 |
| huir | 9640 | 5233 | 0 |
| sobresalto | 8121 | 6288 | 0 |
| plantar_cara | 1456 | 1247 | 0 |
| recordar_comida | 67 | 36 | 0 |
| defenderse | 2 | 0 | 0 |
```

### Salida completa de `comparar` para Archivos

```markdown
### archivos (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 360.52 ± 27.78 | 360.52 ± 27.78 | 0.00 ± 0.00 |
| Equilibrado | fitness | 1788.55 ± 263.63 | 1788.55 ± 263.63 | 0.00 ± 0.00 |
| Equilibrado | nutritivos | 25.85 ± 3.86 | 25.85 ± 3.86 | 0.00 ± 0.00 |
| Equilibrado | toxicos | 2.25 ± 0.32 | 2.25 ± 0.32 | 0.00 ± 0.00 |
| Valiente | latidos | 364.07 ± 22.20 | 364.07 ± 22.20 | 0.00 ± 0.00 |
| Valiente | fitness | 1851.90 ± 241.39 | 1851.90 ± 241.39 | 0.00 ± 0.00 |
| Valiente | nutritivos | 27.18 ± 3.71 | 27.18 ± 3.71 | 0.00 ± 0.00 |
| Valiente | toxicos | 2.35 ± 0.31 | 2.35 ± 0.31 | 0.00 ± 0.00 |
| Reactivo | latidos | 364.85 ± 22.91 | 364.85 ± 22.91 | 0.00 ± 0.00 |
| Reactivo | fitness | 1824.70 ± 241.19 | 1824.70 ± 241.19 | 0.00 ± 0.00 |
| Reactivo | nutritivos | 26.45 ± 3.55 | 26.45 ± 3.55 | 0.00 ± 0.00 |
| Reactivo | toxicos | 2.27 ± 0.33 | 2.27 ± 0.33 | 0.00 ± 0.00 |
| Sin experiencia | latidos | 125.42 ± 45.76 | 125.42 ± 45.76 | 0.00 ± 0.00 |
| Sin experiencia | fitness | 366.05 ± 305.17 | 366.05 ± 305.17 | 0.00 ± 0.00 |
| Sin experiencia | nutritivos | 13.65 ± 4.55 | 13.65 ± 4.55 | 0.00 ± 0.00 |
| Sin experiencia | toxicos | 10.93 ± 1.50 | 10.93 ± 1.50 | 0.00 ± 0.00 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido | ms por latido |
|---|---|---|---|---|---|---|
| Equilibrado | base | 14421 | 0 | 223 | 1.63 / 1.42 / 1.45 | 2.51 |
| Equilibrado | nueva | 14421 | 0 | 223 | 1.63 / 1.42 / 1.45 | 2.62 |
| Valiente | base | 14563 | 0 | 214 | 1.59 / 1.40 / 1.44 | 2.48 |
| Valiente | nueva | 14563 | 0 | 214 | 1.59 / 1.40 / 1.44 | 2.61 |
| Reactivo | base | 14594 | 0 | 214 | 1.61 / 1.39 / 1.45 | 2.48 |
| Reactivo | nueva | 14594 | 0 | 214 | 1.61 / 1.39 / 1.45 | 2.58 |
| Sin experiencia | base | 5017 | 0 | 20 | 1.39 / 1.10 / 0.78 | 2.42 |
| Sin experiencia | nueva | 5017 | 0 | 20 | 1.39 / 1.10 / 0.78 | 2.49 |

| Grupo | Versión | S3 sin recursos con peligro | S3 sin recursos en calma |
|---|---|---|---|
| Equilibrado | base | 2.2 % de 6114 | 0.8 % de 7467 |
| Equilibrado | nueva | 2.2 % de 6114 | 0.8 % de 7467 |
| Valiente | base | 2.3 % de 6092 | 0.7 % de 7646 |
| Valiente | nueva | 2.3 % de 6092 | 0.7 % de 7646 |
| Reactivo | base | 2.1 % de 6050 | 0.7 % de 7688 |
| Reactivo | nueva | 2.1 % de 6050 | 0.7 % de 7688 |
| Sin experiencia | base | 0.5 % de 1776 | 0.4 % de 3093 |
| Sin experiencia | nueva | 0.5 % de 1776 | 0.4 % de 3093 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | depredador | 5 | 5 |
| Equilibrado | hambre | 12 | 12 |
| Equilibrado | vive | 23 | 23 |
| Valiente | depredador | 1 | 1 |
| Valiente | hambre | 12 | 12 |
| Valiente | vive | 27 | 27 |
| Reactivo | depredador | 3 | 3 |
| Reactivo | hambre | 12 | 12 |
| Reactivo | vive | 25 | 25 |
| Sin experiencia | depredador | 3 | 3 |
| Sin experiencia | desgaste | 27 | 27 |
| Sin experiencia | hambre | 6 | 6 |
| Sin experiencia | vive | 4 | 4 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 14421 | 318 | 129 | 115 | 0 |
| Valiente | 14563 | 293 | 106 | 93 | 0 |
| Reactivo | 14594 | 280 | 113 | 99 | 0 |
| Sin experiencia | 5017 | 106 | 36 | 33 | 0 |

| Estrategia (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 21302 | 10929 | 332 |
| explorar | 17765 | 7460 | 31 |
| estudiar | 16690 | 0 | 0 |
| refugiarse | 4343 | 1874 | 10 |
| recordar_comida | 4257 | 3002 | 20 |
| buscar_en_otra_carpeta | 2188 | 1461 | 0 |
| sobresalto | 1120 | 350 | 0 |
| plantar_cara | 594 | 264 | 0 |
| huir | 157 | 7 | 0 |
```

---

## 4. Crafter: referencia de evaluación pareada

- **Origen:** Rama `reorg/medicion-a7b`, commit `9b3bd25edc07c42138408c37ecf44d1cddea83bf`.
- **Ficheros comparados:** `datos/evaluacion/reorg_31.json` y `datos/evaluacion/reorg_32.json` frente a `datos/evaluacion/mapa_31.json` y `datos/evaluacion/mapa_32.json`.
- **Crafter Score:** 15,86 % (semilla base 31) y 17,34 % (semilla base 32) en ambas versiones.
- **Episodios:** 737 episodios pareados idénticos (377 en semilla 31 y 360 en semilla 32).
- **Diferencia pareada conjunta:** Δ Score = 0,00 pp, IC 95 % pareado [0,00, 0,00] pp. Diferencia en cada logro = 0,00 pp, IC 95 % [0,00, 0,00] pp.
- **Medición final v5:** Commit `76ee97a` (`datos/evaluacion/v5_31.json` y `datos/evaluacion/v5_32.json`): idéntico a mapa_31/32 en toda la conducta (Score, episodios, causas de muerte, logros paso a paso). Rendimiento: 15,24 ms/paso (semilla 31) y 16,66 ms/paso (semilla 32) (frente a 12,63 y 12,52 ms/paso en mapa).
