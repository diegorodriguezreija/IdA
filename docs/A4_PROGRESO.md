# A4: progreso por etapas

Encargo: paso A4 de `docs/DISENO_COMPONENTES.md` (sección 5, D4 y D5): la Observación solo la leen los sensores del
Core, y la valoración que hacía el adaptador de Crafter (`nutritivo`, `recurso` y `novedad`) pasa al organismo, como
Componente preatentivo de Crafter (`ValoracionCrafter`). Rama `reorg/a4-observacion`, creada desde
`origin/reorg/componentes` (42e4df9, con A5b fusionado).

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Datos en bruto nuevos en el adaptador (`madura`, `vista` ampliada) | HECHA |
| E2 | `ValoracionCrafter` y orden de la preatención (`Saliencia` la última) | HECHA |
| E3 | El adaptador deja de valorar y de apuntar visitas; `rasgos_declarados` vacío | HECHA |
| E4 | Lectores a piezas y `ctx.observacion = None` tras Core · Sentir | HECHA |
| E5 | Especificación, herramienta, documentación y tests restantes | HECHA |

El hash de cada etapa es el de su commit «A4 E<n>: ...» (`git log --oneline --grep "A4 E"`).

## E1 · Datos en bruto en el adaptador

Estado: HECHA.

Comprobación (última línea de cada una): `All checks passed!` · `Success: no issues found in 49 source files` ·
`320 passed, 1 warning in 39.96s` · `EQUIVALENCIA: OK`.

Decisiones:
- Cada Entidad de una planta lleva `datos["madura"] = bool(obj.ripe)` (después de `pos`).
- Forma de `cuerpo["vista"]` (transitoria hasta B5): `{id: {"clase": str, "pos": [x, y]}}`, con `"madura": bool`
  añadido si la clase es `planta`, para cada objeto de `_cosas()` (criaturas y plantas, sin el corte de 14). Antes era
  `{id: [x, y]}`: `MotorCuadricula.posicion` lee ahora `vista[id]["pos"]` (y `tests/test_motor.py` monta la forma nueva).
- Los materiales a la vista no se duplican en `vista`: `cuerpo["casillas"]` ya da su clase por posición (por ejemplo,
  `agua`). Diferencia teórica: `casillas` también nombra los suelos (`hierba`, `arena`, `camino`) y la casilla propia,
  que `_cosas()` no incluía. La casilla propia no aporta al gradiente (la fórmula exige acercarse); un suelo solo
  aportaría si el manual lo declarase NUTRITIVO, y ningún manual lo hace (estricto y ampliado: `agua`, `planta`, `vaca`).
- `deseables` de `observar` se reproduce así: posiciones de `casillas` cuya clase es nutritiva, más los objetos de
  `vista` cuya clase es nutritiva y que no lleven `madura = False`.

Pendiente: nada de E1.

## E2 · ValoracionCrafter y orden de la preatención

Estado: HECHA.

Comprobación (última línea de cada una): `All checks passed!` · `Success: no issues found in 50 source files` ·
`325 passed, 1 warning in 51.86s` · `EQUIVALENCIA: OK`.

Decisiones:
- `ida/mundos/crafter_valoracion.py`: `ValoracionCrafter(nutritivas, utiles, cuerpo, valor_nutritivo, valor_recurso,
  alcance_gradiente, olvido_novedad)`, preatentivo, tipo `Exterocepcion`. Fichero propio con el prefijo `crafter_` para
  que `herramientas/conocimiento_mundo.py` lo cuente como de Crafter sin cambiarla. Crafter lo registra en
  `S1.Sentir` (`añade`) con sus clases NUTRITIVO y UTIL, `NUTRITIVO_MANUAL`, `RECURSO_MANUAL`, `4 * radio` y el mismo
  objeto `Cuadricula` que registra como cuerpo (así lee la cuenta del mismo Motor que usan los Actuadores).
  `olvido_novedad` = 50 (el divisor de antes), por defecto.
- Orden de lo que hace en cada latido: (a) si la Accion de `ei` fue MOVER con `primitivas` no vacías, apunta
  `visitas[posición actual de «yo»] = cuenta`, donde cuenta = `sum(Motor.ejecutadas.values())`; (b) escribe los rasgos;
  (c) reconstruye cada dict en el orden de antes (`ORDEN_COSA`, `ORDEN_LUGAR`) y deja después lo demás (`peligro`).
- Una cosa es nutritiva si su clase es NUTRITIVO y no lleva `madura = False` (solo las plantas llevan `madura`): igual
  que la regla de antes (`planta` solo madura). Lugar = pieza con `lugar >= 0,5`.
- Orden de la preatención: atributo `Componente.integrador` (False por defecto; `Saliencia` lo pone a True). El montaje
  (`Organismo.__init__`) ordena la preatención con `sorted(..., key=integrador)`, estable: los integradores al final,
  el resto en su orden de registro. Resultado en Crafter: `Amenaza`, `ValoracionCrafter`, `Saliencia`. Línea literal
  añadida a D5.
- Adelantado de E5 por necesidad: `ValoracionCrafter` en `doc-repositorio/componentes.toml` (`hoy = "S1.Sentir"`,
  `hoy_en = ["crafter"]`, sin `paso`, notas de ValoracionCrafter y MapaLocal) y mapa regenerado. Sin ello,
  `test_mapa_componentes` falla en cuanto Crafter registra el Componente.
- Comprobación de la cuenta: `tests/test_valoracion_crafter.py` comprueba en cada latido (semillas 3 y 31, hasta 500
  latidos) `sum(Motor.ejecutadas.values()) == mundo.t`, y que los rasgos de las piezas tras la preatención son
  idénticos (`==`, sin tolerancia) a los que entrega el adaptador, con el orden de claves de antes.

Pendiente: nada de E2.

## E3 · El adaptador deja de valorar

Estado: HECHA.

Comprobación (última línea de cada una): `All checks passed!` · `Success: no issues found in 50 source files` ·
`325 passed, 1 warning in 52.11s` · `EQUIVALENCIA: OK`.

Antes de quitar nada se pasó una sonda (scratchpad, no queda en el código) sobre la configuración de la equivalencia
(`evaluar_crafter.py --pasos 3000 --vista oficial --sin-herencia --manual estricto --plazo-logico 40`, semillas 31 y
32, 23/11/2026): en cada latido, `sum(Motor.ejecutadas) == mundo.t` y rasgos de las piezas tras la preatención iguales
(y en el mismo orden) a los del adaptador. Resultado: 3000 latidos por semilla, 0 fallos de cuenta, 0 de rasgos.

Decisiones:
- `ida/mundos/crafter.py`: fuera `self.visitas`, `_nutritivo`, `deseables` y el cálculo de `nutritivo`, `recurso` y
  `novedad`. Entidades: `proximidad` y `agente`; lugares: `lugar` y `proximidad`. `rasgos_declarados = ()`.
  `NUTRITIVO_MANUAL` y `RECURSO_MANUAL` se quedan en el adaptador: son las escalas que el registro pasa a
  `ValoracionCrafter`.
- `ejecutar_primitivas(primitivas, intencion=None)`: el parámetro se queda, sin usar. Quitarlo cambiaría el contrato
  de `Mundo` (`ida/core/mundo.py`) y la llamada del `Actuador` (`ida/core/sentidos.py`), que también usan los demás
  mundos; queda dicho en su docstring.
- Tests: `tests/test_valoracion_crafter.py` compara ahora con `_valoracion_antigua`, copia literal de la valoración y
  las visitas del adaptador anterior (el espía se instala antes de montar el Organismo: los Actuadores guardan
  `ejecutar_primitivas` al construirse; con el espía puesto después, el test falló en `novedad`, lo que muestra que
  detecta unas visitas mal apuntadas). `tests/test_crafter.py` comprueba que la Observación va en bruto y
  `rasgos_declarados == ()`. `tests/test_paso0.py::test_crafter_el_nutritivo_es_perceptivo_y_constante` lee el
  `nutritivo` de las piezas tras la preatención de un Organismo, con la misma aserción. `tests/test_motor.py` deja de
  comparar `visitas` del adaptador (ya no existen; las compara `test_valoracion_crafter.py`).

Pendiente: nada de E3.

## E4 · Lectores a piezas y `ctx.observacion = None` tras Sentir

Estado: HECHA.

Comprobación (última línea de cada una): `All checks passed!` · `Success: no issues found in 50 source files` ·
`328 passed, 1 warning in 55.91s` · `EQUIVALENCIA: OK`.

Lectores cambiados (R0, sección B, con las líneas de hoy):
- `ida/core/arquitectura.py`: `Contexto.ubicacion()` lee `ubicacion` de la pieza Propiocepcion «yo» (`""` si no hay).
  `onda.ev` no cobra amplitud ni cuenta operaciones (`ida/core/onda.py:353`), así que leer piezas no cambia el plazo.
- `ida/sistemas/s2.py` (6 lecturas), `ida/sistemas/s3.py` (`acercarse_a_clase`, `_pos_propia`),
  `ida/sistemas/proteger.py` (`posicion`, `reactiva`) y `ida/mundos/archivos.py` (2 lecturas en sus Componentes, que
  R0 no listaba porque solo miró core y sistemas): `ctx.ubicacion()`.
- `ida/core/latido.py`: `_aprender` (ubicación y clases al alcance, de piezas Exterocepcion), `_situacion_inventario`
  (inventario y `delante` de «yo»; clases al alcance de las Exterocepcion), `_distancias(ubicacion, piezas)` (clase,
  rasgos y `datos["pos"]` de las piezas) y `_episodio` (ubicación de «yo»).
- Excepción admitida, comentada en `latir`: la sincronización del soma con `obs.vitales` y `obs.dormido`, antes de la
  regulación. Tras `self.sentir.ejecutar(ctx)`, `ctx.observacion = None`; la referencia `obs` local de `latir` es la
  que se queda el Organismo.

Decisiones:
- `Propiocepcion` pone `inventario` en «yo» solo si `obs.inventario is not None`. Antes ponía `{}` si el mundo no lo
  tenía, y `_situacion_inventario` distinguía con `obs.inventario is None` (mundos sin inventario: `None`). Sin la clave
  se conserva esa distinción. Lectores de `inventario` en «yo» comprobados, todos toleran que falte:
  `ida/sistemas/amenaza.py:488` (`or {}`), `proteger.py:72` y `s3.py:481` (`or {}`), `s1.py:278` (`.get(..., {})`).
- `_episodio`: `recordar_lugar` se llamaba si `ctx.observacion is not None`; ahora, si hay pieza «yo». Las dos se dan
  siempre en un latido (el mundo siempre observa y la Propiocepcion siempre emite).
- Tests: los `ctx` simulados de `tests/test_deuda14.py` y `tests/test_planificador.py` exponen `ubicacion()` en vez de
  `observacion`; `tests/test_preatencion.py` compara Amenaza con la Observación capturada (y comprueba que
  `ctx.observacion` es None en la preatención). Nuevo `tests/test_observacion_sensores.py`: en mínimo y Crafter, ningún
  Componente montado fuera de los sensores ve la Observación (con la línea de la garantía comentada, falla: comprobado a
  mano y restaurado), y `inventario` en «yo» solo si el mundo lo tiene.

Pendiente: nada de E4.

## E5 · Especificación, herramienta, documentación y tests

Estado: HECHA.

Comprobación (última línea de cada una): `All checks passed!` · `Success: no issues found in 50 source files` ·
`329 passed, 1 warning in 55.74s` · `EQUIVALENCIA: OK`.

Decisiones:
- Especificación (`doc-repositorio/componentes.toml`): hecha en E2 (ver allí); sin cambiar `destino`, `clase`,
  `registran` ni `decision`. Mapa regenerado con `--escribir` (sin cambios desde E2).
- `herramientas/conocimiento_mundo.py`: cada Componente que registra el mundo se muestra con «(preatentivo)» si lo es y
  con su conocimiento declarado si expone `conocimiento_declarado()`. `ValoracionCrafter.conocimiento_declarado()` da
  las clases NUTRITIVO y UTIL que le pasa el registro. Salida para Crafter: `S1.Sentir: añade: [ValoracionCrafter
  (preatentivo) {NUTRITIVO: agua, planta, vaca; UTIL: arbol, carbon, diamante, hierro, horno, mesa, piedra}]` y el
  fichero `ida/mundos/crafter_valoracion.py` (103 líneas no vacías) en el total de Crafter.
- `docs/DISENO_COMPONENTES.md`: línea literal de D5 (en E2) y una fila en el registro de cambios.
- Test nuevo en `tests/test_valoracion_crafter.py`: el registro de Crafter monta `ValoracionCrafter` con las clases del
  manual y el mismo cuerpo (Motor) que el Organismo, y el informe de conocimiento lo muestra.

Pendiente para el autor (no implementado, fuera del encargo):
- D4 dice que la novedad la calculará el organismo «con su propia memoria de visitas (`MapaLocal`)». Por el encargo,
  las visitas las lleva `ValoracionCrafter` (y así lo dicen las notas de la especificación). Si se quiere, ajustar esa
  frase de D4.
- `_situacion_inventario` y `_distancias` leen las piezas Exterocepcion en el momento de actuar (tras S1-S3). Hoy nadie
  añade piezas a ese canal fuera de Core · Sentir ni cambia `lugar` o `proximidad` (la equivalencia da OK); si un
  Componente futuro lo hiciera, cambiaría lo que ven.

El paso A4 queda listo para revisión; no se ha abierto PR.
