# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Objetos compartilhados entre as telas (banco, pastas, tema e avisos de mudança)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from makerprice3d.core.numeros import para_decimal
from makerprice3d.services import caminhos
from makerprice3d.services.banco import Banco


class Contexto(QObject):
    """Estado global da aplicação."""

    #: Emite o nome da tabela alterada ("" = várias/configurações).
    dados_alterados = Signal(str)
    tema_alterado = Signal(str)

    def __init__(self, banco: Banco | None = None, pasta_dados: Path | None = None) -> None:
        super().__init__()
        self.pasta_dados = pasta_dados or caminhos.pasta_dados()
        self.banco = banco or Banco(self.pasta_dados / "makerprice3d.db")
        self.pasta_fotos = self.pasta_dados / "fotos"
        self.pasta_backups = self.pasta_dados / "backups"
        self.pasta_autosave = self.pasta_dados / "autosave"
        self.cache_cotacao = self.pasta_dados / "cotacao.json"

    @property
    def tema(self) -> str:
        """Nome do tema atual."""
        return self.banco.config("tema") or "escuro"

    def avisar(self, tabela: str = "") -> None:
        """Avisa as telas que os dados mudaram."""
        self.dados_alterados.emit(tabela)

    def config_decimal(self, chave: str):
        """Configuração numérica."""
        return para_decimal(self.banco.config(chave))
