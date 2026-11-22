# Medición Mecanismo: Material Mapa (`material_mapa`)

Medición del mecanismo `material_mapa` en la rama `feature/material-mapa`, evaluado en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto, plazo lógico 40) y comparado de forma pareada contra la referencia (`main` con 11c apagado, `v3`) en las semillas 31 y 32.

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `datos/evaluacion/v3_31.json`: referencia `v3` (`main` con 11c apagado), semilla 31
- `datos/evaluacion/mapa_31.json`: condición `material_mapa`, semilla 31
- `datos/evaluacion/v3_32.json`: referencia `v3` (`main` con 11c apagado), semilla 32
- `datos/evaluacion/mapa_32.json`: condición `material_mapa`, semilla 32

---

## 1. Tabla general

| Métrica | v3_31 | mapa_31 | v3_32 | mapa_32 |
|---|---|---|---|---|
| **Score (%)** | 14,83 | 15,86 | 15,98 | 17,34 |
| **IC 95 % (%)** | [13,71, 15,84] | [14,58, 17,07] | [14,81, 16,96] | [16,06, 18,47] |
| **Episodios** | 382 | 377 | 378 | 360 |
| **Pasos por episodio** | 261,8 | 265,3 | 264,6 | 277,8 |
| **Latidos cortados** | 0 | 0 | 0 | 0 |

---

## 2. Comparaciones pareadas

### Comparación pareada conjunta (737 episodios pareados, 2000 réplicas estratificadas por semilla)

Pares: mapa_31 frente a v3_31 (semilla base 31, 377 pareados de 377 y 382); mapa_32 frente a v3_32 (semilla base 32, 360 pareados de 360 y 378).

Score en los episodios pareados: 16,59 % frente a 15,51 %.

| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |
|---|---|---|---|
| **Score** | 1,08 | [0,17, 2,10] | **Sí** |
| `collect_coal` | 4,07 | [1,36, 7,06] | **Sí** |
| `collect_diamond` | 0,00 | [0,00, 0,00] | No |
| `collect_drink` | -0,54 | [-3,66, 2,31] | No |
| `collect_iron` | 0,54 | [-0,14, 1,36] | No |
| `collect_sapling` | -7,33 | [-10,99, -3,66] | **Sí** |
| `collect_stone` | 7,73 | [3,66, 11,94] | **Sí** |
| `collect_wood` | 1,90 | [0,27, 3,66] | **Sí** |
| `defeat_skeleton` | 0,81 | [-1,49, 3,26] | No |
| `defeat_zombie` | 1,49 | [-3,26, 6,24] | No |
| `eat_cow` | -4,61 | [-8,01, -1,09] | **Sí** |
| `eat_plant` | 0,00 | [-0,68, 0,68] | No |
| `make_iron_pickaxe` | 0,00 | [0,00, 0,00] | No |
| `make_iron_sword` | 0,00 | [0,00, 0,00] | No |
| `make_stone_pickaxe` | 0,00 | [-2,71, 2,85] | No |
| `make_stone_sword` | 1,36 | [-1,22, 3,93] | No |
| `make_wood_pickaxe` | 6,92 | [3,39, 10,45] | **Sí** |
| `make_wood_sword` | 4,48 | [0,41, 8,55] | **Sí** |
| `place_furnace` | 3,26 | [-0,41, 7,06] | No |
| `place_plant` | -6,51 | [-10,31, -2,71] | **Sí** |
| `place_stone` | 7,19 | [3,12, 11,40] | **Sí** |
| `place_table` | 2,85 | [0,54, 5,29] | **Sí** |
| `wake_up` | 1,63 | [-1,90, 5,56] | No |

### mapa_31 frente a v3_31 (semilla base 31, 377 episodios pareados de 377 y 382, 2000 réplicas)

Score en los episodios pareados: 15,86 % frente a 14,89 %.

| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |
|---|---|---|---|
| **Score** | 0,97 | [-0,51, 2,39] | No |
| `collect_coal` | 3,98 | [0,00, 7,96] | No |
| `collect_diamond` | 0,00 | [0,00, 0,00] | No |
| `collect_drink` | -1,33 | [-5,84, 2,92] | No |
| `collect_iron` | 0,53 | [-0,53, 1,59] | No |
| `collect_sapling` | -8,75 | [-13,79, -4,24] | **Sí** |
| `collect_stone` | 5,04 | [-1,06, 10,88] | No |
| `collect_wood` | 2,39 | [-0,27, 5,04] | No |
| `defeat_skeleton` | -0,80 | [-4,51, 2,65] | No |
| `defeat_zombie` | 1,06 | [-5,57, 7,43] | No |
| `eat_cow` | -5,57 | [-10,61, -0,80] | **Sí** |
| `eat_plant` | 0,00 | [-0,80, 0,80] | No |
| `make_iron_pickaxe` | 0,00 | [0,00, 0,00] | No |
| `make_iron_sword` | 0,00 | [0,00, 0,00] | No |
| `make_stone_pickaxe` | 1,06 | [-2,92, 5,04] | No |
| `make_stone_sword` | 2,92 | [-0,53, 6,10] | No |
| `make_wood_pickaxe` | 6,90 | [1,86, 11,94] | **Sí** |
| `make_wood_sword` | 5,57 | [0,27, 10,88] | **Sí** |
| `place_furnace` | 2,12 | [-3,18, 7,43] | No |
| `place_plant` | -7,69 | [-12,73, -2,65] | **Sí** |
| `place_stone` | 5,31 | [-0,80, 11,14] | No |
| `place_table` | 1,06 | [-2,65, 4,51] | No |
| `wake_up` | 0,53 | [-4,77, 5,57] | No |

### mapa_32 frente a v3_32 (semilla base 32, 360 episodios pareados de 360 y 378, 2000 réplicas)

Score en los episodios pareados: 17,34 % frente a 16,06 %.

| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |
|---|---|---|---|
| **Score** | 1,28 | [-0,08, 2,72] | No |
| `collect_coal` | 4,17 | [0,00, 8,61] | No |
| `collect_diamond` | 0,00 | [0,00, 0,00] | No |
| `collect_drink` | 0,28 | [-4,17, 4,72] | No |
| `collect_iron` | 0,56 | [-0,56, 1,67] | No |
| `collect_sapling` | -5,83 | [-11,11, -0,56] | **Sí** |
| `collect_stone` | 10,56 | [4,44, 16,67] | **Sí** |
| `collect_wood` | 1,39 | [-0,56, 3,33] | No |
| `defeat_skeleton` | 2,50 | [-0,56, 5,83] | No |
| `defeat_zombie` | 1,94 | [-5,28, 8,89] | No |
| `eat_cow` | -3,61 | [-8,33, 1,39] | No |
| `eat_plant` | 0,00 | [-1,11, 1,11] | No |
| `make_iron_pickaxe` | 0,00 | [0,00, 0,00] | No |
| `make_iron_sword` | 0,00 | [0,00, 0,00] | No |
| `make_stone_pickaxe` | -1,11 | [-5,56, 3,33] | No |
| `make_stone_sword` | -0,28 | [-4,17, 3,89] | No |
| `make_wood_pickaxe` | 6,94 | [1,94, 11,94] | **Sí** |
| `make_wood_sword` | 3,33 | [-3,06, 9,17] | No |
| `place_furnace` | 4,44 | [-0,56, 9,72] | No |
| `place_plant` | -5,28 | [-10,56, 0,28] | No |
| `place_stone` | 9,17 | [3,33, 15,28] | **Sí** |
| `place_table` | 4,72 | [1,67, 8,06] | **Sí** |
| `wake_up` | 2,78 | [-3,06, 8,33] | No |

---

## 3. Causas de muerte

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa de muerte / finalización | v3_31 (382 ep) | mapa_31 (377 ep) | v3_32 (378 ep) | mapa_32 (360 ep) |
|---|---|---|---|---|
| `zombi` | 278 (72,8 %) | 270 (71,6 %) | 276 (73,0 %) | 250 (69,4 %) |
| `sed` | 44 (11,5 %) | 43 (11,4 %) | 50 (13,2 %) | 36 (10,0 %) |
| `hambre` | 35 (9,2 %) | 32 (8,5 %) | 30 (7,9 %) | 36 (10,0 %) |
| `flecha` | 22 (5,8 %) | 31 (8,2 %) | 21 (5,6 %) | 34 (9,4 %) |
| `cortado por presupuesto` | 2 (0,5 %) | 1 (0,3 %) | 1 (0,3 %) | 2 (0,6 %) |
| `cansancio` | 1 (0,3 %) | 0 (0,0 %) | 0 (0,0 %) | 1 (0,3 %) |
| `esqueleto` | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 1 (0,3 %) |
