"""Test de integridad de enlaces en la documentación Markdown.

Recorre todos los ficheros .md del repositorio (salvo .venv, .git y datos/),
extrae los enlaces relativos ](ruta) y src="ruta", y comprueba que apunten a ficheros existentes.
"""

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {".venv", ".git", "datos"}

RE_MD_LINK = re.compile(r"\]\(([^)]+)\)")
RE_SRC_LINK = re.compile(r"""src=["']([^"']+)["']""")


def extraer_enlaces(texto: str) -> list[str]:
    enlaces: list[str] = []
    for match in RE_MD_LINK.finditer(texto):
        destino = match.group(1).strip()
        # Si tiene título opcional tipo (ruta "título"), extraer solo la ruta
        if " " in destino:
            destino = destino.split()[0]
        enlaces.append(destino)
    for match in RE_SRC_LINK.finditer(texto):
        destino = match.group(1).strip()
        if " " in destino:
            destino = destino.split()[0]
        enlaces.append(destino)
    return enlaces


def test_enlaces_markdown_no_rotos() -> None:
    ficheros_md: list[Path] = []
    for p in REPO_ROOT.rglob("*.md"):
        parts = set(p.relative_to(REPO_ROOT).parts)
        if not parts.intersection(EXCLUDED_DIRS):
            ficheros_md.append(p)

    rotos: list[str] = []
    for md_path in ficheros_md:
        contenido = md_path.read_text(encoding="utf-8")
        enlaces = extraer_enlaces(contenido)
        for enlace in enlaces:
            # Ignorar enlaces externos y anclas locales
            if enlace.startswith(("http://", "https://", "mailto:", "#")) or enlace == "":
                continue
            # Quitar ancla si existe
            ruta_limpia = enlace.split("#")[0]
            if not ruta_limpia:
                continue

            destino = (md_path.parent / ruta_limpia).resolve()
            if not destino.exists():
                rel_origen = md_path.relative_to(REPO_ROOT).as_posix()
                rotos.append(f"{rel_origen} -> {enlace} (resuelto: {destino})")

    assert not rotos, f"Se encontraron {len(rotos)} enlaces rotos:\n" + "\n".join(rotos)
