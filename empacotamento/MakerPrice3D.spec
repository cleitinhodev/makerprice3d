# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
# -*- mode: python ; coding: utf-8 -*-
"""Receita do PyInstaller: gera um único MakerPrice3D.exe (janela, sem console).

Uso (na raiz do repositório):  pyinstaller --noconfirm --clean empacotamento/MakerPrice3D.spec
"""

from pathlib import Path

RAIZ = Path(SPECPATH).parent  # noqa: F821 - SPECPATH é definido pelo PyInstaller
PASTA = Path(SPECPATH)  # noqa: F821

# Módulos do Qt que o programa não usa (deixa o executável menor).
EXCLUIR = [
    "tkinter",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtMultimedia",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtBluetooth",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtDesigner",
    "pytest",
]

a = Analysis(  # noqa: F821
    [str(RAIZ / "main.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=[
        (str(RAIZ / "assets"), "assets"),
        (str(RAIZ / "LICENSE.txt"), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUIR,
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MakerPrice3D",
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon=str(RAIZ / "assets" / "favicon.ico"),
    version=str(PASTA / "versao_windows.txt"),
)
