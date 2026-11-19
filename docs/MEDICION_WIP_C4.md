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
