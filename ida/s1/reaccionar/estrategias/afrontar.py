"""Estrategia Afrontar."""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple, cast

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Definicion, Propuesta
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Verbo
from ida.s1.comun import (
    SEGURIDAD,
    _lugares_permitidos,
    _objetos_llevados,
    _peligro,
    _posicion,
    _yo,
    objetos_peligrosos,
)
from ida.s1.reaccionar.estrategias.defenderse import Defenderse
from ida.s1.reaccionar.estrategias.huir import Huir
from ida.s1.sentir.amenaza import Peligros
from ida.s3.interpretar.requisito import Requisitos


class Afrontar(Definicion):
    """Seguridad (paso 6b): luchar o huir por evaluación, con lo aprendido en 6a
    (``ida.s1.sentir.amenaza``). Para cada amenaza percibida (un Objeto con peligro y posición, de una clase cuyo derribo se ha
    observado o que el manual declara meta de ATACAR):

    - golpes para derribarla con lo que se lleva (aprendido; previo pesimista sin datos), pasos hasta el contacto
      (distancia − 1) y exposición = golpes + pasos;
    - daño recibido = daño por golpe × exposición × tasa de daño por latido de exposición (aprendidos);
    - margen = salud − daño recibido; beneficio = el peligro que elimina + 1 si derribarla es una meta pendiente
      del manual (ATACAR sobre su clase).

    Lucha (fase ``luchar``) contra la de mayor beneficio con margen > ``Perfil.escala.reserva`` (D15) y beneficio > 0: ATACAR si está en
    contacto; si no y su alcance es mayor que el contacto (un emisor: huir no lo reduce y acercarse acorta la
    exposición), MOVER al lugar que más acerca; si daña solo por contacto, no se huye: se espera (ESPERAR) cuando le
    falta un paso para el contacto y, más lejos, no se propone nada.
    Paso 6c: si ninguna lucha es favorable pero lo sería con un objeto que reduce los golpes
    (aprendido por contingencia, ``Peligros.reductores``, y que se distingue de los demás en los derribos: si dos se
    llevaron siempre juntos no se pide ninguno), fase ``armarse``: pide ese objeto al planificador con la
    intensidad de Seguridad (``Definicion.pedir``) y, mientras tanto, hace lo que haría ``Huir`` (o ``Defenderse`` sin
    salida). Solo con el peligro calculado por la base (``ctx.extra["peligro_aprendido"]``).

    Compite con ``Huir`` por el impulso de Seguridad: la elige ``Estrategia`` por su prioridad cuando es elegible, es
    decir, cuando la evaluación es favorable."""

    nombre = "afrontar"
    impulsos = (SEGURIDAD,)
    prioridad = 50
    opcional = True     # D3, D15: solo la monta el mundo que la registra
    LUCHAR, ARMARSE = "luchar", "armarse"

    @staticmethod
    def _valorar(ctx: Contexto, o: Pieza, aqui: Tuple[int, int], salud: float, llevados: FrozenSet[str],
                 reductores: Dict[str, float]) -> Optional[Dict[str, Any]]:
        pos = _posicion(ctx, o.id)
        if pos is None or len(pos) != 2:
            return None
        mem = ctx.memoria
        if not mem.tiene_seccion("peligros"):
            return None
        pel = cast(Peligros, mem.seccion("peligros"))
        req = cast(Requisitos, mem.seccion("requisitos")) if mem.tiene_seccion("requisitos") else None
        d = int(abs(pos[0] - aqui[0]) + abs(pos[1] - aqui[1]))
        golpes, n_golpes = pel.golpes(o.clase, llevados, reductores)
        tasa, n_tasa = pel.tasa(o.clase)
        exposicion = golpes + max(0, d - 1)
        recibido = pel.dano_por_golpe(o.clase, mem.peligrosa) * exposicion * tasa
        meta = req.metas.get((Verbo.ATACAR, o.clase)) if req is not None else None
        beneficio = o.rasgo("peligro") + (1.0 if meta is not None and not meta.conseguida else 0.0)
        return {"pieza": o, "d": d, "golpes": golpes, "n_golpes": n_golpes, "tasa": tasa, "n_tasa": n_tasa,
                "margen": salud - recibido, "beneficio": beneficio, "alcance": pel.alcance(o.clase, mem.peligrosa)}

    def evaluar(self, ctx: Contexto) -> Optional[Dict[str, Any]]:
        """La decisión del latido (se calcula una vez): ``{"fase", "valoracion", "objeto"}`` o None."""
        if "afrontar" in ctx.extra:
            return cast(Optional[Dict[str, Any]], ctx.extra["afrontar"])
        res: Optional[Dict[str, Any]] = None
        aqui = _yo(ctx)
        reserva = ctx.perfil.escala.reserva
        if ctx.extra.get("peligro_aprendido") and aqui is not None and Verbo.ATACAR in ctx.verbos and ctx.memoria.tiene_seccion("peligros"):
            salud = float(ctx.soma.vitalidad)
            llevados = _objetos_llevados(ctx)
            pel = cast(Peligros, ctx.memoria.seccion("peligros"))
            reductores = pel.reductores()
            valoradas = [v for o in objetos_peligrosos(ctx) if (v := self._valorar(ctx, o, aqui, salud, llevados, reductores)) is not None]
            favorables = [v for v in valoradas if v["margen"] > reserva and v["beneficio"] > 0.0]
            if favorables:
                v = max(favorables, key=lambda v: (v["beneficio"], -v["d"], v["pieza"].id))
                res = {"fase": self.LUCHAR, "valoracion": v, "objeto": None}
            elif valoradas:
                principal = max(valoradas, key=lambda v: (v["pieza"].rasgo("peligro"), v["pieza"].id))
                elegido: Optional[Tuple[str, Dict[str, Any]]] = None
                for x in sorted((set(reductores) - llevados) & pel.distinguibles()):
                    w = self._valorar(ctx, principal["pieza"], aqui, salud, llevados | {x}, reductores)
                    if w is not None and w["margen"] > reserva and (elegido is None or w["golpes"] < elegido[1]["golpes"]):
                        elegido = (x, w)
                if elegido is not None:
                    res = {"fase": self.ARMARSE, "valoracion": principal, "objeto": elegido[0], "con_objeto": elegido[1]}
        ctx.extra["afrontar"] = res
        return res

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        return intensidad > 0.0 and self.evaluar(ctx) is not None

    def paso(self, ctx: Contexto, estrategia: Pieza) -> Any:
        e = self.evaluar(ctx)
        return e["fase"] if e is not None else estrategia.carga.get("paso", 0)

    @staticmethod
    def _confianza(v: Dict[str, Any]) -> float:
        n = min(v["n_golpes"] / (v["n_golpes"] + 2.0), v["n_tasa"] / (v["n_tasa"] + 2.0))
        return acotar(0.5 + 0.45 * n)

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        e = self.evaluar(ctx)
        if e is None:
            return None
        v = e["valoracion"]
        o = v["pieza"]
        intensidad = _peligro(ctx)
        urgencia = acotar(0.75 + 0.25 * intensidad)      # la misma escala que Huir y Defenderse
        cifras = f"golpes {v['golpes']:.1f}, margen {v['margen']:.0f}, beneficio {v['beneficio']:.2f}"
        if e["fase"] == self.ARMARSE:
            for alternativa in (Huir(), Defenderse()):
                if alternativa.elegible(ctx, SEGURIDAD, intensidad):
                    p = alternativa.actuar(ctx, estrategia)
                    if p is not None:
                        p.motivo = f"afrontar (armarse: {e['objeto']}): {p.motivo}"
                        return p
            return None
        if v["d"] <= 1:
            return Propuesta(Verbo.ATACAR, o.id, urgencia, self._confianza(v), f"afrontar: atacar {o.clase} ({cifras})", clase=o.clase)
        if v["alcance"] <= 1:
            if v["d"] == 2 and Verbo.ESPERAR in ctx.verbos:     # le falta un paso para el contacto: esperarla, no irse
                return Propuesta(Verbo.ESPERAR, "", urgencia, self._confianza(v), f"afrontar: esperar a {o.clase} ({cifras})")
            return None
        meta = _posicion(ctx, o.id)
        aqui = _yo(ctx)
        if meta is None or aqui is None:
            return None
        ahora = abs(meta[0] - aqui[0]) + abs(meta[1] - aqui[1])
        pasos = [(abs(meta[0] - pos[0]) + abs(meta[1] - pos[1]), lugar.rasgo("peligro"), lugar.id, lugar)
                 for lugar in _lugares_permitidos(ctx) if (pos := _posicion(ctx, lugar.id)) is not None and len(pos) == 2]
        cerca = [x for x in pasos if x[0] < ahora]
        if not cerca:
            return None
        lugar = min(cerca, key=lambda x: x[:3])[3]
        return Propuesta(Verbo.MOVER, lugar.id, urgencia, self._confianza(v),
                         f"afrontar: acercarse a {o.clase} (alcance {v['alcance']}, {cifras})", clase=lugar.clase)

    def pedir(self, ctx: Contexto, estrategia: Pieza) -> List[Dict[str, Any]]:
        e = self.evaluar(ctx)
        if e is None or e["fase"] != self.ARMARSE:
            return []
        return [{"objeto": e["objeto"], "cantidad": 1.0, "urgencia": _peligro(ctx),
                 "motivo": f"afrontar: {e['objeto']} para {e['valoracion']['pieza'].clase}"}]
