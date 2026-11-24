# Mediciones de C1 (bloque C: infraestructura del bucle y S1)

Encargo en [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), parte C1; correspondencia y decisiones en [`C0_CORRESPONDENCIA.md`](C0_CORRESPONDENCIA.md).

- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F` y `... comparar base.json nueva.json`.
- **Versiones:** base = `main` (`b3a6ed6`, bloques A y B); nueva = `feature/bloque-c` (`434742a`, C1.1 a C1.6).
- **Protocolo** de [`BENCHMARK_PERFILES_MUNDOS.md`](../BENCHMARK_PERFILES_MUNDOS.md): N = 10 linajes (semillas 1 a 10, directorio limpio); mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600; perfiles Equilibrado, Valiente y Reactivo y control sin experiencia; IC 95 % con t(0,975; 9) = 2,262; Δ pareado por semilla. Reloj real. 16/11/2026, Windows 10, Python 3.15.1.

## Resultado frente al criterio de paso

**No cumple.** Crafter cumple la no inferioridad (margen −1 logro), pero hay pérdidas significativas en el mundo mínimo y una en archivos.

## Tablas completas


### minimo (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 174.28 ± 39.42 | 261.48 ± 47.99 | 87.20 ± 53.29 |
| Equilibrado | fitness | 420.15 ± 83.84 | 623.85 ± 136.29 | 203.70 ± 136.71 |
| Equilibrado | setas | 2.27 ± 0.42 | 5.58 ± 0.74 | 3.30 ± 0.83 |
| Valiente | latidos | 312.77 ± 40.31 | 252.07 ± 38.47 | -60.70 ± 54.50 |
| Valiente | fitness | 608.02 ± 95.86 | 602.58 ± 110.21 | -5.45 ± 135.56 |
| Valiente | setas | 3.45 ± 0.53 | 5.40 ± 0.86 | 1.95 ± 0.82 |
| Reactivo | latidos | 355.52 ± 27.43 | 329.27 ± 44.70 | -26.25 ± 50.07 |
| Reactivo | fitness | 742.52 ± 65.17 | 693.90 ± 127.17 | -48.62 ± 128.91 |
| Reactivo | setas | 1.70 ± 0.18 | 2.52 ± 0.45 | 0.82 ± 0.48 |
| Sin experiencia | latidos | 177.40 ± 33.40 | 162.30 ± 35.06 | -15.10 ± 29.30 |
| Sin experiencia | fitness | 493.40 ± 92.93 | 450.43 ± 89.71 | -42.98 ± 85.35 |
| Sin experiencia | setas | 7.60 ± 0.86 | 7.62 ± 0.95 | 0.03 ± 0.69 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 6971 | 0 | 0 | 3.45 / 3.53 / 2.38 |
| Equilibrado | nueva | 10459 | 1 | 0 | 2.28 / 2.84 / 2.01 |
| Valiente | base | 12511 | 0 | 0 | 3.20 / 3.37 / 2.30 |
| Valiente | nueva | 10083 | 0 | 0 | 2.18 / 2.75 / 2.00 |
| Reactivo | base | 14221 | 0 | 0 | 3.16 / 3.04 / 1.99 |
| Reactivo | nueva | 13171 | 0 | 0 | 2.80 / 2.89 / 1.96 |
| Sin experiencia | base | 7096 | 0 | 0 | 3.02 / 2.20 / 0.94 |
| Sin experiencia | nueva | 6492 | 0 | 0 | 2.19 / 1.65 / 0.62 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 10459 | 17 | 134 | 51 | 1311 |
| Valiente | 10083 | 9 | 132 | 43 | 1243 |
| Reactivo | 13171 | 88 | 1002 | 412 | 1245 |
| Sin experiencia | 6492 | 3 | 79 | 27 | 663 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| acercarse_a_la_comida | 12056 | 7661 | 38 |
| comer_al_alcance | 7466 | 3329 | 0 |
| huir | 7235 | 4733 | 0 |
| sobresalto | 4031 | 3342 | 0 |
| plantar_cara | 1022 | 980 | 0 |
| defenderse | 2 | 1 | 0 |

### archivos (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 260.88 ± 28.05 | 279.40 ± 18.49 | 18.52 ± 24.28 |
| Equilibrado | fitness | 924.25 ± 174.38 | 1115.20 ± 149.50 | 190.95 ± 203.57 |
| Equilibrado | nutritivos | 11.65 ± 2.76 | 15.32 ± 2.08 | 3.67 ± 3.46 |
| Equilibrado | toxicos | 1.80 ± 0.36 | 2.10 ± 0.38 | 0.30 ± 0.37 |
| Valiente | latidos | 272.07 ± 22.58 | 289.62 ± 16.30 | 17.55 ± 17.23 |
| Valiente | fitness | 960.40 ± 168.50 | 1130.50 ± 159.31 | 170.10 ± 170.12 |
| Valiente | nutritivos | 11.93 ± 2.82 | 16.12 ± 2.12 | 4.20 ± 2.89 |
| Valiente | toxicos | 1.80 ± 0.31 | 2.55 ± 0.69 | 0.75 ± 0.61 |
| Reactivo | latidos | 257.65 ± 22.84 | 275.68 ± 23.77 | 18.02 ± 17.42 |
| Reactivo | fitness | 904.05 ± 115.09 | 1096.85 ± 181.39 | 192.80 ± 155.47 |
| Reactivo | nutritivos | 11.32 ± 1.95 | 15.18 ± 2.50 | 3.85 ± 2.98 |
| Reactivo | toxicos | 1.77 ± 0.33 | 2.15 ± 0.31 | 0.38 ± 0.40 |
| Sin experiencia | latidos | 139.25 ± 56.48 | 142.40 ± 48.50 | 3.15 ± 36.01 |
| Sin experiencia | fitness | 280.60 ± 239.13 | 376.05 ± 281.31 | 95.45 ± 151.81 |
| Sin experiencia | nutritivos | 9.53 ± 1.83 | 13.25 ± 4.20 | 3.73 ± 3.32 |
| Sin experiencia | toxicos | 9.28 ± 2.00 | 10.20 ± 1.47 | 0.93 ± 1.11 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 10435 | 0 | 1 | 1.95 / 1.68 / 1.72 |
| Equilibrado | nueva | 11176 | 0 | 1 | 1.63 / 1.51 / 1.62 |
| Valiente | base | 10883 | 0 | 1 | 1.92 / 1.70 / 1.72 |
| Valiente | nueva | 11585 | 0 | 0 | 1.57 / 1.46 / 1.58 |
| Reactivo | base | 10306 | 0 | 3 | 2.01 / 1.71 / 1.73 |
| Reactivo | nueva | 11027 | 0 | 1 | 1.66 / 1.51 / 1.60 |
| Sin experiencia | base | 5570 | 0 | 0 | 1.47 / 1.11 / 0.79 |
| Sin experiencia | nueva | 5696 | 0 | 0 | 1.25 / 0.95 / 0.68 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 11176 | 106 | 139 | 78 | 487 |
| Valiente | 11585 | 80 | 91 | 47 | 462 |
| Reactivo | 11027 | 55 | 214 | 150 | 514 |
| Sin experiencia | 5696 | 7 | 50 | 43 | 167 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| acercarse_a_la_comida | 17083 | 8250 | 196 |
| comer_al_alcance | 5796 | 3078 | 0 |
| sobresalto | 1436 | 648 | 0 |
| plantar_cara | 664 | 160 | 0 |
| huir | 166 | 1 | 0 |

### crafter (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 246.57 ± 35.08 | 274.73 ± 35.26 | 28.17 ± 50.80 |
| Equilibrado | fitness | 9392.27 ± 1444.62 | 10721.07 ± 1194.33 | 1328.80 ± 1421.59 |
| Equilibrado | logros | 9.13 ± 1.42 | 10.43 ± 1.20 | 1.30 ± 1.40 |
| Valiente | latidos | 260.37 ± 33.50 | 245.50 ± 51.02 | -14.87 ± 55.27 |
| Valiente | fitness | 10674.37 ± 1021.12 | 11426.33 ± 1148.69 | 751.97 ± 1575.57 |
| Valiente | logros | 10.40 ± 1.04 | 11.17 ± 1.13 | 0.77 ± 1.59 |
| Reactivo | latidos | 234.73 ± 26.76 | 277.23 ± 58.15 | 42.50 ± 71.49 |
| Reactivo | fitness | 8812.20 ± 1424.76 | 10489.20 ± 1243.44 | 1677.00 ± 1334.36 |
| Reactivo | logros | 8.57 ± 1.40 | 10.20 ± 1.23 | 1.63 ± 1.29 |
| Sin experiencia | latidos | 262.87 ± 39.63 | 279.60 ± 32.87 | 16.73 ± 52.87 |
| Sin experiencia | fitness | 9675.40 ± 1432.80 | 11026.00 ± 1184.12 | 1350.60 ± 1435.51 |
| Sin experiencia | logros | 9.40 ± 1.41 | 10.73 ± 1.17 | 1.33 ± 1.42 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 7397 | 0 | 0 | 2.42 / 2.69 / 1.88 |
| Equilibrado | nueva | 8242 | 0 | 0 | 2.51 / 2.71 / 2.04 |
| Valiente | base | 7811 | 1 | 0 | 2.29 / 2.76 / 1.96 |
| Valiente | nueva | 7365 | 0 | 0 | 2.14 / 2.60 / 1.92 |
| Reactivo | base | 7042 | 0 | 0 | 2.50 / 2.83 / 1.90 |
| Reactivo | nueva | 8317 | 0 | 0 | 2.74 / 3.09 / 2.10 |
| Sin experiencia | base | 7886 | 0 | 0 | 2.49 / 1.75 / 1.49 |
| Sin experiencia | nueva | 8388 | 0 | 0 | 2.51 / 1.78 / 1.52 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 8242 | 72 | 215 | 80 | 291 |
| Valiente | 7365 | 68 | 100 | 37 | 233 |
| Reactivo | 8317 | 138 | 255 | 56 | 340 |
| Sin experiencia | 8388 | 69 | 201 | 90 | 453 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| acercarse_a_la_comida | 28189 | 7937 | 287 |
| huir | 5996 | 4794 | 25 |
| comer_al_alcance | 2697 | 900 | 0 |
| sobresalto | 2291 | 1739 | 0 |
| cerrar_distancia | 592 | 499 | 0 |
| quieto_o_huir | 501 | 497 | 3 |
| defensa_armada | 449 | 412 | 0 |
| defenderse | 177 | 153 | 0 |

## Análisis de la causa (sin ajustar nada)

**Diagnóstico:** mundo mínimo, perfil Valiente, una vida por semilla 1 a 10 (400 latidos), `main` frente a la rama (script en el scratchpad de la sesión, no publicado).

| | `main` | rama |
|---|---|---|
| Latidos por vida (media) | 282,8 | 244,5 |
| Setas comidas | 43 | 67 |
| … con otro candidato de S1 en ese latido | 17 | **0** |
| … sin ningún otro candidato en el Tribunal | 24 | **48** |
| … con la acción frenada por S3 | 23 | 47 |
| … con valor de S2 negativo | 33 | 57 |
| Muertes | 8 lobo, 2 viven | 8 lobo, 2 viven |

**Causa principal (verificada):** con una estrategia por impulso, S1 ofrece **una sola acción** por necesidad. Antes, S1 proponía a la vez comer lo que tenía al alcance *y* acercarse a la comida, así que cuando S3 frenaba la seta (lo que se sabe que no nutre) o S2 la valoraba mal, el Tribunal elegía otra opción. Ahora el freno de S3 y el valor de S2 bajan la acción, pero **no hay alternativa** y la seta gana igual: 47 de las 67 setas se comieron frenadas por S3. Es el riesgo 4 del C0 («no comas esto»): los frenos por acción no sustituyen a que la estrategia elija otro objeto o se abstenga.

**Causas probables (no verificadas):**
- Valiente vive menos en el mínimo porque las setas bajan la vitalidad y, por debajo de 30, `plantar_cara` deja de ser elegible frente al lobo (las muertes son por el lobo en las dos versiones).
- El aumento de tóxicos de Valiente en archivos sigue el mismo mecanismo con el freno de `Prudencia`.
- El reflejo por cambio brusco hace huir a Valiente por debajo de su umbral de miedo (0,85): 132 reflejos en el mínimo.

**Lo que mejora:** Crafter (+0,77 a +1,63 logros; Reactivo, significativo), archivos (fitness +170 a +193 y nutritivos +3,7 a +4,2, significativos) y el mínimo con Equilibrado (+87 latidos).

---

## Segunda medición, tras las decisiones del autor sobre C1

- **Versiones:** base = `main` (`b3a6ed6`); nueva = `feature/bloque-c` (`8ced7d6`): alimentación como una estrategia con fases y elección de objeto por `Valor` y lo demostrado, histéresis 0,2, reflejo escalado con `umbral_miedo`, `seguir_en_movimiento`, mérito por feedback y plus que se apaga con el progreso.
- **Protocolo:** el mismo (N = 10, IC 95 %, pareado, reloj real). 16/11/2026. Las cifras de la base varían un poco respecto a la primera medición (p. ej., Crafter Equilibrado 9,17 frente a 9,13) porque la guillotina por plazo mira el reloj real.

### Resultado frente al criterio

- **Crafter:** no inferioridad cumplida en los cuatro grupos (límite inferior del Δ de logros: Equilibrado −0,16, Valiente −0,67, Reactivo −0,45, Sin experiencia +0,01). Δ positivo en todos; ninguno significativo.
- **Mínimo:** mejoras significativas en latidos para Equilibrado (+172,5 ± 43,4) y Reactivo (+31,1 ± 28,6), y menos setas en los tres perfiles (−0,65 a −2,42). Valiente +17,2 ± 42,7 (no significativo). Sin experiencia −16,4 ± 31,3 latidos (no significativo).
- **Archivos:** mejoras significativas en latidos (+32 a +47), fitness (+322 a +405) y nutritivos (+6,0 a +7,0) en los tres perfiles. **Pérdida ligera y significativa:** tóxicos +0,33 a +0,40 por vida en los tres perfiles.

### Tablas completas


### minimo (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 173.30 ± 39.70 | 345.77 ± 27.90 | 172.47 ± 43.43 |
| Equilibrado | fitness | 420.55 ± 83.89 | 722.90 ± 89.21 | 302.35 ± 109.75 |
| Equilibrado | setas | 2.25 ± 0.40 | 1.02 ± 0.06 | -1.23 ± 0.42 |
| Valiente | latidos | 312.77 ± 40.31 | 330.00 ± 21.86 | 17.23 ± 42.71 |
| Valiente | fitness | 608.02 ± 95.86 | 691.62 ± 61.76 | 83.60 ± 125.47 |
| Valiente | setas | 3.45 ± 0.53 | 1.02 ± 0.06 | -2.42 ± 0.55 |
| Reactivo | latidos | 355.52 ± 27.43 | 386.57 ± 9.69 | 31.05 ± 28.57 |
| Reactivo | fitness | 740.02 ± 63.56 | 806.83 ± 31.95 | 66.80 ± 76.01 |
| Reactivo | setas | 1.70 ± 0.18 | 1.05 ± 0.08 | -0.65 ± 0.19 |
| Sin experiencia | latidos | 177.40 ± 33.40 | 160.97 ± 36.72 | -16.43 ± 31.25 |
| Sin experiencia | fitness | 493.40 ± 92.93 | 447.98 ± 96.70 | -45.42 ± 93.12 |
| Sin experiencia | setas | 7.60 ± 0.86 | 7.60 ± 0.95 | 0.00 ± 0.73 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 6932 | 1 | 0 | 3.46 / 3.54 / 2.39 |
| Equilibrado | nueva | 13831 | 0 | 0 | 2.28 / 2.55 / 1.80 |
| Valiente | base | 12511 | 0 | 0 | 3.20 / 3.37 / 2.30 |
| Valiente | nueva | 13200 | 0 | 0 | 2.18 / 2.39 / 1.75 |
| Reactivo | base | 14221 | 4 | 0 | 3.16 / 3.05 / 1.99 |
| Reactivo | nueva | 15463 | 0 | 0 | 2.72 / 2.78 / 1.84 |
| Sin experiencia | base | 7096 | 1 | 0 | 3.02 / 2.20 / 0.94 |
| Sin experiencia | nueva | 6439 | 0 | 0 | 2.18 / 1.64 / 0.62 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 13831 | 291 | 260 | 133 | 5 |
| Valiente | 13200 | 753 | 20 | 10 | 0 |
| Reactivo | 15463 | 75 | 1687 | 803 | 111 |
| Sin experiencia | 6439 | 3 | 112 | 45 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 24908 | 16703 | 266 |
| huir | 7736 | 3998 | 0 |
| sobresalto | 6215 | 5014 | 0 |
| plantar_cara | 1648 | 1290 | 0 |
| defenderse | 2 | 1 | 0 |

### archivos (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 260.88 ± 28.05 | 307.60 ± 22.94 | 46.73 ± 23.91 |
| Equilibrado | fitness | 924.25 ± 174.38 | 1328.95 ± 165.90 | 404.70 ± 154.50 |
| Equilibrado | nutritivos | 11.65 ± 2.76 | 18.62 ± 2.43 | 6.97 ± 2.87 |
| Equilibrado | toxicos | 1.80 ± 0.36 | 2.17 ± 0.27 | 0.38 ± 0.32 |
| Valiente | latidos | 272.07 ± 22.58 | 304.07 ± 26.34 | 32.00 ± 27.64 |
| Valiente | fitness | 960.40 ± 168.50 | 1281.90 ± 181.09 | 321.50 ± 178.24 |
| Valiente | nutritivos | 11.93 ± 2.82 | 17.88 ± 2.62 | 5.95 ± 3.04 |
| Valiente | toxicos | 1.80 ± 0.31 | 2.20 ± 0.40 | 0.40 ± 0.31 |
| Reactivo | latidos | 257.65 ± 22.84 | 297.88 ± 25.90 | 40.23 ± 23.32 |
| Reactivo | fitness | 904.05 ± 115.09 | 1287.00 ± 204.74 | 382.95 ± 205.61 |
| Reactivo | nutritivos | 11.32 ± 1.95 | 18.02 ± 3.01 | 6.70 ± 3.58 |
| Reactivo | toxicos | 1.77 ± 0.33 | 2.10 ± 0.38 | 0.33 ± 0.22 |
| Sin experiencia | latidos | 139.25 ± 56.48 | 142.70 ± 49.85 | 3.45 ± 38.33 |
| Sin experiencia | fitness | 280.60 ± 239.13 | 379.85 ± 285.77 | 99.25 ± 160.16 |
| Sin experiencia | nutritivos | 9.53 ± 1.83 | 12.93 ± 4.04 | 3.40 ± 3.13 |
| Sin experiencia | toxicos | 9.28 ± 2.00 | 10.03 ± 1.46 | 0.75 ± 0.94 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 10435 | 1 | 1 | 1.95 / 1.68 / 1.72 |
| Equilibrado | nueva | 12304 | 0 | 1 | 1.44 / 1.35 / 1.57 |
| Valiente | base | 10883 | 0 | 1 | 1.92 / 1.70 / 1.72 |
| Valiente | nueva | 12163 | 0 | 2 | 1.50 / 1.40 / 1.59 |
| Reactivo | base | 10306 | 0 | 3 | 2.01 / 1.71 / 1.73 |
| Reactivo | nueva | 11915 | 0 | 1 | 1.56 / 1.41 / 1.57 |
| Sin experiencia | base | 5570 | 0 | 0 | 1.47 / 1.11 / 0.79 |
| Sin experiencia | nueva | 5708 | 0 | 0 | 1.25 / 0.95 / 0.70 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 12304 | 104 | 140 | 68 | 0 |
| Valiente | 12163 | 95 | 159 | 100 | 0 |
| Reactivo | 11915 | 74 | 257 | 134 | 0 |
| Sin experiencia | 5708 | 8 | 41 | 36 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 22917 | 10819 | 341 |
| sobresalto | 1709 | 794 | 0 |
| plantar_cara | 768 | 164 | 0 |
| huir | 207 | 3 | 0 |

### crafter (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 248.83 ± 33.62 | 249.17 ± 25.60 | 0.33 ± 40.94 |
| Equilibrado | fitness | 9427.93 ± 1425.49 | 10561.40 ± 1196.30 | 1133.47 ± 1299.73 |
| Equilibrado | logros | 9.17 ± 1.40 | 10.30 ± 1.19 | 1.13 ± 1.29 |
| Valiente | latidos | 262.17 ± 34.19 | 260.93 ± 50.49 | -1.23 ± 44.17 |
| Valiente | fitness | 10676.20 ± 1019.71 | 11540.73 ± 971.55 | 864.53 ± 1536.16 |
| Valiente | logros | 10.40 ± 1.04 | 11.27 ± 0.95 | 0.87 ± 1.54 |
| Reactivo | latidos | 234.73 ± 26.76 | 237.07 ± 25.67 | 2.33 ± 36.71 |
| Reactivo | fitness | 8812.20 ± 1424.76 | 9514.37 ± 1234.28 | 702.17 ± 1153.90 |
| Reactivo | logros | 8.57 ± 1.40 | 9.27 ± 1.24 | 0.70 ± 1.15 |
| Sin experiencia | latidos | 262.87 ± 39.63 | 261.10 ± 31.94 | -1.77 ± 34.55 |
| Sin experiencia | fitness | 9675.40 ± 1432.80 | 11006.97 ± 1143.37 | 1331.57 ± 1326.01 |
| Sin experiencia | logros | 9.40 ± 1.41 | 10.73 ± 1.12 | 1.33 ± 1.32 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 7465 | 2 | 0 | 2.44 / 2.72 / 1.90 |
| Equilibrado | nueva | 7475 | 0 | 0 | 2.40 / 2.62 / 1.96 |
| Valiente | base | 7865 | 0 | 0 | 2.33 / 2.79 / 1.97 |
| Valiente | nueva | 7828 | 0 | 0 | 2.13 / 2.52 / 1.96 |
| Reactivo | base | 7042 | 0 | 0 | 2.50 / 2.83 / 1.90 |
| Reactivo | nueva | 7112 | 0 | 0 | 2.41 / 2.61 / 1.88 |
| Sin experiencia | base | 7886 | 0 | 0 | 2.49 / 1.75 / 1.49 |
| Sin experiencia | nueva | 7833 | 0 | 0 | 2.47 / 1.78 / 1.50 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 7475 | 83 | 165 | 40 | 53 |
| Valiente | 7828 | 85 | 58 | 10 | 12 |
| Reactivo | 7112 | 69 | 290 | 97 | 66 |
| Sin experiencia | 7833 | 70 | 181 | 68 | 92 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 24933 | 7057 | 517 |
| huir | 5194 | 4015 | 30 |
| sobresalto | 2059 | 1631 | 0 |
| cerrar_distancia | 647 | 527 | 0 |
| defensa_armada | 546 | 451 | 0 |
| quieto_o_huir | 246 | 237 | 0 |
| defenderse | 131 | 112 | 0 |
