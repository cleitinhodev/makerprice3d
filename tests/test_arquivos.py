# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
import json

import pytest

from makerprice3d.core.projeto import SCHEMA_VERSION, ProjetoInvalidoError, projeto_vazio
from makerprice3d.services import arquivos as a


def test_salvar_e_abrir(tmp_path):
    proj = projeto_vazio()
    proj["meta"]["nome"] = "Busto"
    destino = a.salvar_projeto(proj, tmp_path / "peca.txt")
    assert destino.suffix == ".mp3d"
    dados = json.loads(destino.read_text("utf-8"))
    assert dados["schema_version"] == SCHEMA_VERSION
    carregado = a.abrir_projeto(destino)
    assert carregado.projeto["meta"]["nome"] == "Busto"
    assert not carregado.migrado
    assert not carregado.sugerir_salvar_como


def test_backup_ao_sobrescrever(tmp_path):
    destino = tmp_path / "p.mp3d"
    a.escrever_json_atomico(destino, {"v": 1})
    assert not (tmp_path / "p.mp3d.bak").exists()
    a.escrever_json_atomico(destino, {"v": 2})
    assert json.loads((tmp_path / "p.mp3d.bak").read_text("utf-8")) == {"v": 1}
    assert json.loads(destino.read_text("utf-8")) == {"v": 2}
    assert not list(tmp_path.glob("*.tmp"))


def test_escrita_atomica_nao_corrompe(tmp_path):
    destino = tmp_path / "p.mp3d"
    a.escrever_json_atomico(destino, {"v": 1})
    with pytest.raises(TypeError):
        a.escrever_json_atomico(destino, {"v": object()})
    assert json.loads(destino.read_text("utf-8")) == {"v": 1}
    assert not list(tmp_path.glob(".*.tmp"))


def test_abrir_v1_json(tmp_path, projeto_v1):
    arquivo = tmp_path / "antigo.json"
    arquivo.write_text(json.dumps(projeto_v1), "utf-8")
    carregado = a.abrir_projeto(arquivo)
    assert carregado.migrado
    assert carregado.sugerir_salvar_como
    assert carregado.projeto["material"]["peso"] == "80"


def test_abrir_invalido(tmp_path):
    arquivo = tmp_path / "ruim.mp3d"
    arquivo.write_text("{ quebrado", "utf-8")
    with pytest.raises(ProjetoInvalidoError):
        a.abrir_projeto(arquivo)


def test_autosave(tmp_path):
    anterior = a.Autosave(tmp_path)
    proj = projeto_vazio()
    proj["meta"]["nome"] = "Recuperar"
    anterior.gravar(proj, tmp_path / "x.mp3d")
    atual = a.Autosave(tmp_path)
    atual.gravar(projeto_vazio(), None)
    pendentes = atual.pendentes()
    assert pendentes == [anterior.caminho]
    recuperado, original = a.Autosave.ler(pendentes[0])
    assert recuperado["meta"]["nome"] == "Recuperar"
    assert original.endswith("x.mp3d")
    a.Autosave.descartar(pendentes[0])
    a.Autosave.descartar(pendentes[0])
    atual.limpar()
    atual.limpar()
    assert atual.pendentes() == []
    invalido = tmp_path / "z.mp3d.autosave"
    invalido.write_text("[]", "utf-8")
    with pytest.raises(ProjetoInvalidoError):
        a.Autosave.ler(invalido)
