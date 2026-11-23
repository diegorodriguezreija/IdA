# A5a: progreso por etapas

Encargo: paso A5a de `docs/DISENO_COMPONENTES.md` (sección 5): primer cuerpo, la familia cuadrícula (D10). Rama
`reorg/a5a-cuerpo`, creada desde `origin/reorg/componentes` (6d4441b, con A3 fusionado). Cada etapa en verde y con
«EQUIVALENCIA: OK» por sí sola.

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Contrato `Cuerpo`, montaje y tests de registro (puntos 1, 2 y parte del 9) | HECHA |
| E2 | `Cuadricula`, `ModeloDirecto` y `MapaLocal`, mismo punto, registro de Crafter (puntos 3, 4 y 6) | pendiente |
| E3 | Leer piezas en lugar de la Observación (punto 5) | pendiente |
| E4 | Herramienta, especificación y tests restantes (puntos 7, 8 y 9) | pendiente |

El hash de cada etapa es el de su commit «A5a E<n>: ...» (`git log --oneline --grep "A5a E"`); se anota en la etapa
siguiente.

## E1 · Contrato Cuerpo y montaje

Estado: HECHA. Commit: «A5a E1: contrato Cuerpo y montaje de sus Componentes (D10)».

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

Pendiente: E2.
