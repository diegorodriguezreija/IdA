# Medición Deuda 14: Cadena de herramientas (K1: lote_estacion)

Medición de K1 (subpaso 14.2, interruptor `lote_estacion`) de la Deuda 14 en la rama `feature/deuda14`, evaluado en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto, plazo lógico 40) y comparado de forma pareada contra la referencia `base_v2` en las semillas 31 y 32.

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `datos/evaluacion/base_v2_31.json`: referencia `base_v2`, semilla 31
- `datos/evaluacion/deuda14_K1_31.json`: condición K1 (`lote_estacion`), semilla 31
- `datos/evaluacion/base_v2_32.json`: referencia `base_v2`, semilla 32
- `datos/evaluacion/deuda14_K1_32.json`: condición K1 (`lote_estacion`), semilla 32

---

## 1. Tabla general

| Métrica | base_v2_31 | K1_31 | base_v2_32 | K1_32 |
|---|---|---|---|---|
| **Score (%)** | 14,04 | 14,83 | 15,45 | 15,98 |
| **IC 95 % (%)** | [12,92, 15,06] | [13,71, 15,84] | [14,18, 16,53] | [14,81, 16,96] |
| **Episodios** | 383 | 382 | 365 | 378 |
| **Pasos por episodio** | 261,1 | 261,8 | 274,0 | 264,6 |
| **Latidos cortados** | 0 | 0 | 0 | 0 |

---

## 2. Comparaciones pareadas

### deuda14_K1_31 frente a base_v2_31 (semilla base 31, 382 episodios pareados de 382 y 383, 2000 réplicas)

Score en los episodios pareados: 14,83 % frente a 14,06 %.

| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |
|---|---|---|---|
| **Score** | 0,76 | [-0,09, 1,57] | No |
| `collect_coal` | -1,57 | [-4,19, 0,79] | No |
| `collect_diamond` | 0,00 | [0,00, 0,00] | No |
| `collect_drink` | -3,40 | [-6,28, -0,79] | **Sí** |
| `collect_iron` | 0,00 | [-0,79, 0,79] | No |
| `collect_sapling` | -1,57 | [-4,45, 1,31] | No |
| `collect_stone` | 1,05 | [-2,36, 4,45] | No |
| `collect_wood` | 0,00 | [0,00, 0,00] | No |
| `defeat_skeleton` | 0,52 | [-1,57, 2,62] | No |
| `defeat_zombie` | 3,66 | [-0,52, 8,12] | No |
| `eat_cow` | -2,36 | [-4,97, 0,26] | No |
| `eat_plant` | 0,00 | [0,00, 0,00] | No |
| `make_iron_pickaxe` | 0,00 | [0,00, 0,00] | No |
| `make_iron_sword` | 0,00 | [0,00, 0,00] | No |
| `make_stone_pickaxe` | 3,40 | [1,31, 5,76] | **Sí** |
| `make_stone_sword` | 3,66 | [1,57, 6,02] | **Sí** |
| `make_wood_pickaxe` | 1,31 | [-1,57, 4,19] | No |
| `make_wood_sword` | 5,50 | [1,83, 9,42] | **Sí** |
| `place_furnace` | 0,00 | [-3,40, 3,14] | No |
| `place_plant` | -0,52 | [-3,14, 2,36] | No |
| `place_stone` | 0,79 | [-2,36, 4,19] | No |
| `place_table` | 0,00 | [0,00, 0,00] | No |
| `wake_up` | -2,09 | [-5,76, 1,31] | No |

### deuda14_K1_32 frente a base_v2_32 (semilla base 32, 365 episodios pareados de 378 y 365, 2000 réplicas)

Score en los episodios pareados: 16,02 % frente a 15,45 %.

| Medida | Diferencia (pp) | IC 95 % pareado (pp) | ¿Excluye el 0? |
|---|---|---|---|
| **Score** | 0,57 | [-0,30, 1,43] | No |
| `collect_coal` | -0,82 | [-3,84, 2,19] | No |
| `collect_diamond` | 0,00 | [0,00, 0,00] | No |
| `collect_drink` | 0,00 | [-2,47, 2,47] | No |
| `collect_iron` | 0,27 | [0,00, 0,82] | No |
| `collect_sapling` | -1,37 | [-4,66, 1,92] | No |
| `collect_stone` | 0,00 | [-3,56, 3,56] | No |
| `collect_wood` | 0,00 | [0,00, 0,00] | No |
| `defeat_skeleton` | 0,27 | [-1,64, 2,47] | No |
| `defeat_zombie` | 2,74 | [-1,92, 7,40] | No |
| `eat_cow` | -2,19 | [-5,21, 0,82] | No |
| `eat_plant` | -0,27 | [-0,82, 0,00] | No |
| `make_iron_pickaxe` | 0,00 | [0,00, 0,00] | No |
| `make_iron_sword` | 0,00 | [0,00, 0,00] | No |
| `make_stone_pickaxe` | 3,29 | [0,27, 6,58] | **Sí** |
| `make_stone_sword` | 4,11 | [1,37, 7,12] | **Sí** |
| `make_wood_pickaxe` | -0,27 | [-3,01, 2,74] | No |
| `make_wood_sword` | 7,12 | [3,01, 11,23] | **Sí** |
| `place_furnace` | -2,74 | [-5,75, 0,27] | No |
| `place_plant` | -1,92 | [-4,93, 1,10] | No |
| `place_stone` | 1,92 | [-1,64, 5,48] | No |
| `place_table` | 0,00 | [0,00, 0,00] | No |
| `wake_up` | -0,55 | [-4,11, 3,01] | No |

---

## 3. Causas de muerte

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa de muerte / finalización | base_v2_31 (383 ep) | K1_31 (382 ep) | base_v2_32 (365 ep) | K1_32 (378 ep) |
|---|---|---|---|---|
| `zombi` | 271 (70,8 %) | 278 (72,8 %) | 253 (69,3 %) | 276 (73,0 %) |
| `sed` | 45 (11,7 %) | 44 (11,5 %) | 55 (15,1 %) | 50 (13,2 %) |
| `hambre` | 36 (9,4 %) | 35 (9,2 %) | 27 (7,4 %) | 30 (7,9 %) |
| `flecha` | 27 (7,0 %) | 22 (5,8 %) | 27 (7,4 %) | 21 (5,6 %) |
| `cortado por presupuesto` | 3 (0,8 %) | 2 (0,5 %) | 1 (0,3 %) | 1 (0,3 %) |
| `desgaste` | 1 (0,3 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| `cansancio` | 0 (0,0 %) | 1 (0,3 %) | 0 (0,0 %) | 0 (0,0 %) |
| `lava` | 0 (0,0 %) | 0 (0,0 %) | 2 (0,5 %) | 0 (0,0 %) |
