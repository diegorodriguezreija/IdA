"""Estrategia RecordarComida para S2."""

from typing import Any, Dict, List, Optional, Tuple

from ida.nucleo.arquitectura import Contexto
from ida.nucleo.estrategia import Plan, Propuesta, estado_plan, paso_actual
from ida.nucleo.pieza import Pieza, acotar
from ida.nucleo.vocabulario import Relacion, Verbo
from ida.s2.comun import _peligro
from ida.sistemas_comun import lugares, objetos


class RecordarComida(Plan):
    """Necesidades que satisface lo nutritivo (antes ``Orientacion``): con hambre (≥ 0,35), sin peligro
    (< 0,4) y sin comida a la vista, ir por la ruta del hipocampo hacia donde se vio una clase que se
    cree nutritiva (confianza ≥ 0,55) y no se sabe peligrosa. Si llega y no está, la olvida.

    Con el interruptor de plan (bloque F, F2) es un ``Plan``: al activarse elige destino (confianza y,
    a igualdad, fuerza del nodo en el grafo semántico) y fija la ruta completa del mapa más un paso
    final, encontrar la clase. Sorpresa (el paso falla): estar fuera de la ruta, no ver la puerta
    esperada o llegar y no encontrar la comida (entonces la olvida)."""

    nombre = "recordar_comida"
    rasgo = "nutritivo"
    prioridad = 10

    @staticmethod
    def _plan(ctx: Contexto) -> Optional[Tuple[Pieza, float, str]]:
        if not ctx.con_experiencia or not ctx.memoria.activa:
            return None
        hambre = ctx.soma.hambre()
        if _peligro(ctx) >= 0.4 or hambre < 0.35 or any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):
            return None
        aqui = ctx.ubicacion()
        if not aqui:
            return None
        if ctx.perfil.mecanismos.evocacion:   # bloque E, E5: lo recuperado (piezas Recuerdo), no la memoria
            candidatos = sorted(((r.carga["clase"], r.confianza, r.carga["donde"]) for r in ctx.onda.ev("Recuerdo").values()
                                 if r.carga.get("relacion") == Relacion.NUTRITIVO), key=lambda item: -item[1])
        else:
            candidatos = sorted(
                ((clase, prop.confianza, ctx.memoria.donde_esta(clase)) for (clase, rel), prop in ctx.memoria.saber.items()
                 if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido)),
                key=lambda item: -item[1],
            )
        for clase, confianza, destino in candidatos:
            if destino == aqui and not any(o.clase == clase for o in objetos(ctx)):
                ctx.memoria.olvidar_donde(clase, autor="RecordarComida")
                continue
            if destino and destino != aqui:
                salto = ctx.memoria.ruta(aqui, destino)
                puerta = next((lugar for lugar in lugares(ctx) if lugar.id == salto and lugar.rasgo("peligro") < 0.6), None) if salto else None
                if puerta is not None:
                    return puerta, acotar(0.25 + 0.45 * hambre * confianza), clase
        return None

    @staticmethod
    def _candidatos_plan(ctx: Contexto) -> List[Tuple[str, float, Optional[str]]]:
        """Con plan: los mismos candidatos, con la fuerza del nodo del grafo como desempate."""
        if not ctx.con_experiencia or not ctx.memoria.activa:
            return []
        hambre = ctx.soma.hambre()
        if _peligro(ctx) >= 0.4 or hambre < 0.35 or any(o.rasgo("nutritivo") >= 0.3 for o in objetos(ctx)):
            return []
        if ctx.perfil.mecanismos.evocacion:
            crudos = [(r.carga["clase"], r.confianza, r.carga["donde"]) for r in ctx.onda.ev("Recuerdo").values()
                      if r.carga.get("relacion") == Relacion.NUTRITIVO]
        else:
            crudos = [(clase, prop.confianza, ctx.memoria.donde_esta(clase)) for (clase, rel), prop in ctx.memoria.saber.items()
                      if rel == Relacion.NUTRITIVO and prop.confianza >= 0.55 and not ctx.memoria.demostrada(clase, Relacion.PELIGROSO, ctx.latido)]
        grafo = ctx.memoria.grafo
        return sorted(crudos, key=lambda c: (-c[1], -float(grafo.get(f"Objeto:{c[0]}", {}).get("fuerza", 0.0)), c[0]))

    def construir(self, ctx: Contexto, estrategia: Pieza) -> Optional[List[Dict[str, Any]]]:
        aqui = ctx.ubicacion()
        if not aqui:
            return None
        for clase, confianza, destino in self._candidatos_plan(ctx):
            if destino and destino != aqui:
                camino = ctx.memoria.camino(aqui, destino)
                if camino:
                    return [{"meta": n} for n in camino] + [{"meta": "encontrar", "clase": clase, "en": destino, "confianza": confianza}]
        return None

    def cumplido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        if paso["meta"] == "encontrar":
            return any(o.clase == paso["clase"] for o in objetos(ctx))
        return ctx.ubicacion() == paso["meta"]

    def fallido(self, ctx: Contexto, paso: Dict[str, Any], estado: Dict[str, Any]) -> bool:
        aqui = ctx.ubicacion()
        if paso["meta"] == "encontrar":
            if aqui == paso["en"]:
                ctx.memoria.olvidar_donde(paso["clase"], autor=type(self).__name__)    # llegó y no está
            return True                                     # llegó y no está, o se alejó del destino
        i = int(estado["i"])
        previo = estado["pasos"][i - 1]["meta"] if i > 0 else None
        if aqui == previo:   # donde esperaba estar: ¿está la puerta esperada?
            return not any(lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6 for lugar in lugares(ctx))
        return True          # fuera de la ruta

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        if ctx.perfil.mecanismos.plan:
            aqui = ctx.ubicacion()
            return bool(aqui) and any(d and d != aqui for _, _, d in self._candidatos_plan(ctx))
        return self._plan(ctx) is not None

    def actuar(self, ctx: Contexto, estrategia: Pieza) -> Optional[Propuesta]:
        if ctx.perfil.mecanismos.plan:
            paso = paso_actual(estrategia)
            if paso is None or paso["meta"] == "encontrar":
                return None
            final = estado_plan(estrategia)["pasos"][-1]   # type: ignore[index]
            puerta = next((lugar for lugar in lugares(ctx) if lugar.id == paso["meta"] and lugar.rasgo("peligro") < 0.6), None)
            if puerta is None:
                return None
            ar = acotar(0.25 + 0.45 * ctx.soma.hambre() * float(final.get("confianza", 0.55)))
            return Propuesta(Verbo.MOVER, puerta.id, ar, 0.65, f"plan: recordar {final.get('clase', '')}", clase=puerta.clase)
        plan = self._plan(ctx)
        if plan is None:
            return None
        puerta, ar, clase = plan
        return Propuesta(Verbo.MOVER, puerta.id, ar, 0.65, f"orientación: recordar {clase}", clase=puerta.clase)
