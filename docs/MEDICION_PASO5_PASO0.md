# Medición Oficial: Paso 5 y Paso 0 (Crafter)

Evaluación oficial en Crafter (100.000 pasos, semilla base 31, vista oficial, sin herencia) en la rama `feature/paso0` (commit `43f636c`).

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `suelo_main.json`: suelo de referencia (`main` sin estrategias)
- `main_sin_herencia.json`: referencia `main` con estrategias y sin herencia
- `paso5_G1.json`: G1 (Paso 5, sin estrategias propias, manual estricto)
- `paso5_G2.json`: G2 (Paso 5, sin estrategias propias, manual ampliado)
- `paso5_G3.json`: G3 (Paso 5, manual estricto)
- `paso5_G4.json`: G4 (Paso 5, manual ampliado)
- `paso0_P1.json`: P1 (Paso 0, urgencia_local, manual estricto, sin estrategias propias)
- `paso0_P2.json`: P2 (Paso 0, urgencia_local + aliestesia, manual estricto, sin estrategias propias)
- `paso0_P3.json`: P3 (Paso 0, urgencia_local + aliestesia, manual estricto, con estrategias)


---

## 1. Tabla general

| Condición | Opciones exactas | Score (%) | IC 95 % (%) | Episodios | Pasos / ep. | Rendimiento (ms/paso) |
|---|---|---|---|---|---|---|
| **Suelo (referencia `main`)** | `--pasos 100000 --semilla 31 --vista oficial --sin-estrategias-propias` | **1,46** | [1,38, 1,52] | 401 | 249,4 | 13,79 |
| **`main` sin herencia** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia` | **19,18** | [17,74, 20,46] | 278 | 359,7 | 12,06 |
| **G1 (Paso 5)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto` | **8,81** | [7,91, 9,57] | 410 | 243,9 | 10,81 |
| **G2 (Paso 5)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual ampliado` | **11,52** | [10,63, 12,28] | 413 | 242,1 | 11,09 |
| **G3 (Paso 5)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto` | **14,45** | [13,11, 15,48] | 284 | 352,1 | 10,10 |
| **G4 (Paso 5)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual ampliado` | **15,49** | [14,16, 16,70] | 300 | 333,3 | 10,60 |
| **P1 (Paso 0)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --mecanismos urgencia_local` | **8,85** | [7,97, 9,61] | 412 | 242,7 | 10,84 |
| **P2 (Paso 0)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --sin-estrategias-propias --manual estricto --mecanismos urgencia_local aliestesia` | **10,14** | [9,27, 10,88] | 409 | 244,5 | 10,84 |
| **P3 (Paso 0)** | `--pasos 100000 --semilla 31 --vista oficial --sin-herencia --manual estricto --mecanismos urgencia_local aliestesia` | **14,27** | [13,24, 15,09] | 304 | 328,9 | 10,64 |

---

## 2. Tasas por logro (%)

Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:

| Logro | Suelo | `main` | G1 | G2 | G3 | G4 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|
| `collect_coal` | 0,00 | 20,50 | 5,12 | 14,77 | 13,73 | 18,33 | 5,34 | 6,11 | 14,47 |
| `collect_diamond` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `collect_drink` | 83,79 | 79,86 | 83,66 | 82,32 | 77,46 | 80,00 | 83,50 | 81,66 | 81,58 |
| `collect_iron` | 0,00 | 0,36 | 0,49 | 0,73 | 0,00 | 0,67 | 0,49 | 0,49 | 0,00 |
| `collect_sapling` | 2,74 | 98,56 | 50,24 | 40,19 | 44,01 | 37,67 | 51,21 | 53,55 | 51,32 |
| `collect_stone` | 0,00 | 69,06 | 22,93 | 36,32 | 53,17 | 53,33 | 23,30 | 32,52 | 50,66 |
| `collect_wood` | 72,07 | 100,00 | 85,85 | 93,95 | 99,65 | 99,67 | 85,92 | 93,15 | 99,34 |
| `defeat_skeleton` | 0,00 | 43,17 | 0,00 | 0,24 | 7,39 | 6,33 | 0,00 | 0,24 | 2,96 |
| `defeat_zombie` | 33,67 | 64,03 | 36,10 | 39,47 | 64,44 | 66,00 | 34,71 | 38,63 | 67,76 |
| `eat_cow` | 63,59 | 60,07 | 67,32 | 71,67 | 58,45 | 63,33 | 68,45 | 69,44 | 70,72 |
| `eat_plant` | 0,00 | 0,36 | 0,24 | 0,24 | 0,70 | 0,33 | 0,49 | 0,00 | 0,00 |
| `make_iron_pickaxe` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_iron_sword` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_stone_pickaxe` | 0,00 | 7,55 | 6,10 | 6,54 | 5,63 | 7,00 | 6,07 | 8,56 | 7,24 |
| `make_stone_sword` | 0,00 | 2,52 | 1,95 | 1,94 | 1,76 | 1,33 | 1,70 | 3,18 | 2,96 |
| `make_wood_pickaxe` | 0,00 | 96,40 | 47,07 | 64,89 | 93,66 | 94,33 | 47,57 | 58,68 | 91,78 |
| `make_wood_sword` | 0,00 | 91,73 | 21,71 | 41,16 | 87,68 | 91,00 | 21,36 | 32,03 | 86,18 |
| `place_furnace` | 0,00 | 13,31 | 1,46 | 19,37 | 6,34 | 22,33 | 1,46 | 3,18 | 7,24 |
| `place_plant` | 0,00 | 98,56 | 47,80 | 39,23 | 42,25 | 36,67 | 48,54 | 52,08 | 47,37 |
| `place_stone` | 0,00 | 62,59 | 18,78 | 33,41 | 47,18 | 47,33 | 18,93 | 27,87 | 44,08 |
| `place_table` | 0,00 | 98,92 | 67,32 | 88,14 | 96,83 | 98,33 | 67,48 | 78,00 | 95,39 |
| `wake_up` | 6,73 | 51,44 | 5,85 | 5,08 | 38,73 | 36,67 | 5,34 | 4,16 | 34,87 |

---

## 3. Causas de muerte por condición

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa | Suelo | `main` | G1 | G2 | G3 | G4 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|---|---|---|
| `desgaste` | 18 (4,5 %) | 18 (6,5 %) | 17 (4,1 %) | 16 (3,9 %) | 8 (2,8 %) | 0 (0,0 %) | 12 (2,9 %) | 15 (3,7 %) | 9 (3,0 %) |
| `esqueleto` | 28 (7,0 %) | 62 (22,3 %) | 32 (7,8 %) | 31 (7,5 %) | 56 (19,7 %) | 48 (16,0 %) | 36 (8,7 %) | 27 (6,6 %) | 38 (12,5 %) |
| `flecha` | 3 (0,7 %) | 4 (1,4 %) | 1 (0,2 %) | 1 (0,2 %) | 3 (1,1 %) | 2 (0,7 %) | 3 (0,7 %) | 1 (0,2 %) | 2 (0,7 %) |
| `hambre` | 23 (5,7 %) | 49 (17,6 %) | 21 (5,1 %) | 30 (7,3 %) | 55 (19,4 %) | 51 (17,0 %) | 17 (4,1 %) | 31 (7,6 %) | 53 (17,4 %) |
| `lava` | 4 (1,0 %) | 1 (0,4 %) | 6 (1,5 %) | 3 (0,7 %) | 0 (0,0 %) | 3 (1,0 %) | 5 (1,2 %) | 1 (0,2 %) | 3 (1,0 %) |
| `sed` | 24 (6,0 %) | 38 (13,7 %) | 20 (4,9 %) | 25 (6,1 %) | 38 (13,4 %) | 38 (12,7 %) | 18 (4,4 %) | 13 (3,2 %) | 36 (11,8 %) |
| `zombi` | 300 (74,8 %) | 105 (37,8 %) | 312 (76,1 %) | 306 (74,1 %) | 123 (43,3 %) | 157 (52,3 %) | 320 (77,7 %) | 320 (78,2 %) | 162 (53,3 %) |
| `cortado por presupuesto` | 1 (0,2 %) | 1 (0,4 %) | 1 (0,2 %) | 1 (0,2 %) | 1 (0,4 %) | 1 (0,3 %) | 1 (0,2 %) | 1 (0,2 %) | 1 (0,3 %) |
| **Total episodios** | **401** | **278** | **410** | **413** | **284** | **300** | **412** | **409** | **304** |

---

## 4. Comparaciones

Diferencias de Crafter Score (en puntos porcentuales) y comprobación de solapamiento de intervalos de confianza al 95 %:

### G1 frente al suelo
- **G1 frente a Suelo (`main`)**:
  - Score G1: 8,81 % (IC 95 %: [7,91, 9,57] %)
  - Score Suelo (`main`): 1,46 % (IC 95 %: [1,38, 1,52] %)
  - Diferencia de Score (G1 - Suelo (`main`)): +7,35 pp
  - ¿Se solapan los IC 95 %?: **No**

### G3 y G4 frente a `main` sin herencia
- **G3 frente a `main` sin herencia**:
  - Score G3: 14,45 % (IC 95 %: [13,11, 15,48] %)
  - Score `main` sin herencia: 19,18 % (IC 95 %: [17,74, 20,46] %)
  - Diferencia de Score (G3 - `main` sin herencia): -4,73 pp
  - ¿Se solapan los IC 95 %?: **No**

- **G4 frente a `main` sin herencia**:
  - Score G4: 15,49 % (IC 95 %: [14,16, 16,70] %)
  - Score `main` sin herencia: 19,18 % (IC 95 %: [17,74, 20,46] %)
  - Diferencia de Score (G4 - `main` sin herencia): -3,69 pp
  - ¿Se solapan los IC 95 %?: **No**

### P1 y P2 frente a G1
- **P1 frente a G1**:
  - Score P1: 8,85 % (IC 95 %: [7,97, 9,61] %)
  - Score G1: 8,81 % (IC 95 %: [7,91, 9,57] %)
  - Diferencia de Score (P1 - G1): +0,04 pp
  - ¿Se solapan los IC 95 %?: **Sí**

- **P2 frente a G1**:
  - Score P2: 10,14 % (IC 95 %: [9,27, 10,88] %)
  - Score G1: 8,81 % (IC 95 %: [7,91, 9,57] %)
  - Diferencia de Score (P2 - G1): +1,33 pp
  - ¿Se solapan los IC 95 %?: **Sí**

### P3 frente a G3
- **P3 frente a G3**:
  - Score P3: 14,27 % (IC 95 %: [13,24, 15,09] %)
  - Score G3: 14,45 % (IC 95 %: [13,11, 15,48] %)
  - Diferencia de Score (P3 - G3): -0,18 pp
  - ¿Se solapan los IC 95 %?: **Sí**


---

## 5. Salida literal de `invariancia.py`

```
minimo: OK
archivos: OK
crafter: semilla 1, latido 1: objetivo 'hierba_31_32' -> 'hierba_32_33' | semilla 2, latido 1: decisión 'COGER' -> 'MOVER' | semilla 3, latido 1: decisión 'COGER' -> 'MOVER'
ajedrez: OK
```
