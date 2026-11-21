# Medición Oficial: Paso 6 — La defensa general (Crafter)

Evaluación oficial en Crafter (100.000 pasos, vista oficial, sin herencia, manual estricto, sin estrategias propias) en la rama `feature/defensa` (commit `027062e` para D1-D3; commit `b9daf9c` para D4). Evalúa el paso 6: la defensa general (peligro aprendido, afrontar —luchar o huir— y arma como meta instrumental) y la retirada de las estrategias propias de Crafter (paso 6d, pilar 1).

Ficheros de datos utilizados (en `datos/evaluacion/`):
- `paso3_F1.json`: F1 (Referencia Paso 3, semilla 31, sin estrategias propias)
- `paso6_D1.json`: D1 (Paso 6a, semilla 31, mecanismo `peligro_aprendido`)
- `paso6_D2.json`: D2 (Paso 6 completo, semilla 31, mecanismos `peligro_aprendido`, `afrontar`, `arma_instrumental`)
- `paso6_D4.json`: D4 (Paso 6d en base, semilla 31, sin estrategias propias ni mecanismos)
- `paso3_F2.json`: F2 (Referencia Paso 3, semilla 32, sin estrategias propias)
- `paso6_D3.json`: D3 (Paso 6 completo, semilla 32, mecanismos `peligro_aprendido`, `afrontar`, `arma_instrumental`)

### Control de latidos cortados (guillotina de 100 ms)

Criterio de validez: una medición es válida si registra 10 latidos cortados o menos (menos del 0,01 % de los latidos). En las mediciones evaluadas:
- **F1**: 4 latidos cortados en 4 episodios (0,004 % de los latidos).
- **D1**: 0 latidos cortados.
- **D2**: 0 latidos cortados.
- **D4**: 1 latido cortado en 1 episodio (episodio 64; 0,001 % de los latidos).
- **F2**: 6 latidos cortados en 4 episodios (0,006 % de los latidos).
- **D3**: 0 latidos cortados.


---

## 1. Tabla general

| Métrica | F1 | D1 | D2 | D4 | F2 | D3 |
|---|---|---|---|---|---|---|
| **Score (%)** | **12,82** | **12,47** | **14,04** | **14,04** | **13,58** | **15,45** |
| **IC 95 % (%)** | [11,76, 13,79] | [11,52, 13,24] | [12,92, 15,06] | [12,92, 15,06] | [12,52, 14,47] | [14,18, 16,53] |
| **Episodios** | 380 | 389 | 383 | 383 | 380 | 365 |
| **Pasos por episodio** | 263,2 | 257,1 | 261,1 | 261,1 | 263,2 | 274,0 |
| **ms por paso** | 12,59 | 12,32 | 12,12 | 11,93 | 12,43 | 11,96 |
| **Latidos cortados** | 4 | 0 | 0 | 1 | 6 | 0 |

---

## 2. Tasas por logro (%)

Porcentaje de episodios donde se obtuvo cada uno de los 22 logros oficiales de Crafter:

| Logro | F1 | D1 | D2 | D4 | F2 | D3 |
|---|---|---|---|---|---|---|
| `collect_coal` | 11,84 | 11,05 | 11,49 | 11,49 | 9,21 | 12,05 |
| `collect_diamond` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `collect_drink` | 81,58 | 81,23 | 80,42 | 80,42 | 82,37 | 81,64 |
| `collect_iron` | 0,26 | 0,00 | 0,26 | 0,26 | 0,53 | 0,27 |
| `collect_sapling` | 73,16 | 72,24 | 72,32 | 72,32 | 69,47 | 71,51 |
| `collect_stone` | 37,11 | 37,02 | 38,38 | 38,38 | 42,89 | 43,01 |
| `collect_wood` | 91,05 | 90,23 | 90,08 | 90,08 | 93,95 | 93,70 |
| `defeat_skeleton` | 0,53 | 0,26 | 7,83 | 7,83 | 0,00 | 5,21 |
| `defeat_zombie` | 38,42 | 38,30 | 40,21 | 40,21 | 37,63 | 40,27 |
| `eat_cow` | 69,47 | 68,64 | 71,02 | 71,02 | 73,42 | 74,25 |
| `eat_plant` | 0,26 | 0,26 | 0,26 | 0,26 | 0,79 | 0,82 |
| `make_iron_pickaxe` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_iron_sword` | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `make_stone_pickaxe` | 6,32 | 7,20 | 6,79 | 6,79 | 9,21 | 10,41 |
| `make_stone_sword` | 2,37 | 2,57 | 2,35 | 2,35 | 5,00 | 6,03 |
| `make_wood_pickaxe` | 63,95 | 63,75 | 62,40 | 62,40 | 68,68 | 71,51 |
| `make_wood_sword` | 43,16 | 42,93 | 42,56 | 42,56 | 46,05 | 47,12 |
| `place_furnace` | 19,21 | 19,02 | 20,89 | 20,89 | 18,95 | 22,47 |
| `place_plant` | 69,47 | 68,64 | 68,67 | 68,67 | 67,89 | 69,86 |
| `place_stone` | 33,95 | 32,65 | 34,46 | 34,46 | 37,11 | 37,81 |
| `place_table` | 86,05 | 84,58 | 83,81 | 83,81 | 86,32 | 87,12 |
| `wake_up` | 20,53 | 18,25 | 20,63 | 20,63 | 21,32 | 23,56 |

---

## 3. Causas de muerte por condición

Número de episodios y porcentaje sobre el total de episodios de cada condición:

| Causa | F1 | D1 | D2 | D4 | F2 | D3 |
|---|---|---|---|---|---|---|
| `desgaste` | 12 (3,2 %) | 0 (0,0 %) | 1 (0,3 %) | 1 (0,3 %) | 9 (2,4 %) | 0 (0,0 %) |
| `esqueleto` | 36 (9,5 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 35 (9,2 %) | 0 (0,0 %) |
| `flecha` | 1 (0,3 %) | 32 (8,2 %) | 27 (7,0 %) | 26 (6,8 %) | 1 (0,3 %) | 27 (7,4 %) |
| `hambre` | 32 (8,4 %) | 28 (7,2 %) | 36 (9,4 %) | 36 (9,4 %) | 29 (7,6 %) | 27 (7,4 %) |
| `lava` | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 2 (0,5 %) | 2 (0,5 %) |
| `sed` | 38 (10,0 %) | 45 (11,6 %) | 45 (11,7 %) | 45 (11,7 %) | 38 (10,0 %) | 55 (15,1 %) |
| `zombi` | 260 (68,4 %) | 283 (72,8 %) | 271 (70,8 %) | 272 (71,0 %) | 266 (70,0 %) | 253 (69,3 %) |
| `zombi + desgaste` | 272 (71,6 %) | 283 (72,8 %) | 272 (71,0 %) | 273 (71,3 %) | 275 (72,4 %) | 253 (69,3 %) |
| `cortado por presupuesto` | 1 (0,3 %) | 1 (0,3 %) | 3 (0,8 %) | 3 (0,8 %) | 0 (0,0 %) | 1 (0,3 %) |
| **Total episodios** | **380** | **389** | **383** | **383** | **380** | **365** |

---

## 4. Comparaciones

Diferencias de Crafter Score (en puntos porcentuales), comprobación de solapamiento de intervalos de confianza al 95 % y diferencias en logros clave de combate (`defeat_zombie` y `defeat_skeleton`):

### D1 frente a F1 (semilla 31, peligro aprendido)
- **D1 frente a F1**:
  - Score D1: 12,47 % (IC 95 %: [11,52, 13,24] %)
  - Score F1: 12,82 % (IC 95 %: [11,76, 13,79] %)
  - Diferencia de Score (D1 - F1): -0,35 pp
  - ¿Se solapan los IC 95 %?: **Sí**
  - `defeat_zombie`: 38,30 % frente a 38,42 % (-0,12 pp)
  - `defeat_skeleton`: 0,26 % frente a 0,53 % (-0,27 pp)

### D2 frente a F1 y a D1 (semilla 31, defensa completa)
- **D2 frente a F1**:
  - Score D2: 14,04 % (IC 95 %: [12,92, 15,06] %)
  - Score F1: 12,82 % (IC 95 %: [11,76, 13,79] %)
  - Diferencia de Score (D2 - F1): +1,22 pp
  - ¿Se solapan los IC 95 %?: **Sí**
  - `defeat_zombie`: 40,21 % frente a 38,42 % (+1,79 pp)
  - `defeat_skeleton`: 7,83 % frente a 0,53 % (+7,30 pp)

- **D2 frente a D1**:
  - Score D2: 14,04 % (IC 95 %: [12,92, 15,06] %)
  - Score D1: 12,47 % (IC 95 %: [11,52, 13,24] %)
  - Diferencia de Score (D2 - D1): +1,57 pp
  - ¿Se solapan los IC 95 %?: **Sí**
  - `defeat_zombie`: 40,21 % frente a 38,30 % (+1,91 pp)
  - `defeat_skeleton`: 7,83 % frente a 0,26 % (+7,57 pp)

### D3 frente a F2 (semilla 32, defensa completa)
- **D3 frente a F2**:
  - Score D3: 15,45 % (IC 95 %: [14,18, 16,53] %)
  - Score F2: 13,58 % (IC 95 %: [12,52, 14,47] %)
  - Diferencia de Score (D3 - F2): +1,87 pp
  - ¿Se solapan los IC 95 %?: **Sí**
  - `defeat_zombie`: 40,27 % frente a 37,63 % (+2,64 pp)
  - `defeat_skeleton`: 5,21 % frente a 0,00 % (+5,21 pp)

### D4 frente a D2 (semilla 31, comprobación de equivalencia del paso 6d)
- **D4 frente a D2**:
  - Score D4: 14,04 % (IC 95 %: [12,92, 15,06] %)
  - Score D2: 14,04 % (IC 95 %: [12,92, 15,06] %)
  - Diferencia de Score (D4 - D2): +0,00 pp
  - ¿Se solapan los IC 95 %?: **Sí**
  - `defeat_zombie`: 40,21 % frente a 40,21 % (+0,00 pp)
  - `defeat_skeleton`: 7,83 % frente a 7,83 % (+0,00 pp)

**Resultado de la comprobación de equivalencia del 6d:**
Se comprobó que borrar `DefensaArmada` y `CerrarDistancia` y retirar los interruptores de `Perfil` no altera la conducta de Crafter. Al comparar `paso6_D4.json` con `paso6_D2.json` (ignorando `tiempo_segundos`, `ms_por_paso`, `mecanismos` y `sin_estrategias_propias`), **todos los campos son idénticos** (Score 14,04 %, IC 95 % [12,92, 15,06] %, 383 episodios, 100.000 pasos y las tasas de los 22 logros oficiales de Crafter) salvo una única causa de muerte:
- En D2: 27 muertes por flecha y 271 por zombi (0 latidos cortados).
- En D4: 26 muertes por flecha y 272 por zombi (1 latido cortado).
Esta divergencia de un solo caso se debe exclusivamente a que en D4 la guillotina cortó 1 latido por reloj (> 100 ms) en el episodio 64: dicho episodio duró 167 pasos muriendo por zombi (en vez de 169 pasos muriendo por flecha en D2). Todos los demás episodios siguieron trayectorias idénticas, dándose por buena la equivalencia.

