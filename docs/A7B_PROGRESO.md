# A7b: Memoria por secciones con dueño (D7)

Rama `reorg/a7b-memoria`, desde `origin/reorg/componentes` (`6b7098a`).
Encargo: secciones con dueño en la Memoria (peligros → Amenaza, satisface → Apetencia, cuadricula → cuerpo,
requisitos → `Requisito`), manual y legado diferidos, escrituras delegadas con autor y test estático de dueños.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Mecanismo de secciones, con tests | Hecha | `519916d` |
| E2 | «peligros» a Amenaza, sin `escalar()` | Hecha | `a2db6f7` |
| E3 | «satisface» a Apetencia | Hecha | `7079997` |
| E4 | «cuadricula» al cuerpo | Hecha | `9f2afa6` |
| E5 | `Requisito` y su sección | Hecha | `a21e9ef` |
| E6 | Escrituras delegadas y test estático | Hecha | (ver git log) |
| E7 | Especificación y documentos | Pendiente | |

### Últimas comprobaciones (E6)

```
ruff check .   All checks passed!
mypy ida       Success: no issues found in 63 source files
pytest -q      516 passed, 1 warning
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

## E2 · «peligros» → Amenaza

- `Peligros` (`ida/sistemas/amenaza.py`) es una `Seccion` (`orden_legado = 3`, la última, como antes). Se construye con
  `Peligros(escala=perfil.escala)` (`InitVar` y `__post_init__` con la misma lógica de `escalar`). `escalar()` desaparece,
  y con él las llamadas de cada latido en `Amenaza.reactiva` y `Afrontar.evaluar` (`s1.py`). Sin cambio: `Perfil.escala`
  es fija y nada lee `Peligros` antes del primer `Amenaza.reactiva` (heredar no usa la escala). La equivalencia lo confirma.
- `Peligros.legado(ahora)` y `heredar(legado, tasa)` cumplen el protocolo (toman la clave `peligros`); las de antes pasan a
  `legado_peligros()` y `heredar_peligros(parte)`.
- `Amenaza.seccion_memoria(perfil)` → `("peligros", Peligros(escala=...))`; escribe con `memoria.seccion_propia("peligros", "Amenaza")`.
- `Memoria` ya no crea ni importa `Peligros` (sin `ida.sistemas`, ni en diferido ni en `TYPE_CHECKING`); `legado` y
  `heredar` ya no tratan `peligros`. `Memoria.peligros` queda como propiedad de solo lectura `# A2:` (None sin Amenaza).
- `tests/test_pureza.py`: `test_importaciones_core`: `ida/core` no importa `ida.sistemas`, `ida.cuerpos` ni `ida.mundos`.
- `tests/test_defensa.py` (sin tocar aserciones): la experiencia previa se rellena tras montar el Organismo (la sección
  no existe antes); la escala, con `Peligros(escala=...)`; el legado, con `legado_peligros`/`heredar_peligros`.

## E3 · «satisface» → Apetencia

- Sección `Aliestesia` (`ida/sistemas/s1.py`, `orden_legado = 2`): `satisface`, `linea_base`, `n_base` y los métodos que
  estaban en `Memoria` (`satisfaccion`, `estimacion_satisface`, `aprender_satisface`, `actualizar_linea_base`,
  `VENTANA_BASE`), más su parte de `aplicar_manual` (proposiciones `NUTRITIVO` con `necesidad`), `legado` y `heredar`.
  Comprobado que en `aplicar_manual` el hecho de proposición escribe en `saber` (Core) y en `satisface` sin que una parte
  lea la otra: el bucle no mezcla estado entre secciones.
- `Apetencia.seccion_memoria` → `("satisface", Aliestesia())`. Su `aprender(ctx)` es el antiguo
  `Organismo._aprender_satisface` y escribe con `seccion_propia("satisface", "Apetencia")`.
- Core (`arquitectura.py`, `latido.py`): `Componente.aprende_con_efecto` y `Componente.antes_de_actuar(ctx)`. El Organismo
  guarda `componentes_efecto` (orden de `montados`, sin los del cuerpo); `_plasticidad` los salta y `_aprender` los llama
  en el punto exacto donde estaba `_aprender_satisface` (tras una acción, con experiencia); `antes_de_actuar`, junto a
  `_antes_accion`. Sustituye la condición `"Apetencia" in self.registrados`.
- `Memoria`: propiedades `# A2:` `satisface`, `linea_base`, `n_base`, `satisfaccion`, `estimacion_satisface` (vacías o None
  sin Apetencia, igual que una sección vacía).
- `tests/test_paso0.py` (aserciones intactas): la memoria de las pruebas unitarias registra la sección; las escrituras van
  por la sección.

## E4 · «cuadricula» → cuerpo

- Sección `MapaCuadricula` (fichero nuevo `ida/cuerpos/cuadricula/memoria.py`): `casillas`, `version_mapa`, `paso_libre`,
  `paso_bloqueado`, `peligro_sobre`, `transformaciones`, `cuerpo`, `cierres`, `yo_previo` y los métodos `transitable`,
  `transitable_peligro`, `ver_casillas`, `aprender_transformacion`, `resultado`, `aprender_cuerpo`, `modelo_cuerpo`
  (movidos literalmente de `Memoria`). No da legado (el mapa local no se hereda) ni lee el manual.
- `Cuadricula.seccion_memoria` → `("cuadricula", MapaCuadricula())`. `ModeloDirecto` y `MapaLocal` escriben con
  `seccion_propia("cuadricula", self.de_cuerpo)`; `mapa.py` lee la sección (sin ella, None, como con el mapa vacío);
  `situacion.vecina` recibe la sección.
- Decisión del arquitecto aplicada: las transformaciones son del cuerpo (geometría), no de `Requisito`.
- `Organismo`: si la Memoria ya tiene la sección registrada por el mismo dueño (una memoria preparada o reutilizada en
  otro Organismo del mismo mundo), la conserva; con otro dueño, `registrar_seccion` sigue dando `ValueError`. Así una
  memoria reutilizada conserva su estado, como antes de las secciones.
- `Memoria`: propiedades `# A2:` `casillas`, `version_mapa`, `paso_libre`, `paso_bloqueado`, `peligro_sobre`,
  `transformaciones`, `cuerpo`, `cierres`, `yo_previo`, `transitable`, `transitable_peligro`, `resultado`,
  `modelo_cuerpo` (vacías, None o «abierto» sin cuerpo, como una sección vacía). Las lee `Recinto` (Crafter).
- Pruebas (aserciones intactas): `tests/_secciones.py` (`memoria_con_secciones`) da una Memoria con las secciones que
  registrarían sus dueños; la usan `test_planificador.py` y `test_proteger.py`. `test_cuadricula.py` registra la sección
  y aplica la referencia sobre ella.

## E5 · `Requisito` y la sección «requisitos»

- Fichero nuevo `ida/sistemas/requisito.py`:
  - Sección `Requisitos` (`orden_legado = 1`): `requisitos`, `intentos`, `claves_inventario`, `metas`,
    `fallos_seguidos`, `_tenidos`, `_tenidos_iniciado`; constantes `PASO_CONFIANZA_REQUISITO`, `MAX_INTENTOS`,
    `FALLOS_BLOQUEO`; métodos movidos literalmente de `Memoria` (`objetos` —antes `_objetos`—, `bloqueada`,
    `declarada`, `puede_salir`, `tasa_estimada`, `aprender_requisito`, `registrar_meta`), y su parte de
    `aplicar_manual` (inventario, metas, requisitos), `legado` (`requisitos`) y `heredar` (con `tasa`, como antes).
  - Componente general `Requisito` (S3 · Interpretar, al final del módulo): `activo()` = False (sin barridos ni
    operaciones), `aprende_con_efecto`; `antes_de_actuar` guarda lo que antes era `Organismo._antes_accion` y `aprender`
    hace lo que hacía `Organismo._aprender` con requisitos y metas, en el mismo punto (bucle `componentes_efecto`, tras
    Apetencia: las dos secciones son independientes). `situacion_inventario` y `distancias` salen de `latido.py`.
- `Memoria.aplicar_manual` solo carga proposiciones y sigue contando metas y requisitos en el número devuelto.
- `Requisito` (el dato, en `ida/core/memoria.py`) gana `ajustar_confianza(paso)`: `test_propiedad` prohíbe
  `.confianza =` en `ida/sistemas` (regla pensada para piezas); en vez de añadir una excepción, el ajuste va en el
  dato. `acotar(x + (-p))` es igual a `acotar(x - p)` en coma flotante.
- `Memoria`: propiedades y métodos `# A2:` `requisitos`, `intentos`, `claves_inventario`, `metas`, `fallos_seguidos`,
  `_objetos`, `bloqueada`, `declarada`, `puede_salir`, `tasa_estimada` (valores de una sección vacía sin ella).
- `componentes.toml`: `Requisito` → `hoy = "S3.Interpretar"`, sin `paso`; mapa regenerado (lo exige
  `test_mapa_componentes` desde esta etapa; las notas van en E7).
- Pruebas (aserciones intactas): `test_manual`, `test_planificador`, `test_deuda14` y `test_crafter_manual` usan
  `memoria_con_secciones()` y escriben por `requisitos(mem)` (`tests/_secciones.py`).

## E6 · Escrituras delegadas y vigilancia

- `ver_clase`: el sensor `Exterocepcion` (`ida/core/sentidos.py`) deja de escribir. La cuenta la hace la plasticidad
  del Core (`Organismo._ver_clases`) al empezar la fase «aprender», con una pieza `Exterocepcion` por entidad (solo
  el sensor del Core crea piezas de ese tipo; los demás son preatentivos). Nadie lee `clases_vistas` entre el Sentir y
  ese punto (lo leen `Supervivencia` y `Patron`, en la cognición). Moverla no cambió nada: equivalencia OK.
- `Memoria.recordar_lugar(lugar, bienestar, autor="CORE")`: admite `CORE` y `Recinto` (el que lo hace hoy en Crafter;
  la tabla de D7 decía `Proteger`, que A6 movió a `Recinto`).
- `Memoria.olvidar_donde(clase, autor)`: admite `RecordarComida`.
- `Memoria.fijar_lectura(registro, autor, fin=None)`: admite `Estudio`; `lectura_activa` y `ultimo_fin_lectura`
  pasan a propiedades de solo lectura sobre `_lectura_activa` y `_ultimo_fin_lectura`.
- Un autor no admitido da `PermissionError`.
- `tests/test_duenos_memoria.py` (ast sobre `ida/`): métodos de escritura y `seccion_propia` de cada sección solo en los
  ficheros de su dueño; ninguna escritura en datos de sección a través de la Memoria (propiedades A2); escrituras
  delegadas solo en ficheros del dueño o de autores admitidos; los dueños rechazan autores no admitidos; la tabla cubre
  todas las propiedades A2. En `MapaLocal` y `ModeloDirecto` la variable de la sección pasa de `mem` a `mapa`.
