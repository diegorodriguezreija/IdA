# Medición Oficial: Cierre del Paso 3 (Crafter)

Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto) en la rama `feature/proteger` (commit `c62b1c5`). Evalúa el cierre del Paso 3: la capacidad general «proteger X» (el refugio general) integrada en la base del framework (`ida/`).

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `cierre0_C1.json`: C1 (Cierre Paso 0, sin estrategias propias, semilla 31)
- `paso3_L1a.json`: L1a (Paso 3 exploratorio, sin estrategias propias, mecanismo proteger, semilla 31)
- `paso3_F1.json`: F1 (Cierre Paso 3, sin estrategias propias, refugio general en base, semilla 31)
- `cierre0_C3.json`: C3 (Cierre Paso 0, sin estrategias propias, semilla 32)
- `paso3_L1c.json`: L1c (Paso 3 exploratorio, sin estrategias propias, mecanismo proteger, semilla 32)
- `paso3_F2.json`: F2 (Cierre Paso 3, sin estrategias propias, refugio general en base, semilla 32)
- `cierre0_C2.json`: C2 (Cierre Paso 0, con estrategias propias restantes, semilla 31)
- `paso3_L2.json`: L2 (Paso 3 exploratorio, con estrategias propias restantes, mecanismo proteger, semilla 31)
- `paso3_F3.json`: F3 (Cierre Paso 3, con estrategias propias restantes, refugio general en base, semilla 31)

### Control de latidos cortados (guillotina de 100 ms)

Criterio de validez: una medición es válida si registra 10 latidos cortados o menos (menos del 0,01 % de los latidos). En las mediciones de cierre:
- **F1**: 4 latidos cortados en 4 episodios (0,004 % de los latidos). Se adopta como definitiva esta segunda ejecución (Score 12,82 %, 380 episodios). La primera ejecución registró 1 latido cortado en 1 episodio (Score 12,85 %, 379 episodios).
- **F2**: 6 latidos cortados en 4 episodios (0,006 % de los latidos; Score 13,58 %, 380 episodios).
- **F3**: 1 latido cortado en 1 episodio (0,001 % de los latidos; Score 13,80 %, 358 episodios).
- **C1, C3, C2, L1a, L1c, L2**: anteriores a la instrumentación de conteo de cortes (`no registrado`).


---

## 1. Tabla general

| Métrica | C1 | L1a | F1 | C3 | L1c | F2 | C2 | L2 | F3 |
|---|---|---|---|---|---|---|---|---|---|
| **Score (%)** | **11,29** | **11,95** | **12,82** | **11,05** | **12,41** | **13,58** | **15,29** | **13,12** | **13,80** |
| **IC 95 % (%)** | [10,44, 12,01] | [11,01, 12,76] | [11,76, 13,79] | [10,21, 11,72] | [11,42, 13,24] | [12,52, 14,47] | [14,00, 16,30] | [11,96, 14,12] | [12,65, 14,82] |
| **Episodios** | 416 | 384 | 380 | 423 | 387 | 380 | 296 | 369 | 358 |
| **Pasos por episodio** | 240,4 | 260,4 | 263,2 | 236,4 | 258,4 | 263,2 | 337,8 | 271,0 | 279,3 |
| **ms por paso** | 10,35 | 12,60 | 12,59 | 10,50 | 12,74 | 12,43 | 9,93 | 12,50 | 12,36 |
| **Latidos cortados** | no registrado | no registrado | 4 | no registrado | no registrado | 6 | no registrado | no registrado | 1 |

---

## 2. Tasas por logro (%)

Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:

| Logro | C1 | L1a | F1 | C3 | L1c | F2 | C2 | L2 | F3 |
|---|---|---|---|---|---|---|---|---|---|
| `collect_coal` | 8,89 | 9,38 | 11,84 | 7,09 | 6,46 | 9,21 | 10,81 | 8,94 | 12,57 |
| `collect_diamond` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `collect_drink` | 81,25 | 81,25 | 81,58 | 84,63 | 82,69 | 82,37 | 82,43 | 79,67 | 81,84 |
| `collect_iron` | 0,00 | 0,00 | 0,26 | 0,47 | 0,78 | 0,53 | 0,00 | 0,54 | 0,00 |
| `collect_sapling` | 71,63 | 69,79 | 73,16 | 72,34 | 68,48 | 69,47 | 57,77 | 71,00 | 74,58 |
| `collect_stone` | 33,65 | 35,68 | 37,11 | 35,46 | 37,21 | 42,89 | 53,04 | 36,86 | 36,87 |
| `collect_wood` | 90,62 | 91,15 | 91,05 | 94,33 | 93,80 | 93,95 | 98,99 | 91,33 | 91,06 |
| `defeat_skeleton` | 0,72 | 0,26 | 0,53 | 0,00 | 0,26 | 0,00 | 3,72 | 0,81 | 1,68 |
| `defeat_zombie` | 40,62 | 38,54 | 38,42 | 37,35 | 38,76 | 37,63 | 69,93 | 49,86 | 54,19 |
| `eat_cow` | 69,47 | 68,75 | 69,47 | 70,21 | 71,06 | 73,42 | 67,57 | 69,92 | 70,95 |
| `eat_plant` | 0,00 | 0,78 | 0,26 | 0,24 | 0,52 | 0,79 | 1,01 | 0,81 | 0,56 |
| `make_iron_pickaxe` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_iron_sword` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_stone_pickaxe` | 6,97 | 6,77 | 6,32 | 8,27 | 6,72 | 9,21 | 6,08 | 7,86 | 6,98 |
| `make_stone_sword` | 2,16 | 0,78 | 2,37 | 1,89 | 2,07 | 5,00 | 2,36 | 1,63 | 3,07 |
| `make_wood_pickaxe` | 62,02 | 60,68 | 63,95 | 62,41 | 62,53 | 68,68 | 91,89 | 60,98 | 63,69 |
| `make_wood_sword` | 39,66 | 37,76 | 43,16 | 39,95 | 39,53 | 46,05 | 84,80 | 37,67 | 43,30 |
| `place_furnace` | 15,62 | 17,45 | 19,21 | 15,84 | 16,02 | 18,95 | 14,86 | 18,43 | 20,95 |
| `place_plant` | 69,47 | 67,45 | 69,47 | 69,74 | 66,67 | 67,89 | 56,08 | 68,02 | 71,23 |
| `place_stone` | 30,29 | 31,77 | 33,95 | 31,91 | 33,85 | 37,11 | 49,66 | 34,15 | 35,47 |
| `place_table` | 85,10 | 86,20 | 86,05 | 86,05 | 86,30 | 86,32 | 94,59 | 86,18 | 86,31 |
| `wake_up` | 3,85 | 18,49 | 20,53 | 1,89 | 18,35 | 21,32 | 37,16 | 22,49 | 23,18 |

---

## 3. Causas de muerte por condición

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa | C1 | L1a | F1 | C3 | L1c | F2 | C2 | L2 | F3 |
|---|---|---|---|---|---|---|---|---|---|
| `cansancio` | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 1 (0,2 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| `desgaste` | 15 (3,6 %) | 14 (3,6 %) | 12 (3,2 %) | 13 (3,1 %) | 9 (2,3 %) | 9 (2,4 %) | 6 (2,0 %) | 14 (3,8 %) | 8 (2,2 %) |
| `esqueleto` | 25 (6,0 %) | 36 (9,4 %) | 36 (9,5 %) | 30 (7,1 %) | 34 (8,8 %) | 35 (9,2 %) | 50 (16,9 %) | 30 (8,1 %) | 37 (10,3 %) |
| `flecha` | 3 (0,7 %) | 0 (0,0 %) | 1 (0,3 %) | 5 (1,2 %) | 2 (0,5 %) | 1 (0,3 %) | 3 (1,0 %) | 0 (0,0 %) | 1 (0,3 %) |
| `hambre` | 22 (5,3 %) | 31 (8,1 %) | 32 (8,4 %) | 16 (3,8 %) | 20 (5,2 %) | 29 (7,6 %) | 38 (12,8 %) | 32 (8,7 %) | 30 (8,4 %) |
| `lava` | 2 (0,5 %) | 1 (0,3 %) | 0 (0,0 %) | 2 (0,5 %) | 1 (0,3 %) | 2 (0,5 %) | 4 (1,4 %) | 1 (0,3 %) | 0 (0,0 %) |
| `sed` | 31 (7,5 %) | 39 (10,2 %) | 38 (10,0 %) | 21 (5,0 %) | 40 (10,3 %) | 38 (10,0 %) | 29 (9,8 %) | 49 (13,3 %) | 46 (12,8 %) |
| `zombi` | 317 (76,2 %) | 262 (68,2 %) | 260 (68,4 %) | 333 (78,7 %) | 279 (72,1 %) | 266 (70,0 %) | 164 (55,4 %) | 242 (65,6 %) | 235 (65,6 %) |
| `cortado por presupuesto` | 1 (0,2 %) | 1 (0,3 %) | 1 (0,3 %) | 2 (0,5 %) | 2 (0,5 %) | 0 (0,0 %) | 2 (0,7 %) | 1 (0,3 %) | 1 (0,3 %) |
| **Total episodios** | **416** | **384** | **380** | **423** | **387** | **380** | **296** | **369** | **358** |

---

## 4. Comparaciones

Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:

### F1 frente a C1 y a L1a (semilla 31, sin estrategias propias)
- **F1 frente a C1**:
  - Score F1: 12,82 % (IC 95 %: [11,76, 13,79] %)
  - Score C1: 11,29 % (IC 95 %: [10,44, 12,01] %)
  - Diferencia de Score (F1 - C1): +1,53 pp
  - ¿Se solapan los IC 95 %?: **Sí**

- **F1 frente a L1a**:
  - Score F1: 12,82 % (IC 95 %: [11,76, 13,79] %)
  - Score L1a: 11,95 % (IC 95 %: [11,01, 12,76] %)
  - Diferencia de Score (F1 - L1a): +0,87 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### F2 frente a C3 y a L1c (semilla 32, sin estrategias propias)
- **F2 frente a C3**:
  - Score F2: 13,58 % (IC 95 %: [12,52, 14,47] %)
  - Score C3: 11,05 % (IC 95 %: [10,21, 11,72] %)
  - Diferencia de Score (F2 - C3): +2,53 pp
  - ¿Se solapan los IC 95 %?: **No**

- **F2 frente a L1c**:
  - Score F2: 13,58 % (IC 95 %: [12,52, 14,47] %)
  - Score L1c: 12,41 % (IC 95 %: [11,42, 13,24] %)
  - Diferencia de Score (F2 - L1c): +1,17 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### F3 frente a C2 y a L2 (semilla 31, con estrategias propias)
- **F3 frente a C2**:
  - Score F3: 13,80 % (IC 95 %: [12,65, 14,82] %)
  - Score C2: 15,29 % (IC 95 %: [14,00, 16,30] %)
  - Diferencia de Score (F3 - C2): -1,49 pp
  - ¿Se solapan los IC 95 %?: **Sí**

- **F3 frente a L2**:
  - Score F3: 13,80 % (IC 95 %: [12,65, 14,82] %)
  - Score L2: 13,12 % (IC 95 %: [11,96, 14,12] %)
  - Diferencia de Score (F3 - L2): +0,68 pp
  - ¿Se solapan los IC 95 %?: **Sí**


---

## 5. Comprobación de reproducibilidad (Punto 1)

Se comprobó la reproducibilidad de la medición de referencia antigua C1 ejecutando el commit `1ecf254` (rama `feature/cierre-paso0`) con las opciones exactas originales y guardando el resultado en `datos/evaluacion/repro_C1.json`:

```bash
python herramientas\evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --salida datos\evaluacion\repro_C1.json
```

Al comparar `repro_C1.json` con `origin/feature/cierre-paso0:datos/evaluacion/cierre0_C1.json`, ignorando `tiempo_segundos` y `ms_por_paso`, **TODOS los demás campos son estrictamente idénticos**:
- Score: 11,29 %
- IC 95 %: [10,44, 12,01] %
- Episodios: 416 (240,4 pasos/episodio)
- Tasas de los 22 logros oficiales: exactamente iguales en todos los logros.
- Causas de muerte: exactamente iguales en todas las causas.
- Diferencias de reloj: 1.094,6 s (10,95 ms/paso) frente a 1.035,0 s (10,35 ms/paso).

El fichero `repro_C1.json` no contiene rutas locales y se incluye en el repositorio.
