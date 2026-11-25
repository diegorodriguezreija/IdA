"""MapaLocal (D10, S1.Interpretar): mapa métrico de las casillas vistas, desde lo percibido.

En este orden:
1. COGER o USAR sobre una vecina (para USAR, la de delante): si la casilla cambió de clase, la transformación; si la
   acción salió y la casilla no cambió, también («no la cambia»): así un primer intento real corrige lo inferido. Y
   los cierres: una casilla que el propio individuo cambió con USAR a algo por donde no pasa un peligro.
2. Libres (lugares), ocupadas (algo encima de la casilla) y peligros (un agente peligroso encima), de las piezas
   ``Exterocepcion``; ``mapa.ver_casillas``.
3. ``mapa.yo_previo``: posición y orientación de este latido, para el contraste del siguiente.

No actúa en los barridos: su trabajo va en ``aprender``, que el Core llama en ``Organismo._aprender`` (donde estaba
``_aprender_mapa``), después del de ``ModeloDirecto``. Escribe en la sección «cuadricula» de la Memoria (D7), cuyo dueño es
el cuerpo; las transformaciones son del cuerpo (geometría: qué hace cada acción con la casilla).
"""

from typing import Set, cast

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.onda import Onda
from ida.nucleo.vocabulario import Verbo
from ida.cuerpos.cuadricula.geometria import Pos
from ida.cuerpos.cuadricula.memoria import MapaCuadricula
from ida.cuerpos.cuadricula.situacion import accion_previa, situacion, vecina


class MapaLocal(Componente):
    def activo(self, onda: Onda) -> bool:
        return False   # sin barridos: no cobra ni cuenta operaciones en el latido

    def aprender(self, ctx: Contexto) -> None:
        s = situacion(ctx)
        if s is None:
            return
        mapa = cast(MapaCuadricula, ctx.memoria.seccion_propia("cuadricula", self.de_cuerpo))
        c = accion_previa(ctx)
        v = vecina(mapa, c)
        if c is not None and v is not None:
            _, destino, _ = v
            verbo = c["verbo"]
            antes = mapa.casillas.get(destino)
            despues = s.casillas.get(destino)
            cambio = antes is not None and despues is not None and antes != despues
            if verbo in (Verbo.COGER, Verbo.USAR) and antes is not None and despues is not None and (cambio or bool(c.get("exito"))):
                objetivo = str(c.get("clase") or c.get("objetivo") or "")
                mapa.aprender_transformacion(verbo, objetivo, antes, despues)   # también «no cambió», si la acción salió
                if cambio and verbo == Verbo.USAR and not mapa.transitable_peligro(despues):
                    mapa.cierres.add(destino)
                elif cambio:
                    mapa.cierres.discard(destino)
        libres: Set[Pos] = set()
        ocupadas: Set[Pos] = set()
        peligros: Set[Pos] = set()
        for e in ctx.onda.ev("Exterocepcion").values():   # una pieza por entidad: clase, rasgos (con el peligro) y datos
            pos = e.carga.get("datos", {}).get("pos")
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                continue
            p = (int(pos[0]), int(pos[1]))
            if e.rasgo("lugar") >= 0.5:
                libres.add(p)
            elif e.carga.get("clase") != s.casillas.get(p):
                ocupadas.add(p)          # algo encima de la casilla (no es la propia casilla)
                if e.rasgo("peligro") >= 0.5 and e.rasgo("agente") >= 0.5:
                    peligros.add(p)
        mapa.ver_casillas(s.aqui, s.casillas, libres, ocupadas, peligros)
        mapa.yo_previo = (s.aqui, s.cara)
