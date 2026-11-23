# A3: progreso por etapas

Encargo: paso A3 de `docs/DISENO_COMPONENTES.md` (preatención, plasticidad, regulación; `Amenaza` sustituye a
`ida/core/peligro.py`). Rama `reorg/a3-preatencion`, creada desde `origin/reorg/componentes` (4ee65c2). Etapas, en
orden, cada una en verde y con «EQUIVALENCIA: OK» por sí sola:

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Regulación (punto 5) | HECHA |
| E2 | Gancho de plasticidad (punto 4) | HECHA |
| E3 | Mecanismo de preatención y Saliencia (puntos 1 y 2) | HECHA |
| E4 | Amenaza (punto 3) | pendiente |
| E5 | Especificación, test del mapa y tests restantes (punto 6) | pendiente |

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

Estado: HECHA. Commit: «A3 E3: preatención (D5) y Saliencia».

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

Pendiente: Amenaza (E4) debe ir antes que Saliencia en `crear_s1` (`preatencion=[Amenaza(), Saliencia()]`).
