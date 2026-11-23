"""MapaLocal (D10, S1.Interpretar): mapa métrico de las casillas vistas, desde lo percibido.

En este orden:
1. COGER o USAR sobre una vecina (para USAR, la de delante): si la casilla cambió de clase, la transformación; si la
   acción salió y la casilla no cambió, también («no la cambia»): así un primer intento real corrige lo inferido. Y
   los cierres: una casilla que el propio individuo cambió con USAR a algo por donde no pasa un peligro.
2. Libres (lugares), ocupadas (algo encima de la casilla) y peligros (un agente peligroso encima); ``mem.ver_casillas``.
3. ``mem.yo_previo``: posición y orientación de este latido, para el contraste del siguiente.

No actúa en los barridos: su trabajo va en ``aprender``, que el Core llama en ``Organismo._aprender`` (donde estaba
``_aprender_mapa``), después del de ``ModeloDirecto``. Los datos siguen en ``Memoria`` (``casillas``, ``cierres``,
``yo_previo``): las secciones con dueño son A7.
"""

from typing import Set

from ida.core.arquitectura import Componente, Contexto
from ida.core.memoria import Pos
from ida.core.onda import Onda
from ida.core.vocabulario import Verbo
from ida.cuerpos.cuadricula.situacion import accion_previa, situacion, vecina


class MapaLocal(Componente):
    def activo(self, onda: Onda) -> bool:
        return False   # sin barridos: no cobra ni cuenta operaciones en el latido

    def aprender(self, ctx: Contexto) -> None:
        s = situacion(ctx)
        if s is None:
            return
        mem = ctx.memoria
        c = accion_previa(ctx)
        v = vecina(mem, c)
        if c is not None and v is not None:
            _, destino, _ = v
            verbo = c["verbo"]
            antes = mem.casillas.get(destino)
            despues = s.casillas.get(destino)
            cambio = antes is not None and despues is not None and antes != despues
            if verbo in (Verbo.COGER, Verbo.USAR) and antes is not None and despues is not None and (cambio or bool(c.get("exito"))):
                objetivo = str(c.get("clase") or c.get("objetivo") or "")
                # A7: las transformaciones son de Requisito (S3 · Interpretar) según D7; hasta entonces se aprenden aquí.
                mem.aprender_transformacion(verbo, objetivo, antes, despues)   # también «no cambió», si la acción salió
                if cambio and verbo == Verbo.USAR and not mem.transitable_peligro(despues):
                    mem.cierres.add(destino)
                elif cambio:
                    mem.cierres.discard(destino)
        libres: Set[Pos] = set()
        ocupadas: Set[Pos] = set()
        peligros: Set[Pos] = set()
        exterocepcion = ctx.onda.ev("Exterocepcion")   # el peligro (de Amenaza o del mundo) está en la pieza de cada entidad
        for e in ctx.observacion.entidades if ctx.observacion is not None else []:
            pos = e.datos.get("pos")
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                continue
            p = (int(pos[0]), int(pos[1]))
            if e.rasgos.get("lugar", 0.0) >= 0.5:
                libres.add(p)
            elif e.clase != s.casillas.get(p):
                ocupadas.add(p)          # algo encima de la casilla (no es la propia casilla)
                pieza = exterocepcion.get(e.id)
                if pieza is not None and pieza.rasgo("peligro") >= 0.5 and e.rasgos.get("agente", 0.0) >= 0.5:
                    peligros.add(p)
        mem.ver_casillas(s.aqui, s.casillas, libres, ocupadas, peligros)
        mem.yo_previo = (s.aqui, s.cara)
