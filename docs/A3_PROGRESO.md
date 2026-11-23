# A3: progreso por etapas

Encargo: paso A3 de `docs/DISENO_COMPONENTES.md` (preatención, plasticidad, regulación; `Amenaza` sustituye a
`ida/core/peligro.py`). Rama `reorg/a3-preatencion`, creada desde `origin/reorg/componentes` (4ee65c2). Etapas, en
orden, cada una en verde y con «EQUIVALENCIA: OK» por sí sola:

| Etapa | Qué | Estado |
|---|---|---|
| E1 | Regulación (punto 5) | HECHA |
| E2 | Gancho de plasticidad (punto 4) | pendiente |
| E3 | Mecanismo de preatención y Saliencia (puntos 1 y 2) | pendiente |
| E4 | Amenaza (punto 3) | pendiente |
| E5 | Especificación, test del mapa y tests restantes (punto 6) | pendiente |

El hash de cada etapa es el del commit «A3 E<n>: ...» (`git log --oneline --grep "A3 E"`); el de una etapa se anota
en la siguiente.

Control antes de empezar (árbol 4ee65c2): `herramientas/equivalencia.py` → `EQUIVALENCIA: OK`.

## E1 · Regulación

Estado: HECHA. Commit: «A3 E1: Regulacion sustituye a Marcapasos (D12)».

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
