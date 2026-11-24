# A2: Estructura de paquetes final (D2) y arreglos pendientes

Rama `reorg/a2-paquetes`, desde `origin/reorg/componentes` (`48df2fc`).
Encargo: llevar el código a su estructura de paquetes final según D2, más cuatro arreglos pendientes (P1-P4).

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Arreglos P1 (mapa y S3), P2 (sección directa) y P3 (tipos) | Hecha | `570e444` |
| E2 | `ida/nucleo` e `ida/core` (sentir, actuar, regulacion) | Hecha | `2bdb9e7` |
| E3 | `ida/s1` | Hecha | `4daa83a` |
| E4 | `ida/s2` e `ida/s3` (y eliminar `ida/sistemas`) | Hecha | `ba8a2f7` |
| E5 | `ida/cuerpos/cuadricula` y los mundos como paquetes | Hecha | `99326e4` |
| E6 | P4 (pureza completa), rutas en documentos y herramientas, mapa regenerado | Hecha | `8e80572` |

### Últimas comprobaciones (E6)

```
ruff check .   All checks passed!
mypy ida       Success: no issues found in 159 source files
pytest -q      870 passed, 1 warning in 62.80s
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

## E6 · P4 (pureza completa), rutas en documentos y herramientas, mapa regenerado

- **P4: Regla de pureza ajustada y verificada con AST en `tests/test_pureza.py`:**
  - `ida/nucleo` no importa nada de `ida` salvo `ida/nucleo` (`test_importaciones_nucleo`).
  - `ida/core` importa únicamente `ida/nucleo` e `ida/core` (`test_importaciones_core`).
  - `ida/s1`-`ida/s3` y `ida/sistemas_comun.py` no importan `ida/cuerpos` ni `ida/mundos` (`test_importaciones_sistemas`).
  - `ida/cuerpos` no importa `ida/mundos` (`test_importaciones_cuerpos`).
  - `ida/mundos` puede importar paquetes generales y capas de cuerpo.
  - Ningún paquete general importa `ida/cuerpos` ni `ida/mundos`.
  - La base completa (`nucleo`, `core`, `s1`, `s2`, `s3`, `sistemas_comun`) pasa el linter de pureza de palabras de mundo y dependencias prohibidas.
- **Rutas actualizadas en documentación y configuración:**
  - `AGENTS.md`: actualizadas referencias al framework base (`ida/nucleo/`, `ida/core/`, `ida/s1/`-`ida/s3/`, `ida/sistemas_comun.py`).
  - `doc-repositorio/02_ARQUITECTURA_Y_MECANISMO_VITAL.md`: rutas de tribunal, onda y sistemas actualizadas.
  - `doc-repositorio/04_GUIA_TECNICA_Y_PATRONES.md`: rutas de puerto (`ida/nucleo/mundo.py`), azar (`ida/nucleo/azar.py`) y árbol completo de directorios actualizado con D2.
  - `docs/DISENO_COMPONENTES.md`: marcado D2 como estructura implantada en A2, y actualizado el registro del plan y de cambios.
  - `doc-repositorio/componentes.toml`: actualizadas notas que citaban ficheros antiguos (`saliencia.py`, `amenaza.py`, `requisito.py`, `modelo_directo.py`, `mapa_local.py`).
  - `doc-repositorio/06_MAPA_DE_COMPONENTES.md`: regenerado con `herramientas/mapa_componentes.py --escribir`.
  - `tests/test_defensa.py`: actualizado comentario de ruta.

## E5 · ida/cuerpos/cuadricula y mundos como paquetes

- `ida/cuerpos/cuadricula/`:
  - Componentes trasladados con `git mv`:
    - `ModeloDirecto` a `ida/cuerpos/cuadricula/core/actuar/modelo_directo.py`
    - `MapaLocal` a `ida/cuerpos/cuadricula/s1/interpretar/mapa_local.py`
  - Bibliotecas en la raíz: `buscador.py`, `geometria.py`, `mapa.py`, `memoria.py`, `motor.py`, `situacion.py`, `__init__.py`.
  - `ida/cuerpos/cuadricula/__init__.py` importa `ModeloDirecto` y `MapaLocal` de sus nuevas rutas.
  - `tests/test_duenos_memoria.py`: adaptado `CUERPO` para usar `rglob("*.py")`.
- `ida/mundos/minimo/`:
  - `ida/mundos/minimo.py` movido con `git mv` a `ida/mundos/minimo/adaptador.py` (contiene `MundoMinimo`).
  - Extraído `Defensa` a `ida/mundos/minimo/s1/reaccionar/estrategias/defensa.py`.
  - `ida/mundos/minimo/__init__.py` exporta `MundoMinimo`.
- `ida/mundos/snake/`:
  - `ida/mundos/snake.py` movido con `git mv` a `ida/mundos/snake/adaptador.py` (contiene `MundoSnake`).
  - `ida/mundos/snake/__init__.py` exporta `MundoSnake`, `ALTO`, `ANCHO`, `espacio_libre`.
- `ida/mundos/archivos/`:
  - `ida/mundos/archivos.py` movido con `git mv` a `ida/mundos/archivos/adaptador.py` (contiene `MundoArchivos`).
  - Extraídos componentes y estrategias:
    - `ida/mundos/archivos/s1/reaccionar/estrategias/defensa.py`: `Defensa`
    - `ida/mundos/archivos/s1/reaccionar/estrategias/alimentarse_con_prudencia.py`: `AlimentarseConPrudencia`
    - `ida/mundos/archivos/s3/reaccionar/prudencia.py`: `Prudencia`, `_indicios_de_dano`
    - `ida/mundos/archivos/s3/reaccionar/estrategias/buscar_en_otra_carpeta.py`: `BuscarEnOtraCarpeta`
  - `ida/mundos/archivos/__init__.py` exporta `MundoArchivos`, `clase_de`, `tensor_bytes`.
- `doc-repositorio/componentes.toml`: actualizadas las notas de `ModeloDirecto` y `MapaLocal`.
- `doc-repositorio/06_MAPA_DE_COMPONENTES.md`: regenerado con `herramientas/mapa_componentes.py --escribir`.

## E4 · ida/s2 e ida/s3 (y fuera ida/sistemas)

- Trasladado S2 a `ida/s2/`:
  - `ida/s2/comun.py`: `EXPLORACION`, `SEGURIDAD`, `CANSANCIO`, `_peligro`, `_recordado`.
  - `ida/s2/sentir/`: `patron.py`, `emocion.py`, `recuerdo.py`.
  - `ida/s2/interpretar/`: `sujeto.py`, `valor.py`.
  - `ida/s2/reaccionar/`: `exteriorizacion.py`, `impulso.py`, `feedback.py`, `estrategia.py`, `peticion.py`.
    - `ida/s2/reaccionar/estrategias/`: `explorar.py`, `refugiarse.py`, `recordar_comida.py`.
  - `ida/s2/actuar/`: `accion.py`, `anticipacion.py`.
  - `ida/s2/__init__.py`: `crear_s2`, `estrategias_s2`.
- Trasladado S3 a `ida/s3/`:
  - `ida/s3/comun.py`: `_yo`, `inventario`, `delante`, `_cosas`, `_pos`, `_dist`, `al_alcance_clase`, `desplazamientos_a_clase`, `Paso`, `ir_por_el_mapa`, `acercarse_a_clase`, `_cantidad`, `_conclusion`, `COSTE_RECORDADO`, `COSTE_POR_PROXIMIDAD`, `COSTE_SIN_PRODUCTOR`, `SABER`, `INTENSIDAD_INTENCION_DEL_MUNDO`.
  - `ida/s3/sentir/`: `comunicacion.py`.
  - `ida/s3/interpretar/`: `agente.py`, `predicado.py`, `proposicion.py`, `sentencia.py`, `logica.py`, `creencia.py`, `requisito.py` (movido desde `ida/sistemas/requisito.py` con `git mv`).
  - `ida/s3/reaccionar/`: `intencion.py`, `impulso.py`, `feedback.py`, `estrategia.py`.
    - `ida/s3/reaccionar/estrategias/`: `evitar_lo_peligroso.py`, `comer_lo_nutritivo.py`, `coger_lo_util.py`, `estudio.py`, `perseguir_metas.py`.
  - `ida/s3/actuar/`: `accion.py`.
  - `ida/s3/__init__.py`: `crear_s3`, `estrategias_s3`.
- `ida/sistemas_comun.py`: añade `crear_sistemas()` que instancia S1, S2 y S3 en su orden.
- Eliminado completamente `ida/sistemas/` (`s2.py`, `s3.py`, `__init__.py`).
- Actualizadas importaciones en todo el repositorio y reglas en `tests/test_duenos_memoria.py` (`requisitos`, autores `RecordarComida` y `Estudio`).

## E3 · ida/s1

- Trasladado S1 a su estructura de paquetes final `ida/s1/`:
  - `ida/sistemas_comun.py`: contiene los componentes y utilidades comunes a los sistemas triúnicos (`Accion`, `Anticipacion`, `Estrategia`, `Peticion`, etc.), movido desde `ida/sistemas/comun.py` con `git mv`.
  - `ida/s1/comun.py`: constantes y funciones auxiliares compartidas en S1 (`SEGURIDAD`, `COBIJO`, `TIPO_RECINTO`, `recinto`, `_salida`, `_amenaza`, `_peligro`, `_yo`, `_objetos_llevados`, `objetos_peligrosos`, `_rechazado`, `_al_alcance`, `_posicion`, `_hacia`, `intensidades`, `deficits`, `alostasis`).
  - `ida/s1/sentir/`: `imagen.py`, `amenaza.py` (movido con `git mv`), `saliencia.py` (movido con `git mv`).
  - `ida/s1/interpretar/`: `objeto.py`, `supervivencia.py`, `apetencia.py` (con `Aliestesia`).
  - `ida/s1/reaccionar/`: `reflejo.py`, `impulso.py`, `feedback.py`, `estrategia.py`, `peticion.py`.
    - `ida/s1/reaccionar/estrategias/`: `huir.py`, `defenderse.py`, `sobresalto.py`, `quieto_o_huir.py`, `alimentarse.py`, `seguir_en_movimiento.py`, `afrontar.py`, `proteger.py` (movido con `git mv`).
  - `ida/s1/actuar/`: `accion.py`, `anticipacion.py`.
  - `ida/s1/__init__.py`: exporta `crear_s1` y `estrategias_s1`.
- Eliminado `ida/sistemas/s1.py` con `git rm`.
- Actualizadas importaciones en todo el repositorio y ajustadas las reglas en `tests/test_duenos_memoria.py` para reflejar la nueva ubicación de los dueños (`ida/s1/sentir/amenaza.py` y `ida/s1/interpretar/apetencia.py`).

## E2 · ida/nucleo e ida/core (sentir, actuar, regulacion)

- `ida/nucleo/`: trasladada la mecánica sin cognición con `git mv`:
  `arquitectura.py`, `azar.py`, `biblioteca.py`, `estrategia.py`, `linaje.py`, `memoria.py`, `mundo.py`, `onda.py`, `persistencia.py`, `pieza.py`, `soma.py`, `vocabulario.py`. Creado `ida/nucleo/__init__.py`.
- `ida/core/`:
  - `latido.py` permanece en `ida/core/latido.py` (decisión del arquitecto tras consulta: el latido es del Core, orquesta Onda, regulación, sentir y actuar, evitando un ciclo de dependencias si viviese en `nucleo`). Se verificó que `Organismo` no importa mundos, cuerpos ni sistemas.
  - `regulacion.py` permanece en `ida/core/regulacion.py`.
  - `ida/core/sentir/`: componentes de sensores extraídos de `sentidos.py`: `interocepcion.py`, `propiocepcion.py`, `exterocepcion.py`, `ambiente.py`.
  - `ida/core/actuar/`: componentes de actuación extraídos de `sentidos.py`: `tribunal.py`, `actuador.py` (con `aplicar_efecto`).
  - Eliminado `ida/core/sentidos.py`.
- Actualizadas importaciones en todo el código base (`ida/`, `tests/`, `herramientas/`) de `ida.core.<mecanica>` a `ida.nucleo.<mecanica>` y de `ida.core.sentidos` a `ida.core.sentir.*` / `ida.core.actuar.*`.
- Actualizado `docs/DISENO_COMPONENTES.md` (D2 y registro de cambios) con la decisión arquitectónica sobre `latido.py` y las reglas de importación.

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
