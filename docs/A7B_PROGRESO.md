# A7b: Memoria por secciones con dueño (D7)

Rama `reorg/a7b-memoria`, desde `origin/reorg/componentes` (`6b7098a`).
Encargo: secciones con dueño en la Memoria (peligros → Amenaza, satisface → Apetencia, cuadricula → cuerpo,
requisitos → `Requisito`), manual y legado diferidos, escrituras delegadas con autor y test estático de dueños.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Mecanismo de secciones, con tests | Hecha | (ver git log) |
| E2 | «peligros» a Amenaza, sin `escalar()` | Pendiente | |
| E3 | «satisface» a Apetencia | Pendiente | |
| E4 | «cuadricula» al cuerpo | Pendiente | |
| E5 | `Requisito` y su sección | Pendiente | |
| E6 | Escrituras delegadas y test estático | Pendiente | |
| E7 | Especificación y documentos | Pendiente | |

### Últimas comprobaciones (E1)

```
ruff check .   All checks passed!
mypy ida       Success: no issues found in 61 source files
pytest -q      368 passed, 1 warning
equivalencia.py: 31, 32, 31h y 31h legado IDÉNTICO; minimo, archivos, crafter, ajedrez OK; EQUIVALENCIA: OK
```

## E1 · Mecanismo

- `ida/core/memoria.py`: clase `Seccion` (protocolo con métodos opcionales: `legado(ahora)`, `heredar(legado, tasa)`,
  `aplicar_manual(manual)`; atributos `activa` y `orden_legado`). Cada sección recibe el manual y el legado enteros y
  toma sus claves.
- `Memoria.registrar_seccion(nombre, dueño, seccion)` (nombre repetido → `ValueError`), `seccion(nombre)` (lectura,
  `KeyError` si el dueño no está montado), `tiene_seccion`, `dueño`, `seccion_propia(nombre, autor)` (escritura: solo
  el dueño, `PermissionError` si no).
- Manual y legado diferidos: `aplicar_manual` y `heredar` guardan el dato en `_diferido` (en orden de llegada) y lo
  entregan ya a las secciones registradas; cada sección nueva recibe al registrarse todo lo diferido, en el mismo orden
  (manual y luego legado, como en `evaluar_crafter.py` y `ejecutor.py`). Con memoria apagada no se difiere nada
  (mismas salidas tempranas de antes).
- `Memoria.legado` junta la parte del Core y la de cada sección, ordenadas por `orden_legado`.
- `Memoria.heredados`: hechos heredados, con los que toman las secciones al registrarse. `ejecutor.py` lo lee tras
  montar el Organismo (antes usaba el valor devuelto por `heredar`, que ya no incluye lo diferido).
- `Componente.seccion_memoria(perfil)` y `Cuerpo.seccion_memoria(perfil)` devuelven `(nombre, sección)` o `None`. El
  `Organismo` registra al final del montaje la del cuerpo y después las de los Componentes montados (orden de `montados`).
- `tests/test_secciones_memoria.py`: nombre repetido, diferido en orden, memoria apagada, legado por secciones,
  autor, independencia entre secciones.
