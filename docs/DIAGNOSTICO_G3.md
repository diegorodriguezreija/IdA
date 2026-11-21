# Diagnóstico de la pérdida de G3 frente a `main` (retoño, esqueleto, sueño)

Fecha: 20/11/2026. Rama `feature/cierre-paso0`.

Son diagnósticos de pocas vidas, no mediciones. Las tasas oficiales están en `docs/MEDICION_PASO5_PASO0.md`.

## Protocolo

- Herramienta: `herramientas/diagnostico_logros.py`.
- Condiciones de G3: vista oficial, sin herencia, con estrategias, manual estricto.
- Presupuesto: 3000 pasos por semilla; semillas base 31, 32 y 33.
- `main` es un worktree de `origin/main` (088052c), con el mismo código en `ida/` que 8604414, el commit de la referencia oficial.
- G3 es `a99281d`, antes del arreglo.

```
python herramientas/diagnostico_logros.py --pasos 3000 --semilla 31 --manual estricto --salida g3_31.json
python herramientas/diagnostico_logros.py --raiz <worktree de main> --pasos 3000 --semilla 31 --salida main_31.json
```

| Semillas 31-33 (9000 pasos por rama) | `main` | G3 |
|---|---|---|
| Episodios | 24 | 27 |
| `collect_sapling` | 24 | 16 |
| `defeat_skeleton` | 7 | 1 |
| `wake_up` | 16 | 11 |

## collect_sapling y place_plant (oficial: 98,56 % → 44,01 % y 98,56 % → 42,25 %)

**Hipótesis confirmada.**
- En Crafter, coger hierba da un retoño con probabilidad 0,1 (`data.yaml` de crafter: `grass: {receive: {sapling: 1}, probability: 0.1}`).
- El paso 5 bloquea una acción con 3 fallos seguidos y ningún éxito (`Memoria.bloqueada`). Solo la desbloquea ganar un tipo de objeto nuevo.
- Probabilidad de bloquear antes del primer éxito: 0,9³ = 0,729.

Semilla 31:
- **G3:**
  - 5 de 9 episodios terminan sin retoño, con 3, 11, 11, 9 y 5 intentos, todos fallidos.
  - La acción está bloqueada 239, 66, 82, 42 y 25 latidos.
  - Los desbloqueos llegan al ganar objetos nuevos, y tras 3 fallos más se vuelve a bloquear.
- **`main`:**
  - `PlanTecnologico._oportunidades` prueba cada casilla de hierba hasta 6 veces, así que no tiene tope.
  - Consigue el retoño en 10 de 10 episodios, con 0 a 35 fallos antes del éxito (media 11,4).

`place_plant` sigue a `collect_sapling`: en G3, los 4 episodios con retoño también plantan.

**Arreglo** (commit `d744b39`): una acción cuyo efecto puede salir no se bloquea, y su coste en el planificador crece con los fallos (1/tasa − 1).

Prueba de humo, semilla 31, 3000 pasos:

| | Antes (`a99281d`) | Después (`d744b39`) |
|---|---|---|
| Suelo: `collect_sapling` | 61,54 % (8/13) | 76,92 % (10/13) |
| Suelo: Score | 7,71 % | 8,98 % |
| Con estrategias: `collect_sapling` | 4/9 | 5/10 |
| Con estrategias: Score | 13,83 % | 13,92 % |

Con estrategias ya no hay ningún latido bloqueado, pero 3 episodios hacen 10, 11 y 14 intentos sin éxito.

Lo que queda es arbitraje. En esos episodios, coger hierba está entre las 3 mejores propuestas en 158 latidos y no gana:
- `PerseguirMetas` propone con total 0,5;
- pierde sobre todo contra `RefugioNocturno` («ir a la mina elegida», 0,90-0,93) y empata con «ir a por madera» (0,496).

Es la deuda 2 de `DEUDA_TECNICA_CRAFTER.md` y la sección a de `PROPUESTA_PASO0.md`, y corresponde al paso 3.

## defeat_skeleton (oficial: 43,17 % → 7,39 %)

**Causa:** el peligro sin gradaciones del paso 2.
- El adaptador da `peligro` = `PELIGRO_MANUAL` = 0,8 a todo lo que el manual declara PELIGROSO, flecha incluida (P06).
- `main` graduaba: zombi 0,8, esqueleto 0,7, flecha 0,5 y lava 1,0 (`HOSTILES`).
- La flecha, que se acerca rápido, pasa a ser la amenaza principal, y Huir gana.

| Semillas 31-33 | `main` | G3 | G3 con el peligro de `main` (contrafactual) |
|---|---|---|---|
| Latidos con esqueleto a la vista | 2940 | 2474 | 2245 |
| Gana «huir de flecha» (latidos) | 1 | 293 | 49 |
| «huir de flecha» entre las 3 mejores | 7 | 370 | — |
| Gana «acortar distancia a esqueleto» (`CerrarDistancia`) | 37 | 9 | 28 |
| ATACAR esqueleto | 14 | 4 | 22 |
| `defeat_skeleton` (episodios) | 7/24 | 1/27 | 6/29 |
| Score por semilla | 14,36 · 17,68 · 17,83 | 13,83 · 14,54 · 12,23 | 13,50 · 13,41 · 13,88 |

El contrafactual se hizo en un worktree aparte y no está en la rama. Usa en `observar` (entidades y casillas) los valores de `HOSTILES` de `main`.
- Recupera `defeat_skeleton`.
- No sube el Score en estas tres vidas.

Graduar el peligro desde el adaptador sería conocimiento del mundo que el paso 2 quitó. Ninguna fuente citada da gradaciones (`crafter.py`, comentario de `PELIGRO_MANUAL`). **No se arregla aquí.** Opciones para decidir:
- un peligro aprendido por el daño recibido de cada clase;
- la proximidad y la trayectoria de la flecha como percepción.

## wake_up (oficial: 51,44 % → 38,73 %)

**La hipótesis «es la pérdida de dormir de día» no se confirma en estas vidas.**
- En `main`, la propuesta «plan: dormir de día» (`PlanTecnologico._oportunidades`) está entre las 3 mejores en 16 de 9000 latidos y gana 1.
- Todos los demás sueños de `main` los decide `RefugioNocturno` («refugio: dormir a salvo»), que también existe en G3.
- G3 duerme con luz ≥ 0,5 más latidos que `main`: 350 frente a 247.

La diferencia está en llegar al refugio antes de que anochezca:

| Semillas 31-33 | `main` | G3 |
|---|---|---|
| Episodios que llegan al anochecer (luz < 0,3 tras el latido 50) | 20 | 26 |
| De ellos, en camino de galería (`path`) al anochecer | 15 | 9 |
| Llegan al anochecer, no duermen nunca y mueren (todos por zombi) | 4 | 8 |
| `wake_up` | 16/24 | 11/27 |

Semilla 31:
- **`main`:** está en una galería al anochecer en los 7 episodios que llegan, y duerme como mucho 13 latidos después (en el episodio 9, antes de anochecer).
- **G3:** al anochecer está en hierba o arena en 5 de 8.
  - Los episodios 1, 2 y 6 mueren por zombi esa noche (latidos 262-275) sin haber dormido.
  - En los 40 latidos previos ganan «huir de lava» (22 en el episodio 1) y «huir de flecha» (12 y 19 en los episodios 1 y 2), o `RefugioNocturno` sigue buscando veta («inspeccionar veta de roca»).

La huida de flechas y de lava es el mismo peligro sin gradar del apartado anterior, aunque no está aislado como causa de `wake_up`. En el contrafactual, `wake_up` queda igual (11/29), así que el peligro graduado no lo explica.

No se arregla aquí.
