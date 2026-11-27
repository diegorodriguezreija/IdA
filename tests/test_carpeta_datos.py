"""Tests para _carpeta_datos en ida.ejecutor."""

import os
import sys

from ida.ejecutor import _carpeta_datos


def test_carpeta_datos_en_repositorio(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'ida'\n", encoding="utf-8")
    assert _carpeta_datos(str(tmp_path)) == os.path.join(str(tmp_path), "datos")


def test_carpeta_datos_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    assert _carpeta_datos(str(tmp_path)) == os.path.join(str(tmp_path / "Local"), "IdA", "datos")


def test_carpeta_datos_macos(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert _carpeta_datos(str(tmp_path)) == os.path.join(
        os.path.expanduser("~"), "Library", "Application Support", "IdA", "datos"
    )


def test_carpeta_datos_linux_xdg(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert _carpeta_datos(str(tmp_path)) == os.path.join(str(tmp_path / "xdg"), "ida", "datos")


def test_carpeta_datos_linux_sin_xdg(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert _carpeta_datos(str(tmp_path)) == os.path.join(
        os.path.expanduser("~/.local/share"), "ida", "datos"
    )
