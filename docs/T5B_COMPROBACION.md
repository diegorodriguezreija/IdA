# T5b · Lista de comprobación del Laboratorio (comprensión)

Para revisar a mano la rama `vista/t5b-comprension` (sección 15 de [DISENO_OBSERVABILIDAD.md](DISENO_OBSERVABILIDAD.md)).
Arranca con datos de prueba para no tocar `datos/`:

```bash
.venv\Scripts\python.exe -m ida --datos F:\tmp\t5b\datos
```

Graba una vida de Crafter desde la antesala («Avanzado → Grabar esta vida») y ábrela en `#/lab` → «Grabaciones». Para
comparar hacen falta dos grabaciones; para las estirpes, «Empezar de cero» una vez (archiva la estirpe de antes).

## Epistemología

- [ ] Cifras del saber en el latido del reproductor (cambian al moverse) y la gráfica «Lo que sabe, en el tiempo» con
      los hechos aprende, duda y refuta arriba.
- [ ] «Expectativa»: aciertos y sorpresas acumulados; «Error de predicción»: un punto por sorpresa, arriba si salió
      mejor de lo esperado.
- [ ] Un carril por saber: color por estado (hipótesis discontinua, demostrada verde, refutada, fuera de las 20), línea
      de confianza, ● ◆ ✕ y el cursor. Filtros por tipo, clase, fuente y estado en este latido.
- [ ] Al pulsar un saber: «Nace en el latido N como hipótesis. Se demuestra en el latido M.» y su historia; pulsar un
      latido de la historia lleva a él. Con una grabación cognitiva, el aviso de las 20 proposiciones.

## Biología

- [ ] Cuerpo con los nombres del mundo (en Crafter: Salud, Comida y bebida, Energía; sin Descanso).
- [ ] Química, afecto (valencia y estrés = activación), franja del estado afectivo, indicadores y déficit de cada
      necesidad. ★ logros, ▼ daños, ✕ muerte, ▲ nacimiento y el sueño en azul en todas.
- [ ] Cada serie con análogo lo dice en su leyenda; vitalidad, energía, tensión y calma no llevan ninguno.
- [ ] La tabla «Series y análogos» con lo que hace cada serie y su línea de código.
- [ ] Pulsar una gráfica lleva a ese latido; la escena y el resumen de la derecha lo siguen.

## Análisis y comparación

- [ ] «Esta vida»: puntuación (con la nota de que no es la Score de D17), logros, saber, amplitud y potencia con su
      máximo y las guillotinas en rojo.
- [ ] «Dos grabaciones»: A es la abierta; al elegir B, «Configuración distinta: semilla» y «Primera divergencia en el
      latido N…» con la raya roja; con dos grabaciones de la misma vida, «La misma vida: N latidos comunes, todos
      iguales salvo los tiempos». Superpuestas y lado a lado; cambiar la serie.
- [ ] «Estirpes»: el compañero y una archivada (o una ficha), Score por generación, rasgos y la tabla con B − A.

## Cierre

- [ ] Cómo murió, latidos, Score, logros, cosas aprendidas, sorpresas y daños; «Lo que aprendió al morir» en frases y
      las notas del motor; «Ir al registro de cierre» va al registro marcado como cierre.
- [ ] Una vida que no muere (pocos latidos): «No murió: la fuente termina en el latido N».
- [ ] Con varias vidas (generaciones), el selector de vida.

## Enlaces, plurales y pulido

- [ ] Vivero → «Lo que sabe» → «Abrir en el Laboratorio» abre Epistemología con el aviso de dónde se viene.
- [ ] Vivero → «Carácter» o «Estirpe» → Análisis en modo estirpes, aunque no haya directo.
- [ ] Ningún «1 cosas», «1 latidos», «1 registros»… en español ni en inglés (p. ej. el directo con un latido, una
      grabación de un registro, «Nace … con 1 recuerdo heredado»).
- [ ] Latido: la primera fila (Onda, Core·Sentir, Preatención, Plasticidad, Regulación) sin textos cortados.
- [ ] Todo en inglés y en oscuro; sin errores en la consola del navegador.

## Comprobaciones automáticas

```bash
.venv\Scripts\python.exe herramientas\equivalencia.py                       # EQUIVALENCIA: OK
.venv\Scripts\python.exe herramientas\invariancia.py --observador completo   # OK en los cuatro mundos
.venv\Scripts\python.exe -m pytest -q                                        # incluye tests/test_t5b.py
.venv\Scripts\ruff check ida tests
.venv\Scripts\mypy ida
```
