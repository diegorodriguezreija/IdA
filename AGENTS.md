# Reglas para agentes de IA que contribuyan a IdA

Gran parte del código de IdA se escribió con agentes de IA bajo la dirección y la revisión del autor. Estas reglas valen para cualquier agente (y persona) que proponga cambios.

## Rediseño de la base

La base (Core y sistemas S1, S2, S3) se está rediseñando. Antes de cualquier cambio, lee:

- [`docs/REDISENO_BASE.md`](docs/REDISENO_BASE.md): la referencia de diseño (24 decisiones). Da el contexto completo, aunque cada encargo implemente solo una parte.
- [`docs/PLAN_IMPLEMENTACION.md`](docs/PLAN_IMPLEMENTACION.md): qué se hace y en qué orden (preparación y bloques A a F). Cada bloque es un encargo cerrado con su objetivo, sus pasos, lo que queda fuera de alcance, su verificación y su condición de paso.

Implementa solo el bloque que te encarguen. Lo que el borrador describe para otros bloques queda fuera de alcance aunque parezca relacionado. No empieces un bloque si el anterior no cumple su condición de paso.

Los bloques A a F están terminados. Donde [`docs/DISENO_COMPONENTES.md`](docs/DISENO_COMPONENTES.md) decide algo distinto, manda ese documento.

## Fase actual: reorganización por Componentes

Desde el 22/11/2026 el trabajo sigue [`docs/DISENO_COMPONENTES.md`](docs/DISENO_COMPONENTES.md) (decisiones D1 a D17) y su plan (fases A y B). La etapa en la que la base estaba congelada y solo se tocaba `ida/mundos/` terminó con la fase de generalización de Crafter.

- **El mapa de Componentes es la especificación:** [`doc-repositorio/componentes.toml`](doc-repositorio/componentes.toml) dice dónde debe vivir cada Componente (`destino`) y dónde está hoy (`hoy`); `tests/test_mapa_componentes.py` comprueba que el código coincide con `hoy` en cada mundo.
  - Si mueves, añades o quitas un Componente o una estrategia, actualiza `hoy` (y `hoy_en`, `paso`) en el mismo PR y regenera el documento: `.venv\Scripts\python.exe herramientas/mapa_componentes.py --escribir`.
  - **No cambies `destino`, `clase`, `registran` ni `decision`** sin una decisión nueva o modificada en `docs/DISENO_COMPONENTES.md`, aprobada por el autor. Si el código no puede llegar al destino, para y explica por qué.
  - Nunca cambies la especificación para que pase un test.
- **Ramas de la reorganización:** todo paso sale de `reorg/componentes` y su PR va contra `reorg/componentes`, **nunca contra `main`**. `main` es la referencia fija de la Score (`crafter-general-v4`) hasta que el autor decida fusionar la reorganización completa. No hagas push ni a `main` ni a `reorg/componentes`: sube solo la rama de tu paso.
- **Implementa solo el paso que te encarguen** (A1, A2...). Cada encargo dice qué partes de la base puede tocar; ese es el permiso expreso del no negociable 5.
- **Fase A: mismo resultado.** Con `--plazo-logico 40`, el JSON de `evaluar_crafter.py` (3000 pasos, semillas 31 y 32) debe ser idéntico al de `main`, `invariancia.py` debe dar OK y los tests deben pasar. Si algo cambia, para y explica por qué antes de seguir.
- **Fase B: cada cambio de conducta, por separado y medido** con el criterio de no inferioridad de D17, fijado antes de medir.
- **Componentes de mundo:**
  - se declaran en el registro del mundo (`añade` o `sustituye`), nunca por el nombre de un fichero;
  - pueden emitir y modificar piezas de un tipo de la base si son de ese tipo (propiedad por tipo);
  - solo los Componentes `Accion` proponen acciones.
- **La Observación solo la leen los sensores del Core** y los del mundo en `core/sentir/`. Los datos en bruto no llevan valoración: `nutritivo`, `peligro`, `recurso` y `novedad` los interpreta el organismo. Si un mundo los entrega hechos, lo declara en `Perfil.rasgos_declarados`.
- **Preatención:** solo modifica las piezas de los sensores, no crea piezas, no propone acciones y su coste es lineal en lo percibido.
- **Estrategias:** se activan por piezas de la Onda (nunca por el paso, el reloj ni el estado interno del mundo), pueden omitirse, compiten en el Tribunal y sus umbrales son parámetros o se aprenden. Pueden tener fases con esas condiciones.
- **Las constantes de escala** van en el `Perfil` del mundo o en los parámetros de su cuerpo, no en los Componentes generales.
- **Lo aprendido es de cada mundo:** no pasa de un mundo a otro.
- **Mecanismos de memoria (bloques E y F):** siguen apagados por defecto; un mundo los activa en su `Perfil` si un benchmark pareado demuestra su valor ([`docs/VEREDICTO_E_F.md`](docs/VEREDICTO_E_F.md)).
- Mientras se mide, en la máquina no corre ningún otro proceso de IdA (ni tests ni pruebas rápidas). Cada medición registra sus latidos cortados.
- Los agentes no instalan paquetes sin permiso del autor.

## No negociables

1. **No debilites los tests.** No quites palabras de `PALABRAS_DE_MUNDO` ni imports de `IMPORTS_PROHIBIDOS` en `tests/test_pureza.py`, no añadas excepciones y no relajes aserciones ni umbrales para que algo pase. Si un test falla, di qué falla y por qué.
2. **No metas conocimiento de un mundo en `ida/core/` ni en `ida/sistemas/`**, ni directamente ni con trucos que el test no ve (cadenas construidas en ejecución, imports dinámicos, umbrales afinados para un mundo). Va en `ida/mundos/<mundo>`.
3. **El mundo percibe; IdA piensa.** No mejores un mundo haciendo que su sensor calcule o valore por el individuo (búsquedas, planes, oráculos externos, rasgos valorados). Mejora su percepción en bruto o sus Componentes propios.
4. **Harness engineering: consistencia biológica sin atajos ni trucos rígidos.**
   - Las conductas adaptativas deben apoyarse en principios biológicos plausibles: mapas cognitivos/hipocampales, aliestesia homeostática, asimetrías lucha/huida reguladas por el estado somático y equipamiento, o aprendizaje de contingencias.
   - Prohibido parchear comportamientos mediante autómatas deterministas rígidos, "trampas" de juego, secuencias de acciones cableadas para un fin específico o saltos que ignoren el arbitraje del Tribunal.
   - Cualquier mecanismo orgánico candidato debe evaluarse empíricamente con mediciones repetibles con semilla antes y después. Si demuestra generalidad y rigor entre mundos, puede proponerse para su elevación al Core.
5. **No toques `ida/core/` ni `ida/sistemas/` sin permiso expreso del autor.** Si es imprescindible, en un commit propio, explicado, y comprobando que una vida con semilla da lo mismo antes y después cuando el cambio no busca cambiar la conducta. Cuenta como permiso expreso el que concede la sección «Permiso» de cada encargo de [`docs/PLAN_IMPLEMENTACION.md`](docs/PLAN_IMPLEMENTACION.md), y vale solo para los pasos de ese bloque y mientras dure su encargo. Ese permiso no cambia las reglas 1 a 3: la pureza de `ida/core/` e `ida/sistemas/` y sus tests se mantienen.
6. **Verifica antes de afirmar.** Cada afirmación sobre el código cita fichero y línea o la salida de un comando. Lo que no hayas comprobado, márcalo como no verificado.
7. **No inventes cifras, referencias ni mecanismos.** Toda cifra publicada lleva su comando, sus semillas, su número de vidas y su fecha, y se compara con la versión anterior en las mismas semillas. Publica también los resultados negativos.
8. **Un commit por cambio**, con mensaje descriptivo. Nada de `push` sin que el autor lo pida.
9. **Sin lenguaje enfático.** Describe con cifras y límites. **Informes y documentación, en español** (también las respuestas al autor, los mensajes de PR y los resúmenes).
10. **No importes `chess` fuera de `ida/mundos/ajedrez/`** (licencia, ver [`NOTICE`](NOTICE)).
11. **Seguridad:** el mundo de archivos solo puede tocar su bioma; no amplíes esa frontera. El panel y la pila de observabilidad escuchan solo en local.

## Antes de proponer un cambio

```bash
python -m pytest -q
ruff check ida tests
mypy ida
git diff --stat -- ida/core ida/sistemas   # ¿tocaste el framework base? justifícalo
```
