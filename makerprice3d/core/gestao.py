# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Regras de gestão do ateliê: orçamentos, pedidos, produção, estoque, equipamentos,
painel mensal, retorno do investimento e simulação de cenários.

Tudo aqui é Python puro e trabalha com dicionários simples (as linhas do banco), para
ser testável sem interface e sem SQLite.
"""

from __future__ import annotations

import copy
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import quote

from makerprice3d.core.calculadora import Resultado, calcular
from makerprice3d.core.numeros import CEM, UM, ZERO, arredondar, dividir, formatar_moeda, nao_negativo, para_decimal
from makerprice3d.core.projeto import Projeto, obter_valor

Linha = Mapping[str, Any]

# --- Orçamentos e kits --------------------------------------------------------------

#: Escalas comuns de miniaturas/peças em resina (texto livre também é aceito).
ESCALAS = ("28mm", "32mm", "54mm", "75mm", "Busto", "Outra")


@dataclass(frozen=True)
class ItemOrcamento:
    """Uma linha do orçamento."""

    descricao: str
    quantidade: int
    preco_unitario: Decimal
    custo_unitario: Decimal = ZERO
    produto_id: int | None = None
    peso_g: Decimal = ZERO
    resina_id: int | None = None

    @property
    def total(self) -> Decimal:
        """Preço da linha."""
        return self.preco_unitario * self.quantidade

    @property
    def custo_total(self) -> Decimal:
        """Custo da linha."""
        return self.custo_unitario * self.quantidade


def item_de_dict(dados: Linha) -> ItemOrcamento:
    """Cria um :class:`ItemOrcamento` a partir de um dicionário salvo."""
    resina = dados.get("resina_id")
    produto = dados.get("produto_id")
    return ItemOrcamento(
        descricao=str(dados.get("descricao", "")),
        quantidade=max(1, int(para_decimal(dados.get("quantidade"), UM))),
        preco_unitario=para_decimal(dados.get("preco_unitario")),
        custo_unitario=para_decimal(dados.get("custo_unitario")),
        produto_id=int(produto) if produto not in (None, "") else None,
        peso_g=para_decimal(dados.get("peso_g")),
        resina_id=int(resina) if resina not in (None, "") else None,
    )


def item_para_dict(item: ItemOrcamento) -> dict[str, Any]:
    """Serializa um item para JSON."""
    return {
        "descricao": item.descricao,
        "quantidade": item.quantidade,
        "preco_unitario": f"{item.preco_unitario:.2f}",
        "custo_unitario": f"{item.custo_unitario:.2f}",
        "produto_id": item.produto_id,
        "peso_g": str(item.peso_g),
        "resina_id": item.resina_id,
    }


@dataclass(frozen=True)
class TotaisOrcamento:
    """Totais de um orçamento/pedido."""

    subtotal: Decimal
    desconto: Decimal
    frete: Decimal
    total: Decimal
    custo: Decimal
    lucro: Decimal


def totais_orcamento(itens: Iterable[ItemOrcamento], desconto_percentual: Decimal, frete: Decimal) -> TotaisOrcamento:
    """Soma itens, aplica desconto (%) e soma o frete."""
    lista = list(itens)
    subtotal = sum((i.total for i in lista), ZERO)
    desconto = arredondar(subtotal * min(nao_negativo(desconto_percentual), CEM) / CEM)
    frete = nao_negativo(frete)
    total = subtotal - desconto + frete
    custo = sum((i.custo_total for i in lista), ZERO)
    return TotaisOrcamento(subtotal, desconto, frete, total, custo, total - frete - custo)


def preco_kit(precos_itens: Iterable[tuple[Decimal, int]], desconto_percentual: Decimal) -> tuple[Decimal, Decimal]:
    """Preço de um kit/combo: ``(preço cheio, preço com desconto)``."""
    cheio = sum((preco * qtd for preco, qtd in precos_itens), ZERO)
    com_desconto = cheio * (UM - min(nao_negativo(desconto_percentual), CEM) / CEM)
    return cheio, arredondar(com_desconto)


def validade(data_emissao: date, dias: int) -> date:
    """Data limite de um orçamento."""
    return data_emissao + timedelta(days=max(0, int(dias)))


def orcamento_vencido(data_emissao: date, dias: int, hoje: date | None = None) -> bool:
    """``True`` se a validade do orçamento já passou."""
    return (hoje or date.today()) > validade(data_emissao, dias)


def normalizar_telefone(telefone: str, ddi_padrao: str = "55") -> str:
    """Deixa só dígitos e acrescenta o DDI do Brasil quando faltar (10 ou 11 dígitos)."""
    digitos = re.sub(r"\D", "", telefone or "")
    if len(digitos) in (10, 11):
        digitos = ddi_padrao + digitos
    return digitos


def texto_orcamento(
    numero: int | str,
    cliente: str,
    itens: Iterable[ItemOrcamento],
    totais: TotaisOrcamento,
    validade_ate: date,
    prazo_entrega: str,
    pagamento: str,
    loja: str = "Maker Price 3D",
) -> str:
    """Texto do orçamento para mensagens (WhatsApp, e-mail)."""
    linhas = [f"*Orçamento nº {numero}* — {loja}", f"Cliente: {cliente}" if cliente else "", ""]
    for item in itens:
        linhas.append(f"• {item.quantidade}x {item.descricao} — {formatar_moeda(item.total)}")
    linhas.append("")
    if totais.desconto:
        linhas.append(f"Desconto: -{formatar_moeda(totais.desconto)}")
    if totais.frete:
        linhas.append(f"Frete: {formatar_moeda(totais.frete)}")
    linhas.append(f"*Total: {formatar_moeda(totais.total)}*")
    if prazo_entrega:
        linhas.append(f"Prazo de entrega: {prazo_entrega}")
    if pagamento:
        linhas.append(f"Pagamento: {pagamento}")
    linhas.append(f"Válido até {validade_ate.strftime('%d/%m/%Y')}")
    return "\n".join(linha for linha in linhas if linha is not None).replace("\n\n\n", "\n\n")


def link_whatsapp(telefone: str, texto: str) -> str:
    """Link ``wa.me`` com a mensagem preenchida (o usuário confere e envia no WhatsApp)."""
    numero = normalizar_telefone(telefone)
    base = f"https://wa.me/{numero}" if numero else "https://wa.me/"
    return f"{base}?text={quote(texto)}"


# --- Produção -----------------------------------------------------------------------

#: Fila de produção, na ordem.
STATUS_PRODUCAO = ("aguardando", "imprimindo", "lavando", "curando", "acabamento", "pronto", "entregue")
ROTULOS_STATUS = {
    "aguardando": "Aguardando",
    "imprimindo": "Imprimindo",
    "lavando": "Lavando",
    "curando": "Curando",
    "acabamento": "Acabamento",
    "pronto": "Pronto",
    "entregue": "Entregue",
    "cancelado": "Cancelado",
}
#: Status a partir do qual o material já foi consumido (baixa automática no estoque).
STATUS_CONSOME_ESTOQUE = "imprimindo"
#: Status que contam como venda realizada no painel.
STATUS_VENDA = ("pronto", "entregue")


def proximo_status(status: str) -> str:
    """Avança um passo na fila de produção (fica em "entregue" no fim)."""
    if status not in STATUS_PRODUCAO:
        return STATUS_PRODUCAO[0]
    indice = STATUS_PRODUCAO.index(status)
    return STATUS_PRODUCAO[min(indice + 1, len(STATUS_PRODUCAO) - 1)]


def deve_baixar_estoque(status_anterior: str, status_novo: str, ja_baixado: bool) -> bool:
    """Baixa o estoque uma única vez, quando o pedido chega em "imprimindo" ou além."""
    if ja_baixado or status_novo not in STATUS_PRODUCAO:
        return False
    return STATUS_PRODUCAO.index(status_novo) >= STATUS_PRODUCAO.index(STATUS_CONSOME_ESTOQUE)


# --- Estoque ------------------------------------------------------------------------

CATEGORIAS_ESTOQUE = ("resina", "ipa", "luvas", "filtro", "embalagem", "outro")


def consumo_do_pedido(itens: Iterable[ItemOrcamento], estoque: Iterable[Linha]) -> dict[int, Decimal]:
    """Quanto de cada item de estoque um pedido consome.

    * Resina: itens de estoque da categoria ``resina`` ligados à mesma ``resina_id`` da
      peça perdem ``peso_g × quantidade`` (unidade do estoque: gramas).
    * Demais categorias: ``consumo_por_peca × quantidade total de peças``.

    :return: ``{id_do_item_de_estoque: quantidade_a_baixar}``
    """
    lista_itens = list(itens)
    total_pecas = sum(i.quantidade for i in lista_itens)
    resina_por_id: dict[int, Decimal] = defaultdict(lambda: ZERO)
    for item in lista_itens:
        if item.resina_id is not None:
            resina_por_id[item.resina_id] += item.peso_g * item.quantidade

    consumo: dict[int, Decimal] = {}
    resinas_baixadas: set[int] = set()
    for linha in estoque:
        id_estoque = int(linha["id"])
        if linha.get("categoria") == "resina":
            resina_id = linha.get("resina_id")
            if resina_id is not None and int(resina_id) in resina_por_id and int(resina_id) not in resinas_baixadas:
                consumo[id_estoque] = resina_por_id[int(resina_id)]
                resinas_baixadas.add(int(resina_id))
        else:
            por_peca = para_decimal(linha.get("consumo_por_peca"))
            if por_peca > ZERO and total_pecas:
                consumo[id_estoque] = por_peca * total_pecas
    return {k: v for k, v in consumo.items() if v > ZERO}


def estoque_baixo(estoque: Iterable[Linha]) -> list[Linha]:
    """Itens com quantidade menor ou igual ao mínimo configurado."""
    return [
        linha
        for linha in estoque
        if para_decimal(linha.get("minimo")) > ZERO
        and para_decimal(linha.get("quantidade")) <= para_decimal(linha.get("minimo"))
    ]


# --- Equipamentos -------------------------------------------------------------------

#: Peças com contador de uso.
PECAS_CONTADOR = ("lcd", "fep")
MOTIVOS_FALHA = ("suportes", "adesão", "FEP", "arquivo", "resina", "energia", "outro")


@dataclass(frozen=True)
class UsoPeca:
    """Uso acumulado de uma peça desde a última troca."""

    peca: str
    horas: Decimal
    camadas: int
    impressoes: int
    limite: Decimal
    percentual: Decimal

    @property
    def alerta(self) -> bool:
        """Chegou a 90% da vida útil."""
        return self.limite > ZERO and self.percentual >= Decimal(90)

    @property
    def vencida(self) -> bool:
        """Passou da vida útil."""
        return self.limite > ZERO and self.percentual >= CEM


def uso_desde_troca(
    peca: str, impressoes: Iterable[Linha], manutencoes: Iterable[Linha], limite: Decimal, unidade_limite: str = "horas"
) -> UsoPeca:
    """Soma o uso de ``peca`` ("lcd" ou "fep") desde a última troca registrada.

    :param impressoes: Registros com ``data`` (ISO), ``horas``, ``camadas``.
    :param manutencoes: Registros com ``data``, ``tipo`` ("troca") e ``peca``.
    :param limite: Vida útil (horas para o LCD; impressões para o FEP, como na v1.x).
    :param unidade_limite: ``"horas"``, ``"impressoes"`` ou ``"camadas"``.
    """
    trocas = [str(m.get("data", "")) for m in manutencoes if m.get("tipo") == "troca" and m.get("peca") == peca]
    ultima = max(trocas) if trocas else ""
    horas, camadas, quantidade = ZERO, 0, 0
    for registro in impressoes:
        if str(registro.get("data", "")) >= ultima:
            horas += para_decimal(registro.get("horas"))
            camadas += int(para_decimal(registro.get("camadas")))
            quantidade += 1
    usado = {"horas": horas, "impressoes": Decimal(quantidade), "camadas": Decimal(camadas)}[unidade_limite]
    return UsoPeca(peca, horas, camadas, quantidade, limite, dividir(usado, limite) * CEM)


@dataclass(frozen=True)
class TaxaFalhaMedida:
    """Taxa de falha calculada pelo histórico de impressões."""

    total: int
    falhas: int
    percentual: Decimal
    motivos: dict[str, int] = field(default_factory=dict)


def taxa_falha_medida(
    impressoes: Iterable[Linha], impressora_id: int | None = None, resina_id: int | None = None
) -> TaxaFalhaMedida:
    """Taxa de falha real, opcionalmente filtrada por impressora e/ou resina."""
    filtrados = [
        r
        for r in impressoes
        if (impressora_id is None or r.get("impressora_id") == impressora_id)
        and (resina_id is None or r.get("resina_id") == resina_id)
    ]
    falhas = [r for r in filtrados if not r.get("sucesso")]
    motivos = Counter(str(r.get("motivo_falha") or "outro") for r in falhas)
    return TaxaFalhaMedida(
        total=len(filtrados),
        falhas=len(falhas),
        percentual=dividir(Decimal(len(falhas)), Decimal(len(filtrados))) * CEM,
        motivos=dict(motivos.most_common()),
    )


# --- Painel mensal e retorno do investimento ----------------------------------------


@dataclass(frozen=True)
class ResumoMensal:
    """Indicadores do mês."""

    pedidos: int
    receita: Decimal
    custo: Decimal
    lucro: Decimal
    ticket_medio: Decimal
    pecas: int
    resina_g: Decimal
    top_pecas: list[tuple[str, int]]


def _no_mes(data_iso: str, ano: int, mes: int) -> bool:
    return str(data_iso or "")[:7] == f"{ano:04d}-{mes:02d}"


def resumo_mensal(pedidos: Iterable[Linha], ano: int, mes: int, top: int = 5) -> ResumoMensal:
    """Receita, lucro, ticket médio, peças mais vendidas e resina usada no mês.

    Considera pedidos com status de venda ("pronto"/"entregue") pela ``data_conclusao``
    (ou ``data`` se não houver).
    """
    receita = custo = resina = ZERO
    contagem: Counter[str] = Counter()
    quantidade_pedidos = pecas = 0
    for pedido in pedidos:
        if pedido.get("status") not in STATUS_VENDA:
            continue
        if not _no_mes(pedido.get("data_conclusao") or pedido.get("data", ""), ano, mes):
            continue
        quantidade_pedidos += 1
        receita += para_decimal(pedido.get("total"))
        custo += para_decimal(pedido.get("custo"))
        for item in pedido.get("itens", []) or []:
            obj = item if isinstance(item, ItemOrcamento) else item_de_dict(item)
            contagem[obj.descricao] += obj.quantidade
            pecas += obj.quantidade
            resina += obj.peso_g * obj.quantidade
    lucro = receita - custo
    return ResumoMensal(
        pedidos=quantidade_pedidos,
        receita=receita,
        custo=custo,
        lucro=lucro,
        ticket_medio=dividir(receita, Decimal(quantidade_pedidos)),
        pecas=pecas,
        resina_g=resina,
        top_pecas=contagem.most_common(top),
    )


@dataclass(frozen=True)
class Payback:
    """Retorno do investimento em uma impressora."""

    investimento: Decimal
    lucro_acumulado: Decimal
    percentual_pago: Decimal
    lucro_mensal_medio: Decimal
    meses_restantes: Decimal | None

    @property
    def quitado(self) -> bool:
        """O lucro acumulado já pagou a máquina."""
        return self.lucro_acumulado >= self.investimento > ZERO


def payback(investimento: Decimal, lucro_acumulado: Decimal, meses_de_uso: Decimal) -> Payback:
    """Quanto da impressora já se pagou e em quantos meses termina de pagar."""
    media = dividir(lucro_acumulado, meses_de_uso) if meses_de_uso > ZERO else ZERO
    falta = nao_negativo(investimento - lucro_acumulado)
    meses = None if media <= ZERO else dividir(falta, media)
    return Payback(investimento, lucro_acumulado, dividir(lucro_acumulado, investimento) * CEM, media, meses)


def ponto_de_equilibrio(
    custos_fixos_mensais: Decimal, preco_medio: Decimal, custo_variavel_medio: Decimal
) -> Decimal | None:
    """Peças por mês para cobrir os custos fixos: ``fixos / (preço − custo variável)``.

    :return: ``None`` quando a margem de contribuição é zero ou negativa.
    """
    contribuicao = preco_medio - custo_variavel_medio
    if contribuicao <= ZERO:
        return None
    return nao_negativo(custos_fixos_mensais) / contribuicao


# --- Simulação de cenários ----------------------------------------------------------

#: Ajustes de cenário: chave -> (rótulo, campos afetados).
AJUSTES_CENARIO: dict[str, tuple[str, tuple[str, ...]]] = {
    "resina": ("Preço da resina", ("material.resina",)),
    "tarifa": (
        "Tarifa de energia",
        (
            "energia.impressao",
            "energia.lixa_retificadora",
            "energia.lavagem_cura",
            "energia.pintura",
            "extras.tarifa_kwh",
        ),
    ),
    "mao_de_obra": ("Valor da hora", ("mao_de_obra.ganho_por_hora",)),
    "frete": ("Frete", ("logistica.frete",)),
    "pecas_reposicao": ("LCD/FEP", ("desgaste.preco_lcd", "desgaste.preco_fep")),
    "solvente": ("Álcool isopropílico", ("acabamento.lavagem.custo_solvente",)),
}


def aplicar_cenario(projeto: Projeto, ajustes: Mapping[str, Decimal]) -> Projeto:
    """Cópia do projeto com os campos reajustados em ``ajustes[chave]`` por cento.

    Ex.: ``{"resina": Decimal(20)}`` = resina 20% mais cara.
    """
    novo = copy.deepcopy(projeto)
    for chave, percentual in ajustes.items():
        if chave not in AJUSTES_CENARIO or not percentual:
            continue
        fator = UM + percentual / CEM
        for caminho in AJUSTES_CENARIO[chave][1]:
            texto = obter_valor(novo, caminho, "")
            if str(texto).strip() == "":
                continue
            valor = para_decimal(texto) * fator
            partes = caminho.split(".")
            alvo = novo
            for parte in partes[:-1]:
                alvo = alvo[parte]
            alvo[partes[-1]] = f"{valor:.4f}".rstrip("0").rstrip(".")
    return novo


def simular(projeto: Projeto, ajustes: Mapping[str, Decimal]) -> tuple[Resultado, Resultado]:
    """``(resultado atual, resultado no cenário)``."""
    return calcular(projeto), calcular(aplicar_cenario(projeto, ajustes))
