# Medición Oficial: Cierre del Paso 0 (Crafter)

Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia) en la rama `feature/cierre-paso0` (commit `1ecf254`). Cierra el Paso 0 y verifica la corrección del bloqueo de acciones probabilísticas.

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `suelo_main.json`: suelo con linaje (referencia `main` sin estrategias)
- `suelo_sin_herencia.json`: S0 (suelo sin herencia, commit congelado `crafter-procedimental-v1`)
- `paso5_G1.json`: G1 (Paso 5, sin estrategias propias, manual estricto, semilla 31)
- `paso0_P2.json`: P2 (Paso 0, urgencia_local + aliestesia, manual estricto, sin estrategias propias, semilla 31)
- `cierre0_C1.json`: C1 (Cierre Paso 0, sin estrategias propias, manual estricto, semilla 31)
- `cierre0_C3.json`: C3 (Cierre Paso 0, sin estrategias propias, manual estricto, semilla 32)
- `paso5_G3.json`: G3 (Paso 5, manual estricto, con estrategias propias, semilla 31)
- `paso0_P3.json`: P3 (Paso 0, urgencia_local + aliestesia, manual estricto, con estrategias propias, semilla 31)
- `cierre0_C2.json`: C2 (Cierre Paso 0, manual estricto, con estrategias propias, semilla 31)


---

## 1. Tabla general

| Condición | Opciones exactas | Score (%) | IC 95 % (%) | Episodios | Pasos / ep. | Rendimiento (ms/paso) |
|---|---|---|---|---|---|---|
| **Suelo con linaje** | `--pasos 100000 --semilla 31 --vista oficial --sin-estrategias-propias` | **1,46** | [1,38, 1,52] | 401 | 249,4 | 13,79 |
| **S0** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias` | **1,45** | [1,37, 1,50] | 419 | 238,7 | 9,82 |
| **G1** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto` | **8,81** | [7,91, 9,57] | 410 | 243,9 | 10,81 |
| **P2** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --mecanismos urgencia_local aliestesia` | **10,14** | [9,27, 10,88] | 409 | 244,5 | 10,84 |
| **C1** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto` | **11,29** | [10,44, 12,01] | 416 | 240,4 | 10,35 |
| **C3** | `--pasos 100000 --semilla 32 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto` | **11,05** | [10,21, 11,72] | 423 | 236,4 | 10,50 |
| **G3** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto` | **14,45** | [13,11, 15,48] | 284 | 352,1 | 10,10 |
| **P3** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto --mecanismos urgencia_local aliestesia` | **14,27** | [13,24, 15,09] | 304 | 328,9 | 10,64 |
| **C2** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto` | **15,29** | [14,00, 16,30] | 296 | 337,8 | 9,93 |

---

## 2. Tasas por logro (%)

Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:

| Logro | Suelo con linaje | S0 | G1 | P2 | C1 | C3 | G3 | P3 | C2 |
|---|---|---|---|---|---|---|---|---|---|
| `collect_coal` | 0,00 | 0,00 | 5,12 | 6,11 | 8,89 | 7,09 | 13,73 | 14,47 | 10,81 |
| `collect_diamond` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `collect_drink` | 83,79 | 87,83 | 83,66 | 81,66 | 81,25 | 84,63 | 77,46 | 81,58 | 82,43 |
| `collect_iron` | 0,00 | 0,00 | 0,49 | 0,49 | 0,00 | 0,47 | 0,00 | 0,00 | 0,00 |
| `collect_sapling` | 2,74 | 2,15 | 50,24 | 53,55 | 71,63 | 72,34 | 44,01 | 51,32 | 57,77 |
| `collect_stone` | 0,00 | 0,00 | 22,93 | 32,52 | 33,65 | 35,46 | 53,17 | 50,66 | 53,04 |
| `collect_wood` | 72,07 | 73,75 | 85,85 | 93,15 | 90,62 | 94,33 | 99,65 | 99,34 | 98,99 |
| `defeat_skeleton` | 0,00 | 0,00 | 0,00 | 0,24 | 0,72 | 0,00 | 7,39 | 2,96 | 3,72 |
| `defeat_zombie` | 33,67 | 35,32 | 36,10 | 38,63 | 40,62 | 37,35 | 64,44 | 67,76 | 69,93 |
| `eat_cow` | 63,59 | 63,25 | 67,32 | 69,44 | 69,47 | 70,21 | 58,45 | 70,72 | 67,57 |
| `eat_plant` | 0,00 | 0,00 | 0,24 | 0,00 | 0,00 | 0,24 | 0,70 | 0,00 | 1,01 |
| `make_iron_pickaxe` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_iron_sword` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_stone_pickaxe` | 0,00 | 0,00 | 6,10 | 8,56 | 6,97 | 8,27 | 5,63 | 7,24 | 6,08 |
| `make_stone_sword` | 0,00 | 0,00 | 1,95 | 3,18 | 2,16 | 1,89 | 1,76 | 2,96 | 2,36 |
| `make_wood_pickaxe` | 0,00 | 0,00 | 47,07 | 58,68 | 62,02 | 62,41 | 93,66 | 91,78 | 91,89 |
| `make_wood_sword` | 0,00 | 0,00 | 21,71 | 32,03 | 39,66 | 39,95 | 87,68 | 86,18 | 84,80 |
| `place_furnace` | 0,00 | 0,00 | 1,46 | 3,18 | 15,62 | 15,84 | 6,34 | 7,24 | 14,86 |
| `place_plant` | 0,00 | 0,00 | 47,80 | 52,08 | 69,47 | 69,74 | 42,25 | 47,37 | 56,08 |
| `place_stone` | 0,00 | 0,00 | 18,78 | 27,87 | 30,29 | 31,91 | 47,18 | 44,08 | 49,66 |
| `place_table` | 0,00 | 0,00 | 67,32 | 78,00 | 85,10 | 86,05 | 96,83 | 95,39 | 94,59 |
| `wake_up` | 6,73 | 6,21 | 5,85 | 4,16 | 3,85 | 1,89 | 38,73 | 34,87 | 37,16 |

---

## 3. Causas de muerte por condición

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa | Suelo con linaje | S0 | G1 | P2 | C1 | C3 | G3 | P3 | C2 |
|---|---|---|---|---|---|---|---|---|---|
| `cansancio` | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 1 (0,2 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| `desgaste` | 18 (4,5 %) | 27 (6,4 %) | 17 (4,1 %) | 15 (3,7 %) | 15 (3,6 %) | 13 (3,1 %) | 8 (2,8 %) | 9 (3,0 %) | 6 (2,0 %) |
| `esqueleto` | 28 (7,0 %) | 35 (8,4 %) | 32 (7,8 %) | 27 (6,6 %) | 25 (6,0 %) | 30 (7,1 %) | 56 (19,7 %) | 38 (12,5 %) | 50 (16,9 %) |
| `flecha` | 3 (0,7 %) | 2 (0,5 %) | 1 (0,2 %) | 1 (0,2 %) | 3 (0,7 %) | 5 (1,2 %) | 3 (1,1 %) | 2 (0,7 %) | 3 (1,0 %) |
| `hambre` | 23 (5,7 %) | 29 (6,9 %) | 21 (5,1 %) | 31 (7,6 %) | 22 (5,3 %) | 16 (3,8 %) | 55 (19,4 %) | 53 (17,4 %) | 38 (12,8 %) |
| `lava` | 4 (1,0 %) | 2 (0,5 %) | 6 (1,5 %) | 1 (0,2 %) | 2 (0,5 %) | 2 (0,5 %) | 0 (0,0 %) | 3 (1,0 %) | 4 (1,4 %) |
| `sed` | 24 (6,0 %) | 19 (4,5 %) | 20 (4,9 %) | 13 (3,2 %) | 31 (7,5 %) | 21 (5,0 %) | 38 (13,4 %) | 36 (11,8 %) | 29 (9,8 %) |
| `zombi` | 300 (74,8 %) | 303 (72,3 %) | 312 (76,1 %) | 320 (78,2 %) | 317 (76,2 %) | 333 (78,7 %) | 123 (43,3 %) | 162 (53,3 %) | 164 (55,4 %) |
| `cortado por presupuesto` | 1 (0,2 %) | 2 (0,5 %) | 1 (0,2 %) | 1 (0,2 %) | 1 (0,2 %) | 2 (0,5 %) | 1 (0,4 %) | 1 (0,3 %) | 2 (0,7 %) |
| **Total episodios** | **401** | **419** | **410** | **409** | **416** | **423** | **284** | **304** | **296** |

---

## 4. Comparaciones

Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:

### C1 frente a G1 y P2
- **C1 frente a G1**:
  - Score C1: 11,29 % (IC 95 %: [10,44, 12,01] %)
  - Score G1: 8,81 % (IC 95 %: [7,91, 9,57] %)
  - Diferencia de Score (C1 - G1): +2,48 pp
  - ¿Se solapan los IC 95 %?: **No**

- **C1 frente a P2**:
  - Score C1: 11,29 % (IC 95 %: [10,44, 12,01] %)
  - Score P2: 10,14 % (IC 95 %: [9,27, 10,88] %)
  - Diferencia de Score (C1 - P2): +1,15 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### C2 frente a G3 y P3
- **C2 frente a G3**:
  - Score C2: 15,29 % (IC 95 %: [14,00, 16,30] %)
  - Score G3: 14,45 % (IC 95 %: [13,11, 15,48] %)
  - Diferencia de Score (C2 - G3): +0,84 pp
  - ¿Se solapan los IC 95 %?: **Sí**

- **C2 frente a P3**:
  - Score C2: 15,29 % (IC 95 %: [14,00, 16,30] %)
  - Score P3: 14,27 % (IC 95 %: [13,24, 15,09] %)
  - Diferencia de Score (C2 - P3): +1,02 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### C3 frente a C1
- **C3 frente a C1**:
  - Score C3: 11,05 % (IC 95 %: [10,21, 11,72] %)
  - Score C1: 11,29 % (IC 95 %: [10,44, 12,01] %)
  - Diferencia de Score (C3 - C1): -0,24 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### S0 frente al suelo con linaje
- **S0 frente a Suelo con linaje**:
  - Score S0: 1,45 % (IC 95 %: [1,37, 1,50] %)
  - Score Suelo con linaje: 1,46 % (IC 95 %: [1,38, 1,52] %)
  - Diferencia de Score (S0 - Suelo con linaje): -0,01 pp
  - ¿Se solapan los IC 95 %?: **Sí**

