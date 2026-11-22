Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · 123 episodios · score 12.06, 15.37, 9.52 · latidos cortados por la guillotina: 0 · mecanismos: factibilidad_temporal

Latidos de más de 100 ms de reloj (cognición): 0 (0, 0, 0 por semilla); máximo 60.2 ms.

### a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 1 (2,4 %) | 0 (0,0 %) | 1 (2,2 %) | 2 (1,6 %) |
| no encuentra sitio | 39 (92,9 %) | 36 (100,0 %) | 43 (95,6 %) | 118 (95,9 %) |
| no lo completa a tiempo | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 2 (4,8 %) | 0 (0,0 %) | 0 (0,0 %) | 2 (1,6 %) |
| pasa la noche dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| cortado por presupuesto | 0 (0,0 %) | 0 (0,0 %) | 1 (2,2 %) | 1 (0,8 %) |

Motivos dentro de cada causa (total de las semillas):

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | zombi | 2 |
| no encuentra sitio | — | 85 |
| no encuentra sitio | abandona el sitio antes de lo oscuro (11a) | 33 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | 1 |
| sale antes del amanecer | salir_del_recinto · salir del recinto: abrir piedra (sed 0.88 > cobijo 0.83) | 1 |
| cortado por presupuesto | None | 1 |

Latidos oscuros fuera antes de entrar (episodios que entran): mediana 4, máximo 9, n = 2.

### a3) Factibilidad en el tiempo en la primera noche (deuda 11a)

- Episodios con datos: 122; con un sitio elegido en la ventana: 48 (T infinito: 1).
- T_disponible al elegir: mediana 37 (p25-p75 36-37); holgura: mediana 16 (p25-p75 7-25).
- D* en el ocaso: {0.7: 122}.
- Episodios con abandono en la primera noche: 36 (29,3 %); abandonos: 42 ({'sitio': 27, 'requisitos': 15}); el primero, antes de lo oscuro en 34.
- Latidos desde el ocaso hasta el primer abandono: mediana 9; coste que le quedaba al sitio: mediana 14, 3 pasos o menos en 2.
- Causa de la primera noche de los que abandonan: {'no encuentra sitio': 34, 'sale antes del amanecer': 2}.

### b) Episodios que pasan la primera noche dentro

Episodios: 0.

| Causa de muerte | Episodios |
|---|---|

- Latidos vividos desde el final de lo oscuro: mediana —, mínimo —, máximo —.
- Salen del recinto tras la noche: 0 de 0; latidos desde el final de lo oscuro hasta salir: mediana —.
- Al salir (0-9): comida mediana —, bebida mediana —; con comida ≤ 3: 0; con bebida ≤ 3: 0.
- Con `wake_up`: 0 de 0.

### b2) Quién saca del recinto (cada paso de dentro a fuera)

| Fase | Estrategia · motivo | Verbo | Veces |
|---|---|---|---|
| noche | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | COGER | 1 |
| noche | salir_del_recinto · salir del recinto: abrir piedra (sed 0.88 > cobijo 0.83) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.42 > cobijo 0.00) | COGER | 1 |

### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 15 (12,7 %) | — |
| lejos | 0 (0,0 %) | — |
| dentro del alcance | 103 (87,3 %) | 2 |
- dentro del alcance, descartada: sin forma válida: falta material: 47
- dentro del alcance, descartada: hay candidatos y ninguno completable: 33
- dentro del alcance, descartada: falta para cavar: wood_pickaxe: 16
- dentro del alcance, descartada: sin forma válida: acceso que no se sabe cerrar: 6
- dentro del alcance, descartada: falta para cavar: iron_pickaxe, wood_pickaxe: 1
- clases que se pueden cavar según el modelo: {'arbol': 102, 'diamante': 2, 'piedra': 58, 'carbon': 4}
- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {'falta material': 28927, 'vecina sin ver': 6846, 'acceso que no se sabe cerrar': 2249, 'válida': 1537}
- acciones que el modelo sabe que cierran (episodios): {'place_table (sin material)': 79, 'place_stone (sin material)': 47, 'place_table (con material)': 12, 'place_stone (con material)': 11, 'place_furnace (sin material)': 6, 'place_furnace (con material)': 2}; sin ninguna: 5

### c) Cadena de herramientas

Episodios con mesa: 105 (85,4 %).

Mesas colocadas por episodio (USAR que cambia el inventario): media 1.12, mediana 1, máximo 3; episodios con 2 o más: 28.

USAR con efecto: {'place_table': 138, 'place_plant': 86, 'make_wood_pickaxe': 82, 'make_wood_sword': 55, 'place_stone': 39, 'place_furnace': 21, 'make_stone_pickaxe': 10, 'make_stone_sword': 2}; sin efecto: {'place_table': 133, 'place_furnace': 89, 'make_wood_sword': 27, 'make_wood_pickaxe': 23, 'make_stone_pickaxe': 7, 'place_stone': 7, 'make_stone_sword': 5, 'place_plant': 1}.

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |
|---|---|---|---|
| make_wood_pickaxe | 82 (78,1 %) | 8 | 3-30 |
| make_wood_sword | 55 (52,4 %) | 16 | 8-57 |

**Episodios con mesa y sin pico: 23** (2344 latidos desde la mesa).

- Latidos con madera ≥ 1: 923 (39,4 %); con madera ≥ 1 y una mesa en el 3 × 3: 92 (3,9 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 677 (28,9 %) |
| sobresalto · reflejo: sobresalto, huir | 256 (10,9 %) |
| perseguir_metas · metas: make_wood_pickaxe | 214 (9,1 %) |
| explorar · curiosidad: explorar | 189 (8,1 %) |
| CORE · sin candidatos | 149 (6,4 %) |
| alimentarse · acercarse a agua | 124 (5,3 %) |
| huir · huir de lava | 78 (3,3 %) |
| CORE · sigue dormido | 70 (3,0 %) |
| huir · huir de flecha | 66 (2,8 %) |
| alimentarse · acercarse a vaca | 63 (2,7 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 485 (50,4 %) |
| metas: planta | 152 (15,8 %) |
| metas: hierba | 118 (12,3 %) |
| metas: vaca | 88 (9,1 %) |
| metas: carbon | 26 (2,7 %) |
| proteger: pide wood_pickaxe | 26 (2,7 %) |
| metas: place_table | 23 (2,4 %) |
| metas: hierro | 12 (1,2 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 23 |
| place_table · metas: make_wood_pickaxe | 6 |
| place_plant · metas: place_plant | 2 |

**Episodios con mesa y sin espada: 50** (7014 latidos desde la mesa).

- Latidos con madera ≥ 1: 2291 (32,7 %); con madera ≥ 1 y una mesa en el 3 × 3: 191 (2,7 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 1483 (21,1 %) |
| sobresalto · reflejo: sobresalto, huir | 692 (9,9 %) |
| CORE · sin candidatos | 673 (9,6 %) |
| explorar · curiosidad: explorar | 631 (9,0 %) |
| perseguir_metas · metas: make_wood_pickaxe | 494 (7,0 %) |
| alimentarse · acercarse a agua | 385 (5,5 %) |
| perseguir_metas · metas: make_wood_sword | 240 (3,4 %) |
| huir · huir de flecha | 218 (3,1 %) |
| huir · huir de lava | 205 (2,9 %) |
| huir · huir de esqueleto | 203 (2,9 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 804 (26,8 %) |
| metas: make_wood_sword | 470 (15,7 %) |
| metas: hierba | 449 (15,0 %) |
| metas: piedra | 217 (7,2 %) |
| metas: planta | 209 (7,0 %) |
| metas: vaca | 209 (7,0 %) |
| metas: place_furnace | 201 (6,7 %) |
| metas: hierro | 86 (2,9 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 48 |
| make_wood_pickaxe · metas: make_wood_pickaxe | 26 |
| place_stone · metas: place_stone | 12 |
| place_table · metas: make_wood_pickaxe | 11 |
| place_furnace · metas: place_furnace | 8 |
| place_plant · metas: place_plant | 8 |
| place_table · metas: make_wood_sword | 3 |
| place_table · proteger: pide stone | 2 |
