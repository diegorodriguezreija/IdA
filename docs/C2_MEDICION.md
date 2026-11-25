# Medición de rendimiento C2: v4 frente a v5 en reposo

- **Fecha:** 25/11/2026
- **Máquina:**
  - CPU: Intel(R) Core(TM) i5-6400 CPU @ 2.70GHz (4 procesadores lógicos)
  - Plan de energía: GUID 381b4222-f694-41f0-9685-ff5bb260df2e (Equilibrado)
  - Sistema operativo: Windows-10-10.0.19045-SP0
  - Python: 3.15.1 (tags/v3.15.1:c37e74c, Oct 21 2026, 06:24:08) [MSC v.1951 64 bit (AMD64)]
- **Árboles y commits:**
  - Base (`v4`, etiqueta `crafter-general-v4`, worktree en `F:\tmp\ida_v4`): commit `eaeadaa`
  - Nueva (`v5`, rama `limpieza/c2-medicion` sobre `main` `25f0344`, en `F:\code\IdA`): commit `f7e78ea`

## Comandos exactos

```powershell
# Crafter (medición y perfilado)
F:\code\IdA\.venv\Scripts\python.exe herramientas\c2_medir.py --base F:\tmp\ida_v4 --nueva F:\code\IdA --salida F:\tmp\c2 --reps 3 --pasos 3000 --perfil

# Comparación de perfiles
F:\code\IdA\.venv\Scripts\python.exe herramientas\comparar_perfiles.py F:\tmp\c2\perfil_base_31.prof F:\tmp\ida_v4 F:\tmp\c2\perfil_nueva_31.prof F:\code\IdA --top 40 --salida F:\tmp\c2\perfiles.md

# Mínimo (ejecuciones)
F:\code\IdA\.venv\Scripts\python.exe herramientas\benchmark.py ejecutar --raiz F:\tmp\ida_v4 --mundo minimo --salida F:\tmp\c2\bench_v4_a.json
F:\code\IdA\.venv\Scripts\python.exe herramientas\benchmark.py ejecutar --raiz F:\code\IdA --mundo minimo --salida F:\tmp\c2\bench_v5_a.json
F:\code\IdA\.venv\Scripts\python.exe herramientas\benchmark.py ejecutar --raiz F:\code\IdA --mundo minimo --salida F:\tmp\c2\bench_v5_b.json
F:\code\IdA\.venv\Scripts\python.exe herramientas\benchmark.py ejecutar --raiz F:\tmp\ida_v4 --mundo minimo --salida F:\tmp\c2\bench_v4_b.json

# Mínimo (comparaciones)
F:\code\IdA\.venv\Scripts\python.exe herramientas\benchmark.py comparar F:\tmp\c2\bench_v4_a.json F:\tmp\c2\bench_v5_a.json
F:\code\IdA\.venv\Scripts\python.exe herramientas\benchmark.py comparar F:\tmp\c2\bench_v4_b.json F:\tmp\c2\bench_v5_b.json
```

## Crafter

### Conducta

- Semilla 31: IDÉNTICA
- Semilla 32: IDÉNTICA
- Global: CONDUCTA: IDÉNTICA

### Tiempos y cocientes

| Semilla | Versión | Mediana ms/paso | Mín | Máx | N |
|---|---|---|---|---|---|
| 31 | base | 14.10 | 13.86 | 14.16 | 3 |
| 31 | nueva | 14.22 | 14.21 | 14.22 | 3 |
| 32 | base | 12.94 | 12.89 | 13.01 | 3 |
| 32 | nueva | 13.54 | 13.29 | 13.55 | 3 |

| Semilla | Cociente nueva/base (medianas) | Cociente (mínimos) |
|---|---|---|
| 31 | 1.009 | 1.025 |
| 32 | 1.046 | 1.031 |

## Perfiles (cProfile, semilla 31)

Total perfilado: base 83.18 s, nueva 86.81 s, Δ +3.62 s (+4.4 %).

### Por zona

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `IdA` | 38.18 | 41.26 | +3.08 | 35820668 | 38928057 |
| `herramientas` | 0.12 | 1.86 | +1.74 | 285684 | 3091794 |
| `python` | 16.32 | 15.21 | -1.11 | 51408556 | 51580715 |
| `entorno:opensimplex` | 18.82 | 18.71 | -0.12 | 2744389 | 2744389 |
| `entorno:crafter` | 8.74 | 8.76 | +0.02 | 2970149 | 2949841 |
| `entorno:pil` | 0.73 | 0.75 | +0.01 | 580540 | 580540 |
| `entorno:numpy` | 0.10 | 0.10 | +0.00 | 201128 | 201128 |
| `entorno:imageio` | 0.10 | 0.10 | -0.00 | 36666 | 36666 |
| `entorno:__editable___laboratorio_ida_0_1_0_finder.py` | 0.00 | 0.00 | +0.00 | 2928 | 2928 |
| `entorno:ruamel` | 0.06 | 0.06 | -0.00 | 93124 | 93124 |

### Ficheros de IdA, por Δ

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `ida/sistemas/proteger.py` | 13.45 | 0.00 | -13.45 | 15310679 | 0 |
| `ida/mundos/crafter/s1/interpretar/recinto.py` | 0.00 | 10.54 | +10.54 | 0 | 11515846 |
| `ida/sistemas/s3.py` | 5.35 | 0.00 | -5.35 | 1549052 | 0 |
| `ida/nucleo/pieza.py` | 0.00 | 4.40 | +4.40 | 0 | 6976562 |
| `ida/nucleo/onda.py` | 0.00 | 4.28 | +4.28 | 0 | 5537401 |
| `ida/core/pieza.py` | 4.05 | 0.00 | -4.05 | 6394291 | 0 |
| `ida/core/onda.py` | 3.54 | 0.00 | -3.54 | 4554935 | 0 |
| `ida/nucleo/arquitectura.py` | 0.00 | 3.48 | +3.48 | 0 | 3114486 |
| `ida/core/arquitectura.py` | 3.12 | 0.00 | -3.12 | 2670172 | 0 |
| `ida/s3/reaccionar/estrategias/perseguir_metas.py` | 0.00 | 2.28 | +2.28 | 0 | 978884 |
| `ida/cuerpos/cuadricula/geometria.py` | 0.00 | 2.27 | +2.27 | 0 | 2564995 |
| `ida/core/memoria.py` | 1.77 | 0.00 | -1.77 | 2448783 | 0 |
| `ida/s3/comun.py` | 0.00 | 1.60 | +1.60 | 0 | 627803 |
| `ida/sistemas/comun.py` | 1.31 | 0.00 | -1.31 | 656960 | 0 |
| `ida/sistemas_comun.py` | 0.00 | 1.30 | +1.30 | 0 | 656973 |
| `ida/mundos/crafter.py` | 1.22 | 0.00 | -1.22 | 469864 | 0 |
| `ida/cuerpos/cuadricula/mapa.py` | 0.00 | 1.21 | +1.21 | 0 | 36577 |
| `ida/mundos/crafter/adaptador.py` | 0.00 | 1.05 | +1.05 | 0 | 297503 |
| `ida/nucleo/memoria.py` | 0.00 | 1.03 | +1.03 | 0 | 1586465 |
| `ida/sistemas/s1.py` | 0.97 | 0.00 | -0.97 | 496671 | 0 |
| `<string>` | 0.00 | 0.87 | +0.87 | 0 | 2428215 |
| `<frozen importlib._bootstrap_external>` | 0.00 | 0.70 | +0.70 | 0 | 183991 |
| `ida/s1/sentir/amenaza.py` | 0.00 | 0.67 | +0.67 | 0 | 290390 |
| `ida/s3/interpretar/requisito.py` | 0.00 | 0.65 | +0.65 | 0 | 374980 |
| `ida/mundos/crafter/s1/sentir/valoracion.py` | 0.00 | 0.61 | +0.61 | 0 | 488439 |
| `ida/sistemas/s2.py` | 0.52 | 0.00 | -0.52 | 100090 | 0 |
| `ida/cuerpos/cuadricula/buscador.py` | 0.00 | 0.46 | +0.46 | 0 | 1207944 |
| `ida/cuerpos/cuadricula/memoria.py` | 0.00 | 0.42 | +0.42 | 0 | 890973 |
| `ida/core/sentidos.py` | 0.40 | 0.00 | -0.40 | 57222 | 0 |
| `ida/core/peligro.py` | 0.33 | 0.00 | -0.33 | 238024 | 0 |
| `ida/s1/interpretar/apetencia.py` | 0.00 | 0.30 | +0.30 | 0 | 137840 |
| `ida/core/latido.py` | 1.59 | 1.29 | -0.30 | 351392 | 361017 |
| `ida/s3/interpretar/creencia.py` | 0.00 | 0.29 | +0.29 | 0 | 23174 |
| `ida/s1/comun.py` | 0.00 | 0.25 | +0.25 | 0 | 104934 |
| `ida/core/mundo.py` | 0.25 | 0.00 | -0.25 | 96163 | 0 |
| `ida/cuerpos/cuadricula/situacion.py` | 0.00 | 0.22 | +0.22 | 0 | 18003 |
| `ida/nucleo/estrategia.py` | 0.00 | 0.21 | +0.21 | 0 | 345040 |
| `ida/core/estrategia.py` | 0.20 | 0.00 | -0.20 | 344936 | 0 |
| `ida/nucleo/mundo.py` | 0.00 | 0.18 | +0.18 | 0 | 86841 |
| `ida/s1/reaccionar/estrategias/alimentarse.py` | 0.00 | 0.17 | +0.17 | 0 | 204211 |

### Funciones, por Δ (primeras 20 filas)

| Clave | tottime base (s) | tottime nueva (s) | Δ (s) | llamadas base | llamadas nueva |
|---|---|---|---|---|---|
| `<python>:__hash__` | 0.62 | 0.00 | -0.62 | 1746099 | 323 |
| `__hash__` | 0.00 | 0.60 | +0.60 | 0 | 1745788 |
| `reactiva` | 1.93 | 2.41 | +0.48 | 134413 | 143413 |
| `<python>:_path_join` | 0.47 | 0.00 | -0.47 | 90225 | 0 |
| `_path_join` | 0.00 | 0.47 | +0.47 | 0 | 90674 |
| `modificar` | 0.11 | 0.57 | +0.46 | 46602 | 293946 |
| `rasgo` | 2.11 | 2.40 | +0.28 | 3225353 | 3644785 |
| `<python>:<method 'get' of 'dict' objects>` | 4.44 | 4.71 | +0.27 | 22302868 | 23889873 |
| `__eq__` | 0.00 | 0.23 | +0.23 | 0 | 604380 |
| `<python>:__eq__` | 0.23 | 0.00 | -0.23 | 604822 | 498 |
| `distancias` | 0.00 | 0.22 | +0.22 | 0 | 5987 |
| `aprender` | 0.05 | 0.27 | +0.22 | 5999 | 170973 |
| `situacion` | 0.00 | 0.20 | +0.20 | 0 | 6000 |
| `_requisitos` | 0.03 | 0.23 | +0.20 | 442 | 152291 |
| `_aprender_mapa` | 0.19 | 0.00 | -0.19 | 3000 | 0 |
| `_distancias` | 0.19 | 0.00 | -0.19 | 5987 | 0 |
| `_peligro_aprendido` | 0.18 | 0.00 | -0.18 | 3000 | 0 |
| `_anotar` | 0.41 | 0.56 | +0.15 | 320262 | 443934 |
| `<python>:find_spec` | 0.14 | 0.00 | -0.14 | 23437 | 0 |
| `_par` | 0.00 | 0.14 | +0.14 | 0 | 168980 |

## Mínimo (benchmark pareado, N = 10 linajes)

### Pasada A (`bench_v4_a.json` vs `bench_v5_a.json`)

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
| Equilibrado | base | 15516 | 0 | 217 | 2.64 / 2.59 / 1.80 | 1.24 |
| Equilibrado | nueva | 15516 | 0 | 217 | 2.64 / 2.59 / 1.80 | 1.27 |
| Valiente | base | 14032 | 0 | 129 | 2.24 / 2.48 / 1.79 | 1.19 |
| Valiente | nueva | 14032 | 0 | 129 | 2.24 / 2.48 / 1.79 | 1.25 |
| Reactivo | base | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 | 1.26 |
| Reactivo | nueva | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 | 1.30 |
| Sin experiencia | base | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 | 0.97 |
| Sin experiencia | nueva | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 | 1.00 |

### Pasada B (`bench_v4_b.json` vs `bench_v5_b.json`)

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
| Equilibrado | base | 15516 | 0 | 217 | 2.64 / 2.59 / 1.80 | 1.23 |
| Equilibrado | nueva | 15516 | 0 | 217 | 2.64 / 2.59 / 1.80 | 1.26 |
| Valiente | base | 14032 | 0 | 129 | 2.24 / 2.48 / 1.79 | 1.19 |
| Valiente | nueva | 14032 | 0 | 129 | 2.24 / 2.48 / 1.79 | 1.22 |
| Reactivo | base | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 | 1.26 |
| Reactivo | nueva | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 | 1.29 |
| Sin experiencia | base | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 | 0.97 |
| Sin experiencia | nueva | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 | 1.00 |
