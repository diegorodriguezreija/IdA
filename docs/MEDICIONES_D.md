# Mediciones del bloque D (relaciones más ricas)

Encargo en [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), «Encargo del bloque D»; decisiones 8, 9 y 12 de [`REDISENO_BASE.md`](REDISENO_BASE.md).

- **Comando:** `python herramientas/benchmark.py ejecutar --raiz <código> --mundo M --salida F` y `... comparar base.json nueva.json` (desde `86a7d31` guarda la causa de muerte de cada vida).
- **Versiones:** base = `main` (`05b30a2`, bloques A a C); nueva = `feature/bloque-d` (`86a7d31`).
- **Protocolo** de [`BENCHMARK_PERFILES_MUNDOS.md`](BENCHMARK_PERFILES_MUNDOS.md): N = 10 linajes (semillas 1 a 10), IC 95 % con t de Student, Δ pareado; mínimo y archivos, 4 generaciones de 400 latidos; Crafter, 3 de 600. Reloj real. 16/11/2026.

## Resultado frente al criterio

Criterio (pérdida ligera aceptable hasta el bloque E): **se cumple; no hay pérdidas significativas.**

- Crafter: no inferioridad en los cuatro grupos (límite inferior del Δ de logros: −0,92, −0,66, −0,47 y 0).
- Mínimo: Equilibrado mejora (latidos +53,6 ± 39,7). Muertes por el lobo con experiencia: 36 → 18 vidas (Equilibrado 16 → 2).
- Archivos: sin diferencias significativas.
- El control sin experiencia da exactamente lo mismo en los tres mundos.

## Decisiones tomadas sin consultar al autor

1. **D1:** valencia = placer / 100 − estrés, en [−1, 1].
2. **D2:** peligro si hay hipótesis de daño no refutada (trust = su confianza; la amenaza sube hasta ×1,5); recurso si se sabe que nutre (confianza ≥ 0,5, no refutada) o lo parece; neutro en otro caso (trust = familiaridad = avistamientos / 20; si parece peligroso, la amenaza baja hasta ×0,6). Los objetos neutros sin amenaza ni atractivo no generan pieza propia (no la generaban antes); su clasificación va en la carga de la alarma. Sin experiencia, solo la apariencia.
3. **D3:** potencia = el rasgo de peligro percibido (el cansancio del sujeto no se percibe); social = 0, lo que cambia la valencia de los agentes (antes sumaba agente × (extraversión − 0,5)).
4. **D4:** una creencia por cada proposición de la memoria (no solo de las clases a la vista), en `ef` y sin coste. «Sostiene» = demostrada, así que el criterio no cambia; la fuente afectiva (peso 0,1) solo ajusta el trust. `alimentarse` la lee del latido anterior (S3 corre después). `AlimentarseConPrudencia` (archivos) sigue leyendo los indicios de daño en la memoria (criterio del mundo, en el mismo latido). `Valor` y `recordar_comida` (S2) siguen leyendo la memoria: no estaban en el encargo.
5. **Benchmark:** `main` ya registra la causa de muerte desde el bloque C; la deducción del último latido se usa solo con versiones que no la registran. «desgaste» = sin causa del mundo ni necesidad agotada.

## Pendiente para más adelante

Anotado por el autor al aceptar el bloque D (16/11/2026):

- **Bloque E, coste de las creencias:** `Creencia` emite una pieza por cada proposición de la memoria en cada latido. Hoy es barato (solo `ef`, sin coste), pero crecerá con la memoria: vigilarlo al introducir la memoria duradera.
- **Bloque E, lecturas directas de la memoria:** `Valor` (S2) y la estrategia `recordar_comida` (S2) aún leen la memoria directamente en lugar de las creencias. Revisarlo en E.
- **Fase de mejora de los mundos, Crafter:** las muertes por «desgaste» (sin causa del mundo ni necesidad agotada) pasan de 4 a 8 entre `main` y esta rama. Investigar qué daño no se está atribuyendo.

## Tablas completas


### minimo (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 334.32 ± 34.11 | 387.90 ± 15.52 | 53.58 ± 39.67 |
| Equilibrado | fitness | 689.95 ± 76.72 | 785.40 ± 46.24 | 95.45 ± 100.60 |
| Equilibrado | setas | 1.02 ± 0.06 | 1.00 ± 0.08 | -0.03 ± 0.06 |
| Valiente | latidos | 332.45 ± 31.75 | 350.80 ± 47.06 | 18.35 ± 57.85 |
| Valiente | fitness | 691.58 ± 64.30 | 761.92 ± 104.56 | 70.35 ± 109.38 |
| Valiente | setas | 1.02 ± 0.06 | 1.02 ± 0.06 | 0.00 ± 0.00 |
| Reactivo | latidos | 376.70 ± 19.52 | 383.82 ± 13.29 | 7.12 ± 26.27 |
| Reactivo | fitness | 783.45 ± 45.30 | 785.45 ± 52.08 | 2.00 ± 71.82 |
| Reactivo | setas | 1.05 ± 0.08 | 1.02 ± 0.06 | -0.03 ± 0.06 |
| Sin experiencia | latidos | 157.07 ± 42.90 | 157.07 ± 42.90 | 0.00 ± 0.00 |
| Sin experiencia | fitness | 421.70 ± 106.66 | 421.70 ± 106.66 | 0.00 ± 0.00 |
| Sin experiencia | setas | 8.22 ± 0.60 | 8.22 ± 0.60 | 0.00 ± 0.00 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 13373 | 0 | 0 | 2.25 / 2.48 / 1.79 |
| Equilibrado | nueva | 15516 | 0 | 0 | 2.64 / 2.60 / 1.83 |
| Valiente | base | 13298 | 0 | 0 | 2.15 / 2.39 / 1.76 |
| Valiente | nueva | 14032 | 0 | 0 | 2.24 / 2.48 / 1.80 |
| Reactivo | base | 15068 | 0 | 0 | 2.70 / 2.77 / 1.83 |
| Reactivo | nueva | 15353 | 0 | 0 | 2.68 / 2.61 / 1.75 |
| Sin experiencia | base | 6283 | 0 | 0 | 2.06 / 1.53 / 0.58 |
| Sin experiencia | nueva | 6283 | 0 | 0 | 2.06 / 1.53 / 0.58 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | hambre | 2 | 4 |
| Equilibrado | lobo | 16 | 2 |
| Equilibrado | vive | 22 | 34 |
| Valiente | hambre | 10 | 2 |
| Valiente | lobo | 11 | 10 |
| Valiente | vive | 19 | 28 |
| Reactivo | hambre | 1 | 1 |
| Reactivo | lobo | 9 | 6 |
| Reactivo | vive | 30 | 33 |
| Sin experiencia | desgaste | 18 | 18 |
| Sin experiencia | lobo | 21 | 21 |
| Sin experiencia | vive | 1 | 1 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 15516 | 361 | 856 | 767 | 80 |
| Valiente | 14032 | 654 | 160 | 141 | 8 |
| Reactivo | 15353 | 332 | 1609 | 1518 | 95 |
| Sin experiencia | 6283 | 135 | 86 | 79 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 26073 | 15701 | 281 |
| huir | 9656 | 5258 | 0 |
| sobresalto | 8106 | 6277 | 0 |
| plantar_cara | 1456 | 1248 | 0 |
| defenderse | 2 | 0 | 0 |

### archivos (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 360.88 ± 27.78 | 360.27 ± 27.60 | -0.60 ± 1.36 |
| Equilibrado | fitness | 1781.75 ± 259.74 | 1783.05 ± 259.92 | 1.30 ± 2.82 |
| Equilibrado | nutritivos | 25.70 ± 3.77 | 25.75 ± 3.78 | 0.05 ± 0.08 |
| Equilibrado | toxicos | 2.25 ± 0.32 | 2.25 ± 0.32 | 0.00 ± 0.00 |
| Valiente | latidos | 366.57 ± 23.20 | 362.93 ± 21.31 | -3.65 ± 5.61 |
| Valiente | fitness | 1855.65 ± 226.75 | 1828.35 ± 216.80 | -27.30 ± 40.98 |
| Valiente | nutritivos | 27.10 ± 3.39 | 26.75 ± 3.23 | -0.35 ± 0.57 |
| Valiente | toxicos | 2.33 ± 0.30 | 2.35 ± 0.31 | 0.03 ± 0.06 |
| Reactivo | latidos | 364.15 ± 22.80 | 364.43 ± 22.58 | 0.28 ± 0.62 |
| Reactivo | fitness | 1794.55 ± 250.59 | 1813.85 ± 235.57 | 19.30 ± 43.66 |
| Reactivo | nutritivos | 25.88 ± 3.76 | 26.25 ± 3.44 | 0.38 ± 0.85 |
| Reactivo | toxicos | 2.27 ± 0.33 | 2.27 ± 0.33 | 0.00 ± 0.00 |
| Sin experiencia | latidos | 125.42 ± 45.76 | 125.42 ± 45.76 | 0.00 ± 0.00 |
| Sin experiencia | fitness | 366.05 ± 305.17 | 366.05 ± 305.17 | 0.00 ± 0.00 |
| Sin experiencia | nutritivos | 13.65 ± 4.55 | 13.65 ± 4.55 | 0.00 ± 0.00 |
| Sin experiencia | toxicos | 10.93 ± 1.50 | 10.93 ± 1.50 | 0.00 ± 0.00 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 14435 | 0 | 0 | 1.62 / 1.41 / 1.49 |
| Equilibrado | nueva | 14411 | 0 | 0 | 1.64 / 1.42 / 1.49 |
| Valiente | base | 14663 | 1 | 0 | 1.57 / 1.39 / 1.47 |
| Valiente | nueva | 14517 | 0 | 0 | 1.59 / 1.40 / 1.47 |
| Reactivo | base | 14566 | 0 | 0 | 1.64 / 1.40 / 1.49 |
| Reactivo | nueva | 14577 | 0 | 0 | 1.62 / 1.40 / 1.49 |
| Sin experiencia | base | 5017 | 0 | 0 | 1.39 / 1.10 / 0.78 |
| Sin experiencia | nueva | 5017 | 0 | 0 | 1.39 / 1.10 / 0.78 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | depredador | 4 | 5 |
| Equilibrado | hambre | 13 | 12 |
| Equilibrado | vive | 23 | 23 |
| Valiente | depredador | 2 | 2 |
| Valiente | hambre | 11 | 13 |
| Valiente | vive | 27 | 25 |
| Reactivo | depredador | 3 | 3 |
| Reactivo | hambre | 14 | 13 |
| Reactivo | vive | 23 | 24 |
| Sin experiencia | depredador | 3 | 3 |
| Sin experiencia | desgaste | 27 | 27 |
| Sin experiencia | hambre | 6 | 6 |
| Sin experiencia | vive | 4 | 4 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 14411 | 316 | 129 | 115 | 0 |
| Valiente | 14517 | 294 | 107 | 94 | 0 |
| Reactivo | 14577 | 272 | 113 | 99 | 0 |
| Sin experiencia | 5017 | 106 | 36 | 33 | 0 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 21290 | 10763 | 336 |
| sobresalto | 1121 | 352 | 0 |
| plantar_cara | 590 | 264 | 0 |
| huir | 160 | 7 | 0 |

### crafter (N = 10 linajes, IC 95 %; Δ = nueva − base, pareado por semilla)

| Grupo | Métrica | Base | Nueva | Δ pareado |
|---|---|---|---|---|
| Equilibrado | latidos | 252.80 ± 19.43 | 249.37 ± 35.21 | -3.43 ± 48.92 |
| Equilibrado | fitness | 10398.47 ± 1125.87 | 10627.43 ± 1520.48 | 228.97 ± 1178.50 |
| Equilibrado | logros | 10.13 ± 1.13 | 10.37 ± 1.50 | 0.23 ± 1.15 |
| Valiente | latidos | 253.63 ± 52.61 | 259.80 ± 46.06 | 6.17 ± 27.91 |
| Valiente | fitness | 11500.83 ± 815.24 | 11506.40 ± 1317.59 | 5.57 ± 688.34 |
| Valiente | logros | 11.23 ± 0.80 | 11.23 ± 1.29 | -0.00 ± 0.66 |
| Reactivo | latidos | 242.93 ± 33.14 | 285.27 ± 48.27 | 42.33 ± 60.36 |
| Reactivo | fitness | 9986.43 ± 1478.53 | 10297.20 ± 1633.41 | 310.77 ± 793.07 |
| Reactivo | logros | 9.73 ± 1.46 | 10.00 ± 1.59 | 0.27 ± 0.74 |
| Sin experiencia | latidos | 249.57 ± 31.63 | 249.57 ± 31.63 | 0.00 ± 0.00 |
| Sin experiencia | fitness | 10561.30 ± 1170.77 | 10561.30 ± 1170.77 | 0.00 ± 0.00 |
| Sin experiencia | logros | 10.30 ± 1.16 | 10.30 ± 1.16 | 0.00 ± 0.00 |

| Grupo | Versión | Latidos | Plazo agotado | S3 sin amplitud o potencia | Potencia media S1 / S2 / S3 por latido |
|---|---|---|---|---|---|
| Equilibrado | base | 7584 | 0 | 0 | 2.45 / 2.70 / 1.95 |
| Equilibrado | nueva | 7481 | 0 | 0 | 2.28 / 2.45 / 1.95 |
| Valiente | base | 7609 | 0 | 0 | 2.00 / 2.52 / 1.93 |
| Valiente | nueva | 7794 | 1 | 0 | 2.22 / 2.66 / 2.00 |
| Reactivo | base | 7288 | 0 | 0 | 2.36 / 2.58 / 1.84 |
| Reactivo | nueva | 8558 | 0 | 0 | 2.27 / 2.49 / 1.90 |
| Sin experiencia | base | 7487 | 0 | 0 | 2.23 / 1.63 / 1.45 |
| Sin experiencia | nueva | 7487 | 0 | 0 | 2.23 / 1.62 / 1.45 |

| Grupo | Causa de muerte | Vidas base | Vidas nueva |
|---|---|---|---|
| Equilibrado | desgaste | 0 | 4 |
| Equilibrado | esqueleto | 6 | 3 |
| Equilibrado | hambre | 1 | 0 |
| Equilibrado | sed | 1 | 2 |
| Equilibrado | vive | 0 | 1 |
| Equilibrado | zombi | 22 | 20 |
| Valiente | desgaste | 3 | 3 |
| Valiente | esqueleto | 4 | 2 |
| Valiente | flecha | 1 | 0 |
| Valiente | hambre | 1 | 4 |
| Valiente | sed | 1 | 1 |
| Valiente | vive | 1 | 1 |
| Valiente | zombi | 19 | 19 |
| Reactivo | desgaste | 1 | 1 |
| Reactivo | esqueleto | 3 | 7 |
| Reactivo | flecha | 0 | 1 |
| Reactivo | hambre | 1 | 1 |
| Reactivo | sed | 5 | 3 |
| Reactivo | vive | 1 | 1 |
| Reactivo | zombi | 19 | 16 |
| Sin experiencia | esqueleto | 5 | 5 |
| Sin experiencia | hambre | 3 | 3 |
| Sin experiencia | sed | 1 | 1 |
| Sin experiencia | vive | 1 | 1 |
| Sin experiencia | zombi | 20 | 20 |

| Grupo | Latidos | Plus decide | Reflejos | Reflejo interrumpe | Sustituciones |
|---|---|---|---|---|---|
| Equilibrado | 7481 | 77 | 170 | 129 | 40 |
| Valiente | 7794 | 143 | 56 | 44 | 13 |
| Reactivo | 8558 | 99 | 286 | 248 | 80 |
| Sin experiencia | 7487 | 89 | 166 | 128 | 68 |

| Estrategia de S1 (todos los grupos) | Latidos activa | Latidos ejecutada | Abandonos por agotamiento |
|---|---|---|---|
| alimentarse | 25818 | 7344 | 563 |
| huir | 5110 | 4006 | 21 |
| sobresalto | 2015 | 1615 | 0 |
| cerrar_distancia | 891 | 764 | 0 |
| defensa_armada | 512 | 461 | 0 |
| quieto_o_huir | 176 | 173 | 0 |
| defenderse | 144 | 131 | 0 |
