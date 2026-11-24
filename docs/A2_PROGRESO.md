# A2: Estructura de paquetes final (D2) y arreglos pendientes

Rama `reorg/a2-paquetes`, desde `origin/reorg/componentes` (`48df2fc`).
Encargo: llevar el código a su estructura de paquetes final según D2, más cuatro arreglos pendientes (P1-P4).

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Arreglos P1 (mapa y S3), P2 (sección directa) y P3 (tipos) | Hecha | (este commit) |
| E2 | `ida/nucleo` e `ida/core` (sentir, actuar, regulacion) | Pendiente | - |
| E3 | `ida/s1` | Pendiente | - |
| E4 | `ida/s2` e `ida/s3` (y eliminar `ida/sistemas`) | Pendiente | - |
| E5 | `ida/cuerpos/cuadricula` y los mundos como paquetes | Pendiente | - |
| E6 | P4 (pureza completa), rutas en documentos y herramientas, mapa regenerado | Pendiente | - |

### Últimas comprobaciones (E1)

```
ruff check .   All checks passed!
mypy ida       Success: no issues found in 63 source files
pytest -q      516 passed, 1 warning in 62.57s
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
mapa_componentes.py: Mapa de Componentes válido y al día.
```

## E1 · Arreglos P1, P2 y P3

### P1: Desacoplamiento de cuadrícula y S3
- `ida/cuerpos/cuadricula/mapa.py`: `ir_por_el_mapa` devuelve la tupla `(primero, d, (x, y))` (casilla siguiente, distancia y destino) en vez de construir un `Paso` de S3.
- `ida/sistemas/s3.py`: `ir_por_el_mapa` recibe la tupla del cuerpo, comprueba si la casilla está en `lugares(ctx)` (puerta/cerrada) y construye su propio `Paso` de S3. El cuerpo ya no importa nada de S3.
- `ida/cuerpos/cuadricula/__init__.py`: tipo de retorno actualizado.

### P2: Eliminación de propiedades `# A2:` de Memoria
- Se eliminaron todas las propiedades de solo lectura `# A2:` en `ida/core/memoria.py` (líneas 442-569: `peligros`, `satisface`, `linea_base`, `n_base`, `requisitos`, `intentos`, `claves_inventario`, `metas`, `fallos_seguidos`, `_objetos`, `bloqueada`, `declarada`, `puede_salir`, `tasa_estimada`, `casillas`, `version_mapa`, `paso_libre`, `paso_bloqueado`, `peligro_sobre`, `transformaciones`, `cuerpo`, `cierres`, `yo_previo`, `transitable`, `transitable_peligro`, `resultado`, `modelo_cuerpo`, `satisfaccion`, `estimacion_satisface`).
- Todos los llamadores (`ida/sistemas/s1.py`, `ida/sistemas/s3.py`, `ida/sistemas/amenaza.py`, `ida/sistemas/proteger.py`, `ida/mundos/crafter/s1/interpretar/recinto.py`, herramientas de diagnóstico y tests) fueron actualizados para acceder a través de `ctx.memoria.seccion(nombre)` (o la API de lectura de la sección).

### P3: Tipos de dato Requisito, Meta y Satisface
- Decisión: `Requisito`, `Meta` y `Satisface` se mantienen en el núcleo (`ida/core/memoria.py`).
  - Motivo: `Requisito` modifica `self.confianza` en `ajustar_confianza(paso)`. Si se alojase bajo `ida/sistemas/`, infringiría la comprobación sintáctica de `tests/test_propiedad.py` (`test_sin_mutaciones_directas`), la cual prohíbe `.confianza =` en `sistemas/` para salvaguardar la inmutabilidad directa de las Piezas de la Onda.
  - El núcleo no importa nada de los sistemas para contener estas estructuras de datos (solo dependen de `Verbo` y `acotar`, ambos del núcleo), y tanto los sistemas como los mundos pueden importarlos limpiamente.
