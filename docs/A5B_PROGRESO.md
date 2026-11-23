# A5b: progreso por etapas

Encargo: paso A5b de `docs/DISENO_COMPONENTES.md` (sección 5): el Core ejecuta primitivas del mundo y la traducción
intención → primitivas pasa del adaptador al Motor del cuerpo cuadrícula. Rama `reorg/a5b-primitivas`, creada desde
`origin/reorg/componentes` (643486f, con A5a fusionado).

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Contrato `primitivas`/`ejecutar_primitivas` y adaptador | BLOQUEADA (sin empezar) |
| E2 | Motor (traducción, sinergias, juicio) y Actuador por primitivas | sin empezar |
| E3 | Cuenta de primitivas, «primitivas» en la pieza Accion, especificación y documentación | sin empezar |
| E4 | Tests | sin empezar |

## Bloqueo: el objetivo no está siempre entre las piezas Exterocepcion

El encargo pide comprobar, antes de escribir el Motor, que un objetivo que hoy resuelve `_posicion` vía `_cosas()`
está siempre entre las piezas Exterocepcion del latido, y parar si no es así. No lo está:

- `MundoCrafter.observar` solo entrega las 14 primeras cosas, con los peligrosos primero y después por distancia
  (`ida/mundos/crafter.py:319-321`: `cosas.sort(...)` y `for ... in cosas[:14]`). Los peligrosos del manual estricto
  son zombi, esqueleto, flecha y lava (`crafter_manual.json:47-75`); la lava son casillas, así que puede haber muchas.
- `MundoCrafter._posicion` resuelve los id sin coordenadas (criaturas y plantas, `vaca_3`) buscando en todo
  `_cosas()`, sin el corte (`crafter.py:402-409`). Con 6 o más peligrosos a la vista, una vaca o planta vecina puede
  quedar fuera de las 14 (en distancia ≤ 1 caben como mucho 8 cosas) y aun así `_posicion` la encuentra.
- Hay al menos una fuente de candidatos que no pasa por las piezas Exterocepcion: S3 propone COGER sobre el id de
  `cuerpo["delante"]` (`ida/sistemas/s3.py:983-989`), que `_delante` calcula sobre el mundo entero
  (`crafter.py:300-313`). En ese caso concreto la regla `any(peligro > 0)` de `s3.py:981` lo frena si los peligrosos
  ya tienen `peligro` > 0; eso depende de S2/S3, no del adaptador (no verificado en todos los casos). No se revisaron
  todas las demás fuentes de objetivos (planes de S3, estrategias).

Medición (23/11/2026, sonda en el scratchpad que envuelve `observar` y `_posicion` sin cambiar nada,
`evaluar_crafter.py --pasos 3000 --vista oficial --sin-herencia --manual estricto --plazo-logico 40`, semillas 31 y 32,
2 vidas): 2540 y 2518 llamadas a `_posicion`, 189 y 125 con id sin coordenadas, **0** resueltas fuera de las piezas
(ni vecinas ni no vecinas). La equivalencia no lo detectaría, pero el código no lo garantiza.

Opciones para el autor (no implementadas):
1. El Motor busca también la casilla de delante (`cuerpo["delante"]` de la Propiocepcion «yo», posición = aquí +
   orientación). Cubre la fuente de `s3.py:989`; las demás quedan sin garantía.
2. El adaptador añade a la percepción en bruto la posición de las criaturas y plantas a la vista (p. ej.
   `cuerpo["objetos"]`: id → posición, sin valorar), y el Motor la usa si el id no está en Exterocepcion. Habría que
   comprobar que nadie itera `cuerpo` de forma que cambie la conducta (no verificado).
3. Quitar el corte de 14: cambia la percepción y la conducta; sería fase B.
4. Aceptar la diferencia como teórica y documentarla (0 casos en las 2 vidas de la equivalencia).

Pendiente: decisión del autor. No hay cambios de código en la rama.
