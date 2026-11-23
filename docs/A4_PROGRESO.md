# A4: progreso por etapas

Encargo: paso A4 de `docs/DISENO_COMPONENTES.md` (sección 5, D4 y D5): la Observación solo la leen los sensores del
Core, y la valoración que hacía el adaptador de Crafter (`nutritivo`, `recurso` y `novedad`) pasa al organismo, como
Componente preatentivo de Crafter (`ValoracionCrafter`). Rama `reorg/a4-observacion`, creada desde
`origin/reorg/componentes` (42e4df9, con A5b fusionado).

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Datos en bruto nuevos en el adaptador (`madura`, `vista` ampliada) | HECHA |
| E2 | `ValoracionCrafter` y orden de la preatención (`Saliencia` la última) | HECHA |
| E3 | El adaptador deja de valorar y de apuntar visitas; `rasgos_declarados` vacío | pendiente |
| E4 | Lectores a piezas y `ctx.observacion = None` tras Core · Sentir | pendiente |
| E5 | Especificación, herramienta, documentación y tests restantes | pendiente |

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
