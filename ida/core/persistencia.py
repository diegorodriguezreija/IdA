"""Persistencia en SQLite (modo WAL). Se escribe en lote al dormir o al morir, nunca dentro del latido."""

import json
import os
import sqlite3
from typing import Optional

from ida.core.memoria import Memoria

ESQUEMA = """
CREATE TABLE IF NOT EXISTS piezas (individuo TEXT, latido INTEGER, tipo TEXT, id TEXT, clase TEXT, sistema TEXT, arousal REAL);
CREATE TABLE IF NOT EXISTS episodios (individuo TEXT, id TEXT PRIMARY KEY, inicio INTEGER, fin INTEGER, balance REAL,
                                      resuelto INTEGER, arousal_max REAL, acciones TEXT);
CREATE TABLE IF NOT EXISTS saber (individuo TEXT, sujeto TEXT, relacion TEXT, confianza REAL, confirmaciones INTEGER,
                                  refutaciones INTEGER, estado TEXT, heredada INTEGER, PRIMARY KEY (individuo, sujeto, relacion));
CREATE TABLE IF NOT EXISTS lecturas (individuo TEXT, id TEXT PRIMARY KEY, inicio INTEGER, estado TEXT,
                                     latidos_dedicados INTEGER, elementos TEXT, respuesta TEXT);
"""


class Persistencia:
    def __init__(self, ruta: Optional[str]):
        self.ruta = ruta
        self.conn = None
        self._episodios_guardados = 0
        if ruta:
            os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
            self.conn = sqlite3.connect(ruta)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.executescript(ESQUEMA)

    def volcar(self, memoria: Memoria, individuo: str, ahora: int) -> int:
        """Escribe en lote lo pendiente y vacía el búfer. Devuelve las filas escritas."""
        if self.conn is None or not memoria.activa:
            return 0
        filas = 0
        cur = self.conn.cursor()
        for p in memoria.buffer:
            cur.execute("INSERT INTO piezas VALUES (?,?,?,?,?,?,?)",
                        (individuo, p["latido"], p["tipo"], p["id"], p.get("clase", ""), p.get("sistema", ""), p["arousal"]))
            filas += 1
        memoria.buffer.clear()
        for ep in memoria.episodios[self._episodios_guardados:]:
            cur.execute("INSERT OR REPLACE INTO episodios VALUES (?,?,?,?,?,?,?,?)",
                        (individuo, ep.id, ep.inicio, ep.fin, ep.balance, int(ep.resuelto), ep.arousal_max, json.dumps(ep.acciones)))
            filas += 1
        self._episodios_guardados = len(memoria.episodios)
        for prop in memoria.saber.values():
            cur.execute("INSERT OR REPLACE INTO saber VALUES (?,?,?,?,?,?,?,?)",
                        (individuo, prop.sujeto, prop.relacion.name, prop.confianza, prop.confirmaciones, prop.refutaciones,
                         prop.estado(ahora).value, int(prop.heredada)))
            filas += 1
        for lec in getattr(memoria, "lecturas", []):
            cur.execute("INSERT OR REPLACE INTO lecturas VALUES (?,?,?,?,?,?,?)",
                        (individuo, lec.id, lec.inicio, lec.estado.value, lec.latidos_dedicados,
                         json.dumps(lec.elementos), json.dumps(lec.respuesta) if lec.respuesta is not None else None))
            filas += 1
        self.conn.commit()
        return filas

    def nueva_vida(self) -> None:
        self._episodios_guardados = 0

    def cerrar(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
