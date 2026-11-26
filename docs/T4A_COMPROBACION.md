# T4a · Lista de comprobación del Vivero de un vistazo

Para revisar a mano la rama `vista/t4a-vivero` (O18). Arranca con datos de prueba para no tocar `datos/<mundo>`:

```bash
.venv\Scripts\python.exe -m ida --datos F:\tmp\t4a\datos
```

Se abre el navegador en `http://127.0.0.1:<puerto>/#/antesala`. Lanza Crafter con el carácter «Recomendado» y los
valores recomendados, y ve al Vivero.

## Escena y ritmo (O20)

- [ ] La escena ocupa su sitio sin franjas negras a los lados ni arriba y abajo, en Crafter, mínimo y ajedrez. En
      archivos, el árbol se lee a su tamaño y se desplaza si no cabe.
- [ ] Barra de ritmo: Pausa, Lento, Cómodo (el de entrada), ×4 y Máximo, con «N ms por latido» al lado: Crafter 250,
      mínimo y archivos 300, ajedrez 1000. Lento va al doble y ×4 a la cuarta parte; el cambio se ve en el acto.
- [ ] «Paso a paso» solo aparece en pausa; cada pulsación avanza exactamente un latido (mira el chip «Latido N»).
- [ ] ¿Los ritmos cómodos se siguen bien a ojo? Si alguno va rápido o lento, di cuál: se cambia en
      `ida/telemetria/catalogo.py` (`RITMO_COMODO_MS`), sin tocar el motor.
- [ ] «Parar» (también en pausa) termina la vida: franja «La vida ha terminado» con «Nueva vida».

## Diario y «Ahora»

- [ ] El diario, bajo la escena, enseña los 7 hechos más recientes en frases, con icono y sprite: «Nace…», «Por primera
      vez: tala un árbol», «Ha aprendido que la madera sirve para hacer una mesa», «Logro: Colocar una mesa»…
- [ ] Recargar la página no vacía el diario ni «Lo que sabe» (llegan con el evento `diario`).
- [ ] «Ahora» dice la acción en frase con su motivo («Camina para ponerse a salvo», «Come una vaca porque tiene
      hambre»), y debajo el plan y el sistema. Ya no sale «MOVER celda_5_4».
- [ ] En ajedrez: «Mueve el alfil (c1f4)», «Captura un peón (e4d5)», «Da jaque (…)».

## Tarjetas y «Ver más» (O19)

- [ ] A la derecha: Cuerpo y ánimo, Ahora y Lo que sabe; abajo: Logros y puntuación, Carácter y Estirpe (rayada: «llega
      en T4b», con la generación).
- [ ] «Lo que sabe»: frases con el sprite de la clase («El zombi es peligroso»). Lo recién aprendido se resalta en
      amarillo unos segundos con «Nuevo»; lo que aún es hipótesis va con borde discontinuo y la marca «Hipótesis».
- [ ] Cada «Ver más» abre un panel lateral; se cierra con ✕, con Esc o pulsando fuera, y el foco vuelve al botón.
      El detalle se actualiza en directo sin saltar al principio al desplazarse.
- [ ] Detalle de Cuerpo y ánimo: química, valencia, indicadores viscerales y necesidades.
- [ ] Detalle de Ahora: motivo tal como lo anota IdA, candidatos del Tribunal con el ganador resaltado, planes activos,
      reparto entre S1, S2, S3 y Core, cambios de plan recientes.
- [ ] Detalle de Lo que sabe: cifras (demostradas, hipótesis, refutadas, aciertos, sorpresas, heredados), cada saber con
      fuente y confianza, cantidades de los requisitos, refutadas y sorpresas recientes.
- [ ] Detalle de Logros: todos los logros de Crafter (conseguidos con 🏅, pendientes con ○) e historia de la vida.
- [ ] Detalle de Carácter: radar grande y rasgos; con 2 o más generaciones, el cambio respecto a la anterior.
- [ ] «Abrir en el Laboratorio» lleva a `#/lab?seccion=…` y el Laboratorio dice de qué tarjeta vienes.

## Idioma y tema

- [ ] En inglés todo el Vivero cambia al momento, también el diario, «Lo que sabe» y los logros («It takes wood to make
      a table», «Achievement: Place a table»).
- [ ] Selector de tema con tres botones: sistema, claro y oscuro. «Sistema» sigue al del sistema operativo y no se
      guarda; claro y oscuro se conservan al recargar.

## Antesala

- [ ] Paso 2: con una tarjeta de carácter enfocada, las flechas (y Inicio/Fin) eligen la siguiente o la anterior; Tab
      entra y sale del grupo de una vez.
- [ ] Paso 3 de Crafter: «Vista» ofrece «Oficial (9×7, como el benchmark)» y «Cuadrada»; «Manual», «Estricto (artículo
      y README)» y «Ampliado (también su código)». En ajedrez, «Color de IdA»: Blancas / Negras.
- [ ] Paso 3 de Snake: «Ver también la web real (playsnake.org)» se ve fuera de «Avanzado», apagada.

## Snake (O21; necesita conexión)

- [ ] Con la web real apagada: el Vivero dice «Jugando ahora en playsnake.org ↗» y que el navegador corre en segundo
      plano.
- [ ] Con la web real encendida: se abre la ventana de Chromium con playsnake.org y el Vivero hace de segunda pantalla
      (cuerpo, «Ahora», «Lo que sabe», diario). El ritmo sigue fijo («En tiempo real el ritmo lo marca el mundo»).

## Lo que no debe pasar

- [ ] Ningún error en la consola del navegador (F12) en el Vivero de los cinco mundos.
- [ ] Ningún texto en bruto del tipo `hecho.xxx`, `plan.xxx` o `verbo.XXX.pres` en pantalla.
- [ ] Nada se escribe en `datos/<mundo>` del proyecto cuando se arranca con `--datos`.
