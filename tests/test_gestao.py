# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from datetime import date
from decimal import Decimal as D

from makerprice3d.core import gestao as g
from makerprice3d.core.projeto import projeto_vazio


def _item(**k):
    base = {"descricao": "Peça", "quantidade": 2, "preco_unitario": D(50), "custo_unitario": D(20)}
    base.update(k)
    return g.ItemOrcamento(**base)


def test_item_ida_e_volta():
    item = _item(produto_id=3, peso_g=D(15), resina_id=1)
    volta = g.item_de_dict(g.item_para_dict(item))
    assert volta == g.ItemOrcamento("Peça", 2, D("50.00"), D("20.00"), 3, D(15), 1)
    assert item.total == D(100)
    assert item.custo_total == D(40)
    assert g.item_de_dict({"quantidade": "0", "produto_id": ""}).quantidade == 1


def test_totais_e_kit():
    t = g.totais_orcamento([_item(), _item(quantidade=1)], D(10), D(15))
    assert t.subtotal == D(150)
    assert t.desconto == D(15)
    assert t.total == D(150)
    assert t.custo == D(60)
    assert t.lucro == D(75)
    assert g.preco_kit([(D(50), 2), (D(30), 1)], D(10)) == (D(130), D(117))


def test_validade_e_vencido():
    emissao = date(2026, 1, 1)
    assert g.validade(emissao, 7) == date(2026, 1, 8)
    assert not g.orcamento_vencido(emissao, 7, date(2026, 1, 8))
    assert g.orcamento_vencido(emissao, 7, date(2026, 1, 9))


def test_whatsapp():
    assert g.normalizar_telefone("(11) 98765-4321") == "5511987654321"
    assert g.normalizar_telefone("+351 912 345 678") == "351912345678"
    texto = g.texto_orcamento(
        5, "Ana", [_item()], g.totais_orcamento([_item()], D(10), D(5)), date(2026, 1, 8), "7 dias", "Pix"
    )
    assert "*Orçamento nº 5*" in texto
    assert "Desconto: -R$ 10,00" in texto
    assert "Frete: R$ 5,00" in texto
    assert "Válido até 08/01/2026" in texto
    link = g.link_whatsapp("11987654321", "Olá mundo")
    assert link == "https://wa.me/5511987654321?text=Ol%C3%A1%20mundo"
    assert g.link_whatsapp("", "x").startswith("https://wa.me/?text=")


def test_status_e_estoque():
    assert g.proximo_status("aguardando") == "imprimindo"
    assert g.proximo_status("entregue") == "entregue"
    assert g.proximo_status("???") == "aguardando"
    assert g.deve_baixar_estoque("aguardando", "imprimindo", False)
    assert not g.deve_baixar_estoque("aguardando", "imprimindo", True)
    assert not g.deve_baixar_estoque("aguardando", "cancelado", False)
    assert not g.deve_baixar_estoque("x", "aguardando", False)


def test_consumo_do_pedido():
    itens = [_item(peso_g=D(30), resina_id=1), _item(quantidade=1, peso_g=D(10), resina_id=2)]
    estoque = [
        {"id": 1, "categoria": "resina", "resina_id": 1},
        {"id": 2, "categoria": "resina", "resina_id": 1},
        {"id": 3, "categoria": "luvas", "consumo_por_peca": "2"},
        {"id": 4, "categoria": "resina", "resina_id": None},
        {"id": 5, "categoria": "ipa", "consumo_por_peca": ""},
    ]
    assert g.consumo_do_pedido(itens, estoque) == {1: D(60), 3: D(6)}
    baixo = g.estoque_baixo([{"quantidade": "1", "minimo": "2"}, {"quantidade": "5", "minimo": "2"}, {"minimo": ""}])
    assert len(baixo) == 1


def test_uso_e_falhas():
    impressoes = [
        {"data": "2026-01-01", "horas": "5", "camadas": "100", "sucesso": True, "impressora_id": 1, "resina_id": 1},
        {
            "data": "2026-02-01",
            "horas": "4",
            "camadas": "50",
            "sucesso": False,
            "motivo_falha": "suportes",
            "impressora_id": 1,
            "resina_id": 2,
        },
        {"data": "2026-03-01", "horas": "6", "camadas": "70", "sucesso": False, "impressora_id": 2, "resina_id": 1},
    ]
    manut = [{"data": "2026-01-15", "tipo": "troca", "peca": "lcd"}]
    lcd = g.uso_desde_troca("lcd", impressoes, manut, D(10))
    assert lcd.horas == D(10)
    assert lcd.camadas == 120
    assert lcd.percentual == D(100)
    assert lcd.alerta and lcd.vencida
    fep = g.uso_desde_troca("fep", impressoes, manut, D(0), "impressoes")
    assert fep.impressoes == 3
    assert not fep.alerta
    taxa = g.taxa_falha_medida(impressoes)
    assert taxa.total == 3
    assert taxa.falhas == 2
    assert taxa.motivos == {"suportes": 1, "outro": 1}
    assert g.taxa_falha_medida(impressoes, impressora_id=1, resina_id=1).percentual == 0
    assert g.taxa_falha_medida([]).percentual == 0


def test_resumo_payback_equilibrio():
    pedidos = [
        {
            "status": "pronto",
            "data_conclusao": "2026-03-10T10:00",
            "total": "100",
            "custo": "40",
            "itens": [g.item_para_dict(_item(peso_g=D(10)))],
        },
        {
            "status": "entregue",
            "data": "2026-03-20",
            "total": "50",
            "custo": "20",
            "itens": [{"descricao": "Busto", "quantidade": 1, "peso_g": "30"}],
        },
        {"status": "aguardando", "data": "2026-03-20", "total": "999"},
        {"status": "pronto", "data_conclusao": "2026-04-01", "total": "999"},
    ]
    r = g.resumo_mensal(pedidos, 2026, 3)
    assert (r.pedidos, r.receita, r.lucro, r.ticket_medio, r.pecas, r.resina_g) == (2, 150, 90, 75, 3, 50)
    assert r.top_pecas[0] == ("Peça", 2)
    vazio = g.resumo_mensal([], 2026, 3)
    assert vazio.ticket_medio == 0
    pb = g.payback(D(1000), D(250), D(5))
    assert pb.percentual_pago == 25
    assert pb.lucro_mensal_medio == 50
    assert pb.meses_restantes == 15
    assert not pb.quitado
    assert g.payback(D(100), D(200), D(1)).quitado
    assert g.payback(D(100), D(0), D(0)).meses_restantes is None
    assert g.ponto_de_equilibrio(D(300), D(50), D(20)) == 10
    assert g.ponto_de_equilibrio(D(300), D(20), D(20)) is None


def test_cenarios():
    proj = projeto_vazio()
    proj["material"].update({"resina": "100", "peso": "100"})
    proj["energia"]["impressao"] = "1"
    novo = g.aplicar_cenario(proj, {"resina": D(20), "tarifa": D(-50), "frete": D(10), "inexistente": D(5)})
    assert novo["material"]["resina"] == "120"
    assert novo["energia"]["impressao"] == "0.5"
    assert novo["logistica"]["frete"] == ""  # campos vazios continuam vazios
    assert proj["material"]["resina"] == "100"
    atual, cenario = g.simular(proj, {"resina": D(20)})
    assert cenario.total_gasto - atual.total_gasto == D(2)
