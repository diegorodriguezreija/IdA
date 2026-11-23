# A5a: progreso por etapas

Encargo: paso A5a de `docs/DISENO_COMPONENTES.md` (sección 5): primer cuerpo, la familia cuadrícula (D10). Rama
`reorg/a5a-cuerpo`, creada desde `origin/reorg/componentes` (6d4441b, con A3 fusionado). Cada etapa en verde y con
«EQUIVALENCIA: OK» por sí sola.

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Contrato `Cuerpo`, montaje y tests de registro (puntos 1, 2 y parte del 9) | HECHA |
| E2 | `Cuadricula`, `ModeloDirecto` y `MapaLocal`, mismo punto, registro de Crafter (puntos 3, 4 y 6) | HECHA |
| E3 | Leer piezas en lugar de la Observación (punto 5) | pendiente |
| E4 | Herramienta, especificación y tests restantes (puntos 7, 8 y 9) | pendiente |

El hash de cada etapa es el de su commit «A5a E<n>: ...» (`git log --oneline --grep "A5a E"`); se anota en la etapa
siguiente.

## E1 · Contrato Cuerpo y montaje

Estado: HECHA. Commit 4cd3f13 «A5a E1: contrato Cuerpo y montaje de sus Componentes (D10)».

Comprobación (última línea de cada una):

```
All checks passed!
Success: no issues found in 43 source files
304 passed, 1 warning in 29.70s
EQUIVALENCIA: OK
```

Decisiones:
- `ida/core/mundo.py`: clase base `Cuerpo` (`nombre`, `componentes() -> Dict[str, List[Componente]]`, vacío por
  defecto) y `Registro.cuerpo: Optional[Cuerpo]`. `Componente` solo se importa con `TYPE_CHECKING` (arquitectura
  importa mundo; importarlo en ejecución cerraría un ciclo).
- `ida/core/latido.py`: `DESTINOS_VALIDOS_CUERPO` = los del registro + `CORE.Actuar`. Si hay cuerpo, sus Componentes
  se montan antes que los del registro del mundo, con las reglas de `añade` (al final del módulo; un preatentivo, al
  final de la preatención; nombre de clase único en el módulo), `propio_del_mundo = True` y `de_cuerpo = nombre`. En
  `CORE.Actuar` van al final del módulo actuar con `sistema = "CORE"`; en `CORE.Sentir`, con `sistema = "MUNDO"`
  como lo del registro. Se guardan en orden de montaje en `Organismo.componentes_cuerpo`.
- Para no duplicar las reglas, el `añade` del registro y el del cuerpo comparten `Organismo._añadir`, y la elección
  de módulo, preatención y sistema está en `Organismo._destino`. Mismo comportamiento que antes en el registro.
- `Componente` gana dos atributos de clase: `de_cuerpo = ""` y `propio_del_mundo = False` (este ya se ponía en
  ejecución; declararlo hace falta para mypy ahora que `_añadir` recibe un `Componente` tipado). Nadie lee
  `propio_del_mundo` fuera de los tests (`git grep`).
- Plasticidad: `_plasticidad` salta los Componentes con `de_cuerpo`; su `aprender` lo llama `_aprender` justo después
  de `_aprender_mapa`, con la misma condición (`con_experiencia and memoria.activa`). En E1 ningún mundo registra
  cuerpo, así que no hay cambio; en E2 esa llamada sustituye a `_aprender_mapa`.
- `tests/test_registro.py`: el test «cuerpo distinto de None → ValueError» se sustituye por: el cuerpo se monta antes
  que lo del mundo y admite `CORE.Actuar`; destino no válido → `ValueError`; cuerpo y mundo no pueden repetir clase;
  `aprender` de cada Componente de cuerpo se llama una sola vez por latido (tres latidos).

Pendiente: nada de E1.

## E2 · Cuadricula, ModeloDirecto y MapaLocal

Estado: HECHA. Commit: «A5a E2: cuerpo cuadrícula con ModeloDirecto y MapaLocal; Crafter lo registra».

Comprobación (última línea de cada una):

```
All checks passed!
Success: no issues found in 48 source files
304 passed, 1 warning in 29.65s
EQUIVALENCIA: OK
```

Decisiones:
- `ida/cuerpos/__init__.py` y `ida/cuerpos/cuadricula/`: `__init__.py` (`Cuadricula(Cuerpo)`, `nombre = "cuadricula"`,
  `componentes() = {"CORE.Actuar": [ModeloDirecto()], "S1.Interpretar": [MapaLocal()]}`), un fichero por Componente
  (`modelo_directo.py`, `mapa_local.py`) y `situacion.py` con lo que comparten: `situacion(ctx)` (posición, casillas
  y orientación, o None), `accion_previa(ctx)` (de `ei["Accion"]`, como antes) y `vecina(mem, c)` (casilla vecina de
  la acción anterior). En E2 `situacion` y las entidades de `MapaLocal` aún leen `ctx.observacion` (E3 lo cambia).
- Partición de `_aprender_mapa`: `ModeloDirecto` hace las dos llamadas a `mem.aprender_cuerpo`; `MapaLocal`, en el
  mismo orden de antes, transformaciones y cierres (con el comentario `# A7:`: son de Requisito según D7), libres,
  ocupadas y peligros, `ver_casillas` y `yo_previo`. Por qué sale igual: `aprender_cuerpo` solo escribe
  `Memoria.cuerpo`, que no leen `aprender_transformacion`, `transitable` ni `transitable_peligro` (comprobado con grep
  de `self.cuerpo` en esos métodos), así que adelantar las dos llamadas al bloque de transformaciones no cambia nada; y
  `ModeloDirecto` corre antes, así que lee `yo_previo`, `casillas` y `transitable` sin actualizar, como antes.
- Sin barridos: los dos sobrescriben `activo()` → `False`. Si no, `Modulo.ejecutar` llamaría a `control_vital` por
  cada barrido en S1.Interpretar (no exento) y sumaría operaciones al plazo lógico, lo que cambiaría la guillotina.
- `Organismo._aprender`: donde se llamaba a `_aprender_mapa` (misma condición) se llama a `aprender` de
  `componentes_cuerpo` en orden de montaje (ModeloDirecto, MapaLocal). `_aprender_mapa` se borra (y el import ya
  sin uso de `pos_de` en `latido.py`).
- Crafter: `registro()` devuelve `Registro(cuerpo=Cuadricula())`. Ningún otro mundo de `ida/mundos` da `casillas`
  (`git grep '"casillas"' ida/mundos`: solo `crafter.py`), así que en ellos `_aprender_mapa` no hacía nada.
- Herramientas que quitan las estrategias propias reemplazando el registro por `Registro()`
  (`evaluar_crafter.py --sin-estrategias-propias`, `diagnostico_bucle.py`, `diagnostico_intensidad.py`,
  `diagnostico_tribunal.py`): ahora conservan el cuerpo (`Registro(cuerpo=original(self).cuerpo)`). Si no, esas
  ejecuciones perderían el mapa local, que antes siempre se aprendía. La equivalencia no usa esa opción.
- Adelantado de E4 (obligado, como en A3): `test_el_codigo_coincide_con_hoy[crafter]` falla si hay Componentes
  montados que el toml no declara, así que `ModeloDirecto` y `MapaLocal` ya están en `componentes.toml` con
  `hoy = "CORE.Actuar"` / `"S1.Interpretar"`, `hoy_en = ["crafter"]`, sin `paso` y con notas nuevas. Mapa
  regenerado. `_montado` ya leía `CORE.Actuar` y los módulos de S1, y `_esperado` ya filtra por `hoy_en`: el test del
  mapa no necesitó cambios.
- `tests/test_proteger.py`: su `MundoCueva` es una cuadrícula que da `casillas` y dependía de `_aprender_mapa`; ahora
  registra `Cuadricula()` como Crafter. Los dos tests que llamaban a `Organismo._aprender_mapa` usan un ayudante
  `_aprender_mapa(mem, obs, accion)` que llama a `aprender` de los Componentes de `Cuadricula` con un contexto
  mínimo (memoria, Observación, piezas `Propiocepcion` y `Exterocepcion`, `ei["Accion"]`). Sin cambios en aserciones.

Pendiente: E3 (leer de las piezas).
