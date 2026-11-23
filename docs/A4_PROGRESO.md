# A4: progreso por etapas

Encargo: paso A4 de `docs/DISENO_COMPONENTES.md` (sección 5, D4 y D5): la Observación solo la leen los sensores del
Core, y la valoración que hacía el adaptador de Crafter (`nutritivo`, `recurso` y `novedad`) pasa al organismo, como
Componente preatentivo de Crafter (`ValoracionCrafter`). Rama `reorg/a4-observacion`, creada desde
`origin/reorg/componentes` (42e4df9, con A5b fusionado).

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Datos en bruto nuevos en el adaptador (`madura`, `vista` ampliada) | HECHA |
| E2 | `ValoracionCrafter` y orden de la preatención (`Saliencia` la última) | pendiente |
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
