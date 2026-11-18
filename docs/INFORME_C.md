# Informe de la Fase C: Hábitat y Ciclo Circadiano en Crafter

Referencia base: `datos/benchmarks/ref_c0.json` (commit `f2f1262`).  
Rama: `feature/crafter-fase-c`.  
Sin push a remoto. Framework base (`ida/core/`, `ida/sistemas/`) estrictamente sin modificar.

---

## 1. C.0c: Corrección de fallos de S1

### 1.1 Resultado
La pieza C.0c (desplegada en dos commits: C.0c-1 y C.0c-2) elimina las muertes por inanición dentro del refugio sellado y evita que el individuo persiga recursos inalcanzables bloqueados por el terreno:
- **C.0c-1:** En el arnés (semillas 11–30), **0/20 vidas mueren de hambre o sed dentro del refugio sellado** (11/11 vidas selladas salen al exterior). La semilla 14 desella y sale del refugio a L259 (en lugar de morir atrapada dentro a L332), come fuera a L278, aunque sucumbe por sed a L294 al no tener agua en su memoria previa y hallarse la fuente más cercana a 10 casillas de distancia.
- **C.0c-2:** Se implementa la detección de destinos inalcanzables en `_paso_hacia` y el registro de memoria `self.inalcanzables` (50 latidos de enfriamiento) en `RefugioNocturno`. Las muertes por sed en el arnés caen de 3 a 1. El test unitario sintético confirma que ante agua encerrada tras roca conocida, se anota como inalcanzable y se opta por el agua accesible. El benchmark rápido en Equilibrado mejora el fitness (+132,50) y los logros (+0,13).

### 1.2 Tabla de evaluación

| Pieza | Commit | Hipótesis | Arnés (11–30) | Benchmark Equilibrado (1–10, N=10 pareado) | Decisión |
|---|---|---|---|---|---|
| **C.0c-1** | `16cdf5e` | La semilla 14 sale del refugio; ninguna muerte por hambre o sed dentro de refugio sellado. | 11/11 selladas salen (0 muertes dentro). Semilla 14 sale a L259 (come fuera L278, muere sed L294). | Latidos: +0,77 ± 58,97<br>Fitness: +34,00 ± 742,64<br>Logros: +0,03 ± 0,70<br>Noches: +0,10 ± 0,32 | **Aceptada** |
| **C.0c-2** | `2e5ec72` | No perseguir destinos inalcanzables; descartar aguas cerradas por roca hacia fuentes viables. | Muertes por sed: 3 → 1.<br>Beben tras salir: 9/11 (81,8 %).<br>Test sintético en verde. | Latidos: -0,97 ± 59,66<br>Fitness: +132,50 ± 765,09<br>Logros: +0,13 ± 0,72<br>Noches: +0,10 ± 0,32 | **Aceptada** |

---

### 1.3 Causas de muerte en el arnés (semillas 11–30)

| Causa de muerte | Ref C.0 | C.0c-1 | C.0c-2 | Δ (C.0c-2 vs Ref) |
|---|---|---|---|---|
| **zombi** | 6 | 6 | 6 | = 0 |
| **esqueleto** | 4 | 4 | 4 | = 0 |
| **hambre** | 3 | 6 | 6 | +3 |
| **sed** | 3 | 1 | 1 | **-2** |
| **vivas** | 4 | 3 | 3 | -1 |
| *Muerte dentro de refugio* | 1 (sem 14) | 0 | 0 | **-1 (0 dentro)** |

*Nota sobre causas:* En C.0c-1 y C.0c-2 las vidas que antes morían dentro de sed (como la 14) ahora salen al amanecer; al salir sin reservas previas de comida o agua consiguen alargar su vida en el exterior hasta que el déficit metabólico se agota (p. ej. sem 11 muere a L382 por hambre habiendo bebido a L295; sem 17 muere a L382 por hambre habiendo bebido a L299).

---

### 1.4 Benchmark rápido: Equilibrado (10 linajes, 30 vidas)

Comparación `ref_c0.json` vs `c0c_2.json`:

| Métrica | Base (`ref_c0`) | C.0c-2 | Δ pareado (IC 95 %) |
|---|---|---|---|
| **latidos** | 370.10 ± 66.57 | 369.13 ± 67.92 | -0.97 ± 59.66 |
| **fitness** | 11315.50 ± 1407.01 | 11448.00 ± 1338.52 | **+132.50 ± 765.09** |
| **logros** | 10.93 ± 1.36 | 11.07 ± 1.30 | **+0.13 ± 0.72** |
| **noches** | 0.90 ± 0.28 | 1.00 ± 0.34 | **+0.10 ± 0.32** |

#### Muertes por causa (Equilibrado, 30 vidas)
| Causa | Base | C.0c-2 | Δ |
|---|---|---|---|
| zombi | 10 | 8 | -2 |
| hambre | 6 | 4 | -2 |
| sed | 6 | 10 | +4 |
| esqueleto | 2 | 3 | +1 |
| vive | 6 | 5 | -1 |

#### Logros por tipo (Equilibrado, 30 vidas)
| Logro | Base (`ref_c0`) | C.0c-2 | Δ vidas | Explicación |
|---|---|---|---|---|
| collect_coal | 9 | 10 | +1 | Mayor exploración diurna |
| collect_drink | 23 | 23 | 0 | Estable |
| collect_stone | 23 | 23 | 0 | Estable |
| collect_wood | 30 | 30 | 0 | 100 % de vidas |
| place_plant | 30 | 30 | 0 | 100 % de vidas |
| place_table | 29 | 29 | 0 | Estable |
| make_wood_pickaxe | 29 | 29 | 0 | Estable |
| make_wood_sword | 28 | 28 | 0 | Estable |
| place_stone | 21 | 21 | 0 | Estable |
| wake_up | 20 | 20 | 0 | Estable |
| eat_cow | 19 | 20 | +1 | Mejora en aprovisionamiento |
| defeat_zombie | 15 | 16 | +1 | Reducción de muertes por zombi |
| defeat_skeleton | 12 | 12 | 0 | Estable |
| place_furnace | 7 | 8 | +1 | Avance tecnológico adicional |
| make_stone_pickaxe | 3 | 2 | -1 | Variabilidad de generación con N=10 |
| make_stone_sword | 1 | 1 | 0 | Estable |

---

### 1.5 Verificación de pureza y base

Comandos ejecutados y su salida literal:

```powershell
PS F:\code\IdA> git diff --stat main...HEAD -- ida/core ida/sistemas
(salida vacía: ningún archivo modificado en ida/core ni ida/sistemas)

PS F:\code\IdA> python -m pytest -q
160 passed, 1 warning in 34.39s

PS F:\code\IdA> ruff check ida tests herramientas
All checks passed!

PS F:\code\IdA> mypy ida
Success: no issues found in 40 source files
```

### 1.6 Estado de verificación
- **Verificado:** Todos los valores tabulados fueron medidos directamente en ejecución con semillas idénticas sobre Crafter 1.8.3 y comparados pareadamente con `herramientas/benchmark.py comparar`.
- **No verificado:** Efecto en los grupos Valiente, Reactivo y Sin experiencia (fuera de presupuesto para este paso; se reservan para el cierre de C.1 y C.4).
