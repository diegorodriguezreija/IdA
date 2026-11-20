# Diagnóstico del paso 3 en Crafter: primera noche, después de la noche y cadena de herramientas

Fecha: 20/11/2026. Rama `feature/proteger`, código `04a6417` (3c: sin `RefugioNocturno`, `Proteger` siempre activo). Es un diagnóstico: la herramienta no cambia la conducta. No es una medición oficial.

**Comando** (línea general: sin estrategias propias, manual estricto, sin herencia, vista oficial):

```bash
python herramientas/diagnostico_paso3.py --pasos 10000 --semilla 31 --salida datos/diagnostico/paso3_semilla31.json
python herramientas/diagnostico_paso3.py --pasos 10000 --semilla 32 --salida datos/diagnostico/paso3_semilla32.json
python herramientas/diagnostico_paso3.py --pasos 10000 --semilla 33 --salida datos/diagnostico/paso3_semilla33.json
python herramientas/diagnostico_paso3.py --resumir datos/diagnostico/paso3_semilla3{1,2,3}.json
```

**Muestra:** 3 × 10 000 pasos, 114 episodios (37, 38 y 39). Score de esas vidas: 12,75, 10,13 y 11,48.

**Criterios de clasificación:** están en la cabecera de `herramientas/diagnostico_paso3.py`.
- «Dentro» es un recinto **real** del mundo: 1-3 casillas sin vecinas transitables para un zombi. No es lo que cree IdA.
- La ventana de la primera noche va de la primera luz < 0,5 al final de lo oscuro (luz < 0,3).

## a) Primera noche de cada episodio

| Causa | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| muere antes de anochecer | 0 (0,0 %) | 0 (0,0 %) | 1 (2,6 %) | 1 (0,9 %) |
| no encuentra sitio | 19 (51,4 %) | 22 (57,9 %) | 26 (66,7 %) | 67 (58,8 %) |
| no lo completa a tiempo | 12 (32,4 %) | 11 (28,9 %) | 5 (12,8 %) | 28 (24,6 %) |
| entra un peligro, se rompe o muere dentro | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) | 0 (0,0 %) |
| sale antes del amanecer | 0 (0,0 %) | 1 (2,6 %) | 1 (2,6 %) | 2 (1,8 %) |
| pasa la noche dentro | 5 (13,5 %) | 4 (10,5 %) | 5 (12,8 %) | 14 (12,3 %) |
| cortado por presupuesto (último episodio, vivo) | 1 (2,7 %) | 0 (0,0 %) | 1 (2,6 %) | 2 (1,8 %) |

| Causa | Motivo | Episodios |
|---|---|---|
| muere antes de anochecer | esqueleto | 1 |
| no encuentra sitio | `Recinto` sin sitio ni requisitos en el primer latido oscuro | 67 |
| no lo completa a tiempo | falta material | 12 |
| no lo completa a tiempo | falta tiempo (tenía un sitio completable con lo que llevaba) | 8 |
| no lo completa a tiempo | falta herramienta | 8 |
| sale antes del amanecer | `proteger: abrir piedra (sed 1.00 > cobijo 0.86)` | 1 |
| sale antes del amanecer | `metas: place_furnace` | 1 |

**Lo que llega tarde:** los 16 episodios que entran en la ventana pasan una mediana de 34 latidos oscuros fuera antes de entrar, con un máximo de 65.

**Más sobre «no encuentra sitio»** (67 episodios; cálculo sobre los mismos JSON con un script aparte que no se ha guardado):
- En los 67, la pieza `recinto` existe y está vacía (`coste` nulo, sin acción, sin requisitos).
- 33 tenían ya el pico de madera antes de lo oscuro y 47 la mesa.
- Solo 3 habían recogido piedra antes de lo oscuro.
- Mueren 54 por zombi, 5 por sed, 3 por desgaste, 3 por esqueleto y 2 por hambre.
- Hipótesis, no verificada: en el mapa local no hay ninguna casilla de una clase que se pueda cavar (roca) a menos de 15 pasos. Los sitios en campo abierto piden demasiados cierres para lo que el planificador puede conseguir, así que `_requisitos` devuelve nada. Para comprobarlo habría que registrar las clases del mapa local en ese latido.

**Pico antes de lo oscuro, por grupo:**

| Grupo | Episodios con pico antes de lo oscuro |
|---|---|
| pasan la noche dentro | 13 de 14 |
| no lo completan a tiempo | 14 de 28 |
| todos los que llegan a lo oscuro | 62 de 111 |

## b) Episodios que pasan la primera noche dentro (14)

| Causa de muerte | Episodios |
|---|---|
| sed | 5 |
| zombi | 4 |
| hambre | 3 |
| esqueleto | 2 |

- Los 14 consiguen `wake_up` y los 14 salen del recinto después de la noche.
- **Cuándo salen:** una mediana de 62 latidos después del final de lo oscuro.
- **Cuánto viven después:** desde el final de lo oscuro, una mediana de 212 latidos (mínimo 100, máximo 268).
- **Cómo salen** (escala 0-9):
  - comida: mediana 2, y 12 de 14 salen con 3 o menos;
  - bebida: mediana 2, y 11 de 14 salen con 3 o menos.
- **De qué mueren:** 8 de 14, de sed o de hambre. Pasar la noche dentro cuesta las provisiones: se entra sin reservas y se sale tarde.

## c) Cadena de herramientas

Episodios con mesa: 96 de 114 (84,2 %).

| Herramienta | Fabricada tras la mesa | Latidos desde la mesa: mediana (p25-p75) |
|---|---|---|
| pico de madera | 71 de 96 (74,0 %) | 12 (4-36) |
| espada de madera | 45 de 96 (46,9 %) | 26 (9-58) |

### Sin pico tras la mesa (25 episodios, 3392 latidos desde la mesa)

- **Madera:** 29,7 % de los latidos tiene madera ≥ 1. Solo el **0,7 %** tiene a la vez madera y una mesa en el 3 × 3: tiene la madera cuando la mesa queda lejos.
- **Qué gana** (latidos desde la mesa):
  - huir de zombi, 27,4 %;
  - sobresalto, 11,9 %;
  - `metas: make_wood_pickaxe`, 9,9 %;
  - explorar, 7,4 %;
  - acercarse al agua, 6,4 %;
  - sin candidatos, 5,0 %;
  - huir de flecha, 4,4 %, y de esqueleto, 4,0 %.
- **La mejor propuesta de `PerseguirMetas`** (gane o no) es `make_wood_pickaxe` en el 58,5 % de los latidos. Con huir y el sobresalto ganando el 39 %, rara vez gana.
- **En qué se gasta la madera** (USAR con éxito tras la primera mesa):

| Objetivo · motivo | Veces |
|---|---|
| `place_table` · `metas: place_table` | 23 |
| `place_table` · `metas: make_wood_pickaxe` | 22 |
| `place_table` · `proteger: pide stone` | 7 |
| `place_table` · `proteger: pide wood_pickaxe` | 5 |
| `make_wood_pickaxe` | 1 |

Se colocan 57 mesas nuevas. Hay 1 USAR de `make_wood_pickaxe` marcado con éxito sin que aparezca el logro; no lo he investigado. Para conseguir el pico, el planificador prefiere colocar otra mesa a volver a la que conoce, y cada mesa consume madera.

### Sin espada tras la mesa (51 episodios, 8984 latidos desde la mesa)

- **Madera:** 25,5 % de los latidos tiene madera ≥ 1; solo el 2,0 % tiene a la vez madera y una mesa en el 3 × 3.
- **Qué gana:**
  - huir de zombi, 19,1 %;
  - sin candidatos, 11,1 %;
  - sobresalto, 8,7 %;
  - huir de esqueleto, 7,6 %;
  - explorar, 7,5 %;
  - `metas: make_wood_pickaxe`, 6,8 %.
- **La mejor propuesta de `PerseguirMetas`** es la espada solo en el 8,6 % de los latidos. Delante van:
  - el pico, 30,1 %;
  - hierba, 12,6 %;
  - el horno, 9,4 %;
  - piedra, 6,4 %;
  - vaca, 6,4 %;
  - carbón, 6,1 %.

  La espada no es una meta prioritaria del planificador, aunque huir sea lo que más gana.
- **En qué se gasta la madera:**
  - 87 mesas nuevas: 47 con `metas: place_table`, 33 con `metas: make_wood_pickaxe` y 7 con `metas: make_wood_sword`;
  - 26 hornos;
  - 30 picos.

## Resumen

1. **Encontrar sitio** es el cuello de botella de la primera noche: el 59 % de los episodios llega a lo oscuro sin sitio ni nada que pedir. Solo el 25 % tiene sitio y no lo completa, y las causas de ese 25 % se reparten entre material, herramienta y tiempo.
2. **Lo construido no se reutiliza:** se colocan mesas nuevas en vez de volver a la conocida. Eso gasta la madera de las herramientas y hace raro tener madera y mesa a la vez (0,7-2 % de los latidos).
3. **La espada no llega:** el planificador no la prioriza, y sin ella huir domina la conducta tras la mesa.
4. **Pasar la noche dentro no basta:** se sale con comida y bebida en 2 de 9 y 8 de 14 mueren de sed o de hambre. 3b, que buscaba esto, no tuvo efecto medido.

## Propuestas (sin implementar), ordenadas por impacto esperado

Ninguna pone nombres de Crafter en `ida/core` ni en `ida/sistemas`.

1. **Buscar sitio como meta instrumental de información.**
   - **Qué:** cuando `Recinto` no tiene sitio ni requisitos y el cobijo anticipado sube, `Proteger` pide explorar. No pide un objeto, sino ver casillas de alguna clase que abriría espacio o cerraría un acceso: las que el modelo ya conoce por sus transformaciones o por los requisitos de la memoria. El planificador o la exploración lo atienden con la urgencia del cobijo.
   - **Por qué:** es la búsqueda de refugio dirigida por una necesidad anticipada, sobre el mapa cognitivo.
   - **Impacto esperado:** ataca el 59 % de las primeras noches.
   - **Antes:** verificar la hipótesis de que falta roca en el mapa local, registrando las clases del mapa en el primer latido oscuro.
2. **Reutilizar lo construido: los requisitos «cerca de X» se satisfacen con lo que recuerda el mapa local.**
   - **Qué:** el planificador compara el coste de ir a la X conocida (ruta en el mapa local) con el de producir otra. Una meta de «colocar X» ya conseguida no se repite mientras haya una X recordada y alcanzable.
   - **Impacto esperado:** devuelve a las herramientas la madera de las 57 a 87 mesas repetidas. Hace más frecuente tener madera y mesa a la vez: el pico, y con él cavar sitios, que está en 13 de los 14 episodios que pasan la noche.
3. **Que la Seguridad también pida metas instrumentales.**
   - **Qué:** el impulso de peligro, como el cobijo, pide al planificador lo que la memoria asocia con reducir el daño. Un objeto que es requisito de una acción contra lo peligroso (`Efecto.causa` y los requisitos del manual) tendría la urgencia del peligro aprendido. Encaja con el paso 6 (peligro graduado por el daño aprendido).
   - **Impacto esperado:** la espada (47 % tras la mesa) y la lucha en lugar de la huida, que gana entre el 19 % y el 27 % de los latidos tras la mesa. Es lo que perdió L2 al borrar `RefugioNocturno`.

---

# Segunda ronda (21/11/2026)

## Correcciones al diagnóstico anterior

1. **USAR «con éxito» no es colocar.** En Crafter, un USAR cuenta como éxito si la receta existe, aunque no haga nada. Las tablas de USAR de la sección c contaban intentos, no mesas colocadas; las 57 y 87 «mesas nuevas» eran intentos. La herramienta cuenta ahora solo los USAR que cambian el inventario.
   - **Antes de la ronda:** 1,73 mesas por episodio (media, 113 episodios), y 59 episodios con 2 o más.
   - La conclusión de que se repetían mesas se mantiene, con cifras menores.
2. **Lanzar las semillas una tras otra.** El Core corta un latido que pasa de `Perfil.frecuencia_ms` (100 ms) en tiempo de reloj: es la guillotina.
   - **Lo que se vio:** con 3 o 4 procesos a la vez, la misma semilla dio vidas distintas. Por ejemplo, el episodio 4 de la semilla 32 duró 247 latidos en una corrida y 501 en otra.
   - **Comprobación:** una tras otra, las corridas coinciden (semillas de hash 0 y 2: 273 y 327 latidos en los dos primeros episodios).
   - **Consecuencia:** las tablas de la primera ronda, lanzadas en paralelo, tienen ese ruido.
   - **A partir de aquí:** todo se ha lanzado en serie y el resumen cuenta los latidos cortados (0 en todas las corridas de esta ronda).
   - **Datos:** `datos/diagnostico/paso3_antes_semilla3{1,2,3}.json`. Es el código de `04a6417`, con la herramienta nueva, que no cambia la conducta.

## Punto 2: por qué «no encuentra sitio»

**Datos** (después del punto 1, `b452ec4`): `datos/diagnostico/paso3_p1_semilla3{1,2,3}.json`. Son 62 episodios que no encuentran sitio, de 113.

En el primer latido oscuro, la casilla conocida más cercana de una clase que se puede cavar (según `Modelo.abre`) está así:

| Caso | Episodios | Distancia Manhattan (mediana) |
|---|---|---|
| nunca vista | 13 (21,0 %) | — |
| vista pero fuera del alcance (15 pasos) | 0 (0,0 %) | — |
| dentro del alcance, pero descartada | 49 (79,0 %) | 3 |

**Por qué se descarta** (49 episodios):
- en 31, ninguna forma tiene material para cerrar sus accesos;
- en 7, algún acceso es de una clase que no se sabe cerrar;
- en 6, falta el pico para cavar;
- en 5, hay candidatos y ninguno se completa.

Las clases que el modelo da por cavables son sobre todo `arbol` (49 episodios) y `piedra` (17).

**Lo que de verdad falla dentro de `Recinto`**, con el material contado por su coste:

```bash
python herramientas/diagnostico_sitio.py --pasos 3000 --semilla 31   # y 32, 33, una tras otra
```

Cuenta los latidos con luz < 0,5 en que `_requisitos` no devuelve nada:

| Razón | Semilla 31 | Semilla 32 | Semilla 33 | Total |
|---|---|---|---|---|
| hay candidatos y el plan exacto no cierra ninguno de los 6 más baratos | 60 | 68 | 74 | 202 |
| el planificador no sabe conseguir el material de ningún cierre | 36 | 52 | 42 | 130 |
| la memoria no conoce ninguna acción que cierre | 0 | 35 | 0 | 35 |
| sin candidatos ni contando el material | 0 | 0 | 2 | 2 |

**Forma de los candidatos que no se completan** (interior, cavar, accesos, cierres sin material):
- (1, 0, 2, 2) es la más frecuente en las tres semillas: 169, 89 y 106 veces;
- después vienen otras de 1 casilla con 1 a 3 accesos.

**Causa:** con el modelo del cuerpo aprendido, moverse hacia una casilla libre hace avanzar. Desde una sola casilla interior no se puede quedar mirando a un acceso libre sin salir por él, así que esos sitios no se pueden cerrar. La estimación de `candidatos`, sin orientación, los pone primero por baratos. Como solo se planifican con exactitud los `CANDIDATOS_EXACTOS` (6) más baratos, a menudo fallan los 6 y no se mira más abajo, donde están los de 2 casillas.

**Decisión:** no domina «nunca vista» (21 %) ni «vista pero lejos» (0 %), así que no se implementa ninguna de las dos ramas del encargo (explorar en busca de sitio, o buscar fuera del alcance). Quedan como propuestas, sin implementar:
- **Seguir bajando por la lista de candidatos** hasta encontrar uno que el plan exacto cierre, con un tope de búsquedas por evaluación. Los fallos ya quedan en la caché de planes (`Recinto._planes`). Es general: no supone nada del mundo, solo no confiar en la estimación sin orientación cuando falla.
- **Usar el mapa local para conseguir material** en `PerseguirMetas.conseguir`. Hoy el planificador solo va a lo visible o a lo que recuerda la memoria topológica; `ir_por_el_mapa`, del punto 1, solo se usa para los requisitos de cercanía. Es la segunda razón: 130 latidos.
