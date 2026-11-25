"""Requisito (D7, S3 · Interpretar, general): requisitos de las acciones, intentos fallidos y metas del manual.

Es el dueño de la sección «requisitos» de la Memoria: lo único que escribe en ella. Aprende del efecto de la acción
anterior (``aprender``) en el mismo punto del latido en que antes lo hacía ``Organismo._aprender``, con lo que había
justo antes de actuar (``antes_de_actuar``, donde estaba ``Organismo._antes_accion``). No tiene barridos (``activo`` es
False): no cobra ni cuenta operaciones en el latido. «Delante» y «cerca» los da el cuerpo en la pieza ``Propiocepcion``
«yo» (``cuerpo["delante"]``) y las ``Exterocepcion``; la posición relativa de lo cercano, el espacio del cuerpo
(``Contexto.espacio``, D10).
"""

import math
from typing import Any, Dict, Hashable, List, Optional, Set, Tuple, cast

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.memoria import Memoria, Meta, Seccion
from ida.nucleo.memoria import Requisito as RequisitoAccion
from ida.nucleo.mundo import SIN_ESPACIO, Cuerpo, Perfil
from ida.nucleo.onda import Onda
from ida.nucleo.pieza import Pieza
from ida.nucleo.vocabulario import Verbo

Situacion = Tuple[Dict[str, float], Set[str], Optional[str], Dict[str, Hashable]]


class Requisitos(Seccion):
    """Sección «requisitos» de la Memoria (D7): requisitos de las acciones e intentos fallidos (paso 2), metas del manual,
    bloqueo por fallos seguidos y objetos ya tenidos (paso 5)."""

    orden_legado = 1     # D7: su parte va la primera tras lo del Core (la forma de antes)
    PASO_CONFIANZA_REQUISITO = 0.1
    MAX_INTENTOS = 50           # intentos fallidos recordados por (verbo, objetivo); se olvidan los más antiguos
    FALLOS_BLOQUEO = 3          # paso 5: fallos seguidos sin ningún éxito que bloquean una acción

    def __init__(self) -> None:
        self.requisitos: Dict[Tuple[Verbo, str], RequisitoAccion] = {}
        self.intentos: Dict[Tuple[Verbo, str], List[Dict[str, float]]] = {}
        self.claves_inventario: Optional[Set[str]] = None   # si el manual las declara, solo esas cuentan como objetos
        self.metas: Dict[Tuple[Verbo, str], Meta] = {}
        self.fallos_seguidos: Dict[Tuple[Verbo, str], int] = {}
        self._tenidos: Set[str] = set()
        self._tenidos_iniciado = False

    # --- sección de la Memoria (D7) ---------------------------------------------
    def aplicar_manual(self, manual: Dict[str, Any]) -> None:
        """El inventario que declara el manual, sus metas (sin conseguir) y sus requisitos (fuente «manual»). Un requisito
        repetido (mismo verbo y objetivo) completa al anterior: fija cantidades desconocidas y suma lo que falte."""
        if not self.activa or not manual:
            return
        if manual.get("inventario") is not None:
            self.claves_inventario = {str(k) for k in manual["inventario"]}
        for h in manual.get("hechos", []):
            tipo = h.get("tipo")
            if tipo == "meta":
                clave_m = (Verbo[h["verbo"]], str(h.get("objetivo", "")))
                self.metas.setdefault(clave_m, Meta(clave_m[0], clave_m[1], str(h.get("id", ""))))
            elif tipo == "requisito":
                clave = (Verbo[h["verbo"]], str(h["objetivo"]))
                inv = {str(k): (None if v is None else int(v)) for k, v in (h.get("requiere_inventario") or {}).items()}
                cerca = {str(c) for c in h.get("requiere_cerca") or []}
                efecto = {str(k): int(v) for k, v in (h.get("efecto") or {}).items()}
                aparece = {str(c) for c in h.get("aparece") or []}
                r = self.requisitos.get(clave)
                if r is None:
                    self.requisitos[clave] = RequisitoAccion(clave[0], clave[1], inv, cerca, efecto, fuente="manual",
                                                             confianza=Memoria.CONFIANZA_MANUAL, aparece=aparece)
                else:
                    for k, v in inv.items():
                        previo = r.requiere_inventario.get(k)
                        r.requiere_inventario[k] = v if previo is None else (previo if v is None else max(previo, v))
                    r.requiere_cerca |= cerca
                    r.efecto.update(efecto)
                    r.aparece |= aparece

    def legado(self, ahora: int) -> Dict[str, Any]:
        """Los requisitos que la experiencia ha visto cumplirse al menos una vez."""
        requisitos = [r.a_dict() for r in self.requisitos.values() if r.exitos >= 1]
        return {"requisitos": requisitos} if requisitos else {}

    def heredar(self, legado: Dict[str, Any], tasa: float = 1.0) -> int:
        """Con ``tasa`` < 1 (bloque E, E7) solo pasa esa fracción: los de más éxitos (redondeo hacia arriba)."""
        if not self.activa:
            return 0
        requisitos = list(legado.get("requisitos", []))
        if tasa < 1.0:
            k = math.ceil(max(0.0, tasa) * len(requisitos))
            requisitos = sorted(requisitos, key=lambda d: -float(d["exitos"]))[:k]
        n = 0
        for d in requisitos:   # lo heredado sustituye a lo del manual: la experiencia del linaje lo ha corregido
            req = RequisitoAccion(
                Verbo[d["verbo"]], str(d["objetivo"]),
                {str(k): (None if v is None else int(v)) for k, v in d.get("requiere_inventario", {}).items()},
                {str(c) for c in d.get("requiere_cerca", [])},
                {str(k): int(v) for k, v in d.get("efecto", {}).items()},
                fuente=str(d.get("fuente", "experiencia")), confianza=float(d.get("confianza", 0.5)) * 0.8,
                exitos=max(1, int(d.get("exitos", 1)) // 2), fallos=int(d.get("fallos", 0)) // 2, heredado=True,
            )
            self.requisitos[(req.verbo, req.objetivo)] = req
            n += 1
        return n

    def objetos(self, inventario: Dict[str, float]) -> Dict[str, float]:
        """Las claves del inventario que son objetos (todas, si el manual no lo declara)."""
        if self.claves_inventario is None:
            return {k: float(v) for k, v in inventario.items()}
        return {k: float(v) for k, v in inventario.items() if k in self.claves_inventario}

    def bloqueada(self, verbo: Verbo, objetivo: str) -> bool:
        """Paso 5 (5.2 b): una acción que nunca ha funcionado y ha fallado ``FALLOS_BLOQUEO`` veces seguidas
        no se vuelve a intentar hasta que el inventario gane un tipo de objeto nuevo. Una acción cuyo efecto
        puede salir (``puede_salir``) no se bloquea: si es probabilística, fallar seguido no dice que no
        funcione; lo que dicen los fallos lo recoge su coste (``tasa_estimada``)."""
        if self.puede_salir(verbo, objetivo):
            return False
        return self.fallos_seguidos.get((verbo, objetivo), 0) >= self.FALLOS_BLOQUEO

    def declarada(self, verbo: Verbo, objetivo: str) -> bool:
        """El manual declara la acción: es una de sus metas o tiene un requisito suyo (fuente «manual»)."""
        r = self.requisitos.get((verbo, objetivo))
        return (verbo, objetivo) in self.metas or (r is not None and r.fuente == "manual")

    def puede_salir(self, verbo: Verbo, objetivo: str) -> bool:
        """Según la experiencia (algún éxito) o el manual (``declarada``), el efecto de la acción puede salir,
        aunque sea con poca probabilidad."""
        r = self.requisitos.get((verbo, objetivo))
        return (r is not None and r.exitos > 0) or self.declarada(verbo, objetivo)

    def tasa_estimada(self, verbo: Verbo, objetivo: str) -> float:
        """Tasa de éxito estimada: (éxitos + w) / (éxitos + fallos + w), con w = ``PESO_MANUAL`` si el manual
        declara la acción (su declaración pesa como un éxito propio, como sus proposiciones) y 0 si no. Los
        fallos son los del requisito o, sin requisito aún, los intentos fallidos recordados (hasta
        ``MAX_INTENTOS``). 1 sin intentos."""
        clave = (verbo, objetivo)
        r = self.requisitos.get(clave)
        exitos = r.exitos if r is not None else 0
        fallos = r.fallos if r is not None else len(self.intentos.get(clave, []))
        w = Memoria.PESO_MANUAL if self.declarada(verbo, objetivo) else 0.0
        total = exitos + fallos + w
        return (exitos + w) / total if total > 0 else 1.0

    def aprender_requisito(
        self,
        verbo: Verbo,
        objetivo: str,
        inv_antes: Dict[str, float],
        inv_despues: Dict[str, float],
        cerca: Set[str],
        exito: bool,
        cerca_despues: Optional[Set[str]] = None,
        delante: Optional[str] = None,
        distancias: Optional[Dict[str, Hashable]] = None,
        espacio: Cuerpo = SIN_ESPACIO,
    ) -> None:
        """Tras una acción con objetivo: contrasta el inventario de antes y de después.

        - Hay efecto si la acción tuvo éxito **y** el inventario cambió. Lo consumido fija la cantidad exacta;
          un requisito que no se conocía se descubre (fuente «experiencia»). Lo que aparece cerca y antes no
          estaba queda en ``aparece``. Si antes había fallado, lo que hay ahora y faltaba en todos los fallos
          se induce como requisito (5.2 a) y esos intentos se olvidan.
        - Sin efecto, el intento se recuerda. Si se creía cumplir el requisito, alguna cantidad desconocida
          es mayor: sube a lo que había + 1, salvo las que ya fijó lo consumido en un éxito.
        - ``delante``: la clase de lo que había delante; las clases donde funcionó forman ``requiere_delante``
          y aquellas donde solo ha fallado, ``delante_fallido`` (5.2 d).
        - Ganar un tipo de objeto que no se tenía desbloquea todas las acciones bloqueadas (5.2 b).
        - Un requisito descubierto por un primer éxito sin fallos previos solo registra el efecto: los requisitos
          de inventario los añade la inducción por diferencia.
        - ``distancias`` (clase → posición relativa que da el cuerpo, ``espacio``, hasta su ``radio_prueba``): con
          éxito, la posición relativa queda como válida para cada requisito de cercanía; con fallo y el inventario
          cumplido, como fallida si está más lejos que lo contiguo (salvo si ya funcionó desde ahí).
        - Inducción por diferencia: solo cuentan los fallos que no explica ya un requisito conocido (con el
          inventario del fallo por debajo de una cantidad conocida o estimada, el fallo ya tiene causa).
        - ``delante`` solo cuenta para USAR (COGER y COMER se orientan hacia su objetivo antes de actuar).
        """
        if not self.activa or not objetivo:
            return
        if verbo != Verbo.USAR:
            delante = None
        distancias = distancias or {}
        antes_obj, despues_obj = self.objetos(inv_antes), self.objetos(inv_despues)
        claves = sorted(set(antes_obj) | set(despues_obj))
        antes = {k: antes_obj.get(k, 0.0) for k in claves}
        delta = {k: int(round(despues_obj.get(k, 0.0) - antes[k])) for k in claves}
        delta = {k: d for k, d in delta.items() if d}
        nuevos = {k for k, v in despues_obj.items() if v >= 1} - self._tenidos - {k for k, v in antes_obj.items() if v >= 1}
        if nuevos and self._tenidos_iniciado:
            self.fallos_seguidos.clear()          # novedad: se vuelve a probar lo bloqueado
        self._tenidos |= {k for k, v in antes_obj.items() if v >= 1} | nuevos
        self._tenidos_iniciado = True
        clave = (verbo, objetivo)
        r = self.requisitos.get(clave)
        if exito and delta:
            nuevo = r is None
            if r is None:
                r = self.requisitos[clave] = RequisitoAccion(verbo, objetivo, {}, set(), fuente="experiencia")
            r.exitos += 1
            r.efecto = dict(delta)
            for k, d in delta.items():
                if d < 0 and not nuevo:
                    r.requiere_inventario[k] = -d   # lo consumido es la cantidad exacta (corrige estimaciones por fallos)
            if cerca_despues is not None:
                r.aparece |= set(cerca_despues) - set(cerca)
            for c in r.requiere_cerca:
                if c in distancias:
                    r.cerca_ok.setdefault(c, set()).add(distancias[c])
                    r.cerca_fallida.get(c, set()).discard(distancias[c])
            if delante:
                r.requiere_delante.add(delante)
                r.delante_fallido.discard(delante)
            fallidos = [f for f in self.intentos.pop(clave, []) if r.cumple_inventario(f)]   # sin causa conocida
            if fallidos:                          # 5.2 a: inducción por diferencia
                for k, v in antes.items():
                    if v >= 1 and k not in r.requiere_inventario and all(f.get(k, 0.0) < 1 for f in fallidos):
                        r.requiere_inventario[k] = 1
            self.fallos_seguidos.pop(clave, None)
            r.ajustar_confianza(self.PASO_CONFIANZA_REQUISITO)
            return
        lista = self.intentos.setdefault(clave, [])
        lista.append({k: v for k, v in antes.items() if v})
        del lista[: max(0, len(lista) - self.MAX_INTENTOS)]
        self.fallos_seguidos[clave] = self.fallos_seguidos.get(clave, 0) + 1
        if r is not None and r.cumple_inventario(antes):
            contiguo = espacio.magnitud(espacio.junto)
            for c in r.requiere_cerca:
                dc = distancias.get(c)
                if dc is not None and espacio.magnitud(dc) > contiguo and dc not in r.cerca_ok.get(c, set()):
                    r.cerca_fallida.setdefault(c, set()).add(dc)
        if r is not None and delante and delante not in r.requiere_delante:
            r.delante_fallido.add(delante)
        if r is not None and r.cumple(antes, cerca):
            r.fallos += 1
            for k, n in list(r.requiere_inventario.items()):
                if r.efecto.get(k, 0) < 0:
                    continue
                if n is None or n <= antes.get(k, 0.0):
                    r.requiere_inventario[k] = int(antes.get(k, 0.0)) + 1
            r.ajustar_confianza(-self.PASO_CONFIANZA_REQUISITO)

    def registrar_meta(
        self,
        verbo: Verbo,
        objetivo: str,
        exito: bool,
        inv_antes: Optional[Dict[str, float]],
        inv_despues: Optional[Dict[str, float]],
        delta_vitales: Dict[str, float],
    ) -> bool:
        """Paso 5 (5.0): una meta se consigue con el primer ``Efecto`` con éxito de su verbo sobre su objetivo
        que además cambia algo: el inventario de objetos o alguna constante vital que sube (beber, comer,
        descansar). Devuelve si se ha conseguido ahora."""
        meta = self.metas.get((verbo, objetivo))
        if meta is None or meta.conseguida or not exito:
            return False
        cambio_inv = inv_antes is not None and inv_despues is not None and self.objetos(inv_antes) != self.objetos(inv_despues)
        if cambio_inv or any(float(v) > 0.0 for v in delta_vitales.values()):
            meta.conseguida = True
            return True
        return False

def situacion_inventario(ctx: Contexto) -> Optional[Situacion]:
    """Inventario percibido, clases al alcance (no lugares) y clase de lo que hay delante (``cuerpo["delante"]``,
    si el mundo lo da), si el mundo da inventario. Para los requisitos y las metas. Lee piezas (D4): la
    ``Propiocepcion`` «yo» y las ``Exterocepcion``."""
    yo = ctx.onda.ev("Propiocepcion").get("yo")
    if yo is None or yo.carga.get("inventario") is None:
        return None
    piezas = list(ctx.onda.ev("Exterocepcion").values())
    cerca = {e.clase for e in piezas if e.rasgo("lugar") < 0.5 and e.rasgo("proximidad") >= 0.9}
    delante = (yo.carga.get("cuerpo") or {}).get("delante")
    return (dict(yo.carga["inventario"]), cerca,
            (str(delante.get("clase")) if isinstance(delante, dict) and delante.get("clase") else None),
            distancias(ctx.espacio, str(yo.carga.get("ubicacion") or ""), piezas))


def distancias(espacio: Cuerpo, ubicacion: str, piezas: List[Pieza]) -> Dict[str, Hashable]:
    """Posición relativa (``espacio.relacion``) de la instancia más cercana de cada clase, hasta ``espacio.radio_prueba``
    (entre dos, la primera por ``espacio.orden``). Con posiciones (la del individuo, ``espacio.posicion``, y
    ``datos["pos"]``) la da el cuerpo; sin ellas, lo que está al alcance (proximidad ≥ 0,9) cuenta como ``espacio.junto``."""
    aqui = espacio.posicion(ubicacion)
    dist: Dict[str, Hashable] = {}
    for e in piezas:
        if e.rasgo("lugar") >= 0.5:
            continue
        pos = (e.carga.get("datos") or {}).get("pos")
        d: Optional[Hashable] = None
        if aqui is not None and isinstance(pos, (list, tuple)) and len(pos) == 2:
            d = espacio.relacion(aqui, (int(pos[0]), int(pos[1])))
        elif e.rasgo("proximidad") >= 0.9:
            d = espacio.junto
        if d is None:
            continue
        previo = dist.get(e.clase)
        if espacio.magnitud(d) <= espacio.radio_prueba and (previo is None or espacio.orden(d) < espacio.orden(previo)):
            dist[e.clase] = d
    return dist


class Requisito(Componente):
    """Componente general de S3 · Interpretar (D7): aprende requisitos, intentos y metas del efecto de cada acción."""

    tipo = "Requisito"
    aprende_con_efecto = True   # D6: aprende en ``Organismo._aprender``, donde se aprendían los requisitos y las metas

    def __init__(self, nombre: Optional[str] = None) -> None:
        super().__init__(nombre)
        self._antes: Optional[Situacion] = None   # inventario, cerca, delante y desplazamientos antes de actuar

    def activo(self, onda: Onda) -> bool:
        return False   # sin barridos: no cobra ni cuenta operaciones en el latido

    def seccion_memoria(self, perfil: Perfil) -> Optional[Tuple[str, Any]]:
        """D7: es el dueño de la sección «requisitos»."""
        return "requisitos", Requisitos()

    def antes_de_actuar(self, ctx: Contexto) -> None:
        self._antes = situacion_inventario(ctx)   # paso 2: lo que había antes de actuar (requisitos)

    def aprender(self, ctx: Contexto) -> None:
        """Tras una acción, con experiencia (lo llama el Core): contrasta el inventario de antes y de después para sus
        requisitos (USAR y COGER) y, si el manual declara metas, si la acción consiguió alguna (paso 5)."""
        previa = ctx.onda.ei("Accion").get("Accion")
        if previa is None:
            return
        c = previa.carga
        req = cast(Requisitos, ctx.memoria.seccion_propia("requisitos", type(self).__name__))
        ahora_inv = situacion_inventario(ctx)
        objetivo = str(c.get("clase") or c.get("objetivo") or "")
        antes = self._antes
        if c["verbo"] in (Verbo.USAR, Verbo.COGER) and antes is not None and ahora_inv is not None:
            req.aprender_requisito(c["verbo"], objetivo, antes[0], ahora_inv[0], antes[1], bool(c.get("exito")),
                                   cerca_despues=ahora_inv[1], delante=antes[2], distancias=antes[3], espacio=ctx.espacio)
        if req.metas:   # paso 5: metas del manual (solo si el mundo las declara)
            req.registrar_meta(c["verbo"], objetivo, bool(c.get("exito")), antes[0] if antes is not None else None,
                               ahora_inv[0] if ahora_inv is not None else None, dict(c.get("delta", {})))
