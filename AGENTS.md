# Reglas para agentes de IA que contribuyan a IdA

Gran parte del código de IdA se escribió con agentes de IA bajo la dirección y la revisión del autor. Estas reglas valen para cualquier agente (y persona) que proponga cambios.

## No negociables

1. **No debilites los tests.** No quites palabras de `PALABRAS_DE_MUNDO` ni imports de `IMPORTS_PROHIBIDOS` en `tests/test_pureza.py`, no añadas excepciones y no relajes aserciones ni umbrales para que algo pase. Si un test falla, di qué falla y por qué.
2. **No metas conocimiento de un mundo en `ida/core/` ni en `ida/sistemas/`**, ni directamente ni con trucos que el test no ve (cadenas construidas en ejecución, imports dinámicos, umbrales afinados para un mundo). Va en `ida/mundos/<mundo>`.
3. **El mundo percibe; IdA piensa.** No mejores un mundo haciendo que su sensor calcule por el individuo (búsquedas, planes, oráculos externos). Mejora su percepción o sus componentes propios.
4. **No toques `ida/core/` ni `ida/sistemas/` sin permiso expreso del autor.** Si es imprescindible, en un commit propio, explicado, y comprobando que una vida con semilla da lo mismo antes y después cuando el cambio no busca cambiar la conducta.
5. **Verifica antes de afirmar.** Cada afirmación sobre el código cita fichero y línea o la salida de un comando. Lo que no hayas comprobado, márcalo como no verificado.
6. **No inventes cifras, referencias ni mecanismos.** Toda cifra publicada lleva su comando, sus semillas, su número de vidas y su fecha, y se compara con la versión anterior en las mismas semillas. Publica también los resultados negativos.
7. **Un commit por cambio**, con mensaje descriptivo. Nada de `push` sin que el autor lo pida.
8. **Sin lenguaje enfático.** Describe con cifras y límites.
9. **No importes `chess` fuera de `ida/mundos/ajedrez/`** (licencia, ver [`NOTICE`](NOTICE)).
10. **Seguridad:** el mundo de archivos solo puede tocar su bioma; no amplíes esa frontera. El panel y la pila de observabilidad escuchan solo en local.

## Antes de proponer un cambio

```bash
python -m pytest -q
ruff check ida tests
mypy ida
git diff --stat -- ida/core ida/sistemas   # ¿tocaste el framework base? justifícalo
```
