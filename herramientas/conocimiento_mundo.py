"""Informe estático de conocimiento del mundo por diseño (decisión D3).

Para cada mundo conectable en ida/mundos:
- qué registra (componentes añadidos y sustituidos por destino, estrategias por sistema, cuerpo), con el conocimiento
  que cada Componente del mundo recibe declarado (``conocimiento_declarado()``, si lo tiene);
- sus rasgos_declarados en Perfil;
- las líneas no vacías de los ficheros de su módulo en ida/mundos;
- con ``--latidos N``, vive N latidos en cada mundo (semilla fija) y cuenta las modificaciones que cada Componente del
  mundo o del cuerpo hizo sobre piezas de tipos de la base desde el registro de autoría.

Sin la opción ``--latidos``, es estática y no ejecuta vidas.
"""

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ida.nucleo.mundo import Alta, Registro  # noqa: E402
from ida.mundos import MUNDOS, cargar  # noqa: E402

ORDEN_MUNDOS = ("minimo", "archivos", "snake", "ajedrez", "crafter")

TIPOS_BASE = {
    "Interocepcion", "Propiocepcion", "Exterocepcion", "Ambiente",
    "Imagen", "Objeto", "Supervivencia", "Reflejo", "Impulso", "Feedback",
    "Estrategia", "Peticion", "Accion", "Anticipacion", "Expectativa",
    "Patron", "Emocion", "Recuerdo", "Sujeto", "Valor", "Exteriorizacion",
    "Comunicacion", "Agente", "Predicado", "Proposicion", "Sentencia",
    "Logica", "Creencia", "Requisito", "Intencion",
}


def contar_modificaciones_vida(nombre: str, latidos: int, semilla: int = 31) -> Dict[str, int]:
    """Ejecuta una vida de N latidos y cuenta modificaciones sobre piezas de tipos de la base por autor."""
    from ida.ejecutor import ejecutar

    mods_por_autor: Dict[str, int] = {}

    def al_latir(_o: Any, onda: Any, _r: Any) -> None:
        piezas = {}
        for canal in (onda.reactiva.ev, onda.reactiva.acc, onda.reactiva.ef):
            for grupo in canal.values():
                for p in grupo.values():
                    piezas[id(p)] = p

        for p in piezas.values():
            if p.tipo not in TIPOS_BASE:
                continue
            for r in p.registro:
                if r.get("latido") == onda.ciclo and r.get("op") == "modificar":
                    autor = r.get("autor", "")
                    mods_por_autor[autor] = mods_por_autor.get(autor, 0) + 1

    try:
        with tempfile.TemporaryDirectory(prefix=f"ida_con_mundo_{nombre}_") as tmpdir:
            ejecutar(nombre, latidos=latidos, semilla=semilla, generaciones=1,
                     tabula_rasa=True, consola=False, datos=tmpdir, al_latir=al_latir)
    except Exception as exc:
        print(f"Advertencia: no se pudo simular vida en {nombre}: {exc}", file=sys.stderr)
        return {}

    return mods_por_autor


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


def informe_mundo(nombre: str, latidos: int = 0, semilla: int = 31) -> str:
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

    if latidos > 0:
        nombres_cuerpo: List[str] = []
        if reg.cuerpo:
            for comps_c in reg.cuerpo.componentes().values():
                nombres_cuerpo.extend(type(c).__name__ for c in comps_c)
        nombres_mundo: List[str] = []
        if reg.componentes:
            for alta_c in reg.componentes.values():
                nombres_mundo.extend(type(c).__name__ for c in alta_c.añade)
                nombres_mundo.extend(type(c).__name__ for c in alta_c.sustituye.values())

        salida.append(f"- **Modificaciones sobre la base ({latidos} latidos, semilla {semilla}):**")
        todos_comps = [(c, "cuerpo") for c in nombres_cuerpo] + [(c, "mundo") for c in nombres_mundo]
        if todos_comps:
            mods_por_autor = contar_modificaciones_vida(nombre, latidos, semilla)
            for c, origen in todos_comps:
                n_mods = sum(v for k, v in mods_por_autor.items() if k == c or k.endswith(f".{c}"))
                etiqueta = f" ({origen})" if origen == "cuerpo" else ""
                salida.append(f"  - `{c}`{etiqueta}: {n_mods}")
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
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--latidos", type=int, default=0, help="vive N latidos en cada mundo y cuenta modificaciones")
    parser.add_argument("--semilla", type=int, default=31, help="semilla fija para la vida (por defecto 31)")
    parser.add_argument("--mundo", choices=MUNDOS, help="limita el informe a un mundo")
    args = parser.parse_args()

    print("# Conocimiento del mundo por diseño\n")
    if args.mundo:
        mundos_a_listar = [args.mundo]
    else:
        mundos_a_listar = [m for m in ORDEN_MUNDOS if m in MUNDOS]
        for m in MUNDOS:
            if m not in mundos_a_listar:
                mundos_a_listar.append(m)

    for nombre in mundos_a_listar:
        print(informe_mundo(nombre, latidos=args.latidos, semilla=args.semilla))


if __name__ == "__main__":
    main()
