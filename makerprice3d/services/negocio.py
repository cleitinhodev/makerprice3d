# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Operações de negócio que juntam o banco (SQLite) e as regras puras do núcleo."""

from __future__ import annotations

import shutil
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from makerprice3d.core import gestao as g
from makerprice3d.core.calculadora import calcular, horas_impressao
from makerprice3d.core.numeros import ZERO, arredondar, dividir, para_decimal
from makerprice3d.core.projeto import Projeto, obter_valor
from makerprice3d.services.banco import Banco, agora


# --- Catálogo ------------------------------------------------------------------------
def salvar_no_catalogo(
    banco: Banco, projeto: Projeto, nome: str, escala: str = "", foto: str = "", pasta_fotos: Path | None = None
) -> int:
    """Guarda o projeto atual como produto do catálogo, com preço sugerido e custo.

    Se ``pasta_fotos`` for informada, a foto é copiada para lá (o catálogo não depende
    do arquivo original continuar existindo).
    """
    resultado = calcular(projeto)
    caminho_foto = foto
    if foto and pasta_fotos:
        origem = Path(foto)
        if origem.exists():
            pasta_fotos.mkdir(parents=True, exist_ok=True)
            destino = pasta_fotos / f"{datetime.now():%Y%m%d%H%M%S}_{origem.name}"
            shutil.copy2(origem, destino)
            caminho_foto = str(destino)
    perfil = projeto.get("perfil", {})
    return banco.inserir(
        "produtos",
        {
            "nome": nome,
            "escala": escala,
            "preco": f"{arredondar(resultado.preco_sugerido):.2f}",
            "custo": f"{arredondar(resultado.total_gasto):.2f}",
            "peso_g": str(obter_valor(projeto, "material.peso", "") or ""),
            "tempo_h": f"{horas_impressao(projeto):.2f}",
            "resina_id": perfil.get("resina_id"),
            "impressora_id": perfil.get("impressora_id"),
            "foto": caminho_foto,
            "projeto": projeto,
        },
    )


def item_de_produto(produto: dict[str, Any], quantidade: int = 1) -> g.ItemOrcamento:
    """Converte um produto do catálogo em item de orçamento."""
    descricao = produto.get("nome", "")
    if produto.get("escala"):
        descricao = f"{descricao} ({produto['escala']})"
    return g.ItemOrcamento(
        descricao=descricao,
        quantidade=quantidade,
        preco_unitario=para_decimal(produto.get("preco")),
        custo_unitario=para_decimal(produto.get("custo")),
        produto_id=produto.get("id"),
        peso_g=para_decimal(produto.get("peso_g")),
        resina_id=produto.get("resina_id"),
    )


def itens_de_kit(banco: Banco, kit: dict[str, Any], quantidade: int = 1) -> list[g.ItemOrcamento]:
    """Expande um kit em itens, aplicando o desconto do kit no preço de cada item."""
    desconto = para_decimal(kit.get("desconto_percentual"))
    fator = Decimal(1) - min(desconto, Decimal(100)) / Decimal(100)
    itens = []
    for entrada in kit.get("itens") or []:
        produto = banco.obter("produtos", int(entrada.get("produto_id", 0)))
        if not produto:
            continue
        base = item_de_produto(produto, int(entrada.get("quantidade", 1)) * quantidade)
        itens.append(
            g.ItemOrcamento(
                descricao=f"{base.descricao} [kit {kit.get('nome', '')}]",
                quantidade=base.quantidade,
                preco_unitario=arredondar(base.preco_unitario * fator),
                custo_unitario=base.custo_unitario,
                produto_id=base.produto_id,
                peso_g=base.peso_g,
                resina_id=base.resina_id,
            )
        )
    return itens


def preco_do_kit(banco: Banco, kit: dict[str, Any]) -> tuple[Decimal, Decimal]:
    """``(preço cheio, preço com desconto)`` de um kit."""
    precos = []
    for entrada in kit.get("itens") or []:
        produto = banco.obter("produtos", int(entrada.get("produto_id", 0)))
        if produto:
            precos.append((para_decimal(produto.get("preco")), int(entrada.get("quantidade", 1))))
    return g.preco_kit(precos, para_decimal(kit.get("desconto_percentual")))


# --- Orçamentos e pedidos -------------------------------------------------------------
def itens_do_registro(registro: dict[str, Any]) -> list[g.ItemOrcamento]:
    """Itens de um orçamento/pedido salvo."""
    return [g.item_de_dict(i) for i in registro.get("itens") or []]


def totais_do_orcamento(orcamento: dict[str, Any]) -> g.TotaisOrcamento:
    """Totais de um orçamento salvo."""
    return g.totais_orcamento(
        itens_do_registro(orcamento),
        para_decimal(orcamento.get("desconto_percentual")),
        para_decimal(orcamento.get("frete")),
    )


def data_do_registro(registro: dict[str, Any]) -> date:
    """Data (``date``) de um orçamento/pedido."""
    try:
        return date.fromisoformat(str(registro.get("data", ""))[:10])
    except ValueError:
        return date.today()


def converter_em_pedido(banco: Banco, orcamento_id: int) -> int:
    """Transforma um orçamento aprovado em pedido (entra na fila como "aguardando")."""
    orcamento = banco.obter("orcamentos", orcamento_id)
    if not orcamento:
        raise ValueError("Orçamento não encontrado.")
    if orcamento.get("pedido_id"):
        return int(orcamento["pedido_id"])
    totais = totais_do_orcamento(orcamento)
    pedido_id = banco.inserir(
        "pedidos",
        {
            "orcamento_id": orcamento_id,
            "cliente_id": orcamento.get("cliente_id"),
            "data": agora(),
            "status": "aguardando",
            "prazo_entrega": orcamento.get("prazo_entrega", ""),
            "pagamento": orcamento.get("pagamento", ""),
            "itens": orcamento.get("itens") or [],
            "total": f"{totais.total:.2f}",
            "custo": f"{totais.custo:.2f}",
            "estoque_baixado": False,
        },
    )
    banco.atualizar("orcamentos", orcamento_id, {"status": "convertido", "pedido_id": pedido_id})
    return pedido_id


def baixar_estoque_do_pedido(banco: Banco, pedido: dict[str, Any]) -> dict[int, Decimal]:
    """Dá baixa no estoque e registra os movimentos."""
    consumo = g.consumo_do_pedido(itens_do_registro(pedido), banco.listar("estoque"))
    for estoque_id, quantidade in consumo.items():
        item = banco.obter("estoque", estoque_id)
        if not item:
            continue
        novo = para_decimal(item.get("quantidade")) - quantidade
        banco.atualizar("estoque", estoque_id, {"quantidade": f"{novo:.2f}"})
        banco.inserir(
            "movimentos_estoque",
            {
                "estoque_id": estoque_id,
                "data": agora(),
                "quantidade": f"{-quantidade:.2f}",
                "motivo": f"Pedido nº {pedido['id']}",
                "pedido_id": pedido["id"],
            },
        )
    return consumo


def mudar_status_pedido(banco: Banco, pedido_id: int, status: str) -> dict[int, Decimal]:
    """Muda o status na fila de produção; dá baixa no estoque uma única vez.

    :return: o consumo baixado agora (vazio se nada foi baixado).
    """
    pedido = banco.obter("pedidos", pedido_id)
    if not pedido:
        raise ValueError("Pedido não encontrado.")
    consumo: dict[int, Decimal] = {}
    if g.deve_baixar_estoque(pedido.get("status", ""), status, bool(pedido.get("estoque_baixado"))):
        consumo = baixar_estoque_do_pedido(banco, pedido)
        banco.atualizar("pedidos", pedido_id, {"estoque_baixado": True})
    mudancas: dict[str, Any] = {"status": status}
    if status in g.STATUS_VENDA and not pedido.get("data_conclusao"):
        mudancas["data_conclusao"] = agora()
    banco.atualizar("pedidos", pedido_id, mudancas)
    return consumo


def ajustar_estoque(banco: Banco, estoque_id: int, quantidade: Decimal, motivo: str) -> None:
    """Entrada (positiva) ou saída (negativa) manual no estoque."""
    item = banco.obter("estoque", estoque_id)
    if not item:
        raise ValueError("Item de estoque não encontrado.")
    novo = para_decimal(item.get("quantidade")) + quantidade
    banco.atualizar("estoque", estoque_id, {"quantidade": f"{novo:.2f}"})
    banco.inserir(
        "movimentos_estoque",
        {"estoque_id": estoque_id, "data": agora(), "quantidade": f"{quantidade:.2f}", "motivo": motivo},
    )


# --- Equipamentos -----------------------------------------------------------------------
def uso_da_impressora(banco: Banco, impressora_id: int) -> dict[str, g.UsoPeca]:
    """Uso do LCD (horas) e do FEP (impressões) desde a última troca."""
    impressora = banco.obter("impressoras", impressora_id) or {}
    impressoes = banco.listar("impressoes", impressora_id=impressora_id)
    manutencoes = banco.listar("manutencoes", impressora_id=impressora_id)
    return {
        "lcd": g.uso_desde_troca("lcd", impressoes, manutencoes, para_decimal(impressora.get("vida_lcd_h")), "horas"),
        "fep": g.uso_desde_troca(
            "fep", impressoes, manutencoes, para_decimal(impressora.get("durabilidade_fep")), "impressoes"
        ),
    }


def alertas_de_troca(banco: Banco) -> list[str]:
    """Mensagens de alerta de LCD/FEP perto do fim da vida útil."""
    alertas = []
    for impressora in banco.listar("impressoras"):
        for peca, uso in uso_da_impressora(banco, impressora["id"]).items():
            if uso.alerta:
                estado = "passou da vida útil" if uso.vencida else "está perto do fim da vida útil"
                alertas.append(f"{impressora['nome']}: {peca.upper()} {estado} ({uso.percentual:.0f}%).")
    return alertas


# --- Painel ------------------------------------------------------------------------------
def resumo_do_mes(banco: Banco, ano: int, mes: int) -> g.ResumoMensal:
    """Indicadores do mês a partir dos pedidos."""
    return g.resumo_mensal(banco.listar("pedidos"), ano, mes)


def payback_impressoras(banco: Banco, hoje: date | None = None) -> list[tuple[dict[str, Any], g.Payback]]:
    """Retorno do investimento de cada impressora pelos pedidos vendidos ligados a ela."""
    hoje = hoje or date.today()
    pedidos = [p for p in banco.listar("pedidos") if p.get("status") in g.STATUS_VENDA]
    resultado = []
    for impressora in banco.listar("impressoras"):
        lucro = sum(
            (
                para_decimal(p.get("total")) - para_decimal(p.get("custo"))
                for p in pedidos
                if p.get("impressora_id") == impressora["id"]
            ),
            ZERO,
        )
        try:
            compra = date.fromisoformat(str(impressora.get("data_compra") or "")[:10])
            meses = Decimal(max(1, (hoje - compra).days)) / Decimal("30.4375")
        except ValueError:
            meses = ZERO
        resultado.append((impressora, g.payback(para_decimal(impressora.get("preco")), lucro, meses)))
    return resultado


def ponto_equilibrio_mensal(banco: Banco) -> Decimal | None:
    """Peças/mês para cobrir os custos fixos, com preço e custo médios dos pedidos vendidos."""
    pedidos = [p for p in banco.listar("pedidos") if p.get("status") in g.STATUS_VENDA]
    pecas = sum(sum(i.quantidade for i in itens_do_registro(p)) for p in pedidos)
    if not pecas:
        return None
    receita = sum((para_decimal(p.get("total")) for p in pedidos), ZERO)
    custo = sum((para_decimal(p.get("custo")) for p in pedidos), ZERO)
    return g.ponto_de_equilibrio(
        para_decimal(banco.config("custo_fixo_mensal")),
        dividir(receita, Decimal(pecas)),
        dividir(custo, Decimal(pecas)),
    )
