Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · 129 episodios · score 11.8, 12.5, 9.77 · latidos cortados por la guillotina: 0 · mecanismos: factibilidad_temporal, filtro_orientacion, material_mapa

Latidos de más de 100 ms de reloj (cognición): 0 (0, 0, 0 por semilla); máximo 76.8 ms.

### a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 2 (4,7 %) | 3 (7,1 %) | 2 (4,5 %) | 7 (5,4 %) |
| no encuentra sitio | 41 (95,3 %) | 37 (88,1 %) | 41 (93,2 %) | 119 (92,2 %) |
| no lo completa a tiempo | 0 (0,0 %) | 1 (2,4 %) | 0 (0,0 %) | 1 (0,8 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| pasa la noche dentro | 0 (0,0 %) | 1 (2,4 %) | 0 (0,0 %) | 1 (0,8 %) |
| cortado por presupuesto | 0 (0,0 %) | 0 (0,0 %) | 1 (2,3 %) | 1 (0,8 %) |

Motivos dentro de cada causa (total de las semillas):

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | zombi | 5 |
| muere antes de anochecer | flecha | 2 |
| no encuentra sitio | abandona el sitio antes de lo oscuro (11a) | 60 |
| no encuentra sitio | — | 59 |
| no lo completa a tiempo | falta tiempo | 1 |
| pasa la noche dentro | — | 1 |
| cortado por presupuesto | None | 1 |

Latidos oscuros fuera antes de entrar (episodios que entran): mediana 57, máximo 57, n = 1.

### a3) Factibilidad en el tiempo en la primera noche (deuda 11a)

- Episodios con datos: 126; con un sitio elegido en la ventana: 81 (T infinito: 1).
- T_disponible al elegir: mediana 37 (p25-p75 36-37); holgura: mediana 15 (p25-p75 9-23).
- D* en el ocaso: {0.7: 126}.
- Episodios con abandono en la primera noche: 64 (49,6 %); abandonos: 67 ({'sitio': 22, 'requisitos': 45}); el primero, antes de lo oscuro en 61.
- Latidos desde el ocaso hasta el primer abandono: mediana 7; coste que le quedaba al sitio: mediana 16, 3 pasos o menos en 3.
- Causa de la primera noche de los que abandonan: {'no encuentra sitio': 63, 'pasa la noche dentro': 1}.

### b) Episodios que pasan la primera noche dentro

Episodios: 1.

| Causa de muerte | Episodios |
|---|---|
| sed | 1 |

- Latidos vividos desde el final de lo oscuro: mediana 109, mínimo 109, máximo 109.
- Salen del recinto tras la noche: 1 de 1; latidos desde el final de lo oscuro hasta salir: mediana 47.
- Al salir (0-9): comida mediana 0, bebida mediana 3; con comida ≤ 3: 1; con bebida ≤ 3: 1.
- Con `wake_up`: 0 de 1.

Qué gana desde el final de lo oscuro hasta salir (47 latidos):

| Estrategia · motivo | Latidos |
|---|---|
| CORE · sin candidatos | 47 (100,0 %) |

| Peligro de la alarma | Hostil real | Gana | Latidos |
|---|---|---|---|
| peligro < 0,5 | hostil a ≤ 4 | CORE | 47 (100,0 %) |

| Propuesta de Proteger en esos latidos | Latidos |
|---|---|
| Proteger no propone | 47 (100,0 %) |

| Impulso en esos latidos | Mediana | p75 |
|---|---|---|
| hostil_d | 2.00 | 2.00 |
| luz | 0.58 | 0.71 |
| peligro_alarma | 0.00 | 0.00 |
| primero_total | 0.00 | 0.00 |
| proteger_total | 0.00 | 0.00 |
| puede_abrir | 0.00 | 0.00 |

### b2) Quién saca del recinto (cada paso de dentro a fuera)

| Fase | Estrategia · motivo | Verbo | Veces |
|---|---|---|---|
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.19) | COGER | 1 |
| tras la noche | perseguir_metas · metas: place_furnace | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.53 > cobijo 0.53) | COGER | 1 |

Al salir tras pasar dentro la primera noche (1): proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.19): 1.

### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 15 (12,6 %) | — |
| lejos | 0 (0,0 %) | — |
| dentro del alcance | 104 (87,4 %) | 2 |
- dentro del alcance, descartada: hay candidatos y ninguno completable: 47
- dentro del alcance, descartada: sin forma válida: falta material: 30
- dentro del alcance, descartada: falta para cavar: wood_pickaxe: 18
- dentro del alcance, descartada: sin forma válida: acceso que no se sabe cerrar: 7
- dentro del alcance, descartada: falta para cavar: iron_pickaxe, wood_pickaxe: 1
- dentro del alcance, descartada: falta para cavar: iron_pickaxe: 1
- clases que se pueden cavar según el modelo: {'arbol': 102, 'piedra': 60, 'carbon': 7, 'diamante': 2}
- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {'falta material': 31169, 'vecina sin ver': 7381, 'válida': 2205, 'acceso que no se sabe cerrar': 1997}
- acciones que el modelo sabe que cierran (episodios): {'place_table (sin material)': 70, 'place_stone (sin material)': 38, 'place_stone (con material)': 22, 'place_table (con material)': 21, 'place_furnace (sin material)': 7, 'place_furnace (con material)': 4, 'place_plant (con material)': 1}; sin ninguna: 6

### c) Cadena de herramientas

Episodios con mesa: 107 (82,9 %).

Mesas colocadas por episodio (USAR que cambia el inventario): media 1.09, mediana 1, máximo 3; episodios con 2 o más: 27.

USAR con efecto: {'place_table': 140, 'make_wood_pickaxe': 86, 'place_plant': 76, 'make_wood_sword': 50, 'place_stone': 50, 'place_furnace': 12, 'make_stone_pickaxe': 7, 'make_stone_sword': 1}; sin efecto: {'place_table': 136, 'place_furnace': 103, 'make_wood_sword': 28, 'make_wood_pickaxe': 15, 'place_stone': 7, 'place_plant': 4, 'make_stone_sword': 2, 'make_stone_pickaxe': 1}.

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |
|---|---|---|---|
| make_wood_pickaxe | 85 (79,4 %) | 7 | 3-22 |
| make_wood_sword | 50 (46,7 %) | 16 | 8-44 |

**Episodios con mesa y sin pico: 22** (3036 latidos desde la mesa).

- Latidos con madera ≥ 1: 1215 (40,0 %); con madera ≥ 1 y una mesa en el 3 × 3: 58 (1,9 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 606 (20,0 %) |
| perseguir_metas · metas: make_wood_pickaxe | 369 (12,2 %) |
| CORE · sin candidatos | 342 (11,3 %) |
| sobresalto · reflejo: sobresalto, huir | 291 (9,6 %) |
| explorar · curiosidad: explorar | 262 (8,6 %) |
| alimentarse · acercarse a agua | 227 (7,5 %) |
| huir · huir de flecha | 125 (4,1 %) |
| alimentarse · acercarse a vaca | 82 (2,7 %) |
| perseguir_metas · proteger: pide wood | 65 (2,1 %) |
| alimentarse · comer agua | 61 (2,0 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 621 (44,8 %) |
| metas: carbon | 169 (12,2 %) |
| metas: hierba | 147 (10,6 %) |
| metas: vaca | 119 (8,6 %) |
| metas: planta | 116 (8,4 %) |
| metas: hierro | 84 (6,1 %) |
| proteger: pide wood | 65 (4,7 %) |
| metas: place_table | 22 (1,6 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 22 |
| place_table · metas: make_wood_pickaxe | 7 |
| place_plant · metas: place_plant | 3 |

**Episodios con mesa y sin espada: 57** (9366 latidos desde la mesa).

- Latidos con madera ≥ 1: 3138 (33,5 %); con madera ≥ 1 y una mesa en el 3 × 3: 225 (2,4 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 1655 (17,7 %) |
| CORE · sin candidatos | 1100 (11,7 %) |
| sobresalto · reflejo: sobresalto, huir | 876 (9,4 %) |
| perseguir_metas · metas: make_wood_pickaxe | 751 (8,0 %) |
| alimentarse · acercarse a agua | 672 (7,2 %) |
| explorar · curiosidad: explorar | 628 (6,7 %) |
| huir · huir de flecha | 427 (4,6 %) |
| perseguir_metas · metas: place_furnace | 306 (3,3 %) |
| huir · huir de esqueleto | 296 (3,2 %) |
| alimentarse · acercarse a vaca | 268 (2,9 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 1090 (24,7 %) |
| metas: place_furnace | 769 (17,4 %) |
| metas: piedra | 389 (8,8 %) |
| metas: hierba | 378 (8,6 %) |
| metas: carbon | 369 (8,4 %) |
| metas: make_wood_sword | 275 (6,2 %) |
| metas: vaca | 253 (5,7 %) |
| metas: planta | 230 (5,2 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 55 |
| make_wood_pickaxe · metas: make_wood_pickaxe | 34 |
| place_stone · metas: place_stone | 22 |
| place_table · metas: make_wood_pickaxe | 13 |
| place_plant · metas: place_plant | 10 |
| place_furnace · metas: place_furnace | 6 |
| place_table · metas: make_stone_pickaxe | 5 |
| make_stone_pickaxe · metas: make_stone_pickaxe | 3 |
