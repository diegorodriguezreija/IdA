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

## 3. C.2: Reservas antes de sellar y vacas recordadas (Rechazada y revertida)

### 3.1 Hipótesis y planteamiento
**Hipótesis:** Si la vaca recordada de la memoria episódica (`self.vacas`, ventana de 40 latidos) cuenta como comida alcanzable antes de sellar, la meta de comida pre-cierre se fija en cubrir la noche (`food < 7`, unas 6 unidades para ~165 pasos nocturnos más 1 de margen), y se modula la motivación de `provisiones` de forma continua proporcional al déficit biológico (`ar >= 0,82`, `conf >= 0,84`), el individuo sellará con mayores reservas de alimento.
Consecuencias esperadas:
1. Bajan las muertes por hambre en el arnés (frente a 7/20 en C.1).
2. Bajan las muertes por zombi tras salir con 0/0 (semillas 14, 18 y 19).
3. No bajan las vidas selladas el día 1 (16/20).

---

### 3.2 Tabla de evaluación

| Pieza | Commit | Hipótesis | Arnés (11–30, `--real`) | Validación (31–50, `--real`) | Benchmark Equilibrado vs C.1 (`c1_rapido`) | Decisión |
|---|---|---|---|---|---|---|
| **C.2** | `4011bef` | Vaca recordada viable; meta food < 7; bajan muertes por hambre y zombis en 14/18/19; selladas día 1 $\ge 16/20$. | • Selladas día 1: **16/20 (80,0 %)**<br>• Selladas luz $\ge 0,5$: **10/20 (50,0 %)**<br>• Sin daño dentro: **16/16 (100 %)**<br>• Muertes hambre: **5/20** (bajan de 7)<br>• Vivas L600: **5/20** (vs 4 en C.1)<br>• Semilla 19: **Vive L600** (14 logros) | • Selladas día 1: **14/20 (70,0 %)** (cae de 16/20 en C.1)<br>• Hambre + Sed: **10/20** (5+5, igual a 7+3 en C.1, **no baja**)<br>• Vivas L600: **3/20** (cae de 4/20 en C.1)<br>• Comida media al sellar: **5,71** | • Latidos: **-20,70 ± 58,84** (402,00 vs 422,70)<br>• Fitness: **-354,63 ± 849,47**<br>• Logros: **-0,33 ± 0,80**<br>• Noches: **-0,17 ± 0,26**<br>• Vivas: **7/30** (vs 11/30 en C.1)<br>• Hambre: 7 vs 6; Sed: 2 vs 4; Zombi: 11 vs 6 | **Rechazada y revertida** (`git revert 4011bef`). No cumple la regla de validación en 31–50. |

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
| **vivas** | 4 | 1 | **4** | **5** | **+1 (+25,0 %)** |
| *Selladas día 1* | 11 | 11 | 16 | **16** | = 0 (16/20, 80,0 %) |
| *Selladas con luz $\ge 0,5$* | — | — | 8 | **10** | **+2 (+25,0 %)** |

*Corrección de coherencia:* Se corrige el dato de vidas vivas de C.1 en la tabla 3.4, reflejando las **4 vidas vivas** reales constatadas en la tabla 2.4 (semillas 11, 20, 21 y 28).

---

### 3.5 Benchmark rápido: Comparación pareada C.1 vs C.2 en Equilibrado (10 linajes, 30 vidas)

Comando: `python herramientas/benchmark.py comparar datos/benchmarks/c1_rapido.json datos/benchmarks/c2_rapido.json`

| Métrica | C.1 (`c1_rapido`) | C.2 (`c2_rapido`) | Δ pareado (IC 95 %) |
|---|---|---|---|
| **latidos** | 422,70 ± 74,92 | **402,00 ± 59,90** | -20,70 ± 58,84 |
| **fitness** | 11734,53 ± 1299,05 | **11379,90 ± 1173,81** | -354,63 ± 849,47 |
| **logros** | 11,30 ± 1,23 | **10,97 ± 1,12** | -0,33 ± 0,80 |
| **noches** | 1,20 ± 0,30 | **1,03 ± 0,31** | -0,17 ± 0,26 |
| **ms / latido** | 5,24 | 5,39 | +0,15 ms |

#### Muertes por causa en Equilibrado (30 vidas pareadas)
| Causa de muerte | C.1 (`c1_rapido`) | C.2 (`c2_rapido`) | Δ vidas |
|---|---|---|---|
| **vivas (a L600)** | **11** | 7 | **-4** |
| **zombi** | 6 | **11** | **+5** |
| **hambre** | 6 | **7** | +1 |
| **sed** | 4 | **2** | **-2** |
| **esqueleto** | 3 | 3 | = 0 |

---

### 3.6 Validación en semillas no vistas (semillas 31–50, `--real`, N = 20)

Ejecución pareada en semillas 31–50 con el arnés `--real` (600 latidos, perfil Equilibrado) entre **C.1** (`e0b5c7f`) y **C.2** (`4011bef`):

| Métrica (semillas 31–50) | C.1 (`e0b5c7f`) | C.2 (`4011bef`) | Δ (C.2 vs C.1) |
|---|---|---|---|
| **Vidas selladas día 1** | **16/20 (80,0 %)** | 14/20 (70,0 %) | **-2 vidas (-10,0 %)** |
| **Vivas al final (a L600)** | **4/20 (20,0 %)** | 3/20 (15,0 %) | **-1 vida (-5,0 %)** |
| **Muertes por hambre** | 7 | 5 | -2 |
| **Muertes por sed** | 3 | 5 | +2 |
| **Total muertes hambre + sed** | **10/20 (50,0 %)** | **10/20 (50,0 %)** | **= 0 (no baja)** |
| **Muertes por zombi** | 5 | 6 | +1 |
| **Muertes por esqueleto** | 1 | 1 | = 0 |
| **Latidos medios vividos** | **413,9** | 381,9 | -32,0 latidos |
| **Comida media al sellar (selladas)** | 5,19 | **5,71** | +0,52 |

#### Detalle por semilla en semillas 31–50 (C.2)
- **Selladas día 1 (14/20):** Semillas 31 (L140, sello 7/2/7), 32 (L123, sello 8/7/9), 34 (L120, sello 8/8/9), 36 (L127, sello 8/7/9), 37 (L117, sello 8/3/9), 38 (L133, sello 4/8/9), 39 (L121, sello 8/8/9), 40 (L117, sello 5/7/9), 43 (L157, sello 6/1/9), 45 (L123, sello 4/6/9), 46 (L167, sello 3/1/8), 48 (L124, sello 8/9/9), 49 (L133, sello 7/6/9), 50 (L150, sello 3/6/6).
- **No selladas día 1 (6/20):** Semillas 33 (sed L224, sin sellar), 35 (zombi L242, sin sellar), 41 (sed L297, sin sellar; en C.1 sellaba en paso 168 y vivía L600), 42 (zombi L246, sin sellar), 44 (zombi L274, sin sellar), 47 (zombi L190, sin sellar; en C.1 sellaba en paso 175 y llegaba a L599).

---

### 3.7 Diagnóstico de la semilla 20 (muerte en L168 en C.2 vs vive L600 en C.1)

En C.1, la semilla 20 sellaba en el paso 157 (latido 151) con comida 7 y agua 5, salía por la mañana a L270 y sobrevivía hasta el final (600 latidos, 13 logros). En C.2, muere en L168 por zombi sin sellar.

#### Traza de los 40 latidos previos a la muerte en C.2 (L128–L168)
- **L128–L133:** Fase `elegir_mina`, ejecutada `refugio_nocturno`, motivo `ir a la mina elegida`. Se aproxima a la mina `((17, 30), (-1, 0))`.
- **L134–L136:** Fase `tapar`, ejecutada `refugio_nocturno`, motivo `ir a posición de orientación para tapar` y `orientarse para tapar pared`. Coloca la piedra a L136.
- **L137–L142:** Fase `cerrarse`, ejecutada `refugio_nocturno`. A L137 un zombi aparece junto a la entrada. `RefugioNocturno` emite `refugio: despejar zombi` con la espada. El combate le inflige daño, cayendo la salud de 9 a 5 en L137 y a 3 en L141.
- **L143–L159 (17 latidos):** Fase `cerrarse` en `RefugioNocturno`, pero la estrategia ejecutada por el Tribunal pasa a ser **`huir` (S1)** (`motivo: huir de zombi`). Al bajar la salud a 3, el miedo homeostático dispara la motivación de `huir`, usurpando el control durante 17 latidos consecutivos y arrastrando al individuo 14 casillas campo abierto en plena noche (luz 0,47 $\to$ 0,28).
- **L160–L162:** `RefugioNocturno` recupera el control brevemente intentando regresar (`entrar al recinto para cerrar`).
- **L163:** Reflejo de `sobresalto`.
- **L165–L168:** `huir` vuelve a tomar el control en plena oscuridad exterior hasta que el individuo es abatido en `pos = (0, 29)` a L168.

#### ¿La retiene `provisiones`?
**NO.** La fase `provisiones` **no estuvo activa en ningún momento de los 40 latidos previos a la muerte** (el inventario tenía comida 7–8 y agua 6–7). La divergencia provino de una sutil diferencia de ruta diurna que retrasó la finalización de `tapar` en 5 latidos, coincidiendo con la aparición de un zombi en la boca de entrada en el instante exacto del crepúsculo. Al recibir daño (salud $\le 3$), `huir` usurpó el Tribunal y lo alejó del refugio.

---

### 3.8 Decisión sobre C.2

**Regla de decisión:**
> Se mantiene C.2 si en 31–50 bajan las muertes por hambre + sed frente a C.1 y las vivas no bajan. Si no, `git revert 4011bef` y se anota como resultado negativo, con la explicación de c).

**Evaluación de los criterios en semillas 31–50:**
1. **Muertes por hambre + sed:** 10 en C.1 (7 hambre + 3 sed) vs **10 en C.2** (5 hambre + 5 sed). **No bajan.**
2. **Vivas a L600:** 4 en C.1 (20,0 %) vs **3 en C.2** (15,0 %). **Bajan (-1 vida).**
3. **Vidas selladas el día 1:** 16 en C.1 (80,0 %) vs **14 en C.2** (70,0 %). **Bajan (-2 vidas).**
4. **Benchmark rápido Equilibrado:** vivas caen de 11 a 7; latidos caen de 422,70 a 402,00.

**Veredicto:**  
C.2 no supera el criterio de validación en semillas no vistas (31–50) y degrada la supervivencia en el benchmark rápido frente a C.1. Se procede a ejecutar **`git revert 4011bef`**, registrando C.2 como resultado negativo y restableciendo **C.1 (`e0b5c7f`)** como la base firme y congelada para C.3.

---

## 4. C.3: Línea base de horizonte largo (3000 latidos)

### 4.1 Resumen y objetivo
Se establece la línea base de horizonte largo sobre la base congelada de **C.1** (`e0b5c7f` / `1afe8f6`) ejecutando el arnés con `--latidos 3000` y motivación real (`--real`, perfil Equilibrado) en las semillas 11–20.  
El objetivo es caracterizar cuantitativamente los cuellos de botella de supervivencia a largo plazo y contrastar el supuesto **S4** («una vez superada la primera noche, el límite fundamental es la comida»).

- **Comando exacto:**
  ```powershell
  $t0 = Get-Date; & "C:\Users\diego\AppData\Local\Python\pythoncore-3.15-64\python.exe" herramientas/arnes_refugio_crafter.py --semillas 11 12 13 14 15 16 17 18 19 20 --latidos 3000 --real --salida datos/benchmarks/c3_largo.json; $t1 = Get-Date; Write-Host "Tiempo: $(($t1 - $t0).TotalSeconds) s"
  ```
- **Tiempo de ejecución:** **44,15 s** (10 vidas, 391,2 latidos medios).
- **Fichero de volcado:** `datos/benchmarks/c3_largo.json`.

---

### 4.2 Métricas agregadas de horizonte largo

| Métrica | Valor C.3 (semillas 11–20) |
|---|---|
| **Vidas vivas a L3000** | **0/10 (0,0 %)** |
| **Latidos medios vividos** | **391,2** (máx. 653 en sem. 11, mín. 155 en sem. 16) |
| **Causas de muerte** | **hambre: 5/10 (50,0 %)**, **zombi: 5/10 (50,0 %)** |
| **Noches superadas totales** | **10 noches** (media 1,0 por vida; 2 vidas superan 2 noches) |
| **Vidas selladas el día 1** | **8/10 (80,0 %)** (sin daño dentro: 8/8, 100 %) |
| **Refugios usados totales en noches** | **12 noches de refugio** |
| **Refugio repetido vs cambiado (noches $\ge 1$)** | **3 repetidos / 1 cambiado (75,0 % repetición)** |
| **Refugios con hierba lateral de $e_2$ o $e_3$** | **0/12 noches (0,0 %)** |
| **Días con distancia máxima al refugio previo $< 18$** | **16/18 días evaluados (88,9 %)** |
| **Plantas comidas (`eat_plant`)** | **0 en todos los días de todas las vidas** |
| **Vacas comidas totales** | **11 vacas** (media 1,1 por vida; 0 en el día 2) |

---

### 4.3 Detalle por vida (semillas 11–20)

| Semilla | Latidos | Estado final | Noches superadas | Mín. comida / agua por día | Fuentes comida por día (vaca / planta) | Refugios usados cada noche `(e0, d)` | Max dist al refugio previo |
|---|---|---|---|---|---|---|---|
| **11** | 653 | muerte por **hambre** | 2 | d0: 3 / 6<br>d1: 0 / 6<br>d2: 0 / 8 | d0: 1 v / 0 p<br>d1: 1 v / 0 p<br>d2: 0 v / 0 p | • n0: `((26, 41), (-1, 0))` (día 0)<br>• n1: `((35, 36), (1, 0))` (cambia, dist=14) | d0: 9<br>d1: 19<br>d2: 15 |
| **12** | 441 | muerte por **hambre** | 1 | d0: 3 / 1<br>d1: 0 / 0 | d0: 1 v / 0 p<br>d1: 0 v / 0 p | • n0: `((24, 34), (0, -1))` (día 0)<br>• n1: `((24, 34), (0, -1))` (**repite**, dist=0) | d0: 1<br>d1: 14 |
| **13** | 479 | muerte por **hambre** | 1 | d0: 2 / 6<br>d1: 0 / 5 | d0: 1 v / 0 p<br>d1: 0 v / 0 p | • n0: `((20, 38), (-1, 0))` (día 0)<br>• n1: `((20, 38), (-1, 0))` (**repite**, dist=0) | d0: 1<br>d1: 2 |
| **14** | 311 | muerte por **zombi** | 1 | d0: 0 / 0<br>d1: 0 / 0 | d0: 0 v / 0 p<br>d1: 0 v / 0 p | • n0: `((35, 37), (1, 0))` (día 0) | d0: 12<br>d1: 19 |
| **15** | 169 | muerte por **zombi** | 0 | d0: 2 / 2 | d0: 0 v / 0 p | Ninguno (no selló) | Ninguno |
| **16** | 155 | muerte por **zombi** | 0 | d0: 3 / 3 | d0: 0 v / 0 p | Ninguno (no selló) | Ninguno |
| **17** | 428 | muerte por **hambre** | 1 | d0: 1 / 6<br>d1: 0 / 6 | d0: 1 v / 0 p<br>d1: 0 v / 0 p | • n0: `((15, 27), (0, -1))` (día 0) | d0: 12<br>d1: 16 |
| **18** | 325 | muerte por **zombi** | 1 | d0: 0 / 0<br>d1: 0 / 0 | d0: 0 v / 0 p<br>d1: 0 v / 0 p | • n0: `((31, 24), (0, -1))` (día 0) | d0: 1<br>d1: 9 |
| **19** | 315 | muerte por **zombi** | 1 | d0: 0 / 0<br>d1: 0 / 0 | d0: 0 v / 0 p<br>d1: 0 v / 0 p | • n0: `((26, 24), (-1, 0))` (día 0) | d0: 1<br>d1: 14 |
| **20** | 636 | muerte por **hambre** | 2 | d0: 3 / 0<br>d1: 1 / 0<br>d2: 0 / 2 | d0: 2 v / 0 p<br>d1: 2 v / 0 p<br>d2: 0 v / 0 p | • n0: `((23, 9), (-1, 0))` (día 0)<br>• n1: `((23, 9), (-1, 0))` (**repite**, dist=0) | d0: 1<br>d1: 9<br>d2: 12 |

---

### 4.4 Conclusión sobre el supuesto S4

> **Supuesto S4:** «Una vez superada la noche, el límite es la comida».

Los datos empíricos de C.3 confirman de forma rotunda el supuesto S4:
1. **La barrera temporal infranqueable (~650 latidos):**  
   Ningún individuo de la muestra supera el latido 653. La longevidad máxima observada fue de 653 latidos (semilla 11) y 636 latidos (semilla 20).
2. **Causa de muerte tras superar la noche:**  
   - En la primera noche (L $\le$ 300), solo mueren 2 vidas (semillas 15 y 16) por no completar a tiempo el recinto frente a monstruos.
   - Las 8 vidas restantes superan la primera noche de forma intacta (sin daño nocturno, con `wake_up`).
   - Al abrir la salida al amanecer (L300–L325), 3 vidas (14, 18, 19) son sorprendidas por zombis diurnos debido a que salieron con comida 0, agua 0 y salud mermada.
   - Para **todas las vidas que sobreviven a la salida del primer refugio** (L > 330: semillas 11, 12, 13, 17 y 20), **el 100 % muere de hambre**.
3. **Agotamiento de la fauna y ausencia de agricultura:**  
   - En el Día 0 se cazan entre 1 y 2 vacas por individuo. En el Día 1 la disponibilidad cae drásticamente (1 o 0 vacas). En el Día 2, **las vacas cazadas son 0 en todas las vidas supervivientes**.
   - El consumo de plantas (`eat_plant`) es exactamente **0** en todos los días de todas las vidas.
   - El nivel mínimo de comida desciende inexorablemente a 0 en el Día 1 o 2, provocando la inanición.

---

### 4.5 Hallazgos clave y base de referencia para C.4

1. **Permanencia espacial en radio de cultivo ($< 18$ casillas):**  
   En Crafter, los cultivos (`Plant`) solo actualizan su ciclo biológico de crecimiento si el jugador se encuentra a una distancia Manhattan $< 18$ casillas (`player.distance(obj) < 2 * max(view) = 18`).  
   En la medición diaria de C.3, los individuos permanecen en un radio $< 18$ de su refugio en el **88,9 % de los días** (16 de 18 días). En las vidas con mayor longevidad (12, 13, 20), la distancia máxima al refugio se mantiene en $\le 14$ casillas durante toda la existencia. Esto demuestra que un huerto ubicado en las paredes del refugio crecería de manera regular y sostenida sin requerir restricciones artificiales de movimiento.
2. **Alta fidelidad de hábitat (repetición de refugio):**  
   En las 4 vidas que alcanzaron una segunda noche con refugio (11, 12, 13, 20), **el 75 % (3/4) reutilizó exactamente el mismo refugio** de la noche anterior (`distancia = 0`). El mecanismo de memoria y retorno (`mina_recordada` y `memoria.recordar_lugar`) ya funciona de forma natural.
3. **Necesidad de incentivar nichos de hierba en `_evaluar_recinto`:**  
   Los 12 refugios utilizados se excavaron en formaciones rocosas puras sin bloques de hierba en las paredes laterales de $e_2$ o $e_3$ (**0 % de refugios con hierba lateral**). Para que C.4 sea efectivo, `_evaluar_recinto` debe incluir un incentivo positivo por cada lateral de hierba candidata a nicho huerto, canalizando la selección del refugio hacia recintos con suelo cultivable protegido.

---

## 5. C.3b: Patrulla de forrajeo (vacas que se reponen)

### 5.1 Paso 1: Diagnóstico de presencia real de vacas en el área de campeo

Se ejecutó un diagnóstico observacional sin alterar el código de toma de decisiones (`ida/`), midiendo en el arnés largo (`--real`, semillas 11–20, `--latidos 3000`) cada 50 latidos:
1. Vacas que existen realmente a $\le 17$ del recinto de la última noche (lectura del mundo).
2. Vacas percibidas por el individuo en esa ventana de 50 latidos (`Exterocepcion`).
3. Casillas a $\le 17$ del recinto no visitadas en los últimos 150 latidos.

- **Comando exacto:**
  ```powershell
  $t0 = Get-Date; & "C:\Users\diego\AppData\Local\Python\pythoncore-3.15-64\python.exe" herramientas/diagnostico_vacas_c3b.py --semillas 11 12 13 14 15 16 17 18 19 20 --latidos 3000; $t1 = Get-Date; Write-Host "Tiempo: $(($t1 - $t0).TotalSeconds) s"
  ```
- **Tiempo de ejecución:** **42,38 s** (49 ventanas de 50 latidos con recinto activo).

#### Resultados agregados del diagnóstico
- **Vacas reales a $\le 17$ del recinto (en cada momento, media por foto):** **1,68** vacas tras la noche 1 (1,76 global).
- **Vacas percibidas por el individuo (en cada ventana de 50 latidos):** **1,36** vacas tras la noche 1 (1,10 global), lo que representa el **81,0 %** de las vacas presentes.
- **Casillas a $\le 17$ no visitadas hace $> 150$ latidos:** **96,5 %**.

#### Conclusión del Paso 1
> **¿Existen vacas en el área de campeo que no ve?**  
> En cada instante hay de media ~1,7 vacas reales a $\le 17$ del recinto, y el individuo percibe en cada ventana de 50 latidos una media de 1,36 vacas (el 81 %). La conclusión empírica es que **las ve y no se las come**. No es que las vacas no existan o que queden ocultas sin percibir; están en su campo perceptual pero el individuo no las abate sistemáticamente.  
> Se procedió a implementar el Paso 2 para evaluar el efecto de la patrulla acotada a $\le 17$ y la caducidad de visitadas.

---

### 5.2 Paso 2: Implementación de la patrulla

**Hipótesis:** Si las casillas visitadas caducan a los 150 latidos y la exploración cuando no hay comida conocida se restringe a $\le 17$ del recinto recordado, el individuo patrulla el área de campeo, detecta las vacas que se reponen y aumenta las vacas comidas y los latidos vividos en horizonte largo.

**Cambios en `ida/mundos/crafter.py`:**
1. `self.visitadas` pasa de `Set[Pos]` a `Dict[Pos, int]` (mapeando posición al último latido de visita).
2. Se introduce la caducidad `CADUCIDAD_VISITADA = 150`: una casilla vuelve a contar como «no visitada» si han transcurrido más de 150 latidos desde la última visita (`_es_visitada`).
3. En `_abastecer` y `provisiones`, cuando no hay comida conocida alcanzable, `_explorar_con_rumbo` recibe el centro interior del recinto (`e2`) y restringe las propuestas de movimiento y destinos BFS a casillas con `_dist(c, e2) <= 17`. Si el individuo se encontrara fuera de ese radio, un paso hacia `e2` lo retorna a la zona de campeo.
4. Se actualiza el test de inicialización en `tests/test_crafter.py` (`assert refugio.visitadas == {}`) y se añaden pruebas unitarias de caducidad.

---

### 5.3 Verificación empírica

#### 1. Arnés largo (semillas 11–20, `--latidos 3000`, `--real`) frente a `c3_largo.json`

| Métrica | C.3 (Línea base) | C.3b (Patrulla) | Δ (C.3b vs C.3) |
|---|---|---|---|
| **Latidos medios vividos** | 391,2 | **418,4** | **+27,2 latidos** |
| **Vacas comidas totales** | 11 | **13** | **+2 vacas** |
| **Noches superadas totales** | 10 | **11** | **+1 noche** |
| **Fidelidad de hábitat (repetición refugio)** | 3 / 4 (75,0 %) | **4 / 5 (80,0 %)** | +5,0 % |
| **Semilla 17 (latidos)** | 428 (muerte L428, d1: 0 vacas) | **697 (muerte L697, d1: 2 vacas)** | **+269 latidos (+62,9 %)** |

- **Análisis crítico del arnés largo:** La subida de latidos (+27,2) se debe casi por completo a una única vida, la **semilla 17** (+269 latidos, que caza 2 vacas en el día 1). En el resto de las 9 semillas, la supervivencia y las vacas cazadas permanecen prácticamente idénticas (las vacas totales pasan de 11 a 13 solo por esa semilla).

#### 2. Arnés de 600 latidos (semillas 11–30, `--real`)

| Métrica | C.1 Base | C.3b Patrulla | Criterio / Estado |
|---|---|---|---|
| **Vidas selladas día 1** | **16/20 (80,0 %)** | **16/20 (80,0 %)** | $\ge 16/20$ (**Cumplido**) |
| **Selladas sin daño dentro** | 16/16 (100 %) | 16/16 (100 %) | 100 % (**Cumplido**) |
| **Vivas a L600** | 4/20 (20,0 %) | **5/20 (25,0 %)** | **+1 vida viva** |
| **Latidos medios** | 398,2 | **414,6** | **+16,4 latidos** |
| **Logros medios** | 11,50 | **11,65** | +0,15 logros |

#### 3. Benchmark rápido (Equilibrado, 30 vidas pareadas) frente a `c1_rapido.json`

| Métrica | C.1 (`c1_rapido`) | C.3b (`c3b_rapido`) | Δ pareado (IC 95 %) |
|---|---|---|---|
| **Latidos** | 422,70 ± 74,92 | 419,30 ± 74,43 | -3,40 ± 28,22 |
| **Fitness** | 11734,53 ± 1299,05 | 11731,40 ± 1375,04 | -3,13 ± 202,76 |
| **Logros** | 11,30 ± 1,23 | 11,30 ± 1,31 | -0,00 ± 0,19 |
| **Noches** | 1,20 ± 0,30 | 1,20 ± 0,30 | -0,00 ± 0,16 |
| **Vivas a L600** | 11 | 9 | -2 |
| **Tiempo por latido** | 5,24 ms | 5,45 ms | +0,21 ms ($\le +4\,\%$) |

- **Análisis crítico del benchmark rápido:** El resultado es **neutro**. Las vidas vivas bajan ligeramente de 11 a 9 (dentro del intervalo de confianza pareado), y el logro `eat_cow` baja de 19 a 18 vidas.

---

### 5.4 Decisión sobre C.3b

| Pieza | Hipótesis | Arnés largo (11–20) | Arnés 600 (11–30) | Benchmark rápido (1–10) | Decisión |
|---|---|---|---|---|---|
| **C.3b** | Caducidad a 150 latidos y patrulla $\le 17$ permiten cazar vacas repuestas y prolongar la vida de forma generalizada. | **No confirmada de forma general:**<br>• Ganancia concentrada en 1 semilla (sem. 17: +269 latidos, +2 vacas).<br>• En las otras 9 semillas no hay aumento de vacas. | **Estable:**<br>• Selladas día 1: **16/20 (80,0 %)**.<br>• Vivas: **5/20** (+1 vida).<br>• Latidos: **414,6** (+16,4). | **Neutro:**<br>• Latidos: $\Delta = -3,40 \pm 28,22$.<br>• Vivas: 11 $\to$ 9.<br>• `eat_cow`: 19 $\to$ 18. | **No confirmada (mantenida provisionalmente)** |

**Veredicto:**  
La hipótesis general de C.3b **no queda confirmada**: la patrulla no logra que la mayoría de los individuos cacen más vacas de forma general, ya que el cuello de botella central es que **ven las vacas pero no se las comen**.  
Sin embargo, dado que el confinamiento de la exploración a $\le 17$ del recinto recordado no degrada el sellado (16/20) y es un requisito espacial necesario para operar en torno al huerto en C.4, **se mantiene provisionalmente** en el código y se reevaluará de forma conjunta con C.4.

---

## 6. C.3c: Diagnóstico de episodios de vacas percibidas (¿por qué no se come las vacas que ve?)

### 6.1 Metodología y comando
Se implementó en `herramientas/diagnostico_vacas_c3c.py` (commit `d9e0877`) un seguimiento observacional de cada episodio de vaca percibida a partir del latido 300 (después de la primera noche) en el arnés largo (`--real`, semillas 11–20, `--latidos 3000`).

Un **episodio** se define desde que una vaca concreta entra en el campo perceptual del individuo (`Exterocepcion`, clase `"vaca"`) hasta que desaparece de la vista o es comida. Para cada episodio se registran:
- Parámetros iniciales: comida, agua, salud, distancia euclídea, luz diurna y rasgo `nutritivo`.
- Propuestas generadas por las estrategias hacia la vaca (`alimentarse`, `refugio_nocturno` `abastecer`), su activación/confianza y la estrategia ganadora del Tribunal en cada latido.
- Desenlace del episodio clasificado en tres categorías excluyentes:
  * `comida`: el individuo abate y consume la vaca (`eat_cow`).
  * `perdida_de_vista`: el individuo intentó acercarse o atacarla pero la vaca salió de su rango de visión antes de ser consumida.
  * `ignorada`: ninguna estrategia propuso actuar hacia la vaca o las propuestas fueron derrotadas de principio a fin por otras prioridades en el Tribunal.

- **Comando exacto:**
  ```powershell
  $t0 = Get-Date; & "C:\Users\diego\AppData\Local\Python\pythoncore-3.15-64\python.exe" herramientas/diagnostico_vacas_c3c.py --semillas 11 12 13 14 15 16 17 18 19 20 --latidos 3000; $t1 = Get-Date; Write-Host "TIEMPO_TOTAL: $(($t1 - $t0).TotalSeconds) s"
  ```
- **Tiempo de ejecución:** **47,95 s** (65 episodios registrados en 10 semillas).

---

### 6.2 Resultados por semilla

| Semilla | Latidos vividos | Causa muerte | Episodios totales | Comidos | Perdidos de vista | Ignorados | % Comidos |
|---|---|---|---|---|---|---|---|
| **11** | 620 | Hambre | 3 | 1 | 2 | 0 | 33,3 % |
| **12** | 441 | Hambre | 6 | 0 | 0 | 6 | 0,0 % |
| **13** | 479 | Hambre | 13 | 0 | 0 | 13 | 0,0 % |
| **14** | 311 | Zombi | 0 | 0 | 0 | 0 | 0,0 % |
| **15** | 169 | Zombi | 0 | 0 | 0 | 0 | 0,0 % |
| **16** | 155 | Zombi | 0 | 0 | 0 | 0 | 0,0 % |
| **17** | 697 | Hambre | 10 | 3 | 3 | 4 | 30,0 % |
| **18** | 325 | Zombi | 0 | 0 | 0 | 0 | 0,0 % |
| **19** | 315 | Zombi | 3 | 0 | 0 | 3 | 0,0 % |
| **20** | 636 | Hambre | 30 | 2 | 3 | 25 | 6,7 % |

- En las 4 vidas que mueren antes o inmediatamente al salir de la primera noche (semillas 14, 15, 16, 18) no se registran episodios tras L300.
- En las 6 vidas restantes se registran **65 episodios** (media de **10,83 episodios por vida** que supera L300; media de **6,50 episodios/vida** sobre las 10 semillas).

---

### 6.3 Desglose por desenlace y estado metabólico

| Desenlace | N episodios | % del total | Comida media al ver la vaca | Rango comida | Distancia media inicio | Golpes dados a la vaca |
|---|---|---|---|---|---|---|
| **Comida** | 6 | **9,2 %** | **2,50** | [0, 7] | 2,83 casillas | [0, 2, 0, 2, 2, 0] |
| **Perdida de vista** | 8 | **12,3 %** | **2,75** | [0, 7] | 3,38 casillas | 0 golpes (0/8) |
| **Ignorada** | 51 | **78,5 %** | **4,08** | [0, 9] | 3,33 casillas | 0 golpes (0/51) |
| **Total / Global** | 65 | 100,0 % | 3,77 | [0, 9] | 3,29 casillas | — |

#### Umbral de comida para perseguir la vaca
- Hubo **14 episodios** en los que el individuo intentó activamente ir a por la vaca (`comida` + `perdida_de_vista`), sumando 17 latidos de inicio de aproximación.
- Niveles de comida al inicio de dichos intentos: `[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 6, 6, 7, 7, 7]`.
  * En el **70,6 %** de los intentos (12/17), la comida es crítica: **$\le 1$**.
  * Solo en 5 ocasiones intentó cazar con comida media-alta (6 o 7), todas ellas en las semillas 17 y 20 durante la fase matutina de abastecimiento (`refugio_nocturno.abastecer`).
  * Con comida llena (8 o 9), el individuo **nunca** intentó perseguir una vaca (0/25 episodios con comida $\ge 8$).

---

### 6.4 Estrategias que ganan el Tribunal cuando se ignora la vaca

Durante los episodios en que una vaca estuvo en el campo de visión pero no fue perseguida (159 latidos acumulados en total):

| Estrategia ganadora | Latidos ganados | % de latidos | Contexto / Motivo predominante |
|---|---|---|---|
| **`S2:refugio_nocturno`** | 49 | **30,8 %** | Obras y cierre de la noche 2: cavar (3/3), tapar entrada, o abastecer agua de urgencia al atardecer antes de cerrar. |
| **`desconocida`** | 30 | **18,9 %** | Individuo encerrado en la cueva a oscuras durante la noche 2 (sin luz ni estrategia activa, la vaca se percibe al otro lado del muro). |
| **`S1:alimentarse`** | 24 | **15,1 %** | Buscando o bebiendo agua, recolectando comida vegetal ya localizada, o saciado. |
| **`S1:huir`** | 17 | **10,7 %** | Huida reactiva de zombis o esqueletos detectados en la misma ventana visual. |
| **`S3:plan_tecnologico`** | 12 | **7,5 %** | Tala de madera (`wood`) o extracción de piedra (`stone`) en pleno mediodía con comida alta. |
| **`CORE`** | 9 | **5,7 %** | Dormido en el refugio sellado (`sigue dormido`). |
| **`S1:sobresalto`** | 8 | **5,0 %** | Reacción refleja de sobresalto ante daño o monstruos en proximidad. |
| **`S1` (reflejos)** | 4 | **2,5 %** | Movimientos reflejos de emergencia. |
| **`S1:defenderse`** | 3 | **1,9 %** | Ataque defensivo contra zombis en cuerpo a cuerpo. |
| **`S2:explorar`** | 3 | **1,9 %** | Desplazamiento por curiosidad hacia casillas inexploradas. |

---

### 6.5 Conclusión explícita: ¿dónde está el cuello de botella?

El análisis empírico de los 65 episodios demuestra de forma concluyente que:

1. **La MOTIVACIÓN (aliestesia homeostática y arbitraje del Tribunal) es el cuello de botella principal (78,5 % de episodios):**
   - **Falta de caza preventiva:** La aliestesia actual calcula el deseo de carne como $\text{deseo} = \frac{9 - \text{comida}}{9}$. Con comida $\ge 7$, el rasgo nutritivo es $\le 0,22$ y la activación de `Alimentarse` queda por debajo del umbral competitivo del Tribunal ($\approx 0,35$). Por tanto, `S3:plan_tecnologico` (talar madera) o `S2:explorar` ganan sistemáticamente durante las horas centrales del día, impidiendo que el individuo aproveche vacas adyacentes para hacer acopio.
   - **Conflicto con la rutina nocturna y percepción a través de muros:** El **55,4 %** de los latidos ignorados (88/159 latidos: `refugio_nocturno` 30,8 %, `desconocida` 18,9 %, `CORE` 5,7 %) ocurren mientras el individuo está ocupado en la preparación del refugio al atardecer (cavar, tapar) o durmiendo/esperando dentro de la cueva sellada durante la segunda noche. En Crafter el sensor percibe a través de las paredes de roca; las vacas pastan en el exterior a $r \le 5$, pero el individuo está legítimamente encerrado a salvo de la noche.

2. **La PERSECUCIÓN es un cuello de botella secundario menor (12,3 % de episodios):**
   - En los 8 episodios perdidos de vista, la vaca se desplazó (en Crafter se mueven con $p = 0,50$ por latido) o había obstáculos en la trayectoria (agua, rocas), perdiéndose de vista antes de que el individuo pudiera asestarle el primer golpe (**0 golpes dados en los 8 casos**). No obstante, solo afecta a ~1 de cada 8 episodios.

3. **El COMBATE NO es un cuello de botella (0 % de fracasos):**
   - En todos los episodios en que el individuo logró alcanzar a la vaca en cuerpo a cuerpo (los 6 episodios `comida`), la abatió y consumió con éxito requiriendo entre 0 y 2 golpes adicionales. Ningún episodio se frustró por interrupción o falta de daño una vez trabado el combate.


