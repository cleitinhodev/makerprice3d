# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
import sqlite3

import pytest

from makerprice3d.services import banco as bd


def test_config_e_padroes(banco):
    assert banco.config("margem_padrao") == "30"
    assert banco.config("nao_existe", "x") == "x"
    banco.definir_config("tarifa_kwh", 0.95)
    assert banco.config("tarifa_kwh") == "0.95"
    assert "tema" in banco.todas_configs()
    canais = banco.listar("canais")
    assert canais[0]["nome"] == "Venda direta"
    assert any("exemplo" in c["nome"] for c in canais)


def test_recentes(banco, tmp_path):
    for i in range(bd.MAX_RECENTES + 3):
        banco.adicionar_recente(tmp_path / f"{i}.mp3d")
    recentes = banco.recentes()
    assert len(recentes) == bd.MAX_RECENTES
    assert recentes[0].endswith(f"{bd.MAX_RECENTES + 2}.mp3d")
    banco.adicionar_recente(tmp_path / "5.mp3d")
    assert banco.recentes()[0].endswith("5.mp3d")
    assert len(banco.recentes()) == bd.MAX_RECENTES
    banco.remover_recente(tmp_path / "5.mp3d")
    assert not any(r.endswith("5.mp3d") for r in banco.recentes())
    banco.definir_config("recentes", "lixo")
    assert banco.recentes() == []


def test_crud_e_json(banco):
    cid = banco.inserir("clientes", {"nome": "Ana", "telefone": "11999990000", "ignorada": 1})
    pid = banco.inserir(
        "pedidos", {"cliente_id": cid, "itens": [{"descricao": "x", "quantidade": 1}], "estoque_baixado": True}
    )
    pedido = banco.obter("pedidos", pid)
    assert pedido["cliente_id"] == cid
    assert pedido["itens"][0]["descricao"] == "x"
    assert pedido["estoque_baixado"] is True
    banco.atualizar("pedidos", pid, {"status": "pronto"})
    assert banco.listar("pedidos", status="pronto")[0]["id"] == pid
    assert banco.listar("pedidos", status="outro") == []
    banco.excluir("pedidos", pid)
    assert banco.obter("pedidos", pid) is None
    ids = banco.inserir_varios("clientes", [{"nome": "Bia"}, {"nome": "Caio"}])
    assert len(ids) == 2
    assert [c["nome"] for c in banco.listar("clientes")] == ["Ana", "Bia", "Caio"]
    tudo = banco.exportar_tudo()
    assert len(tudo["clientes"]) == 3
    with pytest.raises(KeyError):
        banco.listar("nao_existe")


def test_backup_para(banco, tmp_path):
    banco.inserir("clientes", {"nome": "Ana"})
    destino = banco.backup_para(tmp_path / "copia" / "b.db")
    con = sqlite3.connect(destino)
    assert con.execute("SELECT nome FROM clientes").fetchone()[0] == "Ana"
    con.close()


def test_reabrir_mantem_dados(tmp_path):
    caminho = tmp_path / "x.db"
    b = bd.Banco(caminho)
    b.inserir("resinas", {"nome": "ABS-like", "preco_litro": "150"})
    b.fechar()
    b2 = bd.Banco(caminho)
    assert b2.listar("resinas")[0]["nome"] == "ABS-like"
    assert len(b2.listar("canais")) == len(bd.CANAIS_PADRAO)
    b2.fechar()
