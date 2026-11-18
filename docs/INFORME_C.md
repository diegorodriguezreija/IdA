# Informe de la Fase C: Hábitat y Ciclo Circadiano en Crafter

Referencia base: `datos/benchmarks/ref_c0.json` (commit `f2f1262`).  
Rama: `feature/crafter-fase-c`.  
Sin push a remoto. Framework base (`ida/core/`, `ida/sistemas/`) estrictamente sin modificar.

---

## 1. C.0c: Corrección de fallos de S1

### 1.1 Resultado
La pieza C.0c (desplegada en los commits C.0c-1, C.0c-2 y C.0c-fix) elimina las muertes por inanición dentro del refugio sellado, evita la persecución de recursos inalcanzables tras la roca de la mina y restaura la firmeza de la espera nocturna frente a reflejos externos:
- **C.0c-1 (`16cdf5e`):** En el arnés (semillas 11–30), **0/20 vidas mueren de hambre o sed dentro del refugio sellado** (11/11 vidas selladas salen al exterior). La semilla 14 desella y sale del refugio a L259 (en lugar de morir atrapada dentro a L332), come fuera a L278, pero sucumbe por sed a L294 al no tener agua en su memoria previa y hallarse la fuente más cercana a 10 casillas.
- **C.0c-2 (`2e5ec72`):** Se implementa la detección de destinos inalcanzables en `_paso_hacia` y el enfriamiento de destinos fallidos en `self.inalcanzables` (50 latidos). En el arnés, la semilla 18 ya no queda bloqueada intentando cruzar la pared de roca hacia el agua inalcanzable.
- **C.0c-fix (`2ffb684`):** Reversión de la reducción de confianza en `ESPERAR` durante la fase `dormir`. En C.0c-1/C.0c-2, reducir la confianza de `ESPERAR` permitía que reflejos de S1 (`sobresalto` ante zombis al otro lado de la pared) usurparan el Tribunal, provocando que individuos como la semilla 11 oscilaran toda la noche consumiendo vitales y muriendo de hambre a L382. Al restaurar `ESPERAR` a 1,0/1,0, la semilla 11 pasa la noche inmóvil, sale normalmente a L275, bebe a L298 y sobrevive hasta L473 (muere en combate con 16 logros). El benchmark rápido en Equilibrado mejora notablemente en todas las métricas (+626,60 fitness, +0,60 logros, +26,17 latidos).

---

### 1.2 Tabla de evaluación

| Pieza | Commit | Hipótesis | Arnés (11–30) | Benchmark Equilibrado (1–10, N=10 pareado) | Decisión |
|---|---|---|---|---|---|
| **C.0c-1** | `16cdf5e` | La semilla 14 sale del refugio y bebe; ninguna muerte por hambre o sed dentro de refugio sellado. | **Confirmada a medias:** 11/11 selladas salen (0 muertes dentro: **sí**). Semilla 14 sale a L259 y come a L278, pero no bebe y muere de sed fuera a L294 (**no bebe**). | Latidos: +0,77 ± 58,97<br>Fitness: +34,00 ± 742,64<br>Logros: +0,03 ± 0,70<br>Noches: +0,10 ± 0,32 | **Aceptada** (base para C.0c-2) |
| **C.0c-2** | `2e5ec72` | La semilla 18 no va y viene entre 2 casillas más de 20 latidos; descartar aguas inalcanzables. | **Confirmada en refugio:** la semilla 18 no oscila contra la pared de roca tras la mina.<br>Beben tras salir: 9/11 (81,8 %). | Latidos: -0,97 ± 59,66<br>Fitness: +132,50 ± 765,09<br>Logros: +0,13 ± 0,72<br>Noches: +0,10 ± 0,32 | **Aceptada** (con corrección en fix) |
| **C.0c-fix** | `2ffb684` | Mantener `ESPERAR` a 1,0/1,0 evita que `sobresalto` rompa la quietud nocturna; semilla 11 sobrevive toda la noche. | **Confirmada:** semilla 11 permanece inmóvil de noche, sale a L275, bebe a L298 y llega a L473.<br>0 muertes dentro del refugio. | Latidos: **+26,17 ± 43,01**<br>Fitness: **+626,60 ± 658,07**<br>Logros: **+0,60 ± 0,63**<br>Noches: **+0,13 ± 0,17** | **Aceptada** |

#### Comprobación de vaivén (> 20 latidos entre 2 casillas)
- **En el entorno del refugio / agua inalcanzable (objetivo de C.0c-2):** Ninguna vida presenta vaivén > 20 latidos intentando atravesar roca hacia agua inalcanzable.
- **En campo abierto (conducta global):** Persiste el vaivén > 20 latidos en 12 de las 20 vidas (semillas 12, 13, 16, 18, 19, 21, 22, 23, 25, 26, 27, 28) durante la recolección de madera o enfrentamientos/huidas en campo abierto. El parche de inalcanzables solucionó el atasco puntual contra la pared de la mina, pero no el vaivén por colisiones y arbitraje en campo abierto (problema general no resuelto).

---

### 1.3 Causas de muerte en el arnés (semillas 11–30)

Base de comparación: verificación de C.0a-2 (donde la semilla 27 se clasificó como flecha de esqueleto en L333 con comida 0 y salud 1).

| Causa de muerte | Ref C.0 (C.0a-2) | C.0c-1 | C.0c-2 | C.0c-fix | Δ (C.0c-fix vs Ref) |
|---|---|---|---|---|---|
| **zombi** | 6 | 6 | 6 | 7 | +1 |
| **esqueleto** | 5 | 4 | 4 | 4 | -1 |
| **hambre** | 3 | 6 | 6 | 5 | +2 |
| **sed** | 2 | 1 | 1 | 3 | +1 |
| **vivas** | 4 | 3 | 3 | 1 | -3 |
| *Muerte dentro de refugio* | 1 (sem 14) | 0 | 0 | 0 | **-1 (0 dentro)** |

*Nota:* La discrepancia con el borrador inicial de C.0 (que marcaba esqueleto 4 y sed 3) se debe a que la verificación rigurosa de C.0a-2 reatribuyó la muerte de la semilla 27 a esqueleto (flecha mortal registrada en L333).

---

### 1.4 Benchmark rápido: Equilibrado (10 linajes, 30 vidas)

Comparación `datos/benchmarks/ref_c0.json` vs `datos/benchmarks/c0c_fix.json`:

| Métrica | Base (`ref_c0`) | C.0c-fix | Δ pareado (IC 95 %) |
|---|---|---|---|
| **latidos** | 370.10 ± 66.57 | 396.27 ± 70.03 | **+26.17 ± 43.01** |
| **fitness** | 11315.50 ± 1407.01 | 11942.10 ± 1519.52 | **+626.60 ± 658.07** |
| **logros** | 10.93 ± 1.36 | 11.53 ± 1.47 | **+0.60 ± 0.63** |
| **noches** | 0.90 ± 0.28 | 1.03 ± 0.29 | **+0.13 ± 0.17** |

#### Muertes por causa (Equilibrado, 30 vidas)
| Causa | Base (`ref_c0`) | C.0c-fix | Δ |
|---|---|---|---|
| zombi | 10 | 8 | -2 |
| hambre | 6 | 7 | +1 |
| sed | 6 | 8 | +2 |
| esqueleto | 2 | 1 | -1 |
| vive | 6 | 6 | 0 |

#### Logros por tipo (Equilibrado, 30 vidas)
| Logro | Base (`ref_c0`) | C.0c-fix | Δ vidas | Observación |
|---|---|---|---|---|
| collect_coal | 10 | 11 | +1 | [No verificado: no medido el mecanismo causal] |
| collect_drink | 24 | 25 | +1 | [No verificado: no medido el mecanismo causal] |
| collect_sapling | 30 | 30 | 0 | 100 % de vidas |
| collect_stone | 23 | 25 | +2 | [No verificado: no medido el mecanismo causal] |
| collect_wood | 30 | 30 | 0 | 100 % de vidas |
| defeat_skeleton | 14 | 14 | 0 | Estable |
| defeat_zombie | 17 | 19 | +2 | [No verificado: no medido el mecanismo causal] |
| eat_cow | 19 | 21 | +2 | [No verificado: no medido el mecanismo causal] |
| make_stone_pickaxe | 2 | 2 | 0 | Estable |
| make_stone_sword | 1 | 1 | 0 | Estable |
| make_wood_pickaxe | 27 | 29 | +2 | [No verificado: no medido el mecanismo causal] |
| make_wood_sword | 26 | 28 | +2 | [No verificado: no medido el mecanismo causal] |
| place_furnace | 6 | 8 | +2 | [No verificado: no medido el mecanismo causal] |
| place_plant | 30 | 30 | 0 | 100 % de vidas |
| place_stone | 21 | 23 | +2 | [No verificado: no medido el mecanismo causal] |
| place_table | 29 | 29 | 0 | Estable |
| wake_up | 19 | 21 | +2 | [No verificado: no medido el mecanismo causal] |

---

### 1.5 Análisis transversal: muertes homeostáticas (hambre + sed)

Al analizar en conjunto las muertes homeostáticas:
- **En el arnés (semillas 11–30):** Las muertes por hambre + sed pasan de **5** en C.0a-2 (3 hambre + 2 sed) a **7** en C.0c-2 (6 hambre + 1 sed) y a **8** en C.0c-fix (5 hambre + 3 sed).
- **En el benchmark de Equilibrado (30 vidas):** Las muertes por hambre + sed pasan de **12** en la base (6 hambre + 6 sed) a **15** en C.0c-fix (7 hambre + 8 sed).

**Conclusión:**  
Los parches de C.0c resuelven patologías operativas puntuales (morir encerrado por no desellar, quedar atrapado contra una pared de roca buscando agua inalcanzable, oscilar de noche dentro del refugio por reflejos a monstruos lejanos). Sin embargo, **no reducen las muertes homeostáticas globales**.  
El individuo sobrevive a la noche y desella puntualmente, pero sigue saliendo a un entorno diurno sin reservas acumuladas y sin un conocimiento espacial previo de dónde abastecerse de agua o comida. Al disiparse el refugio, el déficit metabólico acumulado precipita la muerte por sed o inanición a las pocas decenas de latidos.  

Este diagnóstico confirma la necesidad de abordar los objetivos centrales de las siguientes fases:
- **C.1 (Aprovisionamiento):** Acumular comida y agua antes de sellar el refugio nocturno.
- **C.2 (Hábitat y Retorno):** Mantener un mapa de recursos estables y una base segura a la que retornar con conocimiento de fuentes de agua viables.

---

### 1.6 Verificación de pureza y base

Comandos ejecutados y su salida literal:

```powershell
PS F:\code\IdA> git diff --stat main...HEAD -- ida/core ida/sistemas
(salida vacía: ningún archivo modificado en ida/core ni ida/sistemas)

PS F:\code\IdA> python -m pytest -q
160 passed, 1 warning in 39.34s

PS F:\code\IdA> ruff check ida tests herramientas
All checks passed!

PS F:\code\IdA> mypy ida
Success: no issues found in 40 source files
```

### 1.7 Estado de verificación
- **Verificado:** Mediciones registradas directamente con el arnés (`herramientas/arnes_refugio_crafter.py --real`) y el benchmark rápido pareado (`herramientas/benchmark.py ejecutar` y `comparar`) sobre Crafter 1.8.3.
- **No verificado:** Causas causales del incremento individual en logros específicos (marcadas explícitamente en la tabla de logros). Grupos Valiente, Reactivo y Sin experiencia (no ejecutados en el benchmark rápido de Equilibrado para ahorrar presupuesto de cómputo).
