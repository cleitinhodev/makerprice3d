# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from makerprice3d.core import gestao as g
from makerprice3d.core.projeto import projeto_vazio
from makerprice3d.services import negocio as n


@pytest.fixture
def loja(banco):
    resina = banco.inserir("resinas", {"nome": "ABS-like", "preco_litro": "150"})
    impressora = banco.inserir(
        "impressoras",
        {
            "nome": "Saturn",
            "preco": "3000",
            "vida_lcd_h": "10",
            "durabilidade_fep": "2",
            "data_compra": (date.today() - timedelta(days=61)).isoformat(),
        },
    )
    proj = projeto_vazio()
    proj["material"].update({"resina": "150", "peso": "40"})
    proj["desgaste"]["tempo_total"] = "3"
    proj["lucro"]["estado"] = 100
    proj["perfil"].update({"resina_id": resina, "impressora_id": impressora})
    produto = n.salvar_no_catalogo(banco, proj, "Dragão", "32mm")
    return banco, resina, impressora, produto


def test_catalogo_e_kit(loja, tmp_path):
    banco, resina, impressora, produto_id = loja
    produto = banco.obter("produtos", produto_id)
    assert produto["preco"] == "12.00"
    assert produto["custo"] == "6.00"
    assert produto["tempo_h"] == "3.00"
    assert produto["resina_id"] == resina
    assert produto["projeto"]["material"]["peso"] == "40"
    item = n.item_de_produto(produto, 2)
    assert item.descricao == "Dragão (32mm)"
    assert item.total == D(24)
    kit = {
        "nome": "Combo",
        "desconto_percentual": "10",
        "itens": [{"produto_id": produto_id, "quantidade": 2}, {"produto_id": 999}],
    }
    itens = n.itens_de_kit(banco, kit)
    assert len(itens) == 1
    assert itens[0].preco_unitario == D("10.80")
    assert "[kit Combo]" in itens[0].descricao
    assert n.preco_do_kit(banco, kit) == (D(24), D("21.60"))
    foto = tmp_path / "foto.png"
    foto.write_bytes(b"png")
    outro = n.salvar_no_catalogo(banco, projeto_vazio(), "Com foto", foto=str(foto), pasta_fotos=tmp_path / "fotos")
    copiada = banco.obter("produtos", outro)["foto"]
    assert copiada != str(foto)
    assert (tmp_path / "fotos").exists()


def test_fluxo_orcamento_pedido_estoque(loja):
    banco, resina, impressora, produto_id = loja
    est_resina = banco.inserir(
        "estoque", {"nome": "ABS", "categoria": "resina", "quantidade": "100", "minimo": "50", "resina_id": resina}
    )
    est_luva = banco.inserir(
        "estoque", {"nome": "Luvas", "categoria": "luvas", "quantidade": "10", "consumo_por_peca": "1"}
    )
    item = n.item_de_produto(banco.obter("produtos", produto_id), 2)
    orc = banco.inserir(
        "orcamentos",
        {
            "data": "2026-03-01",
            "validade_dias": "7",
            "desconto_percentual": "0",
            "frete": "5",
            "itens": [g.item_para_dict(item)],
            "status": "aprovado",
        },
    )
    totais = n.totais_do_orcamento(banco.obter("orcamentos", orc))
    assert totais.total == D(29)
    assert n.data_do_registro(banco.obter("orcamentos", orc)) == date(2026, 3, 1)
    assert n.data_do_registro({"data": "x"}) == date.today()
    pid = n.converter_em_pedido(banco, orc)
    assert n.converter_em_pedido(banco, orc) == pid
    assert banco.obter("orcamentos", orc)["status"] == "convertido"
    pedido = banco.obter("pedidos", pid)
    assert pedido["status"] == "aguardando"
    assert pedido["total"] == "29.00"
    banco.atualizar("pedidos", pid, {"impressora_id": impressora})
    consumo = n.mudar_status_pedido(banco, pid, "imprimindo")
    assert consumo == {est_resina: D(80), est_luva: D(2)}
    assert banco.obter("estoque", est_resina)["quantidade"] == "20.00"
    assert n.mudar_status_pedido(banco, pid, "lavando") == {}
    n.mudar_status_pedido(banco, pid, "pronto")
    assert banco.obter("pedidos", pid)["data_conclusao"]
    assert len(banco.listar("movimentos_estoque")) == 2
    assert g.estoque_baixo(banco.listar("estoque"))[0]["id"] == est_resina
    n.ajustar_estoque(banco, est_resina, D(1000), "Compra")
    assert banco.obter("estoque", est_resina)["quantidade"] == "1020.00"
    hoje = date.today()
    resumo = n.resumo_do_mes(banco, hoje.year, hoje.month)
    assert resumo.pedidos == 1
    assert resumo.receita == D(29)
    pb = n.payback_impressoras(banco)
    assert pb[0][1].lucro_acumulado == D(17)
    assert pb[0][1].lucro_mensal_medio > 0
    assert n.ponto_equilibrio_mensal(banco) is not None
    with pytest.raises(ValueError):
        n.converter_em_pedido(banco, 999)
    with pytest.raises(ValueError):
        n.mudar_status_pedido(banco, 999, "pronto")
    with pytest.raises(ValueError):
        n.ajustar_estoque(banco, 999, D(1), "x")


def test_equipamentos(loja):
    banco, resina, impressora, _ = loja
    assert n.ponto_equilibrio_mensal(banco) is None
    banco.inserir_varios(
        "impressoes",
        [
            {"impressora_id": impressora, "resina_id": resina, "data": f"2026-01-0{i}", "horas": "4", "sucesso": True}
            for i in range(1, 4)
        ],
    )
    uso = n.uso_da_impressora(banco, impressora)
    assert uso["lcd"].horas == D(12)
    assert uso["fep"].impressoes == 3
    alertas = n.alertas_de_troca(banco)
    assert any("LCD passou" in a for a in alertas)
    assert any("FEP" in a for a in alertas)
    banco.inserir(
        "manutencoes", {"impressora_id": impressora, "data": "2026-01-03T23:59", "tipo": "troca", "peca": "lcd"}
    )
    assert n.uso_da_impressora(banco, impressora)["lcd"].horas == 0
    banco.atualizar("impressoras", impressora, {"data_compra": "inválida"})
    assert n.payback_impressoras(banco)[0][1].lucro_mensal_medio == 0
