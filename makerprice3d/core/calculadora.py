# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Calculadora geral: lê um projeto e devolve todos os resultados.

Substitui o antigo ``controladores/operador.py`` (``CalculadoraGeral``) sem depender
da interface. As regras de campo vazio de cada seção foram mantidas da v1.x:

* Desgaste: "Area (%)" vazia ou inválida conta como 100%.
* Acabamento: quantidades/divisores vazios ou inválidos contam como 1.
* Demais campos: vazio ou inválido conta como 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from makerprice3d.core import formulas as f
from makerprice3d.core import precificacao as p
from makerprice3d.core.numeros import CEM, UM, ZERO, nao_negativo, para_decimal
from makerprice3d.core.projeto import Projeto, obter_valor


@dataclass(frozen=True)
class Categoria:
    """Uma categoria de custo exibida nos cards e no gráfico."""

    chave: str
    rotulo: str
    cor: str
    nova: bool = False


#: Categorias na ordem do gráfico. As 9 primeiras (e "lucro") vêm da v1.x com as mesmas cores.
CATEGORIAS: tuple[Categoria, ...] = (
    Categoria("material", "Material", "#ff4c4c"),
    Categoria("energia", "Energia", "#4cff4c"),
    Categoria("desgaste", "Desgaste", "#4c4cff"),
    Categoria("lavagem", "Lavagem", "#ffd24c"),
    Categoria("lixa", "Lixa", "#ff7afc"),
    Categoria("pintura", "Pintura", "#4cfff6"),
    Categoria("despesas", "Despesas", "#f26522"),
    Categoria("logistica", "Logística", "#9d4cff"),
    Categoria("mao_de_obra", "Mão de Obra", "#4cff9d"),
    Categoria("perdas_resina", "Perda de Resina", "#00c2ff", nova=True),
    Categoria("falhas", "Falhas", "#c2ff00", nova=True),
    Categoria("custos_fixos", "Custos Fixos", "#ff006e", nova=True),
    Categoria("depreciacao", "Depreciação", "#8338ec", nova=True),
    Categoria("licenca", "Licença STL", "#ffbe0b", nova=True),
    Categoria("epi", "EPI/Consumíveis", "#06d6a0", nova=True),
    Categoria("climatizacao", "Climatização", "#ef476f", nova=True),
    Categoria("das_mei", "DAS MEI", "#adb5bd", nova=True),
)
CATEGORIA_LUCRO = Categoria("lucro", "Lucro", "#ff4c9d")
CATEGORIA_TAXAS = Categoria("taxas", "Taxas/Impostos", "#3a86ff", nova=True)


@dataclass(frozen=True)
class Resultado:
    """Todos os números calculados para um projeto (valores por peça)."""

    subtotais: dict[str, Decimal]
    total_gasto: Decimal
    total_ganho: Decimal
    total_absoluto: Decimal
    lucro_percentual: Decimal
    modo_lucro: p.ModoLucro
    markup_percentual: Decimal
    margem_percentual: Decimal
    sugestao: tuple[str, str]
    taxas: p.TaxasVenda
    taxas_valor: Decimal
    preco_minimo: Decimal
    preco_sugerido: Decimal
    preco_premium: Decimal
    quantidade: int
    total_pedido: Decimal
    analise_reversa: p.AnalisePreco | None = None
    avisos: list[str] = field(default_factory=list)

    def valores_grafico(self) -> list[tuple[Categoria, Decimal]]:
        """Fatias do gráfico de composição (negativos viram zero, como na v1.x)."""
        fatias = [(cat, nao_negativo(self.subtotais.get(cat.chave, ZERO))) for cat in CATEGORIAS]
        fatias.append((CATEGORIA_LUCRO, nao_negativo(self.total_ganho)))
        fatias.append((CATEGORIA_TAXAS, nao_negativo(self.taxas_valor)))
        return fatias


def _num(projeto: Projeto, caminho: str, padrao: Decimal = ZERO) -> Decimal:
    return para_decimal(obter_valor(projeto, caminho, ""), padrao)


def _percentual_area(projeto: Projeto) -> Decimal:
    """Na v1.x: vazio ou inválido = 1.0 (100%); senão valor / 100."""
    return _num(projeto, "desgaste.porcentagem_area", CEM) / CEM


def subtotal_material(projeto: Projeto) -> Decimal:
    """Card Material (fórmula original)."""
    return f.calculo_gasto_material(
        _num(projeto, "material.resina"),
        _num(projeto, "material.suporte"),
        _num(projeto, "material.peso"),
        _num(projeto, "material.custo_fixo"),
    )


def fator_mesa(projeto: Projeto) -> Decimal:
    """Fração da mesa que cabe a esta peça (1 quando imprime sozinha)."""
    return p.fator_rateio_mesa(
        _num(projeto, "material.peso"),
        _num(projeto, "mesa.peso_total_mesa"),
        _num(projeto, "mesa.pecas_na_mesa"),
    )


def subtotal_energia(projeto: Projeto) -> Decimal:
    """Card Gasto em Energia (fórmula original).

    Com mesa compartilhada, a energia da *impressão* é a da mesa inteira e entra
    proporcional ao rateio; lixa, lavagem/cura e pintura continuam por peça.
    """
    return f.calculo_gasto_em_energia(
        _num(projeto, "energia.impressao") * fator_mesa(projeto),
        _num(projeto, "energia.lixa_retificadora"),
        _num(projeto, "energia.lavagem_cura"),
        _num(projeto, "energia.pintura"),
    )


def subtotal_desgaste(projeto: Projeto) -> Decimal:
    """Card Desgaste (fórmula original).

    Com mesa compartilhada, o "Tempo Total (h)" é o da mesa e o LCD entra pelo tempo
    rateado. O FEP já usa a área (%) ocupada pela peça, então não é rateado de novo.
    """
    return f.calculo_desgaste(
        _num(projeto, "desgaste.preco_lcd"),
        _num(projeto, "desgaste.vida_util"),
        _num(projeto, "desgaste.tempo_total") * fator_mesa(projeto),
        _num(projeto, "desgaste.preco_fep"),
        _num(projeto, "desgaste.durabilidade"),
        _percentual_area(projeto),
        _num(projeto, "desgaste.manutencao_fixa_extra"),
    )


def subtotais_acabamento(projeto: Projeto) -> dict[str, Decimal]:
    """Abas Lavagem, Lixa e Pintura (fórmulas originais)."""
    return {
        "lavagem": f.calculo_custo_total_lavagem(
            _num(projeto, "acabamento.lavagem.custo_solvente"),
            _num(projeto, "acabamento.lavagem.lavagens_por_peca", UM),
            _num(projeto, "acabamento.lavagem.litros_usados"),
        ),
        "lixa": f.calculo_custo_total_lixa(
            _num(projeto, "acabamento.lixa.custo_de_ponta"),
            _num(projeto, "acabamento.lixa.vida_util_ponta", UM),
            _num(projeto, "acabamento.lixa.pontas_usadas", UM),
        ),
        "pintura": f.calculo_custo_total_pintura(
            _num(projeto, "acabamento.pintura.custo_unidade_tinta"),
            _num(projeto, "acabamento.pintura.ml_por_unidade", UM),
            _num(projeto, "acabamento.pintura.uso_de_tinta_medio", UM),
        ),
    }


def subtotal_despesas(projeto: Projeto) -> Decimal:
    """Tabela de despesas: soma da coluna Valor."""
    tabela = obter_valor(projeto, "despesas.tabela", []) or []
    return f.calculo_despesas(str(item.get("valor", "")) for item in tabela if isinstance(item, dict))


def subtotal_logistica(projeto: Projeto) -> Decimal:
    """Card Logística (fórmula original, pode ser negativa)."""
    return f.calculo_logistica(
        _num(projeto, "logistica.embrulho"),
        _num(projeto, "logistica.descontos"),
        _num(projeto, "logistica.impostos"),
        _num(projeto, "logistica.frete"),
    )


def subtotal_mao_de_obra(projeto: Projeto) -> Decimal:
    """Card Mão de Obra (fórmula original)."""
    return f.calculo_mao_de_obra(
        _num(projeto, "mao_de_obra.ganho_por_hora"), _num(projeto, "mao_de_obra.horas_trabalhadas")
    )


def custo_resina(projeto: Projeto) -> Decimal:
    """Custo só da resina (base das perdas)."""
    return f.calculo_custo_resina(
        _num(projeto, "material.resina"), _num(projeto, "material.suporte"), _num(projeto, "material.peso")
    )


def horas_impressao(projeto: Projeto) -> Decimal:
    """Horas de máquina desta peça: "Tempo Total (h)" do card Desgaste × rateio da mesa."""
    return nao_negativo(_num(projeto, "desgaste.tempo_total")) * fator_mesa(projeto)


def taxas_do_projeto(projeto: Projeto) -> p.TaxasVenda:
    """Taxas do canal de venda e impostos percentuais sobre o preço.

    O percentual de impostos só vale nos regimes "simples" e "nenhum" (outros impostos
    sobre a venda); no MEI o imposto é o DAS fixo rateado.
    """
    regime = str(obter_valor(projeto, "tributos.regime", "nenhum"))
    impostos = ZERO if regime == "mei" else _num(projeto, "venda.impostos_percentual")
    return p.TaxasVenda(
        percentual_canal=_num(projeto, "venda.taxa_percentual"),
        fixo_canal=_num(projeto, "venda.taxa_fixa"),
        percentual_impostos=impostos,
    )


def calcular(projeto: Projeto) -> Resultado:
    """Calcula tudo para o projeto.

    Com as seções novas vazias, ``total_gasto``, ``total_ganho`` e ``total_absoluto``
    são idênticos aos da v1.x (sem o teto de 9.999,99).
    """
    avisos: list[str] = []
    subtotais: dict[str, Decimal] = {
        "material": subtotal_material(projeto),
        "energia": subtotal_energia(projeto),
        "desgaste": subtotal_desgaste(projeto),
        **subtotais_acabamento(projeto),
        "despesas": subtotal_despesas(projeto),
        "logistica": subtotal_logistica(projeto),
        "mao_de_obra": subtotal_mao_de_obra(projeto),
    }

    horas = horas_impressao(projeto)
    subtotais["perdas_resina"] = p.perda_de_resina(
        custo_resina(projeto),
        _num(projeto, "perdas.tanque"),
        _num(projeto, "perdas.lavagem"),
        _num(projeto, "perdas.suportes"),
    )
    custo_tentativa = (
        subtotais["material"]
        + subtotais["perdas_resina"]
        + _num(projeto, "energia.impressao") * fator_mesa(projeto)
        + subtotais["desgaste"]
    )
    taxa_falha = _num(projeto, "perdas.taxa_falha")
    if taxa_falha > p.TAXA_FALHA_MAXIMA:
        avisos.append("Taxa de falha limitada a 95%.")
    subtotais["falhas"] = p.custo_de_falhas(custo_tentativa, taxa_falha)
    subtotais["custos_fixos"] = p.rateio_custos_fixos(
        _num(projeto, "custos_fixos.mensal"), _num(projeto, "custos_fixos.horas_maquina_mes"), horas
    )
    subtotais["depreciacao"] = p.depreciacao(
        _num(projeto, "custos_fixos.preco_impressora"), _num(projeto, "custos_fixos.vida_util_impressora"), horas
    ) + p.depreciacao(_num(projeto, "custos_fixos.preco_mesa"), _num(projeto, "custos_fixos.vida_util_mesa"), horas)

    subtotais["licenca"] = p.rateio_licenca(
        _num(projeto, "extras.licenca_custo"), _num(projeto, "extras.licenca_vendas_previstas")
    )
    subtotais["epi"] = (
        p.custo_por_peca(_num(projeto, "extras.luvas_custo"), _num(projeto, "extras.luvas_pecas"))
        + p.custo_por_peca(_num(projeto, "extras.mascara_custo"), _num(projeto, "extras.mascara_pecas"))
        + p.custo_por_peca(_num(projeto, "extras.filtro_custo"), _num(projeto, "extras.filtro_pecas"))
        + nao_negativo(_num(projeto, "extras.papel_por_peca"))
    )
    subtotais["climatizacao"] = p.custo_energia_por_potencia(
        _num(projeto, "extras.clima_potencia_w"),
        _num(projeto, "extras.clima_horas"),
        _num(projeto, "extras.tarifa_kwh"),
    ) * fator_mesa(projeto)
    regime = str(obter_valor(projeto, "tributos.regime", "nenhum"))
    subtotais["das_mei"] = (
        p.rateio_das_mei(_num(projeto, "tributos.das_mensal"), _num(projeto, "tributos.vendas_mes"))
        if regime == "mei"
        else ZERO
    )

    try:
        modo = p.ModoLucro(str(obter_valor(projeto, "lucro.modo", "markup")))
    except ValueError:
        modo = p.ModoLucro.MARKUP
    lucro_pct = nao_negativo(_num(projeto, "lucro.estado"))

    if modo == p.ModoLucro.MARKUP:
        total_gasto, total_ganho, total_absoluto = f.calculo_total(subtotais.values(), lucro_pct)
        markup = lucro_pct
        margem = p.markup_para_margem(lucro_pct)
    else:
        total_gasto = nao_negativo(sum(subtotais.values(), ZERO))
        total_absoluto = p.aplicar_lucro(total_gasto, lucro_pct, modo)
        total_ganho = total_absoluto - total_gasto
        margem = min(lucro_pct, p.PERCENTUAL_VENDA_MAXIMO)
        markup = p.margem_para_markup(lucro_pct)

    taxas = taxas_do_projeto(projeto)
    preco_sugerido = p.preco_com_taxas(total_absoluto, taxas)
    preco_minimo = p.preco_com_taxas(total_gasto, taxas)
    premium_pct = lucro_pct + nao_negativo(_num(projeto, "venda.acrescimo_premium", Decimal(25)))
    preco_premium = p.preco_com_taxas(p.aplicar_lucro(total_gasto, premium_pct, modo), taxas)
    if taxas.percentual_total < nao_negativo(taxas.percentual_canal) + nao_negativo(taxas.percentual_impostos):
        avisos.append("Taxas + impostos limitados a 95% do preço.")

    quantidade = max(1, int(_num(projeto, "meta.quantidade", UM)))
    analise = None
    preco_alvo = _num(projeto, "venda.preco_alvo")
    if preco_alvo > ZERO:
        analise = p.preco_reverso(preco_alvo, total_gasto, taxas)

    return Resultado(
        subtotais=subtotais,
        total_gasto=total_gasto,
        total_ganho=total_ganho,
        total_absoluto=total_absoluto,
        lucro_percentual=lucro_pct,
        modo_lucro=modo,
        markup_percentual=markup,
        margem_percentual=margem,
        sugestao=f.definir_sugestao(markup),
        taxas=taxas,
        taxas_valor=preco_sugerido - total_absoluto if preco_sugerido else ZERO,
        preco_minimo=preco_minimo,
        preco_sugerido=preco_sugerido,
        preco_premium=preco_premium,
        quantidade=quantidade,
        total_pedido=preco_sugerido * quantidade,
        analise_reversa=analise,
        avisos=avisos,
    )
