"""Crafter (Hafner, 2021): mundo de supervivencia en 2D con recursos, criaturas, día y noche.

Traducción al vocabulario común:
- Cuerpo: el juego marca salud, comida, bebida y energía (``vitales_propios``). La alimentación
  del soma es el mínimo entre comida y bebida.
- Entidades del entorno cercano (radio 4, como la vista oficial de 9×7; radio 2 de noche):
  árboles, agua, piedra, carbón, hierro, diamante, mesa, horno, lava, hierba, vacas, zombis,
  esqueletos y plantas, en bruto: ``proximidad`` y ``agente`` (y ``datos["madura"]`` de las plantas, que se ve).
- Lugares: las casillas vecinas transitables, con ``lugar`` y ``proximidad``.
- La valoración es del organismo (A4, D4): ``ValoracionCrafter`` (``s1/sentir/valoracion.py``), preatentivo de S1 que
  registra este mundo, pone ``nutritivo`` y ``recurso`` a las cosas y ``nutritivo`` y ``novedad`` a los lugares.
- Manual declarativo (paso 2, ``crafter_manual.json`` o ``crafter_manual_ampliado.json``, opción
  ``manual``): lo que declara NUTRITIVO y UTIL lo recibe ``ValoracionCrafter`` (valor 0,6). Sus proposiciones y
  requisitos entran en la memoria al nacer (``manual()``).
- El mundo no da ``peligro`` (paso 6): lo calcula la base con lo que aprende (``ida.s1.sentir.amenaza``), con el previo de
  lo que el manual declara PELIGROSO. La causa de un daño es lo peligroso **en contacto** (``_contacto``), sin geometría
  de alcance.
- Sin estrategias propias (paso 6d): la conducta de Crafter es la general de la base.
- Verbos: MOVER, COMER (beber agua, comer vaca o planta), ATACAR, COGER (talar, picar, recoger
  un retoño), USAR (colocar o fabricar, con la receta en la carga), DORMIR y ESPERAR. El mundo ejecuta primitivas (las
  acciones del juego, D9): la traducción de cada verbo (girar y ``do`` para interactuar con algo adyacente) y el juicio
  de su éxito son del Motor del cuerpo cuadrícula; el adaptador solo mide.

Diferencias con el benchmark oficial: IdA lee el estado simbólico del juego, no los píxeles.

Escena (O6) y opciones (O8): ``escena()`` describe en rejilla lo que se ve (la misma ventana que ``vista()``) y
``opciones()`` declara las opciones con los valores por defecto de la medición oficial de D17 (``evaluar_crafter.py``).
Los valores por defecto del constructor no cambian: son los de la invariancia.

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

from ida.nucleo.mundo import Alta, Efecto, Entidad, Escala, Mundo, Necesidad, Observacion, Perfil, Registro
from ida.mundos.opciones import opcion
from ida.cuerpos.cuadricula import Cuadricula
from ida.mundos.crafter.s1.sentir.valoracion import ValoracionCrafter
from ida.mundos.crafter.s1.interpretar.recinto import ALCANCE_SITIO, Recinto
from ida.mundos.crafter.s1.reaccionar.estrategias.salir_del_recinto import SalirDelRecinto
from ida.nucleo.vocabulario import Verbo

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

VITALES_JUEGO = {"health": "salud", "food": "comida", "drink": "bebida", "energy": "energia"}   # para la escena
ORIENTACION = {(0, -1): "norte", (0, 1): "sur", (1, 0): "este", (-1, 0): "oeste"}   # x a la derecha, y hacia abajo
LADO_MAPA = 64          # el de crafter.Env (area=(64, 64))

Pos = Tuple[int, int]


def _t(es: str, en: str) -> Dict[str, str]:
    return {"es": es, "en": en}


# O8: el defecto declarado es el de la medición oficial de D17 (``herramientas/evaluar_crafter.py``: vista «oficial»,
# longitud 10000, manual «estricto», radio y ventana sin tocar). Las opciones nuevas (sección 8), por defecto, dan lo
# de hoy: el mapa de 64×64 de crafter y la semilla del mapa igual a la del organismo.
OPCIONES = [
    opcion("vista", "opcion", "oficial",
           _t("Vista", "View"),
           _t("Oficial: 9×7 casillas, como el benchmark de Crafter. Cuadrada: (2·radio+1)² casillas. De noche, la mitad.",
              "Official: 9×7 tiles, as in the Crafter benchmark. Square: (2·radius+1)² tiles. Half at night."),
           valores=["oficial", "cuadrada"]),
    opcion("radio", "entero", 4,
           _t("Radio de visión", "Sight radius"),
           _t("Alcance de la vista cuadrada y escala de la proximidad y del gradiente de la valoración, en casillas.",
              "Reach of the square view and scale of proximity and of the valuation gradient, in tiles."),
           min=2, max=8),
    opcion("manual", "opcion", "estricto",
           _t("Manual", "Manual"),
           _t("Lo que IdA sabe al nacer. Estricto: el artículo y el README de Crafter. Ampliado: además, hechos de su código.",
              "What IdA knows at birth. Strict: the Crafter paper and README. Extended: also facts from its code."),
           valores=["estricto", "ampliado"]),
    opcion("longitud", "entero", 10000,
           _t("Longitud del episodio", "Episode length"),
           _t("Pasos del juego tras los que Crafter termina la partida (10 000 en el benchmark oficial).",
              "Game steps after which Crafter ends the episode (10,000 in the official benchmark)."),
           min=100, max=1000000),
    opcion("mapa", "entero", LADO_MAPA,
           _t("Tamaño del mapa", "Map size"),
           _t("Lado del mapa en casillas (64 en Crafter). IdA nace en el centro.",
              "Map side in tiles (64 in Crafter). IdA is born at the centre."),
           min=32, max=128),
    opcion("semilla_mapa", "entero", None,
           _t("Semilla del mapa", "Map seed"),
           _t("Fija el mapa con independencia de la semilla del organismo. Vacía: la del organismo (cada generación, un mapa).",
              "Fixes the map regardless of the organism seed. Empty: the organism's (each generation, a new map)."),
           min=0, max=2**31 - 2, vacia=True),
    opcion("ventana", "booleano", False,
           _t("Ventana de Crafter", "Crafter window"),
           _t("Abre una ventana con el dibujo oficial de Crafter (necesita tkinter y Pillow).",
              "Opens a window with the official Crafter rendering (needs tkinter and Pillow)."),
           ),
]


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
                    rasgos_declarados=(),
                    # Escala de Crafter (D15): la salud son 9 puntos (vitalidad 0-100)
                    escala=Escala(dano_previo=100.0 * 2.0 / 9.0,      # un golpe desconocido quita 2 de 9
                                  golpes_previo=10.0,                 # golpes para derribar algo sin datos
                                  margen_lugar=3,                     # casillas tras el alcance de lo peligroso
                                  reserva=100.0 * 3.0 / 9.0,          # una lucha deja intactos 3 de 9
                                  coste_sin_sitio=float(3 * ALCANCE_SITIO),   # sin sitio: ir y volver al alcance de búsqueda
                                  coste_recordado=15.0,               # ir a algo recordado no visible
                                  coste_por_proximidad=10.0,          # cruzar el alcance visible
                                  coste_sin_productor=30.0))          # reponer sin acción conocida

    def __init__(self, radio: Any = 4, ventana: Any = 0, vista: str = "cuadrada", longitud: int = 100000,
                 manual: str = "estricto", mapa: Any = LADO_MAPA, semilla_mapa: Any = None, **_):
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
        self.ventana = ventana is True or str(ventana).lower() in ("1", "si", "sí", "true")
        self.lado_mapa = int(mapa)
        self.semilla_mapa = None if semilla_mapa in (None, "") else int(semilla_mapa)
        self.env: Any = None
        self.t = 0
        self.fin = False
        self._tk: Any = None
        self._label: Any = None
        self._photo: Any = None

    @classmethod
    def opciones(cls) -> List[Dict[str, Any]]:
        """O8: vista, radio, manual, longitud, mapa, semilla del mapa y ventana, con los defectos de la medición oficial."""
        return copy.deepcopy(OPCIONES)

    # --- ciclo de vida -------------------------------------------------------
    def reiniciar(self, semilla: Optional[int], longitud: Optional[int] = None) -> None:
        long_ep = self.longitud if longitud is None else int(longitud)
        semilla_env = semilla if self.semilla_mapa is None else self.semilla_mapa   # opción ``semilla_mapa``
        self.env = self._crafter.Env(area=(self.lado_mapa, self.lado_mapa), seed=semilla_env, length=long_ep)
        mundo = self.env._world
        reset_original = mundo.reset

        def reset_ordenado(seed: Any = None) -> None:      # repetible: zonas con orden de inserción
            reset_original(seed=seed)
            mundo._chunks = collections.defaultdict(_ConjuntoOrdenado)

        mundo.reset = reset_ordenado
        self.env.reset()
        self.t, self.fin = 0, False
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
                "agente": 1.0 if obj is not None and clase != "planta" else 0.0,
            }
            datos: Dict[str, Any] = {"pos": cpos}
            if clase == "planta":
                datos["madura"] = bool(getattr(obj, "ripe", False))   # se ve en su textura (en bruto)
            entidades.append(Entidad(cid, clase, rasgos, datos))
        w = self.env._world
        for (dx, dy), _ in MOVIMIENTOS.items():
            c = (pos[0] + dx, pos[1] + dy)
            if not (0 <= c[0] < w.area[0] and 0 <= c[1] < w.area[1]):
                continue
            mat, obj = w[c]
            if mat not in self.constantes.walkable or obj is not None:
                continue
            entidades.append(Entidad(f"celda_{c[0]}_{c[1]}", "suelo", {"lugar": 1.0, "proximidad": 1.0}, {"pos": c}))

        # B5: transitorio. ``vista`` = lo que se ve y cuyo id no lleva coordenadas (criaturas y plantas: los objetos de
        # ``_cosas()``), en bruto y sin valorar: id -> {"clase", "pos": [x, y]} y, si es planta, "madura". Para que el Motor
        # del cuerpo localice un objetivo y la valoración del organismo (``ValoracionCrafter``) vea lo que el corte de 14
        # entidades de arriba deja fuera de las piezas. Los materiales a la vista ya van en ``casillas``. Desaparece al
        # quitar el corte (B5).
        vista: Dict[str, Dict[str, Any]] = {}
        for cid, clase, cpos, obj in cosas:
            if obj is not None:
                vista[cid] = {"clase": clase, "pos": [int(cpos[0]), int(cpos[1])]}
                if clase == "planta":
                    vista[cid]["madura"] = bool(getattr(obj, "ripe", False))
        return Observacion(ubicacion=f"celda_{pos[0]}_{pos[1]}", entidades=entidades, vitales=self._vitales(), dormido=bool(p.sleeping),
                           inventario={k: float(v) for k, v in p.inventory.items()},
                           cuerpo={"orientacion": (int(p.facing[0]), int(p.facing[1])), "delante": self._delante(), "casillas": self._casillas(),
                                   "vista": vista},
                           ambiente={"luz": float(w.daylight)})

    # --- registro (D3) y cuerpo (D10) ----------------------------------------
    def registro(self) -> Registro:
        """Crafter es un mundo de cuadrícula: registra ese cuerpo (``ModeloDirecto``, ``MapaLocal`` y su Motor) y su
        valoración preatentiva (``ValoracionCrafter``, D4), con lo que el manual declara NUTRITIVO y UTIL."""
        cuerpo = Cuadricula()
        valoracion = ValoracionCrafter(self.nutritivos, self.utiles, cuerpo, valor_nutritivo=NUTRITIVO_MANUAL,
                                       valor_recurso=RECURSO_MANUAL, alcance_gradiente=4 * self.radio)
        return Registro(
            componentes={"S1.Sentir": Alta(añade=[valoracion]), "S1.Interpretar": Alta(añade=[Recinto()])},
            estrategias={"S1": Alta(añade=[SalirDelRecinto()])},
            cuerpo=cuerpo,
            opcionales=["Apetencia", "Amenaza", "Afrontar", "Proteger"],   # generales opcionales que monta (D3, D15)
        )

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

    def primitivas(self) -> List[str]:
        """Las acciones del juego (``constants.actions``)."""
        return list(self.constantes.actions)

    def ejecutar_primitivas(self, primitivas: List[str]) -> Efecto:
        """Ejecuta las primitivas en orden y mide antes de la primera y después de la última. ``exito`` queda en True:
        juzga el Motor del cuerpo con ``medidas`` (inventario antes y después y qué claves son objetos)."""
        p = self.jugador
        antes = {"salud": p.health, **dict(p.inventory)}
        inventario_antes = dict(p.inventory)
        logros_antes = {k for k, v in p.achievements.items() if v} if isinstance(p.achievements, dict) else set(p.achievements)
        self._causa_contacto = None
        for primitiva in primitivas:
            self._paso(primitiva)
        ef = self._efecto(antes, logros_antes)
        ef.medidas = {"inventario_antes": inventario_antes, "inventario_despues": dict(p.inventory), "objetos": sorted(INVENTARIO)}
        self._actualizar_ventana()
        return ef

    def _efecto(self, antes: Dict[str, int], logros_antes: Set[str]) -> Efecto:
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
        return Efecto(True, delta, causa=causa, obtenido=ganados[0] if ganados else None,
                      muerte=p.health <= 0, mensaje=("logro: " + ", ".join(nuevos)) if nuevos else "")

    def terminado(self) -> bool:
        return self.fin


    # --- resultados y vista --------------------------------------------------
    def logros(self) -> List[str]:
        a = self.jugador.achievements
        return sorted(k for k, v in a.items() if v) if isinstance(a, dict) else sorted(a)

    def puntuacion(self) -> Dict[str, Any]:
        return {"logros": self.logros(), "n_logros": len(self.logros()), "pasos": self.t}

    def escena(self) -> Dict[str, Any]:
        """Escena v1 en rejilla (O6): la ventana que se ve (la de ``vista()``; de noche, más pequeña), con el fondo de
        cada casilla (``None`` fuera del mapa), las criaturas y plantas, el individuo en el centro con su orientación,
        el inventario (con las constantes del juego) y, en ``extra``, la luz del día y los logros. Coordenadas desde la
        esquina de arriba a la izquierda de la ventana; ``origen`` es esa esquina en el mapa.

        Solo lee (O3). Las criaturas salen de ``_cosas()``, la misma vía que ``observar()`` y ``vista()``: asigna un id a
        la que se ve por primera vez, pero el observador llama a ``vista()`` y a ``escena()`` al final del latido, sin
        que el entorno avance antes del ``observar()`` siguiente, así que los ids y su orden son los mismos."""
        p = self.jugador
        px, py = int(p.pos[0]), int(p.pos[1])
        rx, ry = self._limites_vista()
        x0, y0 = px - rx, py - ry
        fondo = self._casillas()
        celdas = [[fondo.get((x0 + i, y0 + j)) for i in range(2 * rx + 1)] for j in range(2 * ry + 1)]
        entidades: List[Dict[str, Any]] = []
        for cid, clase, (x, y), obj in self._cosas():
            if obj is None:            # los materiales ya están en el fondo
                continue
            e: Dict[str, Any] = {"clase": clase, "x": int(x) - x0, "y": int(y) - y0, "id": cid}
            if clase == "planta" and bool(getattr(obj, "ripe", False)):
                e["estado"] = "madura"
            elif clase == "flecha":
                e["estado"] = ORIENTACION.get((int(obj.facing[0]), int(obj.facing[1])), "")
            entidades.append(e)
        yo: Dict[str, Any] = {"x": rx, "y": ry, "orientacion": ORIENTACION.get((int(p.facing[0]), int(p.facing[1])))}
        if p.sleeping:
            yo["estado"] = "dormido"
        inventario = {VITALES_JUEGO.get(k) or INVENTARIO.get(k, k): int(v) for k, v in p.inventory.items()}
        return {"tipo": "rejilla", "ancho": 2 * rx + 1, "alto": 2 * ry + 1, "origen": [x0, y0], "celdas": celdas,
                "entidades": entidades, "yo": yo, "inventario": inventario,
                "extra": {"luz": round(float(self.env._world.daylight), 2), "logros": self.logros()}}

    def vista(self) -> str:
        pos = tuple(self.jugador.pos)
        mapa = {cpos: LETRA.get(clase, "?") for _, clase, cpos, _ in self._cosas()}
        filas = []
        rx, ry = self._limites_vista()
        for y in range(pos[1] - ry, pos[1] + ry + 1):
            filas.append("".join("@" if (x, y) == pos else mapa.get((x, y), ".") for x in range(pos[0] - rx, pos[0] + rx + 1)))
        inv = {k: v for k, v in self.jugador.inventory.items() if v}
        return "\n".join(filas) + f"\nluz {self.env._world.daylight:.2f} · {inv}\nlogros ({len(self.logros())}/{LOGROS}): {', '.join(self.logros())}"
