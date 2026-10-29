# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from decimal import Decimal as D

from makerprice3d.core import calculadora as calc
from makerprice3d.core.projeto import definir_valor, migrar, projeto_vazio


def _projeto(**valores):
    proj = projeto_vazio()
    for chave, valor in valores.items():
        definir_valor(proj, chave.replace("__", "."), valor)
    return proj


def test_projeto_vazio_zera():
    r = calc.calcular(projeto_vazio())
    assert r.total_gasto == 0
    assert r.preco_sugerido == 0
    assert r.quantidade == 1
    assert r.analise_reversa is None
    assert all(v >= 0 for _, v in r.valores_grafico())


def test_categorias_cobrem_subtotais(projeto_v1):
    r = calc.calcular(migrar(projeto_v1)[0])
    chaves = {c.chave for c in calc.CATEGORIAS}
    assert set(r.subtotais) <= chaves
    assert len(r.valores_grafico()) == len(calc.CATEGORIAS) + 2  # + lucro e taxas


def test_mesa_rateia_energia_e_desgaste():
    base = {
        "material__peso": "20",
        "energia__impressao": "1",
        "desgaste__preco_lcd": "1000",
        "desgaste__vida_util": "1000",
        "desgaste__tempo_total": "4",
        "desgaste__preco_fep": "0",
        "desgaste__durabilidade": "1",
        "desgaste__porcentagem_area": "0",
    }
    sozinha = calc.calcular(_projeto(**base))
    dividida = calc.calcular(_projeto(**base, mesa__peso_total_mesa="80"))
    assert sozinha.subtotais["energia"] == D(1)
    assert dividida.subtotais["energia"] == D("0.25")
    assert dividida.subtotais["desgaste"] == D(1)
    assert calc.horas_impressao(_projeto(**base, mesa__pecas_na_mesa="2")) == D(2)


def test_novos_custos():
    proj = _projeto(
        material__resina="100",
        material__peso="100",
        perdas__tanque="5",
        perdas__taxa_falha="50",
        desgaste__tempo_total="2",
        custos_fixos__mensal="300",
        custos_fixos__horas_maquina_mes="100",
        custos_fixos__preco_impressora="2000",
        custos_fixos__vida_util_impressora="1000",
        extras__licenca_custo="40",
        extras__licenca_vendas_previstas="20",
        extras__luvas_custo="10",
        extras__luvas_pecas="10",
        extras__papel_por_peca="0.5",
        extras__clima_potencia_w="1000",
        extras__clima_horas="2",
        extras__tarifa_kwh="1",
        tributos__regime="mei",
        tributos__das_mensal="75",
        tributos__vendas_mes="25",
        venda__impostos_percentual="10",
    )
    r = calc.calcular(proj)
    s = r.subtotais
    assert s["material"] == D(10)
    assert s["perdas_resina"] == D("0.5")
    assert s["falhas"] == D("10.5")
    assert s["custos_fixos"] == D(6)
    assert s["depreciacao"] == D(4)
    assert s["licenca"] == D(2)
    assert s["epi"] == D("1.5")
    assert s["climatizacao"] == D(2)
    assert s["das_mei"] == D(3)
    # no MEI o imposto % não se aplica
    assert r.taxas.percentual_impostos == 0


def test_taxa_falha_limitada_gera_aviso():
    r = calc.calcular(_projeto(material__resina="100", material__peso="10", perdas__taxa_falha="99"))
    assert any("95%" in a for a in r.avisos)


def test_precos_e_taxas():
    proj = _projeto(mao_de_obra__ganho_por_hora="100", mao_de_obra__horas_trabalhadas="1")
    proj["lucro"]["estado"] = 25
    proj["venda"]["taxa_percentual"] = "20"
    proj["venda"]["acrescimo_premium"] = "25"
    proj["meta"]["quantidade"] = "3"
    proj["venda"]["preco_alvo"] = "200"
    r = calc.calcular(proj)
    assert r.total_absoluto == D(125)
    assert r.preco_minimo == D(125)
    assert r.preco_sugerido == D("156.25")
    assert r.preco_premium == D("187.5")
    assert r.taxas_valor == D("31.25")
    assert r.margem_percentual == D(20)
    assert r.total_pedido == D("468.75")
    assert r.analise_reversa is not None
    assert r.analise_reversa.lucro == D(60)


def test_modo_margem():
    proj = _projeto(mao_de_obra__ganho_por_hora="80", mao_de_obra__horas_trabalhadas="1")
    proj["lucro"] = {"estado": 20, "modo": "margem"}
    r = calc.calcular(proj)
    assert r.total_absoluto == D(100)
    assert r.total_ganho == D(20)
    assert r.markup_percentual == D(25)
    assert r.sugestao[0] == "Ideal"


def test_modo_invalido_vira_markup():
    proj = projeto_vazio()
    proj["lucro"]["modo"] = "xyz"
    assert calc.calcular(proj).modo_lucro.value == "markup"


def test_taxas_acima_de_95_avisam():
    proj = _projeto(mao_de_obra__ganho_por_hora="10", mao_de_obra__horas_trabalhadas="1")
    proj["venda"]["taxa_percentual"] = "90"
    proj["venda"]["impostos_percentual"] = "20"
    assert any("95%" in a for a in calc.calcular(proj).avisos)
