"""Informe estático de conocimiento del mundo por diseño (decisión D3).

Para cada mundo conectable en ida/mundos:
- qué registra (componentes añadidos y sustituidos por destino, estrategias por sistema, cuerpo), con el conocimiento
  que cada Componente del mundo recibe declarado (``conocimiento_declarado()``, si lo tiene);
- sus rasgos_declarados en Perfil;
- las líneas no vacías de los ficheros de su módulo en ida/mundos.

No ejecuta vidas (es estática).
"""

import sys
from pathlib import Path
from typing import Any, List, Tuple

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ida.core.mundo import Alta, Registro  # noqa: E402
from ida.mundos import MUNDOS, cargar  # noqa: E402

ORDEN_MUNDOS = ("minimo", "archivos", "snake", "ajedrez", "crafter")


def ficheros_del_modulo(nombre: str) -> List[Path]:
    """Ficheros que componen el módulo o paquete del mundo en ida/mundos."""
    dir_pkg = RAIZ / "ida" / "mundos" / nombre
    if dir_pkg.is_dir():
        return sorted(
            p
            for p in dir_pkg.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and not p.name.startswith(".")
            and p.suffix in (".py", ".json")
        )
    fichero_py = RAIZ / "ida" / "mundos" / f"{nombre}.py"
    ficheros: List[Path] = [fichero_py] if fichero_py.is_file() else []
    for extra in sorted((RAIZ / "ida" / "mundos").glob(f"{nombre}_*")):
        if extra.is_file():
            ficheros.append(extra)
    return ficheros


def contar_lineas_no_vacias(ruta: Path) -> int:
    """Cuenta las líneas que no están vacías ni son solo espacios."""
    try:
        contenido = ruta.read_text(encoding="utf-8")
        return sum(1 for linea in contenido.splitlines() if linea.strip())
    except UnicodeDecodeError:
        contenido = ruta.read_text(encoding="latin-1")
        return sum(1 for linea in contenido.splitlines() if linea.strip())


def nombre_componente(c: Any) -> str:
    """Nombre de clase, «(preatentivo)» si lo es y el conocimiento que declara el mundo al construirlo, si lo expone
    (``conocimiento_declarado()``: p. ej. las clases que el manual declara NUTRITIVO y UTIL)."""
    texto = type(c).__name__ + (" (preatentivo)" if getattr(c, "preatentivo", False) else "")
    declarado = getattr(c, "conocimiento_declarado", None)
    if callable(declarado):
        texto += " {" + "; ".join(f"{k}: {', '.join(map(str, v))}" for k, v in declarado().items()) + "}"
    return texto


def formatear_alta(alta: Alta) -> str:
    partes: List[str] = []
    if alta.añade:
        nombres_anade = [nombre_componente(c) for c in alta.añade]
        partes.append(f"añade: [{', '.join(nombres_anade)}]")
    if alta.sustituye:
        items_sust = [f"{k} -> {type(v).__name__}" for k, v in alta.sustituye.items()]
        partes.append(f"sustituye: {{{', '.join(items_sust)}}}")
    return "; ".join(partes) if partes else "(vacío)"


def informe_mundo(nombre: str) -> str:
    salida: List[str] = [f"## Mundo: `{nombre}`", ""]
    try:
        clase_mundo = cargar(nombre)
        instancia: Any = clase_mundo()
    except Exception as exc:
        salida.append(f"**Error al importar o instanciar:** {exc}")
        salida.append("")
        return "\n".join(salida)

    perfil = getattr(instancia, "perfil", None)
    rasgos: Tuple[str, ...] = getattr(perfil, "rasgos_declarados", ()) if perfil else ()
    rasgos_txt = ", ".join(f"`{r}`" for r in rasgos) if rasgos else "*(ninguno)*"
    salida.append(f"- **Rasgos declarados:** {rasgos_txt}")

    reg: Registro = instancia.registro()
    if reg.cuerpo is None:
        salida.append("- **Cuerpo:** *(ninguno)*")
    else:
        # Familia de cuerpos (D10): su nombre y sus Componentes por destino, en orden de montaje
        salida.append(f"- **Cuerpo:** `{reg.cuerpo.nombre}` ({type(reg.cuerpo).__module__})")
        for destino, comps in reg.cuerpo.componentes().items():
            salida.append(f"  - `{destino}`: [{', '.join(type(c).__name__ for c in comps)}]")

    # Componentes
    salida.append("- **Componentes:**")
    if reg.componentes:
        for destino, alta in reg.componentes.items():
            salida.append(f"  - `{destino}`: {formatear_alta(alta)}")
    else:
        salida.append("  - *(ninguno)*")

    # Estrategias
    salida.append("- **Estrategias:**")
    if reg.estrategias:
        for sis, alta in reg.estrategias.items():
            salida.append(f"  - `{sis}`: {formatear_alta(alta)}")
    else:
        salida.append("  - *(ninguno)*")

    # Generales opcionales que monta (D3, D15): sustituyen a las activaciones condicionales
    opcionales = ", ".join(f"`{o}`" for o in reg.opcionales) if reg.opcionales else "*(ninguno)*"
    salida.append(f"- **Opcionales:** {opcionales}")

    # Ficheros y líneas de código
    ficheros = ficheros_del_modulo(nombre)
    total_lineas = 0
    desglose: List[str] = []
    for f in ficheros:
        rel = f.relative_to(RAIZ).as_posix()
        n = contar_lineas_no_vacias(f)
        total_lineas += n
        desglose.append(f"`{rel}` ({n} líneas)")

    salida.append(f"- **Líneas no vacías:** **{total_lineas}** total")
    for d in desglose:
        salida.append(f"  - {d}")

    salida.append("")
    return "\n".join(salida)


def main() -> None:
    print("# Conocimiento del mundo por diseño\n")
    mundos_a_listar = [m for m in ORDEN_MUNDOS if m in MUNDOS]
    for m in MUNDOS:
        if m not in mundos_a_listar:
            mundos_a_listar.append(m)

    for nombre in mundos_a_listar:
        print(informe_mundo(nombre))


if __name__ == "__main__":
    main()
