# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from decimal import Decimal as D

import pytest

from makerprice3d.core import precificacao as p


def test_perda_de_resina():
    assert p.perda_de_resina(D(10), D(3), D(2), D(0)) == D("0.5")
    assert p.perda_de_resina(D(10), D(-3), D(0), D(0)) == 0


def test_custo_de_falhas():
    assert p.custo_de_falhas(D(10), D(0)) == 0
    assert p.custo_de_falhas(D(10), D(50)) == D(10)
    # limitado a 95%
    assert p.custo_de_falhas(D(1), D(200)) == p.custo_de_falhas(D(1), D(95))


def test_rateios():
    assert p.rateio_custos_fixos(D(300), D(150), D(3)) == D(6)
    assert p.rateio_custos_fixos(D(300), D(0), D(3)) == 0
    assert p.depreciacao(D(2000), D(4000), D(2)) == D(1)
    assert p.custo_energia_por_potencia(D(1000), D(2), D("0.8")) == D("1.6")
    assert p.preco_por_kg(D(110), D("1.1")) == D(100)
    assert p.rateio_licenca(D(40), D(20)) == D(2)
    assert p.custo_por_peca(D(45), D(50)) == D("0.9")
    assert p.rateio_das_mei(D(75), D(0)) == 0
    assert p.rateio_das_mei(D(75), D(50)) == D("1.5")


def test_lucro_markup_margem():
    assert p.aplicar_lucro(D(100), D(30)) == D(130)
    assert p.aplicar_lucro(D(70), D(30), p.ModoLucro.MARGEM) == D(100)
    assert p.aplicar_lucro(D(5), D(100), p.ModoLucro.MARGEM) == D(100)  # limitado a 95%
    assert p.markup_para_margem(D(25)) == D(20)
    assert p.markup_para_margem(D(-100)) == 0
    assert p.margem_para_markup(D(20)) == D(25)


def test_taxas_e_reverso():
    taxas = p.TaxasVenda(percentual_canal=D(10), fixo_canal=D(5), percentual_impostos=D(10))
    assert taxas.percentual_total == D(20)
    preco = p.preco_com_taxas(D(75), taxas)
    assert preco == D(100)
    assert p.receita_liquida(preco, taxas) == D(75)
    assert p.preco_com_taxas(D(0), p.TaxasVenda()) == 0
    assert p.TaxasVenda(percentual_canal=D(90), percentual_impostos=D(30)).percentual_total == D(95)
    analise = p.preco_reverso(D(100), D(50), taxas)
    assert analise.lucro == D(25)
    assert analise.taxas == D(25)
    assert analise.margem_percentual == D(25)
    assert analise.markup_percentual == D(50)


def test_mesa_e_altura():
    assert p.fator_rateio_mesa(D(20), D(80), D(0)) == D("0.25")
    assert p.fator_rateio_mesa(D(200), D(80), D(0)) == 1
    assert p.fator_rateio_mesa(D(0), D(0), D(4)) == D("0.25")
    assert p.fator_rateio_mesa(D(0), D(0), D(0)) == 1
    assert p.tempo_por_altura(D(50), D("0.05"), D("3.6")) == D(1)
    assert p.tempo_por_altura(D(0), D("0.05"), D(3)) == 0
    assert p.camadas_por_altura(D("10.01"), D("0.05")) == 201
    assert p.camadas_por_altura(D(1), D(0)) == 0


@pytest.mark.parametrize("modo", list(p.ModoLucro))
def test_modo_lucro_valores(modo):
    assert p.ModoLucro(modo.value) is modo
