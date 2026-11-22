Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · 123 episodios · score 10.9, 16.32, 10.82 · latidos cortados por la guillotina: 0 · mecanismos: factibilidad_temporal, filtro_orientacion

Latidos de más de 100 ms de reloj (cognición): 0 (0, 0, 0 por semilla); máximo 55.1 ms.

### a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 2 (4,7 %) | 0 (0,0 %) | 1 (2,4 %) | 3 (2,4 %) |
| no encuentra sitio | 39 (90,7 %) | 36 (94,7 %) | 40 (95,2 %) | 115 (93,5 %) |
| no lo completa a tiempo | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 2 (4,7 %) | 2 (5,3 %) | 0 (0,0 %) | 4 (3,3 %) |
| pasa la noche dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| cortado por presupuesto | 0 (0,0 %) | 0 (0,0 %) | 1 (2,4 %) | 1 (0,8 %) |

Motivos dentro de cada causa (total de las semillas):

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | zombi | 2 |
| muere antes de anochecer | flecha | 1 |
| no encuentra sitio | — | 69 |
| no encuentra sitio | abandona el sitio antes de lo oscuro (11a) | 46 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | 1 |
| sale antes del amanecer | salir_del_recinto · salir del recinto: abrir piedra (sed 0.88 > cobijo 0.83) | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.65 > cobijo 0.60) | 1 |
| sale antes del amanecer | perseguir_metas · metas: make_wood_pickaxe | 1 |
| cortado por presupuesto | None | 1 |

Latidos oscuros fuera antes de entrar (episodios que entran): mediana 0, máximo 9, n = 4.

### a3) Factibilidad en el tiempo en la primera noche (deuda 11a)

- Episodios con datos: 121; con un sitio elegido en la ventana: 56 (T infinito: 1).
- T_disponible al elegir: mediana 37 (p25-p75 36-37); holgura: mediana 15 (p25-p75 7-23).
- D* en el ocaso: {0.7: 121}.
- Episodios con abandono en la primera noche: 49 (39,8 %); abandonos: 57 ({'sitio': 29, 'requisitos': 28}); el primero, antes de lo oscuro en 47.
- Latidos desde el ocaso hasta el primer abandono: mediana 8; coste que le quedaba al sitio: mediana 15, 3 pasos o menos en 2.
- Causa de la primera noche de los que abandonan: {'no encuentra sitio': 47, 'sale antes del amanecer': 2}.

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
| tras la noche | salir_del_recinto · salir del recinto: abrir piedra (hambre 0.42 > cobijo 0.00) | COGER | 1 |
| ocaso | proteger · proteger: abrir piedra (hambre 0.65 > cobijo 0.60) | COGER | 1 |
| noche | perseguir_metas · metas: make_wood_pickaxe | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.42 > cobijo 0.00) | COGER | 1 |

### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 15 (13,0 %) | — |
| lejos | 0 (0,0 %) | — |
| dentro del alcance | 100 (87,0 %) | 2 |
- dentro del alcance, descartada: hay candidatos y ninguno completable: 40
- dentro del alcance, descartada: sin forma válida: falta material: 40
- dentro del alcance, descartada: falta para cavar: wood_pickaxe: 13
- dentro del alcance, descartada: sin forma válida: acceso que no se sabe cerrar: 6
- dentro del alcance, descartada: falta para cavar: iron_pickaxe, wood_pickaxe: 1
- clases que se pueden cavar según el modelo: {'arbol': 99, 'piedra': 55, 'carbon': 4, 'diamante': 1}
- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {'falta material': 28401, 'vecina sin ver': 6995, 'acceso que no se sabe cerrar': 2300, 'válida': 1695}
- acciones que el modelo sabe que cierran (episodios): {'place_table (sin material)': 65, 'place_stone (sin material)': 44, 'place_table (con material)': 24, 'place_stone (con material)': 11, 'place_furnace (sin material)': 4, 'place_furnace (con material)': 3}; sin ninguna: 5

### c) Cadena de herramientas

Episodios con mesa: 105 (85,4 %).

Mesas colocadas por episodio (USAR que cambia el inventario): media 1.15, mediana 1, máximo 3; episodios con 2 o más: 34.

USAR con efecto: {'place_table': 141, 'place_plant': 87, 'make_wood_pickaxe': 83, 'make_wood_sword': 57, 'place_stone': 35, 'place_furnace': 20, 'make_stone_pickaxe': 8, 'make_stone_sword': 2}; sin efecto: {'place_table': 134, 'place_furnace': 90, 'make_wood_sword': 22, 'make_wood_pickaxe': 15, 'place_stone': 6, 'make_stone_pickaxe': 4, 'make_stone_sword': 3, 'place_plant': 2}.

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |
|---|---|---|---|
| make_wood_pickaxe | 83 (79,0 %) | 10 | 4-36 |
| make_wood_sword | 57 (54,3 %) | 29 | 8-80 |

**Episodios con mesa y sin pico: 22** (2174 latidos desde la mesa).

- Latidos con madera ≥ 1: 701 (32,2 %); con madera ≥ 1 y una mesa en el 3 × 3: 31 (1,4 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 639 (29,4 %) |
| sobresalto · reflejo: sobresalto, huir | 218 (10,0 %) |
| explorar · curiosidad: explorar | 162 (7,5 %) |
| CORE · sin candidatos | 156 (7,2 %) |
| perseguir_metas · metas: make_wood_pickaxe | 153 (7,0 %) |
| alimentarse · acercarse a agua | 102 (4,7 %) |
| huir · huir de lava | 101 (4,6 %) |
| CORE · sigue dormido | 70 (3,2 %) |
| huir · huir de esqueleto | 58 (2,7 %) |
| alimentarse · comer agua | 51 (2,3 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 367 (42,2 %) |
| metas: hierba | 141 (16,2 %) |
| metas: planta | 118 (13,6 %) |
| metas: vaca | 85 (9,8 %) |
| metas: carbon | 72 (8,3 %) |
| proteger: pide wood | 27 (3,1 %) |
| metas: place_table | 22 (2,5 %) |
| metas: hierro | 15 (1,7 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 22 |
| place_table · metas: make_wood_pickaxe | 4 |
| place_plant · metas: place_plant | 1 |

**Episodios con mesa y sin espada: 48** (6720 latidos desde la mesa).

- Latidos con madera ≥ 1: 2108 (31,4 %); con madera ≥ 1 y una mesa en el 3 × 3: 144 (2,1 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 1260 (18,8 %) |
| CORE · sin candidatos | 940 (14,0 %) |
| sobresalto · reflejo: sobresalto, huir | 586 (8,7 %) |
| explorar · curiosidad: explorar | 559 (8,3 %) |
| perseguir_metas · metas: make_wood_pickaxe | 415 (6,2 %) |
| alimentarse · acercarse a agua | 343 (5,1 %) |
| huir · huir de lava | 293 (4,4 %) |
| huir · huir de flecha | 232 (3,5 %) |
| huir · huir de esqueleto | 232 (3,5 %) |
| perseguir_metas · metas: make_wood_sword | 186 (2,8 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 694 (25,8 %) |
| metas: hierba | 488 (18,1 %) |
| metas: make_wood_sword | 314 (11,7 %) |
| metas: place_furnace | 269 (10,0 %) |
| metas: vaca | 153 (5,7 %) |
| metas: planta | 146 (5,4 %) |
| metas: piedra | 126 (4,7 %) |
| metas: carbon | 119 (4,4 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 45 |
| make_wood_pickaxe · metas: make_wood_pickaxe | 25 |
| place_stone · metas: place_stone | 12 |
| place_table · metas: make_wood_pickaxe | 8 |
| place_furnace · metas: place_furnace | 7 |
| place_table · metas: make_wood_sword | 4 |
| place_plant · metas: place_plant | 4 |
| place_table · proteger: pide stone | 3 |
