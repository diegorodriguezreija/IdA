# Reglas para agentes de IA que contribuyan a IdA

Gran parte del código de IdA se escribió con agentes de IA bajo la dirección y la revisión del autor. Estas reglas valen para cualquier agente (y persona) que proponga cambios.

## Rediseño de la base

La base (Core y sistemas S1, S2, S3) se está rediseñando. Antes de cualquier cambio, lee:

- [`docs/REDISENO_BASE.md`](docs/REDISENO_BASE.md): la referencia de diseño (24 decisiones). Da el contexto completo, aunque cada encargo implemente solo una parte.
- [`docs/PLAN_IMPLEMENTACION.md`](docs/PLAN_IMPLEMENTACION.md): qué se hace y en qué orden (preparación y bloques A a F). Cada bloque es un encargo cerrado con su objetivo, sus pasos, lo que queda fuera de alcance, su verificación y su condición de paso.

Implementa solo el bloque que te encarguen. Lo que el borrador describe para otros bloques queda fuera de alcance aunque parezca relacionado. No empieces un bloque si el anterior no cumple su condición de paso.

## No negociables

1. **No debilites los tests.** No quites palabras de `PALABRAS_DE_MUNDO` ni imports de `IMPORTS_PROHIBIDOS` en `tests/test_pureza.py`, no añadas excepciones y no relajes aserciones ni umbrales para que algo pase. Si un test falla, di qué falla y por qué.
2. **No metas conocimiento de un mundo en `ida/core/` ni en `ida/sistemas/`**, ni directamente ni con trucos que el test no ve (cadenas construidas en ejecución, imports dinámicos, umbrales afinados para un mundo). Va en `ida/mundos/<mundo>`.
3. **El mundo percibe; IdA piensa.** No mejores un mundo haciendo que su sensor calcule por el individuo (búsquedas, planes, oráculos externos). Mejora su percepción o sus componentes propios.
4. **Harness engineering: consistencia biológica sin atajos ni trucos rígidos.**
   - Las conductas adaptativas deben apoyarse en principios biológicos plausibles: mapas cognitivos/hipocampales, aliestesia homeostática, asimetrías lucha/huida reguladas por el estado somático y equipamiento, o aprendizaje de contingencias.
   - Prohibido parchear comportamientos mediante autómatas deterministas rígidos, "trampas" de juego, secuencias de acciones cableadas para un fin específico o saltos que ignoren el arbitraje del Tribunal.
   - Cualquier mecanismo orgánico candidato debe evaluarse empíricamente con mediciones repetibles con semilla antes y después. Si demuestra generalidad y rigor entre mundos, puede proponerse para su elevación al Core.
5. **No toques `ida/core/` ni `ida/sistemas/` sin permiso expreso del autor.** Si es imprescindible, en un commit propio, explicado, y comprobando que una vida con semilla da lo mismo antes y después cuando el cambio no busca cambiar la conducta. Cuenta como permiso expreso el que concede la sección «Permiso» de cada encargo de [`docs/PLAN_IMPLEMENTACION.md`](docs/PLAN_IMPLEMENTACION.md), y vale solo para los pasos de ese bloque y mientras dure su encargo. Ese permiso no cambia las reglas 1 a 3: la pureza de `ida/core/` e `ida/sistemas/` y sus tests se mantienen.
6. **Verifica antes de afirmar.** Cada afirmación sobre el código cita fichero y línea o la salida de un comando. Lo que no hayas comprobado, márcalo como no verificado.
7. **No inventes cifras, referencias ni mecanismos.** Toda cifra publicada lleva su comando, sus semillas, su número de vidas y su fecha, y se compara con la versión anterior en las mismas semillas. Publica también los resultados negativos.
8. **Un commit por cambio**, con mensaje descriptivo. Nada de `push` sin que el autor lo pida.
9. **Sin lenguaje enfático.** Describe con cifras y límites.
10. **No importes `chess` fuera de `ida/mundos/ajedrez/`** (licencia, ver [`NOTICE`](NOTICE)).
11. **Seguridad:** el mundo de archivos solo puede tocar su bioma; no amplíes esa frontera. El panel y la pila de observabilidad escuchan solo en local.

## Antes de proponer un cambio

```bash
python -m pytest -q
ruff check ida tests
mypy ida
git diff --stat -- ida/core ida/sistemas   # ¿tocaste el framework base? justifícalo
```
