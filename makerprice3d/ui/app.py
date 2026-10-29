# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Ponto de entrada da interface gráfica."""

from __future__ import annotations

import sys

from PySide6.QtCore import QLocale
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from makerprice3d import __app_name__, __version__


def main(argv: list[str] | None = None) -> int:
    """Abre o Maker Price 3D. Aceita um arquivo .mp3d/.json como argumento."""
    argv = list(sys.argv if argv is None else argv)
    QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("CleitinhoDEV")
    fonte = QFont("Segoe UI")
    fonte.setPointSize(10)
    app.setFont(fonte)

    from makerprice3d.ui.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal()
    janela.show()
    arquivos = [a for a in argv[1:] if a.lower().endswith((".mp3d", ".json"))]
    if arquivos:
        janela.abrir(arquivos[0])
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
