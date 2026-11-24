# A8: Cierre de la fase A (D8, D5, D3, D15, D17)

Rama `reorg/a8-cierre`, desde `origin/reorg/componentes` (`c6051a4`).
Paso A8: cerrar la fase A con tests de los criterios (D8, D5), inventario y paso a Perfil.escala de las constantes de escala,
informe de conocimiento del mundo extendido con `--latidos` y documentación al día. NO cambia la conducta.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Tests de criterios D8 y D5 (`tests/test_criterios.py`) | Hecha | Ver git log |
| E2 | Constantes y `Perfil.escala` | Pendiente | |
| E3 | Informe de conocimiento con `--latidos` | Pendiente | |
| E4 | Documentación al día y cierre de fase A | Pendiente | |

### Comprobaciones E1 (24/11/2026)

```
ruff check ida tests   All checks passed!
mypy ida               Success: no issues found in 159 source files
pytest -q              938 passed, 1 warning
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

## E1 · Tests de criterios (D8, D5)

- `tests/test_criterios.py`: análisis estático (`ast`) sobre:
  - **Estrategias:** todas las clases de las carpetas `reaccionar/estrategias/` de `ida/s1`-`s3` y de `ida/mundos/*`. Ninguna lee `observacion`, el mundo (`mundo`, `.env`, `_world`) ni un reloj del mundo (`.t` de un mundo, `paso` del mundo, `reloj`, `hora`).
  - **Componentes fuera de core/sentir:** ningún Componente fuera de `ida/core/sentir` lee `observacion`, el mundo ni un reloj del mundo.
  - **Preatención (D5):** los Componentes preatentivos (`Saliencia`, `Amenaza`, `ValoracionCrafter`) tienen `preatentivo = True` y residen en módulos de una carpeta `sentir/`.
  - **Sustitución de test_crafter_no_escribe_conducta:** se retiró de `tests/test_defensa.py` y se incorporó a `tests/test_criterios.py`, conservando las aserciones de que el adaptador de Crafter no define clases de estrategia y de que Crafter solo registra `SalirDelRecinto` en S1.
- **Casos xfail:** Ninguno (0 violaciones encontradas).
