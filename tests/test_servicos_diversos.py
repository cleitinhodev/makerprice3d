# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
import csv
import json
import zipfile
from datetime import date
from decimal import Decimal as D

from makerprice3d.core import calculadora as calc
from makerprice3d.core import gestao as g
from makerprice3d.core.projeto import migrar
from makerprice3d.services import backup, caminhos, cotacao, exportacao


def test_caminhos(tmp_path, monkeypatch):
    monkeypatch.setenv("MP3D_DATA_DIR", str(tmp_path / "dados"))
    assert caminhos.pasta_dados() == tmp_path / "dados"
    assert caminhos.pasta_autosave().is_dir()
    assert caminhos.caminho_banco().name.endswith(".db")
    assert caminhos.pasta_assets().name == "assets"


def test_backup(banco, tmp_path):
    pasta = tmp_path / "bk"
    for _ in range(3):
        backup.fazer_backup(banco, pasta, manter=2)
    assert len(list(pasta.glob("*.db"))) <= 2
    banco.definir_config("ultimo_backup", "")
    assert backup.backup_automatico(banco, pasta) is not None
    assert backup.backup_automatico(banco, pasta) is None
    banco.definir_config("ultimo_backup", "")
    banco.definir_config("backups_manter", "abc")
    assert backup.backup_automatico(banco, pasta) is not None


def test_exportar_tudo(banco, tmp_path):
    banco.inserir("clientes", {"nome": "Ana"})
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    (fotos / "a.png").write_bytes(b"x")
    destino = backup.exportar_tudo(banco, tmp_path / "tudo.zip", fotos)
    with zipfile.ZipFile(destino) as zip_:
        nomes = set(zip_.namelist())
        assert {"makerprice3d.db", "dados.json", "fotos/a.png"} <= nomes
        assert json.loads(zip_.read("dados.json"))["clientes"][0]["nome"] == "Ana"


def test_cotacao_online_cache_e_falha(tmp_path):
    cache = tmp_path / "c" / "cotacao.json"

    def ok(url, timeout):
        return {"date": "2026-10-29", "rates": {"USD": 0.18, "EUR": 0.17, "XYZ": 1}}

    def falha(url, timeout):
        raise OSError("sem rede")

    online = cotacao.buscar_cotacoes(cache, ok)
    assert online.origem == "online"
    assert "XYZ" not in online.taxas
    assert online.converter(D(100), "USD") == D("18.00")
    assert online.converter(D(1), "JPY") is None
    offline = cotacao.buscar_cotacoes(cache, falha)
    assert offline.origem == "cache"
    assert offline.taxas["EUR"] == D("0.17")
    cache.write_text("{ruim", "utf-8")
    assert cotacao.buscar_cotacoes(cache, falha).origem == "indisponível"
    assert cotacao.buscar_cotacoes(None, lambda u, t: {"rates": {}}).origem == "indisponível"


def test_exportacao(tmp_path, projeto_v1):
    proj = migrar(projeto_v1)[0]
    resultado = calc.calcular(proj)
    destino = exportacao.exportar_resultado_csv(tmp_path / "r.csv", proj, resultado)
    with destino.open(encoding="utf-8-sig") as arquivo:
        linhas = list(csv.reader(arquivo, delimiter=";"))
    assert linhas[0] == ["Projeto", "Sem Título"]
    assert ["Material", "15,70"] in linhas
    tabela = exportacao.exportar_tabela_csv(tmp_path / "t.csv", [{"nome": "Ana", "x": None}], ["nome", "x"])
    assert tabela.read_text("utf-8-sig").splitlines() == ["nome;x", "Ana;"]
    itens = [g.ItemOrcamento("Busto <75mm>", 1, D(100), D(40))]
    html = exportacao.html_orcamento(
        7,
        "Loja & Cia",
        "Ana",
        itens,
        g.totais_orcamento(itens, D(10), D(5)),
        date(2026, 1, 1),
        date(2026, 1, 8),
        "7 dias",
        "Pix",
        "Obs",
        "11 99999-0000",
    )
    assert "Busto &lt;75mm&gt;" in html
    assert "Loja &amp; Cia" in html
    assert "R$ 95,00" in html
