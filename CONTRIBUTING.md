# Cómo contribuir

Gracias por el interés. IdA es un proyecto personal de aprendizaje y experimentación. Las contribuciones son bienvenidas si respetan la arquitectura y la honestidad de las cifras.

## Entorno

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev,crafter,ajedrez]"
python -m pytest -q
ruff check ida tests
mypy ida
```

O abre el repositorio en el [devcontainer](.devcontainer/devcontainer.json). Los tests de Snake no usan la red: sustituyen el navegador por un doble.

## Qué no se puede relajar

- **La pureza del framework base.** Nada de vocabulario ni imports de un mundo en los paquetes base (`ida/nucleo/`, `ida/core/`, `ida/s1/`–`ida/s3/`, `ida/sistemas_comun.py`) (lo vigila `tests/test_pureza.py`). El conocimiento de dominio va en `ida/mundos/<mundo>`: su sensor, su perfil y sus componentes propios.
- **El mundo percibe; IdA piensa.** Un sensor traduce lo que hay ahora a rasgos; no calcula por el individuo ni delega la decisión en un motor o un modelo externo ([principio 7](docs/historico/DISENO_FRAMEWORK_BASE.md)).
- **La guillotina.** Lo lento (disco, red, planificación larga) va fuera del latido: al dormir, al morir o después del plazo.
- **La separación de licencias.** `chess` solo se importa dentro de `ida/mundos/ajedrez/` (`tests/test_licencias.py`, [`NOTICE`](NOTICE)).
- **Los tests.** No se borran ni se debilitan aserciones para que un cambio pase.

## Proceso de cambio de diseño

1. **Especificación viva:** La arquitectura de Componentes está definida en [`docs/DISENO_COMPONENTES.md`](docs/DISENO_COMPONENTES.md) y formalizada en [`doc-repositorio/componentes.toml`](doc-repositorio/componentes.toml). Todo cambio o movimiento de Componentes debe reflejarse en el TOML y regenerar [`doc-repositorio/06_MAPA_DE_COMPONENTES.md`](doc-repositorio/06_MAPA_DE_COMPONENTES.md).
2. **Pureza y límites biológicos:** Se vigilan con `tests/test_pureza.py` (jerarquía de paquetes acíclica) y `tests/test_criterios.py` (límites AST de preatención y estrategias).
3. **Limpieza sin cambio de conducta:** Se acepta con `python herramientas/equivalencia.py` en `EQUIVALENCIA: OK` y manteniendo la invariancia en `herramientas/invariancia.py`.
4. **Cambios de conducta:** Deben medirse uno por uno con el criterio de no inferioridad **D17** (comparación pareada conjunta a 100 000 pasos en Crafter con $\Delta \text{Score} \ge -0,3$ e IC 95 % $\ge -1,0$, más benchmark pareado en mínimo y archivos).
5. **Tareas pendientes:** El trabajo en curso y por hacer se recoge en [`docs/PENDIENTES.md`](docs/PENDIENTES.md).

## Lista de comprobación del pull request

- [ ] `python -m pytest -q`, `ruff check ida tests` y `mypy ida` en verde.
- [ ] Un commit por cambio, con mensaje descriptivo.
- [ ] Si toca `ida/core` o `ida/sistemas`, se explica por qué no podía ir en un mundo, y una vida con semilla da lo mismo antes y después si el cambio no busca cambiar la conducta.
- [ ] Si se publican cifras nuevas: comando exacto, semillas, número de vidas y fecha, comparando con la versión anterior en las mismas semillas. También las malas.
- [ ] Sin rutas absolutas, secretos ni datos personales.
- [ ] Documentación actualizada.

## Cómo informar de un problema

Abre un *issue*. Para problemas de seguridad, sigue [`SECURITY.md`](SECURITY.md).
