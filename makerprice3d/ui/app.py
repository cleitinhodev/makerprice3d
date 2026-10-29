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
    """Abre o Maker Price 3D. Aceita um arquivo .mp3d/.json como argumento.

    Com ``--smoke-test`` a janela principal é montada, todas as páginas são visitadas
    e o programa sai com código 0 sem abrir o laço de eventos (usado no CI do executável).
    """
    argv = list(sys.argv if argv is None else argv)
    teste_rapido = "--smoke-test" in argv
    argv = [a for a in argv if a != "--smoke-test"]
    QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("CleitinhoDEV")
    fonte = QFont("Segoe UI")
    fonte.setPointSize(10)
    app.setFont(fonte)

    from makerprice3d.ui.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(recuperar_autosave=not teste_rapido)
    janela.show()
    if teste_rapido:
        return _teste_rapido(app, janela)
    arquivos = [a for a in argv[1:] if a.lower().endswith((".mp3d", ".json"))]
    if arquivos:
        janela.abrir(arquivos[0])
    return app.exec()


def _teste_rapido(app: QApplication, janela) -> int:
    """Visita todas as páginas, alterna o tema e fecha sem perguntar nada."""
    for chave, _rotulo in janela.PAGINAS:
        janela.ir_para(chave)
        app.processEvents()
    janela.alternar_tema()
    janela.alternar_tema()
    app.processEvents()
    janela.setWindowModified(False)
    janela.close()
    app.processEvents()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
