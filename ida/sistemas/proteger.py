"""S1 · «Proteger X» con X = uno mismo: el refugio general (fase de generalización, paso 3).

Diseño: ``docs/ENCARGO_PASO3_PROTEGER.md``. Proteger es una estrategia general del impulso ``cobijo``;
la interpretación del espacio (recintos, cavar, cerrar accesos) la aporta el mundo (Crafter, D16) a través
de la pieza de afordancia de protección.
"""

from typing import Any, Dict, List, Optional, Tuple

from ida.core.arquitectura import Contexto
from ida.core.estrategia import ConPropuestas
from ida.core.pieza import Pieza, acotar
from ida.core.vocabulario import Verbo

COBIJO = "cobijo"
TIPO_RECINTO = "Recinto"


def recinto(ctx: Contexto) -> Optional[Pieza]:
    """Pieza de afordancia de protección producida por el componente de interpretar del mundo."""
    return ctx.onda.ef(TIPO_RECINTO).get("recinto")


def riesgo_exterior(ctx: Contexto) -> float:
    """El riesgo de salir: el peligro percibido si llega al umbral de miedo (el mismo que hace elegible huir); por debajo,
    0, porque fuera no hay nada de lo que haya que huir."""
    a = ctx.onda.ev("Supervivencia").get("alarma")
    peligro = float(a.carga["peligro"]) if a is not None else 0.0
    return peligro if peligro >= ctx.arquetipo.umbral_miedo else 0.0


def _proponer_abrir(estrategia: ConPropuestas, ctx: Contexto, c: Dict[str, Any], origen: str, necesidad: str, deficit: float,
                    cobijo: float) -> None:
    """Abrir el recinto: la primera pared que se puede cavar (``Recinto``, ``abrir``), con arousal = déficit de la necesidad que
    saca y confianza = tasa estimada de cavarla."""
    pared = c["abrir"][0]
    confianza = ctx.memoria.tasa_estimada(Verbo.COGER, pared["clase"]) if pared["verbo"] == Verbo.COGER else 1.0
    que = f"abrir {pared['clase']}" if pared["verbo"] == Verbo.COGER else "ir junto a la pared para abrir"
    estrategia.proponer(ctx, pared["verbo"], pared["objetivo"], deficit, confianza,
                        f"{origen}: {que} ({necesidad} {deficit:.2f} > cobijo {cobijo:.2f})", clase=pared["clase"])


class Proteger(ConPropuestas):
    """Estrategia general del impulso ``cobijo``: protegerse en un recinto.

    - **Fuera:** si el cobijo pesa al menos tanto como el déficit de las necesidades que se satisfacen fuera, propone la
      primera acción del plan del sitio que interpreta ``Recinto`` (ir, cavar, girarse, cerrar). Arousal = intensidad del
      cobijo (anticipada por la alostasis); confianza = confianza del sitio × esa intensidad: la confianza de que protegerse
      ahora sirve a la necesidad. Sin sitio, o si otra necesidad de fuera pesa más, no propone (deciden otras estrategias).
      Aquí solo cuenta el déficit actual de las demás necesidades, no lo que se prevea de ellas.
    - **Sin sitio completable:** pide al planificador lo que falta (``pedir``, metas instrumentales) y no propone; ante
      un peligro por encima del umbral de miedo, cede (``_cede``).
    - **Dentro:** si el cobijo (o el riesgo de fuera, ``riesgo_exterior``) pesa al menos tanto como el déficit de cualquier
      necesidad que se satisface fuera (las que declaran un ``rasgo``), quedarse: DORMIR (o ESPERAR si el mundo no deja
      dormir). Si una de ellas pesa más, abrir: COGER sobre una pared que se pueda cavar (primero la que cerró uno mismo,
      que además devuelve el material). Cuando el cobijo ya no pide nada (de día), Proteger se cierra y la salida la
      propone ``SalirDelRecinto`` desde la propia necesidad.
    """

    nombre = "proteger"
    impulsos = (COBIJO,)
    prioridad = 10
    opcional = True          # D3, D15: solo la monta el mundo que la registra
    agotable = False         # protegerse no baja el déficit del cobijo (la noche sigue): no se agota por falta de progreso

    def elegible(self, ctx: Contexto, impulso: str, intensidad: float) -> bool:
        r = recinto(ctx)
        return r is not None and (bool(r.carga["dentro"]) or r.carga["accion"] is not None or bool(r.carga.get("requiere")))

    @staticmethod
    def _cede(ctx: Contexto) -> bool:
        """Con un peligro percibido por encima del umbral de miedo (el mismo que hace elegible huir), un sitio que aún no se
        puede completar no se persigue: conseguir lo que falta (material, herramientas) junto a un hostil es exponerse, y
        se deja que respondan las estrategias de Seguridad. Un sitio completable sí se sigue (llegar a él también aleja)."""
        a = ctx.onda.ev("Supervivencia").get("alarma")
        return a is not None and float(a.carga["peligro"]) >= ctx.arquetipo.umbral_miedo

    def pedir(self, ctx: Contexto, estrategia: Pieza) -> List[Dict[str, Any]]:
        """Metas instrumentales: si el mejor sitio necesita algo que no se tiene (``requiere`` del recinto), se pide al
        planificador con urgencia = intensidad anticipada del cobijo. No se pide si otra necesidad de fuera pesa más, ni si
        hay que ceder ante un peligro (``_cede``)."""
        r = recinto(ctx)
        if r is None or r.carga["dentro"] or not r.carga.get("requiere"):
            return []
        cobijo, _, otras = self._intensidades(ctx)
        if otras > cobijo or self._cede(ctx):
            return []
        return [{"objeto": k, "cantidad": n, "urgencia": cobijo, "motivo": f"proteger: {r.carga['explicacion']}"}
                for k, n in sorted(r.carga["requiere"].items())]

    @staticmethod
    def _intensidades(ctx: Contexto) -> Tuple[float, str, float]:
        """Intensidad (anticipada) del cobijo y, de las necesidades «de fuera», la de mayor déficit actual (nombre y déficit).
        «De fuera»: las que se satisfacen con algo del mundo (declaran un ``rasgo``); las del propio cuerpo (descanso, salud)
        se recuperan dentro y no compiten con protegerse."""
        imp = ctx.onda.ef("Impulso")
        cobijo = float(imp[COBIJO].carga["intensidad"]) if COBIJO in imp else 0.0
        fuera = {n.nombre for n in ctx.perfil.necesidades if n.rasgo} - {COBIJO}
        deficits = [(float(p.carga.get("deficit", p.carga["intensidad"])), n) for n, p in imp.items() if n in fuera]
        deficit, nombre = max(deficits, default=(0.0, ""))
        return cobijo, nombre, deficit

    def decidir(self, ctx: Contexto, estrategia: Optional[Pieza] = None) -> None:
        r = recinto(ctx)
        if r is None:
            return
        c = r.carga
        cobijo, otra, otras = self._intensidades(ctx)
        if c["dentro"]:
            if max(cobijo, riesgo_exterior(ctx)) >= otras or not c["abrir"]:
                verbo = Verbo.DORMIR if Verbo.DORMIR in ctx.verbos else Verbo.ESPERAR
                self.proponer(ctx, verbo, "", cobijo, acotar(cobijo), f"proteger: dentro, {verbo.value.lower()}")
                return
            _proponer_abrir(self, ctx, c, "proteger", otra, otras, cobijo)
            return
        accion = c["accion"]
        if accion is None or otras > cobijo:
            return      # otra necesidad de fuera pesa más: que actúen sus estrategias
        self.proponer(ctx, accion["verbo"], accion["objetivo"], cobijo, acotar(float(c["confianza"]) * cobijo),
                      f"proteger: {c['explicacion']}", clase=accion.get("clase", ""), **(accion.get("datos") or {}))
