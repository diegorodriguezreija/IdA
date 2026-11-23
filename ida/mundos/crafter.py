"""Crafter (Hafner, 2021): mundo de supervivencia en 2D con recursos, criaturas, día y noche.

Traducción al vocabulario común:
- Cuerpo: el juego marca salud, comida, bebida y energía (``vitales_propios``). La alimentación
  del soma es el mínimo entre comida y bebida.
- Entidades del entorno cercano (radio 4, como la vista oficial de 9×7; radio 2 de noche):
  árboles, agua, piedra, carbón, hierro, diamante, mesa, horno, lava, hierba, vacas, zombis,
  esqueletos y plantas. **Aliestesia:** el ``nutritivo`` del agua crece con la sed y el de la
  vaca o la planta madura, con el hambre.
- Lugares: las casillas vecinas transitables, con ``nutritivo`` (cuánto acercan a lo que el
  cuerpo necesita) y ``novedad``.
- Manual declarativo (paso 2, ``crafter_manual.json`` o ``crafter_manual_ampliado.json``, opción
  ``manual``): lo que declara UTIL tiene ``recurso`` 0,6. Sus proposiciones y requisitos entran en la memoria al nacer
  (``manual()``).
- El mundo no da ``peligro`` (paso 6): lo calcula la base con lo que aprende (``ida.sistemas.amenaza``), con el previo de
  lo que el manual declara PELIGROSO. La causa de un daño es lo peligroso **en contacto** (``_contacto``), sin geometría
  de alcance.
- Sin estrategias propias (paso 6d): la conducta de Crafter es la general de la base.
- Verbos: MOVER, COMER (beber agua, comer vaca o planta), ATACAR, COGER (talar, picar, recoger
  un retoño), USAR (colocar o fabricar, con la receta en la carga), DORMIR y ESPERAR. Para
  interactuar con algo adyacente, el mundo primero gira hacia ello y después hace ``do``.

Diferencias con el benchmark oficial: IdA lee el estado simbólico del juego, no los píxeles.

La tecnología (fabricar, colocar, qué recoger) ya no es conducta del mundo: la persigue la estrategia
general ``PerseguirMetas`` de S3 (paso 5) a partir de las metas y los requisitos del manual. La
propiocepción incluye lo que hay delante (``cuerpo["delante"]``), que se ve, y la clase de cada casilla a la vista
(``cuerpo["casillas"]``), para el mapa local de la base (paso 3).
"""

import collections
import copy
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from ida.core.mundo import Efecto, Entidad, Mundo, Necesidad, Observacion, Perfil, Registro
from ida.cuerpos.cuadricula import Cuadricula
from ida.core.vocabulario import Verbo

MATERIALES = {"tree": "arbol", "water": "agua", "stone": "piedra", "coal": "carbon", "iron": "hierro",
              "diamond": "diamante", "table": "mesa", "furnace": "horno", "lava": "lava"}
OBJETOS = {"Cow": "vaca", "Zombie": "zombi", "Skeleton": "esqueleto", "Plant": "planta", "Arrow": "flecha"}
RECURSO_MANUAL = 0.6   # recurso de lo que el manual declara UTIL
NUTRITIVO_MANUAL = 0.6   # paso 0b (aliestesia en la base): nutritivo de lo que el manual declara NUTRITIVO, constante
SUELOS = {"grass": "hierba", "sand": "arena", "path": "camino"}   # solo para lo de delante (no son entidades)
MANUALES = {"estricto": "crafter_manual.json", "ampliado": "crafter_manual_ampliado.json"}
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


def cargar_manual(nombre: str = "estricto") -> Dict[str, Any]:
    """Manual declarativo de Crafter (paso 2): ``"estricto"`` (artículo y README) o ``"ampliado"`` (además,
    hechos del código de Crafter). El ampliado carga primero todos los hechos del estricto.

    Los JSON usan los nombres del adaptador («madera», «pico_madera»); las claves de inventario de los
    requisitos se traducen aquí a las del inventario percibido (``wood``, ``wood_pickaxe``), que es lo que
    el individuo compara. ``inventario`` declara qué claves percibidas son objetos (no salud ni comida)."""
    if nombre not in MANUALES:
        raise ValueError(f"Manual de Crafter desconocido: {nombre!r} (opciones: {', '.join(MANUALES)})")
    carpeta = os.path.dirname(os.path.abspath(__file__))

    def leer(fichero: str) -> Dict[str, Any]:
        with open(os.path.join(carpeta, fichero), encoding="utf-8") as f:
            return dict(json.load(f))

    datos = leer(MANUALES[nombre])
    hechos = list(datos["hechos"])
    if datos.get("base"):
        hechos = list(leer(str(datos["base"]))["hechos"]) + hechos
    percibido = {v: k for k, v in INVENTARIO.items()}

    def traducir(d: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {percibido.get(k, k): v for k, v in (d or {}).items()}

    cargados = []
    for h in hechos:
        h = dict(h)
        if h.get("tipo") == "requisito":
            h["requiere_inventario"] = traducir(h.get("requiere_inventario"))
            h["efecto"] = traducir(h.get("efecto"))
        cargados.append(h)
    return {"nombre": nombre, "fuentes": datos.get("fuentes", {}), "hechos": cargados, "inventario": sorted(INVENTARIO)}


def _sujetos(manual: Dict[str, Any], relacion: str) -> Set[str]:
    """Clases que el manual afirma con esa relación."""
    return {str(h["sujeto"]) for h in manual.get("hechos", [])
            if h.get("tipo") == "proposicion" and h.get("relacion") == relacion and h.get("veredicto", "afirma") == "afirma"}


class MundoCrafter(Mundo):
    nombre = "crafter"
    # Deuda 14.0: Crafter es por turnos (el entorno espera a que el individuo decida), así que declara un plazo base
    # generoso. El marcapasos lo sigue acortando con el peligro y ``--plazo-logico`` escala con él.
    perfil = Perfil(tiempo_real=False, frecuencia_ms=1000.0, amplitud=120, memoria="completa", duerme=True, hogar=True,
                    peso_experiencia=0.15, vitales_propios=True,
                    necesidades=(Necesidad("hambre", ("comida",), 95.0, "nutritivo"), Necesidad("sed", ("agua",), 95.0, "nutritivo"),
                                 Necesidad("cansancio", ("energia",), 60.0), Necesidad("salud", ("vitalidad",), 100.0),
                                 Necesidad("cobijo", ("cobijo",), 100.0)),
                    intenciones=("progresar",),
                    rasgos_declarados=("nutritivo", "recurso", "novedad"))

    def __init__(self, radio: Any = 4, ventana: Any = 0, vista: str = "cuadrada", longitud: int = 100000,
                 manual: str = "estricto", **_):
        import crafter                     # dependencia solo de este mundo
        from crafter import constants
        self._crafter = crafter
        self.constantes = constants
        self._manual = cargar_manual(str(manual))
        self.peligrosos = _sujetos(self._manual, "PELIGROSO")
        self.utiles = _sujetos(self._manual, "UTIL")
        self.nutritivos = _sujetos(self._manual, "NUTRITIVO")
        self.acciones = {nombre: i for i, nombre in enumerate(constants.actions)}
        self.radio = int(radio)
        self.modo_vista = str(vista)
        self.longitud = int(longitud)
        self.ventana = str(ventana) in ("1", "si", "sí", "true")
        self.env: Any = None
        self.visitas: Dict[Pos, int] = {}
        self.t = 0
        self.fin = False
        self._tk: Any = None
        self._label: Any = None
        self._photo: Any = None

    # --- ciclo de vida -------------------------------------------------------
    def reiniciar(self, semilla: Optional[int], longitud: Optional[int] = None) -> None:
        long_ep = self.longitud if longitud is None else int(longitud)
        self.env = self._crafter.Env(seed=semilla, length=long_ep)
        mundo = self.env._world
        reset_original = mundo.reset

        def reset_ordenado(seed: Any = None) -> None:      # repetible: zonas con orden de inserción
            reset_original(seed=seed)
            mundo._chunks = collections.defaultdict(_ConjuntoOrdenado)

        mundo.reset = reset_ordenado
        self.env.reset()
        self.visitas, self.t, self.fin = {}, 0, False
        self._causa_contacto: Optional[str] = None
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
    def _limites_vista(self) -> Tuple[int, int]:
        w = self.env._world
        if self.modo_vista == "oficial":
            rx, ry = 4, 3
        else:
            rx = ry = self.radio
        if w.daylight < 0.3:
            rx = max(2, rx // 2)
            ry = max(2, ry // 2)
        return rx, ry

    def _vista_local(self) -> Dict[Pos, str]:
        """Rejilla cruda (coordenada -> material) de todas las casillas dentro del radio de visión actual."""
        w, (px, py) = self.env._world, self.jugador.pos
        rx, ry = self._limites_vista()
        vista: Dict[Pos, str] = {}
        for x in range(px - rx, px + rx + 1):
            for y in range(py - ry, py + ry + 1):
                if 0 <= x < w.area[0] and 0 <= y < w.area[1]:
                    mat, _ = w[(int(x), int(y))]
                    if mat is not None:
                        vista[(int(x), int(y))] = str(mat)
        return vista

    def _casillas(self) -> Dict[Pos, str]:
        """Clase de cada casilla a la vista (se ve), con los nombres de las entidades y de lo de delante: material o suelo.
        Lo que hay encima (criaturas, plantas) va aparte, como entidades. Para el mapa local de la base (paso 3)."""
        return {pos: MATERIALES.get(mat) or SUELOS.get(mat) or mat for pos, mat in self._vista_local().items()}

    def _cosas(self) -> List[Tuple[str, str, Pos, Any]]:
        """(id, clase, posición, objeto) de lo que hay en el radio de visión."""
        w, (px, py) = self.env._world, self.jugador.pos
        rx, ry = self._limites_vista()
        cosas = []
        for x in range(px - rx, px + rx + 1):
            for y in range(py - ry, py + ry + 1):
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

    def manual(self) -> Dict[str, Any]:
        """El manual elegido con la opción ``manual`` (``"estricto"`` por defecto o ``"ampliado"``)."""
        return copy.deepcopy(self._manual)

    def _nutritivo(self, clase: str, obj: Any) -> float:
        """Rasgo ``nutritivo`` de lo percibido, perceptivo y constante (paso 0b): ``NUTRITIVO_MANUAL`` si el manual
        declara la clase NUTRITIVO (la planta, solo madura: su textura se ve). Qué apetece según lo que falta lo
        decide la base (aliestesia: ``Apetencia`` y ``Alimentarse`` por necesidad)."""
        if clase not in self.nutritivos or (clase == "planta" and not (obj is not None and getattr(obj, "ripe", False))):
            return 0.0
        return NUTRITIVO_MANUAL

    def _delante(self) -> Optional[Dict[str, str]]:
        """Lo que hay en la casilla de delante (se ve): la criatura, si hay una, o el material o el suelo."""
        w, p = self.env._world, self.jugador
        x, y = int(p.pos[0] + p.facing[0]), int(p.pos[1] + p.facing[1])
        if not (0 <= x < w.area[0] and 0 <= y < w.area[1]):
            return None
        mat, obj = w[(x, y)]
        if obj is not None and type(obj).__name__ in OBJETOS:
            clase = OBJETOS[type(obj).__name__]
            if obj not in self._ids:
                self._ids[obj] = f"{clase}_{len(self._ids) + 1}"
            return {"id": self._ids[obj], "clase": clase}
        nombre = MATERIALES.get(str(mat)) or SUELOS.get(str(mat))
        return {"id": f"{nombre}_{x}_{y}", "clase": nombre} if nombre else None

    def observar(self) -> Observacion:
        p = self.jugador
        pos = tuple(p.pos)
        cosas = self._cosas()
        cosas.sort(key=lambda c: (c[1] not in self.peligrosos, _dist(pos, c[2])))
        entidades: List[Entidad] = []
        for cid, clase, cpos, obj in cosas[:14]:
            d = _dist(pos, cpos)
            rasgos = {
                "proximidad": 1.0 if d <= 1 else max(0.0, 1.0 - d / (2 * self.radio + 1)),
                "nutritivo": self._nutritivo(clase, obj),
                "recurso": RECURSO_MANUAL if clase in self.utiles else 0.0,
                "agente": 1.0 if obj is not None and clase != "planta" else 0.0,
            }
            entidades.append(Entidad(cid, clase, rasgos, {"pos": cpos}))
        deseables = [(c, self._nutritivo(c[1], c[3])) for c in cosas if self._nutritivo(c[1], c[3]) > 0.1]
        w = self.env._world
        for (dx, dy), _ in MOVIMIENTOS.items():
            c = (pos[0] + dx, pos[1] + dy)
            if not (0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1]):
                continue
            mat, obj = w[c]
            if mat not in self.constantes.walkable or obj is not None:
                continue
            nutritivo = 0.0
            for (_, _, dpos, _), valor in deseables:
                if _dist(c, dpos) < _dist(pos, dpos):
                    nutritivo = max(nutritivo, valor * (1.0 - _dist(c, dpos) / (4 * self.radio)))
            ultima = self.visitas.get(c)
            novedad = 1.0 if ultima is None else min(1.0, (self.t - ultima) / 50.0)
            celda = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "novedad": novedad}
            entidades.append(Entidad(f"celda_{c[0]}_{c[1]}", "suelo", celda, {"pos": c}))

        return Observacion(ubicacion=f"celda_{pos[0]}_{pos[1]}", entidades=entidades, vitales=self._vitales(), dormido=bool(p.sleeping),
                           inventario={k: float(v) for k, v in p.inventory.items()},
                           cuerpo={"orientacion": (int(p.facing[0]), int(p.facing[1])), "delante": self._delante(), "casillas": self._casillas()},
                           ambiente={"luz": float(w.daylight)})

    # --- registro (D3) y cuerpo (D10) ----------------------------------------
    def registro(self) -> Registro:
        """Crafter es un mundo de cuadrícula: registra ese cuerpo (``ModeloDirecto`` y ``MapaLocal``)."""
        return Registro(cuerpo=Cuadricula())

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER, Verbo.COMER, Verbo.ATACAR, Verbo.COGER, Verbo.USAR, Verbo.DORMIR, Verbo.ESPERAR}

    def _paso(self, accion: str) -> None:
        salud, antes = self.jugador.health, self._peligrosos_cerca(2)
        _, _, terminado, _ = self.env.step(self.acciones[accion])
        self.t += 1
        self.fin = self.fin or terminado
        if self.jugador.health < salud:
            causa = self._contacto(antes)
            if causa is not None:
                self._causa_contacto = causa

    def _peligrosos_cerca(self, radio: int) -> Dict[Any, Tuple[str, Pos]]:
        """Lo que el manual declara peligroso a ``radio`` casillas o menos (se ve): objeto -> (clase, posición)."""
        w, (px, py) = self.env._world, self.jugador.pos
        cerca: Dict[Any, Tuple[str, Pos]] = {}
        for x in range(px - radio, px + radio + 1):
            for y in range(py - radio, py + radio + 1):
                if (x, y) == (px, py) or _dist((px, py), (x, y)) > radio or not (0 <= x < w.area[0] and 0 <= y < w.area[1]):
                    continue
                mat, obj = w[(int(x), int(y))]
                clase = OBJETOS.get(type(obj).__name__) if obj is not None else MATERIALES.get(str(mat))
                if clase in self.peligrosos:
                    cerca[obj if obj is not None else (int(x), int(y))] = (str(clase), (int(x), int(y)))
        return cerca

    def _contacto(self, antes: Dict[Any, Tuple[str, Pos]]) -> Optional[str]:
        """Paso 6a: la causa de un daño es lo peligroso **en contacto**: lo que estaba junto a la casilla propia antes del
        paso y ya no está (un proyectil se deshace al dañar, en el mismo paso: ``Arrow.update`` de ``crafter/objects.py``),
        o, si no, lo que está junto a ella ahora (el zombi daña a distancia 1). Sin geometría de alcance. Entre varias, primero
        lo que se mueve (criaturas) y después los materiales (la lava solo daña si se entra en ella)."""
        pos = tuple(self.jugador.pos)
        ahora = self._peligrosos_cerca(3)

        def orden(o: Any, c: str, p: Pos) -> Tuple[bool, str, Pos]:
            return (isinstance(o, tuple), c, p)      # las claves de los materiales son su posición
        desaparecidos = sorted(orden(o, c, p) for o, (c, p) in antes.items() if o not in ahora and _dist(pos, p) <= 1)
        if desaparecidos:
            return desaparecidos[0][1]
        junto = sorted(orden(o, c, p) for o, (c, p) in ahora.items() if _dist(pos, p) <= 1)
        return junto[0][1] if junto else None

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
        self._causa_contacto = None
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
        causa = self._causa_contacto if delta.get("vitalidad", 0) < 0 else None
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

    def puntuacion(self) -> Dict[str, Any]:
        return {"logros": self.logros(), "n_logros": len(self.logros()), "pasos": self.t}

    def vista(self) -> str:
        pos = tuple(self.jugador.pos)
        mapa = {cpos: LETRA.get(clase, "?") for _, clase, cpos, _ in self._cosas()}
        filas = []
        rx, ry = self._limites_vista()
        for y in range(pos[1] - ry, pos[1] + ry + 1):
            filas.append("".join("@" if (x, y) == pos else mapa.get((x, y), ".") for x in range(pos[0] - rx, pos[0] + rx + 1)))
        inv = {k: v for k, v in self.jugador.inventory.items() if v}
        return "\n".join(filas) + f"\nluz {self.env._world.daylight:.2f} · {inv}\nlogros ({len(self.logros())}/{LOGROS}): {', '.join(self.logros())}"
