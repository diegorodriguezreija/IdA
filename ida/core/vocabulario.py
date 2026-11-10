"""Vocabulario cerrado del framework: verbos, rasgos, relaciones, estados y afectos.

Es el idioma común entre el framework y los mundos. Un mundo traduce su realidad
a estos términos; el framework nunca usa palabras de un mundo concreto.
"""

from enum import Enum


class _Voz(str, Enum):
    def __str__(self) -> str:
        return self.value


class Verbo(_Voz):
    """Verbos comunes de Ejecución. Cada mundo declara cuáles admite."""

    MOVER = "MOVER"        # ir a un lugar
    COMER = "COMER"        # ingerir algo (comida, bebida, bytes...)
    ATACAR = "ATACAR"      # dañar una entidad
    COGER = "COGER"        # recoger o recolectar algo
    SOLTAR = "SOLTAR"      # dejar lo que se lleva
    USAR = "USAR"          # fabricar, colocar o usar algo (la carga dice qué)
    DORMIR = "DORMIR"      # dormir
    ESPERAR = "ESPERAR"    # no hacer nada este latido
    ACECHAR = "ACECHAR"    # interno: el Tribunal aún no se decide


# Rasgos con significado que cada mundo calcula para cada entidad, en [0, 1].
RASGOS = (
    "proximidad",  # 1 = al alcance
    "nutritivo",   # lo que promete para el cuerpo
    "peligro",     # lo que amenaza al cuerpo
    "novedad",     # cuánto se desconoce o hace cuánto que no se ve
    "recurso",     # utilidad instrumental (sirve para algo aunque no se coma)
    "lugar",       # es un destino al que se puede ir
    "agente",      # actúa por sí mismo
)


class Relacion(_Voz):
    """Propiedades que el individuo puede llegar a saber de una clase de cosas."""

    NUTRITIVO = "nutre"
    PELIGROSO = "hace daño"
    UTIL = "sirve"


class EstadoSaber(_Voz):
    HIPOTESIS = "hipótesis"
    DEMOSTRADA = "demostrada"
    REFUTADA = "refutada"


class Afecto(_Voz):
    CALMA = "CALMA"
    CURIOSIDAD = "CURIOSIDAD"
    ALERTA = "ALERTA"
    MIEDO = "MIEDO"
    PANICO = "PANICO"
    CANSANCIO = "CANSANCIO"
    DORMIDO = "DORMIDO"
