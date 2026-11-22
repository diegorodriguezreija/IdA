Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · 121 episodios · score 10.64, 15.56, 12.51 · latidos cortados por la guillotina: 0 · mecanismos: factibilidad_temporal, filtro_orientacion

Latidos de más de 100 ms de reloj (cognición): 4 (0, 3, 1 por semilla); máximo 504.7 ms.

### a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 3 (7,0 %) | 0 (0,0 %) | 1 (2,5 %) | 4 (3,3 %) |
| no encuentra sitio | 32 (74,4 %) | 23 (60,5 %) | 33 (82,5 %) | 88 (72,7 %) |
| no lo completa a tiempo | 5 (11,6 %) | 8 (21,1 %) | 4 (10,0 %) | 17 (14,0 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 2 (4,7 %) | 4 (10,5 %) | 0 (0,0 %) | 6 (5,0 %) |
| pasa la noche dentro | 1 (2,3 %) | 2 (5,3 %) | 1 (2,5 %) | 4 (3,3 %) |
| cortado por presupuesto | 0 (0,0 %) | 1 (2,6 %) | 1 (2,5 %) | 2 (1,7 %) |

Motivos dentro de cada causa (total de las semillas):

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | zombi | 3 |
| muere antes de anochecer | flecha | 1 |
| no encuentra sitio | no empieza o no pide por falta de tiempo (11a') | 55 |
| no encuentra sitio | — | 33 |
| no lo completa a tiempo | falta tiempo | 12 |
| no lo completa a tiempo | falta material | 3 |
| no lo completa a tiempo | falta herramienta | 2 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.76) | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.65 > cobijo 0.60) | 1 |
| sale antes del amanecer | perseguir_metas · metas: place_furnace | 1 |
| sale antes del amanecer | perseguir_metas · metas: make_wood_pickaxe | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.86) | 1 |
| pasa la noche dentro | — | 4 |
| cortado por presupuesto | None | 2 |

Latidos oscuros fuera antes de entrar (episodios que entran): mediana 12, máximo 31, n = 10.

### a3) Factibilidad en el tiempo en la primera noche (deuda 11a)

- Episodios con datos: 119; con un sitio elegido en la ventana: 47 (T infinito: 2).
- T_disponible al elegir: mediana 37 (p25-p75 20-87); holgura: mediana 15 (p25-p75 2-41).
- D* en el ocaso: {1.0: 23, 0.527: 18, 0.525: 10, 0.5291: 9, 0.7228: 5, 0.6551: 4, 0.6105: 3, 0.6016: 3, 0.6937: 3, 0.6151: 3, 0.6199: 3, 0.5361: 3, 0.7052: 3, 0.6658: 2, 0.6059: 2, 0.5625: 2, 0.6395: 2, 0.544: 2, 0.7407: 2, 0.7347: 2, 0.7169: 1, 0.6295: 1, 0.6246: 1, 0.5808: 1, 0.711: 1, 0.6344: 1, 0.6824: 1, 0.5929: 1, 0.6994: 1, 0.6768: 1, 0.5559: 1, 0.5468: 1, 0.6604: 1, 0.5659: 1, 0.6446: 1}.
- Sitios no empezados o peticiones no hechas por falta de tiempo: 92 (76,0 %) episodios; 855 evaluaciones ({'sitio': 191, 'requisitos': 664}); antes de lo oscuro en 59 episodios.
- Causa de la primera noche de esos episodios: {'no encuentra sitio': 74, 'no lo completa a tiempo': 14, 'sale antes del amanecer': 3, 'muere antes de anochecer': 1}.
- Error de T_disponible (previsto − latidos reales hasta el primer daño en la ventana): mediana 23 (p25-p75 6-52), n = 38; previsto 39, real 20; sin daño en la ventana: 7.

### b) Episodios que pasan la primera noche dentro

Episodios: 4.

| Causa de muerte | Episodios |
|---|---|
| zombi | 2 |
| hambre | 1 |
| sed | 1 |

- Latidos vividos desde el final de lo oscuro: mediana 209, mínimo 208, máximo 274.
- Salen del recinto tras la noche: 4 de 4; latidos desde el final de lo oscuro hasta salir: mediana 104.
- Al salir (0-9): comida mediana 0, bebida mediana 2; con comida ≤ 3: 4; con bebida ≤ 3: 3.
- Con `wake_up`: 4 de 4.

Qué gana desde el final de lo oscuro hasta salir (408 latidos):

| Estrategia · motivo | Latidos |
|---|---|
| refugiarse · volver al hogar | 65 (15,9 %) |
| CORE · sin candidatos | 63 (15,4 %) |
| afrontar · afrontar: esperar a zombi (golpes 3.0, margen 75, beneficio  | 53 (13,0 %) |
| afrontar · afrontar: acercarse a esqueleto (alcance 2, golpes 10.0, mar | 48 (11,8 %) |
| quieto_o_huir · último recurso: huir | 40 (9,8 %) |
| proteger · proteger: dentro, dormir | 36 (8,8 %) |
| proteger · acecha: proteger: dentro, dormir | 33 (8,1 %) |
| sobresalto · reflejo: sobresalto, huir | 18 (4,4 %) |

| Peligro de la alarma | Hostil real | Gana | Latidos |
|---|---|---|---|
| ≥ 0,8 | hostil a ≤ 4 | afrontar | 107 (26,2 %) |
| peligro < 0,5 | hostil a ≤ 4 | CORE | 76 (18,6 %) |
| ≥ 0,8 | hostil a ≤ 4 | proteger | 69 (16,9 %) |
| ≥ 0,8 | hostil a ≤ 4 | refugiarse | 57 (14,0 %) |
| ≥ 0,8 | hostil a ≤ 4 | quieto_o_huir | 40 (9,8 %) |
| ≥ 0,8 | hostil a ≤ 4 | sobresalto | 16 (3,9 %) |
| 0,5-0,8 | hostil a ≤ 4 | afrontar | 11 (2,7 %) |
| ≥ 0,8 | hostil a ≤ 4 | alimentarse | 11 (2,7 %) |
| 0,5-0,8 | hostil a ≤ 4 | alimentarse | 9 (2,2 %) |
| 0,5-0,8 | hostil a ≤ 4 | refugiarse | 7 (1,7 %) |
| 0,5-0,8 | hostil a ≤ 4 | sobresalto | 2 (0,5 %) |
| 0,5-0,8 | sin hostil a ≤ 4 | refugiarse | 1 (0,2 %) |

| Propuesta de Proteger en esos latidos | Latidos |
|---|---|
| proteger: dentro, dormir | 311 (76,2 %) |
| Proteger no propone | 83 (20,3 %) |
| proteger: abrir carbon (hambre 1.00 > cobijo 0.05) | 3 (0,7 %) |
| proteger: abrir carbon (hambre 1.00 > cobijo 0.04) | 3 (0,7 %) |
| proteger: abrir piedra (hambre 1.00 > cobijo 0.01) | 2 (0,5 %) |
| proteger: abrir carbon (hambre 1.00 > cobijo 0.06) | 2 (0,5 %) |

| Impulso en esos latidos | Mediana | p75 |
|---|---|---|
| cansancio | 0.00 | 0.00 |
| cobijo | 0.18 | 0.38 |
| exploracion | 0.01 | 0.10 |
| hambre | 0.65 | 0.77 |
| hostil_d | 2.00 | 3.00 |
| luz | 0.85 | 0.98 |
| peligro_alarma | 0.97 | 1.00 |
| primero_total | 0.69 | 1.00 |
| proteger_total | 0.13 | 0.36 |
| puede_abrir | 1.00 | 1.00 |
| salud | 0.00 | 0.00 |
| sed | 0.53 | 0.65 |
| seguridad | 0.99 | 1.00 |

### b2) Quién saca del recinto (cada paso de dentro a fuera)

| Fase | Estrategia · motivo | Verbo | Veces |
|---|---|---|---|
| noche | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.01) | COGER | 1 |
| noche | salir_del_recinto · salir del recinto: abrir piedra (sed 0.88 > cobijo 0.83) | COGER | 1 |
| noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.76) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.02) | COGER | 1 |
| ocaso | proteger · proteger: abrir piedra (hambre 0.65 > cobijo 0.60) | COGER | 1 |
| noche | perseguir_metas · metas: place_furnace | COGER | 1 |
| noche | perseguir_metas · metas: make_wood_pickaxe | COGER | 1 |
| tras la noche | proteger · proteger: abrir arbol (sed 0.77 > cobijo 0.01) | COGER | 1 |
| noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.86) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.42 > cobijo 0.00) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.01) | COGER | 1 |

Al salir tras pasar dentro la primera noche (4): proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.01): 1; proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.02): 1; proteger · proteger: abrir arbol (sed 0.77 > cobijo 0.01): 1; proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.01): 1.

### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 14 (15,9 %) | — |
| lejos | 0 (0,0 %) | — |
| dentro del alcance | 74 (84,1 %) | 2 |
- dentro del alcance, descartada: sin forma válida: falta material: 36
- dentro del alcance, descartada: hay candidatos y ninguno completable: 20
- dentro del alcance, descartada: falta para cavar: wood_pickaxe: 11
- dentro del alcance, descartada: sin forma válida: acceso que no se sabe cerrar: 6
- dentro del alcance, descartada: falta para cavar: iron_pickaxe, wood_pickaxe: 1
- clases que se pueden cavar según el modelo: {'arbol': 74, 'piedra': 35, 'diamante': 1, 'carbon': 1}
- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {'falta material': 21073, 'vecina sin ver': 5117, 'acceso que no se sabe cerrar': 2300, 'válida': 609}
- acciones que el modelo sabe que cierran (episodios): {'place_table (sin material)': 49, 'place_stone (sin material)': 29, 'place_table (con material)': 14, 'place_stone (con material)': 6, 'place_furnace (sin material)': 1, 'place_furnace (con material)': 1}; sin ninguna: 5

### c) Cadena de herramientas

Episodios con mesa: 102 (84,3 %).

Mesas colocadas por episodio (USAR que cambia el inventario): media 1.15, mediana 1, máximo 5; episodios con 2 o más: 32.

USAR con efecto: {'place_table': 139, 'place_plant': 79, 'make_wood_pickaxe': 78, 'make_wood_sword': 53, 'place_stone': 39, 'place_furnace': 18, 'make_stone_pickaxe': 9, 'make_stone_sword': 2}; sin efecto: {'place_table': 130, 'place_furnace': 88, 'make_wood_sword': 22, 'make_wood_pickaxe': 13, 'make_stone_pickaxe': 6, 'make_stone_sword': 5, 'place_stone': 4, 'place_plant': 1}.

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |
|---|---|---|---|
| make_wood_pickaxe | 78 (76,5 %) | 10 | 4-30 |
| make_wood_sword | 53 (52,0 %) | 28 | 8-80 |

**Episodios con mesa y sin pico: 24** (2455 latidos desde la mesa).

- Latidos con madera ≥ 1: 721 (29,4 %); con madera ≥ 1 y una mesa en el 3 × 3: 31 (1,3 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 733 (29,9 %) |
| sobresalto · reflejo: sobresalto, huir | 258 (10,5 %) |
| explorar · curiosidad: explorar | 196 (8,0 %) |
| CORE · sin candidatos | 177 (7,2 %) |
| perseguir_metas · metas: make_wood_pickaxe | 167 (6,8 %) |
| alimentarse · acercarse a agua | 112 (4,6 %) |
| huir · huir de lava | 101 (4,1 %) |
| huir · huir de flecha | 85 (3,5 %) |
| CORE · sigue dormido | 70 (2,9 %) |
| alimentarse · comer agua | 60 (2,4 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 447 (45,8 %) |
| metas: hierba | 150 (15,4 %) |
| metas: planta | 130 (13,3 %) |
| metas: vaca | 90 (9,2 %) |
| proteger: pide wood | 47 (4,8 %) |
| metas: carbon | 30 (3,1 %) |
| metas: hierro | 25 (2,6 %) |
| metas: place_table | 24 (2,5 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 24 |
| place_table · metas: make_wood_pickaxe | 6 |
| place_plant · metas: place_plant | 2 |

**Episodios con mesa y sin espada: 49** (7194 latidos desde la mesa).

- Latidos con madera ≥ 1: 2250 (31,3 %); con madera ≥ 1 y una mesa en el 3 × 3: 190 (2,6 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 1293 (18,0 %) |
| CORE · sin candidatos | 863 (12,0 %) |
| sobresalto · reflejo: sobresalto, huir | 642 (8,9 %) |
| explorar · curiosidad: explorar | 538 (7,5 %) |
| perseguir_metas · metas: make_wood_pickaxe | 421 (5,9 %) |
| alimentarse · acercarse a agua | 369 (5,1 %) |
| CORE · sigue dormido | 295 (4,1 %) |
| huir · huir de lava | 293 (4,1 %) |
| huir · huir de esqueleto | 290 (4,0 %) |
| huir · huir de flecha | 226 (3,1 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 728 (24,5 %) |
| metas: hierba | 487 (16,4 %) |
| metas: make_wood_sword | 341 (11,5 %) |
| metas: hierro | 285 (9,6 %) |
| metas: place_furnace | 276 (9,3 %) |
| metas: vaca | 162 (5,5 %) |
| metas: planta | 148 (5,0 %) |
| metas: piedra | 133 (4,5 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 47 |
| make_wood_pickaxe · metas: make_wood_pickaxe | 25 |
| place_stone · metas: place_stone | 12 |
| place_table · metas: make_wood_pickaxe | 8 |
| place_furnace · metas: place_furnace | 7 |
| place_plant · metas: place_plant | 4 |
| place_stone · proteger: cerrar place_stone | 3 |
| place_table · proteger: pide stone | 2 |
