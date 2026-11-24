"""Apetencia: aliestesia (Cabanac, 1971; paso 0b). Dueño de la sección «satisface» de la Memoria."""

from typing import Any, Dict, Optional, Tuple, cast

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.memoria import Memoria, Satisface, Seccion
from ida.nucleo.mundo import Perfil
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Relacion, Verbo
from ida.sistemas_comun import objetos

SATISFACE_MIN = 0.3   # paso 0b: a partir de aquí algo satisface una necesidad (como ``nutritivo`` ≥ 0,3 hoy)


def intensidades(ctx: Contexto) -> Dict[str, float]:
    """Déficit de cada necesidad que declara el mundo (sin Seguridad), desde la interocepción."""
    valores = {n: float(p.carga["valor"]) for n, p in ctx.onda.ev("Interocepcion").items()}
    d: Dict[str, float] = {}
    for necesidad in ctx.perfil.necesidades:
        v = necesidad.deficit(valores)
        if v is not None:
            d[necesidad.nombre] = v
    return d


def satisface_de(ctx: Contexto, o: Pieza) -> Dict[str, float]:
    """Paso 0b: cuánto satisface ``o`` cada necesidad declarada. Lo que sabe la memoria de su clase (manual y
    contingencia aprendida; lo que no consta vale 0). El rasgo perceptivo con el que el mundo declara que se
    satisface cada necesidad (``Necesidad.rasgo``) es el previo: si la memoria no sabe nada de la clase, es
    todo lo que hay, como hasta ahora."""
    previos = {n.nombre: (o.rasgo(n.rasgo) if n.rasgo else 0.0) for n in ctx.perfil.necesidades}
    if ctx.memoria.tiene_seccion("satisface"):
        conocida = cast(Aliestesia, ctx.memoria.seccion("satisface")).satisfaccion(o.clase, previos)
    else:
        conocida = None
    if conocida is not None:
        return {n.nombre: conocida.get(n.nombre, 0.0) for n in ctx.perfil.necesidades}
    return previos


class Aliestesia(Seccion):
    """Sección «satisface» de la Memoria (D7), cuyo dueño es ``Apetencia``: qué necesidad satisface comer cada clase
    (paso 0b), del manual y de la experiencia, y la línea base de cada necesidad (lo que sube sin comer)."""

    orden_legado = 2     # D7: su parte va tras los requisitos y antes de los peligros (la forma de antes)

    def __init__(self) -> None:
        self.satisface: Dict[Tuple[str, str], Satisface] = {}
        self.linea_base: Dict[str, float] = {}      # necesidad -> P(sube | sin comer), media móvil
        self.n_base: Dict[str, int] = {}            # latidos sin comer contados por necesidad

    def aplicar_manual(self, manual: Dict[str, Any]) -> None:
        """Las proposiciones ``NUTRITIVO`` del manual con ``necesidad``: qué necesidad satisface la clase (autoridad)."""
        if not self.activa or not manual:
            return
        for h in manual.get("hechos", []):
            if h.get("tipo") == "proposicion" and h.get("necesidad") and Relacion[h["relacion"]] == Relacion.NUTRITIVO:
                s = self.satisface.setdefault((str(h["sujeto"]), str(h["necesidad"])), Satisface(str(h["sujeto"]), str(h["necesidad"])))
                afirma = str(h.get("veredicto", "afirma")) == "afirma"
                s.c_aut, s.w_aut = (Memoria.CONFIANZA_MANUAL if afirma else 1.0 - Memoria.CONFIANZA_MANUAL), Memoria.PESO_MANUAL

    def legado(self, ahora: int) -> Dict[str, Any]:
        """Solo lo vivido (el manual se vuelve a leer) y, con ello, la línea base."""
        satisface = [{"clase": s.clase, "necesidad": s.necesidad, "n": s.n, "sube": s.sube, "esperado": round(s.esperado, 4)}
                     for s in self.satisface.values() if s.n >= 2]
        if not satisface:
            return {}
        return {"satisface": satisface, "linea_base": {k: round(v, 4) for k, v in self.linea_base.items()}}

    def heredar(self, legado: Dict[str, Any], tasa: float = 1.0) -> int:
        """Como los registros, con la mitad de la evidencia; la línea base, hasta que la vida tenga la suya."""
        if not self.activa:
            return 0
        n = 0
        for d in legado.get("satisface", []):
            s = self.satisface.setdefault((str(d["clase"]), str(d["necesidad"])), Satisface(str(d["clase"]), str(d["necesidad"])))
            veces = max(1, int(d["n"]) // 2)
            s.n += veces
            s.sube += round(veces * int(d["sube"]) / max(1, int(d["n"])))
            s.esperado += veces * float(d.get("esperado", 0.0)) / max(1, int(d["n"]))
            n += 1
        for necesidad, base in legado.get("linea_base", {}).items():
            if necesidad not in self.linea_base:
                self.linea_base[necesidad] = float(base)
        return n

    def satisfaccion(self, clase: str, previos: Optional[Dict[str, float]] = None) -> Optional[Dict[str, float]]:
        """Cuánto satisface comer ``clase`` cada necesidad, o ``None`` si no se sabe nada de esa clase (ni del manual
        ni de la experiencia). ``previos``: lo que sugiere la percepción para cada necesidad (el previo de una clase
        de la que el manual no habla). Las necesidades que no aparecen valen 0."""
        if not self.activa:
            return None
        registros = {nec: s for (c, nec), s in self.satisface.items() if c == clase}
        if not registros:
            return None
        manual = any(s.c_aut is not None for s in registros.values())
        resultado: Dict[str, float] = {}
        for nec in sorted(set(registros) | set(previos or {})):
            s = registros.get(nec) or Satisface(clase, nec)
            if s.c_aut is not None:
                previo, peso = s.c_aut, s.w_aut
            elif manual:
                previo, peso = 0.0, Satisface.PREVIO
            else:
                previo, peso = (previos or {}).get(nec, 0.0), Satisface.PREVIO
            resultado[nec] = s.estimacion(previo, peso)
        return resultado

    def estimacion_satisface(self, clase: str, necesidad: str, previos: Optional[Dict[str, float]] = None) -> float:
        return (self.satisfaccion(clase, previos) or {}).get(necesidad, 0.0)

    def aprender_satisface(self, clase: str, subidas: Dict[str, bool]) -> None:
        """Tras comer algo de ``clase`` con éxito: para cada necesidad, si subió alguna de sus constantes vitales."""
        if not self.activa or not clase:
            return
        for necesidad, subio in subidas.items():
            s = self.satisface.setdefault((clase, necesidad), Satisface(clase, necesidad))
            s.n += 1
            s.sube += int(bool(subio))
            s.esperado += self.linea_base.get(necesidad, 0.0)

    VENTANA_BASE = 10   # latidos de la media móvil de la línea base (media exacta mientras haya menos): lo reciente

    def actualizar_linea_base(self, subidas: Dict[str, bool]) -> None:
        """En un latido sin comer: para cada necesidad, si subió alguna de sus constantes (p. ej. sola, al amanecer)."""
        if not self.activa:
            return
        for necesidad, subio in subidas.items():
            k = self.n_base.get(necesidad, 0) + 1
            self.n_base[necesidad] = k
            previa = self.linea_base.get(necesidad, 0.0)
            self.linea_base[necesidad] = previa + (float(bool(subio)) - previa) / min(k, self.VENTANA_BASE)


class Apetencia(Componente):
    """Aliestesia (Cabanac, 1971; paso 0b; opcional, la registra el mundo en el que un rasgo satisface varias necesidades): el valor de algo
    comestible depende del estado interno. Para cada Objeto que parece comestible (el rasgo de alguna
    necesidad ≥ ``SATISFACE_MIN``, el mismo filtro que sin aliestesia) y satisface alguna necesidad,
    deseo = Σ_n intensidad(n) · satisface(clase, n). Solo existe donde se registra (D15)."""

    tipo = "Apetencia"
    entradas = ("Objeto", "Interocepcion")
    opcional = True     # D3, D15: solo la monta el mundo que la registra
    aprende_con_efecto = True   # D6: aprende en ``Organismo._aprender``, donde se aprendía la aliestesia

    def seccion_memoria(self, perfil: Perfil) -> Optional[Tuple[str, Any]]:
        """D7: es el dueño de la sección «satisface»."""
        return "satisface", Aliestesia()

    def aprender(self, ctx: Contexto) -> None:
        """Paso 0b (aliestesia), aprendizaje por contingencia: qué necesidades subieron respecto al latido anterior
        (``delta`` de la interocepción; cada ``Necesidad`` declara sus constantes). Tras comer algo con éxito, cuenta
        para esa clase; en cualquier otro latido, para la línea base de cada necesidad (lo que sube sin comer). El Core
        lo llama tras una acción, con experiencia."""
        previa = ctx.onda.ei("Accion").get("Accion")
        if previa is None:
            return
        c = previa.carga
        aliestesia = cast(Aliestesia, ctx.memoria.seccion_propia("satisface", type(self).__name__))
        delta = {k: float(p.carga.get("delta", 0.0)) for k, p in ctx.onda.ev("Interocepcion").items()}
        subidas = {n.nombre: any(delta.get(k, 0.0) > 0.0 for k in n.constantes) for n in ctx.perfil.necesidades}
        if c["verbo"] == Verbo.COMER and bool(c.get("exito")) and c.get("clase"):
            aliestesia.aprender_satisface(str(c["clase"]), subidas)
        else:
            aliestesia.actualizar_linea_base(subidas)

    def reactiva(self, ctx: Contexto) -> None:
        inten = intensidades(ctx)
        rasgos = {n.rasgo for n in ctx.perfil.necesidades if n.rasgo}
        for o in objetos(ctx):
            if not any(o.rasgo(r) >= SATISFACE_MIN for r in rasgos):
                continue        # no parece comestible (p. ej. aún no está maduro): la memoria dice a qué sirve, no si lo es ahora
            sat = satisface_de(ctx, o)
            if not any(v >= SATISFACE_MIN for v in sat.values()):
                continue
            por_necesidad = {n: inten.get(n, 0.0) * s for n, s in sat.items()}
            deseo = acotar(sum(por_necesidad.values()))
            self.percibir(ctx, self.pieza(ctx, o.id, arousal=deseo, carga={
                "clase": o.clase, "deseo": round(deseo, 4), "satisface": {n: round(s, 4) for n, s in sat.items() if s > 0.0},
                "necesidad": max(por_necesidad, key=lambda n: (por_necesidad[n], n)) if por_necesidad else None},
                entradas=[o.id]))
