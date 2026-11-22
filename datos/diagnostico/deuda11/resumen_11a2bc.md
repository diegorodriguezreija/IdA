Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · 126 episodios · score 12.36, 10.58, 11.5 · latidos cortados por la guillotina: 0 · mecanismos: factibilidad_temporal, filtro_orientacion, material_mapa

Latidos de más de 100 ms de reloj (cognición): 0 (0, 0, 0 por semilla); máximo 98.3 ms.

### a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 2 (4,7 %) | 3 (7,3 %) | 2 (4,8 %) | 7 (5,6 %) |
| no encuentra sitio | 30 (69,8 %) | 28 (68,3 %) | 35 (83,3 %) | 93 (73,8 %) |
| no lo completa a tiempo | 8 (18,6 %) | 5 (12,2 %) | 4 (9,5 %) | 17 (13,5 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 2 (4,7 %) | 1 (2,4 %) | 0 (0,0 %) | 3 (2,4 %) |
| pasa la noche dentro | 1 (2,3 %) | 3 (7,3 %) | 0 (0,0 %) | 4 (3,2 %) |
| cortado por presupuesto | 0 (0,0 %) | 1 (2,4 %) | 1 (2,4 %) | 2 (1,6 %) |

Motivos dentro de cada causa (total de las semillas):

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | zombi | 5 |
| muere antes de anochecer | flecha | 2 |
| no encuentra sitio | no empieza o no pide por falta de tiempo (11a') | 66 |
| no encuentra sitio | — | 27 |
| no lo completa a tiempo | falta tiempo | 11 |
| no lo completa a tiempo | falta material | 4 |
| no lo completa a tiempo | falta herramienta | 2 |
| sale antes del amanecer | perseguir_metas · metas: make_stone_pickaxe | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.79) | 1 |
| sale antes del amanecer | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | 1 |
| pasa la noche dentro | — | 4 |
| cortado por presupuesto | None | 2 |

Latidos oscuros fuera antes de entrar (episodios que entran): mediana 21, máximo 57, n = 7.

### a3) Factibilidad en el tiempo en la primera noche (deuda 11a)

- Episodios con datos: 122; con un sitio elegido en la ventana: 66 (T infinito: 1).
- T_disponible al elegir: mediana 39 (p25-p75 22-86); holgura: mediana 18 (p25-p75 4-53).
- D* en el ocaso: {1.0: 26, 0.527: 15, 0.525: 11, 0.5291: 8, 0.6551: 6, 0.6016: 5, 0.7228: 4, 0.6151: 3, 0.6937: 3, 0.5497: 3, 0.6059: 3, 0.6344: 2, 0.7407: 2, 0.7347: 2, 0.6768: 2, 0.7052: 2, 0.5361: 2, 0.5313: 2, 0.5468: 2, 0.688: 1, 0.5412: 1, 0.6498: 1, 0.5929: 1, 0.6994: 1, 0.6246: 1, 0.5386: 1, 0.5625: 1, 0.6446: 1, 0.6658: 1, 0.7287: 1, 0.5592: 1, 0.6395: 1, 0.6604: 1, 0.6105: 1, 0.5847: 1, 0.5695: 1, 0.5659: 1, 0.711: 1}.
- Sitios no empezados o peticiones no hechas por falta de tiempo: 102 (81,0 %) episodios; 1029 evaluaciones ({'requisitos': 844, 'sitio': 185}); antes de lo oscuro en 69 episodios.
- Causa de la primera noche de esos episodios: {'no encuentra sitio': 82, 'no lo completa a tiempo': 16, 'muere antes de anochecer': 2, 'pasa la noche dentro': 1, 'sale antes del amanecer': 1}.
- Error de T_disponible (previsto − latidos reales hasta el primer daño en la ventana): mediana 23 (p25-p75 1-38), n = 57; previsto 37, real 18; sin daño en la ventana: 8.

### b) Episodios que pasan la primera noche dentro

Episodios: 4.

| Causa de muerte | Episodios |
|---|---|
| sed | 2 |
| zombi | 1 |
| hambre | 1 |

- Latidos vividos desde el final de lo oscuro: mediana 158, mínimo 89, máximo 240.
- Salen del recinto tras la noche: 4 de 4; latidos desde el final de lo oscuro hasta salir: mediana 42.
- Al salir (0-9): comida mediana 2, bebida mediana 2; con comida ≤ 3: 3; con bebida ≤ 3: 4.
- Con `wake_up`: 3 de 4.

Qué gana desde el final de lo oscuro hasta salir (180 latidos):

| Estrategia · motivo | Latidos |
|---|---|
| CORE · sin candidatos | 78 (43,3 %) |
| proteger · proteger: dentro, dormir | 28 (15,6 %) |
| alimentarse · acercarse a agua | 23 (12,8 %) |
| sobresalto · reflejo: sobresalto, huir | 15 (8,3 %) |
| alimentarse · acercarse a vaca | 14 (7,8 %) |
| proteger · acecha: proteger: dentro, dormir | 13 (7,2 %) |
| refugiarse · volver al hogar | 6 (3,3 %) |
| perseguir_metas · metas: piedra | 3 (1,7 %) |

| Peligro de la alarma | Hostil real | Gana | Latidos |
|---|---|---|---|
| peligro < 0,5 | hostil a ≤ 4 | CORE | 78 (43,3 %) |
| ≥ 0,8 | hostil a ≤ 4 | proteger | 38 (21,1 %) |
| ≥ 0,8 | hostil a ≤ 4 | alimentarse | 26 (14,4 %) |
| 0,5-0,8 | hostil a ≤ 4 | alimentarse | 10 (5,6 %) |
| ≥ 0,8 | hostil a ≤ 4 | sobresalto | 9 (5,0 %) |
| ≥ 0,8 | hostil a ≤ 4 | refugiarse | 5 (2,8 %) |
| 0,5-0,8 | hostil a ≤ 4 | sobresalto | 4 (2,2 %) |
| peligro < 0,5 | hostil a ≤ 4 | proteger | 3 (1,7 %) |
| ≥ 0,8 | hostil a ≤ 4 | perseguir_metas | 2 (1,1 %) |
| ≥ 0,8 | sin hostil a ≤ 4 | alimentarse | 1 (0,6 %) |
| ≥ 0,8 | sin hostil a ≤ 4 | sobresalto | 1 (0,6 %) |
| peligro < 0,5 | hostil a ≤ 4 | perseguir_metas | 1 (0,6 %) |

| Propuesta de Proteger en esos latidos | Latidos |
|---|---|
| proteger: dentro, dormir | 99 (55,0 %) |
| Proteger no propone | 78 (43,3 %) |
| proteger: abrir piedra (sed 1.00 > cobijo 0.61) | 1 (0,6 %) |
| proteger: abrir piedra (sed 1.00 > cobijo 0.60) | 1 (0,6 %) |
| proteger: abrir piedra (sed 1.00 > cobijo 0.59) | 1 (0,6 %) |

| Impulso en esos latidos | Mediana | p75 |
|---|---|---|
| cansancio | 0.00 | 0.00 |
| cobijo | 0.36 | 0.58 |
| exploracion | 0.02 | 0.13 |
| hambre | 0.53 | 0.65 |
| hostil_d | 2.00 | 3.00 |
| luz | 0.61 | 0.79 |
| peligro_alarma | 0.78 | 0.96 |
| primero_total | 0.22 | 0.67 |
| proteger_total | 0.11 | 0.40 |
| puede_abrir | 1.00 | 1.00 |
| salud | 0.00 | 0.00 |
| sed | 0.53 | 0.65 |
| seguridad | 0.95 | 0.97 |

### b2) Quién saca del recinto (cada paso de dentro a fuera)

| Fase | Estrategia · motivo | Verbo | Veces |
|---|---|---|---|
| tras la noche | perseguir_metas · metas: make_stone_pickaxe | COGER | 1 |
| noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.79) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.58) | COGER | 1 |
| tras la noche | proteger · proteger: abrir arbol (sed 0.77 > cobijo 0.01) | COGER | 1 |
| tras la noche | proteger · proteger: abrir arbol (hambre 0.77 > cobijo 0.28) | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.19) | COGER | 1 |
| noche | proteger · proteger: abrir piedra (hambre 0.88 > cobijo 0.88) | COGER | 1 |
| tras la noche | perseguir_metas · metas: place_furnace | COGER | 1 |
| tras la noche | proteger · proteger: abrir piedra (hambre 0.53 > cobijo 0.53) | COGER | 1 |

Al salir tras pasar dentro la primera noche (4): proteger · proteger: abrir piedra (sed 1.00 > cobijo 0.58): 1; proteger · proteger: abrir arbol (sed 0.77 > cobijo 0.01): 1; proteger · proteger: abrir arbol (hambre 0.77 > cobijo 0.28): 1; proteger · proteger: abrir piedra (hambre 1.00 > cobijo 0.19): 1.

### a2) «No encuentra sitio»: casilla conocida más cercana de una clase que se puede cavar

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 13 (14,0 %) | — |
| lejos | 0 (0,0 %) | — |
| dentro del alcance | 80 (86,0 %) | 2 |
- dentro del alcance, descartada: sin forma válida: falta material: 27
- dentro del alcance, descartada: hay candidatos y ninguno completable: 27
- dentro del alcance, descartada: falta para cavar: wood_pickaxe: 17
- dentro del alcance, descartada: sin forma válida: acceso que no se sabe cerrar: 7
- dentro del alcance, descartada: falta para cavar: iron_pickaxe, wood_pickaxe: 1
- dentro del alcance, descartada: falta para cavar: iron_pickaxe: 1
- clases que se pueden cavar según el modelo: {'arbol': 80, 'piedra': 46, 'carbon': 2, 'diamante': 2}
- formas de 1-3 casillas al alcance, por la primera razón de descarte (suma de episodios): {'falta material': 24525, 'vecina sin ver': 5595, 'acceso que no se sabe cerrar': 1997, 'válida': 1419}
- acciones que el modelo sabe que cierran (episodios): {'place_table (sin material)': 55, 'place_stone (sin material)': 33, 'place_stone (con material)': 13, 'place_table (con material)': 12, 'place_furnace (sin material)': 5, 'place_furnace (con material)': 3, 'place_plant (con material)': 1}; sin ninguna: 6

### c) Cadena de herramientas

Episodios con mesa: 105 (83,3 %).

Mesas colocadas por episodio (USAR que cambia el inventario): media 1.14, mediana 1, máximo 5; episodios con 2 o más: 26.

USAR con efecto: {'place_table': 144, 'make_wood_pickaxe': 85, 'place_plant': 72, 'place_stone': 56, 'make_wood_sword': 48, 'place_furnace': 13, 'make_stone_pickaxe': 8, 'make_stone_sword': 2}; sin efecto: {'place_table': 136, 'place_furnace': 96, 'make_wood_sword': 25, 'make_wood_pickaxe': 16, 'place_stone': 7, 'place_plant': 4, 'make_stone_sword': 2}.

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa (mediana) | (p25-p75) |
|---|---|---|---|
| make_wood_pickaxe | 84 (80,0 %) | 7 | 3-24 |
| make_wood_sword | 48 (45,7 %) | 16 | 7-45 |

**Episodios con mesa y sin pico: 21** (2812 latidos desde la mesa).

- Latidos con madera ≥ 1: 1189 (42,3 %); con madera ≥ 1 y una mesa en el 3 × 3: 56 (2,0 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 527 (18,7 %) |
| CORE · sin candidatos | 325 (11,6 %) |
| perseguir_metas · metas: make_wood_pickaxe | 315 (11,2 %) |
| explorar · curiosidad: explorar | 279 (9,9 %) |
| sobresalto · reflejo: sobresalto, huir | 273 (9,7 %) |
| alimentarse · acercarse a agua | 224 (8,0 %) |
| huir · huir de flecha | 91 (3,2 %) |
| alimentarse · acercarse a vaca | 83 (3,0 %) |
| CORE · sigue dormido | 77 (2,7 %) |
| alimentarse · comer agua | 60 (2,1 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 534 (42,9 %) |
| metas: carbon | 181 (14,5 %) |
| metas: hierba | 146 (11,7 %) |
| metas: vaca | 118 (9,5 %) |
| metas: hierro | 86 (6,9 %) |
| proteger: pide wood | 57 (4,6 %) |
| metas: planta | 55 (4,4 %) |
| proteger: pide wood_pickaxe | 28 (2,2 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 21 |
| place_table · metas: make_wood_pickaxe | 4 |
| place_plant · metas: place_plant | 2 |

**Episodios con mesa y sin espada: 57** (8884 latidos desde la mesa).

- Latidos con madera ≥ 1: 2786 (31,4 %); con madera ≥ 1 y una mesa en el 3 × 3: 206 (2,3 %).

| Estrategia · motivo que gana | Latidos |
|---|---|
| huir · huir de zombi | 1544 (17,4 %) |
| CORE · sin candidatos | 988 (11,1 %) |
| sobresalto · reflejo: sobresalto, huir | 862 (9,7 %) |
| perseguir_metas · metas: make_wood_pickaxe | 661 (7,4 %) |
| alimentarse · acercarse a agua | 629 (7,1 %) |
| explorar · curiosidad: explorar | 624 (7,0 %) |
| huir · huir de flecha | 376 (4,2 %) |
| huir · huir de esqueleto | 307 (3,5 %) |
| perseguir_metas · metas: place_furnace | 265 (3,0 %) |
| alimentarse · acercarse a vaca | 247 (2,8 %) |

| Mejor propuesta de PerseguirMetas (gane o no) | Latidos |
|---|---|
| metas: make_wood_pickaxe | 966 (23,0 %) |
| metas: place_furnace | 737 (17,5 %) |
| metas: piedra | 393 (9,3 %) |
| metas: carbon | 393 (9,3 %) |
| metas: hierba | 383 (9,1 %) |
| metas: make_wood_sword | 273 (6,5 %) |
| metas: vaca | 239 (5,7 %) |
| metas: hierro | 191 (4,5 %) |

| USAR con éxito tras la mesa (objetivo · motivo) | Veces |
|---|---|
| place_table · metas: place_table | 54 |
| make_wood_pickaxe · metas: make_wood_pickaxe | 35 |
| place_stone · metas: place_stone | 21 |
| place_table · metas: make_wood_pickaxe | 11 |
| place_plant · metas: place_plant | 8 |
| place_furnace · metas: place_furnace | 5 |
| place_table · metas: make_stone_pickaxe | 4 |
| make_stone_pickaxe · metas: make_stone_pickaxe | 3 |
