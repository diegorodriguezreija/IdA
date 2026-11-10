"""Ajedrez contra un bot local (SPDX-License-Identifier: GPL-3.0-or-later; ver ``LICENCIA.md``).

Traducción al vocabulario común:
- Lugares: cada jugada legal. El sensor de este mundo mira la respuesta del rival para
  calcular sus rasgos: ``nutritivo`` es el material que gana más un pequeño valor posicional
  (centro, desarrollo, enroque); ``peligro`` es el material que puede perder justo después
  (1 si permite mate en 1).
- Clase de cada jugada: su tipo (``captura_dama``, ``jaque``, ``enroque``, ``caballo``...), para
  que la experiencia generalice entre jugadas parecidas.
- Entidades: las piezas propias atacadas y sin defensa suficiente (peligro) y el jaque.
- Cuerpo: ganar material alimenta, perder material daña; recibir mate es la muerte.

La jugada del rival se hace dentro de ``ejecutar`` (tiempo del mundo: no cuenta en la guillotina).

Opciones: ``--opcion dificultad=0..3`` (por defecto 2), ``--opcion color=negras``,
``--opcion stockfish=RUTA`` con ``--opcion elo=1350`` para usar Stockfish como rival.
"""

from typing import Any, Dict, List, Optional, Set

import chess
import chess.engine

from ida.core.mundo import Efecto, Entidad, Mundo, Observacion, Perfil
from ida.core.vocabulario import Verbo
from ida.mundos.ajedrez.rival import VALOR, RivalLocal

NOMBRE = {chess.PAWN: "peon", chess.KNIGHT: "caballo", chess.BISHOP: "alfil", chess.ROOK: "torre", chess.QUEEN: "dama", chess.KING: "rey"}
PUNTOS = {t: v / 100 for t, v in VALOR.items()}   # peón = 1


def _pieza(tablero: chess.Board, casilla: int) -> chess.Piece:
    """La pieza de una casilla que se sabe ocupada (origen de una jugada legal)."""
    pieza = tablero.piece_at(casilla)
    assert pieza is not None, chess.square_name(casilla)
    return pieza


def material(tablero: chess.Board, color: bool) -> float:
    return sum(PUNTOS[p.piece_type] for p in tablero.piece_map().values() if p.color == color)


def perdida_inmediata(tablero: chess.Board) -> float:
    """Lo peor que puede ganar en material el bando que mueve con una sola jugada (y la réplica)."""
    peor = 0.0
    for r in tablero.legal_moves:
        tablero.push(r)
        if tablero.is_checkmate():
            tablero.pop()
            return 99.0
        tablero.pop()
        if not tablero.is_capture(r):
            continue
        victima = tablero.piece_at(r.to_square)
        valor = PUNTOS[victima.piece_type] if victima else 1.0   # captura al paso
        atacante = tablero.piece_at(r.from_square)
        tablero.push(r)
        defendida = tablero.is_attacked_by(tablero.turn, r.to_square)
        tablero.pop()
        ganancia = valor - (PUNTOS[atacante.piece_type] if defendida and atacante else 0.0)
        peor = max(peor, ganancia)
    return peor


class MundoAjedrez(Mundo):
    nombre = "ajedrez"
    perfil = Perfil(frecuencia_ms=100.0, amplitud=120, memoria="ligera", duerme=False, hogar=False, peso_experiencia=0.15,
                    vitales_propios=True)
    MATERIAL_INICIAL = 39.0

    def __init__(self, dificultad: Any = 2, color: str = "blancas", stockfish: str = "", elo: Any = 1350, semilla: Optional[int] = None, **_):
        self.dificultad = int(dificultad)
        self.color = chess.BLACK if str(color).lower().startswith("n") else chess.WHITE
        self.ruta_stockfish = stockfish
        self.elo = int(elo)
        self.motor: Optional[chess.engine.SimpleEngine] = None
        self.tablero = chess.Board()
        self.rival = RivalLocal(self.dificultad)
        self.resultado = ""
        self.jugadas = 0

    # --- ciclo de vida -------------------------------------------------------
    def reiniciar(self, semilla: Optional[int]) -> None:
        self.tablero = chess.Board()
        self.rival = RivalLocal(self.dificultad, semilla)
        self.resultado, self.jugadas = "", 0
        if self.ruta_stockfish and self.motor is None:
            self.motor = chess.engine.SimpleEngine.popen_uci(self.ruta_stockfish)
            self.motor.configure({"UCI_LimitStrength": True, "UCI_Elo": self.elo})
        if self.tablero.turn != self.color:
            self._turno_rival()

    def cerrar(self) -> None:
        if self.motor is not None:
            self.motor.quit()
            self.motor = None

    def _turno_rival(self) -> None:
        if self.tablero.is_game_over():
            return
        if self.motor is not None:
            jugada = self.motor.play(self.tablero, chess.engine.Limit(time=0.05)).move
        else:
            jugada = self.rival.jugar(self.tablero)
        if jugada is not None:
            self.tablero.push(jugada)

    # --- percepción ----------------------------------------------------------
    def _clase(self, m: chess.Move) -> str:
        t = self.tablero
        if t.is_castling(m):
            return "enroque"
        if t.is_capture(m):
            victima = t.piece_at(m.to_square)
            return f"captura_{NOMBRE[victima.piece_type] if victima else 'peon'}"
        if t.gives_check(m):
            return "jaque"
        return NOMBRE[_pieza(t, m.from_square).piece_type]

    def _posicional(self, m: chess.Move, ventaja: float) -> float:
        """Valor posicional de una jugada (sin material). Lo calcula el sensor del mundo.

        Siempre: centro, desarrollo, enroque y coronación. Además, según el balance de material:
        - con ventaja (3 o más): jaque, quitar casillas al rey rival, avanzar peones y no repetir;
        - en desventaja (3 o más): repetir posición vale (buscar tablas).
        """
        t = self.tablero
        pieza = _pieza(t, m.from_square)
        destino = m.to_square
        centro = 1.0 - (abs(3.5 - chess.square_file(destino)) + abs(3.5 - chess.square_rank(destino))) / 7.0
        valor = 0.1 * centro
        if pieza.piece_type in (chess.KNIGHT, chess.BISHOP) and chess.square_rank(m.from_square) in (0, 7):
            valor += 0.1          # desarrollo
        if t.is_castling(m):
            valor += 0.25
        if m.promotion:
            valor += 0.6
        if abs(ventaja) < 3:
            return valor
        rey_antes = self._casillas_rey_rival()
        t.push(m)
        repite = t.can_claim_draw() or t.is_repetition(2)
        jaque = t.is_check()
        rey_despues = self._casillas_rey_rival(tras_jugada=True)
        t.pop()
        if ventaja >= 3:
            valor += 0.15 if jaque else 0.0
            valor += 0.05 * max(0, rey_antes - rey_despues)            # encerrar al rey
            if pieza.piece_type == chess.PAWN:
                avance = chess.square_rank(destino) if self.color == chess.WHITE else 7 - chess.square_rank(destino)
                valor += 0.03 * avance
            if repite:
                valor -= 0.4                                          # con ventaja, no regalar tablas
        elif repite:
            valor += 0.4                                              # en desventaja, las tablas valen
        return max(0.0, valor)

    def _casillas_rey_rival(self, tras_jugada: bool = False) -> int:
        """Casillas a las que puede moverse el rey rival (cuántas le quedan)."""
        t = self.tablero
        rival = not self.color
        rey = t.king(rival)
        if rey is None:
            return 0
        return len([c for c in chess.SquareSet(chess.BB_KING_ATTACKS[rey])
                    if not t.is_attacked_by(self.color, c) and ((p := t.piece_at(c)) is None or p.color != rival)])

    def observar(self) -> Observacion:
        t = self.tablero
        entidades: List[Entidad] = []
        mio = material(t, self.color)
        ventaja = mio - material(t, not self.color)
        for m in t.legal_moves:
            victima = t.piece_at(m.to_square)
            ganancia = PUNTOS[victima.piece_type] if t.is_capture(m) and victima else (1.0 if t.is_capture(m) else 0.0)
            t.push(m)
            mate = t.is_checkmate()
            riesgo = 0.0 if mate else perdida_inmediata(t)
            t.pop()
            nutritivo = 1.0 if mate else min(1.0, ganancia / 9.0 + self._posicional(m, ventaja))
            peligro = 1.0 if riesgo >= 99 else min(1.0, riesgo / 9.0)
            rasgos = {"lugar": 1.0, "proximidad": 1.0, "nutritivo": nutritivo, "peligro": peligro}
            entidades.append(Entidad(m.uci(), self._clase(m), rasgos, {"jugada": m.uci()}))
        for casilla, pieza in t.piece_map().items():
            if pieza.color == self.color and t.is_attacked_by(not self.color, casilla) and not t.is_attacked_by(self.color, casilla):
                entidades.append(Entidad(f"amenaza_{chess.square_name(casilla)}", f"{NOMBRE[pieza.piece_type]}_atacado",
                                         {"proximidad": 1.0, "peligro": min(1.0, PUNTOS[pieza.piece_type] / 9.0 + 0.2)}))
        if t.is_check():
            entidades.append(Entidad("jaque_recibido", "jaque_recibido", {"proximidad": 1.0, "peligro": 0.9, "agente": 1.0}))
        suyo = material(t, not self.color)
        vitales = {  # solo el mate mata: la vitalidad refleja el material propio, la alimentación el balance
            "vitalidad": max(5.0, 100.0 * mio / self.MATERIAL_INICIAL),
            "alimentacion": max(0.0, min(100.0, 60.0 + 5.0 * (mio - suyo))),
            "energia": 100.0, "descanso": 100.0,
        }
        return Observacion(ubicacion=t.fen().split(" ")[0], entidades=entidades, vitales=vitales, mensaje=f"material {mio:.0f}-{suyo:.0f}")

    # --- acción --------------------------------------------------------------
    def verbos(self) -> Set[Verbo]:
        return {Verbo.MOVER}

    def ejecutar(self, verbo: Verbo, objetivo: str, datos: Dict[str, Any]) -> Efecto:
        t = self.tablero
        try:
            m = chess.Move.from_uci(objetivo)
        except ValueError:
            return Efecto(False, mensaje="jugada no válida")
        if verbo != Verbo.MOVER or m not in t.legal_moves:
            return Efecto(False, mensaje="jugada ilegal")
        mio, suyo = material(t, self.color), material(t, not self.color)
        t.push(m)
        self.jugadas += 1
        self._turno_rival()
        ganado = suyo - material(t, not self.color)
        perdido = mio - material(t, self.color)
        delta = {}
        if ganado:
            delta["alimentacion"] = 6.0 * ganado
        if perdido:
            delta["vitalidad"] = -6.0 * perdido
        if t.is_game_over():
            r = t.result(claim_draw=True)
            gano = (r == "1-0") == (self.color == chess.WHITE) and r != "1/2-1/2"
            self.resultado = "TABLAS" if r == "1/2-1/2" else ("VICTORIA" if gano else "DERROTA")
            if self.resultado == "DERROTA":
                return Efecto(True, delta, causa="jaque_mate", muerte=True, mensaje="jaque mate recibido")
            return Efecto(True, delta, mensaje=self.resultado.lower())
        return Efecto(True, delta)

    def terminado(self) -> bool:
        return bool(self.resultado) or self.tablero.can_claim_draw()

    def puntuacion(self) -> Dict[str, Any]:
        resultado = self.resultado or ("TABLAS" if self.tablero.can_claim_draw() else "SIN TERMINAR")
        return {"resultado": resultado, "jugadas": self.jugadas,
                "material": [material(self.tablero, self.color), material(self.tablero, not self.color)]}

    def vista(self) -> str:
        ultima = self.tablero.peek().uci() if self.tablero.move_stack else "—"
        return f"{self.tablero}\núltima: {ultima} · jugadas de IdA: {self.jugadas}"
