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
from ida.core.mundo import Efecto, Entidad, Mundo, Observacion, Perfil
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
                    peso_experiencia=0.15, vitales_propios=True)

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
        # Mapa cognitivo (hipocampo espacial): hitos clave del entorno (mesa, horno, agua, etc.)
        self.hitos: Dict[str, Pos] = {}

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
        self.hitos = {}
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
        return {"vitalidad": self.jugador.health / 9 * 100, "alimentacion": min(inv["food"], inv["drink"]) / 9 * 100,
                "energia": inv["energy"] / 9 * 100, "descanso": inv["energy"] / 9 * 100}

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
                                                                       "nutritivo": nutritivo, "novedad": novedad}, {"pos": c}))
        # Registrar hitos de infraestructura permanente en el mapa cognitivo (hipocampo)
        for _, clase, cpos, _ in cosas:
            if clase in ("mesa", "horno", "planta"):
                self.hitos[clase] = cpos
                if clase == "mesa":
                    self.hitos["table"] = cpos
                elif clase == "horno":
                    self.hitos["furnace"] = cpos
            elif clase == "agua" and "agua" not in self.hitos:
                self.hitos["agua"] = cpos
                self.hitos["water"] = cpos

        return Observacion(ubicacion=f"celda_{pos[0]}_{pos[1]}", entidades=entidades, vitales=self._vitales(), dormido=bool(p.sleeping))

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

    def componentes_propios(self) -> Dict[str, list]:
        return {
            "S1.Reaccionar": [DefensaCrafter(self)],
            "S3.Reaccionar": [PlanTecnologico(self)]
        }

    # --- resultados y vista --------------------------------------------------
    def logros(self) -> List[str]:
        a = self.jugador.achievements
        return sorted(k for k, v in a.items() if v) if isinstance(a, dict) else sorted(a)

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


class DefensaCrafter(Componente):
    """Componente propio de Crafter (S1 · Reaccionar): defensa activa armada y evasión crepuscular.

    Principio biológico:
    - Sin espada o con poca vitalidad (< 35%), luchar contra zombis/esqueletos es suicidio: la prioridad
      absoluta es la huida hacia un lugar seguro.
    - Con espada (hace 2-3 de daño) y vitalidad suficiente (>= 40%), el organismo puede abatir al hostil
      adyacente en 2-3 golpes, convirtiendo una amenaza mortal en defensa efectiva y logro de supervivencia.
    """

    tipo = "Reflejo"

    def __init__(self, mundo: MundoCrafter):
        super().__init__("DefensaCrafter")
        self.mundo = mundo

    def reactiva(self, ctx: Contexto) -> None:
        inv = self.mundo.inventario()
        tiene_espada = any(inv.get(k, 0) >= 1 for k in ("iron_sword", "stone_sword", "wood_sword"))
        salud = self.mundo.jugador.health

        # Buscar hostiles inmediatos (a distancia <= 1)
        hostiles_cerca = [p for p in ctx.onda.ev("Escena").values()
                          if p.clase in ("zombi", "esqueleto") and p.rasgo("proximidad") >= 0.9]

        if hostiles_cerca and tiene_espada and salud >= 4:
            amenaza = hostiles_cerca[0]
            # Con espada y salud suficiente, el ataque defensivo supera el reflejo de huida (0.75 + 0.25*peligro)
            urgencia = 0.96 if salud >= 6 else 0.88
            self.proponer(ctx, Verbo.ATACAR, amenaza.id, urgencia, 0.95, f"defensa armada: abatir {amenaza.clase}", clase=amenaza.clase)
            return


class PlanTecnologico(Componente):
    """Componente propio de Crafter (S3 · Reaccionar): avanza por el árbol tecnológico del juego.

    Usa las recetas de ``crafter.constants``: si puede fabricar o colocar algo útil, lo propone
    (USAR); si no, propone ir hacia el recurso que le falta o recogerlo si está al lado (COGER).
    Puntúa por debajo de la supervivencia, así que solo gana cuando nada urge.
    """

    tipo = "Comportamiento"
    OBJETIVOS = ["place_table", "make_wood_pickaxe", "make_wood_sword", "place_stone", "make_stone_pickaxe",
                 "make_stone_sword", "place_furnace", "make_iron_pickaxe", "make_iron_sword"]
    RECURSO = {"wood": "arbol", "stone": "piedra", "coal": "carbon", "iron": "hierro"}

    def __init__(self, mundo: MundoCrafter):
        super().__init__("PlanTecnologico")
        self.mundo = mundo
        self.fallos: Dict[str, int] = {}

    def _anotar_fallo(self, ctx: Contexto) -> None:
        previa = ctx.onda.ei("Ejecucion").get("Ejecucion")
        if previa is not None and str(previa.carga.get("motivo", "")).startswith("plan:") and previa.carga.get("exito") is False:
            obj = previa.carga["objetivo"]
            self.fallos[obj] = self.fallos.get(obj, 0) + 1

    def _cerca(self, materiales: List[str]) -> bool:
        w, (px, py) = self.mundo.env._world, self.mundo.jugador.pos
        return all(any(w[(px + dx, py + dy)][0] == m for dx in range(-1, 2) for dy in range(-1, 2)
                       if 0 <= px + dx < w.area[0] and 0 <= py + dy < w.area[1]) for m in materiales)

    def _falta(self, receta: str) -> Dict[str, int]:
        c = self.mundo.constantes
        tipo, nombre = receta.split("_", 1)
        info = c.place[nombre] if tipo == "place" else c.make[nombre]
        return info["uses"]

    def _oportunidades(self, ctx: Contexto, inv: Dict[str, int], hecho: Set[str]) -> bool:
        """Logros baratos al alcance: minerales con el pico adecuado, retoño y plantarlo."""
        for logro, clase, herramienta in (("collect_diamond", "diamante", "iron_pickaxe"), ("collect_iron", "hierro", "stone_pickaxe"),
                                          ("collect_coal", "carbon", "wood_pickaxe")):
            if logro in hecho or inv.get(herramienta, 0) < 1:
                continue
            for p in ctx.onda.ev("Escena").values():
                if p.clase == clase and p.rasgo("proximidad") >= 0.9 and self.fallos.get(p.id, 0) < 3:
                    self.proponer(ctx, Verbo.COGER, p.id, 0.55, 0.8, f"plan: {logro}", clase=clase)
                    return True
        if "place_plant" not in hecho and inv.get("sapling", 0) >= 1 and self.fallos.get("place_plant", 0) < 3:
            w, pos, cara = self.mundo.env._world, self.mundo.jugador.pos, self.mundo.jugador.facing
            frente = (int(pos[0] + cara[0]), int(pos[1] + cara[1]))
            if 0 <= frente[0] < w.area[0] and 0 <= frente[1] < w.area[1] and w[frente][0] == "grass" and w[frente][1] is None:
                self.proponer(ctx, Verbo.USAR, "place_plant", 0.5, 0.8, "plan: place_plant", clase="place_plant", receta="place_plant")
                return True
        hostiles = any(p.clase in HOSTILES and p.clase != "lava" for p in ctx.onda.ev("Escena").values())
        if inv.get("energy", 9) <= 6 and self.mundo.env._world.daylight >= 0.5 and not hostiles:
            # Dormir de día, sin hostiles a la vista, para no llegar agotado a la noche (y lograr wake_up).
            self.proponer(ctx, Verbo.DORMIR, "", 0.6, 0.85, "plan: dormir de día para afrontar la noche", clase="")
            return True
        if "collect_sapling" not in hecho and inv.get("sapling", 0) == 0:
            w, (px, py) = self.mundo.env._world, self.mundo.jugador.pos
            for dx, dy in MOVIMIENTOS:
                c = (int(px + dx), int(py + dy))
                cid = f"hierba_{c[0]}_{c[1]}"
                if 0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1] and w[c][0] == "grass" and w[c][1] is None and self.fallos.get(cid, 0) < 6:
                    self.proponer(ctx, Verbo.COGER, cid, 0.4, 0.7, "plan: collect_sapling", clase="hierba")
                    return True
        return False

    def reactiva(self, ctx: Contexto) -> None:
        self._anotar_fallo(ctx)
        inv = self.mundo.inventario()
        hecho = set(self.mundo.logros())
        if self._oportunidades(ctx, inv, hecho):
            return
        for receta in self.OBJETIVOS:
            if receta in hecho or self.fallos.get(receta, 0) >= 3:
                continue
            usos = self._falta(receta)
            if all(inv.get(k, 0) >= v for k, v in usos.items()):
                if receta.startswith("make_"):
                    cerca = self.mundo.constantes.make[receta[5:]]["nearby"]
                    if not self._cerca(cerca):
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
        """Orienta el movimiento hacia una estructura del taller (mesa, horno) recordada en el mapa."""
        # 1. ¿Está visible en la escena actual?
        candidatos = [p for p in ctx.onda.ev("Escena").values() if p.clase == estructura and p.rasgo("proximidad") >= 0.1]
        destino_pos = None
        if candidatos:
            objetivo = max(candidatos, key=lambda p: p.rasgo("proximidad"))
            destino_pos = objetivo.carga["datos"]["pos"]
        elif estructura in self.mundo.hitos:
            destino_pos = self.mundo.hitos[estructura]
        if destino_pos is None:
            return False

        pos = tuple(self.mundo.jugador.pos)
        lugares = [p for p in ctx.onda.ev("Escena").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5]
        mejor = min(lugares, key=lambda l: _dist(l.carga["datos"]["pos"], destino_pos), default=None)
        if mejor is not None and _dist(mejor.carga["datos"]["pos"], destino_pos) < _dist(pos, destino_pos):
            self.proponer(ctx, Verbo.MOVER, mejor.id, 0.48, 0.75, f"hipocampo: volver a {estructura}", clase=mejor.clase)
            return True
        return False

    def _buscar(self, ctx: Contexto, recurso: str) -> None:
        clase = self.RECURSO.get(recurso)
        if clase is None:
            return
        candidatos = [p for p in ctx.onda.ev("Escena").values() if p.clase == clase and self.fallos.get(p.id, 0) < 3]
        if not candidatos:
            return
        objetivo = max(candidatos, key=lambda p: p.rasgo("proximidad"))
        if objetivo.rasgo("proximidad") >= 0.9:
            self.proponer(ctx, Verbo.COGER, objetivo.id, 0.5, 0.75, f"plan: conseguir {recurso}", clase=clase)
            return
        destino_pos = objetivo.carga["datos"]["pos"]
        pos = tuple(self.mundo.jugador.pos)
        lugares = [p for p in ctx.onda.ev("Escena").values() if p.rasgo("lugar") >= 0.5 and p.rasgo("peligro") < 0.5]
        mejor = min(lugares, key=lambda l: _dist(l.carga["datos"]["pos"], destino_pos), default=None)
        if mejor is not None and _dist(mejor.carga["datos"]["pos"], destino_pos) < _dist(pos, destino_pos):
            self.proponer(ctx, Verbo.MOVER, mejor.id, 0.45, 0.7, f"plan: ir a por {recurso}", clase=mejor.clase)

