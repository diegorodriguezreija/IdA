# A3: progreso por etapas

Encargo: paso A3 de `docs/DISENO_COMPONENTES.md` (preatención, plasticidad, regulación; `Amenaza` sustituye a
`ida/core/peligro.py`). Rama `reorg/a3-preatencion`, creada desde `origin/reorg/componentes` (4ee65c2). Etapas, en
orden, cada una en verde y con «EQUIVALENCIA: OK» por sí sola:

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Regulación (punto 5) | HECHA |
| E2 | Gancho de plasticidad (punto 4) | HECHA |
| E3 | Mecanismo de preatención y Saliencia (puntos 1 y 2) | HECHA |
| E4 | Amenaza (punto 3) | HECHA |
| E5 | Especificación, test del mapa y tests restantes (punto 6) | HECHA |

El hash de cada etapa es el del commit «A3 E<n>: ...» (`git log --oneline --grep "A3 E"`); el de una etapa se anota
en la siguiente.

Control antes de empezar (árbol 4ee65c2): `herramientas/equivalencia.py` → `EQUIVALENCIA: OK`.

## E1 · Regulación

Estado: HECHA. Commit d9558e6 «A3 E1: Regulacion sustituye a Marcapasos (D12)».

Comprobación (última línea de cada una):

```
All checks passed!
Success: no issues found in 42 source files
283 passed, 1 warning in 28.49s
EQUIVALENCIA: OK
```

Decisiones:
- `ida/core/marcapasos.py` se renombra a `ida/core/regulacion.py` (`git mv`, quedaba vacío) y `Marcapasos` pasa a
  `Regulacion(Componente)`, `tipo = "Regulacion"`, con las mismas constantes y el mismo método `ritmo(soma,
  frecuencia_base_ms, amplitud_base)`. No usa los barridos: la Onda necesita frecuencia, amplitud y potencia al
  crearse, así que en la fase A se llama en el mismo punto que antes (`Organismo.latir`, antes de `Onda(...)`).
- `Organismo.marcapasos` pasa a `Organismo.regulacion` (con `sistema = "CORE"`). No había otros usos del atributo
  (solo `tests/test_core.py`, actualizado: `test_regulacion_varia_con_el_estado`).
- Línea literal añadida al final de D12 en `docs/DISENO_COMPONENTES.md`.
- Comentarios actualizados en `soma.py`, `onda.py` y `herramientas/benchmark.py`. Los «marcapasos» de `mundo.py`,
  `snake.py` y `crafter.py` hablan del ritmo de tiempo real, no de la clase; se dejan.

- Adelantado de E5 (obligado): `test_especificacion_valida` falla si un `hoy = "fuera:<fichero>"` apunta a un fichero
  que no existe, así que al borrar `marcapasos.py` hay que actualizar ya la entrada `Regulacion` de
  `doc-repositorio/componentes.toml` (`hoy = "CORE.Regulacion"`, sin `paso`, nota nueva; `destino`, `clase` y
  `decision` sin tocar) y que `_montado` lea `org.regulacion` como `CORE.Regulacion` (una línea). Mapa regenerado. Lo
  mismo pasará en E3 (preatención como `S1.Sentir`, Saliencia) y en E4 (Amenaza, al borrar `peligro.py`): cada etapa
  ajusta su entrada; E5 queda para las notas, los tests restantes y la revisión final.
- La equivalencia se pasó con este mismo código (después solo cambiaron el toml, el test y el mapa generado, que no
  intervienen en `evaluar_crafter.py`); ruff, mypy y pytest se repitieron tras ese cambio.

Pendiente: nada de E1.

## E2 · Gancho de plasticidad

Estado: HECHA. Commit a093f59 «A3 E2: gancho de plasticidad Componente.aprender (D6)».

Comprobación (última línea de cada una):

```
All checks passed!
Success: no issues found in 42 source files
285 passed, 1 warning in 29.57s
EQUIVALENCIA: OK
```

Decisiones:
- `Componente.aprender(self, ctx)` en `ida/core/arquitectura.py`, vacío por defecto.
- `Organismo.montados()` da todos los Componentes montados en orden determinista: Core (Sentir, `regulacion`,
  Actuar) y S1, S2 y S3 por módulos. En E3 se añade la preatención entre el Core y S1.
- `Organismo._plasticidad(ctx)` llama a `aprender` de cada uno, dentro de la fase «aprender», justo después de
  `_aprender` y `_contrastar`. Se llama siempre (también sin experiencia y dormido): cada Componente decide con
  `ctx.con_experiencia`. No se pone la Onda en exento: la plasticidad no debe emitir piezas; si alguna lo hiciera,
  pagaría y se le comprobaría la propiedad como a cualquiera (no hay ningún implementador en A3).
- No se apunta tiempo por Componente (no hay implementadores; el tiempo queda dentro de la fase «aprender»).
- Tests en `tests/test_preatencion.py`: orden (`_aprender` y luego Core, S1, S2, S3 por módulos), dentro de la fase
  «aprender» (ya terminó «sentir», aún no hay «S1»), y que corre dormido.

Pendiente: nada de E2.

## E3 · Mecanismo de preatención y Saliencia

Estado: HECHA. Commit 919e4be «A3 E3: preatención (D5) y Saliencia».

Comprobación (última línea de cada una):

```
All checks passed!
Success: no issues found in 43 source files
298 passed, 1 warning in 45.52s
EQUIVALENCIA: OK
```

Decisiones:
- Representación: `Componente.preatentivo = False` (atributo de clase). Cada `Sistema` tiene una lista
  `preatencion` aparte de sus módulos (parámetro nuevo del constructor y `añadir_preatentivo`); solo S1 la admite, y
  un preatentivo dentro de un módulo es `ValueError`. Su ubicación de diseño es `S1.Sentir`, pero al no estar en el
  módulo Sentir no vuelve a correr cuando S1 late. `Sistema.añadir("Sentir", preatentivo)` lo manda a la lista.
- El Organismo junta las listas en `self.preatencion = Preatencion([...])` (módulo exento nuevo de
  `ida/core/arquitectura.py`) y lo ejecuta en la fase «preatencion», justo después de «sentir» y antes de
  «aprender» y de `_dormir`: corre despierto y dormido. `montados()` la pone entre el Core y S1; `registrados` la
  incluye.
- Registro (D3): un preatentivo declarado en `S1.Sentir` (`añade`) va a la preatención; en cualquier otro destino es
  `ValueError`. `sustituye` en `S1.Sentir` busca también en la preatención y exige que sustituto y original sean
  ambos preatentivos o ninguno.
- Control de límites, en la Onda (no por convención): `Preatencion.ejecutar` pone `onda.preatencion = True` (además
  de `exento`). Con esa marca, `Onda._propiedad` solo admite `modificar` de piezas de `CANALES_SENSORES` (movido de
  `latido.py` a `onda.py`) con los campos `arousal` y/o `carga`, y `Onda.modificar` exige que la carga cambie solo la
  clave `rasgos`. Percibir, registrar, proponer, activar, cerrar o modificar otra cosa lanza `PiezaAjena`. La regla
  de propiedad por tipo no cambia para nadie más (la marca solo existe dentro de la preatención).
- Coste: la preatención es exenta: `_cobrar`, `_limitar` y `control_vital` no cobran ni cuentan operaciones (test
  con plazo lógico). Tiempo: fase propia «preatencion» en `onda.fases`; por Componente, en `onda.tiempos_ms` con la
  clave `preatencion:S1.<nombre>` (`Modulo.prefijo_tiempos`), y `ida/telemetria/otel.py` los atribuye a esa fase.
- `Exterocepcion` emite con arousal 0.0 y la misma carga. `Saliencia` (`ida/sistemas/saliencia.py`, `tipo =
  "Exterocepcion"`, preatentivo) pone a cada pieza de `ev["Exterocepcion"]` el arousal con la misma fórmula, vía
  `modificar`. Por qué sale igual: `Pieza.__post_init__` acota el arousal (antes, la saliencia entraba acotada así);
  ahora `modificar` en módulo exento hace `acotar(saliencia)` sin `_limitar` ni cobro, es decir, el mismo valor. Una
  pieza nueva con arousal 0.0 entra en `ev` igual que con otro arousal (el Core exento no comprueba amplitud;
  `Ambiente` ya emitía con 0.0). Rastro extra: una entrada «modificar» en `pieza.registro` (solo lo lee
  `Pieza.audit`, telemetría) y `actualizada` = el mismo latido. Nada de eso entra en la conducta.
- Desviación de D5: D5 dice que `Exterocepcion` emitiría «con la saliencia de lo bruto (proximidad)»; el encargo pide
  arousal 0.0 (sin valorar), y es lo que se hizo.
- Tests que enumeran las fases (`tests/test_observabilidad.py`, `tests/test_organismo.py`): se añade «preatencion»
  a la lista esperada (fase nueva pedida por el encargo; no se relaja nada).
- Adelantado de E5: `componentes.toml` Saliencia → `hoy = "S1.Sentir"`, sin `paso`, nota nueva; `_montado` lee
  `org.preatencion` como `S1.Sentir`. Mapa regenerado.
- Tests nuevos en `tests/test_preatencion.py`: sin consumo de amplitud, potencia ni operaciones; no vuelve a correr
  en la cognición; corre dormido; percibir, registrar, proponer, modificar una pieza no sensora, la confianza o una
  clave de la carga que no sea `rasgos` → `PiezaAjena`; solo preatentivos y solo en S1; Exterocepcion en bruto (0.0)
  y Saliencia igual a la fórmula de antes; el gancho `aprender` incluye la preatención en su orden.

Pendiente: nada de E3 (el orden Amenaza → Saliencia se fijó en E4).

## E4 · Amenaza

Estado: HECHA. Commit de1ccc0 «A3 E4: Amenaza sustituye a ida/core/peligro.py y a _peligro_aprendido».

Comprobación (última línea de cada una):

```
All checks passed!
Success: no issues found in 43 source files
301 passed, 1 warning in 43.67s
EQUIVALENCIA: OK
```

Las noches están cubiertas: la referencia (`datos/equivalencia/base_31.json` y `base_32.json`) tiene
`tasas_logros/wake_up` 7,69 y 16,67, así que en esos 3000 pasos hay latidos dormidos con la preatención activa.

Decisiones:
- `git mv ida/core/peligro.py ida/sistemas/amenaza.py` (el fichero viejo desaparece: regla de traslado). Las clases
  que tenía son `Media`, `Emision` y `Peligros` y las funciones `escala`, `manhattan`, `f_alcance` y `estimar` (el
  encargo citaba `Encuentro`, `ClasePeligrosa` y `PeligroAprendido`, que no existen; se movió todo el contenido).
- `estimar` se parte en `estimaciones(...) -> [(índice, valor)]`, que no escribe, y `estimar`, que escribe en
  `e.rasgos` con ella (lo usan `tests/test_defensa.py` y el test de A3 como referencia). Mismo cálculo y mismo orden.
- `Amenaza(Componente)` (`tipo = "Exterocepcion"`, preatentivo) hace en la preatención lo que hacía
  `_peligro_aprendido`, en el mismo orden (aprender, después estimar), con la misma condición (posiciones y ningún
  `peligro` del mundo) y la marca `ctx.extra["peligro_aprendido"]` (A6 las sustituirá por el registro). Escribe el
  peligro con `modificar(carga={"rasgos": {**rasgos, "peligro": v}})`: la clave queda al final, como antes, porque la
  condición garantiza que no estaba. Orden en S1: `preatencion=[Amenaza(), Saliencia()]`.
- Por qué sale igual aunque ahora corre después de Core · Sentir (antes, antes): Sentir no cambia nada de lo que lee
  Amenaza (el soma no cambia; `ver_clase` solo toca `clases_vistas`, que `peligrosa` y `_objetos` no leen) y las
  piezas copian la Observación (`dict(e.rasgos)`, `dict(e.datos)`, `dict(obs.cuerpo)`, `dict(obs.inventario)`).
- Lecturas: todo sale de piezas. Ubicación, `cuerpo["casillas"]` e inventario, de la pieza `Propiocepcion` «yo»
  (que ya los lleva: `sentidos.py`, `Propiocepcion.reactiva`); clase, rasgos y posición, de cada `Exterocepcion`. No
  quedan lecturas de `ctx.observacion` en Amenaza, así que no hay ningún comentario `# A4:` (el encargo suponía que
  casillas e inventario no estaban en ninguna pieza; sí están, en la Propiocepcion).
- Lector del peligro en la Observación: solo `_aprender_mapa` (`latido.py`), confirmado con `git grep '"peligro"'`
  en `ida/core`, `ida/sistemas`, `ida/mundos/crafter.py` y `herramientas/evaluar_crafter.py`. Ahora lee
  `pieza.rasgo("peligro")` de la `Exterocepcion` de esa entidad (por id). Los demás lectores del peligro
  (`_dormir`, `_indicadores`, S1) ya leían piezas.
- Ciclo de importación: `ida/core/memoria.py` crea `Peligros()`. Importarlo de `ida.sistemas` al cargar `memoria.py`
  cierra un ciclo (`ida.sistemas` → `arquitectura` → `memoria`). Se importa en diferido dentro de
  `Memoria.__init__`, con `TYPE_CHECKING` para la anotación y un comentario `A7:` (la sección pasará a su dueño). Es
  la única dependencia de `ida/core` hacia `ida/sistemas`; `test_pureza` no la prohíbe.
- `Organismo._peligro_aprendido` y su llamada se borran; `memoria.peligros` solo lo escribe `Amenaza`.
- `tests/test_proteger.py`: dos tests llamaban a `_aprender_mapa` con un contexto falso sin Onda. Se añade `_ctx(obs)`,
  que da también las piezas `Exterocepcion` que emitiría el sensor con esa Observación (mismos rasgos). No cambia
  ninguna aserción.
- `componentes.toml`: Amenaza → `hoy = "S1.Sentir"`, `hoy_en = "todos"`, `paso = "A6"`, nota nueva. Mapa
  regenerado. `destino`, `clase`, `registran` y `decision` sin tocar.
- Tests nuevos: Amenaza antes que Saliencia; en Crafter (semilla 31, 30 latidos) el peligro está al final de los
  rasgos de cada pieza con posición, con el valor exacto de `estimar` sobre una copia de la Observación con la misma
  memoria, y la Observación queda sin `peligro`; `ctx.extra["peligro_aprendido"]` puesto.

Pendiente: nada de E4.

## E5 · Especificación, test del mapa y tests restantes

Estado: HECHA. Commit: «A3 E5: especificación y documentación al día».

Comprobación (última línea de cada una, punto 7 del encargo):

```
All checks passed!
Success: no issues found in 43 source files
301 passed, 1 warning in 43.44s
Mapa de Componentes válido y al día.
EQUIVALENCIA: OK
```

Decisiones:
- Las entradas de Regulacion, Saliencia y Amenaza en `componentes.toml` y las dos líneas de `_montado` se hicieron en
  E1, E3 y E4 (cada etapa debía quedar en verde; ver E1). En E5 solo queda la nota de `Exterocepcion` («emite con
  arousal 0; la saliencia la pone Saliencia en la preatención»). Mapa regenerado.
- `doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md`: el párrafo de atención nombra la `Regulacion`
  (`ida/core/regulacion.py`) en lugar del `Marcapasos`.
- No se tocan los documentos históricos que citan `ida/core/peligro.py`, `marcapasos.py` o `_peligro_aprendido`
  (`docs/R0_INVENTARIO.md`, planes, mediciones, `CHANGELOG.md`), ni las columnas «Hoy» de `docs/DISENO_COMPONENTES.md`
  (cambiar el diseño exige al autor; solo se añadió la línea literal de D12).
- Tests pedidos en el punto 6, todos en `tests/test_preatencion.py`: sin consumo de amplitud ni potencia (ni
  operaciones del plazo lógico); corre dormido; emitir o modificar una pieza no sensora → error; Saliencia da el
  arousal de antes; Amenaza escribe el peligro en la pieza y no en la Observación; el gancho `aprender` se llama en la
  fase «aprender» y en orden.

Para quien continúe (A4 en adelante):
- Ninguna lectura `# A4:` en Amenaza: lo que necesitaba de la Observación ya estaba en la pieza `Propiocepcion`.
- `Memoria` importa `Peligros` en diferido (comentario `A7:`); al hacer las secciones con dueño (A7) debería
  desaparecer esa dependencia de `ida/core` hacia `ida/sistemas`.
- La condición de Amenaza (posiciones y sin peligro del mundo) y `ctx.extra["peligro_aprendido"]` siguen; son A6.
- La Regulación se sigue calculando al crear la Onda; moverla tras la preatención es B2 (cambio de conducta).
