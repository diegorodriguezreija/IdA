# A6b: Crafter como paquete, geometría al cuerpo y PerseguirMetas (D2, D10, D16)

Rama `reorg/a6b-carpetas`, desde `origin/reorg/componentes` (`4c0b435`).
Encargo: lo propio de Crafter pasa a su carpeta con la estructura del diseño; la geometría y buscador pasan al cuerpo cuadrícula;
la búsqueda en el mapa de S3 pasa al cuerpo; pureza de importaciones y actualización de especificación.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Paquete de Crafter con adaptador, manuales y ValoracionCrafter | Hecha | `4c926ce` |
| E2 | Recinto y SalirDelRecinto a Crafter; lo general en proteger.py con tipo de pieza | Hecha | ver `git log` |
| E3 | Geometría y buscador al cuerpo | Pendiente | |
| E4 | PerseguirMetas y Contexto.cuerpo | Pendiente | |
| E5 | Pureza, especificación y documentos | Pendiente | |

### Últimas comprobaciones (E2)

```
ruff check .          All checks passed!
mypy ida              Success: no issues found in 58 source files
pytest -q             342 passed, 1 warning in 54.90s
equivalencia.py       minimo: OK · archivos: OK · crafter: OK · ajedrez: OK · EQUIVALENCIA: OK
```

## E1 · Paquete de Crafter con adaptador, manuales y ValoracionCrafter

- Estructura creada:
  - `ida/mundos/crafter/__init__.py`: exporta `MundoCrafter` y constantes comunes (`INVENTARIO`, `MOVIMIENTOS`, etc.).
  - `ida/mundos/crafter/adaptador.py`: traslado de `ida/mundos/crafter.py`.
  - `ida/mundos/crafter/crafter_manual.json` y `crafter_manual_ampliado.json`: trasladados a la carpeta de Crafter.
  - `ida/mundos/crafter/s1/sentir/valoracion.py`: traslado de `ida/mundos/crafter_valoracion.py`.
  - Subpaquetes con `__init__.py` en `ida/mundos/crafter/s1/` y `ida/mundos/crafter/s1/sentir/`.
- Referencias actualizadas:
  - `herramientas/verificar_manual.py`
  - `tests/test_paso0.py`
  - `tests/test_valoracion_crafter.py`
  - `tests/test_defensa.py`
- Borrados `ida/mundos/crafter.py` y `ida/mundos/crafter_valoracion.py` mediante git mv.

## E2 · Recinto y SalirDelRecinto a Crafter; lo general en proteger.py con tipo de pieza

- `ida/sistemas/proteger.py`: reducido a lo general:
  - `COBIJO = "cobijo"`
  - `TIPO_RECINTO = "Recinto"` (constante del tipo de pieza de afordancia)
  - `recinto(ctx)` lector de la pieza
  - `riesgo_exterior(ctx)`
  - `_proponer_abrir(...)` compartido
  - `Proteger`: estrategia general del cobijo
  - Ya no importa nada de Crafter ni de cuerpos.
- Traslados a Crafter:
  - `ida/mundos/crafter/s1/interpretar/recinto.py`: `Recinto`, modelo (`Modelo`, `Cerrador`), candidatos y constantes de Crafter (`ALCANCE_SITIO`, etc.).
  - `ida/mundos/crafter/s1/reaccionar/estrategias/salir_del_recinto.py`: `SalirDelRecinto`.
  - `__init__.py` en `ida/mundos/crafter/s1/interpretar/`, `ida/mundos/crafter/s1/reaccionar/` y `ida/mundos/crafter/s1/reaccionar/estrategias/`.
- Referencias actualizadas en `adaptador.py`, `tests/test_proteger.py`, `herramientas/diagnostico_paso3.py`.

## Decisiones y desviaciones

- Ninguna en E1. Todo se trasladó tal como especificaba el encargo.

## Pendientes

- E2: Mover `Recinto` y `SalirDelRecinto` a `ida/mundos/crafter/`; definir en `ida/sistemas/proteger.py` la constante del tipo de pieza de afordancia (TIPO_RECINTO / "recinto"); Proteger y SalirDelRecinto comparten `_proponer_abrir`.
- E3: Geometría (`geometria.py`) y buscador (`buscador.py`) a `ida/cuerpos/cuadricula/`.
- E4: Búsqueda de material en el mapa de S3 a `ida/cuerpos/cuadricula/mapa.py`, accesible mediante `Contexto.cuerpo`.
- E5: Pureza (ast), actualizar `doc-repositorio/componentes.toml`, regenerar mapa, D16 en `DISENO_COMPONENTES.md`.
