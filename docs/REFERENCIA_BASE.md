# Referencia congelada de la base

Comparación para toda la fase de mejora de los mundos ([`AGENTS.md`](../AGENTS.md), «Fase de mejora de los mundos»). Cada mejora de un mundo se mide con `herramientas/benchmark.py` frente a estas cifras, pareado por semilla.

- **Código medido:** `feature/cierre-base` en `ce0e262` (bloques A a D y escasez de atención calibrada, `Marcapasos.FACTOR_AMPLITUD = 0,45`). Tras la fusión, etiqueta `base-v2.0`.
- **Fecha:** 16/11/2026, Windows 10, Python 3.15.1. Reloj real.
- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F` (M = minimo, archivos, crafter) y `... comparar base.json nueva.json`.
- **Protocolo** de [`BENCHMARK_PERFILES_MUNDOS.md`](BENCHMARK_PERFILES_MUNDOS.md): N = 10 linajes (semillas 1 a 10, directorio limpio); mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600. Perfiles Equilibrado, Valiente y Reactivo y control sin experiencia (Equilibrado con `sin_experiencia`). Media por linaje, IC 95 % con t(0,975; 9) = 2,262.
- **Invariancia:** la referencia de `herramientas/invariancia.py` (semillas 1 a 3, 400 latidos, cuatro mundos) se regeneró en este código y da OK.

## Valores de referencia (media ± IC 95 %, N = 10 linajes)

| Mundo | Métrica | Equilibrado | Valiente | Reactivo | Sin experiencia |
|---|---|---|---|---|---|
| Crafter | logros | 9,87 ± 1,47 | 10,67 ± 1,66 | 9,37 ± 1,46 | 9,67 ± 1,40 |
| Crafter | latidos | 247,43 ± 37,93 | 252,50 ± 65,72 | 282,00 ± 44,07 | 265,00 ± 51,19 |
| Mínimo | latidos | 387,90 ± 15,52 | 350,80 ± 47,06 | 383,82 ± 13,29 | 157,07 ± 42,90 |
| Mínimo | setas | 1,00 ± 0,08 | 1,02 ± 0,06 | 1,02 ± 0,06 | 8,22 ± 0,60 |
| Archivos | fitness | 1788,55 ± 263,63 | 1851,90 ± 241,39 | 1824,70 ± 241,19 | 366,05 ± 305,17 |
| Archivos | latidos | 360,52 ± 27,78 | 364,07 ± 22,20 | 364,85 ± 22,91 | 125,42 ± 45,76 |
| Archivos | tóxicos | 2,25 ± 0,32 | 2,35 ± 0,31 | 2,27 ± 0,33 | 10,93 ± 1,50 |

## Muertes por causa (vidas de los 10 linajes)

| Mundo | Grupo | Causas |
|---|---|---|
| Crafter (30 vidas) | Equilibrado | zombi 22, esqueleto 3, sed 2, flecha 1, hambre 1, desgaste 1 |
| | Valiente | zombi 18, esqueleto 5, desgaste 4, sed 2; vive 1 |
| | Reactivo | zombi 15, esqueleto 5, sed 5, hambre 2, flecha 1, desgaste 1; vive 1 |
| | Sin experiencia | zombi 19, esqueleto 6, hambre 2, sed 1, desgaste 1; vive 1 |
| Mínimo (40 vidas) | Equilibrado | hambre 4, lobo 2; viven 34 |
| | Valiente | lobo 10, hambre 2; viven 28 |
| | Reactivo | lobo 6, hambre 1; viven 33 |
| | Sin experiencia | lobo 21, desgaste 18; vive 1 |
| Archivos (40 vidas) | Equilibrado | hambre 12, depredador 5; viven 23 |
| | Valiente | hambre 12, depredador 1; viven 27 |
| | Reactivo | hambre 12, depredador 3; viven 25 |
| | Sin experiencia | desgaste 27, hambre 6, depredador 3; viven 4 |

«desgaste»: sin causa del mundo ni necesidad agotada.

## Efecto de la calibración de la atención

Frente a `main` antes de calibrar (bloque D, misma medición de [`MEDICIONES_D.md`](MEDICIONES_D.md)), ninguna diferencia es significativa: Crafter, logros de −0,50 a −0,63 (los IC incluyen el 0); mínimo y archivos, prácticamente iguales. Detalle del barrido en [`CALIBRACION_ATENCION.md`](CALIBRACION_ATENCION.md).

## Tablas completas (base = `main` antes de calibrar; nueva = esta referencia)


### minimo (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 387.90 ± 15.52 | 387.90 ± 15.52 | 0.00 ± 0.00 |
| Equilibrado | fitness | 785.40 ± 46.24 | 782.90 ± 47.65 | -2.50 ± 5.66 |
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

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 15516 | 0 | 0 | 2.64 / 2.60 / 1.83 |
| Equilibrado | nueva | 15516 | 1 | 209 | 2.64 / 2.58 / 1.80 |
| Valiente | base | 14032 | 0 | 0 | 2.24 / 2.48 / 1.80 |
| Valiente | nueva | 14032 | 0 | 129 | 2.24 / 2.48 / 1.79 |
| Reactivo | base | 15353 | 0 | 0 | 2.68 / 2.61 / 1.75 |
| Reactivo | nueva | 15353 | 0 | 177 | 2.68 / 2.61 / 1.73 |
| Sin experiencia | base | 6283 | 0 | 0 | 2.06 / 1.53 / 0.58 |
| Sin experiencia | nueva | 6283 | 0 | 36 | 2.06 / 1.53 / 0.58 |

| Grupo | Versión | S3 sin recursos con peligro | S3 sin recursos en calma |
|---|---|---|---|
| Equilibrado | nueva | 2.2 % de 7509 | 0.6 % de 7285 |
| Valiente | nueva | 2.0 % de 4152 | 0.5 % de 9308 |
| Reactivo | nueva | 1.8 % de 7047 | 0.6 % de 7630 |
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
| Equilibrado | 15516 | 360 | 857 | 768 | 82 |
| Valiente | 14032 | 654 | 160 | 141 | 8 |
| Reactivo | 15353 | 332 | 1609 | 1518 | 95 |
| Sin experiencia | 6283 | 135 | 86 | 79 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 26120 | 15730 | 283 |
| huir | 9666 | 5257 | 0 |
| sobresalto | 8109 | 6284 | 0 |
| plantar_cara | 1458 | 1250 | 0 |
| defenderse | 2 | 0 | 0 |

### archivos (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 360.27 ± 27.60 | 360.52 ± 27.78 | 0.25 ± 0.57 |
| Equilibrado | fitness | 1783.05 ± 259.92 | 1788.55 ± 263.63 | 5.50 ± 8.95 |
| Equilibrado | nutritivos | 25.75 ± 3.78 | 25.85 ± 3.86 | 0.10 ± 0.17 |
| Equilibrado | toxicos | 2.25 ± 0.32 | 2.25 ± 0.32 | 0.00 ± 0.00 |
| Valiente | latidos | 362.93 ± 21.31 | 364.07 ± 22.20 | 1.15 ± 3.07 |
| Valiente | fitness | 1828.35 ± 216.80 | 1851.90 ± 241.39 | 23.55 ± 54.16 |
| Valiente | nutritivos | 26.75 ± 3.23 | 27.18 ± 3.71 | 0.42 ± 0.96 |
| Valiente | toxicos | 2.35 ± 0.31 | 2.35 ± 0.31 | 0.00 ± 0.00 |
| Reactivo | latidos | 364.43 ± 22.58 | 364.85 ± 22.91 | 0.42 ± 0.96 |
| Reactivo | fitness | 1813.85 ± 235.57 | 1824.70 ± 241.19 | 10.85 ± 16.42 |
| Reactivo | nutritivos | 26.25 ± 3.44 | 26.45 ± 3.55 | 0.20 ± 0.30 |
| Reactivo | toxicos | 2.27 ± 0.33 | 2.27 ± 0.33 | 0.00 ± 0.00 |
| Sin experiencia | latidos | 125.42 ± 45.76 | 125.42 ± 45.76 | 0.00 ± 0.00 |
| Sin experiencia | fitness | 366.05 ± 305.17 | 366.05 ± 305.17 | 0.00 ± 0.00 |
| Sin experiencia | nutritivos | 13.65 ± 4.55 | 13.65 ± 4.55 | 0.00 ± 0.00 |
| Sin experiencia | toxicos | 10.93 ± 1.50 | 10.93 ± 1.50 | 0.00 ± 0.00 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 14411 | 0 | 0 | 1.64 / 1.42 / 1.49 |
| Equilibrado | nueva | 14421 | 0 | 223 | 1.63 / 1.42 / 1.45 |
| Valiente | base | 14517 | 0 | 0 | 1.59 / 1.40 / 1.47 |
| Valiente | nueva | 14563 | 0 | 214 | 1.59 / 1.40 / 1.44 |
| Reactivo | base | 14577 | 0 | 0 | 1.62 / 1.40 / 1.49 |
| Reactivo | nueva | 14594 | 0 | 214 | 1.61 / 1.39 / 1.45 |
| Sin experiencia | base | 5017 | 0 | 0 | 1.39 / 1.10 / 0.78 |
| Sin experiencia | nueva | 5017 | 0 | 20 | 1.39 / 1.10 / 0.78 |

| Grupo | Versión | S3 sin recursos con peligro | S3 sin recursos en calma |
|---|---|---|---|
| Equilibrado | nueva | 2.2 % de 6114 | 0.8 % de 7467 |
| Valiente | nueva | 2.3 % de 6092 | 0.7 % de 7646 |
| Reactivo | nueva | 2.1 % de 6050 | 0.7 % de 7688 |
| Sin experiencia | nueva | 0.5 % de 1776 | 0.4 % de 3093 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | depredador | 5 | 5 |
| Equilibrado | hambre | 12 | 12 |
| Equilibrado | vive | 23 | 23 |
| Valiente | depredador | 2 | 1 |
| Valiente | hambre | 13 | 12 |
| Valiente | vive | 25 | 27 |
| Reactivo | depredador | 3 | 3 |
| Reactivo | hambre | 13 | 12 |
| Reactivo | vive | 24 | 25 |
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

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 21302 | 10929 | 332 |
| sobresalto | 1120 | 350 | 0 |
| plantar_cara | 594 | 264 | 0 |
| huir | 157 | 7 | 0 |

### crafter (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 249.37 ± 35.21 | 247.43 ± 37.93 | -1.93 ± 50.51 |
| Equilibrado | fitness | 10627.43 ± 1520.48 | 10126.43 ± 1485.51 | -501.00 ± 891.44 |
| Equilibrado | logros | 10.37 ± 1.50 | 9.87 ± 1.47 | -0.50 ± 0.85 |
| Valiente | latidos | 259.80 ± 46.06 | 252.50 ± 65.72 | -7.30 ± 61.22 |
| Valiente | fitness | 11506.40 ± 1317.59 | 10932.10 ± 1709.16 | -574.30 ± 1303.90 |
| Valiente | logros | 11.23 ± 1.29 | 10.67 ± 1.66 | -0.57 ± 1.25 |
| Reactivo | latidos | 285.27 ± 48.27 | 282.00 ± 44.07 | -3.27 ± 43.92 |
| Reactivo | fitness | 10297.20 ± 1633.41 | 9660.57 ± 1481.90 | -636.63 ± 879.35 |
| Reactivo | logros | 10.00 ± 1.59 | 9.37 ± 1.46 | -0.63 ± 0.85 |
| Sin experiencia | latidos | 249.57 ± 31.63 | 265.00 ± 51.19 | 15.43 ± 63.67 |
| Sin experiencia | fitness | 10561.30 ± 1170.77 | 9942.70 ± 1426.24 | -618.60 ± 1072.51 |
| Sin experiencia | logros | 10.30 ± 1.16 | 9.67 ± 1.40 | -0.63 ± 1.03 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 7481 | 0 | 0 | 2.28 / 2.45 / 1.95 |
| Equilibrado | nueva | 7423 | 0 | 1620 | 2.31 / 2.68 / 1.66 |
| Valiente | base | 7794 | 1 | 0 | 2.22 / 2.66 / 2.00 |
| Valiente | nueva | 7575 | 0 | 1741 | 2.16 / 2.55 / 1.62 |
| Reactivo | base | 8558 | 0 | 0 | 2.27 / 2.49 / 1.90 |
| Reactivo | nueva | 8460 | 0 | 1891 | 2.39 / 2.74 / 1.63 |
| Sin experiencia | base | 7487 | 0 | 0 | 2.23 / 1.62 / 1.45 |
| Sin experiencia | nueva | 7950 | 0 | 1725 | 2.51 / 1.84 / 1.29 |

| Grupo | Versión | S3 sin recursos con peligro | S3 sin recursos en calma |
|---|---|---|---|
| Equilibrado | nueva | 29.5 % de 2331 | 22.7 % de 4107 |
| Valiente | nueva | 32.1 % de 2629 | 22.6 % de 3940 |
| Reactivo | nueva | 31.6 % de 2641 | 22.2 % de 4745 |
| Sin experiencia | nueva | 28.4 % de 2666 | 23.0 % de 4183 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | desgaste | 4 | 1 |
| Equilibrado | esqueleto | 3 | 3 |
| Equilibrado | flecha | 0 | 1 |
| Equilibrado | hambre | 0 | 1 |
| Equilibrado | sed | 2 | 2 |
| Equilibrado | vive | 1 | 0 |
| Equilibrado | zombi | 20 | 22 |
| Valiente | desgaste | 3 | 4 |
| Valiente | esqueleto | 2 | 5 |
| Valiente | hambre | 4 | 0 |
| Valiente | sed | 1 | 2 |
| Valiente | vive | 1 | 1 |
| Valiente | zombi | 19 | 18 |
| Reactivo | desgaste | 1 | 1 |
| Reactivo | esqueleto | 7 | 5 |
| Reactivo | flecha | 1 | 1 |
| Reactivo | hambre | 1 | 2 |
| Reactivo | sed | 3 | 5 |
| Reactivo | vive | 1 | 1 |
| Reactivo | zombi | 16 | 15 |
| Sin experiencia | desgaste | 0 | 1 |
| Sin experiencia | esqueleto | 5 | 6 |
| Sin experiencia | hambre | 3 | 2 |
| Sin experiencia | sed | 1 | 1 |
| Sin experiencia | vive | 1 | 1 |
| Sin experiencia | zombi | 20 | 19 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 7423 | 84 | 139 | 112 | 34 |
| Valiente | 7575 | 113 | 81 | 70 | 11 |
| Reactivo | 8460 | 97 | 288 | 244 | 84 |
| Sin experiencia | 7950 | 97 | 140 | 115 | 140 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 26216 | 8793 | 583 |
| huir | 5259 | 4179 | 25 |
| sobresalto | 1933 | 1558 | 0 |
| cerrar_distancia | 553 | 482 | 0 |
| defensa_armada | 390 | 342 | 0 |
| quieto_o_huir | 193 | 181 | 0 |
| defenderse | 162 | 147 | 0 |
