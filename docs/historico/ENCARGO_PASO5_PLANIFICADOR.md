# Encargo del paso 5: planificador general sobre requisitos

Fase de generalización (`docs/FASE_GENERALIZACION_CRAFTER.md`), paso 5, adelantado para ir justo después del 2. Rama `feature/planificador` desde `feature/manual-crafter` (o desde `main`, si el paso 2 ya se fusionó).

**Modelos:** 5.0 a 5.3, Opus 5.5; 5.4 (mediciones), Flash.

**Depende del paso 2:** usa `Memoria.requisitos`, `Memoria.intentos`, `aprender_requisito` y el manual.

---

## 1. Qué se quiere y por qué

**Hipótesis:** si la base sabe **encadenar requisitos hacia atrás** (para conseguir X necesito Y; Y se consigue haciendo Z), y **aprende lo que el manual no dice** a partir de sus éxitos y fracasos, entonces:
- el núcleo sin conducta de Crafter pasa de no fabricar nada (0 % en todos los logros de fabricación) a fabricar la cadena de madera y piedra;
- `PlanTecnologico` se puede borrar con poca pérdida.

**Por qué es general:** el planificador no sabe qué es una mesa ni un pico. Trabaja con `(verbo, objetivo) → requisitos → efecto`, que vale para cualquier mundo con acciones que tienen precondiciones (llaves y puertas, herramientas, recetas). En mínimo, archivos y ajedrez el manual está vacío y no hay requisitos, así que el planificador no propone nada y la conducta no cambia.

**Lo que sustituye:** `PlanTecnologico` entero, con sus recetas (`self.constantes.make/place`) y su lista `OBJETIVOS`. Se borra en este paso (regla de traslado).

**Lo que no hace:**
- No decide cuándo dormir ni cuándo refugiarse. El «dormir de día» de `PlanTecnologico` (`_oportunidades`) es conducta de supervivencia: se pierde aquí y vuelve con los pasos 0 y 3. Hay que medir la pérdida.
- No pelea: `defeat_zombie` y `defeat_skeleton` siguen a cargo de `DefensaArmada` hasta el paso 6.

---

## 5.0 Metas declaradas (ampliación del manual)

El artículo enumera los 22 logros (figura 4). Son metas declaradas por las instrucciones, igual que las leyó SPRING: entran en el manual como hechos de tipo `meta`:

```json
{"id": "M01", "tipo": "meta", "verbo": "USAR", "objetivo": "make_wood_pickaxe", "cita": "Make Wood Pickaxe", "lugar": "artículo, figura 4"},
{"id": "M02", "tipo": "meta", "verbo": "COGER", "objetivo": "carbon", "cita": "Collect Coal", "lugar": "artículo, figura 4"}
```

**Correspondencia** de cada logro con `(verbo, objetivo)`, usando los verbos y nombres que el adaptador ya admite:
- collect_X → (COGER, clase); collect_drink → (COMER, agua);
- place_X y make_X → (USAR, «place_X» o «make_X»);
- eat_cow → (COMER, vaca); eat_plant → (COMER, planta);
- defeat_X → (ATACAR, X);
- wake_up → (DORMIR, «»).

Los requisitos del manual (paso 2) se completan con **lo que produce** cada acción, si el artículo lo dice. Por ejemplo, «craft wood pickaxes» da `produce: {"pico_madera": 1}`, y «collect wood» desde los bosques da `COGER arbol → produce madera`. Lo que el artículo no diga, se aprende del efecto observado (`Requisito.efecto`, paso 2).

**Memoria:** `Memoria.metas: Dict[Tuple[Verbo, str], Meta]`, con `conseguida_en_esta_vida: bool`. Se marca con el primer éxito (`Efecto` con éxito para ese verbo y objetivo).

## 5.1 El planificador (S3, estrategia general; pseudocódigo mío)

Estrategia `PerseguirMetas(ConPropuestas)` en `ida/sistemas/s3.py`, para la intención `progresar`. Esa intención ya existe: la declara el `Perfil` de Crafter, con intensidad fija 0,5. Con `memoria.metas` vacía no es elegible.

```python
class PerseguirMetas(ConPropuestas):
    nombre = "perseguir_metas"
    impulsos = ("progresar",)
    prioridad = 10
    PROFUNDIDAD = 5

    def elegible(self, ctx, impulso, intensidad) -> bool:
        return ctx.con_experiencia and any(not m.conseguida for m in ctx.memoria.metas.values())

    def decidir(self, ctx, estrategia=None) -> None:
        inv = inventario(ctx)                         # propiocepción, como hoy
        candidatas = [m for m in ctx.memoria.metas.values() if not m.conseguida]
        # orden: primero la más barata de completar (menos submetas pendientes), luego el orden del manual
        mejor = None
        for meta in candidatas:
            pasos = self._resolver(ctx, (meta.verbo, meta.objetivo), inv, visitado=set(), prof=0)
            if pasos is not None and (mejor is None or pasos.coste < mejor.coste):
                mejor = pasos
        if mejor is not None:
            self.proponer(ctx, mejor.verbo, mejor.objetivo, mejor.arousal, mejor.confianza, mejor.motivo, clase=mejor.clase)
        else:
            self._explorar_efectos(ctx, inv)          # 5.2

    def _resolver(self, ctx, accion, inv, visitado, prof) -> Optional[Paso]:
        """Devuelve la primera acción ejecutable que acerca a «accion», con su coste estimado."""
        if prof > self.PROFUNDIDAD or accion in visitado:
            return None
        visitado = visitado | {accion}
        r = ctx.memoria.requisitos.get(accion)            # puede no existir: se intenta sin requisitos
        faltan_inv = {k: (n or 1) - inv.get(k, 0) for k, n in (r.requiere_inventario if r else {}).items()
                      if inv.get(k, 0) < (n or 1)}
        faltan_cerca = [c for c in (r.requiere_cerca if r else ()) if not al_alcance_clase(ctx, c)]
        if not faltan_inv and not faltan_cerca:
            return self._ejecutar(ctx, accion)            # USAR directo; COGER/COMER/ATACAR sobre la instancia más cercana
        mejor = None
        for item in faltan_inv:                           # conseguir lo que falta en el inventario
            for productora in productoras(ctx.memoria, item):    # requisitos cuyo produce/efecto da «item»
                p = self._resolver(ctx, productora, inv, visitado, prof + 1)
                mejor = p if p is not None and (mejor is None or p.coste < mejor.coste) else mejor
        for clase in faltan_cerca:                        # tener cerca una estructura
            ir = acercarse_a_clase(ctx, clase)            # visible o recordada (memoria.donde_esta / ruta)
            if ir is not None:
                mejor = ir if mejor is None or ir.coste < mejor.coste else mejor
            for colocadora in colocadoras(ctx.memoria, clase):   # requisitos cuyo efecto pone «clase» (place_table)
                p = self._resolver(ctx, colocadora, inv, visitado, prof + 1)
                mejor = p if p is not None and (mejor is None or p.coste < mejor.coste) else mejor
        return mejor
```

- **Coste:** número de submetas pendientes, más la distancia (en pasos) a la instancia objetivo. Si no se ve ninguna, un coste alto fijo, y se recurre a la memoria (`donde_esta`).
- **`_ejecutar` sobre una clase** (COGER piedra): si hay una instancia al alcance, la acción. Si se ve pero está lejos, MOVER hacia ella. Si no se ve, ir adonde se recuerda. Si no se recuerda, `None`: no hay plan, y entra la exploración normal (S1 y `Curiosidad`).
- **Arousal y confianza:** arousal 0,5 (el mismo rango que `PlanTecnologico`, para no cambiar el equilibrio con la supervivencia hasta el paso 0); confianza = la del requisito usado (`Requisito.confianza`). Una cadena de requisitos poco fiables propone con menos confianza, y el Tribunal ya pondera eso.
- **Motivo legible:** «metas: make_stone_pickaxe ← falta piedra ← COGER piedra». Es la conducta explicable que queremos mostrar.
- **Fallos:** si la acción propuesta falla, `aprender_requisito` (paso 2) lo anota en `intentos`. Para no repetir en bucle: tras 3 fallos seguidos de la misma acción sin cambios en el inventario, esa acción queda bloqueada hasta que cambie el inventario (sección 5.2).

**Navegación:** hay que reutilizar lo que ya existe en la base. Como referencia, `_ir_hacia_estructura` de `PlanTecnologico` usa la percepción, `memoria.donde_esta` y `memoria.ruta`. Esa lógica se mueve a una función general de S3 (`acercarse_a_clase`), sin nombres de Crafter. **Comprobar** qué datos de posición dan las entidades en mínimo y archivos. Si solo Crafter da `pos`, la función debe funcionar también sin ella (con la ruta topológica de la memoria).

## 5.2 Aprender lo que el manual no dice

Son tres mecanismos generales, todos en la memoria o en S3, sin nombres de Crafter:

**a) Inducción de requisitos por diferencia.** Cuando una acción que había fallado tiene éxito:
- se compara el inventario del éxito con los de los fallos (`intentos`);
- los objetos presentes en el éxito y ausentes en **todos** los fallos son requisitos candidatos;
- se añaden a `requiere_inventario` con `fuente="experiencia"`.

```python
def inducir(self, accion, inv_exito):
    fallos = self.intentos.get(accion, [])
    if not fallos:
        return
    candidatos = {k for k, v in inv_exito.items() if v >= 1 and all(f.get(k, 0) < 1 for f in fallos)}
    r = self.requisitos.setdefault(accion, Requisito(..., fuente="experiencia"))
    for k in candidatos:
        r.requiere_inventario.setdefault(k, 1)
```

Así se aprende, por ejemplo, que la piedra pide el pico de madera: COGER piedra falla sin pico, y funciona después de fabricarlo.

**b) Reintento tras novedad.** Una acción bloqueada por fallos repetidos se desbloquea cuando el inventario gana un tipo de objeto que no tenía. Biológicamente, es probar de nuevo con la herramienta nueva. Es lo que hace posible a).

**c) Exploración de efectos.** Sin plan, con calma (sin peligro a la vista) y con poca frecuencia, se prueba COGER sobre lo que se tiene delante y aún no se ha probado en esta vida. Es balbuceo motor. Se anota el efecto, aunque sea nulo.
- Los efectos **probabilísticos** (la hierba da un retoño 1 de cada 10 veces) se reconocen porque alguna vez hubo éxito. Una acción con algún éxito no se bloquea: tiene una tasa de éxito (`exitos / (exitos + fallos)`) y el coste del planificador la usa.
- Para poder probar con el suelo (la hierba), el adaptador debe dar **la clase de la casilla de delante** en la propiocepción (`carga["delante"]`). Es percepción legítima, porque se ve. **Comprobar** si ya existe algo así antes de añadirlo.

**d) Dónde se puede colocar.** `aprender_requisito` guarda también la clase de la casilla de delante en cada intento. Para una acción USAR:
- las clases donde funcionó forman `Requisito.requiere_delante`;
- una clase donde solo ha fallado se evita.

## 5.3 Borrar `PlanTecnologico`

- Se quita de `estrategias_propias()` y se borra la clase, junto con `OBJETIVOS`, `RECURSO`, `LOGROS_PLAN` y el uso de `self.constantes.make/place`.
- **Lo que hacía y se pierde a propósito:**
  - dormir de día con energía baja: vuelve en los pasos 0 y 3;
  - la prioridad fija de minerales baratos: el planificador lo cubre si los minerales son metas.
- `RefugioNocturno` usa recetas propias (fabricar pico y espada, colocar mesa) como conducta de refugio. **No se toca en este paso**: va con el paso 3. Hay que anotarlo en `INVENTARIO_CONOCIMIENTO_CRAFTER.md` como pendiente.

**Tests:**
- con un manual de juguete (A requiere B; B se obtiene cogiendo C), el planificador propone COGER C;
- la inducción por diferencia aprende un requisito tras un fallo y un éxito;
- el reintento tras novedad desbloquea;
- con el manual vacío, `PerseguirMetas` no es elegible.

## 5.4 Mediciones (Flash)

Protocolo oficial abreviado: 100 000 pasos, semilla 31, vista 9×7, Equilibrado y **sin herencia**. En secuencia:

| Medición | Qué es | Comparar con | Expectativa (escrita antes) |
|---|---|---|---|
| G1 | Suelo (`--sin-estrategias-propias`) + planificador, manual estricto | Suelo: 1,46 % | **Subida clara**: madera, mesa, pico y espada de madera, retoño y planta. Entre 3 y 8 % |
| G2 | Igual, con manual ampliado | G1 | Algo mayor: no tiene que descubrir cantidades ni herramientas |
| G3 | `main` sin `PlanTecnologico` + planificador, estricto | `main`: 19,18 % | Pérdida moderada (dormir de día, minerales) |
| G4 | Igual, con manual ampliado | 19,18 % | Pérdida pequeña |
| P1 | G3 con una receta cambiada desde el arnés (la mesa pide 3 de madera) | G3 | Casi igual: el planificador lo aprende |
| — | `invariancia.py` en mínimo, archivos y ajedrez | — | OK |

Además, para G1 y G3, **qué requisitos aprendió** la última vida de algunos episodios: un volcado de `memoria.requisitos` con su fuente. Es la prueba de que aprende lo que el manual no dice.

**Coste:** unas 2 h 30 min de máquina. Puede ir de noche.

## 6. Criterios de aceptación

1. **Pilar 1, parcial:** `PlanTecnologico` borrado y ninguna receta de Crafter en `crafter.py` fuera del manual.
2. G1 es significativamente mayor que el suelo (1,46 %).
3. G4 no pierde más de 3 puntos frente a 19,18 % (margen declarado antes de medir).
4. P1 (receta cambiada) no pierde de forma significativa frente a G3.
5. Invariancia OK en los otros mundos; tests, ruff y mypy en verde.

Si G1 no sube, el problema está en la navegación o en la exploración, no en el planificador. Se diagnostica con los motivos legibles de las propuestas antes de cambiar nada.
