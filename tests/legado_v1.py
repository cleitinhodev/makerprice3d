# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Oráculo: cópia fiel das fórmulas em float da v1.x (interface tkinter).

Copiado de interface_grafica/*_frame.py e controladores/operador.py antes da
remoção da interface antiga, para garantir que a v2 calcula exatamente o mesmo.
"""

LIMITE = 9999.99


def converter_float(valor: str) -> float:
    valor = valor.strip().replace(",", ".")
    if not valor:
        return 0.0
    try:
        return float(valor)
    except ValueError:
        return 0.0


def converter_int_desgaste(valor: str) -> int:
    if valor == "":
        return 0
    try:
        return int(valor)
    except ValueError:
        return 0


def converter_int_acabamento(valor: str) -> int:
    if valor == "":
        return 1
    try:
        return int(valor)
    except ValueError:
        return 1


def converter_porcentagem(valor: str) -> float:
    # A v1.x não trocava vírgula por ponto aqui ("40,5" virava 100%).
    if not valor:
        return 1.0
    try:
        return float(valor) / 100
    except ValueError:
        return 1.0


def material(resina, suporte, peso, fixo):
    r = ((peso / 1000) * resina) * (1 + suporte / 100) + fixo
    return max(0, min(r, LIMITE))


def energia(impressao, lixa, lavagem_cura, pintura):
    return max(0, min(impressao + lixa + lavagem_cura + pintura, LIMITE))


def desgaste(preco_lcd, vida_util, tempo_total, preco_fep, durabilidade, porcentagem_area, manutencao):
    try:
        r = (
            ((preco_lcd / vida_util) * tempo_total)
            + ((preco_fep / durabilidade) * (porcentagem_area + 0.33))
            + manutencao
        )
    except ZeroDivisionError:
        r = 0.0
    return max(0, min(r, LIMITE))


def lavagem(custo_solvente, lavagens_por_peca, litros_usados):
    if lavagens_por_peca == 0:
        lavagens_por_peca = 1
    return max(0, min((custo_solvente / lavagens_por_peca) * litros_usados, LIMITE))


def lixa(custo_de_ponta, vida_util_ponta, pontas_usadas):
    if vida_util_ponta == 0:
        vida_util_ponta = 1
    return max(0, min((custo_de_ponta / vida_util_ponta) * pontas_usadas, LIMITE))


def pintura(custo_unidade_tinta, ml_por_unidade, uso_de_tinta_medio):
    if ml_por_unidade == 0:
        ml_por_unidade = 1
    return max(0, min((custo_unidade_tinta * uso_de_tinta_medio) / ml_por_unidade, LIMITE))


def logistica(embrulho, descontos, impostos, frete):
    r = (embrulho + impostos + frete) - abs(descontos)
    return max(-LIMITE, min(r, LIMITE))


def mao_de_obra(ganho_por_hora, horas):
    return max(0, min(ganho_por_hora * horas, LIMITE))


def total(valores, lucro_int):
    lucro = float(lucro_int) / 100
    total_gasto = max(0.0, min(LIMITE, sum(valores)))
    total_ganho = total_gasto * lucro
    if total_gasto + total_ganho > LIMITE:
        total_ganho = LIMITE - total_gasto
    return total_gasto, total_ganho, total_gasto + total_ganho


def calcular_projeto_v1(dados: dict) -> tuple[float, float, float]:
    """Calcula um dicionário de projeto (formato .json da v1.x) como a v1.x faria."""
    m, e, d, a, lo, mo = (
        dados[k] for k in ("material", "energia", "desgaste", "acabamento", "logistica", "mao_de_obra")
    )
    cf = converter_float
    valores = [
        material(cf(m["resina"]), cf(m["suporte"]), cf(m["peso"]), cf(m["custo_fixo"])),
        energia(cf(e["impressao"]), cf(e["lixa_retificadora"]), cf(e["lavagem_cura"]), cf(e["pintura"])),
        desgaste(
            cf(d["preco_lcd"]),
            converter_int_desgaste(d["vida_util"]),
            converter_int_desgaste(d["tempo_total"]),
            cf(d["preco_fep"]),
            converter_int_desgaste(d["durabilidade"]),
            converter_porcentagem(d["porcentagem_area"]),
            cf(d["manutencao_fixa_extra"]),
        ),
        lavagem(
            cf(a["lavagem"]["custo_solvente"]),
            converter_int_acabamento(a["lavagem"]["lavagens_por_peca"]),
            cf(a["lavagem"]["litros_usados"]),
        ),
        lixa(
            cf(a["lixa"]["custo_de_ponta"]),
            converter_int_acabamento(a["lixa"]["vida_util_ponta"]),
            converter_int_acabamento(a["lixa"]["pontas_usadas"]),
        ),
        pintura(
            cf(a["pintura"]["custo_unidade_tinta"]),
            converter_int_acabamento(a["pintura"]["ml_por_unidade"]),
            converter_int_acabamento(a["pintura"]["uso_de_tinta_medio"]),
        ),
        sum(cf(str(linha[3]).replace("R$", "")) for linha in dados["despesas"]["tabela"]),
        logistica(cf(lo["embrulho"]), cf(lo["descontos"]), cf(lo["impostos"]), cf(lo["frete"])),
        mao_de_obra(cf(mo["ganho_por_hora"]), cf(mo["horas_trabalhadas"])),
    ]
    return total(valores, dados["lucro"]["estado"])
