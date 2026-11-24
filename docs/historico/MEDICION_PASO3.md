# Medición Oficial: Paso 3 (Crafter)

Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto) en la rama `feature/proteger` (commit `c0fd4e3`). Evalúa la capacidad general «proteger X» (el refugio general) y la alostasis.

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `cierre0_C1.json`: C1 (Cierre Paso 0, sin estrategias propias, semilla 31)
- `paso3_L1a.json`: L1a (Paso 3, sin estrategias propias, mecanismo proteger, semilla 31)
- `paso3_L1b.json`: L1b (Paso 3, sin estrategias propias, mecanismos proteger + alostasis, semilla 31)
- `cierre0_C3.json`: C3 (Cierre Paso 0, sin estrategias propias, semilla 32)
- `paso3_L1c.json`: L1c (Paso 3, sin estrategias propias, mecanismo proteger, semilla 32)
- `cierre0_C2.json`: C2 (Cierre Paso 0, con estrategias propias, semilla 31)
- `paso3_L2.json`: L2 (Paso 3, con estrategias propias, mecanismo proteger, semilla 31)


---

## 1. Tabla general

| Métrica | C1 | L1a | L1b | C3 | L1c | C2 | L2 |
|---|---|---|---|---|---|---|---|
| **Score (%)** | **11,29** | **11,95** | **11,70** | **11,05** | **12,41** | **15,29** | **13,12** |
| **IC 95 % (%)** | [10,44, 12,01] | [11,01, 12,76] | [10,86, 12,41] | [10,21, 11,72] | [11,42, 13,24] | [14,00, 16,30] | [11,96, 14,12] |
| **Episodios** | 416 | 384 | 384 | 423 | 387 | 296 | 369 |
| **Pasos por episodio** | 240,4 | 260,4 | 260,4 | 236,4 | 258,4 | 337,8 | 271,0 |
| **ms por paso** | 10,35 | 12,60 | 12,74 | 10,50 | 12,74 | 9,93 | 12,50 |

---

## 2. Tasas por logro (%)

Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:

| Logro | C1 | L1a | L1b | C3 | L1c | C2 | L2 |
|---|---|---|---|---|---|---|---|
| `collect_coal` | 8,89 | 9,38 | 8,33 | 7,09 | 6,46 | 10,81 | 8,94 |
| `collect_diamond` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `collect_drink` | 81,25 | 81,25 | 80,99 | 84,63 | 82,69 | 82,43 | 79,67 |
| `collect_iron` | 0,00 | 0,00 | 0,00 | 0,47 | 0,78 | 0,00 | 0,54 |
| `collect_sapling` | 71,63 | 69,79 | 68,75 | 72,34 | 68,48 | 57,77 | 71,00 |
| `collect_stone` | 33,65 | 35,68 | 35,94 | 35,46 | 37,21 | 53,04 | 36,86 |
| `collect_wood` | 90,62 | 91,15 | 91,15 | 94,33 | 93,80 | 98,99 | 91,33 |
| `defeat_skeleton` | 0,72 | 0,26 | 0,26 | 0,00 | 0,26 | 3,72 | 0,81 |
| `defeat_zombie` | 40,62 | 38,54 | 39,84 | 37,35 | 38,76 | 69,93 | 49,86 |
| `eat_cow` | 69,47 | 68,75 | 68,75 | 70,21 | 71,06 | 67,57 | 69,92 |
| `eat_plant` | 0,00 | 0,78 | 0,52 | 0,24 | 0,52 | 1,01 | 0,81 |
| `make_iron_pickaxe` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_iron_sword` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_stone_pickaxe` | 6,97 | 6,77 | 6,25 | 8,27 | 6,72 | 6,08 | 7,86 |
| `make_stone_sword` | 2,16 | 0,78 | 0,52 | 1,89 | 2,07 | 2,36 | 1,63 |
| `make_wood_pickaxe` | 62,02 | 60,68 | 61,46 | 62,41 | 62,53 | 91,89 | 60,98 |
| `make_wood_sword` | 39,66 | 37,76 | 38,54 | 39,95 | 39,53 | 84,80 | 37,67 |
| `place_furnace` | 15,62 | 17,45 | 17,45 | 15,84 | 16,02 | 14,86 | 18,43 |
| `place_plant` | 69,47 | 67,45 | 66,67 | 69,74 | 66,67 | 56,08 | 68,02 |
| `place_stone` | 30,29 | 31,77 | 31,77 | 31,91 | 33,85 | 49,66 | 34,15 |
| `place_table` | 85,10 | 86,20 | 86,46 | 86,05 | 86,30 | 94,59 | 86,18 |
| `wake_up` | 3,85 | 18,49 | 18,75 | 1,89 | 18,35 | 37,16 | 22,49 |

---

## 3. Causas de muerte por condición

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa | C1 | L1a | L1b | C3 | L1c | C2 | L2 |
|---|---|---|---|---|---|---|---|
| `cansancio` | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 1 (0,2 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| `desgaste` | 15 (3,6 %) | 14 (3,6 %) | 12 (3,1 %) | 13 (3,1 %) | 9 (2,3 %) | 6 (2,0 %) | 14 (3,8 %) |
| `esqueleto` | 25 (6,0 %) | 36 (9,4 %) | 37 (9,6 %) | 30 (7,1 %) | 34 (8,8 %) | 50 (16,9 %) | 30 (8,1 %) |
| `flecha` | 3 (0,7 %) | 0 (0,0 %) | 0 (0,0 %) | 5 (1,2 %) | 2 (0,5 %) | 3 (1,0 %) | 0 (0,0 %) |
| `hambre` | 22 (5,3 %) | 31 (8,1 %) | 31 (8,1 %) | 16 (3,8 %) | 20 (5,2 %) | 38 (12,8 %) | 32 (8,7 %) |
| `lava` | 2 (0,5 %) | 1 (0,3 %) | 1 (0,3 %) | 2 (0,5 %) | 1 (0,3 %) | 4 (1,4 %) | 1 (0,3 %) |
| `sed` | 31 (7,5 %) | 39 (10,2 %) | 38 (9,9 %) | 21 (5,0 %) | 40 (10,3 %) | 29 (9,8 %) | 49 (13,3 %) |
| `zombi` | 317 (76,2 %) | 262 (68,2 %) | 264 (68,8 %) | 333 (78,7 %) | 279 (72,1 %) | 164 (55,4 %) | 242 (65,6 %) |
| `cortado por presupuesto` | 1 (0,2 %) | 1 (0,3 %) | 1 (0,3 %) | 2 (0,5 %) | 2 (0,5 %) | 2 (0,7 %) | 1 (0,3 %) |
| **Total episodios** | **416** | **384** | **384** | **423** | **387** | **296** | **369** |

---

## 4. Comparaciones

Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:

### L1a frente a C1
- **L1a frente a C1**:
  - Score L1a: 11,95 % (IC 95 %: [11,01, 12,76] %)
  - Score C1: 11,29 % (IC 95 %: [10,44, 12,01] %)
  - Diferencia de Score (L1a - C1): +0,66 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### L1b frente a L1a
- **L1b frente a L1a**:
  - Score L1b: 11,70 % (IC 95 %: [10,86, 12,41] %)
  - Score L1a: 11,95 % (IC 95 %: [11,01, 12,76] %)
  - Diferencia de Score (L1b - L1a): -0,25 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### L1c frente a C3
- **L1c frente a C3**:
  - Score L1c: 12,41 % (IC 95 %: [11,42, 13,24] %)
  - Score C3: 11,05 % (IC 95 %: [10,21, 11,72] %)
  - Diferencia de Score (L1c - C3): +1,36 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### L2 frente a C2
- **L2 frente a C2**:
  - Score L2: 13,12 % (IC 95 %: [11,96, 14,12] %)
  - Score C2: 15,29 % (IC 95 %: [14,00, 16,30] %)
  - Diferencia de Score (L2 - C2): -2,17 pp
  - ¿Se solapan los IC 95 %?: **Sí**

