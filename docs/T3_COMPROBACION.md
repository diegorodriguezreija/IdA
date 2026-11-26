# T3 · Lista de comprobación de la antesala y del servidor v1

Para revisar a mano la rama `vista/t3-antesala` (O18). Arranca con datos de prueba para no tocar `datos/<mundo>`:

```bash
.venv\Scripts\python.exe -m ida --datos F:\tmp\t3\datos
```

Se abre el navegador en `http://127.0.0.1:<puerto>/#/antesala` (el puerto sale en la consola; 8000 si está libre).

## Cabecera

- [ ] La marca IdA (un brote con un latido que pulsa suave), «Antesala», «Vivero» y «Laboratorio» y, a la derecha,
      ES/EN y el botón de tema.
- [ ] El idioma de entrada es el del navegador (español si es `es-*`; inglés en otro caso). Cambiarlo traduce toda la
      página al momento, también las etiquetas y ayudas de las opciones del mundo y los nombres de los presets.
      Recargar la página conserva el elegido.
- [ ] El tema de entrada es el del sistema. El botón cambia entre claro y oscuro y se conserva al recargar.
- [ ] En una ventana privada (sin `localStorage`) todo funciona igual; solo no se recuerdan idioma y tema.
- [ ] Con el teclado (Tab) cada control enseña un anillo de foco visible, en los dos temas.

## Paso 1 · Mundo

- [ ] Cinco tarjetas. Crafter, primero y más grande, con el collage de sus texturas y la etiqueta «Mundo estrella».
- [ ] Cada tarjeta: sprite, nombre, descripción breve y estado: «Listo», «No instalado», «Falta el navegador» (Snake
      sin Chromium) o «Listo · rival local» (ajedrez sin Stockfish en el `PATH`). Snake lleva además «Tiempo real».
- [ ] Pulsar una tarjeta (o su botón «Elegir») la marca con el borde verde y el ✓; «Siguiente» solo se activa con un
      mundo que se pueda lanzar.
- [ ] Si un mundo no está instalado: «Instalar» enseña una barra de progreso y «Ver la salida» con las líneas de pip
      en vivo; al acabar, aviso abajo a la derecha y la tarjeta pasa a «Listo». Si falla, la salida queda abierta y
      el botón dice «Reintentar la instalación». *Solo en un entorno de prueba: instala de verdad en el `.venv`.*
- [ ] Recargar durante una instalación: la tarjeta retoma la salida desde el principio.

## Paso 2 · Carácter

- [ ] Cinco tarjetas: Óptimo, Cauto, Audaz, Equilibrado y Al azar, cada una con su icono, un radar de los cinco
      rasgos y una frase. «Al azar» enseña un pentágono discontinuo con «?».
- [ ] «Óptimo» cambia de forma según el mundo elegido en el paso 1.
- [ ] «Avanzado» despliega los cinco deslizadores (apertura, responsabilidad, neuroticismo, extraversión: 0,15–0,85;
      umbral de miedo: 0,45–0,75) con su valor y un radar grande. Mover uno crea la tarjeta «Personalizado» y la elige.

## Paso 3 · Empezar

- [ ] Semilla con el botón 🎲 (cambia la semilla y el resumen), latidos y generaciones con los sugeridos del mundo.
- [ ] «Opciones de <mundo>» generadas desde `opciones()`, con su etiqueta, su ayuda y «Recomendado: …»: en Crafter,
      vista, radio, manual, longitud y tamaño del mapa; en mínimo, tamaño, depredadores y comida.
- [ ] «Avanzado» (plegado) trae las opciones booleanas o que admiten vacío (en Crafter, `semilla_mapa` y `ventana`),
      «Sin experiencia» y «Empezar de cero».
- [ ] «Restablecer los recomendados» vuelve a los valores declarados.
- [ ] Un valor fuera de rango se marca en rojo y «Empezar» no lanza: dice qué falla.
- [ ] «Cargar ficha» con una ficha descargada del panel clásico del mismo mundo: aparece «Ficha: <individuo>» y, en el
      paso 2, la tarjeta «De la ficha». Con una ficha de otro mundo: «Esa ficha es de …: lo aprendido no pasa de un
      mundo a otro». «Quitar la ficha» la descarta.
- [ ] El resumen «Tu IdA» (derecha) enseña mundo, carácter con su radar, semilla y la nota «Vida reproducible» (o, en
      Snake, «Mundo en tiempo real»).
- [ ] «Empezar» lleva al Vivero. Con una vida ya en marcha pregunta si pararla.

## Vivero (esqueleto)

- [ ] Sin vida: «El Vivero está en calma» con un brote y el botón «Ir a la antesala».
- [ ] Con mínimo en marcha: la pradera con sprites, el latido que sube, el individuo y la generación; a la derecha,
      vitalidad, alimentación, energía y descanso (verde, ámbar por debajo de 60 y arcilla por debajo de 30), el
      ánimo traducido, la acción con su motivo y la puntuación.
- [ ] Ritmo: «Pausa» detiene el latido; «×1» va como antes de T3 (100 ms por latido en mínimo, 1 s en Crafter);
      «×4» y «Máximo», más deprisa. El cambio se ve en el acto.
- [ ] En Snake la barra de ritmo está deshabilitada y dice «En tiempo real el ritmo lo marca el mundo».
- [ ] «Parar» (también en pausa) termina la vida: franja «La vida ha terminado» con «Nueva vida».
- [ ] «Panel clásico» abre `/panel` con la misma vida.
- [ ] Archivos (árbol) y ajedrez (tablero) se dibujan; un mundo sin escena enseña su vista de texto.

## Laboratorio

- [ ] «Próximamente» con la lista de lo que traerá T5 y el botón al visor de grabaciones (`/escena`), que también
      sigue el idioma elegido.

## Compatibilidad (hasta T6)

- [ ] `/antesala-antigua` (y `/antesala`) y `/panel` funcionan como antes: lanzar desde la antesala antigua lleva al
      panel, y «Detener» del panel vuelve a la antesala antigua.
- [ ] `python -m ida --mundo minimo --ver` abre el panel de siempre en `/`.

## Lo que no debe pasar

- [ ] Ningún error en la consola del navegador (F12) en ninguna de las pantallas.
- [ ] Un `POST` desde otra página (otro origen) a `http://127.0.0.1:<puerto>/api/v1/vidas` da 403.
- [ ] Nada se escribe en `datos/<mundo>` del proyecto cuando se arranca con `--datos`.
