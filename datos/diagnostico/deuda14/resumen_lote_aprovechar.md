Semillas 31, 32, 33 · 10000, 10000, 10000 pasos · mecanismos: aprovechar_estacion, lote_estacion · 115 episodios · latidos cortados: 0 · máximo de ms por latido (reloj): 4.3 · tiempo: 119.9, 120.1, 129.1 s

### Por semilla

| Semilla | Episodios | Score | Pico | Espada | `wake_up` | Muertes por zombi | Pasos por episodio |
|---|---|---|---|---|---|---|---|
| 31 | 37 | 16,25 | 62,16 | 43,24 | 24,32 | 25 (67,6 %) | 270,3 |
| 32 | 36 | 15,32 | 69,44 | 55,56 | 25,00 | 23 (63,9 %) | 277,8 |
| 33 | 42 | 10,93 | 69,05 | 47,62 | 9,52 | 36 (85,7 %) | 238,1 |

Episodios con mesa: 99 (86,1 %). Madera justo después de la primera mesa: {0: 90, 1: 7, 2: 1, 3: 1}.

| Herramienta | Tras la mesa | Latidos desde la mesa: mediana (p25-p75) |
|---|---|---|
| make_wood_pickaxe | 77 (77,8 %) | 10 (4-28) |
| make_wood_sword | 56 (56,6 %) | 16 (9-48) |

## Con mesa y sin pico (22 episodios)

**1. Madera con una mesa al alcance.** Latidos con la mesa al alcance: 858 (35,7 %) de los latidos desde la mesa.

| Madera | Sin pico (latidos) | Con pico, antes de fabricarlo (latidos) |
|---|---|---|
| 0 | 816 (95,1 %) | 381 (70,9 %) |
| 1 | 13 (1,5 %) | 109 (20,3 %) |
| 2 | 10 (1,2 %) | 40 (7,4 %) |
| 3 | 19 (2,2 %) | 7 (1,3 %) |

Episodios sin pico que tienen la mesa al alcance algún latido: 22; de ellos, con 0 de madera en todos esos latidos: 15.

**2. Meta de PerseguirMetas en los 50 latidos tras la mesa** (965 latidos).

| Meta | Latidos |
|---|---|
| (PerseguirMetas no propone meta) | 562 (58,2 %) |
| lote mesa (make_wood_pickaxe, make_wood_sword) | 222 (23,0 %) |
| make_wood_pickaxe | 98 (10,2 %) |
| vaca | 44 (4,6 %) |
| hierba | 16 (1,7 %) |
| planta | 13 (1,3 %) |
| hierro | 6 (0,6 %) |
| agua | 3 (0,3 %) |
| probar a coger agua (sin plan) | 1 (0,1 %) |

| Latidos tras la mesa | Distancia a la mesa: mediana (p25-p75) | Al alcance |
|---|---|---|
| 1-10 | 2 (1-3) | 89 (40,8 %) |
| 11-25 | 3 (2-6) | 74 (24,7 %) |
| 26-50 | 6 (2-9) | 74 (19,7 %) |

Episodios que mueren dentro de la ventana: 8.

**3. Quién gana con la mesa al alcance, madera ≥ 1 y sin fabricar** (42 latidos).

| Estrategia · motivo | Latidos |
|---|---|
| huir · huir de zombi | 9 (21,4 %) |
| defenderse · defenderse de zombi | 9 (21,4 %) |
| perseguir_metas · metas: lote mesa (make_wood_pickaxe, make_wood_sword) | 5 (11,9 %) |
| sobresalto · reflejo: sobresalto, huir | 5 (11,9 %) |
| proteger · proteger: colocarse arena | 4 (9,5 %) |
| perseguir_metas · proteger: pide wood_pickaxe | 3 (7,1 %) |
| CORE · sin candidatos | 2 (4,8 %) |
| perseguir_metas · metas: make_wood_pickaxe | 2 (4,8 %) |
| perseguir_metas · metas: place_table | 1 (2,4 %) |
| proteger · proteger: cerrar place_table | 1 (2,4 %) |

PerseguirMetas propone fabricar el pico en 1 (2,4 %) de esos latidos; puesto entre los evaluados (mediana): 2.

**4. Muertes.** Mueren sin el pico: 22 (100,0 %); causas: {'zombi': 19, 'hambre': 2, 'flecha': 1}.

- Latidos entre la primera mesa y la muerte: mediana 82 (38-118).
- Se alejan de la mesa y no vuelven a tenerla al alcance antes de morir: 8; vuelven al menos una vez: 14.
- Latidos desde la última vez con una mesa al alcance hasta la muerte: mediana 43 (18-90).

## Con mesa y sin espada (43 episodios)

**1. Madera con una mesa al alcance.** Latidos con la mesa al alcance: 1220 (19,0 %) de los latidos desde la mesa.

| Madera | Sin espada (latidos) | Con espada, antes de fabricarlo (latidos) |
|---|---|---|
| 0 | 1107 (90,7 %) | 372 (66,8 %) |
| 1 | 79 (6,5 %) | 135 (24,2 %) |
| 2 | 15 (1,2 %) | 42 (7,5 %) |
| 3 | 19 (1,6 %) | 8 (1,4 %) |

Episodios sin espada que tienen la mesa al alcance algún latido: 43; de ellos, con 0 de madera en todos esos latidos: 15.

**2. Meta de PerseguirMetas en los 50 latidos tras la mesa** (1969 latidos).

| Meta | Latidos |
|---|---|
| (PerseguirMetas no propone meta) | 1016 (51,6 %) |
| lote mesa (make_wood_pickaxe, make_wood_sword) | 269 (13,7 %) |
| make_wood_pickaxe | 186 (9,4 %) |
| hierba | 90 (4,6 %) |
| place_furnace | 84 (4,3 %) |
| make_wood_sword | 81 (4,1 %) |
| vaca | 76 (3,9 %) |
| piedra | 68 (3,5 %) |
| planta | 40 (2,0 %) |
| carbon | 17 (0,9 %) |

| Latidos tras la mesa | Distancia a la mesa: mediana (p25-p75) | Al alcance |
|---|---|---|
| 1-10 | 2 (1-2) | 206 (48,1 %) |
| 11-25 | 3 (2-5) | 132 (22,0 %) |
| 26-50 | 6 (2-9) | 114 (13,2 %) |

Episodios que mueren dentro de la ventana: 10.

**3. Quién gana con la mesa al alcance, madera ≥ 1 y sin fabricar** (113 latidos).

| Estrategia · motivo | Latidos |
|---|---|
| huir · huir de zombi | 23 (20,4 %) |
| perseguir_metas · metas: make_wood_pickaxe | 18 (15,9 %) |
| CORE · sin candidatos | 10 (8,8 %) |
| defenderse · defenderse de zombi | 9 (8,0 %) |
| sobresalto · reflejo: sobresalto, huir | 8 (7,1 %) |
| perseguir_metas · metas: lote mesa (make_wood_pickaxe, make_wood_sword) | 8 (7,1 %) |
| explorar · curiosidad: explorar | 7 (6,2 %) |
| huir · huir de flecha | 5 (4,4 %) |
| perseguir_metas · proteger: pide wood_pickaxe | 5 (4,4 %) |
| huir · huir de esqueleto | 4 (3,5 %) |

PerseguirMetas propone fabricar el espada en 6 (5,3 %) de esos latidos; puesto entre los evaluados (mediana): 2.

**4. Muertes.** Mueren sin el espada: 43 (100,0 %); causas: {'zombi': 33, 'hambre': 6, 'sed': 2, 'flecha': 2}.

- Latidos entre la primera mesa y la muerte: mediana 111 (54-186).
- Se alejan de la mesa y no vuelven a tenerla al alcance antes de morir: 13; vuelven al menos una vez: 30.
- Latidos desde la última vez con una mesa al alcance hasta la muerte: mediana 69 (24-163).
