# A7b: Memoria por secciones con dueño (D7)

Rama `reorg/a7b-memoria`, desde `origin/reorg/componentes` (`6b7098a`).
Encargo: secciones con dueño en la Memoria (peligros → Amenaza, satisface → Apetencia, cuadricula → cuerpo,
requisitos → `Requisito`), manual y legado diferidos, escrituras delegadas con autor y test estático de dueños.

## Estado

| Etapa | Qué | Estado | Commit |
|---|---|---|---|
| E1 | Mecanismo de secciones, con tests | Hecha | `519916d` |
| E2 | «peligros» a Amenaza, sin `escalar()` | Hecha | `a2db6f7` |
| E3 | «satisface» a Apetencia | Hecha | (ver git log) |
| E4 | «cuadricula» al cuerpo | Pendiente | |
| E5 | `Requisito` y su sección | Pendiente | |
| E6 | Escrituras delegadas y test estático | Pendiente | |
| E7 | Especificación y documentos | Pendiente | |

### Últimas comprobaciones (E3)

```
ruff check .   All checks passed!
mypy ida       Success: no issues found in 61 source files
pytest -q      384 passed, 1 warning
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
