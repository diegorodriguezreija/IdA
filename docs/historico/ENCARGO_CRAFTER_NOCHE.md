# Encargo: Crafter, estrategia de refugio nocturno (madriguera)

Este encargo pertenece a la **fase de mejora de los mundos** (`AGENTS.md`). Léelo entero antes de tocar nada.

Tiene tres fases:
- **Fase 0:** sin código. Al terminarla se espera la revisión del autor.
- **Fase A:** que la estrategia sepa hacer el refugio.
- **Fase B:** que la elija a tiempo compitiendo con el resto de impulsos.

No se pasa de una fase a la siguiente sin la revisión del autor.

## 1. Situación y objetivo

En Crafter, la primera causa de muerte es el zombi de noche: entre 15 y 22 de cada 30 vidas por grupo (`docs/REFERENCIA_BASE.md`, «Muertes por causa»). El objetivo es que el individuo pase las noches a salvo **sin empeorar el resto de su vida**: logros, alimentación, sed y progreso.

Ya hubo un intento (rama `feature/crafter-nido`) que salió mal; está resumido en la sección 7. **No partas de esa rama.**

## 2. La receta (probada por el autor jugando a mano, 6 partidas)

La forma más fiable de superar la primera noche fue esta:

1. Coger 3 maderas, colocar la mesa (2 maderas) y fabricar el pico de madera (1 madera).
2. Beber y comer hasta llenar.
3. Buscar una mina de piedra lo bastante grande, picar 3 casillas en línea recta, retroceder una casilla (así se queda mirando a la salida) y tapar la entrada con una piedra.
4. Dormir. A la mañana siguiente suele quedar algún monstruo cerca que hay que matar.
5. Repetir cada día: beber y comer, y volver a una mina (puede ser la misma) para encerrarse otra vez.

Mejoras del autor sobre la receta:

- **La elección de la mina es clave.** Se valora que los lados sean roca, que tenga profundidad para 3 casillas y que esté **cerca de agua**, para beber fácilmente antes de entrar y al salir. La comida depende más del azar.
- **Una madera más para la espada de madera** (4 en total). Por la mañana, un zombi (5 de vida) cae en 3 golpes en lugar de 5, y además se recupera el logro `make_wood_sword`.

## 3. Mecánica de Crafter que condiciona el diseño

Fuente: Crafter 1.8.3, `danijar/crafter`, commit `e04542a`. Compruébalo en el paquete instalado y corrige este apartado si difiere.

- **Recetas** (`data.yaml`):
  - Mesa: 2 maderas. Pico de madera: 1. Espada de madera: 1. Ambos se fabrican junto a la mesa.
  - Piedra: se obtiene con el pico de madera y la casilla picada queda como camino.
  - **Talar un árbol lo convierte en hierba** (`collect: tree … leaves: grass`): cada madera sale de un árbol distinto.
  - El inventario admite como máximo 9 de cada material.
- **Zombis** (`objects.py`, `Zombie.update`):
  - Atacan a distancia Manhattan ≤ 1 (`distance` suma las diferencias de coordenadas). **Solo cuentan los 4 vecinos en cruz; las diagonales no.**
  - Hacen 7 de daño si el jugador duerme y 2 si está despierto.
  - Solo andan por hierba, arena o camino (`walkable`).
  - Aparecen sobre hierba a ≥ 6 casillas del jugador, y más cuanta menos luz (`env.py`, `_balance_chunk`).
- **Orientación** (`objects.py`, `_move` y `_place`):
  - Solo se coloca piedra en la casilla a la que se mira.
  - Intentar moverse hacia una casilla bloqueada (roca, agua, árbol) gira al jugador sin desplazarlo.
  - Intentar moverse hacia una casilla libre lo desplaza.

  Por eso hace falta retroceder para quedar mirando a la salida. Una consecuencia útil: **el agua puede servir de pared y se puede beber desde dentro del refugio**, mirándola.
- **Ciclo de luz** (`env.py`, `_update_time`):
  - El día dura 300 pasos. La luz baja de 0,83 hacia el paso 116, que es cuando los zombis empiezan a aparecer de forma sostenida.
  - Hacia el paso 150 queda la mitad de la luz, la oscuridad máxima llega hacia el 210 y amanece hacia el 300.
  - Comprueba si en IdA un latido equivale a un paso de Crafter.
- **Riesgos al cavar:**
  - Los esqueletos aparecen sobre casillas de camino, y lo excavado también cuenta como camino.
  - Las flechas atraviesan agua y lava, pero no la piedra.
  - Pisar lava mata.

**Condición de un buen refugio:** que las casillas en cruz alrededor del hueco excavado no sean transitables para un zombi. Las diagonales no hacen falta. La rama anterior exigía 8 vecinos de roca y casi nunca encontraba sitio.

## 4. Diseño pedido

Es **una estrategia propia del mundo** (`Mundo.estrategias_propias`): una máquina de estados con fases, cada una disparada por lo que se percibe (regla 4). **No es una secuencia cableada.** Las fases son estas, en el orden en que suelen ocurrir:

1. **Madera** (hasta 4).
2. **Mesa y herramientas** (pico, espada).
3. **Provisiones:** beber y comer hasta llenar antes de que caiga la luz.
4. **Elegir mina:** se valora con lo percibido o recordado:
   - laterales no transitables (roca, agua o árbol);
   - profundidad para 3 casillas;
   - cercanía al agua;
   - distancia actual;
   - que no haya lava a la vista ni túnel oscuro.
5. **Cavar:** picar 3 casillas en línea recta.
6. **Cerrarse:** retroceder una casilla y tapar la entrada.
7. **Dormir.**
8. **Amanecer:** picar la salida (se recupera esa piedra), defenderse o huir de lo que quede, beber y comer.

**Memoria del refugio:** recordar la mina usada y preferir volver a ella al día siguiente si está a mano. Es fidelidad al sitio; se apoya en el hogar que ya existe (`Perfil.hogar = True`, `memoria.hogar()`).

**Motivación.** La necesidad de refugiarse debe crecer de forma continua conforme baja la luz y aumenta la distancia a la mina elegida. **No** puede depender de un umbral que corte, ni de un número de paso fijo. Usa lo que permite la fase de mundos: necesidades o intenciones del `Perfil`, rasgos y percepción. En la fase 0, explica cómo se expresa esa intensidad con la base actual. Si no se puede sin tocar `ida/core/` o `ida/sistemas/`, dilo y propón una alternativa; **no toques la base**.

**Coherencia (contra el vaivén):**
- Una vez elegida, la mina se guarda en el estado de la estrategia (`paso`, decisión 17) y se mantiene mientras la distancia baje.
- La mina solo se abandona por evidencia: N latidos sin avance, peligro en el camino o descubrir que no cumple la condición del refugio.
- Mientras se busca, mantener el rumbo; no volver a elegir destino en cada latido.

## 5. Lectura obligatoria

- `AGENTS.md` («Fase de mejora de los mundos» y reglas 3, 4, 6 y 7). **No se toca `ida/core/` ni `ida/sistemas/`.**
- `docs/REDISENO_BASE.md`, decisiones 3, 4, 6, 16, 17 y 23.
- `ida/core/estrategia.py` (`Definicion`, `Plan`, `avanzar`).
- `ida/sistemas/comun.py`, clase `Estrategia`: elección, histéresis `MARGEN_SUSTITUCION = 0,2`, cierre y enfriamiento.
- `ida/core/sentidos.py`, clase `Tribunal`:
  - puntuación = `arousal·estrés + confianza·(1 − estrés)` + experiencia;
  - plus de continuidad = `0,1 × (1 − agotamiento) × (1 − progreso)`;
  - si las dos mejores quedan a menos de 0,02, decide el azar.
- `ida/sistemas/s1.py` (`Huir`, `Alimentarse`), `ida/sistemas/s2.py` (`Explorar`, `Refugiarse`) e `ida/mundos/crafter.py` (`estrategias_propias`, `PlanTecnologico`, `DefensaArmada`, `_terreno`, `_luz`).
- `docs/REFERENCIA_BASE.md` y `docs/BENCHMARK_PERFILES_MUNDOS.md`.

## 6. Fases y criterios

### Fase 0 (sin código; se entrega y se espera la revisión)

- Un mapa con referencias a fichero y línea: cómo una necesidad de Crafter se convierte en acción (impulso → estrategia → propuesta → Tribunal).
- Qué percibe hoy el individuo de Crafter (terreno, luz, inventario). Qué falta percibir para evaluar una mina, y cómo añadirlo sin que el sensor piense por el individuo (regla 3).
- Cómo se expresará la motivación del refugio (sección 4).
- Qué estrategias compiten de noche, con las puntuaciones de 2 o 3 latidos reales (`onda.notas["evaluados"]`), y dónde está hoy el vaivén.
- Los pasos de implementación, cada uno con la hipótesis que pone a prueba.

### Fase A: competencia (saber hacer el refugio)

- Se prueba la estrategia con su motivación dominante, mediante un arnés de prueba en `herramientas/` o en los tests (**nunca en el `Perfil` que se fusiona**), para medir solo si sabe ejecutarla.
- Semillas 11 a 30, 1 vida, 600 latidos.
- **Métricas:**
  - porcentaje de vidas selladas;
  - latido y nivel de luz en el momento de sellar;
  - porcentaje que pasa la noche sin daño dentro y `wake_up`;
  - causa de cada fallo: sin árboles, sin roca adecuada, interrumpida por un zombi, lava, error de orientación o tiempo.
- **Criterio para pasar a la fase B:** ≥ 70 % de las vidas selladas antes de que la luz baje de 0,5, y ≥ 80 % de las selladas sin daño durante la noche. El autor puede ajustar estas cifras a la vista de la fase 0.

### Fase B: integración (elegirla a tiempo)

- La estrategia compite con su motivación real.
- Después de cada paso:
  - `pytest`, `ruff` y `mypy`;
  - benchmark rápido (`--grupos Equilibrado`);
  - si no empeora, benchmark completo de los cuatro grupos frente a `docs/REFERENCIA_BASE.md`.
- **Criterio de éxito.** Es el único que decide; las métricas de diagnóstico solo lo explican.
  1. Suben los latidos de vida o bajan las muertes por zombi, en al menos dos grupos.
  2. En ningún grupo el límite inferior del IC 95 % de Δ logros queda por debajo de −1,0.
  3. Ningún grupo empeora de forma significativa (IC entero por debajo de 0) en latidos ni en fitness.
- **Regla de parada:** el paso que empeore de forma significativa cualquier grupo se revierte (`git revert`) y se anota como resultado negativo.
- Un cambio por hipótesis. Ajustar con las semillas 11 a 30; las semillas 1 a 10 quedan para el benchmark.

## 7. Lecciones del intento anterior (`feature/crafter-nido`)

- El diagnóstico mejoró: las oscilaciones bajaron de 44 a 25 y la piedra subió de 2,3 a 5,0. Pero el benchmark empeoró:
  - los logros bajaron entre −2,1 y −2,6 de forma significativa en Equilibrado, Valiente y Reactivo;
  - la supervivencia bajó en Reactivo (−62,8 ± 39,6 latidos).
- **La madriguera no cumplió su objetivo:**
  - las vidas que llegan a dormir bajaron del 70 % al 40 %;
  - `wake_up` pasó de 95 a 69 vidas;
  - las muertes por zombi no bajaron;
  - aparecieron muertes en «preparar_nido».

  Causa probable: exigir 8 vecinos de roca.
- **Se perdieron logros baratos:** `make_wood_sword` pasó de 71 vidas a 0, `place_plant` perdió 64, `collect_sapling` 41 y `place_furnace` 35.
- **Errores de método:**
  - se ajustó y se evaluó con las mismas semillas;
  - el benchmark solo se hizo al final, no paso a paso;
  - el paso 2.d no tuvo efecto medible y no se investigó;
  - la comprobación de pureza se hizo contra la propia rama remota, no contra `main`.
- **Se puede reutilizar, revisándolo antes:** `herramientas/diagnostico_crafter.py` (commit `59d5ee4`) y las ampliaciones de `herramientas/benchmark.py` (logros por tipo, muertes por causa, noches). Si se traen, que sea en commits propios al principio de la rama nueva.

## 8. Fuera de alcance

- `ida/core/` e `ida/sistemas/`. Si algo los necesita, se anota como pendiente con datos.
- Activar los mecanismos de memoria E y F en el `Perfil` de Crafter.
- Otros mundos y cambios en el protocolo del benchmark o en la referencia.
- Construir el refugio en campo abierto (posible iteración futura).

## 9. Entrega de cada fase

1. **Resultado primero.** Si no se cumple el criterio, el titular lo dice así.
2. **Tabla por paso:** hipótesis, diagnóstico (semillas 11 a 30), benchmark (semillas 1 a 10, solo en la fase B) y decisión (se mantiene o se revierte).
3. **En la fase B:**
   - muertes por causa y logros por tipo, base frente a nueva;
   - para cada logro que empeore, una explicación comprobada.
4. **Verificación de la base, con la salida literal:**
   ```bash
   git diff --stat main...HEAD -- ida/core ida/sistemas
   python -m pytest -q && ruff check ida tests herramientas && mypy ida
   ```
5. **Lo no verificado, marcado como tal.** Sin lenguaje enfático. Rama nueva desde `main`, un commit por cambio y sin `push`.
