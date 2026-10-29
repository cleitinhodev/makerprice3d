# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Temas claro e escuro (QSS) do Maker Price 3D."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Paleta:
    """Cores de um tema."""

    nome: str
    fundo: str
    superficie: str
    superficie_alt: str
    borda: str
    texto: str
    texto_suave: str
    destaque: str
    destaque_hover: str
    erro: str
    sucesso: str
    aviso: str


ESCURO = Paleta(
    nome="escuro",
    fundo="#0f1115",
    superficie="#171a21",
    superficie_alt="#1f232c",
    borda="#2a2f3a",
    texto="#e7e9ee",
    texto_suave="#9aa3b2",
    destaque="#7c5cff",
    destaque_hover="#9479ff",
    erro="#ff5c6c",
    sucesso="#3ddc84",
    aviso="#ffb020",
)

CLARO = Paleta(
    nome="claro",
    fundo="#f3f4f8",
    superficie="#ffffff",
    superficie_alt="#f6f7fb",
    borda="#dfe3ea",
    texto="#1b1f29",
    texto_suave="#5d6676",
    destaque="#6c4cf0",
    destaque_hover="#7f63f5",
    erro="#d93a4a",
    sucesso="#1f9d55",
    aviso="#c27c00",
)

TEMAS = {"escuro": ESCURO, "claro": CLARO}


def paleta(nome: str) -> Paleta:
    """Paleta pelo nome (padrão: escuro)."""
    return TEMAS.get(nome, ESCURO)


def folha_de_estilo(p: Paleta) -> str:
    """Gera o QSS completo do tema."""
    return f"""
* {{ font-family: "Segoe UI", "Inter", "Noto Sans", Arial; font-size: 10pt; }}
QMainWindow, QDialog, QWidget#fundo {{ background: {p.fundo}; color: {p.texto}; }}
QWidget {{ color: {p.texto}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QFrame#card {{ background: {p.superficie}; border: 1px solid {p.borda}; border-radius: 14px; }}
QFrame#cardResumo {{ background: {p.superficie}; border: 1px solid {p.borda}; border-radius: 16px; }}
QLabel#tituloCard {{ font-size: 12pt; font-weight: 600; }}
QLabel#subtituloCard, QLabel#suave {{ color: {p.texto_suave}; }}
QLabel#rotuloCampo {{ color: {p.texto_suave}; font-size: 9pt; }}
QLabel#selo {{ border-radius: 8px; padding: 4px 10px; font-weight: 700; }}
QLabel#novo {{ background: {p.destaque}; color: white; border-radius: 6px; padding: 1px 6px; font-size: 8pt; font-weight: 700; }}
QLabel#totalGrande {{ font-size: 30pt; font-weight: 700; color: {p.texto}; }}
QLabel#metricaValor {{ font-size: 14pt; font-weight: 700; }}
QLabel#alerta {{ background: {p.aviso}22; border: 1px solid {p.aviso}; border-radius: 8px; padding: 6px 10px; color: {p.texto}; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QPlainTextEdit, QTextEdit {{
    background: {p.superficie_alt}; border: 1px solid {p.borda}; border-radius: 8px;
    padding: 6px 8px; selection-background-color: {p.destaque};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {p.destaque}; }}
QLineEdit[invalido="true"] {{ border: 1px solid {p.erro}; background: {p.erro}18; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {p.superficie}; border: 1px solid {p.borda}; selection-background-color: {p.destaque}; }}
QPushButton {{
    background: {p.superficie_alt}; border: 1px solid {p.borda}; border-radius: 8px; padding: 7px 14px;
}}
QPushButton:hover {{ border-color: {p.destaque}; }}
QPushButton:disabled {{ color: {p.texto_suave}; }}
QPushButton#primario {{ background: {p.destaque}; color: white; border: none; font-weight: 600; }}
QPushButton#primario:hover {{ background: {p.destaque_hover}; }}
QPushButton#perigo {{ color: {p.erro}; }}
QPushButton#navegacao {{
    background: transparent; border: none; border-radius: 10px; padding: 10px 14px; text-align: left; font-size: 10.5pt;
}}
QPushButton#navegacao:hover {{ background: {p.superficie_alt}; }}
QPushButton#navegacao:checked {{ background: {p.destaque}; color: white; font-weight: 600; }}
QWidget#barraLateral {{ background: {p.superficie}; border-right: 1px solid {p.borda}; }}
QLabel#marca {{ font-size: 15pt; font-weight: 800; color: {p.destaque}; }}
QTabWidget::pane {{ border: 1px solid {p.borda}; border-radius: 10px; top: -1px; background: {p.superficie}; }}
QTabBar::tab {{ background: transparent; padding: 6px 14px; color: {p.texto_suave}; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {p.texto}; border-bottom: 2px solid {p.destaque}; }}
QTableWidget, QTableView, QListWidget {{
    background: {p.superficie}; alternate-background-color: {p.superficie_alt}; border: 1px solid {p.borda};
    border-radius: 10px; gridline-color: {p.borda}; selection-background-color: {p.destaque}; selection-color: white;
}}
QHeaderView::section {{ background: {p.superficie_alt}; color: {p.texto_suave}; border: none; border-bottom: 1px solid {p.borda}; padding: 6px; font-weight: 600; }}
QSlider::groove:horizontal {{ height: 6px; background: {p.borda}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: #ff4c9d; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: #ff4c9d; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }}
QMenuBar {{ background: {p.superficie}; border-bottom: 1px solid {p.borda}; }}
QMenuBar::item {{ padding: 6px 10px; background: transparent; }}
QMenuBar::item:selected {{ background: {p.superficie_alt}; border-radius: 6px; }}
QMenu {{ background: {p.superficie}; border: 1px solid {p.borda}; padding: 4px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: {p.destaque}; color: white; }}
QStatusBar {{ background: {p.superficie}; color: {p.texto_suave}; border-top: 1px solid {p.borda}; }}
QToolTip {{ background: {p.superficie}; color: {p.texto}; border: 1px solid {p.borda}; padding: 6px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {p.borda}; border-radius: 5px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {p.borda}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
QGroupBox {{ border: 1px solid {p.borda}; border-radius: 10px; margin-top: 14px; padding-top: 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {p.texto_suave}; }}
"""
