"""ModeloDirecto (D10, CORE.Actuar): qué hace cada acción con el propio cuerpo, aprendido de la copia eferente.

Contrasta la acción anterior con lo percibido ahora (propiocepción):
- MOVER hacia una casilla vecina de clase conocida: si la posición cambió y si quedó mirando hacia ella, según la
  casilla fuera transitable o no;
- COGER, COMER o ATACAR sobre una vecina: si quedó mirando hacia ella.

No actúa en los barridos: su trabajo va en ``aprender``, que el Core llama en ``Organismo._aprender`` (donde estaba
``_aprender_mapa``), antes que el de ``MapaLocal``: lee ``mapa.yo_previo`` y ``mapa.casillas`` antes de que este los
actualice. Escribe en la sección «cuadricula» de la Memoria (D7), cuyo dueño es el cuerpo.
"""

from typing import cast

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.onda import Onda
from ida.nucleo.vocabulario import Verbo
from ida.cuerpos.cuadricula.memoria import MapaCuadricula
from ida.cuerpos.cuadricula.situacion import accion_previa, situacion, vecina


class ModeloDirecto(Componente):
    def activo(self, onda: Onda) -> bool:
        return False   # sin barridos: no cobra ni cuenta operaciones en el latido

    def aprender(self, ctx: Contexto) -> None:
        s = situacion(ctx)
        if s is None:
            return
        mapa = cast(MapaCuadricula, ctx.memoria.seccion_propia("cuadricula", self.de_cuerpo))
        c = accion_previa(ctx)
        v = vecina(mapa, c)
        if c is None or v is None:
            return
        p0, destino, direccion = v
        verbo = c["verbo"]
        if verbo == Verbo.MOVER:
            libre = mapa.transitable(mapa.casillas.get(destino))
            if libre is not None:
                mapa.aprender_cuerpo("mover", libre, s.aqui == destino, s.cara == direccion)
        elif verbo in (Verbo.COGER, Verbo.COMER, Verbo.ATACAR):
            mapa.aprender_cuerpo("interactuar", True, s.aqui != p0, s.cara == direccion)
