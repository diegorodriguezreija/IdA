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

import collections
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.core.arquitectura import Componente, Contexto
from ida.core.estrategia import ConPropuestas, Definicion, Plan, Propuesta, estado_plan
from ida.core.memoria import Proposicion
from ida.core.mundo import Efecto, Entidad, Mundo, Necesidad, Observacion, Perfil
from ida.core.pieza import Pieza
from ida.core.vocabulario import Relacion, Verbo

MATERIALES = {"tree": "arbol", "water": "agua", "stone": "piedra", "coal": "carbon", "iron": "hierro",
              "diamond": "diamante", "table": "mesa", "furnace": "horno", "lava": "lava"}
OBJETOS = {"Cow": "vaca", "Zombie": "zombi", "Skeleton": "esqueleto", "Plant": "planta", "Arrow": "flecha"}
HOSTILES = {"zombi": 1.0, "esqueleto": 1.0, "flecha": 1.0, "lava": 1.0}
MOVIMIENTOS = {(-1, 0): "move_left", (1, 0): "move_right", (0, -1): "move_up", (0, 1): "move_down"}
LETRA = {"arbol": "T", "agua": "~", "piedra": "#", "carbon": "c", "hierro": "i", "diamante": "D", "mesa": "M", "horno": "H",
         "lava": "!", "vaca": "v", "zombi": "Z", "esqueleto": "S", "planta": "p", "flecha": "-"}
LOGROS = 22
INVENTARIO = {"wood": "madera", "stone": "piedra", "coal": "carbon", "iron": "hierro", "diamond": "diamante", "sapling": "retoño",
              "wood_pickaxe": "pico_madera", "stone_pickaxe": "pico_piedra", "iron_pickaxe": "pico_hierro",
              "wood_sword": "espada_madera", "stone_sword": "espada_piedra", "iron_sword": "espada_hierro"}

DOTACION_INNATA: List[Tuple[str, Relacion, float]] = [
    ("zombi", Relacion.PELIGROSO, 0.95),
    ("esqueleto", Relacion.PELIGROSO, 0.95),
    ("vaca", Relacion.NUTRITIVO, 0.95),
    ("planta", Relacion.NUTRITIVO, 0.95),
    ("agua", Relacion.NUTRITIVO, 0.95),
    ("arbol", Relacion.UTIL, 0.95),
    ("piedra", Relacion.UTIL, 0.95),
]


def asegurar_dotacion_innata(memoria: Any) -> None:
    """Asegura la dotación innata de Crafter (trust 0,95) en la memoria semántica del individuo."""
    if memoria is None or not getattr(memoria, "activa", False):
        return
    saber = getattr(memoria, "saber", None)
    if saber is None:
        return
    for sujeto, relacion, confianza in DOTACION_INNATA:
        if (sujeto, relacion) not in saber:
            p = Proposicion(sujeto, relacion, confianza=confianza)
            p.confirmaciones = Proposicion.CONFIRMACIONES_MINIMAS - 1
            p.heredada = True
            saber[(sujeto, relacion)] = p

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
                                 Necesidad("preparar_nido", ("nido",), 100.0, "recurso")),
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
        self.madriguera: Optional[Dict[str, Any]] = None
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
        self.madriguera = None
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

    def _en_refugio_cerrado(self) -> bool:
        """Determina si el jugador se encuentra en una celda protegida/sellada (madriguera)."""
        if self.env is None:
            return False
        w = self.env._world
        pos = tuple(self.jugador.pos)
        adyacentes_transitables = 0
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            c = (pos[0] + dx, pos[1] + dy)
            if not (0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1]):
                continue
            mat, obj = w[c]
            if mat in self.constantes.walkable and obj is None:
                adyacentes_transitables += 1
        if adyacentes_transitables == 0:
            return True
        if self.madriguera is not None:
            c1, c2, e = self.madriguera.get("c1"), self.madriguera.get("c2"), self.madriguera.get("e")
            if pos in (c1, c2) and e is not None:
                mat_e, obj_e = w[e]
                if mat_e not in self.constantes.walkable or obj_e is not None:
                    return True
        return False

    def _calcular_nido(self) -> float:
        """Constante vital 'nido' (0-100). Déficit = (100 - nido) / 100."""
        w = self.env._world
        inv = self.jugador.inventory
        luz = float(w.daylight)
        tiene_pico = (inv["wood_pickaxe"] >= 1 or inv["stone_pickaxe"] >= 1 or inv["iron_pickaxe"] >= 1)
        tiene_madera = inv["wood"] >= 2

        if self._en_refugio_cerrado():
            return 100.0
        if luz < 0.3:
            return 0.0
        if luz < 0.6:
            factor_luz = max(0.0, (luz - 0.3) / 0.3)
            return max(0.0, 50.0 * factor_luz)
        if not tiene_pico:
            return 40.0 if not tiene_madera else 50.0
        if inv["stone"] < 1:
            return 70.0
        return 85.0

    def _vitales(self) -> Dict[str, float]:
        inv = self.jugador.inventory
        return {"vitalidad": self.jugador.health / 9 * 100, "alimentacion": min(inv["food"], inv["drink"]) / 9 * 100,
                "energia": inv["energy"] / 9 * 100, "descanso": inv["energy"] / 9 * 100,
                "comida": inv["food"] / 9 * 100, "agua": inv["drink"] / 9 * 100,
                "nido": self._calcular_nido()}

    # --- percepción ----------------------------------------------------------
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

    def _valor_recurso(self, clase: str) -> float:
        """Da valor a la madera y la piedra según lo que falte y lo que ya se lleva."""
        inv = self.jugador.inventory
        tiene_pico = (inv["wood_pickaxe"] >= 1 or inv["stone_pickaxe"] >= 1 or inv["iron_pickaxe"] >= 1)
        if clase == "arbol":
            if inv["wood"] < 2:
                return 0.95
            if not tiene_pico and inv["wood"] < 4:
                return 0.85
            return 0.4
        if clase == "piedra":
            if tiene_pico and inv["stone"] < 1:
                return 0.95
            if tiene_pico and inv["stone"] < 3:
                return 0.75
            return 0.4
        if clase in ("carbon", "hierro", "diamante"):
            return 0.6
        return 0.0

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
                "recurso": self._valor_recurso(clase),
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
                           cuerpo={"orientacion": (int(p.facing[0]), int(p.facing[1]))}, ambiente={"luz": float(w.daylight)})

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

    def componentes_propios(self) -> Dict[str, list]:
        return {"S1.Interpretar": [EvaluacionNido()]}

    def estrategias_propias(self) -> Dict[str, list]:
        return {"S1": [DefensaArmada(), CerrarDistancia(), Anidar()], "S3": [PlanTecnologico(self.constantes)]}

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


def _terreno(ctx: Contexto) -> Dict[Pos, str]:
    """Terreno de las casillas libres a las que se puede ir (lugares percibidos)."""
    return {tuple(p.carga["datos"]["pos"]): p.carga["datos"].get("terreno", "")
            for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and "pos" in p.carga.get("datos", {})}


def _luz(ctx: Contexto) -> float:
    a = ctx.onda.ev("Ambiente").get("ambiente")
    return float(a.carga.get("luz", 1.0)) if a is not None else 1.0


class EvaluacionNido(Componente):
    """Componente propio de Crafter en S1.Interpretar.

    Interpreta el estado del nido y de los recursos necesarios, asegurando la
    dotación innata en la memoria semántica del individuo. Produce una pieza
    propia de tipo 'EvaluacionNido' en la Onda.
    """

    tipo = "EvaluacionNido"
    entradas = ("Exterocepcion", "Propiocepcion", "Ambiente")

    def reactiva(self, ctx: Contexto) -> None:
        asegurar_dotacion_innata(ctx.memoria)
        inv = _inventario(ctx)
        luz = _luz(ctx)
        tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))
        madera = inv.get("wood", 0)
        piedra = inv.get("stone", 0)
        necesita_madera = madera < 2 or (not tiene_pico and madera < 3)
        necesita_pico = not tiene_pico
        urgencia_noche = 1.0 - luz if luz < 0.6 else 0.0

        self.registrar(ctx, self.pieza(ctx, "estado_nido", arousal=max(urgencia_noche, 0.5 if necesita_pico else 0.0),
                                       carga={"tiene_pico": tiene_pico, "madera": madera, "piedra": piedra,
                                              "necesita_madera": necesita_madera, "necesita_pico": necesita_pico,
                                              "luz": luz, "urgencia_noche": round(urgencia_noche, 3)}))


def _trazar_anidar(fase: str, pos: Optional[Pos], motivo: str) -> None:
    print(f"[anidar] paso: {fase}, pos: {pos}, motivo: {motivo}")


def _buscar_madriguera(ctx: Contexto) -> Optional[Dict[str, Any]]:
    """Busca en Exterocepcion un frente de roca válido para excavar la madriguera:
    Casillas: E (fuera, transitable), C1 y C2 (dos casillas seguidas hacia dentro que sean piedra o path).
    Condición: C1 y C2 son piedra (o path) y las casillas que las rodean (salvo E, C1 y C2) son intransitables.
    """
    pos = _posicion(ctx)
    if pos is None:
        return None
    vistas = list(ctx.onda.ev("Exterocepcion").values())
    piedras = {tuple(p.carga["datos"]["pos"]) for p in vistas if p.clase == "piedra" and "pos" in p.carga.get("datos", {})}
    lugares = {tuple(p.carga["datos"]["pos"]): p for p in vistas if p.rasgo("lugar") >= 0.5 and "pos" in p.carga.get("datos", {})}
    transitables = set(lugares.keys())
    candidatas_e = sorted(transitables, key=lambda c: _dist(pos, c))

    dirs = ((0, -1), (0, 1), (-1, 0), (1, 0))
    for e in candidatas_e:
        for d in dirs:
            c1 = (e[0] + d[0], e[1] + d[1])
            c2 = (e[0] + 2 * d[0], e[1] + 2 * d[1])
            c1_es_roca = c1 in piedras or (c1 in transitables and _dist(pos, c1) <= 1)
            c2_es_roca = c2 in piedras or (c2 in transitables and _dist(pos, c2) <= 2)
            if not (c1_es_roca and c2_es_roca):
                continue
            exclusiones = {e, c1, c2}
            vecinos_c1 = {(c1[0] + vd[0], c1[1] + vd[1]) for vd in dirs} - exclusiones
            vecinos_c2 = {(c2[0] + vd[0], c2[1] + vd[1]) for vd in dirs} - exclusiones
            entorno = vecinos_c1 | vecinos_c2
            if any(vc in transitables for vc in entorno):
                continue
            return {"e": e, "c1": c1, "c2": c2, "dir": d}
    return None


def _navegar_hacia(ctx: Contexto, destino: Pos) -> Optional[Propuesta]:
    pos = _posicion(ctx)
    if pos is None or pos == destino:
        return None
    lugares = [p for p in ctx.onda.ev("Exterocepcion").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.7]
    if not lugares:
        return None
    mejor = min(lugares, key=lambda l: (_dist(tuple(l.carga["datos"]["pos"]), destino), -l.rasgo("novedad")), default=None)
    if mejor is not None:
        c_pos = tuple(mejor.carga["datos"]["pos"])
        if _dist(c_pos, destino) < _dist(pos, destino) or _dist(pos, destino) > 1:
            return Propuesta(Verbo.MOVER, mejor.id, 0.78, 0.85, f"anidar: avanzar hacia {destino}", clase=mejor.clase)
    return None


class Anidar(Definicion):
    """Estrategia de S1 propia de Crafter para preparar y ocupar una madriguera en roca.

    Fases guiadas por la percepción:
    1. equipar: reunir madera -> colocar mesa -> fabricar pico de madera (solo lo que falte).
    2. ir_sitio: navegar hacia la entrada E de la madriguera (recordada o frente de roca nuevo).
    3. entrar_tapar: picar C1 si es roca -> avanzar a C1 -> picar C2 si es roca -> avanzar a C2
                    -> retroceder hacia C1 (queda mirando a E) -> colocar piedra en E -> avanzar a C2.
    4. dormir: en C2 sellada, dormir hasta el amanecer.
    5. salir: al amanecer, avanzar a C1 mirando a E -> picar E -> salir a E.

    Respeta estrictamente la regla 3 de AGENTS.md: lee exclusivamente la percepción
    (piezas de la Onda).
    """

    nombre = "anidar"
    impulsos = ("preparar_nido",)
    prioridad = 35

    def __init__(self) -> None:
        super().__init__()
        self.madriguera: Optional[Dict[str, Any]] = None
        self.fase_previa: Optional[str] = None

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return impulso == "preparar_nido" and intensidad > 0.05

    def paso(self, ctx: Contexto, estrategia: Pieza) -> str:
        inv = _inventario(ctx)
        tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))
        luz = _luz(ctx)
        pos = _posicion(ctx)

        if not tiene_pico:
            fase = "equipar"
        else:
            if self.madriguera is None:
                self.madriguera = _buscar_madriguera(ctx)
            if self.madriguera is None:
                fase = "sin_sitio" if luz < 0.6 else "ir_sitio"
            else:
                c1, c2, e = self.madriguera["c1"], self.madriguera["c2"], self.madriguera["e"]
                vistas = list(ctx.onda.ev("Exterocepcion").values())
                piedras = {tuple(p.carga["datos"]["pos"]) for p in vistas if p.clase == "piedra" and "pos" in p.carga.get("datos", {})}
                e_tapado = e in piedras
                if pos == c2 and e_tapado:
                    fase = "dormir" if luz < 0.5 else "salir"
                elif pos == c1 and self.fase_previa in ("dormir", "salir") and luz >= 0.5:
                    fase = "salir"
                elif pos in (e, c1, c2):
                    fase = "entrar_tapar"
                else:
                    fase = "ir_sitio"

        if fase != self.fase_previa:
            _trazar_anidar(fase, pos, f"cambio de {self.fase_previa} a {fase}")
            self.fase_previa = fase
        return fase

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        inv = _inventario(ctx)
        tiene_pico = any(inv.get(k, 0) >= 1 for k in ("wood_pickaxe", "stone_pickaxe", "iron_pickaxe"))
        luz = _luz(ctx)
        pos = _posicion(ctx)
        cara = _orientacion(ctx)
        if pos is None:
            return None

        # 1. Fase equipar
        if not tiene_pico:
            madera = inv.get("wood", 0)
            vistas = list(ctx.onda.ev("Exterocepcion").values())
            mesas = [p for p in vistas if p.clase == "mesa" and "pos" in p.carga.get("datos", {})]
            mesa_cerca = any(_dist(pos, tuple(m.carga["datos"]["pos"])) <= 1 for m in mesas)
            if mesa_cerca and madera >= 1:
                return Propuesta(Verbo.USAR, "make_wood_pickaxe", 0.92, 0.95, "anidar: fabricar pico de madera",
                                 clase="make_wood_pickaxe", datos={"receta": "make_wood_pickaxe"})
            if madera >= 2 and not mesa_cerca and cara is not None:
                enfrente = (pos[0] + cara[0], pos[1] + cara[1])
                lugares = {tuple(p.carga["datos"]["pos"]): p for p in vistas if p.rasgo("lugar") >= 0.5 and "pos" in p.carga.get("datos", {})}
                if enfrente in lugares:
                    return Propuesta(Verbo.USAR, "place_table", 0.88, 0.95, "anidar: colocar mesa para pico",
                                     clase="place_table", datos={"receta": "place_table"})
            # Necesita madera: buscar arbol
            arboles = [p for p in vistas if p.clase == "arbol" and "pos" in p.carga.get("datos", {})]
            if arboles:
                cercano = min(arboles, key=lambda a: _dist(pos, tuple(a.carga["datos"]["pos"])))
                c_pos = tuple(cercano.carga["datos"]["pos"])
                if _dist(pos, c_pos) <= 1:
                    return Propuesta(Verbo.COGER, cercano.id, 0.85, 0.9, "anidar: talar madera", clase="arbol")
                return _navegar_hacia(ctx, c_pos)
            # Explorar para encontrar árboles
            lugares = [p for p in vistas if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.6]
            if lugares:
                mejor = max(lugares, key=lambda l: float(l.rasgo("novedad")))
                return Propuesta(Verbo.MOVER, mejor.id, 0.7, 0.8, "anidar: buscar arboles", clase=mejor.clase)
            return None

        # 2. Fase ir_sitio / localizar madriguera
        if self.madriguera is None:
            self.madriguera = _buscar_madriguera(ctx)
        if self.madriguera is None:
            if luz < 0.6:
                _trazar_anidar("sin_sitio", pos, "anochecer sin frente de roca valido: delegando en huir/defenderse")
                return None
            vistas = list(ctx.onda.ev("Exterocepcion").values())
            piedras = [p for p in vistas if p.clase == "piedra" and "pos" in p.carga.get("datos", {})]
            if piedras:
                cercana = min(piedras, key=lambda p: _dist(pos, tuple(p.carga["datos"]["pos"])))
                return _navegar_hacia(ctx, tuple(cercana.carga["datos"]["pos"]))
            lugares = [p for p in vistas if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.6]
            if lugares:
                mejor = max(lugares, key=lambda l: float(l.rasgo("novedad")))
                return Propuesta(Verbo.MOVER, mejor.id, 0.7, 0.8, "anidar: buscar frente de roca", clase=mejor.clase)
            return None

        e, c1, c2, d = self.madriguera["e"], self.madriguera["c1"], self.madriguera["c2"], self.madriguera["dir"]
        vistas = list(ctx.onda.ev("Exterocepcion").values())
        piedras = {tuple(p.carga["datos"]["pos"]): p for p in vistas if p.clase == "piedra" and "pos" in p.carga.get("datos", {})}
        lugares = {tuple(p.carga["datos"]["pos"]): p for p in vistas if p.rasgo("lugar") >= 0.5 and "pos" in p.carga.get("datos", {})}

        # Si aún no está en la madriguera: navegar a E
        if pos != e and pos != c1 and pos != c2:
            return _navegar_hacia(ctx, e)

        # 3. Fase entrar_tapar
        if pos == e:
            if c1 in piedras:
                return Propuesta(Verbo.COGER, piedras[c1].id, 0.92, 0.95, "anidar: picar roca C1", clase="piedra")
            if c1 in lugares:
                return Propuesta(Verbo.MOVER, lugares[c1].id, 0.9, 0.95, "anidar: entrar a C1", clase="suelo")

        if pos == c1:
            if c2 in piedras:
                return Propuesta(Verbo.COGER, piedras[c2].id, 0.92, 0.95, "anidar: picar roca C2", clase="piedra")
            if c2 in lugares:
                # Comprobar si E ya está tapado
                if e in piedras:
                    return Propuesta(Verbo.MOVER, lugares[c2].id, 0.9, 0.95, "anidar: pasar al fondo C2", clase="suelo")
                # E aún no está tapado
                if cara == (-d[0], -d[1]):
                    if inv.get("stone", 0) >= 1:
                        return Propuesta(Verbo.USAR, "place_stone", 0.95, 0.95, "anidar: tapar entrada E con piedra",
                                         clase="place_stone", datos={"receta": "place_stone"})
                # Si no está mirando a E, ir a C2 para poder volver hacia C1 mirando a E
                return Propuesta(Verbo.MOVER, lugares[c2].id, 0.9, 0.95, "anidar: avanzar a C2", clase="suelo")

        if pos == c2:
            if e not in piedras and c1 in lugares:
                # Volver a C1: queda mirando a E
                return Propuesta(Verbo.MOVER, lugares[c1].id, 0.9, 0.95, "anidar: volver a C1 mirando a E", clase="suelo")
            # E tapado y en C2: dormir si es noche
            if luz < 0.5:
                if inv.get("energy", 9) < 9:
                    return Propuesta(Verbo.DORMIR, "", 0.9, 0.95, "anidar: dormir a salvo", clase="")
                return Propuesta(Verbo.ESPERAR, "", 0.75, 0.9, "anidar: esperar amanecer a salvo", clase="")
            # Amaneció (luz >= 0.5): salir
            if c1 in lugares:
                return Propuesta(Verbo.MOVER, lugares[c1].id, 0.88, 0.95, "anidar: avanzar a C1 para salir", clase="suelo")

        # 4. Fase salir
        if luz >= 0.5:
            if pos == c1:
                if e in piedras:
                    return Propuesta(Verbo.COGER, piedras[e].id, 0.92, 0.95, "anidar: picar piedra en E para salir", clase="piedra")
                if e in lugares:
                    return Propuesta(Verbo.MOVER, lugares[e].id, 0.88, 0.95, "anidar: salir a E", clase="suelo")
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
    OBJETIVOS = ["place_stone", "make_stone_pickaxe", "make_stone_sword", "place_furnace",
                 "make_iron_pickaxe", "make_iron_sword"]
    RECURSO = {"wood": "arbol", "stone": "piedra", "coal": "carbon", "iron": "hierro"}
    LOGROS_PLAN = set(OBJETIVOS) | {"place_table", "make_wood_pickaxe", "make_wood_sword",
                                    "collect_diamond", "collect_iron", "collect_coal", "place_plant", "collect_sapling"}

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
        if inv.get("energy", 9) <= 6 and _luz(ctx) >= 0.5 and not hostiles:
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
