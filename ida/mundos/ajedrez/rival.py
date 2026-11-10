"""Bot rival local (SPDX-License-Identifier: GPL-3.0-or-later, por depender de python-chess).

Negamax con poda alfa-beta:
1. La evaluación de las hojas se hace desde el bando que mueve.
2. La variedad viene de barajar el orden de las jugadas, no de sumar azar a las cotas de poda.
"""

import random
from typing import Optional

import chess

VALOR = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def evaluar(tablero: chess.Board) -> int:
    """Material más un pequeño bono por el centro, desde el punto de vista del bando que mueve."""
    if tablero.is_checkmate():
        return -100000
    if tablero.is_stalemate() or tablero.is_insufficient_material():
        return 0
    total = 0
    for casilla, pieza in tablero.piece_map().items():
        centro = 7 - (abs(3.5 - chess.square_file(casilla)) + abs(3.5 - chess.square_rank(casilla)))
        valor = VALOR[pieza.piece_type] + int(centro * (4 if pieza.piece_type in (chess.KNIGHT, chess.PAWN) else 1))
        total += valor if pieza.color == tablero.turn else -valor
    return total


class RivalLocal:
    """Dificultad 0: capturas o azar · 1: mejor jugada a 1 ply · 2: alfa-beta a 2 ply · 3: alfa-beta a 3 ply."""

    def __init__(self, dificultad: int = 2, semilla: Optional[int] = None):
        self.dificultad = int(dificultad)
        self.azar = random.Random(semilla)

    def jugar(self, tablero: chess.Board) -> chess.Move:
        legales = list(tablero.legal_moves)
        self.azar.shuffle(legales)
        if self.dificultad <= 0:
            capturas = [m for m in legales if tablero.is_capture(m)]
            return capturas[0] if capturas else legales[0]
        profundidad = {1: 1, 2: 2}.get(self.dificultad, 3)
        legales.sort(key=tablero.is_capture, reverse=True)
        mejor, alfa = legales[0], -10**9
        for m in legales:
            tablero.push(m)
            valor = -self._alfabeta(tablero, profundidad - 1, -10**9, -alfa)
            tablero.pop()
            if valor > alfa:
                alfa, mejor = valor, m
        return mejor

    def _alfabeta(self, tablero: chess.Board, profundidad: int, alfa: int, beta: int) -> int:
        if profundidad == 0 or tablero.is_game_over():
            return evaluar(tablero)
        jugadas = sorted(tablero.legal_moves, key=tablero.is_capture, reverse=True)
        for m in jugadas:
            tablero.push(m)
            valor = -self._alfabeta(tablero, profundidad - 1, -beta, -alfa)
            tablero.pop()
            if valor >= beta:
                return beta
            alfa = max(alfa, valor)
        return alfa
