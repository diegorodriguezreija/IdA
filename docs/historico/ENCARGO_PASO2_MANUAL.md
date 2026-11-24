# Encargo del paso 2: el manual declarativo

Fase de generalización (`docs/FASE_GENERALIZACION_CRAFTER.md`), paso 2. Rama nueva `feature/manual-crafter` desde `main`.

**Modelos:** 2.0 y 2.1, Flash; 2.2 y 2.3, Opus 5.5 (o Argon); 2.4, Flash.

**Reglas de siempre:**
- No hacer push de `main`.
- Ninguna cifra sin su fichero de salida.
- Benchmarks en secuencia, nunca dos a la vez.

---

## 1. Qué se quiere y qué no

**Objetivo:** que todo lo que IdA sabe de Crafter **antes de vivir** esté en un manual declarativo, con la fuente de cada hecho, y que entre en la memoria del individuo como conocimiento de autoridad (`c_aut`), refutable por la experiencia.

**Qué no es este paso:**
- No crea ninguna conducta nueva. Nadie usará todavía las recetas: el planificador general que las use es el paso 5.
- No toca `PlanTecnologico`, que pertenece a la línea procedimental congelada. Su receta sale del mundo en el paso 5, cuando se borre entero.
- No quita la aliestesia del adaptador (`_deseo`), que pasa al paso 0 (sección 6).

**Lo que sí cambia la conducta:** los valores de peligro del adaptador (`HOSTILES`) pasan a salir del manual. Con el manual estricto, **la lava deja de ser peligrosa de entrada**, porque ni el artículo ni el README dicen que lo sea. Es una pérdida esperada y honesta.

## 2. Por qué hace falta tocar el núcleo

Hoy la memoria solo puede saber tres relaciones de una clase: `nutre`, `hace daño` y `sirve` (`Relacion`, en `ida/core/vocabulario.py`). Una receta («para fabricar un pico de madera hace falta madera y tener una mesa cerca») no cabe ahí.

Hace falta una forma general de conocimiento: **los requisitos de una acción**, es decir, qué tiene que darse para que una acción sobre un objetivo tenga efecto y qué efecto tiene. Es la representación clásica de precondiciones y efectos. No es específica de Crafter: sirve para cualquier mundo con fabricación, herramientas o llaves.

---

## 2.0 Inventario del conocimiento implícito del adaptador (Flash)

Antes de escribir nada, hay que listar todo lo que `ida/mundos/crafter.py` sabe de Crafter **fuera de la percepción pura**. Ya conocidos:

| Dónde | Qué sabe | Qué será |
|---|---|---|
| `HOSTILES` (zombi 0,8; esqueleto 0,7; flecha 0,5; lava 1,0) | Qué hace daño y cuánto | Manual (paso 2) |
| `observar`: `recurso` = 0,6 para árbol, piedra, carbón, hierro y diamante | Qué sirve | Manual (paso 2) |
| `_deseo` (aliestesia: agua según sed, vaca o planta madura según hambre, ×1,3 si salud < 7) | Qué satisface cada necesidad y la regla de regeneración | Paso 0 |
| `self.constantes` en `PlanTecnologico` (`make`, `place`) | Recetas y cantidades | Paso 5 |
| `self.constantes.walkable` en `observar` | Por dónde se puede andar | Percepción: se ve si una casilla está libre. Se mantiene |

**Tarea:** recorrer el fichero entero (incluidas las estrategias) y completar esta tabla con cada constante, umbral o regla que codifique un hecho de Crafter: línea, qué sabe y si sale del artículo o el README, del código de Crafter, o de lo que medimos nosotros.

**Entregable:** `docs/INVENTARIO_CONOCIMIENTO_CRAFTER.md`. Sin cambios de código.

## 2.1 El manual (Flash, con verificación literal)

Dos ficheros: `ida/mundos/crafter_manual.json` (estricto) y `ida/mundos/crafter_manual_ampliado.json`.

**Regla de procedencia:**
- **Estricto:** solo el artículo (Hafner, 2021, arXiv:2109.06780v2) y el README de `danijar/crafter`.
- **Ampliado:** el estricto más hechos de `crafter/data.yaml`, `objects.py` y `env.py`, cada uno con su fichero y línea.

**Cada hecho lleva una cita literal corta (menos de 15 palabras) y su lugar** (sección, tabla o línea). **Verificación:** el autor descarga el PDF y lo deja **fuera del repositorio**, por ejemplo en `f:\fuentes\crafter.pdf`. Flash comprueba que cada cita aparece literalmente en el PDF o en el README. Si no la encuentra, el hecho no entra.

**Formato:**

```json
{
  "fuentes": {"articulo": "Hafner (2021), arXiv:2109.06780v2", "readme": "danijar/crafter, README"},
  "hechos": [
    {"id": "P01", "tipo": "proposicion", "sujeto": "vaca", "relacion": "NUTRITIVO", "veredicto": "afirma",
     "cita": "eating cows or fruit", "lugar": "artículo, 3.1"},
    {"id": "R01", "tipo": "requisito", "verbo": "USAR", "objetivo": "make_wood_pickaxe",
     "requiere_inventario": {"madera": null}, "requiere_cerca": ["mesa"],
     "cita": "Nearby table; wood in inventory.", "lugar": "artículo, tabla F.1"},
    {"id": "N01", "tipo": "nota", "texto": "las plantas se cosechan cientos de pasos después",
     "cita": "can be harvested many hundred time steps later", "lugar": "artículo, 3.4"}
  ]
}
```

- `sujeto` y `objetivo` usan los nombres del adaptador (`MATERIALES`, `OBJETOS` e `INVENTARIO`: «vaca», «madera», «pico_madera»…) y los nombres de acción que ya usa `USAR` (`make_wood_pickaxe`, `place_table`…).
- `null` en una cantidad significa «hace falta al menos uno; la cantidad exacta se desconoce».
- Los hechos de tipo `nota` no se cargan: documentan lo que el artículo dice y aún no se puede representar (ritmos de necesidades, la noche, dormir a salvo…). Servirán para las pautas innatas de los pasos 0 y 3.

**Borrador del manual estricto** (extraído del artículo; **todas las citas hay que verificarlas literalmente**):

| Tipo | Hecho | Fuente aproximada |
|---|---|---|
| Proposición | agua NUTRITIVO | 3.1: se restauran «drinking from lakes» |
| Proposición | vaca NUTRITIVO | 3.1: «Cows move randomly and offer a food source» |
| Proposición | planta NUTRITIVO (fruto) | 3.1: «eating cows or fruit»; 4.3 «eats the growing fruits» |
| Proposición | zombi PELIGROSO | 3.1: daño «when attacked by monsters» y zombis |
| Proposición | esqueleto PELIGROSO, flecha PELIGROSO | 3.1: «shoot arrows at the player» |
| Proposición | árbol, piedra, carbón, hierro y diamante, UTIL | 3.1: «Resources include saplings, wood, stone, coal, iron, and diamonds» |
| Proposición | mesa UTIL, horno UTIL | 3.1: la mesa y el horno permiten fabricar |
| Requisito | `place_table`: madera | Tabla F.1 |
| Requisito | `place_furnace`: piedra | Tabla F.1 |
| Requisito | `place_stone`: piedra | Tabla F.1 |
| Requisito | `place_plant`: retoño | Tabla F.1 |
| Requisito | `make_wood_pickaxe`, `make_wood_sword`: madera; cerca, mesa | Tabla F.1 |
| Requisito | `make_stone_pickaxe`, `make_stone_sword`: madera y piedra; cerca, mesa | Tabla F.1 |
| Requisito | `make_iron_pickaxe`, `make_iron_sword`: madera, carbón y hierro; cerca, mesa y horno | Tabla F.1 |
| Requisito | COGER diamante: pico_hierro | 3.4 |
| Notas | necesidades que bajan y se restauran; salud que se regenera sin hambre, sed ni sueño; dormir donde no llegan monstruos; noche con vista reducida y más zombis; esqueletos en cuevas; zombis y vacas en pradera; dormir requiere energía por debajo del máximo; plantas cosechables cientos de pasos después | 3.1, 3.4 y tabla F.1 |

**Lo que el manual estricto no dice** y por tanto IdA tendrá que aprender (o el ampliado declarar):
- las cantidades (cuánta madera pide la mesa, cuánta piedra el horno);
- qué herramienta pide cada material, salvo el diamante;
- que el retoño sale de la hierba;
- sobre qué casillas se puede colocar cada cosa;
- que la lava mata.

Es justo la diferencia que medirán las dos cifras.

## 2.2 Representación y carga en el núcleo (Opus 5.5; pseudocódigo mío)

**Mundo** (`ida/core/mundo.py`):

```python
def manual(self) -> Dict[str, Any]:
    """Hechos declarados del mundo (instrucciones). Por defecto, ninguno."""
    return {}
```

El adaptador de Crafter lo implementa leyendo el JSON; una opción del adaptador elige entre `"estricto"` (por defecto) y `"ampliado"`.

**Memoria** (`ida/core/memoria.py`):

```python
@dataclass
class Requisito:
    verbo: Verbo
    objetivo: str
    requiere_inventario: Dict[str, Optional[int]]   # None = al menos 1, cantidad desconocida
    requiere_cerca: Set[str]
    efecto: Dict[str, int] = field(default_factory=dict)   # cambio de inventario observado (aprendido)
    fuente: str = "manual"                          # "manual" | "experiencia"
    confianza: float = 0.8                          # c_aut inicial; la experiencia la mueve
    exitos: int = 0
    fallos: int = 0

class Memoria:
    requisitos: Dict[Tuple[Verbo, str], Requisito]
    intentos: Dict[Tuple[Verbo, str], List[Dict[str, int]]]   # inventario en cada intento fallido (para el paso 5)

    def aplicar_manual(self, manual: Dict[str, Any]) -> int:
        """Al nacer, antes de heredar. Proposiciones con c_aut; requisitos con fuente 'manual'."""
        for h in manual.get("hechos", []):
            if h["tipo"] == "proposicion":
                p = self.proposicion(h["sujeto"], Relacion[h["relacion"]], crear=True)
                p.aplicar_autoridad(h["veredicto"], confianza_fuente=0.8, peso_fuente=1.0, ahora=0)  # API existente (Fase 3)
            elif h["tipo"] == "requisito":
                self.requisitos[(Verbo[h["verbo"]], h["objetivo"])] = Requisito(...)
        return n

    def aprender_requisito(self, verbo, objetivo, inv_antes, inv_despues, cerca, exito) -> None:
        """Tras cada acción USAR o COGER con objetivo."""
        r = self.requisitos.get((verbo, objetivo))
        delta = {k: inv_despues[k] - inv_antes[k] for k in inv_antes if inv_despues[k] != inv_antes[k]}
        if exito:
            if r is None:   # requisito descubierto por experiencia
                r = self.requisitos[(verbo, objetivo)] = Requisito(verbo, objetivo, {}, set(cerca), fuente="experiencia")
            r.exitos += 1
            r.efecto = delta
            for k, d in delta.items():               # lo consumido fija la cantidad mínima
                if d < 0:
                    r.requiere_inventario[k] = max(r.requiere_inventario.get(k) or 0, -d)
            r.confianza = acotar(r.confianza + 0.1)
        else:
            self.intentos.setdefault((verbo, objetivo), []).append(dict(inv_antes))
            if r is not None and self._cumplia(r, inv_antes, cerca):
                r.fallos += 1
                # creía cumplir y falló: alguna cantidad desconocida es mayor
                for k, n in r.requiere_inventario.items():
                    if n is None or n <= inv_antes.get(k, 0):
                        r.requiere_inventario[k] = inv_antes.get(k, 0) + 1
                r.confianza = acotar(r.confianza - 0.1)
```

- **Dónde se llama:** `aplicar_manual`, en el nacimiento (`ejecutor.py` / `Organismo`), antes de `heredar`, para que lo heredado pueda corregir el manual. `aprender_requisito`, en el paso de aprendizaje del latido, con el `Efecto` que ya devuelve el mundo.
- **Herencia:** los requisitos con `exitos ≥ 1` pasan al legado, como los registros. Con `--sin-herencia`, nada.
- **Invariancia:** con `manual() == {}` no cambia nada en mínimo, archivos ni ajedrez. Es requisito de aceptación.
- **Referencia útil:** `origin/feature/fase5-ciclo-y-refugio` (commit `a71eaf2`) tiene una infraestructura parecida para la dotación innata (`aplicar_dotacion`, `c_inst`). Se puede reutilizar su patrón. **No se fusiona esa rama.**

**Tests:**
- el manual vacío no cambia nada;
- una proposición del manual queda con `c_aut` y la experiencia la puede refutar;
- un éxito de `place_table` con 2 de madera consumida fija la cantidad en 2;
- un fallo con 1 de madera, creyendo que bastaba, sube la cantidad a 2;
- los requisitos pasan al legado solo con `exitos ≥ 1`.

## 2.3 El adaptador lee el manual (Opus 5.5)

- `HOSTILES` desaparece. El `peligro` de una clase es 0,8 si el manual cargado dice que es PELIGROSO, y 0 si no. **Las gradaciones de antes (0,7, 0,5…) no salen de ninguna fuente**, así que no se mantienen.
- `recurso` = 0,6 para las clases que el manual declara UTIL.
- La aliestesia (`_deseo`) no se toca, pero lleva un comentario que dice que es deuda del paso 0.
- **Comprobación:** con el manual ampliado (que declara la lava), la conducta de Crafter debe ser casi la de antes. Se mide en 2.4.

## 2.4 Mediciones (Flash)

Protocolo oficial abreviado: 100 000 pasos, semilla base 31, vista 9×7, Equilibrado y **sin herencia**. En secuencia:

| Medición | Qué es | Comparar con |
|---|---|---|
| M1 | Suelo con manual estricto (`--sin-estrategias-propias`) | Suelo actual: 1,46 % |
| M2 | Suelo con manual ampliado | M1 |
| M3 | `main` con manual estricto | `main` sin herencia: 19,18 % |
| M4 | `main` con manual ampliado | 19,18 % |
| — | `invariancia.py` en mínimo, archivos y ajedrez | Debe dar OK. Crafter cambia por diseño |

**Expectativa, escrita antes de medir:**
- M1 y M2 apenas se moverán respecto al suelo. El adaptador ya daba peligro y nutrición, y nadie usa todavía las recetas.
- M3 puede perder algo por la lava (muertes por lava frente al 0,4 % actual).
- M4 debería quedar dentro del intervalo de 19,18 %.

**Si M4 cae de forma significativa**, hay un error en el traslado y se para.

**Entregable:** `docs/MEDICION_PASO2.md`, generado con `resumen_evaluacion.py`, ampliado para estas condiciones.

## 3. Criterios de aceptación

1. Cada hecho del manual estricto tiene una cita literal verificada en el artículo o el README.
2. `invariancia.py` da OK en mínimo, archivos y ajedrez.
3. M4 no es peor de forma significativa que `main` (19,18 %).
4. Tests nuevos en verde; ruff y mypy en verde.
5. `docs/INVENTARIO_CONOCIMIENTO_CRAFTER.md` completo: es la lista de lo que falta por trasladar en los pasos siguientes.

## 4. Lo que queda fuera (y a qué paso va)

- **Aliestesia y separación de hambre y sed → paso 0.** Hoy Crafter declara una sola necesidad, `alimentacion = min(comida, bebida)`, y es el adaptador el que decide si el agua o la vaca «apetece» según cuál falta. Eso es pensar por el individuo. Con dos necesidades (hambre y sed), cada una con su intensidad, la elección pasa a la base, que es justo el tema del paso 0.
- **Uso de los requisitos (planificador general) → paso 5.**
- **Aprender qué herramienta pide un material** a partir de `intentos` → paso 5.
