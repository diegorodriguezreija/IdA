# Fase 5 — Ciclo diurno, cobijo y dotación innata

Documento de trabajo para el agente implementador. Complementa a `PLAN_EVOLUCION.md` (fases 1 a 4) y se lee junto a `AGENTS.md`. Las reglas de ambos siguen vigentes salvo lo que este documento autoriza de forma expresa en la sección 2.

Fecha: 2026-11-12. Base: `feature/ajustes-cognitivos` (`25e1303`).

Revisión 2 (2026-11-12): incorpora las dudas del implementador sobre la orientación al colocar piedra y sobre el canal de meta entre `Anidar` y `PlanTecnologico`. Cambian §1.4, §4.3, §4.4, §5 y §7 (ver §1.5).

---

## 1. Contexto y justificación del diseño

Esta sección resume la conversación entre el autor y el revisor que dio lugar a la fase. Se incluye para que el implementador entienda **por qué** el diseño es así y no proponga atajos que el autor ya descartó.

### 1.1 Datos de partida

- `docs/BENCHMARK_PERFILES_MUNDOS.md` (N = 10 linajes): en Crafter, el **100 % de las muertes registradas (120/120)** se deben a hostiles nocturnos o combate. Ninguna por hambre o sed.
- La experiencia no reduce esas muertes: `DefensaCrafter` actúa sobre el estado somático y la escena actual, sin usar lo aprendido.
- Las fases 1 a 4 no produjeron diferencias detectables en conducta. El mayor efecto medido es el del **carácter** (Reactivo frente a Equilibrado en Mínimo, con intervalos sin solapamiento), y su óptimo cambia según el mundo.

### 1.2 Observación cualitativa del autor (Crafter, en vivo)

1. De día, el individuo apenas se mueve: va y viene entre dos casillas sin sentido aparente y solo se desplaza cuando tiene hambre o sed. Después vuelve a ese patrón.
2. No distingue momentos del día. Un animal complejo explora de día, cuando está tranquilo, y al acercarse la noche sube su alerta, reduce el movimiento y busca protección.
3. No prepara un refugio, ni natural ni construido, aunque el primer día da tiempo de sobra para conseguir madera, una mesa, un pico y piedra, y cerrarse antes de que oscurezca.
4. Los animales complejos no empiezan de cero: nacen con predisposiciones fruto de la selección acumulada de sus antepasados.

### 1.3 Propuesta inicial descartada y por qué

El autor propuso una "estrategia ancestral" en cuatro pasos para cuando el individuo esté en calma y sin refugio: talar 3 maderas, fabricar mesa y pico, minar 6-8 piedras y cerrarse al caer la tarde.

Se descarta como mecanismo, y el autor está de acuerdo, por dos motivos:

- **Incumple la regla 4 de `AGENTS.md`**, que prohíbe las "secuencias de acciones cableadas para un fin específico". IdA mejoraría en Crafter y perdería lo que le diferencia de un bot.
- **No es así como funcionan los instintos.** Los genes no guardan recetas con cantidades. Guardan **predisposiciones**: valoraciones innatas (miedo a ciertos agentes, preferencia por lugares cerrados al descansar, como la tigmotaxis de los roedores), **ritmos internos** (el reloj circadiano) e **impulsos activados por estímulos** (el impulso de anidar se activa por el estado interno y las señales del entorno, y cada parte de la construcción se dispara por lo que el animal tiene delante).

La estrategia de cuatro pasos se conserva solo como **referencia de lo que debería emerger**, no como especificación.

### 1.4 Traducción a mecanismos (decisión adoptada)

| Observación del autor | Mecanismo | Dónde vive | Principio biológico |
|---|---|---|---|
| No sabe qué momento del día es | Percepción de la luz | Adaptador del mundo | El animal ve que oscurece |
| No cambia de conducta entre el día y la noche | Ritmo circadiano en `Soma` que modula alerta y curiosidad | Core (genérico) | Reloj circadiano: actividad diurna, anticipación del crepúsculo |
| No busca protección | Rasgo percibido `cobijo` (cierre del recinto inmediato) y búsqueda de refugio en `Hogar` usando el mapa de la fase 1 | Rasgo: vocabulario del Core, calculado por el adaptador. Búsqueda: S2 | Tigmotaxis, selección de madriguera |
| No construye refugio | Impulso de anidar en S2: emite una meta de cobijo que `PlanTecnologico` (S3) resuelve con la cadena de recetas existente; se orienta hacia los huecos moviéndose dentro del recinto | Componentes propios de Crafter | Construcción del nido activada por estímulos; acomodarse en el nido (el perro que da vueltas antes de tumbarse) |
| Empieza de cero | Dotación innata como fuente de evidencia refutable | Contenido: adaptador. Mecanismo: Core (fuente `instinto` del modelo de la fase 3) | Reconocimiento innato de depredadores |

Con estos mecanismos, la secuencia madera → mesa → pico → piedra → cerrarse debería **emerger**: la meta "más cobijo" necesita piedra, la piedra necesita pico, el pico necesita mesa, y `PlanTecnologico` ya resuelve cadenas de recetas a partir de metas.

### 1.5 Revisión 2: orientación y canal de meta

**Orientación.** En `main`, `MundoCrafter.ejecutar()` resuelve `USAR` con `self._paso(receta)`, sin gestionar la orientación: la piedra se coloca en la casilla hacia la que mira el jugador (`facing`). `_interactuar()` sí gira antes de actuar, pero aprovecha que moverse hacia una casilla **bloqueada** solo gira (`# bloqueado por el objetivo: solo gira`). Hacia una casilla **libre**, el mismo movimiento desplaza al jugador.

Consecuencia (pendiente de verificar en el código de `crafter`, §7): el individuo no puede mirar la casilla por la que acaba de entrar sin volver a salir a ella. **Un refugio de una casilla no se puede cerrar desde dentro.** Uno de **dos casillas** sí: ir a la casilla interior y volver deja al individuo mirando hacia el hueco de entrada. Un recinto de dos casillas tiene 6 vecinas, muchas de ellas naturales si se aprovecha la roca, lo que cuadra con la estimación del autor de 6-8 piedras.

Decisiones derivadas:
- **No se añaden maniobras de varios pasos dentro de `ejecutar()`.** `_interactuar()` ya consume dos pasos del mundo (girar y actuar) en un latido; ese precedente no se amplía.
- **La orientación se expone como propiocepción** (adaptador), y el impulso de anidar decide con ella (§4.4). Moverse dentro del recinto para quedar frente a un hueco es acomodarse en el nido, no una secuencia fija.
- **El `cobijo` mide el cierre del recinto inmediato** (hasta 2 casillas), no la fracción de vecinas bloqueadas de una casilla, que nunca llega a 1 en un refugio de dos casillas (§4.3).

**Canal de meta.** `Anidar` (S2) emite una pieza de meta en la `Onda` que `PlanTecnologico` (S3) lee en el mismo latido, porque el latido ejecuta S1 → S2 → S3. Es el mismo patrón con el que ya se comunican los componentes (`Valor`, `Patron`, `Sentencia`). Así no se duplica la cadena de recetas (§4.4).

---

## 2. Autorización del autor

Se amplía la autorización de la sección 1 de `PLAN_EVOLUCION.md` a los cambios de esta fase en `ida/core/` e `ida/sistemas/`, con las mismas condiciones: un commit por cambio, invariancia con semilla en todo lo que no busca cambiar la conducta, mediciones antes y después, y nada de `push` sin permiso.

**Invariancia obligatoria en esta fase:** con `perfil.ciclo_diurno == False` y sin dotación innata, `minimo`, `archivos`, `snake` y `ajedrez` deben dar vidas idénticas con la misma semilla en todos los pasos.

---

## 3. Paso 0 — Diagnóstico del vaivén diurno (antes de implementar)

Antes de añadir mecanismos, explicar la observación 1.2.1 con datos.

- Reproducir el vaivén en Crafter, en las semillas donde el autor lo observó (si no constan, buscarlo en las semillas 1 a 10 con el perfil Equilibrado).
- Para los latidos del vaivén, registrar el ganador del Tribunal, su motivo, los dos mejores candidatos con sus puntuaciones y si decidió el azar por empate (`Tribunal.EMPATE`).
- Clasificar la causa:
  - **(a) Empate repetido** entre candidatos de `MOVER`, decidido por el azar.
  - **(b) Dos componentes que tiran en sentidos opuestos** (por ejemplo, `Hogar` frente a `Curiosidad` u `Orientacion`).
  - **(c) Ausencia de impulso** cuando las necesidades están cubiertas (novedad agotada o curiosidad demasiado débil).
  - **(d) Otra**, descrita.
- Entregar un informe breve con cifras, en un commit propio o en `docs/`.

Si la causa es (c), el ritmo circadiano del paso 2 es la corrección prevista. Si es (a), (b) o (d), se corrige aparte antes de seguir y se mide.

---

## 4. Diseño por pasos

### 4.1 Paso 1 — Percepción de la luz

- `Observacion` (`ida/core/mundo.py`) gana un campo opcional `luz: Optional[float]` en [0, 1]. `None` significa que el mundo no tiene ciclo diurno.
- `Perfil` gana `ciclo_diurno: bool = False`.
- `MundoCrafter.observar()` rellena `luz` con el nivel de luz del entorno, que ya usa internamente (`env._world.daylight`, `crafter.py:175` y `:359`), y activa `ciclo_diurno` en su perfil.
- `Soma` guarda `luz` y su **tendencia** (media móvil exponencial de la variación entre latidos).
- Lenguaje interno: una etiqueta legible derivada de la luz y su tendencia (`amanecer`, `día`, `atardecer`, `noche`), para la consola y el panel. La etiqueta es descriptiva: los mecanismos usan los valores continuos, no la etiqueta.

**Deuda que se paga en este paso.** Hay componentes de Crafter que leen el estado interno del entorno en vez de la percepción:
- `PlanTecnologico._oportunidades` decide dormir de día con `self.mundo.env._world.daylight` (`crafter.py:462`).
- `_cerca` y otros métodos consultan `env._world` directamente (`:435`, `:456`, `:467`).

Al menos la lectura de la luz debe pasar a usar `ctx.soma.luz`. El resto se documenta como deuda pendiente, con fichero y línea, sin ampliarla.

**Aceptación:** invariancia completa en los cinco mundos, porque nada consume todavía la luz salvo el cambio de `_oportunidades`. Si ese cambio altera la conducta de Crafter (no debería, porque el valor es el mismo), se explica.

### 4.2 Paso 2 — Ritmo circadiano en `Soma`

Modulación genérica del estado interno, activa solo con `perfil.ciclo_diurno`:

- **De día y en calma:** baja la alerta basal y sube la ganancia de la curiosidad (`Curiosidad` en S2 escala su arousal con un factor diurno expuesto por `Soma`). Es la respuesta prevista a la observación 1.2.1 si el paso 0 da la causa (c).
- **Al atardecer:** la alerta basal sube en función de la **tendencia negativa** de la luz, no solo de su nivel. Así la anticipación empieza antes de que oscurezca.
- **De noche:** se inhibe la exploración (la curiosidad baja) y crece una **necesidad de cobijo**, que se expone como valor en [0, 1] para que la consuman `Hogar` y el impulso de anidar.

Parámetros (ganancias y umbrales) en el `Perfil`, nunca constantes del Core ajustadas para Crafter (regla 2 de `AGENTS.md`).

**Extensión condicionada:** si la anticipación por tendencia resulta tardía (ver la métrica de antelación en la sección 5), sustituirla por un **oscilador endógeno sincronizado con la luz**: un reloj interno que estima el periodo a partir de los amaneceres observados y predice el crepúsculo antes de que la luz baje. Es lo que hace un reloj circadiano real. No se implementa si la tendencia basta.

### 4.3 Paso 3 — Rasgo `cobijo` y búsqueda de refugio

- Nuevo rasgo en `RASGOS` (`vocabulario.py`): `cobijo`, en [0, 1], que indica lo protegido que está un lugar.
- `MundoCrafter` lo calcula para la ubicación actual y para cada lugar percibido, como **cierre del recinto inmediato**:
  - El recinto de una casilla P es P más, como máximo, **una** casilla transitable adyacente (el movimiento en Crafter es en 4 direcciones, `MOVIMIENTOS` en `crafter.py:36`). Si P tiene más de una vecina transitable, el recinto es solo P.
  - `cobijo = 1 − (salidas abiertas del recinto) / (perímetro del recinto)`, donde el perímetro son las casillas vecinas del recinto que no forman parte de él (4 para una casilla, 6 para dos) y una salida abierta es una de ellas que es transitable.
  - `cobijo = 1` significa recinto cerrado: nada puede entrar caminando.
  - Es percepción del entorno inmediato, dentro del radio de visión (como ver que estás en un cuarto cerrado), no una búsqueda de planes, así que respeta la regla 3 de `AGENTS.md`. El recinto se limita a 2 casillas precisamente para que no se convierta en una búsqueda.
- El adaptador expone también, para el recinto actual, **qué casillas son huecos** (salidas abiertas). Es la información que usa el impulso de anidar (§4.4).
- `Memoria` recuerda el cobijo percibido de cada ubicación, junto al bienestar que ya guarda en `lugares`.
- `Hogar` (S2): cuando la necesidad de cobijo supera un umbral, el destino pasa a ser el lugar conocido que maximiza una combinación de bienestar y cobijo, y se llega a él con `Memoria.ruta()` (fase 1). Así puede usar un **refugio natural** si lo ha visto: un hueco en la roca, una esquina entre agua y piedra.
- Dentro de un lugar con cobijo alto y de noche, las propuestas de quedarse y dormir ganan peso. Encaja con el sueño existente: dormir a cubierto es seguro.
- **Invariancia:** en los mundos que no calculan `cobijo`, el rasgo vale 0 y no altera ninguna puntuación ni consume azar.

### 4.4 Paso 4 — Impulso de anidar (componente propio de Crafter)

Componente nuevo `Anidar` en `ida/mundos/crafter.py`, registrado en `componentes_propios()` en **`S2.Reaccionar`**: es un impulso homeostático (necesidad de cobijo), como `Hogar`.

**Propiocepción de la orientación (adaptador).** `MundoCrafter.observar()` expone hacia dónde mira el individuo y qué casilla tiene delante, como dato de la pieza propioceptiva o de la escena. Es percepción del propio cuerpo; no decide nada.

**Activación.**
- Hay necesidad de cobijo (§4.2) y el cobijo del recinto actual está por debajo de un umbral; **o**
- es de día, hay calma y no se conoce ningún refugio con cobijo alto. En ese caso la intensidad es baja y la modula la dotación innata (paso 5). Es la predisposición a "preparar el nido": un impulso, no un horario.

**Conducta, latido a latido, según lo que percibe:**
- **Tiene piedra y un hueco del recinto delante:** propone `USAR place_stone`, con arousal proporcional a la necesidad.
- **Tiene piedra y hay huecos, pero ninguno delante:** propone `MOVER` a la otra casilla del recinto, la que deja al individuo mirando un hueco al volver. Es acomodarse en el nido. El componente no guarda una secuencia: en cada latido elige con la orientación y los huecos que percibe en ese momento.
- **El recinto actual no puede cerrarse** (tiene más de dos casillas transitables conectadas, o no hay un recinto de dos casillas a mano): no propone nada aquí. La búsqueda de un lugar mejor la hace `Hogar` con el cobijo recordado y el mapa (§4.3). `Anidar` no busca lugares.
- **No tiene piedra:** emite una **meta de cobijo** (abajo) y no propone acciones.

**Canal de meta hacia `PlanTecnologico`:**
- `Anidar` emite una pieza `Meta` (por ejemplo, `{"recurso": "stone", "motivo": "cobijo"}`) con **arousal igual a la intensidad de la necesidad**.
- La emite con `percibir()`, que **consume presupuesto de atención**, no con `registrar()`: tener metas cuesta atención, y la guillotina puede cortarlas.
- `PlanTecnologico` (S3), en el mismo latido, lee el canal `Meta` y, si hay una, prioriza el recurso pedido, escalando el arousal de sus propuestas con la intensidad de la meta. Resuelve la cadena con su lógica actual de recetas (madera → mesa → pico → piedra). **La cadena no se escribe en `Anidar`.**
- La meta no persiste entre latidos: se recalcula cada latido a partir del estado del cuerpo. Sin necesidad no hay meta, y `PlanTecnologico` se comporta como hoy.
- `PlanTecnologico` sigue limitándose a **proponer**: decide el Tribunal.

**Salida al amanecer.** Con la necesidad de cobijo baja y las necesidades corporales o la curiosidad al alza, el individuo debe poder salir: minar una piedra del recinto con el pico, lo que además devuelve la piedra al inventario (a verificar, §7). La salida no la propone `Anidar`, sino los componentes que ya buscan comida, agua o novedad, al percibir la piedra como recurso que se puede recoger. Si no consigue salir, puede morir de hambre encerrado: se vigila en §5.

### 4.5 Paso 5 — Dotación innata

- Nuevo método opcional en `Mundo`: `dotacion_innata() -> Dict[str, Any]`, que por defecto devuelve `{}`.
- La dotación se aplica a **cada individuo al nacer, en todas las generaciones**, antes de `heredar()`. Es genética, no cultural: no depende del linaje ni del `legado()`.
- Con el modelo de la fase 3, entra como fuente de evidencia **`instinto`**: confianza moderada, sin estado DEMOSTRADA por sí sola, y refutable por la experiencia. `texto()` muestra el origen.
- **Contenido permitido:** solo valoraciones sobre clases (`Relacion`) y pesos de impulsos (por ejemplo, la intensidad diurna del impulso de anidar).
  - Ejemplo para Crafter: hipótesis innatas «zombi hace daño» y «esqueleto hace daño», como el reconocimiento innato de depredadores que tienen muchas especies.
- **Contenido prohibido:** verbos, secuencias, recetas, cantidades de recursos o referencias a pasos del mundo.
- El contenido concreto lo aporta el adaptador. El Core no conoce nombres de clases (`tests/test_pureza.py`).
- Nota para la Vía 4 (poblaciones): los pesos de los impulsos innatos son candidatos naturales a evolucionar por selección. No se convierten en rasgos del `Arquetipo` en esta fase, porque cambiaría la secuencia de `Azar` en `Arquetipo.nuevo`.

---

## 5. Medición e hipótesis registradas de antemano

**Protocolo:** el de `docs/BENCHMARK_PERFILES_MUNDOS.md`. N = 10 linajes independientes (semillas 1..10, directorio limpio por semilla), 3 generaciones en Crafter, máximo 600 latidos, perfiles Equilibrado y Valiente, IC al 95 % con la t de Student (t₀,₉₇₅,₉ = 2,262) y diferencias pareadas frente a la base (`25e1303`).

**Ablación por pasos**, para atribuir cada efecto a su mecanismo:

| Variante | Contenido |
|---|---|
| Base | `25e1303` |
| +P2 | Ritmo circadiano |
| +P3 | Ritmo y búsqueda de refugio (solo natural) |
| +P4 | Lo anterior más el impulso de anidar |
| +P5 | Lo anterior más la dotación innata |

**Hipótesis:**

- **H5.1:** el número de muertes nocturnas por vida baja frente a la base.
- **H5.2:** los latidos por vida suben.
- **H5.3:** los logros no empeoran (no inferioridad con margen de −1 logro y TOST).
- **H5.4:** se reduce el vaivén diurno (proporción de latidos diurnos en calma con patrón A→B→A→B).

**Métricas adicionales:**
- Fracción de latidos nocturnos con recinto cerrado (`cobijo = 1`), y fracción con `cobijo ≥ 0,75`.
- Latido del primer cierre de refugio en G1, y si fue natural o construido.
- Piedras colocadas por noche, y movimientos de acomodo (`MOVER` dentro del recinto propuestos por `Anidar`) por cierre completado. Muchos acomodos por cierre indican un problema de orientación.
- Antelación: latidos entre el inicio de la subida de alerta y la caída de la luz por debajo de 0,3.
- **Muertes por hambre o sed** (hoy 0): si aparecen, indican individuos atrapados en su refugio y se analizan.
- Lecturas de la biblioteca, si la variante la tiene activa.

Se publican todas las cifras, incluidas las negativas, con comando, semillas, número de vidas y fecha.

**Comprobación de generalidad:** invariancia en `minimo`, `archivos`, `snake` y `ajedrez` en cada paso.

---

## 6. Prohibiciones específicas de esta fase

- Ninguna secuencia de acciones con cantidades ("talar 3 maderas", "minar 6-8 piedras"), ni en el Core ni en componentes propios.
- Ningún temporizador basado en el contador de pasos del entorno. El tiempo del día se infiere **solo** de la luz percibida (y, en su caso, del oscilador interno sincronizado con ella).
- Ningún componente nuevo lee `env._world`. Todo pasa por la percepción del adaptador.
- Ningún umbral calibrado para Crafter dentro de `ida/core/` o `ida/sistemas/`. Esos valores van en el `Perfil` del mundo.
- La dotación innata no incluye acciones ni recetas (sección 4.5).

---

## 7. Hechos a verificar antes de implementar

No se pudieron comprobar al redactar este plan porque el paquete `crafter` no estaba instalado en el entorno de revisión. Verificar en el código de `crafter` y citar fichero y línea:

1. La fórmula de `daylight` y la duración real del ciclo de día y noche en pasos (el autor estima unos 300).
2. Las condiciones de aparición de zombis (oscuridad, hierba, distancia al jugador) y si pueden aparecer dentro de un recinto cerrado.
3. Si un zombi o una flecha de esqueleto pueden alcanzar al jugador con las 4 casillas vecinas bloqueadas (movimiento en 4 direcciones, sin diagonales).
4. Las casillas válidas para `place_stone` y su coste en piedra. Confirmar que se coloca en la casilla de `facing`.
5. Si minar una piedra colocada devuelve la piedra al inventario.
6. **Orientación:** si moverse hacia una casilla libre siempre desplaza al jugador, y si existe alguna forma de girar sin moverse (una acción, o moverse hacia una casilla bloqueada como ya aprovecha `_interactuar()`).
   - Si **se puede girar sin moverse** hacia una casilla libre: el refugio de una casilla basta, el recinto de `cobijo` puede limitarse a 1 casilla y desaparecen los movimientos de acomodo. Se informa al autor y se simplifican §4.3 y §4.4.
   - Si **no se puede**: se mantiene el diseño de recinto de dos casillas de esta revisión.
7. Si los zombis pueden caminar sobre `path` (las casillas minadas), lo que afecta a los túneles como refugio natural.

Si algún punto contradice este plan (por ejemplo, si los zombis pueden aparecer dentro del recinto), se detiene la implementación del paso afectado y se informa al autor.

---

## 8. Checklist por PR

```bash
python -m pytest -q
ruff check ida tests
mypy ida
git diff --stat -- ida/core ida/sistemas
```

- [ ] Paso 0 entregado antes de cualquier cambio de conducta.
- [ ] Invariancia comprobada en los mundos sin ciclo diurno, en cada paso.
- [ ] Ablación por pasos medida con el protocolo de la sección 5.
- [ ] Hechos de la sección 7 verificados y citados.
- [ ] Deuda de lecturas de `env._world` documentada con fichero y línea.
- [ ] `docs/ESTADO_IMPLEMENTACION.md`, `docs/BENCHMARK_PERFILES_MUNDOS.md` y `CHANGELOG.md` actualizados.
- [ ] Sin lenguaje enfático.
