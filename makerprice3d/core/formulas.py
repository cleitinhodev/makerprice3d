# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Fórmulas originais do Maker Price 3D (v1.x), agora em ``Decimal`` e sem interface.

Cada função reproduz *exatamente* a fórmula da versão 1.x, que nasceu da experiência
real do autor com impressão em resina. As únicas mudanças intencionais são:

* o antigo teto de ``R$ 9.999,99`` foi removido (o piso em zero foi mantido);
* os cálculos usam ``Decimal`` em vez de ``float``.

As regras de "campo vazio" de cada seção (por exemplo, área do FEP vazia = 100%)
ficam em :mod:`makerprice3d.core.calculadora`, que lê os campos do projeto.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from makerprice3d.core.numeros import CEM, UM, ZERO, nao_negativo, para_decimal

#: Fração extra (1/3) de desgaste "invisível" do FEP: camadas, sucção, tensão do material.
FATOR_DESGASTE_INVISIVEL = Decimal("0.33")


def calculo_gasto_material(resina: Decimal, suporte: Decimal, peso: Decimal, fixo: Decimal) -> Decimal:
    """Custo do material.

    Fórmula: ``((peso / 1000) * resina) * (1 + suporte / 100) + fixo``

    :param resina: Preço de 1 kg de resina (R$).
    :param suporte: Percentual de suportes da peça (%).
    :param peso: Peso da peça em gramas (cuidado: alguns fatiadores já somam o suporte).
    :param fixo: Custo fixo cobrado pela peça independente do material (R$).
    """
    resultado = ((peso / Decimal(1000)) * resina) * (UM + suporte / CEM) + fixo
    return nao_negativo(resultado)


def calculo_custo_resina(resina: Decimal, suporte: Decimal, peso: Decimal) -> Decimal:
    """Parte do custo de material que é só resina (sem o custo fixo).

    Usado como base para as novas perdas de resina. Fórmula:
    ``((peso / 1000) * resina) * (1 + suporte / 100)``
    """
    return nao_negativo(((peso / Decimal(1000)) * resina) * (UM + suporte / CEM))


def calculo_gasto_em_energia(
    impressao: Decimal, lixa_retificadora: Decimal, lavagem_cura: Decimal, pintura: Decimal
) -> Decimal:
    """Soma do gasto de energia em todas as etapas.

    Fórmula: ``impressao + lixa_retificadora + lavagem_cura + pintura``
    """
    return nao_negativo(impressao + lixa_retificadora + lavagem_cura + pintura)


def calculo_desgaste(
    preco_lcd: Decimal,
    vida_util: Decimal,
    tempo_total: Decimal,
    preco_fep: Decimal,
    durabilidade: Decimal,
    porcentagem_area: Decimal,
    manutencao_fixa_extra: Decimal,
) -> Decimal:
    """Desgaste de LCD, FEP e manutenção.

    Fórmula: ``((preco_lcd / vida_util) * tempo_total)
    + ((preco_fep / durabilidade) * (porcentagem_area + 0.33)) + manutencao_fixa_extra``

    ``porcentagem_area`` é uma fração (0,25 = 25%). O ``0.33`` representa 1/3 adicional
    de desgastes invisíveis. Como na v1.x, se ``vida_util`` ou ``durabilidade`` for zero
    o desgaste inteiro vale zero.
    """
    if vida_util == ZERO or durabilidade == ZERO:
        return ZERO
    resultado = (
        ((preco_lcd / vida_util) * tempo_total)
        + ((preco_fep / durabilidade) * (porcentagem_area + FATOR_DESGASTE_INVISIVEL))
        + manutencao_fixa_extra
    )
    return nao_negativo(resultado)


def _divisor_seguro(valor: Decimal) -> Decimal:
    """Na v1.x, divisores zero no acabamento eram trocados por 1."""
    return UM if valor == ZERO else valor


def calculo_custo_total_lavagem(custo_solvente: Decimal, lavagens_por_peca: Decimal, litros_usados: Decimal) -> Decimal:
    """Custo do solvente (álcool isopropílico).

    Fórmula: ``(custo_solvente / lavagens_por_peca) * litros_usados``
    """
    return nao_negativo((custo_solvente / _divisor_seguro(lavagens_por_peca)) * litros_usados)


def calculo_custo_total_lixa(custo_de_ponta: Decimal, vida_util_ponta: Decimal, pontas_usadas: Decimal) -> Decimal:
    """Custo das pontas de micro retífica.

    Fórmula: ``(custo_de_ponta / vida_util_ponta) * pontas_usadas``
    """
    return nao_negativo((custo_de_ponta / _divisor_seguro(vida_util_ponta)) * pontas_usadas)


def calculo_custo_total_pintura(
    custo_unidade_tinta: Decimal, ml_por_unidade: Decimal, uso_de_tinta_medio: Decimal
) -> Decimal:
    """Custo de tinta por regra de três.

    Fórmula: ``(custo_unidade_tinta * uso_de_tinta_medio) / ml_por_unidade``
    """
    return nao_negativo((custo_unidade_tinta * uso_de_tinta_medio) / _divisor_seguro(ml_por_unidade))


def calculo_despesas(valores_totais: Iterable[Decimal | str]) -> Decimal:
    """Soma a coluna "Valor" da tabela de despesas (valor já multiplicado pela quantidade)."""
    total = ZERO
    for valor in valores_totais:
        total += para_decimal(valor)
    return total


def calculo_logistica(embrulho: Decimal, descontos: Decimal, impostos: Decimal, frete: Decimal) -> Decimal:
    """Logística: embrulho, impostos e frete, menos descontos.

    Fórmula: ``(embrulho + impostos + frete) - abs(descontos)``

    Pode ser negativa (desconto maior que os custos), como na v1.x.
    """
    return (embrulho + impostos + frete) - abs(descontos)


def calculo_mao_de_obra(ganho_por_hora: Decimal, horas_trabalhadas: Decimal) -> Decimal:
    """Mão de obra. Fórmula: ``ganho_por_hora * horas_trabalhadas``"""
    return nao_negativo(ganho_por_hora * horas_trabalhadas)


def calculo_total(valores: Iterable[Decimal], lucro_percentual: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Soma geral e lucro, como o ``CalculadoraGeral`` da v1.x.

    ``total_gasto = max(0, soma)``, ``total_ganho = total_gasto * lucro / 100`` e
    ``total_absoluto = total_gasto + total_ganho`` (sem o antigo teto de 9.999,99).

    :return: ``(total_gasto, total_ganho, total_absoluto)``
    """
    total_gasto = nao_negativo(sum(valores, ZERO))
    total_ganho = total_gasto * (lucro_percentual / CEM)
    return total_gasto, total_ganho, total_gasto + total_ganho


#: Sugestões por faixa de lucro (texto, cor) — mesmas faixas e cores da v1.x.
CORES_SUGESTAO = {
    "vermelho": "#ff4c4c",
    "laranja": "#ff9f43",
    "amarelo": "#ffd24c",
    "verde": "#4cff4c",
    "azul": "#4c9dff",
}


def definir_sugestao(lucro_percentual: Decimal) -> tuple[str, str]:
    """Classifica a porcentagem de lucro (sobre o custo).

    ``< 0`` Prejuízo · ``<= 10`` Baixo · ``<= 30`` Ideal · ``<= 60`` Alto · acima Muito Alto.

    :return: ``(texto, cor_hex)``
    """
    if lucro_percentual < 0:
        return "Prejuízo", CORES_SUGESTAO["vermelho"]
    if lucro_percentual <= 10:
        return "Baixo", CORES_SUGESTAO["laranja"]
    if lucro_percentual <= 30:
        return "Ideal", CORES_SUGESTAO["verde"]
    if lucro_percentual <= 60:
        return "Alto", CORES_SUGESTAO["azul"]
    return "Muito Alto", CORES_SUGESTAO["amarelo"]
