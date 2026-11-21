# Inventario del conocimiento implícito del adaptador de Crafter

Paso 2.0 de la fase de generalización (`docs/ENCARGO_PASO2_MANUAL.md`). Fecha: 19/11/2026.

Lista de cada constante, umbral o regla de `ida/mundos/crafter.py` que codifica un hecho de Crafter más allá de la percepción pura. Las líneas se refieren a `ida/mundos/crafter.py` en `main` (088052c, etiqueta `crafter-procedimental-v1`), antes de los cambios del paso 2.

**Procedencia:**
- **Artículo / README:** Hafner (2021), arXiv:2109.06780v2, o README de `danijar/crafter`.
- **Código:** `crafter` 1.8.3 (`data.yaml`, `objects.py`, `env.py`).
- **Medido / diseño:** lo fijamos nosotros (medición en fases anteriores o decisión de diseño), sin fuente en Crafter.
- **Percepción:** se ve en la imagen oficial o es la forma de actuar del adaptador; se mantiene.

**Destino:** paso del plan en el que sale del mundo (`docs/FASE_GENERALIZACION_CRAFTER.md`, parte II).

## 1. Adaptador (`MundoCrafter`)

| Línea | Qué sabe | Procedencia | Destino |
|---|---|---|---|
| 36-38 | Nombres de materiales y criaturas (`MATERIALES`, `OBJETOS`) | Percepción (identidad visible de cada casilla y criatura) | Se mantiene |
| 39 | `HOSTILES`: zombi 0,8; esqueleto 0,7; flecha 0,5; lava 1,0 | Que son peligrosos: artículo (3.1, 3.2). Las gradaciones: diseño, sin fuente | Paso 2 (manual) |
| 44-46 | Nombres del inventario (`INVENTARIO`) | Percepción (filas de inventario de la imagen) | Se mantiene |
| 177-180 | Escala de constantes: salud, comida, bebida y energía sobre 9 | Código (`data.yaml:40-43`, `max: 9`); también visible en la imagen | Se mantiene |
| 177 | `alimentacion = min(comida, bebida)` | Diseño | Paso 0 |
| 180 | `cobijo = max(2, luz × 100)`: la oscuridad como necesidad | Diseño, sobre la luz percibida | Paso 0 / 3 |
| 189-191 | De noche (luz < 0,3) el radio de visión se reduce a la mitad | Diseño (restricción propia declarada; el artículo dice «the agent's view is restricted and noisy», 3.1) | Se mantiene (declarada) |
| 226-237 | `_deseo` (aliestesia): el agua vale según la sed; la vaca y la planta madura, según el hambre | Qué nutre: artículo (3.1). Que la planta solo nutre madura: código (`objects.py:188-191`) | Paso 0 |
| 230-232 | ×1,3 al deseo con salud < 7, «regeneración +1 cada 25 pasos si hay comida y bebida» | Regla: artículo (3.1, «Health points regenerate over time when the player is not hungry, thirsty, or sleepy»). Umbral 7 y factor 1,3: diseño | Paso 0 |
| 248 | `proximidad` = 1 a distancia Manhattan ≤ 1 y decae con el radio | Percepción | Se mantiene |
| 250 | `peligro` de una entidad = `HOSTILES` | Como la línea 39 | Paso 2 |
| 251 | `recurso` = 0,6 para árbol, piedra, carbón, hierro y diamante | Qué sirve: artículo (3.1, «resources, such as saplings, wood, stone, coal, iron, and diamonds»). El 0,6: diseño | Paso 2 |
| 243, 255 | Las hostiles se ordenan primero entre las 14 entidades | Diseño, sobre `HOSTILES` | Paso 2 |
| 262 | Casillas transitables (`constants.walkable`) | Percepción (se ve si la casilla está libre) | Se mantiene |
| 264 | Peligro de una casilla: el de la hostil más cercana × (1 − d/4) | Alcance 4: diseño | Paso 6 |
| 268 | Nutritivo de una casilla: gradiente hacia lo deseado, escala 4 × radio | Diseño | Paso 0 |
| 270 | Novedad: una casilla vuelve a ser nueva a los 50 pasos | Diseño | Se mantiene (o paso 1) |
| 297-305 | Para interactuar: girar hacia el objetivo y después `do` | Código (`objects.py`, orientación del jugador). Es la forma de actuar del adaptador | Se mantiene |
| 322-325 | COMER es éxito si sube comida o bebida; COGER, si algo entra en el inventario | Percepción (cambio del inventario visible) | Se mantiene |
| 353 | Atribución del daño: hostil a distancia ≤ 1, o ≤ 4 si es esqueleto | Código (zombi adyacente, `objects.py:303-311`; flecha, `objects.py:377`). Alcance 4 del esqueleto: diseño | Paso 6 |

## 2. Estrategias de S1: `DefensaArmada` y `CerrarDistancia`

| Línea | Qué sabe | Procedencia | Destino |
|---|---|---|---|
| 423 | Luchar solo con espada y salud ≥ 4 | Diseño (medido en fase C) | Paso 6 |
| 412-413, 426 | Zombi y esqueleto se abaten en 2-3 golpes con espada | Código (daño de espada `objects.py:182-187`; salud del zombi 5, `objects.py:287`) | Paso 6 |
| 435 | Urgencia 0,96 con salud ≥ 6, si no 0,88 | Diseño | Paso 0 / 6 |
| 441, 450 | El esqueleto tiene 3 de vitalidad y dispara desde 2-3 casillas; acercarse con salud ≥ 5 | Código (`objects.py`, clase `Skeleton`: dispara a distancia ≤ 5, se aleja a ≤ 3) | Paso 6 |

## 3. Estrategia de S2: `RefugioNocturno`

| Línea | Qué sabe | Procedencia | Destino |
|---|---|---|---|
| 503 | Casillas no transitables para un zombi | Código (`objects.py`, `Zombie` camina por grass, sand, path) | Paso 3 |
| 504 | Roca excavable: piedra y carbón (con pico de madera) | Código (`data.yaml:59-60`). Piedra con pico de madera también en el artículo (3.4) | Paso 3 / 5 |
| 505 | Transitables para el jugador: grass, path, sand | Código (`data.yaml:34-37`); percepción | Se mantiene |
| 513, 624-630 | Madera necesaria: mesa 2, pico 1, espada 1 | Código (`data.yaml:68, 73, 76`). El artículo solo dice «wood in inventory» | Paso 3 / 5 |
| 542, 988 | `LUZ_PLENO_DIA` = 0,83: con más luz no aparecen zombis (máximo 3,5 − 3 × luz por zona) | Código (`env.py:147`) | Paso 3 |
| 543 | Se recuerda una vaca 40 latidos | Diseño | Paso 1 |
| 583 | Luz < 0,35: ya ha pasado lo oscuro | Diseño | Paso 3 |
| 606-607 | Hostil «cerca» a distancia ≤ 4 | Diseño | Paso 3 / 6 |
| 612-613 | Mesa «cerca» = en el cuadrado 3 × 3 | Código (`objects.py:252`, `world.nearby(pos, 1)`) | Paso 5 |
| 620-622 | Qué es un pico y qué es una espada | Percepción (nombres del inventario) | Se mantiene |
| 660-681 | Mina: 3 casillas en línea, laterales en cruz no transitables para zombis | Diseño (fase C), sobre la línea 503 | Paso 3 |
| 683-687 | Sin lava a radio 2 de la mina | Lava peligrosa: artículo (3.2). Radio 2: diseño | Paso 3 |
| 699-704 | Puntuación de minas (agua en pared, fidelidad al hogar, rocas) | Diseño | Paso 3 |
| 745-761 | Coste en pasos: 2 por interacción, 3 por roca, 4 por cierre, 28 de margen | Adaptador (girar + `do`) y diseño | Paso 3 |
| 763-771 | Modelo de la luz: `1 − |cos(π t)|³` con día de 300 pasos | Código (`env.py:138`; duración del día en `env.py`) | Paso 3 |
| 853, 908, 1003 | Noche si luz < 0,5; salir con luz ≥ 0,65 | Diseño | Paso 3 |
| 854, 868, 883, 1008-1011 | Márgenes de tiempo (×1,35, ×1,55, ×1,8, ×1,9, 28, 32, 2,5 pasos por unidad) | Medido / diseño (fase C) | Paso 3 |
| 865, 875, 1157-1158, 1289, 1313, 1421 | Comida y bebida llenas = 9 | Código (`data.yaml:41-42`); visible en la imagen | Se mantiene |
| 946, 1017, 1208 | Sed crítica: bebida ≤ 3 | Diseño | Paso 0 |
| 1013-1033 | Urgencias del refugio (0,98; 0,92; 0,72 + 0,24 × empuje…) | Diseño (deuda 2: la intensidad no llega al Tribunal) | Paso 0 / 3 |
| 1146, 1222, 1230 | Despejar o abatir con espada y salud ≥ 4 (≥ 5 para el esqueleto) | Diseño | Paso 6 |
| 1255-1260 | Fabricar pico y espada de madera con madera ≥ 1 | Código (`data.yaml:73, 76`); artículo (tabla F.1, sin cantidad) | Paso 5 |
| 1266-1274 | Colocar la mesa con madera ≥ 2 sobre grass, sand o path | Código (`data.yaml:68`) | Paso 5 |
| 1323 | Abastecerse si bebida o comida < 8 | Diseño | Paso 0 |
| 1381, 1414 | Tapar la entrada con 1 piedra (`place_stone`) | Código (`data.yaml:67`); artículo (tabla F.1, «Stone in inventory.») | Paso 3 |
| 1435 | Dormir si energía < 9 | Artículo (tabla F.1, «Energy level is below maximum.») | Paso 3 |
| 1447-1449 | Al amanecer, picar la piedra de la entrada (se recupera) | Código (`data.yaml:59`, piedra da piedra) | Paso 3 |

## 4. Estrategia de S3: `PlanTecnologico`

| Línea | Qué sabe | Procedencia | Destino |
|---|---|---|---|
| 1482-1483 | Orden del árbol tecnológico (mesa → madera → piedra → horno → hierro) | Artículo (figura 4 y 3.4); código | Paso 5 |
| 1484 | Qué material da cada objeto del inventario (madera ← árbol…) | Código (`data.yaml:58-62`) | Paso 5 |
| 1524-1525 | Recetas y cantidades (`constants.place`, `constants.make`) | Código (`data.yaml:66-78`) | Paso 5 |
| 1529-1530 | Herramienta de cada mineral: diamante ← pico de hierro; hierro ← pico de piedra; carbón ← pico de madera | Diamante: artículo (3.4). Hierro y carbón: código (`data.yaml:60-62`) | Paso 5 |
| 1534, 1559, 1565 | Una receta u objetivo se abandona tras 3 fallos | Diseño | Paso 5 |
| 1539 | Plantar solo sobre grass | Código (`data.yaml:70`) | Paso 5 |
| 1542 | Hostiles a la vista impiden dormir de día (usa `HOSTILES` sin la lava) | Diseño, sobre `HOSTILES` | Paso 2 (lectura) / 5 |
| 1543-1544 | Dormir de día con energía ≤ 4 (≤ 6 sin necesidad de cobijo) y luz ≥ 0,5 | Diseño | Paso 3 / 5 |
| 1548-1553 | El retoño sale de la hierba; se reintenta hasta 6 veces | Código (`data.yaml:64`, probabilidad 0,1). El artículo dice «saplings» pero no de dónde salen | Paso 5 |
| 1582 | Estaciones necesarias para fabricar (`nearby`) | Código (`data.yaml:73-78`); artículo (tabla F.1) | Paso 5 |
| 1589 | Colocar una mesa nueva si no hay ninguna conocida y hay madera ≥ 2 | Código (`data.yaml:68`) | Paso 5 |

## 5. Resumen por destino

- **Paso 2 (este):** `HOSTILES` (líneas 39, 243, 250, 255, 264, 353 y la lectura de 1542) y la lista de recursos (línea 251).
- **Paso 0:** aliestesia (`_deseo`), `alimentacion = min(comida, bebida)`, urgencias numéricas.
- **Paso 3:** casi todo `RefugioNocturno`: geometría de la mina, modelo de la luz, umbrales de aparición de zombis, márgenes de tiempo.
- **Paso 5:** recetas, cantidades, herramientas por material, de dónde sale el retoño, dónde se puede colocar cada cosa.
- **Paso 6:** daño y alcance de las criaturas, cuándo luchar, atribución de la causa del daño.
- **Se mantiene (percepción o forma de actuar):** nombres, escala de 9, transitabilidad, proximidad, girar y `do`, éxito de COMER y COGER por el inventario visible.

## 6. Estado tras el paso 5 (rama `feature/planificador`)

- **Borrado:** `PlanTecnologico` entero (sección 4): recetas (`constants.make/place`), `OBJETIVOS`, `RECURSO`, `LOGROS_PLAN`, herramientas por mineral, plantar sobre hierba, retoño de la hierba y dormir de día. La tecnología la persigue `PerseguirMetas` (S3, general) con las metas y los requisitos del manual.
- **Pendiente para el paso 3:** `RefugioNocturno` sigue usando recetas propias como conducta de refugio: fabricar pico y espada de madera con madera ≥ 1 (líneas 1255-1260 de la tabla 3), colocar la mesa con madera ≥ 2 sobre grass, sand o path (1266-1274), tapar con 1 piedra (1381, 1414) y la madera necesaria de `_madera_faltante` (624-630).
- **Percepción nueva:** `cuerpo["delante"]` (clase e id de lo que hay en la casilla de delante; se ve). Para los suelos usa `SUELOS` (hierba, arena, camino), que solo nombra lo visible.

## 7. Estado tras el paso 3 (rama `feature/proteger`, subpaso 3c)

- **Borrado:** `RefugioNocturno` entero (sección 3) y lo que solo usaba él:
  - sus constantes: `NO_TRANSITABLES_ZOMBI`, `ROCA_EXCAVABLE`, `TRANSITABLES_JUGADOR`, `LUZ_PLENO_DIA` y `MEMORIA_VACA`;
  - su mapa propio y las lecturas de la propiocepción que lo alimentaban (`_inventario`, `_orientacion`, `_vista`, `_terreno`, `_luz`);
  - su apaño de motivación (0,98; 0,92; 0,84 + 0,12 × empuje);
  - lo que el adaptador daba solo para él: `cuerpo["vista"]` (la rejilla de materiales) y el dato `terreno` de cada lugar;
  - el arnés `herramientas/arnes_refugio_crafter.py`.
- **Quién lo hace ahora:** el refugio nocturno lo da la base: `Recinto` y `Proteger` (`ida/sistemas/proteger.py`), con el mapa local de la memoria, el modelo del cuerpo y la alostasis del cobijo. Siempre activos, sin interruptor. El material y las herramientas para cerrar o cavar se piden a `PerseguirMetas` como metas instrumentales.
- **Lo que el mundo da para eso:** solo percepción. Es `cuerpo["casillas"]`, la clase de cada casilla a la vista, con los mismos nombres que las entidades y que `SUELOS`.
- **Lo que queda en el mundo:** `DefensaArmada` y `CerrarDistancia` (sección 2, paso 6).

## 8. Estado tras el paso 6 (rama `feature/defensa`, subpaso 6d)

- **Conducta escrita para Crafter: ninguna.** `estrategias_propias()` devuelve `{}`, y un test (`tests/test_defensa.py::test_crafter_no_escribe_conducta`) comprueba que ninguna clase de `ida/mundos/crafter.py` hereda de `Definicion`, `Plan` ni `ConPropuestas`.
- **Borrado:**
  - `DefensaArmada` y `CerrarDistancia` (sección 2) y lo que solo usaban ellas: `ESPADAS`, `_salud`, `_tiene_espada` y `_posicion`;
  - `PELIGRO_MANUAL` (el 0,8 de lo que el manual declara PELIGROSO, líneas 250 y 264 de la tabla 1);
  - el peligro de las casillas, con alcance 4 (línea 264);
  - la atribución del daño por geometría, a ≤ 1 casilla y a ≤ 4 si es esqueleto (línea 353).
- **Quién lo hace ahora:** la base.
  - El peligro lo aprende `ida/core/peligro.py`: daño por golpe (despierto y dormido), tasa por latido de exposición, emisores por contingencia y su alcance, y golpes por derribo según lo que se lleva.
  - Luchar o huir lo decide `Afrontar` (S1).
  - El arma la pide `Afrontar` a `PerseguirMetas` como meta instrumental.
  - Todo siempre activo, sin interruptor.
- **Lo que el mundo da para eso:** solo percepción.
  - la posición de cada cosa;
  - si se mueve (`agente`);
  - la causa de un daño, que es lo peligroso en contacto con la casilla propia (`_contacto`), sin geometría de alcance;
  - qué es peligroso, que viene del manual (`PELIGROSO`) y solo da el previo.
- **Lo que queda en el mundo:** percepción, forma de actuar y el manual declarativo, incluidos los rasgos que lee del manual (`RECURSO_MANUAL`, `NUTRITIVO_MANUAL`).
