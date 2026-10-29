# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Cálculos novos da versão 2.0, somados por cima das fórmulas originais.

Nada aqui altera as fórmulas da v1.x: são categorias extras de custo e ferramentas de
preço (taxas de canal, preço reverso, margem x markup).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from makerprice3d.core.numeros import CEM, UM, ZERO, dividir, nao_negativo

#: Taxa de falha máxima aceita (%). Acima disso o custo esperado explode.
TAXA_FALHA_MAXIMA = Decimal("95")
#: Soma máxima de percentuais sobre o preço (taxas + impostos) aceita (%).
PERCENTUAL_VENDA_MAXIMO = Decimal("95")


class ModoLucro(str, Enum):
    """Como a porcentagem de lucro é aplicada."""

    #: Lucro sobre o custo (comportamento da v1.x): preço = custo × (1 + p).
    MARKUP = "markup"
    #: Margem sobre o preço de venda: preço = custo ÷ (1 − p).
    MARGEM = "margem"


def perda_de_resina(
    custo_resina: Decimal, perda_tanque: Decimal, perda_lavagem: Decimal, perda_suportes: Decimal
) -> Decimal:
    """Custo da resina que se perde no processo.

    ``custo_resina × (tanque% + lavagem% + suportes%) / 100``

    :param custo_resina: Custo só da resina da peça (sem custo fixo).
    :param perda_tanque: % que fica no tanque/FEP e não volta ao frasco.
    :param perda_lavagem: % que escorre/vai embora na lavagem.
    :param perda_suportes: % extra de suportes/raft descartados *além* do % de suportes
        já informado no card Material (deixe 0 para não contar duas vezes).
    """
    percentual = nao_negativo(perda_tanque) + nao_negativo(perda_lavagem) + nao_negativo(perda_suportes)
    return nao_negativo(custo_resina) * percentual / CEM


def custo_de_falhas(custo_producao: Decimal, taxa_falha: Decimal) -> Decimal:
    """Custo extra esperado por falhas/reimpressões.

    Se ``p`` é a taxa de falha, em média são necessárias ``1 / (1 − p)`` tentativas
    por peça boa. O extra é ``custo_producao × p / (1 − p)``.

    :param custo_producao: Custo de uma tentativa de impressão (material, perdas,
        energia da impressão e desgaste).
    :param taxa_falha: Percentual de impressões que falham (0 a 95).
    """
    p = min(nao_negativo(taxa_falha), TAXA_FALHA_MAXIMA) / CEM
    if p == ZERO:
        return ZERO
    return nao_negativo(custo_producao) * p / (UM - p)


def rateio_custos_fixos(custo_fixo_mensal: Decimal, horas_maquina_mes: Decimal, horas_impressao: Decimal) -> Decimal:
    """Rateio dos custos fixos mensais (aluguel, internet, software, MEI...) por hora de máquina.

    ``(custo_fixo_mensal / horas_maquina_mes) × horas_impressao``
    """
    taxa_hora = dividir(nao_negativo(custo_fixo_mensal), nao_negativo(horas_maquina_mes))
    return taxa_hora * nao_negativo(horas_impressao)


def depreciacao(preco: Decimal, vida_util_horas: Decimal, horas_uso: Decimal) -> Decimal:
    """Depreciação linear de um equipamento ou peça: ``preco / vida_util × horas``."""
    return dividir(nao_negativo(preco), nao_negativo(vida_util_horas)) * nao_negativo(horas_uso)


def custo_energia_por_potencia(potencia_w: Decimal, horas: Decimal, tarifa_kwh: Decimal) -> Decimal:
    """Custo de energia de um aparelho: ``(W / 1000) × horas × R$/kWh``."""
    return nao_negativo(potencia_w) / Decimal(1000) * nao_negativo(horas) * nao_negativo(tarifa_kwh)


def preco_por_kg(preco_litro: Decimal, densidade_g_ml: Decimal) -> Decimal:
    """Converte preço por litro em preço por kg usando a densidade (g/ml = kg/L)."""
    return dividir(nao_negativo(preco_litro), nao_negativo(densidade_g_ml))


def aplicar_lucro(custo: Decimal, percentual: Decimal, modo: ModoLucro = ModoLucro.MARKUP) -> Decimal:
    """Preço antes das taxas de venda.

    * markup: ``custo × (1 + p)``
    * margem: ``custo / (1 − p)`` (p limitado a 95%)
    """
    p = percentual / CEM
    if modo == ModoLucro.MARGEM:
        p = min(p, PERCENTUAL_VENDA_MAXIMO / CEM)
        return custo / (UM - p)
    return custo * (UM + p)


def markup_para_margem(markup_percentual: Decimal) -> Decimal:
    """Converte markup (sobre o custo) em margem (sobre o preço), em %."""
    m = markup_percentual / CEM
    if m == -UM:
        return ZERO
    return m / (UM + m) * CEM


def margem_para_markup(margem_percentual: Decimal) -> Decimal:
    """Converte margem (sobre o preço) em markup (sobre o custo), em %."""
    m = min(margem_percentual, PERCENTUAL_VENDA_MAXIMO) / CEM
    return m / (UM - m) * CEM


@dataclass(frozen=True)
class TaxasVenda:
    """Taxas cobradas sobre o preço de venda (canal + impostos)."""

    percentual_canal: Decimal = ZERO
    fixo_canal: Decimal = ZERO
    percentual_impostos: Decimal = ZERO

    @property
    def percentual_total(self) -> Decimal:
        """Soma dos percentuais, limitada a 95%."""
        total = nao_negativo(self.percentual_canal) + nao_negativo(self.percentual_impostos)
        return min(total, PERCENTUAL_VENDA_MAXIMO)


def preco_com_taxas(preco_liquido: Decimal, taxas: TaxasVenda) -> Decimal:
    """Preço de venda que, depois das taxas, devolve ``preco_liquido``.

    ``(preco_liquido + taxa_fixa) / (1 − percentual_total)``
    """
    if preco_liquido <= ZERO and taxas.fixo_canal <= ZERO:
        return ZERO
    return (preco_liquido + nao_negativo(taxas.fixo_canal)) / (UM - taxas.percentual_total / CEM)


def receita_liquida(preco_venda: Decimal, taxas: TaxasVenda) -> Decimal:
    """Quanto sobra de um preço de venda depois das taxas do canal e impostos."""
    return preco_venda * (UM - taxas.percentual_total / CEM) - nao_negativo(taxas.fixo_canal)


@dataclass(frozen=True)
class AnalisePreco:
    """Resultado do preço reverso: dado um preço de venda, qual o lucro real."""

    preco_venda: Decimal
    taxas: Decimal
    receita_liquida: Decimal
    custo: Decimal
    lucro: Decimal
    margem_percentual: Decimal
    markup_percentual: Decimal


def preco_reverso(preco_venda: Decimal, custo: Decimal, taxas: TaxasVenda) -> AnalisePreco:
    """Analisa um preço de venda já definido (ex.: preço da concorrência).

    :param preco_venda: Preço que o cliente paga.
    :param custo: Custo total da peça (o "Total Gasto").
    :param taxas: Taxas de canal e impostos sobre a venda.
    """
    liquido = receita_liquida(preco_venda, taxas)
    lucro = liquido - custo
    return AnalisePreco(
        preco_venda=preco_venda,
        taxas=preco_venda - liquido,
        receita_liquida=liquido,
        custo=custo,
        lucro=lucro,
        margem_percentual=dividir(lucro, preco_venda) * CEM,
        markup_percentual=dividir(lucro, custo) * CEM,
    )


# --- Rateio de mesa (várias peças na mesma impressão) -------------------------------


def fator_rateio_mesa(peso_peca: Decimal, peso_total_mesa: Decimal, pecas_na_mesa: Decimal) -> Decimal:
    """Fração da impressão que cabe a esta peça quando a mesa é compartilhada.

    * Com ``peso_total_mesa`` (soma do peso/resina de todas as peças da mesa), o rateio é
      proporcional ao volume: ``peso_peca / peso_total_mesa``.
    * Sem pesos, divide igualmente: ``1 / pecas_na_mesa``.
    * Sem nenhum dos dois, a peça ocupa a mesa sozinha (fator 1).
    """
    if peso_total_mesa > ZERO and peso_peca > ZERO:
        return min(UM, peso_peca / peso_total_mesa)
    if pecas_na_mesa > UM:
        return UM / pecas_na_mesa
    return UM


def tempo_por_altura(altura_mm: Decimal, altura_camada_mm: Decimal, segundos_por_camada: Decimal) -> Decimal:
    """Tempo de impressão da mesa (h) a partir da altura da peça mais alta.

    Em resina o tempo depende da quantidade de camadas, não de quantas peças há na mesa:
    ``camadas = arredondar_para_cima(altura / camada)``; ``horas = camadas × s/camada / 3600``.
    """
    if altura_camada_mm <= ZERO or altura_mm <= ZERO or segundos_por_camada <= ZERO:
        return ZERO
    camadas = (altura_mm / altura_camada_mm).to_integral_value(rounding="ROUND_CEILING")
    return camadas * segundos_por_camada / Decimal(3600)


def camadas_por_altura(altura_mm: Decimal, altura_camada_mm: Decimal) -> int:
    """Quantidade de camadas da mesa (usada no contador de uso do LCD/FEP)."""
    if altura_camada_mm <= ZERO or altura_mm <= ZERO:
        return 0
    return int((altura_mm / altura_camada_mm).to_integral_value(rounding="ROUND_CEILING"))


# --- Custos extras ------------------------------------------------------------------


def rateio_licenca(custo_licenca: Decimal, vendas_previstas: Decimal) -> Decimal:
    """Licença comercial de STL rateada pelas vendas previstas do modelo."""
    return dividir(nao_negativo(custo_licenca), nao_negativo(vendas_previstas))


def custo_por_peca(custo_unidade: Decimal, pecas_por_unidade: Decimal) -> Decimal:
    """Consumível que rende várias peças (luvas, máscara, filtro de carvão...)."""
    return dividir(nao_negativo(custo_unidade), nao_negativo(pecas_por_unidade))


def rateio_das_mei(das_mensal: Decimal, vendas_mes: Decimal) -> Decimal:
    """DAS mensal do MEI rateado pela quantidade de peças vendidas no mês."""
    return dividir(nao_negativo(das_mensal), nao_negativo(vendas_mes))
