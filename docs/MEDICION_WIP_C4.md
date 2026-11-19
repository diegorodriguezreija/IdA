# Medición del estado WIP C.4 (huerto en bolsillos cerrados)

**Rama:** `wip/c4-argon`  
**Base commit:** `dc4519f` (HEAD de `feature/crafter-fase-c`)  
**Commit WIP:** `c39cb4a`  
**Fecha:** 2026-11-19  
**Código medido:** idéntico a lo dejado por el modelo anterior en `ida/` y `tests/` (sin modificaciones).

---

## 1. Verificación estática y batería de tests

### 1.1 `pytest -q`
```
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [100%]
============================== warnings summary ===============================
C:\Users\diego\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages\chess\engine.py:54
  C:\Users\diego\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages\chess\engine.py:54: DeprecationWarning: 'asyncio.DefaultEventLoopPolicy' is deprecated and slated for removal in Python 3.16
    EventLoopPolicy = asyncio.DefaultEventLoopPolicy

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
171 passed, 1 warning in 41.70s
```

### 1.2 `ruff check ida tests herramientas`
```
F841 Local variable `coste` is assigned to but never used
    --> ida\mundos\crafter.py:1426:9
     |
1424 |         estado["mina"] = mina_actual
1425 |         pasos_luz = self._pasos_luz_restantes(luz)
1426 |         coste = self._coste_restante_pasos(pos, inv, mina_actual)
     |         ^^^^^
1427 |         coste_refugio = self._coste_restante_pasos(pos, inv, mina_actual, incluir_huerto=False)
1428 |         es_noche = luz < 0.5 and not estado.get("manana") and (self.bajando or luz < 0.35)
     |
help: Remove assignment to unused variable `coste`
     |
1425 |         pasos_luz = self._pasos_luz_restantes(luz)
     -         coste = self._coste_restante_pasos(pos, inv, mina_actual)
1426 +         self._coste_restante_pasos(pos, inv, mina_actual)
1427 |         coste_refugio = self._coste_restante_pasos(pos, inv, mina_actual, incluir_huerto=False)
     |
note: This is an unsafe fix and may change runtime behavior

Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
```

### 1.3 `mypy ida`
```
ida\core\sentidos.py:97: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
ida\mundos\archivos.py:347: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
Success: no issues found in 40 source files
```

---

## 2. Arnés de 600 latidos (semillas 11–50, 40 vidas, `--real`)

**Comando:**  
`python herramientas/arnes_refugio_crafter.py --real --semillas 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 --latidos 600 --salida datos/benchmarks/c4_wip_600.json`

| Métrica | Referencia C.3d (`arnes_600_despues.json`) | WIP C.4 (`c4_wip_600.json`) | Diferencia (Δ) |
|---|---|---|---|
| **Vidas selladas el día 1** | **32 / 40 (80,0 %)** | **25 / 40 (62,5 %)** | **-7 vidas (-17,5 pp)** |
| **Selladas con luz ≥ 0,5** | 19 / 40 (47,5 %) | 13 / 40 (32,5 %) | -6 vidas (-15,0 pp) |
| **Selladas sin daño nocturno** | 32 / 32 (100,0 %) | 25 / 25 (100,0 %) | = 0 (100 %) |
| **Vidas con `wake_up`** | 33 / 40 (82,5 %) | 24 / 40 (60,0 %) | -9 vidas (-22,5 pp) |
| **Vivas al final (L600)** | **10 / 40 (25,0 %)** | **7 / 40 (17,5 %)** | **-3 vidas (-7,5 pp)** |
| **Latidos medios** | **418,9** | **354,5** | **-64,4 latidos** |
| **Logros medios** | 11,70 | 10,90 | -0,80 logros |
| **Muertes por causa** | Zombi: 12<br>Hambre: 12<br>Sed: 4<br>Esqueleto: 2 | Zombi: 15<br>Hambre: 8<br>Sed: 5<br>Esqueleto: 5 | Zombi: +3<br>Hambre: -4<br>Sed: +1<br>Esqueleto: +3 |
| **Salen del refugio** | 32 | 25 | -7 |
| **Tiempo de ejecución (40 vidas)** | 159,96 s | 145,20 s | -14,76 s |
| **Tiempo por latido** | 9,55 ms | 10,24 ms | +0,69 ms (+7,2 %) |

---

## 3. Arnés largo (semillas 11–30, `--latidos 3000`, `--real`)

**Comando:**  
`python herramientas/medicion_c4_largo.py`  
(Fichero generado: `datos/benchmarks/c4_medicion_largo.json`)

### 3.1 Detalle por vida

| Semilla | Latidos | Estado | Causa muerte | Día muerte | Bolsillo colocadas | Bolsillo maduradas | Bolsillo comidas (`eat_plant`) | Bolsillo destruidas (causa) | Comida mínima por día (`min_comida`) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **11** | 1040 | Muerta | Hambre | 3 | 2 | 2 | 3 | 2 ((34,39) y (33,38) en L821 por `zombie`) | d0: 4, d1: 3, d2: 0, d3: 0 |
| **12** | 157 | Muerta | Esqueleto | 0 | 0 | 0 | 0 | 0 | d0: 3 |
| **13** | 541 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 2, d1: 0 |
| **14** | 349 | Muerta | Sed | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **15** | 169 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 2 |
| **16** | 192 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 5 |
| **17** | 644 | Muerta | Hambre | 2 | 1 | 1 | 1 | 0 | d0: 1, d1: 0, d2: 0 |
| **18** | 389 | Muerta | Sed | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **19** | 318 | Muerta | Zombi | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **20** | 211 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 4 |
| **21** | 355 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **22** | 422 | Muerta | Esqueleto | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 2 |
| **23** | 412 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 1, d1: 0 |
| **24** | 189 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 2 |
| **25** | 322 | Muerta | Sed | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **26** | 502 | Muerta | Esqueleto | 1 | 0 | 0 | 0 | 0 | d0: 4, d1: 0 |
| **27** | 299 | Muerta | Hambre | 0 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **28** | 481 | Muerta | Esqueleto | 1 | 1 | 0 | 0 | 0 | d0: 1, d1: 0 |
| **29** | 682 | Muerta | Hambre | 2 | 0 | 0 | 0 | 0 | d0: 2, d1: 0, d2: 0 |
| **30** | 216 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 4 |

### 3.2 Resumen agregado frente a C.3d

| Métrica | Referencia C.3d (`arnes_largo_despues.json`) | WIP C.4 (`c4_medicion_largo.json`) | Diferencia (Δ) |
|---|---|---|---|
| **Latidos vividos (media)** | **454,10** | **394,50** | **-59,60 latidos** |
| **Latidos vividos (mediana)** | **417,00** | **352,00** | **-65,00 latidos** |
| **Máximo de latidos** | 1002 (semilla 20) | 1040 (semilla 11) | +38 latidos |
| **Muertes por hambre en día 1** (`dia == 1`) | 6 / 20 | **3 / 20** (sem. 13, 21, 23) | -3 muertes |
| **Muertes por hambre totales** | 11 / 20 | **7 / 20** | -4 muertes |
| **Muertes totales en día 1** (`dia == 1`) | 12 / 20 | **10 / 20** (3 hambre, 3 sed, 3 esqueleto, 1 zombi) | -2 muertes |
| **Muertes totales en día 0** (`dia == 0`) | 4 / 20 | **7 / 20** (5 zombi, 1 esqueleto, 1 hambre) | +3 muertes |
| **Vidas que pasan de L450** | 8 / 20 (40,0 %) | **6 / 20 (30,0 %)** (sem. 11, 13, 17, 26, 28, 29) | -2 vidas |
| **Vidas > L450 que comen ≥ 1 planta** | 0 / 8 (0,0 %) | **2 / 6 (33,3 %)** (sem. 11: 3 comidas, sem. 17: 1 comida) | **+2 vidas** |
| **Plantas colocadas en bolsillos** | 0 | **4 en 3 vidas** (sem. 11: 2, sem. 17: 1, sem. 28: 1) | +4 plantas |
| **Plantas maduradas en bolsillos** | 0 | **3** (sem. 11: 2, sem. 17: 1) | +3 plantas |
| **Plantas comidas totales** | 0 | **4** (sem. 11: 3, sem. 17: 1) | +4 plantas |
| **Plantas destruidas en bolsillos** | 0 | **2** (sem. 11 en L821 por `zombie`) | +2 plantas |

---

## 4. Tiempo por latido frente a C.3d

| Experimento | C.3d (referencia) | WIP C.4 | Variación |
|---|---|---|---|
| **Arnés largo (semillas 11–30, 3000 latidos)** | 9,62 ms / latido (87,34 s / 9082 lat.) | 10,20 ms / latido (80,45 s / 7890 lat.) | +0,58 ms / latido (+6,0 %) |
| **Arnés 600 latidos (semillas 11–50, 40 vidas)** | 9,55 ms / latido (159,96 s / 16756 lat.) | 10,24 ms / latido (145,20 s / 14180 lat.) | +0,69 ms / latido (+7,2 %) |

---

## 5. Observaciones de fallos detectados

1. **Aviso de linter F841:** En [`ida/mundos/crafter.py:1426`](file:///f:/code/IdA/ida/mundos/crafter.py#L1426), la variable local `coste` se asigna mediante `coste = self._coste_restante_pasos(pos, inv, mina_actual)` pero no se utiliza posteriormente en la función.
2. **Caída de sellado en día 1:** En el arnés de 600 latidos sobre 40 vidas (11–50), las vidas selladas el día 1 descienden de 32/40 (80,0 %) en C.3d a 25/40 (62,5 %) en WIP C.4. Las muertes en día 0 por monstruos suben (zombi de 12 a 15, esqueleto de 2 a 5).
3. **Baja frecuencia de plantación:** En el arnés largo (20 vidas), solo 3 vidas colocan plantas en bolsillo (semillas 11, 17 y 28). En las otras 17 vidas no se llega a colocar ninguna planta (en 7 vidas por muerte prematura en día 0 antes del anochecer; en las restantes por no encontrar bolsillo válido o porque el presupuesto de luz no lo permite).
4. **Vulnerabilidad a monstruos en L800+:** En la semilla 11, las 2 plantas colocadas en bolsillos cerrados maduraron y aportaron 3 cosechas (extendiendo la vida hasta L1040), pero al latido 821 un zombi alcanzó la posición de los bolsillos y destruyó ambas plantas.

---

## 6. Diagnóstico de la semilla 11 (destrucción de plantas en L821)

En la semilla 11 (código WIP C.4), se colocaron dos plantas en los bolsillos en $P_1 = (34, 39)$ y $P_2 = (33, 38)$. Ambas maduraron y aportaron 3 cosechas. En el latido 821, un zombi destruyó ambas plantas.

### Análisis de casillas en cruz y transitabilidad:
- **Planta $P_1$ en $(34, 39)$:**
  - $(34, 40)$: `stone` (no transitable)
  - $(34, 38)$: `stone` (no transitable)
  - $(35, 39)$: `diamond` (no transitable)
  - **$(33, 39)$:** `path` (**transitable**)
- **Planta $P_2$ en $(33, 38)$:**
  - $(33, 37)$: `tree` (no transitable)
  - $(34, 38)$: `stone` (no transitable)
  - $(32, 38)$: `stone` (no transitable)
  - **$(33, 39)$:** `path` (**transitable**)

### Origen y cronología:
- Ambas plantas compartían como vecina en cruz la celda **$(33, 39)$**, que era la celda de acceso $A$ del bolsillo $P_1$.
- La celda $(33, 39)$ estuvo cerrada con piedra desde el día 1 (L100 a L723).
- En el latido **724**, el individuo picó la piedra (`COGER piedra_33_39`, motivo `"refugio: abrir bolsillo para cosechar"`) para entrar a cosechar la planta madura, completando la ingesta en L726.
- A partir del latido 727, inició la fase de recierre (`"refugio: recerrar bolsillo: ir a P"`), pero la presencia cercana de un esqueleto activó repetidamente `S1:huir:seguridad` y `S1:sobresalto:seguridad` entre L727 y L750, interrumpiendo el cierre y alejando al individuo.
- La celda $(33, 39)$ permaneció como **`path` transitable y abierta desde el latido 724**.
- En el latido 820, un zombi entró en la casilla abierta $(33, 39)$ y en el latido 821 alcanzó $P_1$ y $P_2$, destruyendo ambas plantas por adyacencia de monstruo.

---

## 7. Medición tras ajustes C.4 (puntos 1–4)

**Commits de ajuste:**
1. `fecf4e0`: `crafter: exigir recursos y presupuesto de luz estricto en _puede_plantar_dia1`
2. `f6aa3a4`: `crafter: plantar oportunista el dia 1 con bolsillo natural y sin busqueda de recursos`
3. `f800364`: `crafter: separar plantas_vistas (obstaculo) y plantas_propias (pared de bolsillo)`
4. `2c93d47`: `crafter: corregir aviso F841 de ruff (variable coste sin uso)`

### 7.1 Arnés de 600 latidos (semillas 11–50, 40 vidas, `--real`)
**Comando:** `python herramientas/arnes_refugio_crafter.py --real --semillas 11..50 --latidos 600 --salida datos/benchmarks/c4_ajustado_600.json`

| Métrica | Referencia C.3d | WIP C.4 inicial | C.4 Ajustado (puntos 1–4) | Δ frente a C.3d | Δ frente a WIP C.4 |
|---|---|---|---|---|---|
| **Vidas selladas el día 1** | **32 / 40 (80,0 %)** | 25 / 40 (62,5 %) | **29 / 40 (72,5 %)** | -3 vidas (-7,5 pp) | **+4 vidas (+10,0 pp)** |
| **Selladas con luz ≥ 0,5** | 19 / 40 (47,5 %) | 13 / 40 (32,5 %) | **18 / 40 (45,0 %)** | -1 vida (-2,5 pp) | **+5 vidas (+12,5 pp)** |
| **Selladas sin daño dentro** | 32 / 32 (100,0 %) | 25 / 25 (100,0 %) | **29 / 29 (100,0 %)** | = 0 (100 %) | = 0 (100 %) |
| **Vidas con `wake_up`** | 33 / 40 (82,5 %) | 24 / 40 (60,0 %) | **30 / 40 (75,0 %)** | -3 vidas (-7,5 pp) | **+6 vidas (+15,0 pp)** |
| **Vivas al final (L600)** | 10 / 40 (25,0 %) | 7 / 40 (17,5 %) | **7 / 40 (17,5 %)** | -3 vidas (-7,5 pp) | = 0 |
| **Latidos medios** | 418,9 | 354,5 | **384,1** | -34,8 latidos | **+29,6 latidos** |
| **Logros medios** | 11,70 | 10,90 | **11,38** | -0,32 logros | **+0,48 logros** |
| **Muertes por causa** | Zombi: 12<br>Hambre: 12<br>Sed: 4<br>Esqueleto: 2 | Zombi: 15<br>Hambre: 8<br>Sed: 5<br>Esqueleto: 5 | Zombi: 13<br>Hambre: 11<br>Sed: 4<br>Esqueleto: 5 | Zombi: +1<br>Hambre: -1<br>Sed: = 0<br>Esqueleto: +3 | Zombi: -2<br>Hambre: +3<br>Sed: -1<br>Esqueleto: = 0 |

---

### 7.2 Arnés largo (semillas 11–30, `--latidos 3000`, `--real`)
**Comando:** `python -c "from herramientas.medicion_c4_largo import ejecutar_medicion; ejecutar_medicion(list(range(11, 31)), latidos=3000, salida='datos/benchmarks/c4_ajustado_largo.json')"`

#### Detalle por vida (semillas 11–30)

| Semilla | Latidos | Estado | Causa muerte | Día muerte | Bolsillo colocadas | Bolsillo maduradas | Bolsillo comidas (`eat_plant`) | Bolsillo destruidas (causa) | Comida mínima diaria (`min_comida`) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **11** | 609 | Muerta | Hambre | 2 | 0 | 0 | 0 | 0 | d0: 3, d1: 0, d2: 0 |
| **12** | 331 | Muerta | Esqueleto | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **13** | 574 | Muerta | Zombi | 1 | 0 | 0 | 0 | 0 | d0: 2, d1: 0 |
| **14** | 298 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **15** | 169 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 2 |
| **16** | 446 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 3, d1: 0 |
| **17** | 470 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 1, d1: 0 |
| **18** | 566 | Muerta | Hambre | 1 | 0 | 0 | 1 | 0 | d0: 0, d1: 0 |
| **19** | 300 | Muerta | Sed | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **20** | 1168 | Muerta | Zombi | 3 | 1 | 1 | 1 | 0 | d0: 2, d1: 2, d2: 3, d3: 0, d4: 0 |
| **21** | 358 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **22** | 422 | Muerta | Esqueleto | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 2 |
| **23** | 412 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 1, d1: 0 |
| **24** | 189 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 2 |
| **25** | 311 | Muerta | Esqueleto | 1 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **26** | 268 | Muerta | Zombi | 0 | 0 | 0 | 0 | 0 | d0: 4 |
| **27** | 299 | Muerta | Hambre | 0 | 0 | 0 | 0 | 0 | d0: 0, d1: 0 |
| **28** | 484 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 1, d1: 0 |
| **29** | 391 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 2, d1: 0 |
| **30** | 493 | Muerta | Hambre | 1 | 0 | 0 | 0 | 0 | d0: 2, d1: 0 |

#### Resumen agregado frente a C.3d y WIP C.4

| Métrica | Referencia C.3d | WIP C.4 inicial | C.4 Ajustado (puntos 1–4) | Δ frente a C.3d | Δ frente a WIP C.4 |
|---|---|---|---|---|---|
| **Latidos vividos (media)** | **454,10** | 394,50 | **427,90** | -26,20 latidos | **+33,40 latidos** |
| **Latidos vividos (mediana)** | **417,00** | 352,00 | **401,50** | -15,50 latidos | **+49,50 latidos** |
| **Máximo de latidos** | 1002 (sem. 20) | 1040 (sem. 11) | **1168 (sem. 20)** | **+166 latidos** | **+128 latidos** |
| **Muertes por hambre en día 1 (`dia == 1`)** | 6 / 20 | 3 / 20 | **8 / 20** | +2 muertes | +5 muertes |
| **Muertes por hambre totales** | 11 / 20 | 7 / 20 | **10 / 20** | -1 muerte | +3 muertes |
| **Muertes totales en día 1 (`dia == 1`)** | 12 / 20 | 10 / 20 | **13 / 20** (8 hambre, 3 esqueleto, 1 zombi, 1 sed) | +1 muerte | +3 muertes |
| **Muertes totales en día 0 (`dia == 0`)** | 4 / 20 | 7 / 20 | **5 / 20** (4 zombi, 1 hambre) | +1 muerte | -2 muertes |
| **Vidas que superan L450** | 8 / 20 (40,0 %) | 6 / 20 (30,0 %) | **7 / 20 (35,0 %)** | -1 vida | +1 vida |
| **Vidas > L450 que comen ≥ 1 planta** | 0 / 8 (0,0 %) | 2 / 6 (33,3 %) | **2 / 7 (28,6 %)** (sem. 18 y sem. 20) | +2 vidas | = 0 |
| **Vidas con plantas en bolsillo** | 0 / 20 | 3 / 20 | **1 / 20** (semilla 20) | +1 vida | -2 vidas |
| **Plantas colocadas en bolsillos** | 0 | 4 | **1** (semilla 20) | +1 planta | -3 plantas |
| **Plantas maduradas en bolsillos** | 0 | 3 | **1** (semilla 20) | +1 planta | -2 plantas |
| **Plantas comidas totales** | 0 | 4 | **2** (sem. 18: 1 silvestre, sem. 20: 1 bolsillo) | +2 plantas | -2 plantas |
| **Plantas destruidas en bolsillos** | 0 | 2 | **0** | = 0 | -2 plantas |

---

### 7.3 Aplicación de la regla de parada

1. **Condición 1:** Vidas selladas el día 1 en el arnés de 600 latidos (semillas 11–50) = **29 / 40** (< 30 / 40).
2. **Condición 2:** Mediana del arnés largo (semillas 11–30) = **401,50** (< 417,00 de la referencia C.3d).

Ambas condiciones de parada se cumplen. Conforme a las instrucciones del encargo, no se realizan más ajustes y se entregan las mediciones registradas.
