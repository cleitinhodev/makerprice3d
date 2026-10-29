# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Gera ``dist/MakerPrice3D.exe`` e o zip ``dist/MakerPrice3D-v<versão>-windows.zip``.

Uso (Windows, na raiz do repositório)::

    pip install -r requirements-build.txt
    python empacotamento/gerar_executavel.py
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from makerprice3d import __version__  # noqa: E402


def main() -> int:
    spec = RAIZ / "empacotamento" / "MakerPrice3D.spec"
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec)],
        cwd=RAIZ,
        check=True,
    )
    dist = RAIZ / "dist"
    exe = dist / ("MakerPrice3D.exe" if sys.platform == "win32" else "MakerPrice3D")
    if not exe.exists():
        print(f"Executável não encontrado: {exe}")
        return 1
    destino = dist / f"MakerPrice3D-v{__version__}-windows.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe, exe.name)
        zf.write(RAIZ / "LICENSE.txt", "LICENSE.txt")
        zf.write(RAIZ / "README.md", "README.md")
    print(f"Pronto: {destino} ({destino.stat().st_size / 1_048_576:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
