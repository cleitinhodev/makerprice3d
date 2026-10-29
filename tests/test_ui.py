# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Teste de fumaça da interface (headless, QT_QPA_PLATFORM=offscreen)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")


@pytest.fixture
def janela(tmp_path, monkeypatch):
    monkeypatch.setenv("MP3D_DATA_DIR", str(tmp_path))
    from PySide6.QtWidgets import QApplication

    from makerprice3d.ui.janela_principal import JanelaPrincipal

    app = QApplication.instance() or QApplication([])
    j = JanelaPrincipal(recuperar_autosave=False)
    j.show()
    app.processEvents()
    yield j, app
    j.setWindowModified(False)
    j.close()


def test_calcula_na_interface(janela):
    j, app = janela
    c = j.calculadora
    for chave, valor in {
        "material.resina": "150",
        "material.suporte": "10",
        "material.peso": "80",
        "desgaste.preco_lcd": "600",
        "desgaste.vida_util": "2000",
        "desgaste.tempo_total": "5",
        "desgaste.preco_fep": "60",
        "desgaste.durabilidade": "30",
    }.items():
        c.campos[chave].setText(valor)
    app.processEvents()
    assert c.projeto["material"]["resina"] == "150"
    assert c.resultado.total_gasto > 0
    c.campos["material.peso"].setText("12abc")
    assert "material.peso" in c.campos_invalidos()


def test_paginas_e_tema(janela):
    j, app = janela
    for chave, _ in j.PAGINAS:
        j.ir_para(chave)
        app.processEvents()
    tema = j.contexto.tema
    j.alternar_tema()
    assert j.contexto.tema != tema
    assert not j.grab().isNull()


def test_salvar_e_abrir(janela, tmp_path):
    j, _ = janela
    j.calculadora.campos["material.peso"].setText("33")
    destino = tmp_path / "peca.mp3d"
    assert j._gravar(destino)
    assert destino.exists()
    assert not j.isWindowModified()
    j.novo_projeto(perguntar=False)
    assert j.calculadora.projeto["material"]["peso"] == ""
    j.abrir(destino)
    assert j.calculadora.projeto["material"]["peso"] == "33"
    assert str(destino) in j.contexto.banco.recentes()[0]
