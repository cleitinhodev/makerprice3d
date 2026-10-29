# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from decimal import Decimal

import pytest

from makerprice3d.core import numeros as n


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("12,5", "12.5"),
        ("12.5", "12.5"),
        ("R$ 3,40", "3.40"),
        ("1.234,56", "1234.56"),
        ("1,234.56", "1234.56"),
        ("10%", "10"),
        (7, "7"),
        (2.5, "2.5"),
        (Decimal("3"), "3"),
    ],
)
def test_para_decimal(entrada, esperado):
    assert n.para_decimal(entrada) == Decimal(esperado)


@pytest.mark.parametrize("entrada", [None, "", "abc", "   ", True, Decimal("NaN"), "inf"])
def test_para_decimal_padrao(entrada):
    assert n.para_decimal(entrada, Decimal(9)) == Decimal(9)


def test_texto_valido():
    assert n.texto_valido("")
    assert n.texto_valido(None)
    assert n.texto_valido("3,5")
    assert not n.texto_valido("3,5a")


def test_utilitarios():
    assert n.esta_vazio(" ")
    assert not n.esta_vazio("0")
    assert n.arredondar(Decimal("2.345")) == Decimal("2.35")
    assert n.nao_negativo(Decimal(-1)) == 0
    assert n.dividir(Decimal(1), Decimal(0), Decimal(5)) == 5
    assert n.dividir(Decimal(1), Decimal(4)) == Decimal("0.25")


def test_formatacao():
    assert n.formatar_moeda(Decimal("1234567.891")) == "R$ 1.234.567,89"
    assert n.formatar_moeda(Decimal("-5")) == "-R$ 5,00"
    assert n.formatar_moeda(Decimal("0.5"), "US$") == "US$ 0,50"
    assert n.formatar_numero(Decimal("2.5")) == "2,50"
    assert n.formatar_percentual(Decimal("12.345")) == "12,3%"
