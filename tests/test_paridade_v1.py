# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Paridade com a v1.x: com as seções novas vazias, os totais devem ser idênticos."""

import random
from decimal import Decimal

import pytest

from makerprice3d.core import calculadora as calc
from makerprice3d.core import formulas as f
from makerprice3d.core.projeto import migrar
from tests import legado_v1 as v1


def _perto(a: Decimal, b: float) -> None:
    assert float(a) == pytest.approx(b, abs=1e-9)


def test_projeto_exemplo_igual_v1(projeto_v1):
    esperado = v1.calcular_projeto_v1(projeto_v1)
    projeto, migrado = migrar(projeto_v1)
    assert migrado
    resultado = calc.calcular(projeto)
    _perto(resultado.total_gasto, esperado[0])
    _perto(resultado.total_ganho, esperado[1])
    _perto(resultado.total_absoluto, esperado[2])
    # sem taxas, o preço sugerido é o mesmo total da v1.x
    _perto(resultado.preco_sugerido, esperado[2])


def _texto(rng: random.Random, inteiro: tuple[int, int] | None = None, vazio: float = 0.15) -> str:
    if rng.random() < vazio:
        return ""
    if inteiro:
        return str(rng.randint(*inteiro))
    return f"{rng.uniform(0, 60):.2f}".replace(".", rng.choice([",", "."]))


@pytest.mark.parametrize("semente", range(60))
def test_paridade_aleatoria(semente, projeto_v1):
    rng = random.Random(semente)
    dados = projeto_v1
    for secao in ("material", "energia", "logistica", "mao_de_obra"):
        for campo in dados[secao]:
            dados[secao][campo] = _texto(rng)
    for campo in ("preco_lcd", "preco_fep", "manutencao_fixa_extra"):
        dados["desgaste"][campo] = _texto(rng)
    # campos que a v1.x lia como inteiros: usamos inteiros (ver divergências no README)
    for campo, faixa in (("vida_util", (300, 5000)), ("tempo_total", (1, 24)), ("durabilidade", (5, 100))):
        dados["desgaste"][campo] = _texto(rng, inteiro=faixa)
    dados["desgaste"]["porcentagem_area"] = rng.choice(["", "25", "40", "100", "12.5"])
    for sub, campos in (
        ("lavagem", ("custo_solvente", "litros_usados")),
        ("lixa", ("custo_de_ponta",)),
        ("pintura", ("custo_unidade_tinta",)),
    ):
        for campo in campos:
            dados["acabamento"][sub][campo] = _texto(rng)
    for sub, campos in (
        ("lavagem", ("lavagens_por_peca",)),
        ("lixa", ("vida_util_ponta", "pontas_usadas")),
        ("pintura", ("ml_por_unidade", "uso_de_tinta_medio")),
    ):
        for campo in campos:
            dados["acabamento"][sub][campo] = _texto(rng, inteiro=(0, 20))
    dados["lucro"]["estado"] = rng.randint(0, 100)
    esperado = v1.calcular_projeto_v1(dados)
    if esperado[2] >= v1.LIMITE:  # a v2 removeu o teto de 9.999,99
        pytest.skip("acima do antigo teto")
    resultado = calc.calcular(migrar(dados)[0])
    _perto(resultado.total_gasto, esperado[0])
    _perto(resultado.total_ganho, esperado[1])
    _perto(resultado.total_absoluto, esperado[2])


def test_formulas_individuais():
    d = Decimal
    _perto(f.calculo_gasto_material(d(150), d(10), d(80), d(2)), v1.material(150, 10, 80, 2))
    _perto(f.calculo_gasto_em_energia(d(1), d(2), d(3), d(4)), 10)
    _perto(
        f.calculo_desgaste(d(600), d(2000), d(5), d(60), d(30), d("0.4"), d(1)),
        v1.desgaste(600, 2000, 5, 60, 30, 0.4, 1),
    )
    assert f.calculo_desgaste(d(600), d(0), d(5), d(60), d(30), d("0.4"), d(1)) == 0
    assert f.calculo_desgaste(d(600), d(10), d(5), d(60), d(0), d("0.4"), d(1)) == 0
    _perto(f.calculo_custo_total_lavagem(d(35), d(0), d("0.1")), v1.lavagem(35, 0, 0.1))
    _perto(f.calculo_custo_total_lixa(d(12), d(0), d(2)), v1.lixa(12, 0, 2))
    _perto(f.calculo_custo_total_pintura(d(15), d(0), d(4)), v1.pintura(15, 0, 4))
    _perto(f.calculo_logistica(d(3), d(-5), d(1), d(0)), v1.logistica(3, -5, 1, 0))
    assert f.calculo_logistica(d(0), d(10), d(0), d(0)) == d(-10)
    _perto(f.calculo_mao_de_obra(d(25), d("1.5")), 37.5)
    assert f.calculo_mao_de_obra(d(-1), d(2)) == 0
    assert f.calculo_despesas(["1.50", "R$ 2,50", ""]) == d(4)


def test_sem_teto_de_9999():
    gasto, ganho, total = f.calculo_total([Decimal(9000), Decimal(5000)], Decimal(50))
    assert gasto == Decimal(14000)
    assert ganho == Decimal(7000)
    assert total == Decimal(21000)


@pytest.mark.parametrize(
    ("lucro", "texto"),
    [(-1, "Prejuízo"), (0, "Baixo"), (10, "Baixo"), (11, "Ideal"), (30, "Ideal"), (60, "Alto"), (61, "Muito Alto")],
)
def test_sugestao_igual_v1(lucro, texto):
    assert f.definir_sugestao(Decimal(lucro))[0] == texto
