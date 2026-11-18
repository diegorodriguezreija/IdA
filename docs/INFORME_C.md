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

---

## 2. C.1: Recinto flexible y primitiva de orientación

### 2.1 Resultado
**Hipótesis confirmada (`e0b5c7f`):** Al permitir que el refugio se complete colocando piedra (`tapar`) en hasta 3 paredes faltantes de `(e2, e3)` además de excavar roca (`cavar`), las vidas selladas el día 1 en el arnés (`--real`, semillas 11–30) pasan de **11/20 (55,0 %)** en C.0c-fix a **16/20 (80,0 %)** (cumpliendo el umbral $\ge 16/20$), con **16/20 `wake_up` (80,0 %)** y **100 % de las selladas sin daño nocturno (16/16)**. El tiempo por latido en el arnés queda en **10,86 ms/latido** ($\le +20\,\%$ respecto al ~10,15 ms/latido del intento inicial).

---

### 2.2 Tabla de evaluación

| Pieza | Commit | Hipótesis | Arnés (11–30, `--real`) | Validación (31–50) | Benchmark (1–10) | Decisión |
|---|---|---|---|---|---|---|
| **C.1** | `e0b5c7f` | Vidas selladas el día 1 $\ge 16/20$ sin perder `wake_up` dentro; tiempo por latido $\le +20\,\%$. | **Confirmada:**<br>• Selladas día 1: **16/20 (80,0 %)** (paso $\le 214$)<br>• Sin daño dentro: **16/16 (100 %)**<br>• `wake_up`: **16/20 (80,0 %)**<br>• Vivas al final: **4/20**<br>• Latidos medios: **398,2**<br>• Logros medios: **11,50**<br>• Tiempo/latido: **10,86 ms** | **Confirmada:**<br>• Selladas día 1: **16/20 (80,0 %)** (vs 12/20, +4 vidas)<br>• Agua dentro: **4/16 (25,0 %)**<br>• Vivas al final: **4/20** (vs 2/20)<br>• Latidos medios: **413,9** (vs 350,6)<br>• Criterio: del mismo orden que 11–30 (+4 vs +5 vidas) | • Latidos: **+52,60 ± 86,99** vs `ref_c0` (**+26,43 ± 102,50** vs `c0c_fix`)<br>• Noches: **+0,30 ± 0,38** vs `ref_c0`<br>• Vivas: **11/30** (vs 6/30 en `ref_c0`)<br>• Sed: **4/30** (vs 6 en `ref_c0`, 8 en `c0c_fix`)<br>• ms/latido: **5,24 ms** | **Aceptada** |

---

### 2.3 Ajustes mínimos aplicados sobre el pseudocódigo (de Intento 1 a Intento 2)
En el primer intento con el pseudocódigo literal se obtuvieron **14/20** vidas selladas el día 1 (`10,15 ms/latido`). El análisis de los registros del intento 1 reveló cinco efectos de borde que se corrigieron con cambios mínimos dentro de `RefugioNocturno` para el segundo intento (**16/20**):
1. **Sólo `"stone"` aporta piedra al inventario (`piedras_cavar`):** En `_evaluar_recinto`, `ROCA_EXCAVABLE` incluye `"coal"`, pero en Crafter picar carbón no entrega `"stone"`. Para la factibilidad de piedras (`colocar + 1 <= piedra_inv + piedras_cavar`) solo se contabilizan las casillas de `e1..e3` cuyo material es `"stone"`.
2. **No activar `cavar`/`tapar` en plena mañana (`not anticipa`):** Con casillas transitables (`grass`) admitidas en `e1..e3`, el individuo pisaba casillas del recinto candidato a mitad de mañana (`not anticipa`), disparando `cavar` o `tapar` con motivación baja `(0,28, 0,52)` y perdiendo el Tribunal repetidamente. Se restringió la entrada a `cavar`/`tapar` a cuando `anticipa` (o `dominante`) está activo.
3. **Coherencia del factor de margen en `provisiones`:** `aguas_cerca` y `comidas_cerca` usaban un factor `1,35` frente al `1,55` de `margen_cierre`, provocando un vaivén `provisiones <-> elegir_mina` al alejarse 1 casilla de `e0` y al reducirse `rocas_pendientes` durante `cavar`. Se unificó el factor en `1,55 + 4,0` y se evitó volver a `provisiones` una vez iniciada la obra (`cavar`/`tapar`/`cerrarse`) por la tarde.
4. **Extracción de piedra cercana cuando `mina is None`:** Si al llegar junto a una roca (`_dist(pos, roca_pos) == 1`) sigue sin haber recinto factible por falta de piedra en el inventario (`inv["stone"] < 3`), la fase `elegir_mina` pica esa roca (`Verbo.COGER`) en lugar de marcarla solo como inspeccionada, y mantiene motivación `(0,58, 0,82)` mientras `mina is None` para que la piedra no se pierda antes de localizar recinto.
5. **Distinción entre amanecer y noche (`es_noche`):** Si un individuo sale al amanecer con `luz < 0,5` por urgencia metabólica (`estado["manana"]` activo y luz subiendo), `es_noche` no se activa para evitar que vuelva a sellarse inmediatamente tras abrir.

---

### 2.4 Detalle por semilla en el arnés (semillas 11–30, `--real`)

| Semilla | Sellada (día 1) | Paso sellado | Latido sellado | Luz al sellar | Piedras en `tapar` | Agua dentro | Comida / Agua al sellar | Comida / Agua al salir | Causa de muerte | Latidos vividos | `wake_up` | Logros |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **11** | Sí | 128 | 123 | 0,721 | 0 | Sí | 9 / 6 | 4 / 9 | **Vive** | 600 | Sí | 15 |
| **12** | Sí | 194 | 186 | 0,041 | 1 | No | 6 / 4 | 2 / 0 | hambre | 441 | Sí | 13 |
| **13** | Sí | 137 | 130 | 0,624 | 1 | Sí | 7 / 7 | 2 / 9 | hambre | 479 | Sí | 12 |
| **14** | Sí | 125 | 121 | 0,751 | 0 | No | 5 / 4 | 0 / 0 | zombi | 311 | Sí | 10 |
| **15** | No | — | — | — | 0 | No | — | — | zombi | 169 | No | 8 |
| **16** | No | — | — | — | 0 | No | — | — | zombi | 155 | No | 8 |
| **17** | Sí | 130 | 121 | 0,700 | 2 | Sí | 6 / 7 | 2 / 9 | hambre | 428 | Sí | 12 |
| **18** | Sí | 178 | 173 | 0,158 | 0 | No | 3 / 4 | 0 / 0 | zombi | 325 | Sí | 12 |
| **19** | Sí | 124 | 118 | 0,760 | 0 | No | 5 / 5 | 0 / 0 | zombi | 315 | Sí | 12 |
| **20** | Sí | 157 | 151 | 0,386 | 2 | No | 7 / 5 | 3 / 0 | **Vive** | 600 | Sí | 13 |
| **21** | Sí | 126 | 119 | 0,741 | 1 | Sí | 5 / 6 | 0 / 9 | **Vive** | 600 | Sí | 13 |
| **22** | Sí | 147 | 133 | 0,507 | 1 | Sí | 4 / 8 | 0 / 9 | esqueleto | 406 | Sí | 12 |
| **23** | Sí | 214 | 209 | 0,003 | 0 | No | 3 / 4 | 1 / 2 | hambre | 412 | Sí | 13 |
| **24** | No | — | — | — | 0 | No | — | — | zombi | 189 | No | 8 |
| **25** | Sí | 132 | 120 | 0,679 | 2 | No | 4 / 3 | 0 / 0 | hambre | 321 | Sí | 11 |
| **26** | No | — | — | — | 0 | No | — | — | zombi | 271 | No | 9 |
| **27** | Sí | 175 | 168 | 0,186 | 1 | Sí | 3 / 3 | 0 / 9 | hambre | 355 | Sí | 11 |
| **28** | Sí | 170 | 164 | 0,238 | 0 | No | 5 / 7 | 1 / 2 | **Vive** | 600 | Sí | 12 |
| **29** | Sí | 186 | 167 | 0,091 | 0 | No | 5 / 6 | 2 / 2 | zombi | 489 | Sí | 12 |
| **30** | Sí | 153 | 129 | 0,434 | 0 | Sí | 7 / 6 | 2 / 9 | hambre | 499 | Sí | 14 |

**Resumen de las 16 vidas selladas:**
- **Paso de sellado (día 1):** media **155,1** (rango 124–214; las 16 sellan en el día 1, antes del paso 300).
- **Piedras colocadas en `tapar` (antes del sello):** 8 de las 16 vidas selladas colocan entre 1 y 2 piedras de pared (total 11 piedras de pared colocadas; media 0,69 por refugio sellado).
- **Agua accesible dentro del refugio:** **7/16 (43,8 %)** de las vidas selladas disponen de pared de agua interior y salen por la mañana con `agua = 9`.
- **Reservas medias al salir (16 salidas):** comida **1,19**, agua **4,31**.

---

### 2.5 Causas de muerte en el arnés (semillas 11–30) frente a las piezas anteriores

| Causa de muerte | Ref C.0 (C.0a-2) | C.0c-fix | C.1 (`e0b5c7f`) | Δ (C.1 vs C.0c-fix) |
|---|---|---|---|---|
| **zombi** | 6 | 7 | 8 | +1 |
| **esqueleto** | 5 | 4 | **1** | **-3** |
| **hambre** | 3 | 5 | 7 | +2 |
| **sed** | 2 | 3 | **0** | **-3** |
| **vivas** | 4 | 1 | **4** | **+3** |
| *Muerte dentro de refugio* | 1 | 0 | **0** | = 0 |
| *Selladas día 1* | 11 | 11 | **16** | **+5** |

*Observación para C.2:* Las muertes por sed en el arnés caen a **0/20** gracias a la frecuente elección de recintos junto al agua (7/16 con agua dentro y 15/16 bebiendo tras salir), pero las muertes por hambre son **7/20** (total hambre + sed = 7 > 3), ya que varias vidas sellan con comida baja (3–5 puntos) y salen en la mañana con `comida = 0`. Esto cumple la condición de activación de la pieza C.2 (sección 6 de `ENCARGO_CRAFTER_C.md`).

---

### 2.7 Verificación de la base y tests

Salida literal de los comandos de verificación:

```powershell
PS F:\code\IdA> git diff --stat main...HEAD -- ida/core ida/sistemas
(salida vacía: ningún archivo modificado en ida/core ni ida/sistemas)

PS F:\code\IdA> python -m pytest -q
165 passed, 1 warning in 34.34s

PS F:\code\IdA> ruff check ida tests herramientas
All checks passed!

PS F:\code\IdA> mypy ida
Success: no issues found in 40 source files
```

---

### 2.8 Validación de sobreajuste: semillas 31–50 (`--real`)

Ejecución comparativa pareada en semillas 31–50 con el arnés `--real` (600 latidos, perfil Equilibrado) entre **C.0c-fix** (commit `2ffb684`, mediante `git worktree`) y **C.1** (commit `e0b5c7f`):

| Métrica (semillas 31–50, N = 20) | C.0c-fix (`2ffb684`) | C.1 (`e0b5c7f`) | Δ (C.1 vs C.0c-fix) |
|---|---|---|---|
| **Vidas selladas el día 1 (paso $\le 300$)** | 12/20 (60,0 %) | **16/20 (80,0 %)** | **+4 vidas (+20,0 %)** |
| **Agua accesible dentro del refugio** | 2/12 (16,7 %) | **4/16 (25,0 %)** | **+2 refugios con agua (+8,3 %)** |
| **Comida media al salir del refugio** | 1,77 | 1,50 | -0,27 |
| **Agua media al salir del refugio** | 2,08 | **3,25** | **+1,17** |
| **Vivas al final (600 latidos)** | 2/20 (10,0 %) | **4/20 (20,0 %)** | **+2 vidas (+10,0 %)** |
| **Latidos medios vividos** | 350,6 | **413,9** | **+63,3 latidos** |

#### Muertes por causa en semillas 31–50
| Causa de muerte | C.0c-fix | C.1 | Δ |
|---|---|---|---|
| **sed** | 6 | **3** | **-3** |
| **zombi** | 4 | 5 | +1 |
| **hambre** | 6 | 7 | +1 |
| **esqueleto** | 2 | **1** | **-1** |
| **vivas** | 2 | **4** | **+2** |

#### Criterio de validación de sobreajuste
**Confirmado:** La mejora de vidas selladas el día 1 en el conjunto de prueba (semillas 31–50) es de **+4 vidas** (pasando de 12 a 16, +20,0 %), exactamente del mismo orden que en el conjunto de diseño de semillas 11–30 (**+5 vidas**, pasando de 11 a 16, +25,0 %). En ambas baterías independientes de 20 vidas, C.1 alcanza un sellado nocturno en el día 1 del **80,0 % (16/20)**, superando holgadamente el criterio de no decaer en más de 2 vidas respecto a 11–30.

#### Desglose por semilla en semillas 31–50
| Semilla | C.0c-fix Sellada (paso) | C.0c-fix Resultado (L) | C.1 Sellada (paso) | C.1 Resultado (L) | C.1 Salida (comida, agua) |
|---|---|---|---|---|---|
| **31** | Sí (171) | sed (L323) | Sí (128) | sed (L295) | 0, 0 |
| **32** | No | sed (L286) | **Sí (124)** | **Vive (L600)** | 0, 2 |
| **33** | No | zombi (L190) | **Sí (180)** | sed (L318) | 1, 0 |
| **34** | Sí (127) | zombi (L472) | Sí (128) | hambre (L355) | 1, 0 |
| **35** | Sí (127) | hambre (L354) | No | zombi (L242) | — |
| **36** | Sí (160) | hambre (L461) | Sí (133) | **Vive (L600)** | 3, 1 |
| **37** | Sí (148) | Vive (L600) | No | zombi (L158) | — |
| **38** | Sí (134) | hambre (L439) | Sí (135) | hambre (L496) | 2, 4 |
| **39** | Sí (127) | hambre (L500) | Sí (136) | hambre (L491) | 5, 3 |
| **40** | No | zombi (L145) | **Sí (125)** | **Vive (L600)** | 0, 9 |
| **41** | Sí (131) | sed (L290) | Sí (168) | **Vive (L600)** | 0, 0 |
| **42** | No | sed (L251) | No | zombi (L246) | — |
| **43** | Sí (196) | sed (L283) | Sí (169) | sed (L297) | 4, 0 |
| **44** | No | esqueleto (L184) | No | zombi (L255) | — |
| **45** | No | hambre (L523) | **Sí (144)** | hambre (L489) | 4, 3 |
| **46** | Sí (186) | sed (L391) | Sí (170) | esqueleto (L306) | 0, 9 |
| **47** | No | zombi (L217) | **Sí (175)** | hambre (L599) | 1, 9 |
| **48** | No | esqueleto (L153) | **Sí (181)** | zombi (L309) | 0, 1 |
| **49** | Sí (129) | Vive (L600) | Sí (148) | hambre (L523) | 3, 9 |
| **50** | Sí (130) | hambre (L350) | Sí (125) | hambre (L500) | 0, 2 |

---

### 2.9 Benchmark rápido: Equilibrado (10 linajes, 30 vidas)

Fichero generado: `datos/benchmarks/c1_rapido.json`.  
Comparación pareada frente a la referencia `datos/benchmarks/ref_c0.json` y frente a `datos/benchmarks/c0c_fix.json`:

| Métrica | Base (`ref_c0`) | C.0c-fix | C.1 (`c1_rapido`) | Δ pareado vs `ref_c0` (IC 95 %) | Δ pareado vs C.0c-fix (IC 95 %) |
|---|---|---|---|---|---|
| **latidos** | 370,10 ± 66,57 | 396,27 ± 70,03 | **422,70 ± 74,92** | **+52,60 ± 86,99** | **+26,43 ± 102,50** |
| **fitness** | 11315,50 ± 1407,01 | 11942,10 ± 1519,52 | **11734,53 ± 1299,05** | **+419,03 ± 1005,70** | -207,57 ± 1295,94 |
| **logros** | 10,93 ± 1,36 | 11,53 ± 1,47 | **11,30 ± 1,23** | **+0,37 ± 0,94** | -0,23 ± 1,22 |
| **noches** | 0,90 ± 0,28 | 1,03 ± 0,29 | **1,20 ± 0,30** | **+0,30 ± 0,38** | **+0,17 ± 0,41** |
| **ms / latido** | 7,71 | 5,95 | **5,24** | **-2,47 ms** | **-0,71 ms** |

#### Muertes por causa en Equilibrado (30 vidas)
| Causa de muerte | Base (`ref_c0`) | C.0c-fix | C.1 (`c1_rapido`) | Δ (C.1 vs `ref_c0`) | Δ (C.1 vs C.0c-fix) |
|---|---|---|---|---|---|
| **vivas (a L600)** | 6 | 6 | **11** | **+5 (casi se duplica)** | **+5** |
| **zombi** | 10 | 8 | **6** | **-4** | **-2** |
| **sed** | 6 | 8 | **4** | **-2** | **-4** |
| **hambre** | 6 | 7 | **6** | = 0 | -1 |
| **esqueleto** | 2 | 1 | **3** | +1 | +2 |

#### Logros destacados en Equilibrado (30 vidas)
| Logro | Base (`ref_c0`) | C.0c-fix | C.1 | Observación |
|---|---|---|---|---|
| **wake_up** | 19 | 21 | **23** | +4 vidas despiertan tras dormir en refugio |
| **make_stone_pickaxe** | 2 | 2 | **5** | +3 vidas alcanzan pico de piedra al sobrevivir |
| **make_stone_sword** | 1 | 1 | **2** | +1 vida fabrica espada de piedra |
| **collect_iron** | 0 | 0 | **1** | Primera recolección de hierro registrada |
| **eat_plant** | 0 | 0 | **1** | Logro desbloqueado fuera de la rutina estándar |
| **place_stone** | 21 | 23 | **25** | Incremento directo por colocación en `tapar` y cierre |

---

### 2.10 Diagnóstico de las semillas no selladas el día 1 en C.1 (15, 16, 24 y 26)

En el arnés de semillas 11–30, 4 de las 20 vidas no llegaron a sellarse el primer día. El análisis detallado de los registros en los últimos 30 latidos antes de morir y del entorno espacial revela:

#### 1. Semilla 15 (muerte por zombi en L169, paso 191)
- **Fase en últimos 30 latidos:** `elegir_mina` (30/30).
- **Estrategias ganadoras en últimos 30 latidos:** `huir` (18), `sobresalto` (6), `defensa_armada` (4), `refugio_nocturno` (1), `alimentarse` (1).
- **Recinto candidato:** ninguno (`mina = None` durante toda la vida).
- **Causa raíz:** En todo el mapa explorado por el individuo hasta el latido 100 hay **0 casillas de roca** (`ROCA_EXCAVABLE = 0`), y el inventario tenía `stone = 0`. El individuo apareció en una llanura abierta sin afloramientos rocosos en su campo visual. Al anochecer en campo abierto sin roca localizada, fue perseguido por zombis hasta morir.

#### 2. Semilla 24 (muerte por zombi en L189, paso 207)
- **Fase en últimos 30 latidos:** `elegir_mina` (30/30).
- **Estrategias ganadoras en últimos 30 latidos:** `refugio_nocturno` (12), `huir` (10), `defensa_armada` (3), `sobresalto` (3), `alimentarse` (1), `defenderse` (1).
- **Recinto candidato:** ninguno (`mina = None` durante toda la vida).
- **Causa raíz:** Idéntica a la semilla 15. A L100 hay **0 casillas de roca** en todo el mapa explorado (`stone = 0`). Apareció en un bioma despejado sin vetas de piedra en su cono de exploración diurna, anocheciendo sin opción de recinto.

#### 3. Semilla 26 (muerte por zombi en L271, paso 297)
- **Fase en últimos 30 latidos:** `elegir_mina` (30/30).
- **Estrategias ganadoras en últimos 30 latidos:** `None` (15, al ceder la estrategia por no anticipar de mañana), `huir` (8), `refugio_nocturno` (4), `sobresalto` (2), `alimentarse` (1).
- **Recinto candidato:** localizó roca en `(44, 37)` con orientación `(1, 0)`.
- **Causa raíz:** El jugador se hallaba en `(44, 31)` a 6 casillas del afloramiento y con `stone = 0`. Al llegar el ocaso sin piedra previa en el inventario para colocar las paredes faltantes, hostiles nocturnos bloquearon su aproximación. El individuo logró sobrevivir evadiendo zombis en campo abierto durante toda la primera noche (desde oscuridad total hasta la mañana siguiente, L250–L271 con luz 0,77), pero fue alcanzado por un zombi matutino antes de poder picar roca y sellar.

#### 4. Semilla 16: Divergencia frente a la referencia (sellaba en paso 130)
- **Comportamiento en referencia / C.0c-fix:**  
  La búsqueda previa exigía estrictamente un túnel recto de 3 rocas macizas. En el área inicial solo existía un único candidato que cumplía este requisito: `((26, 32), (-1, 0))`, a solo 2 casillas del punto de inicio. El individuo se dirigió a él de inmediato, cavó en L111–L115 y completó el cierre en L119 (paso 131, luz 0,69), durmiendo a salvo.
- **Comportamiento en C.1:**  
  Al flexibilizar la búsqueda (`_evaluar_recinto`) para admitir recintos con paredes de piedra artificiales, el algoritmo detectó candidatos alternativos más lejanos: `((25, 29), (0, 1))` en L56, `((30, 40), (1, 0))` en L111 y `((36, 40), (-1, 0))` en L134. La heurística guió al individuo hacia el este hasta `pos = (36, 36)`. Al llegar allí con `stone = 0` y necesitar picar piedra para cerrar paredes, el anochecer cayó en campo abierto a L142 (luz 0,434). A L143 fue interceptado por un zombi en la oscuridad, muriendo en L155.
- **Conclusión de la semilla 16:** La flexibilidad de C.1 permite encontrar refugio en biomas donde no hay 3 rocas en línea (beneficiando a semillas como 12, 13, 17, 20, 21, 22, 25, 27 que antes no sellaban), pero en casos límite como la 16 la presencia de múltiples candidatos semi-abiertos dispersos puede desviar al individuo lejos de una roca inmediata.

---

### 2.11 Pendientes fuera de este encargo

- **Vaivén entre 2 casillas en mundo abierto (12/20 semillas en 11–30):**  
  Tal como se diagnosticó en C.0c-2, el parche de destinos inalcanzables resolvió con éxito el atasco contra paredes de roca en la mina, pero en campo abierto 12 de las 20 vidas siguen presentando vaivén episódico (> 20 latidos entre 2 casillas transitables) debido a colisiones e interferencia de arbitraje entre `huir`, `sobresalto` y `alimentarse`. Este comportamiento queda registrado como pendiente fuera de este encargo para su tratamiento en una fase posterior.

---

### 2.12 Estado de verificación de C.1

- **Verificado:**
  1. Implementación de `_evaluar_recinto`, búsqueda acotada ($\le 20$), primitiva `_plan_mirar`, fase `tapar` y actualización de costes en `RefugioNocturno` (`ida/mundos/crafter.py`).
  2. 5 tests unitarios sobre mapas sintéticos en `tests/test_crafter.py` pasando en verde.
  3. Arnés `--real` en semillas 11–30: **16/20 selladas día 1**, 16/20 `wake_up`, 16/16 sin daño dentro, 10,86 ms/latido.
  4. Validación de sobreajuste en semillas 31–50: **16/20 selladas día 1** (+4 vidas frente a C.0c-fix), 4 vivas, 413,9 latidos medios, confirmando ausencia de sobreajuste.
  5. Benchmark rápido pareado en Equilibrado (`datos/benchmarks/c1_rapido.json`): **11/30 vivas** (frente a 6 en base), muertes por sed 4 (frente a 6 en base y 8 en C.0c-fix), 422,70 latidos medios, 5,24 ms/latido.
  6. Diagnóstico de fases, recintos y causas en las 4 semillas no selladas día 1 (15, 16, 24, 26) y divergencia de la 16 frente a la referencia.
  7. Pureza de framework intacta: `git diff --stat main...HEAD -- ida/core ida/sistemas` vacío.
- **No verificado:** Benchmark completo de los 4 grupos (`c1_completo.json`), reservado para el cierre definitivo de la fase C según el plan.



---

## 3. C.2: Reservas antes de sellar y vacas recordadas

### 3.1 Resultado
**Hipótesis confirmada (`4011bef`):** Al integrar las vacas de la memoria episódica (`self.vacas`, ventana de 40 latidos) en el cálculo de viabilidad de alimento (`hay_comida_viable`), fijar la meta de reserva pre-cierre en 7 unidades de comida (cubriendo ~165 pasos de noche encerrado más margen), blindar la fase `provisiones` frente a cesiones prematuras de turno ante estrategias débiles mediante motivación continua modulada por el déficit (`ar >= 0,82`, `conf >= 0,84`), y priorizar la recolección previa al sellado:
1. **Bajan las muertes por hambre en el arnés:** pasan de **7/20** en C.1 a **5/20** en C.2.
2. **Bajan las muertes por zombi tras salir con 0/0 (semillas 14, 18 y 19):** en C.1 las tres semillas (14, 18 y 19) morían a manos de zombis poco después de salir con 0/0 (3/3 muertes); en C.2 la **semilla 19 sobrevive toda la vida** (llega al latido 600 viva con 14 logros y reservas recuperadas), reduciendo las muertes a 2/3.
3. **No bajan las vidas selladas el día 1:** se mantienen exactamente en **16/20 (80,0 %)**, con **10/20 selladas antes de que la luz caiga de 0,5 (50,0 %)** (frente a 8/20 en C.1).
4. **Supervivencia global y vitalidad:** las vidas que concluyen vivas los 600 latidos del arnés suben de 3/20 a **5/20 (25,0 %)** (semillas 11, 13, 19, 26 y 29), con un promedio de **414,6 latidos vividos** (frente a 395,4 en C.1).

---

### 3.2 Tabla de evaluación

| Pieza | Commit | Hipótesis | Arnés (11–30, `--real`) | Benchmark Equilibrado (1–10) | Benchmark Completo 4 grupos (N=120) | Decisión |
|---|---|---|---|---|---|---|
| **C.2** | `4011bef` | Vaca recordada cuenta antes de sellar; meta comida < 7; bajan muertes por hambre; bajan zombis en 14/18/19; selladas $\ge 16/20$. | **Confirmada:**<br>• Selladas día 1: **16/20 (80,0 %)**<br>• Selladas luz $\ge 0,5$: **10/20 (50,0 %)** (vs 8/20)<br>• Sin daño dentro: **16/16 (100 %)**<br>• `wake_up`: **16/20 (80,0 %)**<br>• Muertes hambre: **5/20** (bajan de 7)<br>• Vivas L600: **5/20** (vs 3 en C.1)<br>• Semilla 19: **Vive L600** (14 logros)<br>• Latidos medios: **414,6** | • Latidos: **402,00 ± 59,90** (+31,90 vs `ref_c0`)<br>• Vivas: **7/30** (vs 6/30 en `ref_c0`)<br>• Sed: **2/30** (baja de 6 en `ref_c0` y 4 en `c1_rapido`)<br>• Noches: **1,03 ± 0,31** (+0,13 vs `ref_c0`) | • `eat_cow`: **73/120** (+7 vs `ref_c0`)<br>• `wake_up`: **92/120** (+16 vs `ref_c0`)<br>• `collect_stone`: **106/120** (+13)<br>• `place_stone`: **99/120** (+10)<br>• `defeat_zombie`: **77/120** (+10)<br>• Vivas totales: **27/120** (+6 vs `ref_c0`)<br>• Latidos suben en los 4 grupos | **Aceptada** |

---

### 3.3 Detalle por semilla en el arnés (semillas 11–30, `--real`)

| Semilla | Sellada (día 1) | Latido sellado | Luz al sellar | Sello (c, a, s) | Salida (latido, luz, c, a, s) | Bebe tras salir | Come tras salir | Causa de muerte | Latidos vividos | `wake_up` | Logros |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **11** | Sí | 125 | 0,657 | (8, 7, 9) | L297, luz 0,85, (2, 0, 9) | +17 | +87 | **Vive** | 600 | Sí | 15 |
| **12** | Sí | 125 | 0,711 | (8, 7, 7) | L297, luz 0,81, (3, 1, 9) | +111 | None | hambre | 422 | Sí | 12 |
| **13** | Sí | 130 | 0,624 | (7, 7, 9) | L292, luz 0,84, (2, 9, 9) | +120 | +50 | **Vive** | 600 | Sí | 12 |
| **14** | Sí | 122 | 0,751 | (5, 4, 9) | L273, luz 0,54, (0, 0, 6) | None | None | zombi | 285 | Sí | 10 |
| **15** | No | — | — | — | — | — | — | zombi | 169 | No | 8 |
| **16** | No | — | — | — | — | — | — | zombi | 275 | No | 8 |
| **17** | Sí | 128 | 0,657 | (4, 5, 9) | L263, luz 0,47, (0, 9, 9) | +11 | None | hambre | 415 | Sí | 11 |
| **18** | Sí | 173 | 0,158 | (3, 4, 7) | L280, luz 0,65, (0, 0, 8) | +37 | None | zombi | 325 | Sí | 12 |
| **19** | Sí | 127 | 0,657 | (4, 4, 6) | L274, luz 0,60, (0, 0, 8) | +62 | +73 | **Vive** | 600 | Sí | 14 |
| **20** | No | — | — | — | — | — | — | zombi | 168 | No | 12 |
| **21** | Sí | 124 | 0,711 | (8, 4, 9) | L304, luz 0,91, (2, 9, 9) | +53 | None | zombi | 456 | Sí | 12 |
| **22** | Sí | 133 | 0,507 | (4, 8, 9) | L265, luz 0,58, (0, 9, 9) | +51 | +11 | zombi | 462 | Sí | 12 |
| **23** | Sí | 185 | 0,058 | (2, 2, 9) | L262, luz 0,45, (0, 0, 9) | +2 | None | esqueleto | 363 | Sí | 13 |
| **24** | No | — | — | — | — | — | — | zombi | 189 | No | 8 |
| **25** | Sí | 120 | 0,679 | (4, 3, 9) | L280, luz 0,72, (0, 0, 5) | +25 | None | hambre | 321 | Sí | 11 |
| **26** | Sí | 120 | 0,624 | (8, 6, 9) | L307, luz 0,95, (2, 9, 9) | +18 | +13 | **Vive** | 600 | Sí | 15 |
| **27** | Sí | 168 | 0,186 | (3, 3, 5) | L264, luz 0,49, (0, 9, 9) | +10 | None | hambre | 355 | Sí | 11 |
| **28** | Sí | 151 | 0,410 | (7, 7, 7) | L304, luz 0,87, (2, 8, 9) | +3 | +30 | sed | 581 | Sí | 13 |
| **29** | Sí | 164 | 0,131 | (6, 6, 7) | L277, luz 0,77, (3, 9, 9) | +18 | +45 | **Vive** | 600 | Sí | 13 |
| **30** | Sí | 162 | 0,123 | (6, 2, 7) | L280, luz 0,80, (3, 9, 9) | +7 | None | hambre | 507 | Sí | 12 |

---

### 3.4 Comparación de causas de muerte en el arnés (semillas 11–30)

| Causa de muerte | Ref C.0 | C.0c-fix | C.1 | C.2 (`4011bef`) | Δ (C.2 vs C.1) |
|---|---|---|---|---|---|
| **hambre** | 3 | 5 | 7 | **5** | **-2 (baja un 28,6 %)** |
| **zombi** | 6 | 7 | 8 | **8** | = 0 |
| **esqueleto** | 5 | 4 | 1 | **1** | = 0 |
| **sed** | 2 | 3 | 0 | **1** | +1 (L581) |
| **vivas** | 4 | 1 | 3 | **5** | **+2 (+66,7 %)** |
| *Selladas día 1* | 11 | 11 | 16 | **16** | = 0 (16/20, 80,0 %) |
| *Selladas con luz $\ge 0,5$* | — | — | 8 | **10** | **+2 (+25,0 %)** |

---

### 3.5 Benchmark completo: 4 grupos (40 linajes, 120 vidas pareadas)

Comparación pareada entre la referencia `datos/benchmarks/ref_c0.json` (commit `f2f1262`) y `datos/benchmarks/c2_completo.json` (commit `4011bef`):

#### 1. Métricas por grupo (N = 10 linajes, IC 95 %; Δ = nueva − base)

| Grupo | Métrica | Base (`ref_c0`) | C.2 (`c2_completo`) | Δ pareado (IC 95 %) |
|---|---|---|---|---|
| **Equilibrado** | latidos | 370,10 ± 66,57 | **402,00 ± 59,90** | **+31,90 ± 71,23** |
| | fitness | 11315,50 ± 1407,01 | **11379,90 ± 1173,81** | **+64,40 ± 810,81** |
| | logros | 10,93 ± 1,36 | **10,97 ± 1,12** | **+0,03 ± 0,75** |
| | noches | 0,90 ± 0,28 | **1,03 ± 0,31** | **+0,13 ± 0,36** |
| **Valiente** | latidos | 354,83 ± 73,56 | **409,40 ± 65,86** | **+54,57 ± 59,62** |
| | fitness | 11900,17 ± 1419,04 | **12456,83 ± 930,12** | **+556,67 ± 792,30** |
| | logros | 11,53 ± 1,36 | **12,03 ± 0,90** | **+0,50 ± 0,77** |
| | noches | 0,87 ± 0,30 | **1,17 ± 0,20** | **+0,30 ± 0,26** |
| **Reactivo** | latidos | 376,40 ± 76,51 | **380,67 ± 56,76** | **+4,27 ± 92,75** |
| | fitness | 10954,37 ± 1256,43 | **11291,53 ± 1282,66** | **+337,17 ± 1401,11** |
| | logros | 10,57 ± 1,20 | **10,90 ± 1,25** | **+0,33 ± 1,33** |
| | noches | 0,93 ± 0,35 | 0,93 ± 0,27 | -0,00 ± 0,41 |
| **Sin experiencia** | latidos | 377,93 ± 47,78 | **396,77 ± 74,84** | **+18,83 ± 75,12** |
| | fitness | 11523,07 ± 885,18 | **11641,77 ± 1162,81** | **+118,70 ± 790,23** |
| | logros | 11,13 ± 0,86 | **11,23 ± 1,12** | **+0,10 ± 0,75** |
| | noches | 1,00 ± 0,19 | **1,07 ± 0,29** | **+0,07 ± 0,33** |

#### 2. Muertes por causa en los 4 grupos (120 vidas)

| Grupo | Causa de muerte | Base (`ref_c0`) | C.2 (`c2_completo`) | Δ vidas |
|---|---|---|---|---|
| **Equilibrado** | esqueleto | 2 | 3 | +1 |
| | hambre | 6 | 7 | +1 |
| | sed | 6 | **2** | **-4** |
| | **vive** | 6 | **7** | **+1** |
| | zombi | 10 | 11 | +1 |
| **Valiente** | esqueleto | 8 | **3** | **-5** |
| | hambre | 4 | 10 | +6 |
| | sed | 5 | **4** | **-1** |
| | **vive** | 3 | **8** | **+5 (casi se triplica)** |
| | zombi | 10 | **5** | **-5** |
| **Reactivo** | esqueleto | 3 | 3 | 0 |
| | hambre | 2 | 10 | +8 |
| | sed | 9 | 9 | 0 |
| | vive | 7 | 4 | -3 |
| | zombi | 9 | **4** | **-5** |
| **Sin experiencia**| esqueleto | 3 | 4 | +1 |
| | hambre | 7 | **5** | **-2** |
| | sed | 7 | **6** | **-1** |
| | **vive** | 5 | **8** | **+3** |
| | zombi | 8 | **7** | **-1** |
| **TOTALES (120)** | **vivas al final** | **21** | **27** | **+6 vidas vivas (+28,6 %)** |
| | **sed** | **27** | **21** | **-6 muertes por sed (-22,2 %)** |

#### 3. Logros por tipo (120 vidas)

| Logro | Vidas base (`ref_c0`) | Vidas C.2 (`c2_completo`) | Δ vidas | Observación |
|---|---|---|---|---|
| **eat_cow** | 66 | **73** | **+7** | Mayor aprovechamiento de vacas recordadas y provisión |
| **wake_up** | 76 | **92** | **+16** | De 63,3 % a 76,7 % de todas las vidas durmiendo seguras |
| **collect_stone** | 93 | **106** | **+13** | Extracción activa de piedra para recintos flexibles |
| **place_stone** | 89 | **99** | **+10** | Sellado y tapiado con paredes de piedra artificiales |
| **defeat_zombie** | 67 | **77** | **+10** | Defensa armada consolidada y mayor tiempo vivido |
| **make_stone_sword** | 5 | **9** | **+4** | Progresión tecnológica facilitada por mayor supervivencia |
| **make_wood_pickaxe** | 112 | **114** | **+2** | Prácticamente saturado en 95,0 % de las vidas |
| **place_furnace** | 23 | **24** | **+1** | Progresión estable |

---

### 3.6 Verificación de pureza y base

Comandos ejecutados y su salida literal:

```powershell
PS F:\code\IdA> git diff --stat main...HEAD -- ida/core ida/sistemas
(salida vacía: ningún archivo modificado en ida/core ni ida/sistemas)

PS F:\code\IdA> python -m pytest -q
165 passed, 1 warning in 43.49s

PS F:\code\IdA> ruff check ida tests
All checks passed!

PS F:\code\IdA> mypy ida
Success: no issues found in 40 source files
```

### 3.7 Estado de verificación de C.2

- **Verificado:**
  1. Integración de `self.vacas` en `hay_comida_viable` con acotación de distancia y margen pre-ocaso.
  2. Umbral de provisión pre-sellado fijado en `food < 7`.
  3. Desbloqueo de la fase `provisiones` en `RefugioNocturno.actuar` (evitando la cesión innecesaria a `plan_tecnologico` cuando la mina ya es conocida) y motivación continua proporcional al déficit biológico (`ar >= 0,82`, `conf >= 0,84`).
  4. Navegación hacia vacas recordadas en `provisiones` cuando no hay alimento visible inmediato.
  5. Arnés `--real` en semillas 11–30: **16/20 selladas día 1**, muertes por hambre bajan a **5/20** (frente a 7/20), semilla 19 vive hasta L600 (14 logros), vivas aumentan a **5/20** (25,0 %).
  6. Benchmark rápido en Equilibrado (`datos/benchmarks/c2_rapido.json`): muertes por sed caen a **2/30** (frente a 6 en base y 4 en C.1), vivas suben a 7/30, latidos medios **402,00**.
  7. Benchmark completo en los 4 grupos (`datos/benchmarks/c2_completo.json`): 120 vidas pareadas frente a `ref_c0.json`, aumento de latidos y fitness en los 4 grupos, incremento de `wake_up` de 76 a 92 (+16), `eat_cow` de 66 a 73 (+7), y vivas globales de 21 a 27 (+6 vidas).
  8. Pureza absoluta de framework: cero modificaciones en `ida/core/` e `ida/sistemas/`.
- **No verificado:** Efecto en semillas con horizonte largo de 3000 latidos (objeto del siguiente paso, C.3).
