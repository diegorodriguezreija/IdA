"""Crafter (Hafner, 2021): mundo de supervivencia en 2D con recursos, criaturas, día y noche.

Traducción al vocabulario común:
- Cuerpo: el juego marca salud, comida, bebida y energía (``vitales_propios``). La alimentación
  del soma es el mínimo entre comida y bebida.
- Entidades del entorno cercano (radio 4, como la vista oficial de 9×9; radio 2 de noche):
  árboles, agua, piedra, carbón, hierro, diamante, mesa, horno, lava, hierba, vacas, zombis,
  esqueletos y plantas. **Aliestesia:** el ``nutritivo`` del agua crece con la sed y el de la
  vaca o la planta madura, con el hambre.
- Lugares: las casillas vecinas transitables, con ``nutritivo`` (cuánto acercan a lo que el
  cuerpo necesita), ``peligro`` (lava o criaturas hostiles cerca) y ``novedad``.
- Verbos: MOVER, COMER (beber agua, comer vaca o planta), ATACAR, COGER (talar, picar, recoger
  un retoño), USAR (colocar o fabricar, con la receta en la carga), DORMIR y ESPERAR. Para
  interactuar con algo adyacente, el mundo primero gira hacia ello y después hace ``do``.

Diferencias con el benchmark oficial: IdA lee el estado simbólico del juego, no los píxeles, y
el plan tecnológico es un **componente propio de este mundo** escrito a mano (``PlanTecnologico``).

Componente propio:
- ``PlanTecnologico`` (S3 · Reaccionar): con las recetas del juego (``crafter.constants``) decide
  qué fabricar o colocar y hacia qué recurso ir; además aprovecha logros baratos (retoño,
  plantar, carbón, hierro, diamante). Puntúa por debajo de la supervivencia.
"""

from collections import deque
import collections
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.core.arquitectura import Contexto
from ida.core.estrategia import ConPropuestas, Definicion, Plan, Propuesta, estado_plan
from ida.core.mundo import Efecto, Entidad, Mundo, Necesidad, Observacion, Perfil
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Verbo

MATERIALES = {"tree": "arbol", "water": "agua", "stone": "piedra", "coal": "carbon", "iron": "hierro",
              "diamond": "diamante", "table": "mesa", "furnace": "horno", "lava": "lava"}
OBJETOS = {"Cow": "vaca", "Zombie": "zombi", "Skeleton": "esqueleto", "Plant": "planta", "Arrow": "flecha"}
HOSTILES = {"zombi": 0.8, "esqueleto": 0.7, "flecha": 0.5, "lava": 1.0}
MOVIMIENTOS = {(-1, 0): "move_left", (1, 0): "move_right", (0, -1): "move_up", (0, 1): "move_down"}
LETRA = {"arbol": "T", "agua": "~", "piedra": "#", "carbon": "c", "hierro": "i", "diamante": "D", "mesa": "M", "horno": "H",
         "lava": "!", "vaca": "v", "zombi": "Z", "esqueleto": "S", "planta": "p", "flecha": "-"}
LOGROS = 22
INVENTARIO = {"wood": "madera", "stone": "piedra", "coal": "carbon", "iron": "hierro", "diamond": "diamante", "sapling": "retoño",
              "wood_pickaxe": "pico_madera", "stone_pickaxe": "pico_piedra", "iron_pickaxe": "pico_hierro",
              "wood_sword": "espada_madera", "stone_sword": "espada_piedra", "iron_sword": "espada_hierro"}

Pos = Tuple[int, int]


class _ConjuntoOrdenado:
    """Conjunto que recuerda el orden de inserción.

    Crafter guarda las criaturas de cada zona en un ``set``, que se ordena por dirección de memoria; al despoblar
    una zona elige una criatura por índice, así que la misma semilla no daba siempre la misma vida. Con este
    conjunto el orden solo depende de la historia del mundo.
    """

    def __init__(self) -> None:
        self._d: Dict[Any, None] = {}

    def add(self, x: Any) -> None:
        self._d[x] = None

    def remove(self, x: Any) -> None:
        del self._d[x]

    def discard(self, x: Any) -> None:
        self._d.pop(x, None)

    def __contains__(self, x: Any) -> bool:
        return x in self._d

    def __iter__(self) -> Any:
        return iter(list(self._d))

    def __len__(self) -> int:
        return len(self._d)


def _dist(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class MundoCrafter(Mundo):
    nombre = "crafter"
    perfil = Perfil(frecuencia_ms=100.0, amplitud=120, memoria="completa", duerme=True, hogar=True,
                    peso_experiencia=0.15, vitales_propios=True,
                    necesidades=(Necesidad("hambre", ("comida",), 95.0, "nutritivo"), Necesidad("sed", ("agua",), 95.0, "nutritivo"),
                                 Necesidad("cansancio", ("energia",), 60.0), Necesidad("salud", ("vitalidad",), 100.0),
                                 Necesidad("cobijo", ("cobijo",), 100.0)),
                    intenciones=("progresar",))

    def __init__(self, radio: Any = 4, ventana: Any = 0, **_):
        import crafter                     # dependencia solo de este mundo
        from crafter import constants
        self._crafter = crafter
        self.constantes = constants
        self.acciones = {nombre: i for i, nombre in enumerate(constants.actions)}
        self.radio = int(radio)
        self.ventana = str(ventana) in ("1", "si", "sí", "true")
        self.env: Any = None
        self.visitas: Dict[Pos, int] = {}
        self.t = 0
        self.fin = False
        self._tk: Any = None
        self._label: Any = None
        self._photo: Any = None

    # --- ciclo de vida -------------------------------------------------------
    def reiniciar(self, semilla: Optional[int]) -> None:
        self.env = self._crafter.Env(seed=semilla, length=100000)
        mundo = self.env._world
        reset_original = mundo.reset

        def reset_ordenado(seed: Any = None) -> None:      # repetible: zonas con orden de inserción
            reset_original(seed=seed)
            mundo._chunks = collections.defaultdict(_ConjuntoOrdenado)

        mundo.reset = reset_ordenado
        self.env.reset()
        self.visitas, self.t, self.fin = {}, 0, False
        # Identificador estable y repetible para cada criatura. La clave es el propio objeto (no id(obj)):
        # así sigue vivo y su dirección no se reutiliza para otra criatura, lo que hacía la vida no repetible.
        self._ids: Dict[object, str] = {}
        self._actualizar_ventana()

    def _actualizar_ventana(self) -> None:
        if not self.ventana or self.env is None:
            return
        try:
            import tkinter as tk
            from PIL import Image, ImageTk
            if self._tk is None:
                self._tk = tk.Tk()
                self._tk.title("Crafter · IdA")
                self._tk.resizable(False, False)
                self._label = tk.Label(self._tk)
                self._label.pack()

                def _al_cerrar():
                    self.ventana = False
                    if self._tk:
                        self._tk.destroy()
                        self._tk = None

                self._tk.protocol("WM_DELETE_WINDOW", _al_cerrar)
            img = self.env.render()
            pil_img = Image.fromarray(img).resize((400, 400), Image.Resampling.NEAREST)
            self._photo = ImageTk.PhotoImage(pil_img)
            self._label.config(image=self._photo)
            self._tk.update()
        except Exception:
            pass

    def cerrar(self) -> None:
        if self._tk is not None:
            try:
                self._tk.destroy()
            except Exception:
                pass
            self._tk = None

    @property
    def jugador(self):
        return self.env._player

    def inventario(self) -> Dict[str, int]:
        return dict(self.jugador.inventory)

    def _vitales(self) -> Dict[str, float]:
        inv = self.jugador.inventory
        w = self.env._world
        return {"vitalidad": self.jugador.health / 9 * 100, "alimentacion": min(inv["food"], inv["drink"]) / 9 * 100,
                "energia": inv["energy"] / 9 * 100, "descanso": inv["energy"] / 9 * 100,
                "comida": inv["food"] / 9 * 100, "agua": inv["drink"] / 9 * 100,
                "cobijo": max(2.0, float(w.daylight) * 100)}

    # --- percepción ----------------------------------------------------------
    def _vista_local(self) -> Dict[Pos, str]:
        """Rejilla cruda (coordenada -> material) de todas las casillas dentro del radio de visión actual."""
        w, (px, py) = self.env._world, self.jugador.pos
        radio = self.radio if w.daylight >= 0.3 else max(2, self.radio // 2)
        vista: Dict[Pos, str] = {}
        for x in range(px - radio, px + radio + 1):
            for y in range(py - radio, py + radio + 1):
                if 0 <= x < w.area[0] and 0 <= y < w.area[1]:
                    mat, _ = w[(int(x), int(y))]
                    if mat is not None:
                        vista[(int(x), int(y))] = str(mat)
        return vista

    def _cosas(self) -> List[Tuple[str, str, Pos, Any]]:
        """(id, clase, posición, objeto) de lo que hay en el radio de visión."""
        w, (px, py) = self.env._world, self.jugador.pos
        radio = self.radio if w.daylight >= 0.3 else max(2, self.radio // 2)
        cosas = []
        for x in range(px - radio, px + radio + 1):
            for y in range(py - radio, py + radio + 1):
                if not (0 <= x < w.area[0] and 0 <= y < w.area[1]) or (x, y) == (px, py):
                    continue
                mat, obj = w[(x, y)]
                if mat in MATERIALES:
                    cosas.append((f"{MATERIALES[mat]}_{x}_{y}", MATERIALES[mat], (x, y), None))
                if obj is not None and type(obj).__name__ in OBJETOS:
                    clase = OBJETOS[type(obj).__name__]
                    if obj not in self._ids:
                        self._ids[obj] = f"{clase}_{len(self._ids) + 1}"
                    cosas.append((self._ids[obj], clase, (x, y), obj))
        return cosas

    def _deseo(self, clase: str, obj: Any) -> float:
        """Aliestesia: lo que vale cada cosa para el cuerpo depende de lo que le falta."""
        inv = self.jugador.inventory
        salud = self.jugador.health
        # Homeostasis de reparación: si la salud está mermada, comer/beber es aún más prioritario
        # para activar la regeneración pasiva del organismo (+1 salud cada 25 pasos si hay comida y bebida).
        urgencia_reparacion = 1.3 if salud < 7 else 1.0
        if clase == "agua":
            return min(1.0, max(0.1, (9 - inv["drink"]) / 9 * urgencia_reparacion))
        if clase == "vaca" or (clase == "planta" and obj is not None and getattr(obj, "ripe", False)):
            return min(1.0, max(0.1, (9 - inv["food"]) / 9 * urgencia_reparacion))
        return 0.0

    def observar(self) -> Observacion:
        p = self.jugador
        pos = tuple(p.pos)
        cosas = self._cosas()
        cosas.sort(key=lambda c: (c[1] not in HOSTILES, _dist(pos, c[2])))
        entidades: List[Entidad] = []
        for cid, clase, cpos, obj in cosas[:14]:
            d = _dist(pos, cpos)
            entidades.append(Entidad(cid, clase, {
                "proximidad": 1.0 if d <= 1 else max(0.0, 1.0 - d / (2 * self.radio + 1)),
                "nutritivo": self._deseo(clase, obj),
                "peligro": HOSTILES.get(clase, 0.0),
                "recurso": 0.6 if clase in ("arbol", "piedra", "carbon", "hierro", "diamante") else 0.0,
                "agente": 1.0 if obj is not None and clase != "planta" else 0.0,
            }, {"pos": cpos}))
        deseables = [(c, self._deseo(c[1], c[3])) for c in cosas if self._deseo(c[1], c[3]) > 0.1]
        hostiles = [c for c in cosas if c[1] in HOSTILES]
        w = self.env._world
        for (dx, dy), _ in MOVIMIENTOS.items():
            c = (pos[0] + dx, pos[1] + dy)
            if not (0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1]):
                continue
            mat, obj = w[c]
            if mat not in self.constantes.walkable or obj is not None:
                continue
            peligro = max([HOSTILES[h[1]] * max(0.0, 1.0 - _dist(c, h[2]) / 4.0) for h in hostiles] or [0.0])
            nutritivo = 0.0
            for (_, _, dpos, _), valor in deseables:
                if _dist(c, dpos) < _dist(pos, dpos):
                    nutritivo = max(nutritivo, valor * (1.0 - _dist(c, dpos) / (4 * self.radio)))
            ultima = self.visitas.get(c)
            novedad = 1.0 if ultima is None else min(1.0, (self.t - ultima) / 50.0)
            entidades.append(Entidad(f"celda_{c[0]}_{c[1]}", "suelo", {"lugar": 1.0, "proximidad": 1.0, "peligro": peligro,
                                                                       "nutritivo": nutritivo, "novedad": novedad}, {"pos": c, "terreno": mat}))

        return Observacion(ubicacion=f"celda_{pos[0]}_{pos[1]}", entidades=entidades, vitales=self._vitales(), dormido=bool(p.sleeping),
                           inventario={k: float(v) for k, v in p.inventory.items()},
                           cuerpo={"orientacion": (int(p.facing[0]), int(p.facing[1])), "vista": self._vista_local()},
                           ambiente={"luz": float(w.daylight)})

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COMER, Verbo.ATACAR, Verbo.COGER, Verbo.USAR, Verbo.DORMIR, Verbo.ESPERAR}

    def _paso(self, accion: str) -> None:
        _, _, terminado, _ = self.env.step(self.acciones[accion])
        self.t += 1
        self.fin = self.fin or terminado

    def _posicion(self, objetivo: str) -> Optional[Pos]:
        partes = objetivo.rsplit("_", 2)
        if len(partes) == 3 and partes[1].lstrip("-").isdigit() and partes[2].lstrip("-").isdigit():
            return int(partes[1]), int(partes[2])
        for cid, _, cpos, _ in self._cosas():
            if cid == objetivo:
                return cpos
        return None

    def _interactuar(self, objetivo: str) -> bool:
        pos, destino = tuple(self.jugador.pos), self._posicion(objetivo)
        if destino is None or _dist(pos, destino) != 1:
            return False
        direccion = (destino[0] - pos[0], destino[1] - pos[1])
        if tuple(self.jugador.facing) != direccion:
            self._paso(MOVIMIENTOS[direccion])      # bloqueado por el objetivo: solo gira
        self._paso("do")
        return True

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        p = self.jugador
        antes = {"salud": p.health, **dict(p.inventory)}
        logros_antes = {k for k, v in p.achievements.items() if v} if isinstance(p.achievements, dict) else set(p.achievements)
        exito = True
        if verbo == Verbo.MOVER:
            destino = self._posicion(objetivo)
            pos = tuple(p.pos)
            if destino is not None and _dist(pos, destino) == 1:
                self._paso(MOVIMIENTOS[(destino[0] - pos[0], destino[1] - pos[1])])
                self.visitas[tuple(p.pos)] = self.t
            else:
                exito = False
        elif verbo in (Verbo.COMER, Verbo.ATACAR, Verbo.COGER):
            exito = self._interactuar(objetivo)
            if exito and verbo == Verbo.COMER and p.inventory["food"] <= antes["food"] and p.inventory["drink"] <= antes["drink"]:
                exito = False      # un golpe a la vaca que aún no la abate: intento en curso, no prueba de que no nutra
            if exito and verbo == Verbo.COGER and not any(p.inventory[k] > antes[k] for k in INVENTARIO):
                exito = False      # coger solo es éxito si algo entra en el inventario
        elif verbo == Verbo.USAR:
            receta = datos.get("receta") or objetivo
            exito = receta in self.acciones
            if exito:
                self._paso(receta)
        elif verbo == Verbo.DORMIR:
            self._paso("sleep")
        else:
            self._paso("noop")
        ef = self._efecto(antes, logros_antes, exito)
        self._actualizar_ventana()
        return ef

    def _efecto(self, antes: Dict[str, int], logros_antes: Set[str], exito: bool) -> Efecto:
        p = self.jugador
        inv = p.inventory
        escala = 100.0 / 9.0
        delta = {
            "vitalidad": (p.health - antes["salud"]) * escala,
            "alimentacion": (min(inv["food"], inv["drink"]) - min(antes["food"], antes["drink"])) * escala,
            "energia": (inv["energy"] - antes["energy"]) * escala,
        }
        if inv["food"] > antes["food"] or inv["drink"] > antes["drink"]:   # comer o beber alimenta aunque la otra necesidad siga baja
            delta["alimentacion"] = max(delta["alimentacion"], (max(inv["food"] - antes["food"], inv["drink"] - antes["drink"])) * escala)
        delta = {k: round(v, 2) for k, v in delta.items() if v}
        causa = None
        if delta.get("vitalidad", 0) < 0:
            cerca = [c for c in self._cosas() if c[1] in HOSTILES and _dist(tuple(p.pos), c[2]) <= (4 if c[1] == "esqueleto" else 1)]
            if cerca:
                causa = cerca[0][1]
        ganados = [INVENTARIO.get(k, k) for k in inv if inv[k] > antes.get(k, 0) and k not in ("health", "food", "drink", "energy")]
        logros = {k for k, v in p.achievements.items() if v} if isinstance(p.achievements, dict) else set(p.achievements)
        nuevos = sorted(logros - logros_antes)
        return Efecto(exito, delta, causa=causa, obtenido=ganados[0] if ganados else None,
                      muerte=p.health <= 0, mensaje=("logro: " + ", ".join(nuevos)) if nuevos else "")

    def terminado(self) -> bool:
        return self.fin


    # --- resultados y vista --------------------------------------------------
    def logros(self) -> List[str]:
        a = self.jugador.achievements
        return sorted(k for k, v in a.items() if v) if isinstance(a, dict) else sorted(a)

    def estrategias_propias(self) -> Dict[str, list]:
        return {"S1": [DefensaArmada(), CerrarDistancia()], "S2": [RefugioNocturno()], "S3": [PlanTecnologico(self.constantes)]}

    def puntuacion(self) -> Dict[str, Any]:
        return {"logros": self.logros(), "n_logros": len(self.logros()), "pasos": self.t}

    def vista(self) -> str:
        pos = tuple(self.jugador.pos)
        mapa = {cpos: LETRA.get(clase, "?") for _, clase, cpos, _ in self._cosas()}
        filas = []
        for y in range(pos[1] - self.radio, pos[1] + self.radio + 1):
            filas.append("".join("@" if (x, y) == pos else mapa.get((x, y), ".") for x in range(pos[0] - self.radio, pos[0] + self.radio + 1)))
        inv = {k: v for k, v in self.jugador.inventory.items() if v}
        return "\n".join(filas) + f"\nluz {self.env._world.daylight:.2f} · {inv}\nlogros ({len(self.logros())}/{LOGROS}): {', '.join(self.logros())}"


ESPADAS = ("iron_sword", "stone_sword", "wood_sword")


def _salud(ctx: Contexto) -> int:
    """Salud de Crafter (0-9) desde la interocepción (``vitalidad`` = salud / 9 × 100)."""
    vit = ctx.onda.ev("Interocepcion").get("vitalidad")
    return int(round(float(vit.carga["valor"]) * 9 / 100)) if vit is not None else 0


def _tiene_espada(ctx: Contexto) -> bool:
    """Desde el inventario percibido (propiocepción), no desde el estado del juego."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    inv = yo.carga.get("inventario", {}) if yo is not None else {}
    return any(inv.get(k, 0) >= 1 for k in ESPADAS)


def _posicion(ctx: Contexto) -> Optional[Pos]:
    """Posición propia desde la ubicación percibida (``celda_x_y``)."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    partes = str(yo.carga.get("ubicacion", "")).split("_") if yo is not None else []
    return (int(partes[1]), int(partes[2])) if len(partes) == 3 and partes[0] == "celda" else None


class DefensaArmada(Definicion):
    """Estrategia de S1 propia de Crafter para Seguridad: con espada y salud ≥ 4, abatir al zombi o
    esqueleto adyacente (2-3 golpes) en vez de huir. Sin espada o con poca salud, luchar es suicidio
    y quedan las estrategias genéricas. Lee la salud por interocepción y la espada por el inventario
    percibido."""

    nombre = "defensa_armada"
    impulsos = ("seguridad",)
    prioridad = 50

    @staticmethod
    def _hostil(ctx: Contexto) -> Optional[Pieza]:
        if not _tiene_espada(ctx) or _salud(ctx) < 4:
            return None
        return next((p for p in ctx.onda.ev("Exterocepcion").values()
                     if p.clase in ("zombi", "esqueleto") and p.rasgo("proximidad") >= 0.9), None)

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return self._hostil(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        amenaza = self._hostil(ctx)
        if amenaza is None:
            return None
        urgencia = 0.96 if _salud(ctx) >= 6 else 0.88
        return Propuesta(Verbo.ATACAR, amenaza.id, urgencia, 0.95, f"defensa armada: abatir {amenaza.clase}", clase=amenaza.clase)


class CerrarDistancia(Definicion):
    """Estrategia de S1 propia de Crafter para Seguridad: con espada y salud ≥ 5, acercarse a un
    esqueleto que dispara desde 2-3 casillas (solo tiene 3 de vitalidad) en vez de ser diezmado en
    campo abierto."""

    nombre = "cerrar_distancia"
    impulsos = ("seguridad",)
    prioridad = 40

    @staticmethod
    def _paso(ctx: Contexto) -> Optional[Pieza]:
        if not _tiene_espada(ctx) or _salud(ctx) < 5:
            return None
        pos = _posicion(ctx)
        esq = next((p for p in ctx.onda.ev("Exterocepcion").values()
                    if p.clase == "esqueleto" and 0.4 <= p.rasgo("proximidad") < 0.9), None)
        if esq is None or pos is None:
            return None
        pos_esq = esq.carga["datos"]["pos"]
        lugares = [p for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5]
        mejor = min(lugares, key=lambda lugar: _dist(lugar.carga["datos"]["pos"], pos_esq), default=None)
        if mejor is None or _dist(mejor.carga["datos"]["pos"], pos_esq) >= _dist(pos, pos_esq):
            return None
        return mejor

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return self._paso(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        mejor = self._paso(ctx)
        if mejor is None:
            return None
        return Propuesta(Verbo.MOVER, mejor.id, 0.82, 0.85, "defensa armada: acortar distancia a esqueleto", clase=mejor.clase)


def _inventario(ctx: Contexto) -> Dict[str, float]:
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    return dict(yo.carga.get("inventario", {})) if yo is not None else {}


def _orientacion(ctx: Contexto) -> Optional[Pos]:
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    cara = yo.carga.get("cuerpo", {}).get("orientacion") if yo is not None else None
    return (int(cara[0]), int(cara[1])) if cara is not None else None


def _vista(ctx: Contexto) -> Dict[Pos, str]:
    """Rejilla cruda de materiales dentro del radio de visión actual, leída de la propiocepción."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    raw = yo.carga.get("cuerpo", {}).get("vista", {}) if yo is not None else {}
    return {(int(k[0]), int(k[1])): str(v) for k, v in raw.items()} if isinstance(raw, dict) else {}


def _terreno(ctx: Contexto) -> Dict[Pos, str]:
    """Terreno de las casillas libres a las que se puede ir (lugares percibidos)."""
    return {tuple(p.carga["datos"]["pos"]): p.carga["datos"].get("terreno", "")
            for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and "pos" in p.carga.get("datos", {})}


def _luz(ctx: Contexto) -> float:
    a = ctx.onda.ev("Ambiente").get("ambiente")
    return float(a.carga.get("luz", 1.0)) if a is not None else 1.0


NO_TRANSITABLES_ZOMBI = {"stone", "coal", "iron", "diamond", "water", "tree", "table", "furnace"}
ROCA_EXCAVABLE = {"stone", "coal"}
TRANSITABLES_JUGADOR = {"grass", "path", "sand"}


class RefugioNocturno(Definicion):
    """Estrategia propia de Crafter (S2) para el reloj circadiano («cobijo»): construir, reutilizar y
    ocupar un refugio excavado en roca durante la noche (sección 4 de ``docs/ENCARGO_CRAFTER_NOCHE.md``).

    Máquina de estados determinista disparada por lo percibido (regla 4):
    - ``madera``: reunir madera hasta cubrir mesa (2), pico de madera (1) y espada de madera (1).
    - ``herramientas``: colocar la mesa y fabricar pico y espada de madera.
    - ``provisiones``: beber y comer mientras los pasos restantes hasta la puesta de sol superen con
      holgura el coste estimado de llegar a la mina, excavar y cerrarse (contando que interactuar
      puede gastar 2 pasos de Crafter por latido).
    - ``elegir_mina``: seleccionar o mantener una mina percibida/recordada con 3 casillas en línea
      recta, laterales en cruz no transitables para un zombi, sin lava cerca ni túnel ajeno al fondo,
      valorando cercanía al agua y fidelidad al hogar/mina previa.
    - ``cavar``: acercarse a la entrada y picar las 3 casillas en línea recta hasta el fondo.
    - ``cerrarse``: desde el fondo, retroceder 1 casilla (quedando orientado hacia la entrada) y
      colocar piedra en la entrada.
    - ``dormir``: descansar dentro del refugio sellado; si despierta con energía máxima antes de que
      suba la luz, beber de una pared de agua adyacente o esperar sin abrir el sello.
    - ``amanecer``: cuando la luz sube, picar la piedra de la entrada (recuperándola) y salir.

    Solo lee la percepción (regla 3): el mapa de materiales lo recuerda la propia estrategia a partir
    de ``_vista(ctx)`` y se reinicia vacío al comenzar cada vida (``latido == 1``).
    Nota (pendiente de la base): en calma el Tribunal pondera sobre todo ``confianza`` y no recibe la
    intensidad del impulso; como apaño declarado del mundo, tanto ``arousal`` como ``confianza`` de la
    propuesta crecen de forma continua con la oscuridad y el coste de llegar y excavar la mina.
    """

    nombre = "refugio_nocturno"
    impulsos = ("cobijo",)
    prioridad = 20
    agotable = False

    RUMBO_PASOS = 12
    PACIENCIA_AVANCE = 10
    LUZ_PLENO_DIA = 0.83      # Crafter: con luz > 0,83 el máximo de zombis por zona (3,5 − 3·luz) baja de 1
    MEMORIA_VACA = 40         # latidos que se recuerda dónde se vio una vaca

    def __init__(self) -> None:
        self.mapa: Dict[Pos, str] = {}
        self.visitadas: Set[Pos] = set()
        self.rocas_inspeccionadas: Set[Pos] = set()
        self.mina_recordada: Optional[Tuple[Pos, Pos]] = None
        self._estado_mem: Dict[str, Any] = {}
        self.luz_previa: float = 0.0
        self.bajando: bool = False
        self.paso_oscuro: bool = False
        self.ultimo_latido: int = 0
        self.rumbo: Pos = (1, 0)
        self.pasos_rumbo: int = 0
        self.dominante: bool = False   # usado solo por el arnés de prueba de la Fase A
        self.vacas: Dict[Pos, int] = {}

    def _reiniciar_vida(self) -> None:
        self.vacas.clear()
        self.mapa.clear()
        self.visitadas.clear()
        self.rocas_inspeccionadas.clear()
        self.mina_recordada = None
        self._estado_mem.clear()
        self.luz_previa = 0.0
        self.bajando = False
        self.paso_oscuro = False
        self.ultimo_latido = 0
        self.rumbo = (1, 0)
        self.pasos_rumbo = 0

    def _actualizar_memoria(self, ctx: Contexto) -> None:
        if ctx.latido == 1 or ctx.latido < self.ultimo_latido:
            self._reiniciar_vida()
        self.ultimo_latido = ctx.latido
        luz = _luz(ctx)
        if luz > self.luz_previa + 1e-4:
            self.bajando = False
        elif luz < self.luz_previa - 1e-4:
            self.bajando = True
        if luz < 0.35:
            self.paso_oscuro = True
        self.luz_previa = luz
        vista = _vista(ctx)
        if vista:
            self.mapa.update(vista)
        pos = _posicion(ctx)
        vistas = {tuple(p.carga["datos"]["pos"]) for p in ctx.onda.ev("Exterocepcion").values()
                  if p.clase == "vaca" and "pos" in p.carga.get("datos", {})}
        for v in vistas:
            self.vacas[v] = ctx.latido
        for v, lat in list(self.vacas.items()):
            olvidada = ctx.latido - lat > self.MEMORIA_VACA
            if olvidada or (pos is not None and v not in vistas and _dist(pos, v) <= 1):
                del self.vacas[v]
        if pos is not None:
            self.visitadas.add(pos)
            for p, m in self.mapa.items():
                if m == "stone" and max(abs(pos[0] - p[0]), abs(pos[1] - p[1])) <= 2:
                    self.rocas_inspeccionadas.add(p)

    def _hay_hostil_cerca(self, ctx: Contexto, pos: Pos) -> bool:
        return any(
            p.clase in ("zombi", "esqueleto", "flecha") and "pos" in p.carga.get("datos", {})
            and _dist(pos, tuple(p.carga["datos"]["pos"])) <= 4
            for p in ctx.onda.ev("Exterocepcion").values()
        )

    def _mesa_cerca(self, pos: Pos) -> bool:
        return any(self.mapa.get((pos[0] + dx, pos[1] + dy)) == "table"
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1))

    def _mesa_conocida(self) -> Optional[Pos]:
        mesas = [p for p, m in self.mapa.items() if m == "table"]
        return mesas[0] if mesas else None

    def _falta_herramienta(self, inv: Dict[str, float]) -> bool:
        tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))
        tiene_espada = any(inv.get(k, 0) >= 1 for k in ESPADAS)
        return not (tiene_pico and tiene_espada)

    def _madera_faltante(self, inv: Dict[str, float]) -> int:
        tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))
        tiene_espada = any(inv.get(k, 0) >= 1 for k in ESPADAS)
        necesaria = (0 if tiene_pico else 1) + (0 if tiene_espada else 1)
        if necesaria > 0 and self._mesa_conocida() is None:
            necesaria += 2
        return max(0, necesaria - int(inv.get("wood", 0)))

    def _agua_accesible_dentro(self, mina: Optional[Tuple[Pos, Pos]]) -> Optional[Tuple[Pos, Pos]]:
        """Devuelve ``(casilla_desde_donde_beber, casilla_agua)`` si e2 o e3 tienen pared de agua."""
        if mina is None:
            return None
        e0, (dx, dy) = mina
        e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
        e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
        for ldx, ldy in ((-dy, dx), (dy, -dx)):
            vec2 = (e2[0] + ldx, e2[1] + ldy)
            if self.mapa.get(vec2) == "water":
                return e2, vec2
        for ldx, ldy in ((-dy, dx), (dy, -dx), (dx, dy)):
            vec3 = (e3[0] + ldx, e3[1] + ldy)
            if self.mapa.get(vec3) == "water":
                return e3, vec3
        return None

    def _evaluar_candidato(self, e0: Pos, d: Pos, pos_actual: Pos, hogar_pos: Optional[Pos]) -> Optional[float]:
        """Evalúa una mina con acceso ``e0`` y dirección de excavación ``d``. Devuelve su puntuación o None."""
        m0 = self.mapa.get(e0)
        if m0 not in TRANSITABLES_JUGADOR and e0 != pos_actual:
            return None
        dx, dy = d
        e1 = (e0[0] + dx, e0[1] + dy)
        e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
        e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
        es_recordada = self.mina_recordada == (e0, d) or (hogar_pos is not None and hogar_pos == e2)

        for idx, ek in enumerate((e1, e2, e3), start=1):
            mk = self.mapa.get(ek)
            if mk is None:
                return None
            if mk in ROCA_EXCAVABLE:
                pass
            elif mk == "path" and (es_recordada or pos_actual in (e0, e1, e2, e3)):
                pass
            else:
                return None
            # Condición de buen refugio: las casillas en cruz alrededor del hueco no son transitables para un zombi
            laterales = [(-dy, dx), (dy, -dx)]
            if idx == 3:
                laterales.append((dx, dy))   # fondo de la galería
            for ldx, ldy in laterales:
                vec = (ek[0] + ldx, ek[1] + ldy)
                mv = self.mapa.get(vec)
                if mv not in NO_TRANSITABLES_ZOMBI:
                    return None
                if idx >= 2 and mv == "water":
                    if any(self.mapa.get((vec[0] + k * ldx, vec[1] + k * ldy)) == "path" for k in (1, 2)):
                        return None

        # Sin lava en un entorno de radio 2 de la galería
        for x in range(min(e0[0], e3[0]) - 2, max(e0[0], e3[0]) + 3):
            for y in range(min(e0[1], e3[1]) - 2, max(e0[1], e3[1]) + 3):
                if self.mapa.get((x, y)) == "lava":
                    return None

        dist_jugador = _dist(pos_actual, e0)
        aguas = [p for p, m in self.mapa.items() if m == "water"]
        dist_agua = min((_dist(e0, a) for a in aguas), default=12)
        agua_pared_e2 = any(self.mapa.get((e2[0] + ldx, e2[1] + ldy)) == "water" for ldx, ldy in ((-dy, dx), (dy, -dx)))
        agua_pared_e3 = any(
            self.mapa.get((e3[0] + ldx, e3[1] + ldy)) == "water"
            for ldx, ldy in ((-dy, dx), (dy, -dx), (dx, dy))
        )
        rocas_a_picar = sum(1 for ek in (e1, e2, e3) if self.mapa.get(ek) in ROCA_EXCAVABLE)

        bono_agua_pared = 16.0 if agua_pared_e2 else (12.0 if agua_pared_e3 else 0.0)
        puntuacion = 100.0 - 3.0 * dist_jugador - 2.0 * dist_agua + bono_agua_pared
        if es_recordada:
            puntuacion += 25.0
        # Si aún no tiene piedra en el inventario, necesita que la mina dé al menos 1 piedra al cavar
        puntuacion += 2.0 * rocas_a_picar
        return puntuacion

    def _buscar_mejor_mina(self, ctx: Contexto, pos: Pos, inv: Dict[str, float]) -> Optional[Tuple[Pos, Pos, float]]:
        hogar_id = ctx.memoria.hogar() if ctx.perfil.hogar else None
        hogar_pos: Optional[Pos] = None
        if hogar_id and hogar_id.startswith("celda_"):
            partes = hogar_id.split("_")
            if len(partes) == 3:
                hogar_pos = (int(partes[1]), int(partes[2]))

        mejor: Optional[Tuple[Pos, Pos, float]] = None
        tiene_piedra = inv.get("stone", 0) >= 1
        for e0, m0 in list(self.mapa.items()):
            if m0 not in TRANSITABLES_JUGADOR and e0 != pos:
                continue
            for d in MOVIMIENTOS:
                e1 = (e0[0] + d[0], e0[1] + d[1])
                e2 = (e0[0] + 2 * d[0], e0[1] + 2 * d[1])
                e3 = (e0[0] + 3 * d[0], e0[1] + 3 * d[1])
                rocas = sum(1 for ek in (e1, e2, e3) if self.mapa.get(ek) in ROCA_EXCAVABLE)
                if not tiene_piedra and rocas < 1:
                    continue
                s = self._evaluar_candidato(e0, d, pos, hogar_pos)
                if s is not None and (mejor is None or s > mejor[2]):
                    mejor = (e0, d, s)
        return mejor

    def _en_galeria(self, pos: Pos, mina: Optional[Tuple[Pos, Pos]]) -> bool:
        if mina is None:
            return False
        e0, (dx, dy) = mina
        return pos in ((e0[0] + dx, e0[1] + dy), (e0[0] + 2 * dx, e0[1] + 2 * dy), (e0[0] + 3 * dx, e0[1] + 3 * dy))

    def _sellado(self, mina: Optional[Tuple[Pos, Pos]]) -> bool:
        if mina is None:
            return False
        e0, (dx, dy) = mina
        e1 = (e0[0] + dx, e0[1] + dy)
        return self.mapa.get(e1) == "stone"

    def _coste_restante_pasos(self, pos: Pos, inv: Dict[str, float], mina: Optional[Tuple[Pos, Pos]]) -> int:
        """Estimación de pasos de Crafter necesarios para quedar encerrado desde el estado actual
        (contando 2 pasos por interacción de giro + acción)."""
        madera_falta = self._madera_faltante(inv)
        pasos_herramientas = madera_falta * 4 + (4 if self._falta_herramienta(inv) else 0)
        if mina is None:
            return pasos_herramientas + 28   # margen de búsqueda + excavación (3×2 + 3 movs) + cierre (3)
        e0, (dx, dy) = mina
        e1 = (e0[0] + dx, e0[1] + dy)
        e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
        e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
        if pos == e2 and self._sellado(mina):
            return 0
        dist_acceso = 0 if pos in (e0, e1, e2, e3) else _dist(pos, e0)
        rocas = sum(1 for ek in (e1, e2, e3) if self.mapa.get(ek) in ROCA_EXCAVABLE)
        # Cada roca cuesta hasta 2 pasos (girar + picar) + 1 paso de avanzar; retroceder y tapar cuesta 3 pasos
        return pasos_herramientas + dist_acceso + rocas * 3 + 4

    def _pasos_luz_restantes(self, luz: float) -> float:
        """Pasos de Crafter estimados que quedan antes de que la luz caiga de 0,5 según la pendiente solar."""
        if luz < 0.5:
            return 0.0
        p_ocaso = 1.0 - math.acos(0.5 ** (1.0 / 3.0)) / math.pi
        c = max(0.0, min(1.0, 1.0 - luz)) ** (1.0 / 3.0)
        dist_mediodia = 0.5 - math.acos(c) / math.pi
        p_est = (0.5 + dist_mediodia) if self.bajando else (0.5 - dist_mediodia)
        return max(0.0, (p_ocaso - p_est) * 300.0)

    def _guardar_estado(self, estado: Dict[str, Any]) -> Dict[str, Any]:
        self._estado_mem = dict(estado)
        return estado

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return _posicion(ctx) is not None

    def paso(self, ctx: Contexto, estrategia: Pieza) -> Dict[str, Any]:
        self._actualizar_memoria(ctx)
        pos = _posicion(ctx)
        inv = _inventario(ctx)
        luz = _luz(ctx)
        subiendo = not self.bajando

        prev = estrategia.carga.get("paso")
        if not isinstance(prev, dict) and self._estado_mem:
            prev = self._estado_mem
        estado: Dict[str, Any] = dict(prev) if isinstance(prev, dict) else {
            "fase": "madera",
            "mina": None,
            "mejor_dist": 999,
            "sin_avance": 0,
            "saliendo": False,
        }
        if pos is None:
            return self._guardar_estado(estado)

        # Recuperar o validar la mina guardada en el estado (coherencia contra el vaivén)
        mina_actual: Optional[Tuple[Pos, Pos]] = estado.get("mina")
        hogar_id = ctx.memoria.hogar() if ctx.perfil.hogar else None
        hogar_pos: Optional[Pos] = None
        if hogar_id and hogar_id.startswith("celda_"):
            partes = hogar_id.split("_")
            if len(partes) == 3:
                hogar_pos = (int(partes[1]), int(partes[2]))

        previa_acc = ctx.onda.ei("Accion").get("Accion")
        ejecuto_refugio = previa_acc is not None and str(previa_acc.carga.get("motivo", "")).startswith("refugio:")

        if mina_actual is not None:
            e0, d = mina_actual
            e2_m = (e0[0] + 2 * d[0], e0[1] + 2 * d[1])
            e3_m = (e0[0] + 3 * d[0], e0[1] + 3 * d[1])
            dentro_sellado = pos in (e2_m, e3_m) and self._sellado(mina_actual)
            if not dentro_sellado and not estado.get("saliendo"):
                val = self._evaluar_candidato(e0, d, pos, hogar_pos)
                dist_ahora = 0 if self._en_galeria(pos, mina_actual) else _dist(pos, e0)
                if val is None:
                    mina_actual = None
                elif dist_ahora == 0:
                    estado["mejor_dist"] = 0
                    estado["sin_avance"] = 0
                else:
                    # Si mientras el individuo se desplazaba descubrió una mina claramente mejor/más cercana, adoptarla
                    mejor_alt = self._buscar_mejor_mina(ctx, pos, inv)
                    if mejor_alt is not None and mejor_alt[2] > val + 10.0:
                        mina_actual = (mejor_alt[0], mejor_alt[1])
                        estado["mejor_dist"] = _dist(pos, mejor_alt[0])
                        estado["sin_avance"] = 0
                    elif not ejecuto_refugio:
                        estado["mejor_dist"] = dist_ahora
                    elif estado.get("fase") in ("elegir_mina", "cavar"):
                        if dist_ahora < int(estado.get("mejor_dist", 999)):
                            estado["mejor_dist"] = dist_ahora
                            estado["sin_avance"] = 0
                        else:
                            estado["sin_avance"] = int(estado.get("sin_avance", 0)) + 1
                            if int(estado["sin_avance"]) >= self.PACIENCIA_AVANCE:
                                mina_actual = None

        if mina_actual is None:
            candidata = self._buscar_mejor_mina(ctx, pos, inv)
            if candidata is not None:
                mina_actual = (candidata[0], candidata[1])
                estado["mejor_dist"] = _dist(pos, candidata[0])
                estado["sin_avance"] = 0

        estado["mina"] = mina_actual
        pasos_luz = self._pasos_luz_restantes(luz)
        coste = self._coste_restante_pasos(pos, inv, mina_actual)
        es_noche = luz < 0.5
        margen_cierre = max(12.0, coste * 1.55)

        # ¿Hay agua o comida alcanzable para llenar antes de que el margen de cierre obligue a entrar?
        hay_agua_viable = False
        hay_comida_viable = False
        e0_ref = mina_actual[0] if mina_actual is not None else pos
        rocas_pend_ref = (
            sum(1 for k in (1, 2, 3) if self.mapa.get((e0_ref[0] + k * mina_actual[1][0], e0_ref[1] + k * mina_actual[1][1])) in ROCA_EXCAVABLE)
            if mina_actual is not None else 3
        )
        tiene_agua_dentro = self._agua_accesible_dentro(mina_actual) is not None
        if not tiene_agua_dentro and inv.get("drink", 0) < 9:
            aguas_cerca = [
                p for p, m in self.mapa.items()
                if m == "water" and (_dist(pos, p) + _dist(p, e0_ref) + rocas_pend_ref * 3 + 6) * 1.35 < pasos_luz
            ]
            hay_agua_viable = bool(aguas_cerca)
        comidas_visibles = [
            p for p in ctx.onda.ev("Exterocepcion").values()
            if p.clase in ("vaca", "planta") and p.rasgo("nutritivo") > 0.05 and "pos" in p.carga.get("datos", {})
        ]
        if inv.get("food", 0) < 9 and comidas_visibles:
            comidas_cerca = [
                p for p in comidas_visibles
                if (_dist(pos, tuple(p.carga["datos"]["pos"])) + _dist(tuple(p.carga["datos"]["pos"]), e0_ref) + rocas_pend_ref * 3 + 6) * 1.35 < pasos_luz
            ]
            hay_comida_viable = bool(comidas_cerca)
        falta_llenar_antes_de_cerrar = hay_agua_viable or hay_comida_viable
        ocaso_proximo = es_noche or (self.bajando and pasos_luz <= margen_cierre) or (
            self.bajando and pasos_luz <= max(28.0, coste * 1.8) and not falta_llenar_antes_de_cerrar
        )

        # 1. ¿Está ya dentro de la galería (e1, e2 o e3)?
        if mina_actual is not None:
            e0, (dx, dy) = mina_actual
            e1 = (e0[0] + dx, e0[1] + dy)
            e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
            e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
            if pos not in (e1, e2, e3):
                estado["saliendo"] = False
            if estado.get("saliendo") and pos in (e1, e2, e3):
                # Mientras el sello siga puesto, la salida se revisa con lo percibido (p. ej. un zombi en la entrada)
                if self._sellado(mina_actual) and estado.get("manana") and not self._conviene_salir(ctx, inv, luz, mina_actual):
                    estado["saliendo"] = False
                    self.paso_oscuro = True
                    estado["fase"] = "dormir"
                    return self._guardar_estado(estado)
                estado["fase"] = "amanecer"
                return self._guardar_estado(estado)
            if pos in (e2, e3) and self._sellado(mina_actual):
                self.mina_recordada = mina_actual
                if ctx.con_experiencia and ctx.perfil.hogar:
                    ctx.memoria.recordar_lugar(f"celda_{e2[0]}_{e2[1]}", 1.0)
                debe_salir = (self.paso_oscuro and subiendo and self._conviene_salir(ctx, inv, luz, mina_actual)) or (
                    not self.paso_oscuro and not ocaso_proximo and subiendo and luz >= 0.65)
                if debe_salir:
                    estado["manana"] = self.paso_oscuro
                    self.paso_oscuro = False
                    estado["saliendo"] = True
                    estado["fase"] = "amanecer"
                else:
                    estado["fase"] = "dormir"
                return self._guardar_estado(estado)
            # Solo cerrarse cuando ya esté lleno o cuando el margen de cierre lo exija
            if ocaso_proximo and inv.get("stone", 0) >= 1 and not estado.get("saliendo"):
                if pos == e2 and self.mina_recordada == mina_actual and not self._sellado(mina_actual):
                    estado["fase"] = "cerrarse"
                    return self._guardar_estado(estado)
                if pos == e3:
                    estado["fase"] = "cerrarse"
                    return self._guardar_estado(estado)
                if pos == e2 and self.mapa.get(e3) == "path" and not self._sellado(mina_actual):
                    estado["fase"] = "cerrarse"
                    return self._guardar_estado(estado)

        # 1b. Mañana tras salir del refugio: comer y beber es la prioridad hasta que la luz vuelva a bajar
        if estado.get("manana"):
            if self.bajando:
                estado["manana"] = False
            elif not self._en_galeria(pos, mina_actual) and (inv.get("food", 0) < 9 or inv.get("drink", 0) < 9):
                estado["fase"] = "abastecer"
                return self._guardar_estado(estado)

        # 2. Preparación de madera y herramientas
        if self._falta_herramienta(inv):
            if self._madera_faltante(inv) > 0:
                estado["fase"] = "madera"
            else:
                estado["fase"] = "herramientas"
            return self._guardar_estado(estado)

        # 3. Beber y comer hasta llenar (9/9) justo antes de cerrar, o rescate de sed crítica con el mapa recordado
        sed_critica_mapa = inv.get("drink", 0) <= 3 and any(m == "water" for m in self.mapa.values())
        if (falta_llenar_antes_de_cerrar and pasos_luz > margen_cierre) or (sed_critica_mapa and not ocaso_proximo):
            estado["fase"] = "provisiones"
            return self._guardar_estado(estado)

        # 4. Elegir mina o cavar
        if mina_actual is None:
            estado["fase"] = "elegir_mina"
            return self._guardar_estado(estado)

        e0, (dx, dy) = mina_actual
        e1 = (e0[0] + dx, e0[1] + dy)
        e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
        e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
        rocas_pendientes = sum(1 for ek in (e1, e2, e3) if self.mapa.get(ek) in ROCA_EXCAVABLE)
        hora_de_entrar = es_noche or (self.bajando and pasos_luz <= max(28.0, coste * 1.8))
        if rocas_pendientes == 0 and not ocaso_proximo and falta_llenar_antes_de_cerrar:
            estado["fase"] = "provisiones"
            return self._guardar_estado(estado)
        if pos in (e0, e1, e2, e3) and (rocas_pendientes > 0 or hora_de_entrar):
            estado["fase"] = "cavar"
        else:
            estado["fase"] = "elegir_mina"
        return self._guardar_estado(estado)

    @staticmethod
    def _presion_interna(inv: Dict[str, float], agua_dentro: bool) -> float:
        """Presión continua (0-1) del hambre o la sed: déficit cuadrático de la reserva más baja. Con una
        pared de agua dentro del refugio la sed se calma sin salir y no empuja a abrir."""
        deficit_comida = 1.0 - inv.get("food", 9.0) / 9.0
        deficit_agua = 0.0 if agua_dentro else 1.0 - inv.get("drink", 9.0) / 9.0
        return acotar(max(deficit_comida, deficit_agua)) ** 2

    def _riesgo_exterior(self, ctx: Contexto, luz: float, pos: Pos) -> float:
        """Riesgo continuo de salir: crece cuanto más lejos está la luz del pleno día (en Crafter, con luz
        por encima de LUZ_PLENO_DIA el máximo de zombis por zona es 0 y desaparecen) y por cada hostil
        percibido cerca."""
        hostiles = sum(
            1 for p in ctx.onda.ev("Exterocepcion").values()
            if p.clase in ("zombi", "esqueleto") and "pos" in p.carga.get("datos", {})
            and _dist(pos, tuple(p.carga["datos"]["pos"])) <= 4
        )
        return max(0.0, (self.LUZ_PLENO_DIA - luz) / 0.5) + 0.3 * hostiles

    def _conviene_salir(self, ctx: Contexto, inv: Dict[str, float], luz: float, mina: Optional[Tuple[Pos, Pos]]) -> bool:
        """Al amanecer, salir si la presión del hambre o la sed, modulada por la salud (capacidad de
        afrontar lo que quede fuera), iguala o supera el riesgo exterior. Con reservas o agua dentro la
        presión es baja y espera a pleno día; con poca salud la capacidad es baja y se queda."""
        pos = _posicion(ctx)
        if pos is None:
            return False
        presion = self._presion_interna(inv, self._agua_accesible_dentro(mina) is not None)
        capacidad = _salud(ctx) / 9.0
        return presion * capacidad >= self._riesgo_exterior(ctx, luz, pos)

    def _anticipa_refugio(self, luz: float, pos: Pos, inv: Dict[str, float], mina: Optional[Tuple[Pos, Pos]]) -> bool:
        """Indica si la luz restante frente al coste de llegar, abastecerse, cavar y sellar exige activar el repliegue."""
        if luz < 0.5:
            return True
        if not self.bajando:
            return False
        coste = self._coste_restante_pasos(pos, inv, mina)
        falta_prov = max(0, 9 - int(inv.get("drink", 9))) + max(0, 9 - int(inv.get("food", 9)))
        pasos_prov = min(14.0, falta_prov * 2.5) if mina is not None else 0.0
        pasos_luz = self._pasos_luz_restantes(luz)
        return pasos_luz <= max(32.0, coste * 1.9 + pasos_prov)

    def _motivacion(self, ctx: Contexto, estado: Dict[str, Any], pos: Pos, inv: Dict[str, float]) -> Tuple[float, float]:
        """Motivación continua (arousal, confianza) en función de la luz restante y el coste hasta sellar."""
        if self.dominante:
            return 0.98, 0.98
        if inv.get("drink", 0) <= 3 and any(m == "water" for m in self.mapa.values()):
            return 0.92, 0.92
        luz = _luz(ctx)
        mina: Optional[Tuple[Pos, Pos]] = estado.get("mina")
        if not self._anticipa_refugio(luz, pos, inv, mina):
            # Con mucho día por delante: si ya tiene herramientas y no sufre hambre/sed pero aún no ha visto mina,
            # explorar con rumbo (0,72 supera el 0,60+0,10 de continuidad de alimentarse ocioso, y cede en cuanto halla mina)
            if mina is None and not self._falta_herramienta(inv) and inv.get("food", 0) >= 6 and inv.get("drink", 0) >= 6:
                return 0.50, 0.72
            return 0.28, 0.52
        coste = self._coste_restante_pasos(pos, inv, mina)
        pasos_luz = max(1.0, self._pasos_luz_restantes(luz))
        ratio = acotar(coste / pasos_luz)
        oscuridad = acotar(1.0 - luz)
        empuje = max(oscuridad, ratio)
        urgencia = acotar(0.72 + 0.24 * empuje)
        confianza = acotar(0.86 + 0.12 * empuje)
        return urgencia, confianza

    def _paso_hacia(self, ctx: Contexto, origen: Pos, destino: Pos) -> Optional[Pieza]:
        """Elige la casilla vecina transitable (lugar en Exterocepcion) que acerca a ``destino`` por BFS en ``self.mapa``."""
        lugares = {
            tuple(p.carga["datos"]["pos"]): p
            for p in ctx.onda.ev("Exterocepcion").values()
            if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.6 and "pos" in p.carga.get("datos", {})
        }
        if not lugares:
            return None
        if destino in lugares:
            return lugares[destino]

        # BFS sobre las casillas conocidas transitables para sortear agua y roca
        cola: deque[Tuple[Pos, Optional[Pos], int]] = deque([(origen, None, 0)])
        visitados: Set[Pos] = {origen}
        mejor_salto: Optional[Pos] = None
        mejor_dist = _dist(origen, destino)
        while cola:
            actual, primer, prof = cola.popleft()
            if prof >= 30:
                continue
            for dx, dy in MOVIMIENTOS:
                sig = (actual[0] + dx, actual[1] + dy)
                if sig in visitados:
                    continue
                if prof == 0 and sig not in lugares:
                    continue
                mat = self.mapa.get(sig)
                if sig != destino and mat not in TRANSITABLES_JUGADOR and mat is not None:
                    continue
                visitados.add(sig)
                salto = primer if primer is not None else sig
                if sig == destino:
                    return lugares.get(salto)
                d = _dist(sig, destino)
                if d < mejor_dist:
                    mejor_dist = d
                    mejor_salto = salto
                cola.append((sig, salto, prof + 1))

        if mejor_salto is not None and mejor_salto in lugares:
            return lugares[mejor_salto]
        # Si está encajonado por obstáculo y ningún paso reduce la distancia Manhattan, seguir el rumbo exploratorio
        return None

    def _explorar_con_rumbo(self, ctx: Contexto, pos: Pos, ar: float, conf: float, motivo: str) -> Optional[Propuesta]:
        """Mantiene un rumbo sostenido al buscar árbol o mina y bordea obstáculos hacia casillas no visitadas."""
        lugares = {
            tuple(p.carga["datos"]["pos"]): p
            for p in ctx.onda.ev("Exterocepcion").values()
            if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5 and "pos" in p.carga.get("datos", {})
        }
        if not lugares:
            return None
        adelante = (pos[0] + self.rumbo[0], pos[1] + self.rumbo[1])
        if adelante in lugares and self.pasos_rumbo < self.RUMBO_PASOS and adelante not in self.visitadas:
            self.pasos_rumbo += 1
            elegido = lugares[adelante]
            return Propuesta(Verbo.MOVER, elegido.id, ar, conf, motivo, clase=elegido.clase)

        # Si el rumbo está bloqueado o pisa casilla ya visitada, buscar por BFS la casilla no visitada más cercana
        cola: deque[Tuple[Pos, Optional[Pos], int]] = deque([(pos, None, 0)])
        vistos: Set[Pos] = {pos}
        while cola:
            actual, primer, prof = cola.popleft()
            if prof >= 24:
                continue
            for dx, dy in MOVIMIENTOS:
                sig = (actual[0] + dx, actual[1] + dy)
                if sig in vistos:
                    continue
                if prof == 0 and sig not in lugares:
                    continue
                mat = self.mapa.get(sig)
                if mat not in TRANSITABLES_JUGADOR:
                    continue
                vistos.add(sig)
                salto = primer if primer is not None else sig
                if sig not in self.visitadas:
                    if salto in lugares:
                        self.rumbo = (salto[0] - pos[0], salto[1] - pos[1])
                        self.pasos_rumbo = 1
                        return Propuesta(Verbo.MOVER, lugares[salto].id, ar, conf, motivo, clase=lugares[salto].clase)
                cola.append((sig, salto, prof + 1))

        candidatos = sorted(
            lugares.items(),
            key=lambda kv: (
                kv[0] in self.visitadas,
                kv[0] == (pos[0] - self.rumbo[0], pos[1] - self.rumbo[1]),
                -kv[1].rasgo("novedad"),
            ),
        )
        destino_pos, elegido = candidatos[0]
        self.rumbo = (destino_pos[0] - pos[0], destino_pos[1] - pos[1])
        self.pasos_rumbo = 1
        return Propuesta(Verbo.MOVER, elegido.id, ar, conf, motivo, clase=elegido.clase)

    def _abastecer(self, ctx: Contexto, pos: Pos, inv: Dict[str, float], ar: float, conf: float) -> Optional[Propuesta]:
        """Mañana fuera del refugio: ir a beber o comer (agua del mapa recordado, comida percibida o vacas
        vistas hace poco), eligiendo el objetivo por cercanía y por el déficit de cada reserva, y apartarse
        de los hostiles cercanos si no puede abatirlos."""
        exter = [p for p in ctx.onda.ev("Exterocepcion").values() if "pos" in p.carga.get("datos", {})]
        hostiles = [tuple(p.carga["datos"]["pos"]) for p in exter if p.clase in ("zombi", "esqueleto")]
        deficit_agua = 9.0 - inv.get("drink", 9.0)
        deficit_comida = 9.0 - inv.get("food", 9.0)
        objetivos: List[Tuple[float, Pos, str, str]] = []   # (coste, posición, id, clase)
        if deficit_agua > 0:
            for a, m in self.mapa.items():
                if m == "water":
                    objetivos.append((_dist(pos, a) - 3.0 * deficit_agua, a, f"agua_{a[0]}_{a[1]}", "agua"))
        if deficit_comida > 0:
            vistas: Set[Pos] = set()
            for p in exter:
                if p.clase in ("vaca", "planta") and p.rasgo("nutritivo") > 0.05:
                    cp = tuple(p.carga["datos"]["pos"])
                    vistas.add(cp)
                    objetivos.append((_dist(pos, cp) - 3.0 * deficit_comida, cp, p.id, p.clase))
            for v in self.vacas:
                if v not in vistas:
                    objetivos.append((_dist(pos, v) + 2.0 - 3.0 * deficit_comida, v, "", "vaca"))
        objetivo = min(objetivos, key=lambda o: o[0]) if objetivos else None

        armado = _tiene_espada(ctx) and _salud(ctx) >= 4
        if hostiles and not armado and min(_dist(pos, h) for h in hostiles) <= 2:
            lugares = [p for p in exter if p.rasgo("lugar") >= 0.5]
            if lugares:
                def _valor(lugar: Pieza) -> Tuple[int, int]:
                    lp = tuple(lugar.carga["datos"]["pos"])
                    return (min(_dist(lp, h) for h in hostiles), -_dist(lp, objetivo[1]) if objetivo else 0)
                mejor = max(lugares, key=_valor)
                return Propuesta(Verbo.MOVER, mejor.id, ar, conf, "refugio: apartarse de hostil al salir", clase=mejor.clase)

        if objetivo is not None:
            _, opos, oid, oclase = objetivo
            if _dist(pos, opos) == 1 and oid:
                return Propuesta(Verbo.COMER, oid, ar, conf, f"refugio: {'beber' if oclase == 'agua' else 'comer'} al salir", clase=oclase)
            paso_p = self._paso_hacia(ctx, pos, opos)
            if paso_p is not None:
                return Propuesta(Verbo.MOVER, paso_p.id, ar, conf, f"refugio: ir a por {oclase} al salir", clase=paso_p.clase)
        return self._explorar_con_rumbo(ctx, pos, ar, conf, "refugio: buscar agua o comida al salir")

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        pos = _posicion(ctx)
        if pos is None:
            return None
        inv = _inventario(ctx)
        luz = _luz(ctx)
        cara = _orientacion(ctx) or (0, 1)
        estado = estrategia.carga.get("paso")
        if not isinstance(estado, dict):
            estado = self.paso(ctx, estrategia)
        fase = estado.get("fase", "madera")
        mina_est: Optional[Tuple[Pos, Pos]] = estado.get("mina")
        anticipa = self._anticipa_refugio(luz, pos, inv, mina_est)
        sed_critica = inv.get("drink", 0) <= 3 and any(m == "water" for m in self.mapa.values())

        # Con mucho día por delante, si ya tiene herramientas, mina localizada y sin sed crítica, dejar vía libre a alimentarse y plan_tecnologico
        if not self.dominante and fase not in ("dormir", "amanecer", "cerrarse", "abastecer") and not anticipa and not sed_critica:
            if not self._falta_herramienta(inv) and mina_est is not None and not self._en_galeria(pos, mina_est):
                return None

        ar, conf = self._motivacion(ctx, estado, pos, inv)
        if fase == "abastecer":
            empuje = self._presion_interna(inv, False)
            ar, conf = max(ar, acotar(0.84 + 0.12 * empuje)), max(conf, acotar(0.86 + 0.12 * empuje))

        # Defensa inmediata si un hostil bloquea al jugador en plena maniobra y tiene espada;
        # si un esqueleto dispara a distancia 2-3 y tiene espada, cerrar distancia para abatirlo
        if fase != "dormir" and (self.dominante or anticipa or fase in ("amanecer", "abastecer")) and _tiene_espada(ctx) and _salud(ctx) >= 4:
            hostil = next((p for p in ctx.onda.ev("Exterocepcion").values()
                           if p.clase in ("zombi", "esqueleto") and p.rasgo("proximidad") >= 0.9), None)
            if hostil is not None:
                return Propuesta(Verbo.ATACAR, hostil.id, max(ar, 0.95), max(conf, 0.95),
                                 f"refugio: despejar {hostil.clase}", clase=hostil.clase)
            esq = next((p for p in ctx.onda.ev("Exterocepcion").values()
                        if p.clase == "esqueleto" and 0.4 <= p.rasgo("proximidad") < 0.9 and "pos" in p.carga.get("datos", {})), None)
            if esq is not None and _salud(ctx) >= 5 and fase not in ("abastecer", "amanecer"):
                paso_esq = self._paso_hacia(ctx, pos, (int(esq.carga["datos"]["pos"][0]), int(esq.carga["datos"]["pos"][1])))
                if paso_esq is not None:
                    return Propuesta(Verbo.MOVER, paso_esq.id, max(ar, 0.92), max(conf, 0.92),
                                     "refugio: cerrar distancia a esqueleto", clase=paso_esq.clase)

        if fase == "abastecer":
            return self._abastecer(ctx, pos, inv, ar, conf)

        if fase == "madera":
            arboles = [p for p in list( self.mapa.keys()) if self.mapa.get(p) == "tree"]
            if arboles:
                objetivo_pos = min(arboles, key=lambda a: _dist(pos, a))
                if _dist(pos, objetivo_pos) == 1:
                    return Propuesta(Verbo.COGER, f"arbol_{objetivo_pos[0]}_{objetivo_pos[1]}", ar, conf,
                                     "refugio: talar madera", clase="arbol")
                paso_p = self._paso_hacia(ctx, pos, objetivo_pos)
                if paso_p is not None:
                    return Propuesta(Verbo.MOVER, paso_p.id, ar, conf, "refugio: ir a por madera", clase=paso_p.clase)
            return self._explorar_con_rumbo(ctx, pos, ar, conf, "refugio: buscar árboles")

        if fase == "herramientas":
            tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))
            tiene_espada = any(inv.get(k, 0) >= 1 for k in ESPADAS)
            if self._mesa_cerca(pos):
                if not tiene_pico and inv.get("wood", 0) >= 1:
                    return Propuesta(Verbo.USAR, "make_wood_pickaxe", ar, conf, "refugio: fabricar pico",
                                     clase="make_wood_pickaxe", datos={"receta": "make_wood_pickaxe"})
                if not tiene_espada and inv.get("wood", 0) >= 1:
                    return Propuesta(Verbo.USAR, "make_wood_sword", ar, conf, "refugio: fabricar espada",
                                     clase="make_wood_sword", datos={"receta": "make_wood_sword"})
            mesa_pos = self._mesa_conocida()
            if mesa_pos is not None and _dist(pos, mesa_pos) <= 6:
                paso_p = self._paso_hacia(ctx, pos, mesa_pos)
                if paso_p is not None:
                    return Propuesta(Verbo.MOVER, paso_p.id, ar, conf, "refugio: acercarse a la mesa", clase=paso_p.clase)
            if inv.get("wood", 0) >= 2:
                frente = (pos[0] + cara[0], pos[1] + cara[1])
                terreno = _terreno(ctx)
                if terreno.get(frente) in ("grass", "sand", "path"):
                    return Propuesta(Verbo.USAR, "place_table", ar, conf, "refugio: colocar mesa",
                                     clase="place_table", datos={"receta": "place_table"})
                for dx, dy in MOVIMIENTOS:
                    c = (pos[0] + dx, pos[1] + dy)
                    if terreno.get(c) in ("grass", "sand", "path"):
                        return Propuesta(Verbo.MOVER, f"celda_{c[0]}_{c[1]}", ar, conf,
                                         "refugio: orientarse para colocar mesa", clase="suelo")
            return self._explorar_con_rumbo(ctx, pos, ar, conf, "refugio: buscar sitio para mesa")

        if fase == "provisiones":
            e0_ref = mina_est[0] if mina_est is not None else pos
            rocas_ref = (
                sum(
                    1 for k in (1, 2, 3)
                    if self.mapa.get((e0_ref[0] + k * mina_est[1][0], e0_ref[1] + k * mina_est[1][1])) in ROCA_EXCAVABLE
                )
                if mina_est is not None else 3
            )
            pasos_luz_ahora = self._pasos_luz_restantes(luz)
            if inv.get("drink", 0) < 9:
                aguas = [
                    p for p, m in self.mapa.items()
                    if m == "water"
                    and (not anticipa or (_dist(pos, p) + _dist(p, e0_ref) + rocas_ref * 3 + 6) * 1.35 < pasos_luz_ahora)
                ]
                if aguas:
                    agua_pos = min(aguas, key=lambda a: _dist(pos, a) + _dist(a, e0_ref))
                    if _dist(pos, agua_pos) == 1:
                        return Propuesta(Verbo.COMER, f"agua_{agua_pos[0]}_{agua_pos[1]}", max(ar, 0.90), max(conf, 0.90),
                                         "refugio: beber hasta llenar antes de cerrar", clase="agua")
                    paso_p = self._paso_hacia(ctx, pos, agua_pos)
                    if paso_p is not None:
                        return Propuesta(Verbo.MOVER, paso_p.id, max(ar, 0.88), max(conf, 0.88),
                                         "refugio: ir al agua antes de cerrar", clase=paso_p.clase)
            comidas = [
                p for p in ctx.onda.ev("Exterocepcion").values()
                if p.clase in ("vaca", "planta") and p.rasgo("nutritivo") > 0.05 and "pos" in p.carga.get("datos", {})
                and (
                    not anticipa
                    or (_dist(pos, tuple(p.carga["datos"]["pos"])) + _dist(tuple(p.carga["datos"]["pos"]), e0_ref) + rocas_ref * 3 + 6) * 1.35
                    < pasos_luz_ahora
                )
            ]
            if comidas and inv.get("food", 0) < 9:
                mejor_c = max(comidas, key=lambda p: p.rasgo("proximidad"))
                if mejor_c.rasgo("proximidad") >= 0.9:
                    return Propuesta(Verbo.COMER, mejor_c.id, max(ar, 0.90), max(conf, 0.90),
                                     f"refugio: comer {mejor_c.clase} hasta llenar", clase=mejor_c.clase)
                cpos = tuple(mejor_c.carga["datos"]["pos"])
                paso_p = self._paso_hacia(ctx, pos, (int(cpos[0]), int(cpos[1])))
                if paso_p is not None:
                    return Propuesta(Verbo.MOVER, paso_p.id, max(ar, 0.88), max(conf, 0.88),
                                     f"refugio: acercarse a {mejor_c.clase} antes de cerrar", clase=paso_p.clase)
            if inv.get("drink", 0) < 8 or inv.get("food", 0) < 8:
                return self._explorar_con_rumbo(ctx, pos, ar, conf, "refugio: buscar agua o comida")

        if fase in ("elegir_mina", "provisiones"):
            mina: Optional[Tuple[Pos, Pos]] = estado.get("mina")
            if mina is not None:
                e0, (dx, dy) = mina
                e1 = (e0[0] + dx, e0[1] + dy)
                if pos != e0:
                    paso_p = self._paso_hacia(ctx, pos, e0)
                    if paso_p is not None:
                        return Propuesta(Verbo.MOVER, paso_p.id, ar, conf, "refugio: ir a la mina elegida", clase=paso_p.clase)
                # Ya está en e0: si ya está excavada y aún queda mucho día por delante, no encerrarse todavía
                e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
                e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
                rocas_pend = sum(1 for ek in (e1, e2, e3) if self.mapa.get(ek) in ROCA_EXCAVABLE)
                if rocas_pend == 0 and not anticipa:
                    if self.dominante:
                        return Propuesta(Verbo.ESPERAR, "", ar, conf, "refugio: aguardar ocaso en el acceso")
                    return None
                fase = "cavar"
            else:
                # Si se ve alguna piedra aún no inspeccionada de cerca, ir hacia ella para revelar el resto del macizo
                rocas = [p for p, m in self.mapa.items() if m == "stone" and p not in self.rocas_inspeccionadas]
                if rocas:
                    roca_pos = min(rocas, key=lambda r: _dist(pos, r))
                    paso_p = self._paso_hacia(ctx, pos, roca_pos)
                    if paso_p is not None:
                        return Propuesta(Verbo.MOVER, paso_p.id, ar, conf, "refugio: inspeccionar veta de roca", clase=paso_p.clase)
                    self.rocas_inspeccionadas.add(roca_pos)
                return self._explorar_con_rumbo(ctx, pos, ar, conf, "refugio: explorar en busca de mina")

        if fase == "cavar":
            mina = estado.get("mina")
            if mina is None:
                return self._explorar_con_rumbo(ctx, pos, ar, conf, "refugio: buscar mina")
            e0, (dx, dy) = mina
            e1 = (e0[0] + dx, e0[1] + dy)
            e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
            e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
            secuencia = [e0, e1, e2, e3]
            if pos not in secuencia:
                paso_p = self._paso_hacia(ctx, pos, e0)
                if paso_p is not None:
                    return Propuesta(Verbo.MOVER, paso_p.id, ar, conf, "refugio: ir a la entrada de la mina", clase=paso_p.clase)
                return None
            idx = secuencia.index(pos)
            if idx < 3:
                sig = secuencia[idx + 1]
                msig = self.mapa.get(sig)
                if msig in ROCA_EXCAVABLE:
                    clase_r = MATERIALES.get(msig, "piedra")
                    return Propuesta(Verbo.COGER, f"{clase_r}_{sig[0]}_{sig[1]}", ar, conf,
                                     f"refugio: cavar casilla {idx + 1}/3", clase=clase_r)
                # Casilla ya excavada (path): avanzar hacia el fondo
                return Propuesta(Verbo.MOVER, f"celda_{sig[0]}_{sig[1]}", ar, conf,
                                 f"refugio: avanzar por galería {idx + 1}/3", clase="suelo")
            # Ya está en e3: si aún no tiene piedra (mina reutilizada sin piedra en inventario), picar el fondo e3+d si es roca
            if inv.get("stone", 0) < 1:
                e4 = (e3[0] + dx, e3[1] + dy)
                if self.mapa.get(e4) in ROCA_EXCAVABLE:
                    clase_r = MATERIALES.get(self.mapa[e4], "piedra")
                    return Propuesta(Verbo.COGER, f"{clase_r}_{e4[0]}_{e4[1]}", ar, conf,
                                     "refugio: extraer piedra para sellar", clase=clase_r)
            # Si ya excavó hasta e3 pero aún queda mucho día por delante, no encerrarse todavía
            if not anticipa:
                return Propuesta(Verbo.MOVER, f"celda_{e2[0]}_{e2[1]}", ar, conf,
                                 "refugio: galería lista, salir hasta el ocaso", clase="suelo")
            fase = "cerrarse"

        if fase == "cerrarse":
            mina = estado.get("mina")
            if mina is None:
                return None
            e0, (dx, dy) = mina
            e1 = (e0[0] + dx, e0[1] + dy)
            e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
            e3 = (e0[0] + 3 * dx, e0[1] + 3 * dy)
            if pos == e3:
                # Retroceder 1 casilla hacia e2: deja al jugador en e2 mirando hacia e1 (-dx, -dy)
                return Propuesta(Verbo.MOVER, f"celda_{e2[0]}_{e2[1]}", max(ar, 0.9), max(conf, 0.9),
                                 "refugio: retroceder para mirar a la salida", clase="suelo")
            if pos == e2:
                dir_salida = (-dx, -dy)
                if cara != dir_salida:
                    # Si por cualquier motivo no mira a e1, girar contra un lateral bloqueado o dar un paso a e3
                    return Propuesta(Verbo.MOVER, f"celda_{e3[0]}_{e3[1]}", max(ar, 0.9), max(conf, 0.9),
                                     "refugio: reorientar hacia la salida", clase="suelo")
                return Propuesta(Verbo.USAR, "place_stone", max(ar, 0.95), max(conf, 0.95),
                                 "refugio: tapar la entrada con piedra", clase="place_stone", datos={"receta": "place_stone"})

        if fase == "dormir":
            mina = estado.get("mina")
            # Si una pared de e2 o e3 es agua y tiene sed, beber desde dentro sin abrir el sello
            agua_dentro = self._agua_accesible_dentro(mina)
            if agua_dentro is not None and inv.get("drink", 0) < 9:
                casilla_beber, vec_agua = agua_dentro
                if pos == casilla_beber:
                    return Propuesta(Verbo.COMER, f"agua_{vec_agua[0]}_{vec_agua[1]}", 1.0, 1.0,
                                     "refugio: beber agua desde dentro", clase="agua")
                return Propuesta(Verbo.MOVER, f"celda_{casilla_beber[0]}_{casilla_beber[1]}", 1.0, 1.0,
                                 "refugio: acercarse a pared de agua interior", clase="suelo")
            if mina is not None:
                e0, (dx, dy) = mina
                e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
                if pos != e2:
                    return Propuesta(Verbo.MOVER, f"celda_{e2[0]}_{e2[1]}", 1.0, 1.0,
                                     "refugio: colocarse en e2 tras beber", clase="suelo")
            # Dormir si falta energía (incluso con sed/hambre a 0: en Crafter dormir reduce a la mitad la tasa de degeneración)
            if inv.get("energy", 9) < 9:
                return Propuesta(Verbo.DORMIR, "", 1.0, 1.0, "refugio: dormir a salvo")
            # Mientras esté encerrado dentro del refugio esperando a que amanezca, prioridad máxima para que otra
            # estrategia (p. ej. Alimentarse o Explorar) no mueva al jugador hacia el fondo e3 ni rompa el sello
            return Propuesta(Verbo.ESPERAR, "", 1.0, 1.0, "refugio: esperar al amanecer")

        if fase == "amanecer":
            mina = estado.get("mina")
            if mina is not None:
                e0, (dx, dy) = mina
                e1 = (e0[0] + dx, e0[1] + dy)
                e2 = (e0[0] + 2 * dx, e0[1] + 2 * dy)
                if self.mapa.get(e1) == "stone":
                    if _dist(pos, e1) == 1:
                        return Propuesta(Verbo.COGER, f"piedra_{e1[0]}_{e1[1]}", max(ar, 0.95), max(conf, 0.95),
                                         "refugio: abrir salida al amanecer", clase="piedra")
                    return Propuesta(Verbo.MOVER, f"celda_{e2[0]}_{e2[1]}", max(ar, 0.95), max(conf, 0.95),
                                     "refugio: acercarse al sello para abrir", clase="suelo")
                if pos != e0:
                    paso_p = self._paso_hacia(ctx, pos, e0)
                    if paso_p is not None:
                        return Propuesta(Verbo.MOVER, paso_p.id, max(ar, 0.95), max(conf, 0.95),
                                         "refugio: salir al exterior", clase=paso_p.clase)
        return None


class PlanTecnologico(Plan, ConPropuestas):
    """Estrategia de S3 propia de Crafter para la intención «progresar» (decisión 11): avanza por el
    árbol tecnológico del juego. Si puede fabricar o colocar algo útil, lo propone (USAR); si no, va
    hacia el recurso que le falta o lo recoge si está al lado (COGER). Aprovecha logros baratos al
    alcance y duerme de día si está cansado. Puntúa por debajo de la supervivencia.

    Solo lee la percepción (regla 3 de AGENTS.md): inventario y orientación por propiocepción,
    posición por la ubicación percibida, estructuras y terreno por exterocepción, luz por el ambiente.
    Los logros conseguidos los recuerda él: lo que su plan logró y lo que ha llegado a tener en el
    inventario. Las recetas (``crafter.constants``) son reglas fijas del mundo, no su estado. Lleva su
    propio control de fallos, así que no se agota.

    Con el interruptor de plan (bloque F, F2) es un ``Plan``: la cadena son las recetas pendientes en el
    orden del árbol; un paso se cumple al tenerlo hecho y falla (sorpresa) cuando la receta ha fallado
    tres veces. Rehacer el plan la deja fuera; si vuelve a fallar, la estrategia se agota.
    """

    nombre = "plan_tecnologico"
    impulsos = ("progresar",)
    prioridad = 10
    agotable = False
    OBJETIVOS = ["place_table", "make_wood_pickaxe", "make_wood_sword", "place_stone", "make_stone_pickaxe",
                 "make_stone_sword", "place_furnace", "make_iron_pickaxe", "make_iron_sword"]
    RECURSO = {"wood": "arbol", "stone": "piedra", "coal": "carbon", "iron": "hierro"}
    LOGROS_PLAN = set(OBJETIVOS) | {"collect_diamond", "collect_iron", "collect_coal", "place_plant", "collect_sapling"}

    def __init__(self, constantes: Any):
        super().__init__()
        self.constantes = constantes
        self.fallos: Dict[str, int] = {}
        self.hecho: Set[str] = set()
        self.tenido: Set[str] = set()

    def _recordar(self, ctx: Contexto, inv: Dict[str, float]) -> None:
        """Fallos y logros del plan en el latido anterior, y lo que se ha llegado a tener."""
        self.tenido |= {k for k, v in inv.items() if v >= 1}
        previa = ctx.onda.ei("Accion").get("Accion")
        if previa is None or not str(previa.carga.get("motivo", "")).startswith("plan:"):
            return
        if previa.carga.get("exito") is False:
            obj = previa.carga["objetivo"]
            self.fallos[obj] = self.fallos.get(obj, 0) + 1
        elif previa.carga.get("exito"):
            logro = str(previa.carga["motivo"])[len("plan:"):].strip().split(" ")[0]
            if logro in self.LOGROS_PLAN:
                self.hecho.add(logro)

    def _hechos(self, inv: Dict[str, float]) -> Set[str]:
        hechos = set(self.hecho)
        hechos |= {r for r in self.OBJETIVOS if r.startswith("make_") and inv.get(r[5:], 0) >= 1}
        hechos |= {f"collect_{m}" for m in ("coal", "iron", "diamond", "sapling") if m in self.tenido}
        return hechos

    def _cerca(self, ctx: Contexto, materiales: List[str]) -> bool:
        pos = _posicion(ctx)
        if pos is None:
            return False
        vistas = list(ctx.onda.ev("Exterocepcion").values())
        return all(any(p.clase == MATERIALES.get(m, m) and max(abs(p.carga["datos"]["pos"][0] - pos[0]), abs(p.carga["datos"]["pos"][1] - pos[1])) <= 1
                       for p in vistas if "pos" in p.carga.get("datos", {})) for m in materiales)

    def _falta(self, receta: str) -> Dict[str, int]:
        tipo, nombre = receta.split("_", 1)
        info = self.constantes.place[nombre] if tipo == "place" else self.constantes.make[nombre]
        return info["uses"]

    def _oportunidades(self, ctx: Contexto, inv: Dict[str, float], hecho: Set[str]) -> bool:
        """Logros baratos al alcance: minerales con el pico adecuado, retoño y plantarlo."""
        for logro, clase, herramienta in (("collect_diamond", "diamante", "iron_pickaxe"), ("collect_iron", "hierro", "stone_pickaxe"),
                                          ("collect_coal", "carbon", "wood_pickaxe")):
            if logro in hecho or inv.get(herramienta, 0) < 1:
                continue
            for p in ctx.onda.ev("Exterocepcion").values():
                if p.clase == clase and p.rasgo("proximidad") >= 0.9 and self.fallos.get(p.id, 0) < 3:
                    self.proponer(ctx, Verbo.COGER, p.id, 0.55, 0.8, f"plan: {logro}", clase=clase)
                    return True
        pos, cara, terreno = _posicion(ctx), _orientacion(ctx), _terreno(ctx)
        if "place_plant" not in hecho and inv.get("sapling", 0) >= 1 and self.fallos.get("place_plant", 0) < 3 and pos and cara:
            if terreno.get((pos[0] + cara[0], pos[1] + cara[1])) == "grass":
                self.proponer(ctx, Verbo.USAR, "place_plant", 0.5, 0.8, "plan: place_plant", clase="place_plant", receta="place_plant")
                return True
        hostiles = any(p.clase in HOSTILES and p.clase != "lava" for p in ctx.onda.ev("Exterocepcion").values())
        umbral_energia = 4 if any(n.nombre == "cobijo" for n in ctx.perfil.necesidades) else 6
        if inv.get("energy", 9) <= umbral_energia and _luz(ctx) >= 0.5 and not hostiles:
            # Dormir de día, sin hostiles a la vista, para no llegar agotado a la noche (y lograr wake_up).
            self.proponer(ctx, Verbo.DORMIR, "", 0.6, 0.85, "plan: dormir de día para afrontar la noche", clase="")
            return True
        if "collect_sapling" not in hecho and inv.get("sapling", 0) == 0 and pos:
            for dx, dy in MOVIMIENTOS:
                c = (int(pos[0] + dx), int(pos[1] + dy))
                cid = f"hierba_{c[0]}_{c[1]}"
                if terreno.get(c) == "grass" and self.fallos.get(cid, 0) < 6:
                    self.proponer(ctx, Verbo.COGER, cid, 0.4, 0.7, "plan: collect_sapling", clase="hierba")
                    return True
        return False

    def construir(self, ctx: Contexto, estrategia: Pieza) -> Optional[List[Dict[str, Any]]]:
        hecho = self._hechos(_inventario(ctx))
        return [{"meta": r} for r in self.OBJETIVOS if r not in hecho and self.fallos.get(r, 0) < 3] or None

    def cumplido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        return paso["meta"] in self._hechos(_inventario(ctx))

    def fallido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        return self.fallos.get(paso["meta"], 0) >= 3

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        inv = _inventario(ctx)
        self._recordar(ctx, inv)
        hecho = self._hechos(inv)
        if self._oportunidades(ctx, inv, hecho):
            return
        plan = estado_plan(estrategia) if estrategia is not None and ctx.perfil.mecanismos.plan else None
        orden = [p["meta"] for p in plan["pasos"][int(plan["i"]):]] if plan is not None and not plan["fallido"] else self.OBJETIVOS
        for receta in orden:
            if receta in hecho or self.fallos.get(receta, 0) >= 3:
                continue
            usos = self._falta(receta)
            if all(inv.get(k, 0) >= v for k, v in usos.items()):
                if receta.startswith("make_"):
                    cerca = self.constantes.make[receta[5:]]["nearby"]
                    if not self._cerca(ctx, cerca):
                        # La mesa o el horno necesarios están lejos: usar el mapa cognitivo (hipocampo) para orientarse
                        # hacia ellos en vez de congelarse sin candidatos.
                        if self._ir_hacia_estructura(ctx, cerca[0]):
                            return
                        # Si no hay mesa en el mapa y tiene madera de sobra, colocar una mesa nueva
                        if cerca[0] == "table" and inv.get("wood", 0) >= 2:
                            self.proponer(ctx, Verbo.USAR, "place_table", 0.52, 0.8,
                                          "plan: place_table (nueva estación)", clase="place_table", receta="place_table")
                            return
                        continue
                self.proponer(ctx, Verbo.USAR, receta, 0.55, 0.8, f"plan: {receta}", clase=receta, receta=receta)
                return
            faltan = [k for k, v in usos.items() if inv.get(k, 0) < v]
            self._buscar(ctx, faltan[0])
            return

    def _ir_hacia_estructura(self, ctx: Contexto, estructura: str) -> bool:
        """Orienta el movimiento hacia una estructura del taller (mesa, horno) usando Exterocepcion o el hipocampo del Core."""
        clase_percibida = MATERIALES.get(estructura, estructura)
        pos = _posicion(ctx)
        # 1. ¿Está visible en la escena actual?
        candidatos = [p for p in ctx.onda.ev("Exterocepcion").values() if p.clase == clase_percibida and p.rasgo("proximidad") >= 0.1]
        if candidatos and pos is not None:
            objetivo = max(candidatos, key=lambda p: p.rasgo("proximidad"))
            destino_pos = objetivo.carga["datos"]["pos"]
            lugares = [p for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5]
            mejor = min(lugares, key=lambda lugar: _dist(lugar.carga["datos"]["pos"], destino_pos), default=None)
            if mejor is not None and _dist(mejor.carga["datos"]["pos"], destino_pos) < _dist(pos, destino_pos):
                self.proponer(ctx, Verbo.MOVER, mejor.id, 0.48, 0.75, f"hipocampo: volver a {estructura}", clase=mejor.clase)
                return True
        # 2. Si no está visible, consultar la ruta topológica en la Memoria del individuo
        aqui = ctx.observacion.ubicacion if ctx.observacion else ""
        destino_nodo = ctx.memoria.donde_esta(clase_percibida) if ctx.con_experiencia else None
        if aqui and destino_nodo and destino_nodo != aqui:
            salto = ctx.memoria.ruta(aqui, destino_nodo)
            if salto:
                lugares = [p for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5]
                puerta = next((lugar for lugar in lugares if lugar.id == salto), None)
                if puerta is not None:
                    self.proponer(ctx, Verbo.MOVER, puerta.id, 0.48, 0.75, f"hipocampo: volver a {estructura}", clase=puerta.clase)
                    return True
        return False

    def _buscar(self, ctx: Contexto, recurso: str) -> None:
        clase = self.RECURSO.get(recurso)
        if clase is None:
            return
        candidatos = [p for p in ctx.onda.ev("Exterocepcion").values() if p.clase == clase and self.fallos.get(p.id, 0) < 3]
        if not candidatos:
            return
        objetivo = max(candidatos, key=lambda p: p.rasgo("proximidad"))
        if objetivo.rasgo("proximidad") >= 0.9:
            self.proponer(ctx, Verbo.COGER, objetivo.id, 0.5, 0.75, f"plan: conseguir {recurso}", clase=clase)
            return
        destino_pos = objetivo.carga["datos"]["pos"]
        pos = _posicion(ctx)
        if pos is None:
            return
        lugares = [p for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5]
        mejor = min(lugares, key=lambda lugar: _dist(lugar.carga["datos"]["pos"], destino_pos), default=None)
        if mejor is not None and _dist(mejor.carga["datos"]["pos"], destino_pos) < _dist(pos, destino_pos):
            self.proponer(ctx, Verbo.MOVER, mejor.id, 0.45, 0.7, f"plan: ir a por {recurso}", clase=mejor.clase)
