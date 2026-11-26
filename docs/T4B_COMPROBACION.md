# T4b · Lista de comprobación del compañero, la colección y la estirpe

Para revisar a mano la rama `vista/t4b-estirpe` (O9, O10, sección 13 de
[DISENO_OBSERVABILIDAD.md](DISENO_OBSERVABILIDAD.md)). Arranca con datos de prueba para no tocar `datos/`:

```bash
.venv\Scripts\python.exe -m ida --datos F:\tmp\t4b\datos
```

## Cómo comprobar que los datos del usuario no se pierden

Antes de nada, una foto del disco de prueba; al final, otra. Todo lo que había debe seguir en algún sitio.

```powershell
Get-ChildItem -Recurse F:\tmp\t4b\datos | Select-Object FullName, Length | Out-File F:\tmp\t4b\antes.txt -Encoding utf8
# ... la revisión ...
Get-ChildItem -Recurse F:\tmp\t4b\datos | Select-Object FullName, Length | Out-File F:\tmp\t4b\despues.txt -Encoding utf8
```

- [ ] Cada `linaje.json` de `antes.txt` está en `despues.txt`: en `<mundo>\` (el compañero) o en
      `vivero\estirpes\<id>\` (archivado), con el mismo tamaño. Solo falta lo que borraste tú con «Sí, borrar para
      siempre».
- [ ] Ninguna ficha de `vivero\fichas\` ha cambiado de contenido salvo su `nombre` (si la renombraste).
- [ ] En archivos, `archivos\bioma\` sigue ahí después de archivar o adoptar (es del mundo, no de la estirpe).
- [ ] Ningún fichero cambia fuera de la carpeta de `--datos` (en especial, `datos\` del proyecto).

Los caminos que quitan algo del disco son tres, y solo tres (`ida/telemetria/vivero.py`):

| Camino | Qué quita | Salvaguarda |
|---|---|---|
| `Vivero.archivar` (archivar, adoptar, «Empezar de cero») | los ficheros de la estirpe en `<mundo>\` | antes los copia a `vivero\estirpes\<id>\` y comprueba el tamaño de cada copia; si algo falla no quita nada y la carpeta queda marcada `incompleta` |
| `Vivero.adoptar` de una estirpe archivada | su carpeta en `vivero\estirpes\` | antes la copia entera a `<mundo>\` y comprueba cada copia; el compañero que había ya está archivado |
| `Vivero.confirmar_borrado` | una ficha o una estirpe archivada | exige el testigo que dio `pedir_borrado` para ese mismo elemento (un solo uso, 120 s). El compañero no se puede borrar por la API |

La CLI conserva su conducta: `python -m ida --mundo M --tabula-rasa` borra `datos\M` (o `--datos`) como siempre. Desde
la aplicación (antesala, `POST /api/v1/vidas` con `tabula_rasa` y la antesala antigua) se archiva.

Tests: `tests/test_vivero_t4b.py` (ciclo completo en un directorio temporal: vida, guardar, otra vida, adoptar, volver a
adoptar la estirpe archivada, empezar de cero, importar una ficha antigua, borrar sin confirmar y confirmando;
`archivar` no toca el bioma; la CLI sigue borrando).

## Antesala: «Tu compañero»

- [ ] Paso 3, con un mundo que ya tiene compañero: «Continuar con tu compañero» elegido por defecto, con su nombre, la
      generación que nacerá, las vidas del linaje y su mejor Score. El resumen dice «Compañero: Crafter_G3, generación 4» y
      «Carácter: heredado, con mutación», y el radar es el del compañero.
- [ ] «Adoptar de la colección» está apagado si la colección de ese mundo está vacía; con algo, el desplegable lista
      fichas (🧬) y estirpes (🌳) con su Score.
- [ ] «Empezar de cero (se archiva)»: tras lanzar, la estirpe anterior aparece en la Colección como «Estirpe
      archivada, al empezar de cero».
- [ ] Sin compañero (mundo nuevo): solo «Adoptar» y «Empezar una estirpe nueva».
- [ ] «Importar a la colección» con una ficha antigua del panel (`ida-individuo-*.json`): aviso «Importada… (N avisos)»,
      queda elegida para adoptar. Una ficha de otro mundo da el error de siempre.
- [ ] «Avanzado» ya no tiene «Empezar de cero» (está en «Tu compañero»).

## Vivero: Estirpe y Carácter

- [ ] La tarjeta Estirpe enseña la generación actual, «N vidas en el linaje · mejor Score», la línea de tiempo (las 6
      últimas generaciones, con «… y N generaciones antes») con individuo, «murió de … tras N latidos» o «llegó viva al
      final», el Score, 🏆 en la mejor y la que vive ahora resaltada.
- [ ] «Guardar» crea una ficha (aviso «Guardada en la colección: …»); apagado si el mundo aún no tiene compañero.
- [ ] «Colección» lleva a `#/vivero/coleccion`.
- [ ] Su «Ver más»: tabla del linaje (generación, individuo, Score, latidos, final, logros), «Exportar» y la mutación de
      cada rasgo en una línea, con el primer y el último valor.
- [ ] Carácter: el cambio respecto a la generación anterior sale del linaje (también al abrir la página a mitad de la
      tercera generación); su «Ver más» incluye la mutación a lo largo de la estirpe.

## Colección (`#/vivero/coleccion`)

- [ ] Por mundo (Crafter primero), el ranking por mejor Score: compañero (🌱, fondo verde), estirpes archivadas (🌳, con
      fecha y motivo) y fichas (🧬), con puesto y 🏆 en el primero. Filtro por mundo arriba.
- [ ] Compañero: Guardar, Exportar y Archivar (pide confirmación y dice que no se borra).
- [ ] Ficha o estirpe: Adoptar (dice que el compañero actual se archivará), Renombrar (en línea), Exportar y Borrar.
- [ ] Borrar: el primer clic solo abre el recuadro rojo «¿Borrar…? … no se puede recuperar. Si quieres conservarla,
      expórtala antes.» con «Sí, borrar para siempre» y «Cancelar». Cancelar no borra nada. Tras dos minutos, confirmar
      da «La confirmación ha caducado…» y no borra.
- [ ] Las fichas importadas con avisos enseñan «⚠️ N avisos al importarla» y, al abrirlo, qué faltaba.
- [ ] La nota del pie explica qué es el Score de una vida (no es la Score oficial de la medición).

## Diario, Cuerpo y Lo que sabe (pendientes de T4a)

- [ ] Archivos, semilla 6, carácter «Al azar», 600 latidos: al morir por el depredador, el diario dice «Al morir, ha
      aprendido que el depredador es peligroso» (en cursiva, con 🕯️), después de «Muere por el depredador…».
- [ ] Cuerpo: en ajedrez, «Material propio» y «Balance de material» (sin energía ni descanso); en Crafter, «Salud»,
      «Comida y bebida» y «Energía»; en Snake, «Vida», «Saciedad» y «Energía»; en mínimo y archivos, las cuatro. El
      «Ver más» explica cada barra.
- [ ] Lo que sabe: «y N cosas más» = proposiciones no refutadas + requisitos − 5. En Crafter aparecen desde el primer
      latido los requisitos del manual («La mesa necesita madera…»).
- [ ] Su «Ver más»: siete cifras de toda la memoria (con «requisitos» y «heredadas») y «De dónde lo sabe: N del
      manual, N de la experiencia…».
- [ ] Ahora › Ver más: «Quién decide (las N acciones de esta vida)»; al recargar la página, el reparto no vuelve a cero.

## Idiomas y tema

- [ ] En inglés, todo lo nuevo está traducido (antesala, Estirpe, Colección, cuerpo por mundo, «On dying, …»).
- [ ] En oscuro, la línea de tiempo, la mutación y la Colección se leen bien.

## Capturas

Hechas el 26/11/2026 con Chromium de Playwright a 1280 px, servidor con datos en `F:\tmp\t4b\capturas`:

- [Vivero de Crafter con la Estirpe tras tres generaciones](img/t4b_vivero_crafter.png) y [su «Ver más»](img/t4b_estirpe_ver_mas.png)
- [Carácter con la mutación de la estirpe](img/t4b_caracter_estirpe.png)
- [Colección con fichas y estirpes de varios mundos](img/t4b_coleccion.png), [el primer paso de «Borrar»](img/t4b_coleccion_borrar.png)
  y [en inglés y oscuro](img/t4b_coleccion_en_oscuro.png)
- [Antesala con «Continuar con tu compañero»](img/t4b_antesala_continuar.png)
- [Cuerpo de ajedrez con sus etiquetas](img/t4b_cuerpo_ajedrez.png)
- [Diario con lo aprendido al morir](img/t4b_diario_al_morir.png)
