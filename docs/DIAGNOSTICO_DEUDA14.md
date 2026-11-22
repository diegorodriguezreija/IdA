# Diagnóstico de la deuda 14: la cadena de herramientas tras la mesa

Fecha: 22/11/2026. Rama `feature/deuda14`, código `7dfcfc1` (14.0: Crafter por turnos, plazo base de 1000 ms). Encargo: `docs/ENCARGO_DEUDA14_HERRAMIENTAS.md`, 14.1. Es un diagnóstico, no una medición oficial.

## Comando

En serie, sin ningún otro proceso de IdA en la máquina, guillotina lógica:

```bash
.venv\Scripts\python.exe herramientas\diagnostico_deuda14.py --pasos 10000 --semilla S --plazo-logico 40 --salida datos\diagnostico\deuda14\apagados_semillaS.json
.venv\Scripts\python.exe herramientas\diagnostico_deuda14.py --resumir datos\diagnostico\deuda14\apagados_semilla3{1,2,3}.json
```

Semillas 31, 32 y 33, 10 000 pasos cada una (vista oficial, sin herencia, manual estricto, sin estrategias propias). Resumen completo: `datos/diagnostico/deuda14/resumen_apagados.md`. La herramienta no cambia la conducta. La mesa y su distancia son las del mundo (`_mat_map`); «al alcance» es el 3 × 3 del jugador, la regla de Crafter para fabricar.

**Control:**
- Las Scores (15,05 / 17,00 / 10,60) son las de «apagados» en `docs/DIAGNOSTICO_DEUDA11.md`.
- Los 35 episodios completos de la semilla 31 y los 32 de la 32 tienen los mismos pasos que los primeros episodios de `base_v2_31.json` y `base_v2_32.json`.
- 0 latidos cortados. El latido más lento, 4,3 ms de reloj.

## Datos

112 episodios; 95 con mesa (84,8 %). Tras la mesa, el 77,9 % fabrica el pico (mediana: 8 latidos después) y el 51,6 % la espada (16 latidos).

**Madera justo después de colocar la primera mesa:** 0 en 86 de 95 episodios, 1 en 7, 2 en 1 y 3 en 1. La mesa gasta 2 de madera (`data.yaml`), y casi siempre era toda la que había.

| Pregunta | Con mesa y sin pico (21 episodios) | Con mesa y sin espada (46 episodios) |
|---|---|---|
| **1. Madera con una mesa al alcance** | | |
| Latidos con la mesa al alcance (de los latidos desde la mesa) | 345 (14,3 %) | 1247 (17,4 %) |
| — con 0 de madera | 254 (73,6 %) | 1067 (85,6 %) |
| — con 1 / 2 / 3 | 63 / 12 / 16 | 149 / 15 / 16 |
| Episodios con 0 de madera en todos esos latidos | 14 de 21 | 14 de 46 |
| Comparación: los que sí la fabrican, antes de hacerlo, con 0 de madera | 66,4 % | 62,9 % |
| **2. Meta de PerseguirMetas en los 50 latidos tras la mesa** | | |
| Ninguna (PerseguirMetas no propone meta) | 53,1 % | 48,4 % |
| `make_wood_pickaxe` | 22,1 % | 16,3 % |
| `make_wood_sword` | 0,3 % | 5,5 % |
| Otras (planta, vaca, hierba, horno, piedra…) | 24,5 % | 29,8 % |
| Distancia a la mesa, mediana (p25-p75): latidos 1-10 / 11-25 / 26-50 | 2 (1-3) / 4 (1-7) / 7 (4-9) | 1 (1-2) / 3 (1-6) / 5 (2-8) |
| Al alcance: latidos 1-10 / 11-25 / 26-50 | 48,1 % / 27,0 % / 13,5 % | 52,4 % / 26,6 % / 14,9 % |
| **3. Mesa al alcance, madera ≥ 1, falta la herramienta y no se fabrica** | 91 latidos | 180 latidos |
| Gana `metas: make_wood_pickaxe` | 14,3 % | 27,2 % |
| Gana `metas: make_wood_sword` | 3,3 % | 2,8 % |
| Gana huir (lava, zombi, flecha), sobresalto o «último recurso» | 59,4 % | 38,9 % |
| PerseguirMetas propone fabricar esa herramienta | 37,4 % (puesto mediano 2) | 3,9 % (puesto mediano 2) |
| **4. Muertes** | | |
| Mueren sin la herramienta | 20 (95,2 %): zombi 19, flecha 1 | 45 (97,8 %): zombi 35, sed 4, flecha 3, hambre 3 |
| Latidos de la primera mesa a la muerte, mediana (p25-p75) | 112 (77-163) | 135 (89-191) |
| Se alejan y no vuelven a tener la mesa al alcance | 6 | 10 |
| Vuelven al menos una vez | 14 | 35 |
| Latidos desde la última vez al alcance hasta la muerte, mediana (p25-p75) | 63 (34-100) | 60 (30-100) |

«Huir de lava» suma 33 latidos en cada columna. No se ha mirado en cuántos episodios ocurre ni si son los mismos latidos.

## Lectura frente a las hipótesis

1. **«No reúne de una vez la madera»: la apoyan los datos.** Tras la primera mesa quedan 0 de madera en 86 de 95 episodios. En los latidos con la mesa al alcance, el 74-86 % de las veces no hay madera. Los que sí fabrican la herramienta también llegan a menudo sin madera (63-66 %), pero vuelven con ella.
2. **«Elige una meta cada vez y se aleja de la mesa»: la apoyan los datos.** En los 50 latidos tras la mesa, la espada es la meta del planificador en el 0,3-5,5 % de los latidos. En la mitad de los latidos PerseguirMetas no propone ninguna meta. La distancia a la mesa pasa de una mediana de 1-2 a una de 5-7, y la fracción al alcance baja del 48-52 % al 14-15 %. Cuando está junto a la mesa con madera y sin espada, el planificador propone el pico (27 %) y casi nunca la espada (3,9 %). Con una sola unidad de madera, el pico la gasta.
3. **«Muere antes de volver»: la apoyan solo en parte.** Casi todos los episodios sin herramienta mueren sin ella (95-98 %), sobre todo por zombi, una mediana de 112-135 latidos después de la mesa. Pero solo 6 y 10 mueren sin volver a la mesa. La mayoría (14 de 20 y 35 de 45) vuelve al menos una vez, y lo que les falta entonces es la madera (punto 1). El coste de volver no está en llegar a la mesa, sino en llegar con el material.
4. **El Tribunal pesa, pero no explica lo principal.** Con mesa, madera y sin pico, huir (de lava sobre todo) gana el 59 % de esos latidos. Pero son pocos latidos (91 y 180 en tres semillas): lo que falta es estar junto a la mesa con madera, no ganar el Tribunal en ese momento.

**Conclusión:** los datos apoyan las hipótesis 1 y 2, que son las que atacan 14.2 (reunir el material del lote antes de ir) y 14.3 (hacer junto a la mesa lo que ya se puede). La 3 se matiza: no hace falta acortar la vuelta, sino volver con el material. Se sigue con 14.2 y 14.3.

**Lo que no explica este diagnóstico:** por qué PerseguirMetas no propone meta en la mitad de los latidos tras la mesa (otra estrategia activa para el impulso, peticiones de Proteger o ninguna meta resoluble). No se ha investigado.
