# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Geração de PDF a partir de HTML usando o próprio Qt (sem dependências extras)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument


def html_para_pdf(html: str, destino: str | Path) -> Path:
    """Grava ``html`` como PDF A4."""
    destino = Path(destino)
    if destino.suffix.lower() != ".pdf":
        destino = destino.with_suffix(".pdf")
    escritor = QPdfWriter(str(destino))
    escritor.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    escritor.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)
    escritor.setResolution(96)
    documento = QTextDocument()
    documento.setHtml(html)
    layout = escritor.pageLayout()
    area = layout.paintRectPixels(escritor.resolution())
    documento.setPageSize(QSizeF(area.width(), area.height()))
    documento.print_(escritor)
    return destino
