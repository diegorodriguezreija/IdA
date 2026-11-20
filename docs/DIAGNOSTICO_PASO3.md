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
