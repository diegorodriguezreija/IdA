"""Componente Impulso para S3."""

from ida.nucleo.arquitectura import Componente, Contexto
from ida.nucleo.vocabulario import EstadoSaber, Relacion
from ida.s3.interpretar.creencia import creencia
from ida.sistemas.piezas import objetos


class Impulso(Componente):
    """Control de S3 de arriba abajo (decisión 13): con certeza, sube los impulsos que encajan con lo
    que sabe y baja los que no. Gradual, no un interruptor: el cambio es proporcional a la confianza
    de lo demostrado (hasta ``FUERZA``). Sin nada demostrado, no toca nada. Solo modifica piezas
    ``Impulso`` (de cualquier sistema, decisión 14); el Tribunal suma ese cambio al arousal de las
    acciones de ese impulso.
    - Peligro demostrado cerca (proximidad ≥ 0,5): sube Seguridad.
    - Todo lo comestible a la vista se sabe que no nutre: baja las necesidades que satisface lo nutritivo.
    """

    tipo = "Impulso"
    FUERZA = 0.2

    def reactiva(self, ctx: Contexto) -> None:
        if not ctx.con_experiencia:
            return
        creencias = ctx.onda.ef("Creencia")
        impulsos = ctx.onda.ef("Impulso")
        seguridad = impulsos.get("seguridad")
        if seguridad is not None:
            certeza = max((c.carga["trust"] for o in objetos(ctx) if o.rasgo("proximidad") >= 0.5
                           for c in [creencia(creencias, o.clase, Relacion.PELIGROSO)] if c is not None and c.carga["sostiene"]),
                          default=0.0)
            if certeza > 0.0:
                self.modificar(ctx, seguridad, arousal=seguridad.arousal + self.FUERZA * certeza, entrada="S3: peligro demostrado cerca")
        comestibles = [o for o in objetos(ctx) if o.rasgo("nutritivo") >= 0.3]
        refutadas = [creencia(creencias, o.clase, Relacion.NUTRITIVO) for o in comestibles]
        if comestibles and all(c is not None and c.carga["estado"] == EstadoSaber.REFUTADA for c in refutadas):
            confianza_nutre = max(c.carga["trust"] for c in refutadas if c is not None)
            certeza = 1.0 - confianza_nutre        # certeza de que no nutre
            for imp in impulsos.values():
                if imp.carga.get("rasgo") == "nutritivo":
                    self.modificar(ctx, imp, arousal=imp.arousal - self.FUERZA * certeza, entrada="S3: lo que hay no nutre")
