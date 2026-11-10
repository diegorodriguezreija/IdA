"""El cuerpo: constantes vitales, química, indicadores generales y presupuesto del latido."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ida.core.pieza import acotar
from ida.core.vocabulario import Afecto

VITALES = ("vitalidad", "alimentacion", "energia", "descanso")


@dataclass
class Soma:
    vitalidad: float = 100.0
    alimentacion: float = 80.0
    energia: float = 90.0
    descanso: float = 90.0
    dopamina: float = 35.0        # «querer»: sube con el error de predicción positivo, vuelve a 35
    placer: float = 20.0          # «disfrutar»: sube al comer, baja solo
    estres: float = 0.05          # en [0, 1]
    dormido: bool = False
    afecto: Afecto = Afecto.CALMA
    cargando: Optional[str] = None             # clase de lo que lleva encima
    indicadores: Dict[str, float] = field(default_factory=lambda: {"peligro": 0.0, "tension": 0.0, "calma": 1.0})
    vitales_propios: Tuple[str, ...] = ()      # constantes que marca el mundo (no el metabolismo)
    agotado_previo: bool = False               # el latido anterior agotó la amplitud

    DOPAMINA_BASAL = 35.0
    HAMBRE_CRITICA = 15.0

    # --- estado -------------------------------------------------------------
    @property
    def esta_vivo(self) -> bool:
        return self.vitalidad > 0.0

    def valores(self) -> Dict[str, float]:
        return {k: round(getattr(self, k), 2) for k in VITALES + ("dopamina", "placer")} | {"estres": round(self.estres, 3)}

    def hambre(self) -> float:
        """Urgencia de alimentarse, en [0, 1]."""
        return acotar((70.0 - self.alimentacion) / 70.0)

    def cansancio(self) -> float:
        return acotar((60.0 - min(self.energia, self.descanso)) / 60.0)

    # --- cambios ------------------------------------------------------------
    def metabolismo(self) -> None:
        """Desgaste y recuperación de un latido. No toca las constantes que marca el mundo."""
        def cambia(nombre: str, delta: float) -> None:
            if nombre not in self.vitales_propios:
                setattr(self, nombre, acotar(getattr(self, nombre) + delta, 0.0, 100.0))

        if self.dormido:
            cambia("descanso", +4.0)
            cambia("energia", +3.0)
            if self.alimentacion >= 25.0:
                cambia("vitalidad", +1.0)
        else:
            cambia("alimentacion", -(0.5 + (0.3 if self.cargando else 0.0)))
            cambia("descanso", -0.3)
            cambia("energia", +0.3 if self.alimentacion > 20.0 else -1.0)
            if self.alimentacion >= 60.0 and self.descanso >= 50.0:
                cambia("vitalidad", +0.5)
        if self.alimentacion <= 0.0:
            cambia("vitalidad", -2.0)
        self.placer = acotar(self.placer - 1.0, 0.0, 100.0)
        self.dopamina = acotar(self.dopamina - 0.15 * (self.dopamina - self.DOPAMINA_BASAL), 0.0, 100.0)

    def aplicar(self, delta: Dict[str, float]) -> None:
        for nombre, d in delta.items():
            if nombre in VITALES:
                setattr(self, nombre, acotar(getattr(self, nombre) + d, 0.0, 100.0))
        if delta.get("alimentacion", 0.0) > 0:
            self.placer = acotar(self.placer + 2.0 * delta["alimentacion"], 0.0, 100.0)
            if self.placer >= 60.0:
                self.estres = acotar(self.estres * 0.5)

    def sincronizar(self, vitales: Dict[str, float]) -> None:
        """Copia las constantes que marca el mundo (p. ej. salud y comida de un juego)."""
        for nombre, valor in vitales.items():
            if nombre in VITALES:
                setattr(self, nombre, acotar(valor, 0.0, 100.0))

    def error_prediccion(self, rpe: float) -> None:
        """Dopamina: sube o baja con el error de predicción de recompensa."""
        self.dopamina = acotar(self.dopamina + rpe, 0.0, 100.0)

    # --- indicadores y afecto ----------------------------------------------
    def actualizar_indicadores(self, peligro: float, tension: float, novedad: float) -> None:
        """Los tres indicadores generales (peligro, tensión, calma), con el arousal como base."""
        urgencia = max(peligro, self.hambre() if self.alimentacion <= self.HAMBRE_CRITICA else 0.0)
        self.estres = acotar(0.7 * self.estres + 0.3 * urgencia)
        calma = acotar(1.0 - max(peligro, tension, self.estres))
        self.indicadores = {"peligro": round(peligro, 3), "tension": round(tension, 3), "calma": round(calma, 3)}
        if self.dormido:
            self.afecto = Afecto.DORMIDO
        elif peligro >= 0.75:
            self.afecto = Afecto.PANICO if self.estres >= 0.6 else Afecto.MIEDO
        elif peligro >= 0.4 or self.alimentacion <= self.HAMBRE_CRITICA:
            self.afecto = Afecto.ALERTA
        elif self.cansancio() >= 0.6:
            self.afecto = Afecto.CANSANCIO
        elif novedad >= 0.6:
            self.afecto = Afecto.CURIOSIDAD
        else:
            self.afecto = Afecto.CALMA

    # --- presupuesto del latido --------------------------------------------
    def presupuesto(self, frecuencia_base_ms: float, amplitud_base: int) -> Tuple[float, int]:
        """Frecuencia y amplitud del próximo latido según el estado del cuerpo.

        - La energía escala la amplitud (cansado se atiende a menos cosas).
        - Dormido, la amplitud baja a 20.
        - Si el latido anterior agotó la amplitud, este tiene un 50 % más («taquicardia»).
        - Con peligro, el plazo se acorta hasta un 30 %: se decide antes y S1 gana peso.
        """
        if self.dormido:
            amplitud = 20
        else:
            amplitud = int(amplitud_base * (0.5 + 0.5 * self.energia / 100.0))
            if self.agotado_previo:
                amplitud = int(amplitud * 1.5)
        frecuencia = frecuencia_base_ms * (1.0 - 0.3 * self.indicadores.get("peligro", 0.0))
        return frecuencia, max(5, amplitud)
