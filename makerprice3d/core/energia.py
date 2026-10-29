# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Calculadora de consumo de energia (kWh), a mesma da ferramenta da v1.x."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from makerprice3d.core.numeros import ZERO


@dataclass(frozen=True)
class ConsumoEnergia:
    """Resultado da calculadora de kWh."""

    consumo_dia_kwh: Decimal
    consumo_mes_kwh: Decimal
    custo_dia: Decimal
    custo_mes: Decimal


def calcular_consumo(
    potencia_w: Decimal, minutos_dia: Decimal, dias_mes: Decimal, valor_kwh: Decimal
) -> ConsumoEnergia:
    """Calcula consumo e custo, como na v1.x.

    ``consumo_dia = (potência × minutos/60) / 1000``; ``consumo_mes = consumo_dia × dias``;
    ``custo = consumo × R$/kWh``.

    :raises ValueError: se algum valor for negativo.
    """
    if min(potencia_w, minutos_dia, dias_mes, valor_kwh) < ZERO:
        raise ValueError("Os valores não podem ser negativos.")
    horas = minutos_dia / Decimal(60)
    consumo_dia = (potencia_w * horas) / Decimal(1000)
    consumo_mes = consumo_dia * dias_mes
    return ConsumoEnergia(
        consumo_dia_kwh=consumo_dia,
        consumo_mes_kwh=consumo_mes,
        custo_dia=consumo_dia * valor_kwh,
        custo_mes=consumo_mes * valor_kwh,
    )
