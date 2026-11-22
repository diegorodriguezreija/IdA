Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · 117 episodios · score 12.68, 16.63, 11.02 · latidos cortados por la guillotina: 0 · mecanismos: factibilidad_temporal

Latidos de más de 100 ms de reloj (cognición): 0 (0, 0, 0 por semilla); máximo 74.0 ms.

### a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 1 (2,5 %) | 0 (0,0 %) | 1 (2,3 %) | 2 (1,7 %) |
| no encuentra sitio | 30 (75,0 %) | 24 (70,6 %) | 35 (81,4 %) | 89 (76,1 %) |
| no lo completa a tiempo | 4 (10,0 %) | 6 (17,6 %) | 4 (9,3 %) | 14 (12,0 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 2 (5,0 %) | 2 (5,9 %) | 0 (0,0 %) | 4 (3,4 %) |
| pasa la noche dentro | 2 (5,0 %) | 1 (2,9 %) | 2 (4,7 %) | 5 (4,3 %) |
| cortado por presupuesto | 1 (2,5 %) | 1 (2,9 %) | 1 (2,3 %) | 3 (2,6 %) |

Motivos dentro de cada causa (total de las semillas):

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | zombi | 2 |
| no encuentra sitio | — | 54 |
| no encuentra sitio | no empieza o no pide por falta de tiempo (11a') | 35 |
| no lo completa a tiempo | falta tiempo | 11 |
| no lo completa a tiempo | falta herramienta | 2 |
| no lo completa a tiempo | falta material | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.76) | 1 |
| sale antes del amanecer | perseguir_metas · metas: place_furnace | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.86) | 1 |
| pasa la noche dentro | — | 5 |
| cortado por presupuesto | None | 3 |

Latidos oscuros fuera antes de entrar (episodios que entran): mediana 16, máximo 79, n = 9.

### a3) Factibilidad en el tiempo en la primera noche (deuda 11a)

- Episodios con datos: 114; con un sitio elegido en la ventana: 34 (T infinito: 1).
- T_disponible al elegir: mediana 30 (p25-p75 15-80); holgura: mediana 16 (p25-p75 2-44).
- D* en el ocaso: {1.0: 31, 0.527: 17, 0.525: 9, 0.5291: 7, 0.6105: 4, 0.6658: 3, 0.6994: 3, 0.7228: 3, 0.711: 2, 0.7407: 2, 0.6937: 2, 0.6551: 2, 0.5625: 2, 0.6395: 2, 0.6295: 2, 0.544: 2, 0.6246: 2, 0.6446: 2, 0.5361: 2, 0.6151: 1, 0.6059: 1, 0.7169: 1, 0.6199: 1, 0.5808: 1, 0.6344: 1, 0.5929: 1, 0.6604: 1, 0.5559: 1, 0.5468: 1, 0.7052: 1, 0.6824: 1, 0.6498: 1, 0.7347: 1, 0.5659: 1}.
- Sitios no empezados o peticiones no hechas por falta de tiempo: 80 (68,4 %) episodios; 530 evaluaciones ({'requisitos': 335, 'sitio': 195}); antes de lo oscuro en 37 episodios.
- Causa de la primera noche de esos episodios: {'no encuentra sitio': 64, 'no lo completa a tiempo': 14, 'sale antes del amanecer': 1, 'pasa la noche dentro': 1}.
- Error de T_disponible (previsto − latidos reales hasta el primer daño en la ventana): mediana 21 (p25-p75 -4-41), n = 26; previsto 36, real 24; sin daño en la ventana: 7.

### b) Episodios que pasan la primera noche dentro

Episodios: 5.

| Causa de muerte | Episodios |
|---|---|
| sed | 2 |
| zombi | 2 |
| hambre | 1 |

- Latidos vividos desde el final de lo oscuro: mediana 232, mínimo 208, máximo 274.
- Salen del recinto tras la noche: 5 de 5; latidos desde el final de lo oscuro hasta salir: mediana 76.
- Al salir (0-9): comida mediana 1, bebida mediana 3; con comida ≤ 3: 4; con bebida ≤ 3: 3.
- Con `wake_up`: 5 de 5.

Qué gana desde el final de lo oscuro hasta salir (437 latidos):

| Estrategia · motivo | Latidos |
|---|---|
| refugiarse · volver al hogar | 76 (17,4 %) |
| CORE · sigue dormido | 68 (15,6 %) |
| CORE · sin candidatos | 64 (14,6 %) |
| afrontar · afrontar: esperar a zombi (golpes 3.0, margen 75, beneficio  | 53 (12,1 %) |
| afrontar · afrontar: acercarse a esqueleto (alcance 2, golpes 10.0, mar | 48 (11,0 %) |
| quieto_o_huir · último recurso: huir | 40 (9,2 %) |
| alimentarse · acercarse a agua | 20 (4,6 %) |
| proteger · acecha: proteger: dentro, dormir | 20 (4,6 %) |

| Peligro de la alarma | Hostil real | Gana | Latidos |
|---|---|---|---|
| ≥ 0,8 | hostil a ≤ 4 | afrontar | 107 (24,5 %) |
| peligro < 0,5 | sin hostil a ≤ 4 | CORE | 70 (16,0 %) |
| ≥ 0,8 | hostil a ≤ 4 | refugiarse | 65 (14,9 %) |
| peligro < 0,5 | hostil a ≤ 4 | CORE | 62 (14,2 %) |
| ≥ 0,8 | hostil a ≤ 4 | quieto_o_huir | 40 (9,2 %) |
| ≥ 0,8 | hostil a ≤ 4 | proteger | 31 (7,1 %) |
| ≥ 0,8 | hostil a ≤ 4 | alimentarse | 17 (3,9 %) |
| ≥ 0,8 | hostil a ≤ 4 | sobresalto | 14 (3,2 %) |
| 0,5-0,8 | hostil a ≤ 4 | afrontar | 11 (2,5 %) |
| 0,5-0,8 | hostil a ≤ 4 | refugiarse | 10 (2,3 %) |
| 0,5-0,8 | hostil a ≤ 4 | alimentarse | 5 (1,1 %) |
| 0,5-0,8 | hostil a ≤ 4 | sobresalto | 1 (0,2 %) |

| Propuesta de Proteger en esos latidos | Latidos |
|---|---|
| proteger: dentro, dormir | 282 (64,5 %) |
| Proteger no propone | 139 (31,8 %) |
| proteger: abrir carbon (hambre 1.00 > cobijo 0.05) | 3 (0,7 %) |
| proteger: abrir carbon (hambre 1.00 > cobijo 0.04) | 3 (0,7 %) |
| proteger: abrir piedra (hambre 1.00 > cobijo 0.01) | 2 (0,5 %) |
| proteger: abrir carbon (hambre 1.00 > cobijo 0.06) | 2 (0,5 %) |

| Impulso en esos latidos | Mediana | p75 |
|---|---|---|
| cansancio | 0.00 | 0.00 |
| cobijo | 0.20 | 0.41 |
| exploracion | 0.01 | 0.06 |
| hambre | 0.65 | 0.77 |
| hostil_d | 3.00 | 4.00 |
| luz | 0.80 | 0.96 |
| peligro_alarma | 0.96 | 1.00 |
| primero_total | 0.91 | 1.00 |
| proteger_total | 0.06 | 0.36 |
| puede_abrir | 1.00 | 1.00 |
| salud | 0.00 | 0.00 |
| sed | 0.53 | 0.65 |
| seguridad | 0.99 | 1.00 |

### b2) Quién saca del recinto (cada paso de dentro a fuera)

| Fase | Estrategia · motivo | Verbo | Veces |
|---|---|---|---|
| noche | perseguir_metas · metas: place_furnace | COGER | 2 |
| tras la noche | perseguir_metas · metas: place_furnace | COGER | 1 |
| noche | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.01) | COGER | 1 |
| noche | salir_del_recinto · salir del recinto: abrir piedra (sed 0.88 > cobijo 0.83) | COGER | 1 |
| noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.76) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.02) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.05) | COGER | 1 |
| noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.86) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.42 > cobijo 0.00) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.04) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.01) | COGER | 1 |

Al salir tras pasar dentro la primera noche (5): perseguir_metas · metas: place_furnace: 1; proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.01): 1; proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.02): 1; proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.04): 1; proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.01): 1.

### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 14 (15,7 %) | — |
| lejos | 0 (0,0 %) | — |
| dentro del alcance | 75 (84,3 %) | 2 |
- dentro del alcance, descartada: sin forma válida: falta material: 41
- dentro del alcance, descartada: hay candidatos y ninguno completable: 15
- dentro del alcance, descartada: falta para cavar: wood_pickaxe: 12
- dentro del alcance, descartada: sin forma válida: acceso que no se sabe cerrar: 6
- dentro del alcance, descartada: falta para cavar: iron_pickaxe, wood_pickaxe: 1
- clases que se pueden cavar según el modelo: {'arbol': 74, 'diamante': 2, 'piedra': 35}
- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {'falta material': 21193, 'vecina sin ver': 4879, 'acceso que no se sabe cerrar': 2249, 'válida': 386}
- acciones que el modelo sabe que cierran (episodios): {'place_table (sin material)': 57, 'place_stone (sin material)': 29, 'place_table (con material)': 7, 'place_stone (con material)': 6, 'place_furnace (sin material)': 2}; sin ninguna: 5

### c) Cadena de herramientas

Episodios con mesa: 99 (84,6 %).

Mesas colocadas por episodio (USAR que cambia el inventario): media 1.10, mediana 1, máximo 3; episodios con 2 o más: 27.

USAR con efecto: {'place_table': 129, 'place_plant': 80, 'make_wood_pickaxe': 76, 'place_stone': 57, 'make_wood_sword': 52, 'place_furnace': 23, 'make_stone_pickaxe': 10, 'make_stone_sword': 3}; sin efecto: {'place_table': 128, 'place_furnace': 86, 'make_wood_sword': 28, 'make_wood_pickaxe': 21, 'make_stone_pickaxe': 7, 'make_stone_sword': 7, 'place_stone': 5, 'place_plant': 1}.

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |
|---|---|---|---|
| make_wood_pickaxe | 76 (76,8 %) | 8 | 3-26 |
| make_wood_sword | 52 (52,5 %) | 16 | 8-55 |

**Episodios con mesa y sin pico: 23** (2268 latidos desde la mesa).

- Latidos con madera ≥ 1: 813 (35,8 %); con madera ≥ 1 y una mesa en el 3 × 3: 86 (3,8 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 630 (27,8 %) |
| sobresalto · reflejo: sobresalto, huir | 236 (10,4 %) |
| perseguir_metas · metas: make_wood_pickaxe | 226 (10,0 %) |
| explorar · curiosidad: explorar | 190 (8,4 %) |
| CORE · sin candidatos | 146 (6,4 %) |
| alimentarse · acercarse a agua | 129 (5,7 %) |
| huir · huir de lava | 78 (3,4 %) |
| CORE · sigue dormido | 70 (3,1 %) |
| huir · huir de flecha | 66 (2,9 %) |
| alimentarse · acercarse a vaca | 59 (2,6 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 476 (51,1 %) |
| metas: planta | 136 (14,6 %) |
| metas: hierba | 118 (12,7 %) |
| metas: vaca | 87 (9,3 %) |
| metas: carbon | 26 (2,8 %) |
| metas: place_table | 23 (2,5 %) |
| proteger: pide wood_pickaxe | 23 (2,5 %) |
| metas: hierro | 11 (1,2 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 23 |
| place_table · metas: make_wood_pickaxe | 6 |
| place_plant · metas: place_plant | 2 |

**Episodios con mesa y sin espada: 47** (6934 latidos desde la mesa).

- Latidos con madera ≥ 1: 2270 (32,7 %); con madera ≥ 1 y una mesa en el 3 × 3: 229 (3,3 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 1306 (18,8 %) |
| sobresalto · reflejo: sobresalto, huir | 707 (10,2 %) |
| CORE · sin candidatos | 663 (9,6 %) |
| explorar · curiosidad: explorar | 603 (8,7 %) |
| perseguir_metas · metas: make_wood_pickaxe | 426 (6,1 %) |
| alimentarse · acercarse a agua | 323 (4,7 %) |
| CORE · sigue dormido | 315 (4,5 %) |
| huir · huir de esqueleto | 267 (3,9 %) |
| perseguir_metas · metas: make_wood_sword | 208 (3,0 %) |
| huir · huir de flecha | 206 (3,0 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 715 (24,1 %) |
| metas: make_wood_sword | 464 (15,7 %) |
| metas: hierba | 439 (14,8 %) |
| metas: hierro | 281 (9,5 %) |
| metas: planta | 193 (6,5 %) |
| metas: place_furnace | 192 (6,5 %) |
| metas: piedra | 187 (6,3 %) |
| metas: vaca | 177 (6,0 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 46 |
| make_wood_pickaxe · metas: make_wood_pickaxe | 24 |
| place_stone · metas: place_stone | 12 |
| place_table · metas: make_wood_pickaxe | 11 |
| place_furnace · metas: place_furnace | 9 |
| place_plant · metas: place_plant | 8 |
| place_stone · proteger: cerrar place_stone | 3 |
| place_table · metas: make_wood_sword | 2 |
