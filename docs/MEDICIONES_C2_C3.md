# Mediciones de C2 y C3 (bloque C: S2, S3 y fin de las excepciones)

Encargo en [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), «C2 y C3, en un solo encargo»; tabla en [`C0_CORRESPONDENCIA.md`](C0_CORRESPONDENCIA.md).

- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F` y `... comparar base.json nueva.json`.
- **Versiones:** base = `main` (`b3a6ed6`, bloques A y B); nueva = `feature/bloque-c` (`5fb4e46`, C1 a C3.5).
- **Protocolo** de [`BENCHMARK_PERFILES_MUNDOS.md`](BENCHMARK_PERFILES_MUNDOS.md): N = 10 linajes (semillas 1 a 10), IC 95 % con t de Student, Δ pareado por semilla; mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600. Reloj real. 16/11/2026.

## Resultado frente al criterio

Criterio del autor: hasta el bloque E, una pérdida ligera es aceptable. **Se cumple.**

- Crafter: no inferioridad (límite inferior del Δ de logros entre −0,63 y −0,10); Δ de +0,83 a +1,17 logros, ninguno significativo.
- Archivos: latidos (+94 a +107), fitness (+857 a +895) y nutritivos (+14 a +15) mejoran de forma significativa en los tres perfiles. **Pérdida ligera y significativa:** tóxicos +0,45 a +0,53 por vida; en el control sin experiencia, +1,65 ± 0,97.
- Mínimo: Equilibrado mejora (latidos +160 ± 33, fitness +270 ± 71); setas −0,65 a −2,38 en los tres perfiles. Control sin experiencia: −20 latidos y −72 de fitness, no significativos.

## Tablas completas


### minimo (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 174.28 ± 39.42 | 334.32 ± 34.11 | 160.05 ± 32.64 |
| Equilibrado | fitness | 420.15 ± 83.84 | 689.95 ± 76.72 | 269.80 ± 71.13 |
| Equilibrado | setas | 2.27 ± 0.42 | 1.02 ± 0.06 | -1.25 ± 0.43 |
| Valiente | latidos | 303.35 ± 45.10 | 332.45 ± 31.75 | 29.10 ± 51.33 |
| Valiente | fitness | 599.85 ± 104.44 | 691.58 ± 64.30 | 91.72 ± 106.83 |
| Valiente | setas | 3.40 ± 0.52 | 1.02 ± 0.06 | -2.38 ± 0.55 |
| Reactivo | latidos | 355.52 ± 27.43 | 376.70 ± 19.52 | 21.18 ± 28.00 |
| Reactivo | fitness | 742.52 ± 65.17 | 783.45 ± 45.30 | 40.92 ± 59.96 |
| Reactivo | setas | 1.70 ± 0.18 | 1.05 ± 0.08 | -0.65 ± 0.19 |
| Sin experiencia | latidos | 177.40 ± 33.40 | 157.07 ± 42.90 | -20.32 ± 37.24 |
| Sin experiencia | fitness | 493.40 ± 92.93 | 421.70 ± 106.66 | -71.70 ± 101.84 |
| Sin experiencia | setas | 7.60 ± 0.86 | 8.22 ± 0.60 | 0.62 ± 0.89 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 6971 | 1 | 0 | 3.45 / 3.53 / 2.38 |
| Equilibrado | nueva | 13373 | 0 | 0 | 2.25 / 2.48 / 1.79 |
| Valiente | base | 12134 | 3 | 0 | 3.15 / 3.37 / 2.29 |
| Valiente | nueva | 13298 | 0 | 0 | 2.15 / 2.39 / 1.76 |
| Reactivo | base | 14221 | 0 | 0 | 3.16 / 3.04 / 1.99 |
| Reactivo | nueva | 15068 | 0 | 0 | 2.70 / 2.77 / 1.83 |
| Sin experiencia | base | 7096 | 0 | 0 | 3.02 / 2.20 / 0.94 |
| Sin experiencia | nueva | 6283 | 0 | 0 | 2.06 / 1.53 / 0.58 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 13373 | 399 | 246 | 216 | 2 |
| Valiente | 13298 | 531 | 13 | 4 | 0 |
| Reactivo | 15068 | 281 | 1587 | 1454 | 111 |
| Sin experiencia | 6283 | 135 | 86 | 79 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 23983 | 15963 | 285 |
| huir | 7295 | 3831 | 0 |
| sobresalto | 5775 | 4602 | 0 |
| plantar_cara | 1610 | 1288 | 0 |
| defenderse | 2 | 0 | 0 |

### archivos (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 260.88 ± 28.05 | 360.88 ± 27.78 | 100.00 ± 34.35 |
| Equilibrado | fitness | 924.25 ± 174.38 | 1781.75 ± 259.74 | 857.50 ± 261.69 |
| Equilibrado | nutritivos | 11.65 ± 2.76 | 25.70 ± 3.77 | 14.05 ± 4.37 |
| Equilibrado | toxicos | 1.80 ± 0.36 | 2.25 ± 0.32 | 0.45 ± 0.28 |
| Valiente | latidos | 272.07 ± 22.58 | 366.57 ± 23.20 | 94.50 ± 27.93 |
| Valiente | fitness | 960.40 ± 168.50 | 1855.65 ± 226.75 | 895.25 ± 253.90 |
| Valiente | nutritivos | 11.93 ± 2.82 | 27.10 ± 3.39 | 15.18 ± 4.47 |
| Valiente | toxicos | 1.80 ± 0.31 | 2.33 ± 0.30 | 0.53 ± 0.31 |
| Reactivo | latidos | 257.65 ± 22.84 | 364.15 ± 22.80 | 106.50 ± 33.28 |
| Reactivo | fitness | 904.05 ± 115.09 | 1794.55 ± 250.59 | 890.50 ± 264.18 |
| Reactivo | nutritivos | 11.32 ± 1.95 | 25.88 ± 3.76 | 14.55 ± 4.43 |
| Reactivo | toxicos | 1.77 ± 0.33 | 2.27 ± 0.33 | 0.50 ± 0.27 |
| Sin experiencia | latidos | 139.25 ± 56.48 | 125.42 ± 45.76 | -13.82 ± 31.62 |
| Sin experiencia | fitness | 280.60 ± 239.13 | 366.05 ± 305.17 | 85.45 ± 179.34 |
| Sin experiencia | nutritivos | 9.53 ± 1.83 | 13.65 ± 4.55 | 4.12 ± 3.59 |
| Sin experiencia | toxicos | 9.28 ± 2.00 | 10.93 ± 1.50 | 1.65 ± 0.97 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 10435 | 0 | 1 | 1.95 / 1.68 / 1.72 |
| Equilibrado | nueva | 14435 | 0 | 0 | 1.62 / 1.41 / 1.49 |
| Valiente | base | 10883 | 0 | 1 | 1.92 / 1.70 / 1.72 |
| Valiente | nueva | 14663 | 0 | 0 | 1.57 / 1.39 / 1.47 |
| Reactivo | base | 10306 | 0 | 3 | 2.01 / 1.71 / 1.73 |
| Reactivo | nueva | 14566 | 0 | 0 | 1.64 / 1.40 / 1.49 |
| Sin experiencia | base | 5570 | 0 | 0 | 1.47 / 1.11 / 0.79 |
| Sin experiencia | nueva | 5017 | 0 | 0 | 1.39 / 1.10 / 0.78 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 14435 | 317 | 113 | 99 | 0 |
| Valiente | 14663 | 310 | 107 | 94 | 0 |
| Reactivo | 14566 | 279 | 112 | 97 | 0 |
| Sin experiencia | 5017 | 106 | 36 | 33 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 21483 | 10806 | 340 |
| sobresalto | 1072 | 321 | 0 |
| plantar_cara | 578 | 268 | 0 |
| huir | 125 | 5 | 0 |

### crafter (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 246.57 ± 35.08 | 252.80 ± 19.43 | 6.23 ± 43.94 |
| Equilibrado | fitness | 9392.27 ± 1444.62 | 10398.47 ± 1125.87 | 1006.20 ± 1124.20 |
| Equilibrado | logros | 9.13 ± 1.42 | 10.13 ± 1.13 | 1.00 ± 1.10 |
| Valiente | latidos | 262.17 ± 34.19 | 253.63 ± 52.61 | -8.53 ± 43.88 |
| Valiente | fitness | 10676.20 ± 1019.71 | 11500.83 ± 815.24 | 824.63 ± 1450.42 |
| Valiente | logros | 10.40 ± 1.04 | 11.23 ± 0.80 | 0.83 ± 1.46 |
| Reactivo | latidos | 234.73 ± 26.76 | 242.93 ± 33.14 | 8.20 ± 37.52 |
| Reactivo | fitness | 8812.20 ± 1424.76 | 9986.43 ± 1478.53 | 1174.23 ± 1209.60 |
| Reactivo | logros | 8.57 ± 1.40 | 9.73 ± 1.46 | 1.17 ± 1.19 |
| Sin experiencia | latidos | 262.87 ± 39.63 | 249.57 ± 31.63 | -13.30 ± 45.63 |
| Sin experiencia | fitness | 9675.40 ± 1432.80 | 10561.30 ± 1170.77 | 885.90 ± 1211.56 |
| Sin experiencia | logros | 9.40 ± 1.41 | 10.30 ± 1.16 | 0.90 ± 1.20 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 7397 | 0 | 0 | 2.42 / 2.69 / 1.88 |
| Equilibrado | nueva | 7584 | 0 | 0 | 2.45 / 2.70 / 1.95 |
| Valiente | base | 7865 | 0 | 0 | 2.33 / 2.79 / 1.97 |
| Valiente | nueva | 7609 | 0 | 0 | 2.00 / 2.52 / 1.93 |
| Reactivo | base | 7042 | 0 | 0 | 2.50 / 2.83 / 1.90 |
| Reactivo | nueva | 7288 | 0 | 0 | 2.36 / 2.58 / 1.84 |
| Sin experiencia | base | 7886 | 0 | 0 | 2.49 / 1.75 / 1.49 |
| Sin experiencia | nueva | 7487 | 0 | 0 | 2.23 / 1.63 / 1.45 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 7584 | 100 | 180 | 146 | 57 |
| Valiente | 7609 | 117 | 43 | 32 | 11 |
| Reactivo | 7288 | 92 | 282 | 225 | 76 |
| Sin experiencia | 7487 | 89 | 166 | 128 | 68 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 24897 | 7464 | 552 |
| huir | 4832 | 3667 | 28 |
| sobresalto | 1993 | 1590 | 0 |
| cerrar_distancia | 660 | 568 | 0 |
| defensa_armada | 505 | 451 | 0 |
| quieto_o_huir | 231 | 221 | 0 |
| defenderse | 148 | 138 | 0 |
