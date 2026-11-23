# A7a: Preparación antes de reorganizar la memoria (D11, D13)

Rama `reorg/a7a-preparacion`, desde `origin/reorg/componentes` (`b3b6570`).
Encargo: equivalencia con herencia y legado frente a eaeadaa; Peticion a Reaccionar en S1 y S2; cola de memoria a corto plazo.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Equivalencia con herencia y línea base de legado | Hecha | `78ee258` |
| E2 | Peticion a Reaccionar (D11) | Hecha | `ce3f314` |
| E3 | Memoria a corto plazo (D13) | Hecha | ver `git log` |

### Últimas comprobaciones (E3)

```
ruff check .          All checks passed!
mypy ida              Success: no issues found in 61 source files
pytest -q             362 passed, 1 warning in 95.60s
equivalencia.py:
  31: IDÉNTICO
  32: IDÉNTICO
  31h: IDÉNTICO
  31h legado: IDÉNTICO
  minimo: OK
  archivos: OK
  crafter: OK
  ajedrez: OK
  EQUIVALENCIA: OK
```

## E1 · Equivalencia con herencia y línea base de legado

- **Medición con herencia en equivalencia:**
  - `herramientas/equivalencia.py` incorpora una tercera medición de Crafter: semilla 31, 3000 pasos, plazo lógico 40, con linaje/herencia (sin `--sin-herencia`), acumulando 13 vidas.
  - Se añade la opción `--solo-faltan` a `--base` para generar solo los ficheros de base inexistentes (`base_herencia_31.json`) desde `eaeadaa` en worktree temporal sin tocar `base_31.json` ni `base_32.json`.
- **Captura y verificación del legado:**
  - `herramientas/evaluar_crafter.py` incorpora la opción `--legado-salida <fichero>` que vuelca la lista secuencial de `memoria.legado(org.ciclo)` de cada vida registrada.
  - Se verifica que `--legado-salida` no altera la conducta ni el JSON principal de `evaluar_crafter.py`.
  - Generada la referencia `datos/equivalencia/legado_herencia_31.json` (13 legados) en el commit base `b3b6570` (`origin/reorg/componentes`), cuya conducta es idéntica a `eaeadaa`.
  - Anotada la procedencia del legado en `datos/equivalencia/base_ref.txt`.
  - `equivalencia.py` compara `base_herencia_31.json` y `legado_herencia_31.json` («31h: IDÉNTICO» y «31h legado: IDÉNTICO»).

## E2 · Peticion a Reaccionar (D11)

- Se comprueba que `Peticion` únicamente lee `ctx.onda.estrategias` y despacha a `Definicion.pedir(ctx, p)` (implementado solo en `Proteger` y `Afrontar`), sin leer propuestas en `acc`, piezas `Accion` ni piezas `Expectativa`.
- En `ida/sistemas/s1.py` y `ida/sistemas/s2.py`:
  - `Peticion(catalogo)` pasa del módulo `Actuar` al final del módulo `Reaccionar` (después de `Estrategia`).
  - Actualizadas las tablas de los docstrings de ambos sistemas.
- En `doc-repositorio/componentes.toml`:
  - Actualizado `Peticion` de S1 y S2 con `hoy = "S1.Reaccionar"` y `hoy = "S2.Reaccionar"`, retirando `paso = "A7"`.
- Regenerado `doc-repositorio/06_MAPA_DE_COMPONENTES.md` mediante `herramientas/mapa_componentes.py --escribir`.

## E3 · Memoria a corto plazo (D13)

- En `Perfil` (`ida/core/mundo.py`): se añade el parámetro `corto_plazo: int = 8` con valor por defecto 8.
- En `Contexto` (`ida/core/arquitectura.py`): se añade el campo `corto_plazo: Tuple[Any, ...] = ()` (secuencia inmutable, de la más antigua a la más reciente).
- En `Organismo` (`ida/core/latido.py`):
  - Inicializa una cola circular `self._corto_plazo: deque[Any] = deque(maxlen=max(0, self.perfil.corto_plazo))`.
  - Expone la propiedad `corto_plazo` como tupla inmutable.
  - Al instanciar `Contexto` en `latir()`, pasa `corto_plazo=tuple(self._corto_plazo)`.
  - Al cerrar la onda en `latir()`, guarda una copia inmutable del `ef` (`MappingProxyType` multinivel) con las piezas que contienen `tipo`, `id`, `arousal` y `carga`.
- En `tests/test_corto_plazo.py`:
  - Se verifica que el valor por defecto en `Perfil` es 8.
  - Se verifica con N=3 y N=4 que la cola desborda correctamente respetando el tamaño máximo.
  - Se comprueba el orden estricto de la onda más antigua a la más reciente.
  - Se verifica la inmutabilidad de la tupla y de los mapeos `MappingProxyType`.
  - Se verifica que cada pieza retiene sus atributos identificativos (`tipo`, `id`, `arousal`, `carga`).


