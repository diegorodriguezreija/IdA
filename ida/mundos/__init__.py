"""Mundos conectables. Cada uno es un paquete que implementa ``ida.core.mundo.Mundo``."""

MUNDOS = {
    "minimo": "ida.mundos.minimo:MundoMinimo",
    "archivos": "ida.mundos.archivos:MundoArchivos",
    "snake": "ida.mundos.snake:MundoSnake",
    "crafter": "ida.mundos.crafter:MundoCrafter",
    "ajedrez": "ida.mundos.ajedrez:MundoAjedrez",
}


def cargar(nombre: str):
    """Importa la clase del mundo solo cuando se pide (cada mundo tiene sus propias dependencias)."""
    import importlib

    if nombre not in MUNDOS:
        raise ValueError(f"Mundo desconocido '{nombre}'. Disponibles: {', '.join(MUNDOS)}")
    modulo, clase = MUNDOS[nombre].split(":")
    return getattr(importlib.import_module(modulo), clase)
