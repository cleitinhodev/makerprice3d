# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Pastas do usuário onde o Maker Price 3D guarda banco, autosave e cache."""

from __future__ import annotations

import os
import sys
from pathlib import Path

NOME_PASTA = "MakerPrice3D"


def pasta_dados() -> Path:
    """Pasta de dados do usuário (criada se não existir).

    * Windows: ``%APPDATA%\\MakerPrice3D``
    * macOS: ``~/Library/Application Support/MakerPrice3D``
    * Linux: ``$XDG_DATA_HOME/MakerPrice3D`` ou ``~/.local/share/MakerPrice3D``

    A variável de ambiente ``MP3D_DATA_DIR`` sobrescreve o local (útil em testes).
    """
    forcada = os.environ.get("MP3D_DATA_DIR")
    if forcada:
        base = Path(forcada)
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / NOME_PASTA
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / NOME_PASTA
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / NOME_PASTA
    base.mkdir(parents=True, exist_ok=True)
    return base


def pasta_autosave() -> Path:
    """Subpasta para salvamentos automáticos/recuperação."""
    pasta = pasta_dados() / "autosave"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def caminho_banco() -> Path:
    """Arquivo SQLite com perfis, biblioteca de resinas e configurações."""
    return pasta_dados() / "makerprice3d.db"


def pasta_assets() -> Path:
    """Pasta ``assets`` (funciona no código-fonte e em executáveis PyInstaller)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / "assets"
