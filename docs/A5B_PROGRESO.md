# A5b: progreso por etapas

Encargo: paso A5b de `docs/DISENO_COMPONENTES.md` (sección 5): el Core ejecuta primitivas del mundo y la traducción
intención → primitivas pasa del adaptador al Motor del cuerpo cuadrícula. Rama `reorg/a5b-primitivas`, creada desde
`origin/reorg/componentes` (643486f, con A5a fusionado).

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Contrato `primitivas`/`ejecutar_primitivas`, adaptador y `vista` | HECHA |
| E2 | Motor (traducción, sinergias, juicio) y Actuador por primitivas | sin empezar |
| E3 | Cuenta de primitivas, «primitivas» en la pieza Accion, especificación y documentación | sin empezar |
| E4 | Tests | sin empezar |

El hash de cada etapa es el de su commit «A5b E<n>: ...» (`git log --oneline --grep "A5b E"`).

## Bloqueo (resuelto): el objetivo no está siempre entre las piezas Exterocepcion

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

Decisión del autor (23/11/2026): opción 2, con la clave `cuerpo["vista"]` = {id: [x, y]} (lo que se ve, no partes del
cuerpo), transitoria hasta B5 (quitar el corte de 14, apuntado en `docs/DISENO_COMPONENTES.md`). El Motor resuelve en
este orden: coordenadas en el id; pieza Exterocepcion con ese id; `vista` de la Propiocepcion «yo»; si no, sin
primitivas. La sonda no queda en el código.

## E1 · Contrato y adaptador

Estado: HECHA (commit «A5b E1: contrato de primitivas y adaptador de Crafter»).

Comprobación previa (punto 3 de la decisión): qué recorre `obs.cuerpo` o `carga["cuerpo"]` de forma genérica.
`git grep -n -E '\.cuerpo|\["cuerpo"\]|get\("cuerpo"\)' -- ida herramientas tests` y búsqueda de copias de la
carga «yo» y de iteraciones de `reactiva.ev`:
- `ida/core/sentidos.py:45`: `Propiocepcion` copia `obs.cuerpo` entero a la carga «yo» (es el transporte; no decide).
- Lecturas por clave: `ida/core/latido.py:389` (`delante`), `ida/cuerpos/cuadricula/situacion.py:30-36` (`casillas`,
  `orientacion`), `ida/sistemas/amenaza.py:483` (`casillas`), `ida/sistemas/proteger.py:67` (`orientacion`),
  `ida/sistemas/s3.py:486` (`delante`).
- Copias de la carga «yo» entera: `proteger.py:59` y `s3.py:476` (`_yo`); sus usos solo leen `cuerpo.orientacion`,
  `cuerpo.delante` e `inventario` (`proteger.py:67,72`, `s3.py:481,486`).
- `ida/core/latido.py:493` (`_memoria_rapida`) recorre `reactiva.ev` pero excluye `Propiocepcion` y no copia cargas;
  `latido.py:477,507,517` solo leen el arousal y excluyen los canales de los sensores; `ida/consola.py:42` cuenta piezas.
- Tests: `tests/test_cuadricula.py:29` y `tests/test_proteger.py:173` leen o copian `obs.cuerpo` para montar casos.
Nada itera las claves de `cuerpo` ni lo pasa entero a algo que decida: la clave nueva no cambia la conducta (y la
equivalencia da OK).

Decisiones:
- `ida/core/mundo.py`: `Efecto.medidas` (dict, vacío por defecto); `Mundo.primitivas()` (None por defecto) y
  `Mundo.ejecutar_primitivas(primitivas, intencion=None)`. `Mundo.ejecutar` deja de ser abstracto (por defecto lanza
  `NotImplementedError`): Crafter lo pierde en E2 y los mundos sin cuerpo lo siguen implementando.
- `ida/mundos/crafter.py`: `primitivas()` = `constants.actions`; `ejecutar_primitivas` mide antes de la primera y después
  de la última (mismo `_efecto`, ahora siempre con `exito=True`), `medidas = {"inventario_antes", "inventario_despues"}`
  (inventario completo del juego, con salud, comida, bebida y energía). `intencion` solo se lee para las visitas
  (`# A4:`), cuando es MOVER y hubo primitivas, como antes. `_interactuar` desaparece. `observar` añade
  `cuerpo["vista"]` (`# B5:`).
- `ejecutar` queda en E1 como función de transición sobre `ejecutar_primitivas` (misma traducción y mismo juicio);
  E2 la quita.

Pendiente: E2 a E4.
