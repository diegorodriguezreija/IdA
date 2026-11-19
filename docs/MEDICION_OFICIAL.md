# Medición Oficial Crafter · Paso −1

Fecha: 19/11/2026.  
Protocolo: Evaluación oficial con Crafter 1.8.3, vista oficial (9×7), perfil Equilibrado, longitud de episodio 10.000, 100.000 pasos acumulados, semilla base 31.

---

## 1. Comandos exactos ejecutados

### Adaptador y reproducibilidad
```bash
# Verificación de invariancia en la rama de trabajo
python herramientas/invariancia.py

# Comprobación de determinismo (3.000 pasos, ejecutado dos veces seguidas)
python herramientas/evaluar_crafter.py --pasos 3000 --semilla 31 --vista oficial
python herramientas/evaluar_crafter.py --pasos 3000 --semilla 31 --vista oficial
```

### Mediciones oficiales de Crafter (100.000 pasos en secuencia)
```bash
# a) Suelo: main sin estrategias propias
python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial --sin-estrategias-propias --salida datos/evaluacion/suelo_main.json

# b) Techo main: con estrategias propias y linaje
python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial --salida datos/evaluacion/techo_main.json

# c) Main sin herencia: con estrategias propias, sin herencia entre vidas
python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial --sin-herencia --salida datos/evaluacion/main_sin_herencia.json

# d) Techo C.3d (worktree aislado de feature/crafter-fase-c con adaptador oficial)
python herramientas/evaluar_crafter.py --pasos 100000 --semilla 31 --vista oficial --salida datos/evaluacion/techo_c3d.json
```

### Referencia de generalización (`ref_generalizacion`)
```bash
# Benchmark completo en minimo
python herramientas/benchmark.py ejecutar --raiz . --mundo minimo --salida datos/evaluacion/ref_generalizacion_minimo.json

# Benchmark completo en archivos
python herramientas/benchmark.py ejecutar --raiz . --mundo archivos --salida datos/evaluacion/ref_generalizacion_archivos.json

# Invariancia en ajedrez
python herramientas/invariancia.py --mundos ajedrez
```

---

## 2. Diagnóstico previo (Puntos 1 y 2)

### Punto 1: Reproducibilidad
- **Discrepancia en cronometrajes iniciales:** El primer reporte de 18 episodios y Score 11,23 % se debió a un borrador emitido prematuramente por el modelo anterior antes de que concluyera el proceso en segundo plano en la máquina. La salida real única del proceso piloto (`task-5461`) fue de 25 episodios y 17,74 % de Score.
- **Verificación empírica:** Dos ejecuciones consecutivas e independientes de 3.000 pasos produjeron resultados **100 % idénticos bit a bit**:
  - Mismos 9 episodios y mismas duraciones: 482, 223, 201, 284, 107, 741, 546, 325, 91 pasos.
  - Mismas causas de muerte: zombi (4), esqueleto (3), hambre (1), sobrevive (1).
  - Mismas tasas de éxito por logro e idéntica Crafter Score: **10,54 %** (IC 95 %: [7,14, 12,46] %).

### Punto 2: Salida de `invariancia.py`
- `invariancia.py` compara latido a latido `("latido", "decisión", "objetivo", "vitales", "amplitud")` contra `datos/invariancia/referencia.json` para las semillas 1, 2 y 3 (400 latidos) en los cuatro mundos.
- **Resultado:**
  - `minimo`: OK
  - `archivos`: OK
  - `ajedrez`: OK
  - `crafter`: Falla únicamente en el campo `amplitud` (amplitud consumida por la Onda difiere en 1 unidad: 35 $\to$ 36 en s1 latido 15; 45 $\to$ 46 en s2 latido 5; 21 $\to$ 22 en s3 latido 1).
  - Todas las decisiones (`verbo`, `objetivo`), constantes vitales y puntuaciones finales coinciden de forma exacta.
- **Estado en `main`:** El fallo con código 1 ya ocurría en `main` antes de realizar ningún cambio en esta rama. La referencia se regeneró en el commit `766e6d3` y desde entonces `invariancia.py` da OK en los cuatro mundos.

---

## 3. Comparación global Crafter (100.000 pasos)

| Condición | Score Crafter (IC 95 %) | Episodios | Pasos / episodio | Rendimiento (ms/paso) | Tiempo total (s) |
|---|---|---|---|---|---|
| **Suelo (`main` sin estrategias)** | **1,46 %** [1,38, 1,52] % | 401 | 249,4 | 13,79 ms | 1.379,2 s |
| **Techo `main` (con linaje)** | **20,26 %** [18,45, 21,69] % | 264 | 378,8 | 11,65 ms | 1.165,1 s |
| **`main` sin herencia** | **19,18 %** [17,74, 20,46] % | 278 | 359,7 | 12,06 ms | 1.205,8 s |
| **Techo C.3d (`feature/crafter-fase-c`)** | **20,58 %** [18,91, 21,88] % | 251 | 398,4 | 9,92 ms | 992,0 s |

---

## 4. Tasa de éxito por logro (%)

Fracción de episodios en que se consiguió el logro al menos una vez (sobre el total de episodios de cada condición):

| Logro | Suelo (`main`) | Techo `main` | `main` sin herencia | Techo C.3d |
|---|---|---|---|---|
| `collect_coal` | 0,00 % | 24,24 % | 20,50 % | 17,93 % |
| `collect_diamond` | 0,00 % | 0,00 % | 0,00 % | 0,00 % |
| `collect_drink` | 83,79 % | 81,82 % | 79,86 % | 78,88 % |
| `collect_iron` | 0,00 % | 1,14 % | 0,36 % | 0,40 % |
| `collect_sapling` | 2,74 % | 98,48 % | 98,56 % | 98,41 % |
| `collect_stone` | 0,00 % | 67,05 % | 69,06 % | 84,46 % |
| `collect_wood` | 72,07 % | 99,24 % | 100,00 % | 99,60 % |
| `defeat_skeleton` | 0,00 % | 35,23 % | 43,17 % | 33,07 % |
| `defeat_zombie` | 33,67 % | 57,95 % | 64,03 % | 61,75 % |
| `eat_cow` | 63,59 % | 58,71 % | 60,07 % | 60,16 % |
| `eat_plant` | 0,00 % | 1,52 % | 0,36 % | 1,20 % |
| `make_iron_pickaxe` | 0,00 % | 0,00 % | 0,00 % | 0,00 % |
| `make_iron_sword` | 0,00 % | 0,00 % | 0,00 % | 0,00 % |
| `make_stone_pickaxe` | 0,00 % | 7,95 % | 7,55 % | 9,16 % |
| `make_stone_sword` | 0,00 % | 3,79 % | 2,52 % | 3,98 % |
| `make_wood_pickaxe` | 0,00 % | 95,45 % | 96,40 % | 96,41 % |
| `make_wood_sword` | 0,00 % | 92,42 % | 91,73 % | 92,43 % |
| `place_furnace` | 0,00 % | 10,98 % | 13,31 % | 16,33 % |
| `place_plant` | 0,00 % | 98,48 % | 98,56 % | 98,41 % |
| `place_stone` | 0,00 % | 63,64 % | 62,59 % | 77,29 % |
| `place_table` | 0,00 % | 97,35 % | 98,92 % | 97,21 % |
| `wake_up` | 6,73 % | 55,30 % | 51,44 % | 69,32 % |

---

## 5. Causas de muerte / finalización por condición

| Causa de muerte | Suelo (`main`) | Techo `main` | `main` sin herencia | Techo C.3d |
|---|---|---|---|---|
| `desgaste` | 18 (4,5 %) | 9 (3,4 %) | 18 (6,5 %) | 4 (1,6 %) |
| `esqueleto` | 28 (7,0 %) | 56 (21,2 %) | 62 (22,3 %) | 33 (13,1 %) |
| `flecha` | 3 (0,7 %) | 2 (0,8 %) | 4 (1,4 %) | 0 (0,0 %) |
| `hambre` | 23 (5,7 %) | 57 (21,6 %) | 49 (17,6 %) | 102 (40,6 %) |
| `lava` | 4 (1,0 %) | 2 (0,8 %) | 1 (0,4 %) | 0 (0,0 %) |
| `sed` | 24 (6,0 %) | 40 (15,2 %) | 38 (13,7 %) | 42 (16,7 %) |
| `zombi` | 300 (74,8 %) | 97 (36,7 %) | 105 (37,8 %) | 69 (27,5 %) |
| `cortado por presupuesto` | 1 (0,2 %) | 1 (0,4 %) | 1 (0,4 %) | 1 (0,4 %) |
| **Total episodios** | **401** | **264** | **278** | **251** |

---

## 6. Referencia de generalización (`ref_generalizacion`)

Línea base registrada sobre `main` (4 grupos: Equilibrado, Valiente, Reactivo, Sin experiencia; semillas 1 a 10; 4 generaciones de 400 latidos por celda = 160 vidas por mundo). Datos procedentes de `datos/evaluacion/ref_generalizacion_minimo.json` y `datos/evaluacion/ref_generalizacion_archivos.json`:

| Mundo | Celdas ejecutadas | Vidas totales | Vidas vivas (400 lat.) | Latidos/vida (media / med.) | Fitness/vida (media / med.) | Muertes por causa | Rendimiento |
|---|---|---|---|---|---|---|---|
| **`minimo`** | 40 / 40 (100 %) | 160 | 96 (60,0 %) | 319,9 / 400,0 | 688,99 / 772,50 | lobo: 39, desgaste: 18, hambre: 7 | 1,36 ms/latido |
| **`archivos`** | 40 / 40 (100 %) | 160 | 79 (49,4 %) | 303,7 / 393,5 | 1.457,80 / 1.750,00 | hambre: 42, desgaste: 27, depredador: 12 | 1,82 ms/latido |
| **`ajedrez`** | — | — | — | — | — | Invariancia: **OK** | — |
