# Plan de evolución de IdA (núcleo)

Documento de trabajo para el agente implementador. Se lee junto a [`AGENTS.md`](../AGENTS.md), cuyas reglas siguen vigentes salvo lo que este documento autoriza de forma expresa en la sección 2.

Fecha: 2026-11-11. Base: `main` tras el PR #3 (`crafter: mapa cognitivo (hipocampo), defensa armada activa y aliestesia de reparacion`).
Revisión arquitectónica y ajustes: mantenemos estrictamente el diseño modular por **Componentes (`Sentir / Interpretar / Reaccionar`) y barridos (`reactiva / activa / proactiva`)** sin introducir rupturas arquitectónicas ni acoplamientos ajenos a la dinámica habitual de IdA.

---

## 0. Principios Rectores de Diseño (Continuidad con IdA)

Ninguna fase rompe la arquitectura basada en Componentes, Piezas, Onda y Tribunal. Cualquier extensión sigue exactamente el mismo patrón que los módulos actuales de `S1`, `S2` y `S3`:
1. **Aislamiento en Componentes independientes**: cada capacidad nueva (orientación espacial, estudio) se implementa como un `Componente` estándar con sus entradas declaradas (`entradas`), barrido limpio y emisión de propuestas vía `self.proponer(...)` hacia el Tribunal, nunca como lógica incrustada en el bucle de `Organismo`.
2. **Integración gradual no invasiva**: se trabaja rama a rama, commit a commit, validando la invariancia donde no se busca alterar conducta y midiendo empíricamente cada mejora conductual con semillas repetibles.
3. **Los cambios en el Core son acotados y orgánicos**: `ida/core` sigue siendo únicamente sustrato de memoria, soma, onda y arbitraje (igual que `Memoria.lugares` y `Memoria.consolidar` ya existentes).

---

## 1. Resumen y orden de fases

| Fase | Contenido | Valor | Encaje arquitectónico (Componentes) | Viabilidad | Estado |
|---|---|---|---|---|---|
| 1 | Hipocampo en el Core + Componente `Orientacion` | Muy Alto | Usa el mismo esquema que `Hogar` / `Curiosidad` en S2 | Alta | **Implementar primero** |
| 2 | *Replay* inverso de trayectorias al dormir | Medio-Alto | Extiende `Memoria.consolidar()` existente sin tocar sistemas | Alta | **Implementar** tras la 1 |
| 3 | Confianza ponderada (experiencia / autoridad) | Alto (habilita la 4) | Refactor interno en `Proposicion`, invariancia total | Alta | **Implementar** |
| 4 | Biblioteca: consulta asíncrona y componente `Estudio` | Alto | Nuevo componente en `S3` compitiendo en el Tribunal | Media | **Evaluar/Implementar** 4a tras 3 |
| 5 | Telemetría 2.0 (mapa cognitivo, lecturas, afecto) | Alto | Lee datos expuestos por `Onda` y `Memoria` | Alta | **Siguiente hito** tras 4 |
| — | Poblaciones, multiagente, mundos continuos | — | Fuera de alcance en este ciclo (§7) | — | Aplazadas/Descartadas |

Cada fase es una rama y un PR propios. No se empieza una fase sin que la anterior esté fusionada.

---

## 2. Autorización del autor sobre `ida/core/` e `ida/sistemas/`

El autor autoriza modificar `ida/core/` e `ida/sistemas/` **solo** para lo descrito en las fases 1 a 4, con estas condiciones:

1. Cada cambio en el núcleo va en un commit propio con su justificación.
2. **Invariancia con semilla.** Todo cambio que no busca cambiar la conducta (refactors, registro de datos que nada consume todavía, mecanismos desactivados por defecto) debe dejar idénticas las vidas con semilla. Comprobación mínima, antes y después (PowerShell en Windows, forzando UTF-8 para evitar falsas diferencias):
   ```powershell
   $env:PYTHONIOENCODING = "utf-8"
   $ETAPA = "antes"   # cambiar a "despues" en la segunda ejecución
   foreach ($m in "minimo", "archivos", "crafter") {
     python -m ida --mundo $m --latidos 400 --semilla 3 --tabula-rasa --cada 1 | Out-File -Encoding utf8 "$env:TEMP\$m.$ETAPA.txt"
   }
   ```
   y comparación (`Compare-Object (Get-Content ...) (Get-Content ...)` o `diff`) excluyendo exclusivamente campos dependientes del reloj (`ms`, `plazo_ms`, tiempos de fase). Documentar exactamente el filtro aplicado.
3. Los cambios que **sí** buscan cambiar la conducta se miden antes y después en las mismas semillas (idealmente 10 semillas independientes en `crafter` como en `05_METRICAS_E_HITOS.md`), con comando, semillas, número de vidas y fecha (regla 7 de `AGENTS.md`). Se publican también los resultados negativos.
4. `tests/test_pureza.py` no se relaja. Se **añade** `ida.bibliotecas` a `IMPORTS_PROHIBIDOS` en la fase 4.
5. Nada de `push` sin que el autor lo pida.

---

## 2. Fase 1 — Hipocampo en el Core

### 2.1 Diagnóstico (verificado en el código actual)

- El mapa cognitivo de Crafter vive hoy en el **adaptador del mundo**: `self.hitos` en `MundoCrafter` (`ida/mundos/crafter.py:102`, rellenado en `:238-248`), y `PlanTecnologico` lo lee vía `self.mundo.hitos` (`:514-515`). Esto viola parcialmente el aislamiento hexagonal (regla 3 de `AGENTS.md`): el mundo no debería almacenar la memoria espacial del individuo.
- Esa memoria está hardcodeada para cuatro clases (`mesa`/`table`, `horno`/`furnace`, `planta`, `agua`), no tiene olvido ni capacidad acotada.
- El Core ya recuerda **qué** lugar fue placentero (`Memoria.lugares` en `ida/core/memoria.py:112` y `hogar()` en `:267-271`), pero `Hogar` (`ida/sistemas/s2.py:123-146`) solo puede regresar si el id del hogar aparece como pieza adyacente en la escena actual (`l.id == hogar`). Si está a más de un salto, queda ciego.

### 2.2 Diseño (ajustado al contrato real de los 5 mundos)

Añadir a `Memoria` (`ida/core/memoria.py`) un mapa topológico genérico sin vocabulario de mundo:

- **Grafo de transiciones** `mapa: Dict[str, Dict[str, Arista]]` (con `Arista`: `usos`, `ultimo_latido`, `valor_replay`). Cuando `Observacion.ubicacion` cambia respecto al latido previo, el `Organismo` registra la arista `origen → destino` en la fase `aprender`.
  - *Nota técnica de acoplamiento de mundos*: En `minimo` (`celda_x_y`), `archivos` (`rel`) y `crafter` (`celda_x_y`), `Observacion.ubicacion` coincide **exactamente** con el `id` de las entidades `lugar` devueltas en `Observacion.entidades`. En `snake` (`snake.py:188`), la ubicación por celda sí existe (`f"{hx}_{hy}"`, y `"fin"` al morir), pero los lugares observables se identifican por dirección (`dir_N`, `dir_S`...). Por tanto, en Snake las aristas del grafo se registrarán hasta llenar la capacidad máxima (y se irán renovando), pero como ningún `l.id` coincide con el nodo devuelto por `ruta()`, el consumidor no emitirá propuestas y la conducta de Snake (y Ajedrez) permanecerá invariante sin introducir excepciones por nombre de mundo.
- **Memoria de clase por lugar** `donde: Dict[str, RecuerdoLugar]` (`ubicacion`, `ultimo_latido`, `confianza`): cuando una entidad de clase C está al alcance (`proximidad >= ALCANCE` en `sistemas/comun.py`), o inmediatamente después de una interacción exitosa (`COGER`, `COMER`, `USAR`), se asocia C a `ubicacion` actual. Consulta pública unificada mediante el método `donde_esta(clase) -> Optional[str]` (o `donde` coherente en toda la API).
  - *Ajuste crítico para Crafter (traducción de recetas vs clases observadas)*: En Crafter, la escena percibe clases en español (`"mesa"`, `"horno"`), mientras que las recetas de `crafter.constants.make` piden `"table"` o `"furnace"`. Al eliminar `self.mundo.hitos`, `PlanTecnologico` (`crafter.py`) debe traducir el nombre de receta a la clase percibida (`{"table": "mesa", "furnace": "horno"}`) antes de consultar `ctx.memoria.donde_esta(...)` y `ctx.memoria.ruta(...)`. El Core nunca conoce esos nombres.
- **Ruta**: búsqueda en anchura (BFS) acotada por profundidad máxima sobre `mapa` desde la ubicación actual hacia el destino. Devuelve el siguiente nodo `siguiente_lugar`. El consumidor solo propone `Verbo.MOVER` si existe un `l` en `lugares(ctx)` con `l.id == siguiente_lugar` y `l.rasgo("peligro") < 0.8`.
- **Invariancia de presupuesto y coste**: Limitar el tamaño de `mapa` (p. ej. `MAX_NODOS_MAPA = 200` mediante política LRU/olvido por desuso) para que BFS sobre grafos de mundo nunca exceda el presupuesto de tiempo del latido ni dispare la guillotina. El olvido y poda ocurren dentro de `consolidar()` al dormir (o al superar capacidad máxima).
- **Barrera de Weismann**: el mapa espacial **no** entra en `legado()` (es memoria episódica/topológica de la vida individual).
- Con `perfil.memoria == "apagada"` el mapa no se registra ni responde rutas.

Consumidores en `ida/sistemas/` y `ida/mundos/`:

- `Hogar` (`ida/sistemas/s2.py`): si `hogar != aqui`, primero busca adyacencia directa (`l.id == hogar`); si no está al lado, consulta `ctx.memoria.ruta(aqui, hogar)` para dar el siguiente salto.
- **Nuevo componente `Orientacion` en `S2.Reaccionar`**: cuando hay hambre/necesidad no crítica (`apetito` activo o `hambre >= 0.35`) o una meta pendiente y no hay fuente visible en `Escena`, consulta si alguna clase que satisface esa necesidad (proposición `nutritivo` demostrada o con alta confianza) está registrada en `ctx.memoria.donde_esta(...)`, y solicita `ruta` hacia esa ubicación (a arousal moderado para no pisar reflejos de S1 ni el plan local inmediato).
- **Crafter (`ida/mundos/crafter.py`)**: `PlanTecnologico._ir_hacia_estructura` deja de usar `self.mundo.hitos`, traduce la estructura requerida a su clase percibida (`mesa`/`horno`) y pide el siguiente paso a `ctx.memoria.ruta(aqui, destino)`. **Se elimina `self.hitos` por completo de `MundoCrafter`.**

### 2.3 Pasos y commits

1. Core (`memoria.py`, `latido.py`): estructuras `Arista`, `mapa`, `donde`, registro en `_aprender`, limpieza en `consolidar()`. Sin consumidores todavía. **Invariancia obligatoria 100%** en `minimo`, `archivos` y `crafter`.
2. Core: API `ruta(origen, destino)` y `donde_esta(clase)` + tests unitarios en `tests/test_memoria.py` (grafos con ciclos, callejones sin salida, capacidad máxima, ausencia de propuestas si los ids no coinciden, y olvido).
3. Sistemas (`s2.py`): `Hogar` usando `ruta()`. Medición pareada en `minimo` y `archivos` (latidos y tasa de retorno al hogar).
4. Sistemas (`s2.py`): `Orientacion` en `S2.Reaccionar`. Medición pareada en `minimo` y `archivos`.
5. Crafter (`crafter.py`): reemplazo de `self.hitos` por `ctx.memoria` con mapeo local de nombres. Comparación pareada exacta sobre las mismas 10 semillas publicadas en `doc-repositorio/05_METRICAS_E_HITOS.md` (`python -m ida --mundo crafter --latidos 600 --semilla S` para `S=1..10`), publicando los resultados por semilla sin descenso significativo respecto al baseline (`263.8` latidos / `10.9` logros).

---

## 3. Fase 2 — *Replay* inverso de trayectorias al dormir

### 3.1 Valoración y Ajustes

- **Valor real**: Excelente base neurobiológica (el *hippocampal replay* durante el sueño SWS consolida trayectorias hacia recompensas y aversiones).
- **Riesgo detectado respecto a la propuesta original**: En `Episodio.acciones`, un episodio puede contener muchos pasos erráticos o bucles `A -> B -> A -> B`. Propagar valor de recompensa con descuento simple sobre ciclos puede inflar artificialmente nodos intermedios.
- **Ajuste de diseño**:
  - Extraer la secuencia única sin bucles triviales recientes o aplicar actualización TD/elegibilidad decreciente solo en la última aparición de cada nodo dentro del episodio (`mapa_valores: Dict[str, float]`).
  - Mantener el límite estricto: `Replay` **nunca** crea ni altera `Proposicion` (no fabrica evidencia falsa), solo modula el atractivo/valor heurístico de los lugares en el mapa cognitivo para desempatar exploración (`Curiosidad`) o rutas alternativas en `ruta()`.

### 3.2 Criterios de aceptación

- Con `perfil.duerme == False` (Snake, Ajedrez): invariancia absoluta.
- Test unitario sintético: trayectoria resuelta `A -> B -> C` deja `valor(C) > valor(B) > valor(A) > 0`; trayectoria con muerte o daño deja valencia negativa decreciente desde el evento adverso.
- Comparativa empírica en `minimo`, `archivos` y `crafter` (tiempo hasta reencontrar comida tras dormir, supervivencia media).

---

## 4. Fase 3 — Confianza ponderada por fuente de evidencia

### 4.1 Valoración y Ajuste sobre la Herencia

- El diseño de separar `c_exp` y `c_aut` con peso dinámico `w_exp = 1 + confirmaciones + refutaciones` frente a `w_aut` es limpio, matemáticamente estable y preserva el principio de "mucha experiencia propia acaba venciendo a la autoridad".
- **Ajuste en Herencia (`memoria.py:309-319`)**:
  Hoy en día `heredar()` inicializa `Proposicion(..., confianza=float(d["confianza"]) * 0.8)` con `confirmaciones = CONFIRMACIONES_MINIMAS - 1` (`= 2`). Si forzamos una fórmula algebraica distinta para simular herencia en esta fase sin tocar conducta, es fácil introducir divergencias de redondeo flotante en `confirmar()` o `refutar()`.
  **Decisión práctica:** mantener el mecanismo actual de `heredar()` idéntico como estado inicial heredado de `c_exp` (para garantizar **invariancia numérica al 100%** en todas las generaciones y tests existentes), y añadir exclusivamente la dimensión ortogonal de **autoridad** (`c_aut`, `w_aut`) + etiqueta de origen en `texto()`.
- **Ajuste en Deferencia**: derivar `deferencia = 0.6 * responsabilidad + 0.4 * (1.0 - apertura)` sin tocar `Arquetipo.nuevo` para preservar la secuencia del PRNG `Azar` en todas las semillas.

### 4.2 Criterios de aceptación

- **Invariancia 100% verificada** en los 5 mundos y en todos los tests de linaje existentes (`test_historico.py`, etc.).
- Tests unitarios específicos en `test_memoria.py` para el balance experiencia vs autoridad (concordancia, conflicto y superación por acumulación de experiencia).

---

## 5. Fase 4 — Biblioteca (Lectura con Atención Sostenida)

### 5.1 Concepto y Cautelas de Diseño

IdA puede consultar una biblioteca externa sobre sus **hipótesis sin resolver**. La consulta es **asíncrona** (el latido nunca espera a la red) y **leer cuesta atención**: el nuevo componente `Estudio` en `S3` debe sostener la lectura latido a latido hasta terminarla. Si la atención se rompe (alarma, hambre, guillotina, sueño), no se extrae nada, igual que una lección leída a medias. Toda consulta queda guardada como **registro** (consulta y respuesta) que IdA puede releer más tarde sin volver a consultar.

- **Alineación con la Regla 3 de `AGENTS.md`**: la biblioteca es una fuente de **autoridad** (fase 3), nunca un sensor del mundo ni un oráculo de acciones; solo modifica la confianza de proposiciones que el individuo ya formó por su cuenta.
- **Cautela 1 — Espera fuera del latido cronometrado**: en modo determinista (no tiempo real), si al terminar la lectura la respuesta aún no llegó, la espera bloqueante **debe ocurrir en `Organismo.vivir()` entre un latido y otro** (nunca dentro de `latir()` ni de `Estudio`), o de lo contrario saltaría la guillotina de tiempo del latido.
- **Cautela 2 — Control del coste por turnos**: dado que cada `LEER` consume un paso real en mundos por turnos como Crafter (avanzan hambre, sed y el ciclo día/noche), conviene acotar las hipótesis por consulta (`MAX_HIPOTESIS_POR_LECTURA = 2` o `3`) y exigir una ventana de enfriamiento mínima entre lecturas o tras una interrupción.

### 5.2 Puerto hexagonal y adaptadores

`ida/core/biblioteca.py` define únicamente la interfaz y los tipos, sin red ni hilos:

```python
class Biblioteca(ABC):
    def solicitar(self, consulta: Consulta) -> Ticket: ...   # no bloquea
class Ticket(ABC):
    def lista(self) -> bool: ...
    def respuesta(self) -> Optional[Respuesta]: ...
```

- `Consulta`: lista acotada de `(clase, Relacion)` con el estado actual de cada hipótesis. **No** incluye el nombre del mundo ni datos del individuo.
- `Respuesta`: por elemento, `veredicto ∈ {afirma, niega, no_sabe}` y `confianza ∈ [0, 1]`. `no_sabe` no aporta evidencia. Una respuesta mal formada se guarda como inválida (`invalido`) y no aporta evidencia.

Implementaciones en `ida/bibliotecas/` (fuera del Core; `ida.bibliotecas` se añade a `IMPORTS_PROHIBIDOS` en `tests/test_pureza.py`):

- `nula`: no existe biblioteca (por defecto). Garantiza invariancia absoluta.
- `fija`: diccionario determinista cargado de un JSON. Para tests y CI.
- `erronea`: como `fija`, pero invierte una fracción configurable de veredictos con semilla. Para contrastar pérdida de fe / robustez.
- `llm` (fase 4b): llamada a un modelo de lenguaje en un hilo propio (`ThreadPoolExecutor(max_workers=1)`), con salida JSON validada contra el esquema de `Respuesta`, caché en disco indexada por `sha256(modelo + consulta normalizada)` y modo `solo-cache` para experimentos reproducibles. Dependencia opcional en extra `[biblioteca]`; la CI no la instala.

Conexión: `ejecutor.py` recibe la biblioteca y la pasa al `Organismo`; la CLI añade `--biblioteca {nula,fija,erronea,llm}` y sus opciones. La antesala web se integrará en la Fase 5.

### 5.3 Lectura con atención sostenida (`Estudio` en S3)

- **Verbo interno `LEER`** en `Verbo` (`vocabulario.py`). No tiene actuador propio: `Actuador` lo ejecuta en el mundo como `ESPERAR`, igual que hoy hace con `ACECHAR` (`sentidos.py:153-155`). Así leer **consume tiempo del mundo**. En mundos sin `Verbo.ESPERAR` (Ajedrez), `Estudio` no ofrece lectura.
- **Componente `Estudio` en `S3.Reaccionar`**. Inicia una lectura cuando:
  - existe biblioteca;
  - el afecto es `CALMA`, no hay alarma, y hambre/cansancio están por debajo de sus umbrales;
  - existen proposiciones en `HIPÓTESIS` que no se consultaron en los últimos `N` latidos y ha pasado el enfriamiento desde la última lectura/interrupción.
  
  Al iniciarla, crea el registro, llama a `solicitar()` (hasta `MAX_HIPOTESIS_POR_LECTURA`) y propone `LEER` (`self.proponer`). Mientras dura la lectura, propone `LEER` cada latido con arousal bajo y confianza moderada, compitiendo en el Tribunal como cualquier componente estándar.
- **Interrupción**: si en un latido de lectura la decisión ejecutada (`ctx.onda.ei("Ejecucion")`) no fue `LEER`, o si IdA se duerme, la lectura queda **interrumpida** (`interrumpido`) y no se aplica evidencia. La guillotina no requiere lógica especial: si S3 no llega a ejecutarse, no hay propuesta `LEER`, gana otra acción y la lectura se rompe.
- **Duración en latidos**: `latidos_lectura = L0 + L1 · n_elementos` (inicial: `L0 = 4`, `L1 = 2`). Al cumplirse:
  - si la respuesta está lista, se aplica como evidencia de autoridad (fase 3) y el registro pasa a `leido`;
  - si no está lista y el perfil es no-tiempo-real, el cierre de `Organismo.vivir()` espera antes del siguiente latido hasta obtener la respuesta (determinismo reproducible con caché);
  - si no está lista y el perfil es tiempo real (`Snake`), se sigue proponiendo `LEER` hasta un máximo tras el cual pasa a `sin_respuesta`.
- **Relectura**: si existe un registro con respuesta disponible y no leído (tras interrupción previa), `Estudio` puede releerlo pagando de nuevo la duración en latidos **sin volver a llamar a `solicitar()`**. La evidencia de un registro se aplica **una sola vez**.
- **Registros y persistencia**: `Memoria.lecturas` guarda consulta, respuesta, estado (`pendiente`, `disponible`, `leido`, `interrumpido`, `sin_respuesta`, `invalido`), latido de inicio e interrupciones. Se persisten en una nueva tabla de `persistencia.py`. **No se heredan**: son vivencias del individuo; solo lo demostrado pasa al linaje.
- **Lenguaje interno**: cada evento emite nota en `onda.notas["aprendizaje"]` (ej. `«empieza a leer sobre 2 hipótesis»`, `«deja la lectura: alarma»`, `«lee: la biblioteca afirma 'C hace daño' (0.80); confianza 0.34 -> 0.55»`).

### 5.4 Extensión opcional y orden de entrega

- **Fiabilidad aprendida de la fuente**: si la experiencia refuta repetidamente lo que la autoridad afirmó, `fiabilidad_fuente` desciende; si lo confirma, sube. Se evaluará tras validar 4a usando la biblioteca `erronea`.
- **4a (Prioritaria y autocontenida)**: puerto, `nula`, `fija`, `erronea`, `LEER`, `Estudio`, registros, espera externa en `vivir()` y persistencia.
  - Tests unitarios y de invariancia (`nula`): evidencia aplicada una sola vez; interrupción no aplica nada; relectura sin `solicitar()`; duración determinista; respuesta inválida ignorada; sin `ESPERAR` no hay lectura.
  - Medición pareada en `minimo` y `crafter` (`fija` frente a `nula` sobre 10 semillas): lecturas iniciadas/completadas/interrumpidas, latidos leyendo, supervivencia y logros (publicando el coste de latidos aunque sea negativo).
- **4b (`llm` con caché `sha256` y `solo-cache`)**: se aborda tras consolidar 4a, testeada con cliente simulado sin llamadas de red en CI.

---

## 6. Lo que dejamos fuera de estas 4 fases (y por qué)

- **Telemetría 2.0**: Se agenda como **Fase 5 natural** una vez integradas las Fases 1-4, para visualizar en la UI web el mapa del hipocampo (grafo real vs conocido), los valores de *replay*, el origen de confianza (experiencia/herencia/autoridad) y el historial de lecturas de biblioteca sin tener que modificar el panel dos veces.
- **Poblaciones y especiación**: Aplazada hasta aclarar explícitamente en diseño si la evolución muta el arquetipo sobre vivencias (lamarckismo actual en `Arquetipo.mutar()`) o pasa a selección estricta darwiniana entre múltiples individuos simultáneos/en paralelo por generación.
- **Multiagente**: Aplazado tras poblaciones (implica refactor profundo de `Organismo` y el protocolo `Mundo`).
- **Mundos continuos (CartPole, LunarLander) y Condicionamiento de 2º orden**: Descartados en esta iteración porque desvían el foco del núcleo simbólico-biológico y no aprovechan el vocabulario discreto de proposiciones y rasgos del framework.

---

## 7. Checklist obligatorio antes de cada PR

```bash
python -m pytest -q
ruff check ida tests
mypy ida
git diff --stat -- ida/core ida/sistemas    # cada cambio, justificado en su propio commit
```

- [ ] **Invariancia con semilla** comprobada y documentada en pasos de infraestructura (filtrando únicamente tiempos `ms`).
- [ ] **Evaluación empírica** antes/después con comando exacto, 10 semillas en Crafter (y semillas equivalentes en `minimo`/`archivos`), fecha y publicación íntegra de resultados (incluidos los negativos).
- [ ] **Test de pureza AST** intacto (sin excepciones ni rebajas).
- [ ] **Documentación al día**: `docs/ESTADO_IMPLEMENTACION.md`, `doc-repositorio/05_METRICAS_E_HITOS.md` y `CHANGELOG.md`.
- [ ] **Sin lenguaje enfático**; conclusiones basadas en cifras y límites observados.
