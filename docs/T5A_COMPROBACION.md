# T5a · Lista de comprobación del Laboratorio (base)

Para revisar a mano la rama `vista/t5a-laboratorio` (O1, O7, O13, sección 14 de
[DISENO_OBSERVABILIDAD.md](DISENO_OBSERVABILIDAD.md)). Arranca con datos de prueba para no tocar `datos/`:

```bash
.venv\Scripts\python.exe -m ida --datos F:\tmp\t5a\datos
```

Lanza una vida de Crafter desde la antesala con «Avanzado → Grabar esta vida» marcado, o sin marcar y pulsa «Grabar» en
el Vivero cuando quieras. El Laboratorio está en `#/lab`.

## Grabar (O7)

- [ ] Antesala, paso 3, «Avanzado»: la casilla «Grabar esta vida». Con ella, la vida se graba desde el primer latido y
      con el nivel completo; en el Vivero sale «● Grabando» (enlace a la lista de grabaciones del Laboratorio).
- [ ] Vivero: «⏺ Grabar» empieza a grabar desde el latido siguiente; el botón pasa a «■ Terminar grabación» y avisa
      «Grabando en crafter-…». «Terminar» avisa «Grabación … guardada (N latidos)».
- [ ] Al terminar la vida (o pararla) la grabación se cierra sola.
- [ ] En disco: `F:\tmp\t5a\datos\grabaciones\<mundo>-<AAAAMMDD>-<HHMMSS>.jsonl.gz`; nada en `datos\` del proyecto.
- [ ] La grabación se lee con el lector de siempre:
      `.venv\Scripts\python.exe -c "from ida.telemetria.grabacion import leer; c, r = leer(r'RUTA'); print(c['nivel'], len(r))"`.

## Fuentes y reproductor

- [ ] «● En directo» abre la vida en curso aunque no se grabe: dice cuántos latidos guarda la memoria (máx. 2000) y,
      con «⏭ Directo» pulsado, sigue al último latido.
- [ ] «🎞 Grabaciones» lista las grabaciones (nivel, registros, tamaño, desde qué latido); «Abrir» la carga en el
      reproductor; «⬇ Descargar» baja el `.jsonl.gz`; «🗑 Borrar» pide confirmación en la propia fila («¿Borrar …? No
      se puede deshacer.») y solo con «Sí, borrar» desaparece. Mientras se graba, la fila dice «Grabando» y no se abre,
      descarga ni borra.
- [ ] «📂 Cargar fichero» abre un `.jsonl.gz`, un `.jsonl` o un registro `.json` sin subirlo al servidor.
- [ ] Línea de tiempo: ★ logros, ● lo aprendido, ✕ muerte, ▲ nacimiento, raya roja en las guillotinas y rayas
      discontinuas entre vidas. Al pasar el ratón, la frase del hecho; al pulsar, va a ese latido.
- [ ] ⏮ ◀ ▶/❚❚ ▶| ⏭, «Ir al latido», velocidad (0,5 a 8 latidos por segundo) y el deslizador con el teclado (flechas).
- [ ] La escena pequeña, a la derecha, se queda a la vista al bajar por la página.
- [ ] Desde el Vivero, «🔬 Abrir en el Laboratorio» de cada tarjeta lleva al latido que se estaba viendo y al paso que lo
      explica: Cuerpo y ánimo → Core·Sentir; Ahora → Tribunal; Lo que sabe → Plasticidad; Logros → Cierre; Carácter y
      Estirpe → Onda (con el aviso de que su vista es de T5b).

## Vista «Latido»

- [ ] Los ocho pasos de D1: 1 Onda, 2 Core·Sentir, 3 Preatención (borde discontinuo: no paga atención), 4 Plasticidad,
      5 Regulación, 6 S1, S2 y S3, 7 Tribunal y Actuar, 8 Cierre, y la flecha discontinua del efecto a la plasticidad
      del latido siguiente.
- [ ] La Onda (punto amarillo) recorre los pasos y se para más donde más tiempo se gastó; con «reducir movimiento» en el
      sistema, no hay animación y la ayuda lo dice.
- [ ] En S1-S3: tiempo de cada módulo (Sentir, Interpretar, Reaccionar, Actuar), amplitud y potencia consumidas sobre
      el máximo, piezas creadas, candidatos propuestos, lo que quedaba al entrar y la estrategia activa. Dormido, «la
      cognición no corre».
- [ ] Guillotina: si saltó, ✂ sobre el sistema donde cortó y «Sin turno» en los siguientes, y el motivo abajo.
- [ ] Tribunal: los cuatro primeros candidatos con su total y el ganador (★); el título dice cuántos había.
- [ ] Al pulsar un paso, el detalle: qué hace, su análogo biológico, su tiempo (latido y media), sus Componentes con
      tiempo, las piezas que salen, las que modifica y las que le entran, agrupadas por autor. En el Tribunal, la tabla
      base/activa/proactiva/plus/total.
- [ ] Al pulsar una pieza: su registro completo (tipo, autor, arousal, confianza, creada, entradas, registro de quién
      la tocó y carga en JSON). Al pulsar un autor o un Componente: su ficha. «← Volver» regresa.

## Vista «Ingeniería»

- [ ] Columnas Core, S1, S2, S3 y Cuerpo con los Componentes que monta el mundo de la vida, por módulo; la
      preatención agrupada con borde discontinuo; las estrategias en óvalo, la activa resaltada y la ejecutada con ▶.
- [ ] Cada Componente con su barra (este latido, escala logarítmica) y su raya (media de la fuente); los que solo
      aprenden dicen «sin tiempo propio: aprende en el paso 4»; la Regulación, que se calcula al crear la Onda.
- [ ] ✱ plástico, ◐ preatentivo; borde de color por clase (general, opcional, del cuerpo, del mundo).
- [ ] «Ver también lo que <mundo> no monta» enseña el resto en gris discontinuo.
- [ ] Ficha: nombre, sistema y módulo, insignias, análogo biológico (o «Sin análogo biológico honesto»), qué hace, su
      tiempo, la decisión de diseño (D<n> desplegable con el texto de `DISENO_COMPONENTES.md`, en español) o «anterior a
      la reorganización», si está montado y la nota técnica.

## Idiomas y temas (O12, O16)

- [ ] Todo el Laboratorio cambia con ES/EN sin recargar (el texto de las decisiones y las notas técnicas siguen en
      español, y la interfaz lo dice).
- [ ] Claro y oscuro: el SVG del latido, la línea de tiempo y el mapa usan las variables del tema.
- [ ] A 1024 px el lateral se estrecha; por debajo de 900 px pasa arriba y el mapa de Ingeniería va a dos columnas.

## Lo que no cambia

- [ ] `herramientas\equivalencia.py` → `EQUIVALENCIA: OK`.
- [ ] `herramientas\invariancia.py --observador completo` → OK en los cuatro mundos.
- [ ] `git diff --stat main -- ida/nucleo ida/core ida/sistemas ida/s1 ida/s2 ida/s3 ida/mundos ida/ejecutor.py` vacío.
