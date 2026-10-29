# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from decimal import Decimal

import pytest

from makerprice3d.core.energia import calcular_consumo


def test_consumo_como_v1():
    r = calcular_consumo(Decimal(60), Decimal(120), Decimal(30), Decimal("0.80"))
    assert r.consumo_dia_kwh == Decimal("0.12")
    assert r.consumo_mes_kwh == Decimal("3.6")
    assert r.custo_dia == Decimal("0.096")
    assert r.custo_mes == Decimal("2.88")


def test_negativo_falha():
    with pytest.raises(ValueError):
        calcular_consumo(Decimal(-1), Decimal(1), Decimal(1), Decimal(1))
