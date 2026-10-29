# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Exportação em CSV e geração do HTML do orçamento (usado no PDF)."""

from __future__ import annotations

import csv
import html
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from makerprice3d.core.calculadora import CATEGORIAS, Resultado
from makerprice3d.core.gestao import ItemOrcamento, TotaisOrcamento
from makerprice3d.core.numeros import formatar_moeda, formatar_numero
from makerprice3d.core.projeto import Projeto


def linhas_resultado(projeto: Projeto, resultado: Resultado) -> list[list[str]]:
    """Tabela "Item; Valor" com a composição do preço."""
    nome = projeto.get("meta", {}).get("nome") or "Sem Título"
    linhas = [["Projeto", nome], ["Categoria", "Valor (R$)"]]
    for cat in CATEGORIAS:
        linhas.append([cat.rotulo, formatar_numero(resultado.subtotais.get(cat.chave, 0))])
    linhas += [
        ["Total Gasto", formatar_numero(resultado.total_gasto)],
        ["Lucro", formatar_numero(resultado.total_ganho)],
        ["Preço sem taxas", formatar_numero(resultado.total_absoluto)],
        ["Taxas e impostos", formatar_numero(resultado.taxas_valor)],
        ["Preço mínimo", formatar_numero(resultado.preco_minimo)],
        ["Preço sugerido", formatar_numero(resultado.preco_sugerido)],
        ["Preço premium", formatar_numero(resultado.preco_premium)],
        ["Markup (%)", formatar_numero(resultado.markup_percentual)],
        ["Margem (%)", formatar_numero(resultado.margem_percentual)],
        ["Quantidade", str(resultado.quantidade)],
        ["Total do pedido", formatar_numero(resultado.total_pedido)],
    ]
    return linhas


def escrever_csv(caminho: str | Path, linhas: Iterable[Sequence[Any]]) -> Path:
    """CSV com ``;`` e BOM UTF-8 (abre direto no Excel em português)."""
    destino = Path(caminho)
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        for linha in linhas:
            escritor.writerow(["" if v is None else v for v in linha])
    return destino


def exportar_resultado_csv(caminho: str | Path, projeto: Projeto, resultado: Resultado) -> Path:
    """Exporta a composição do preço do projeto atual."""
    return escrever_csv(caminho, linhas_resultado(projeto, resultado))


def exportar_tabela_csv(caminho: str | Path, registros: list[dict[str, Any]], colunas: Sequence[str]) -> Path:
    """Exporta uma lista de registros (clientes, pedidos, estoque...)."""
    return escrever_csv(caminho, [list(colunas), *[[r.get(c, "") for c in colunas] for r in registros]])


def html_orcamento(
    numero: int | str,
    loja: str,
    cliente: str,
    itens: Iterable[ItemOrcamento],
    totais: TotaisOrcamento,
    emissao: date,
    validade_ate: date,
    prazo_entrega: str,
    pagamento: str,
    observacoes: str = "",
    contato_loja: str = "",
) -> str:
    """HTML simples e elegante do orçamento, pronto para virar PDF (QTextDocument)."""
    e = html.escape
    linhas = "".join(
        f"<tr><td>{e(i.descricao)}</td><td align='center'>{i.quantidade}</td>"
        f"<td align='right'>{formatar_moeda(i.preco_unitario)}</td>"
        f"<td align='right'>{formatar_moeda(i.total)}</td></tr>"
        for i in itens
    )
    extras = ""
    if totais.desconto:
        extras += f"<tr><td colspan='3' align='right'>Desconto</td><td align='right'>-{formatar_moeda(totais.desconto)}</td></tr>"
    if totais.frete:
        extras += (
            f"<tr><td colspan='3' align='right'>Frete</td><td align='right'>{formatar_moeda(totais.frete)}</td></tr>"
        )
    return f"""
<html><body style="font-family: 'Segoe UI', Arial; color:#1b1f29;">
<table width="100%"><tr>
<td><h1 style="color:#6c4cf0; margin:0;">{e(loja or "Maker Price 3D")}</h1>
<div style="color:#667;">{e(contato_loja)}</div></td>
<td align="right"><h2 style="margin:0;">Orçamento nº {e(str(numero))}</h2>
<div>Emissão: {emissao.strftime("%d/%m/%Y")}</div>
<div><b>Válido até: {validade_ate.strftime("%d/%m/%Y")}</b></div></td>
</tr></table>
<hr/>
<p><b>Cliente:</b> {e(cliente or "-")}</p>
<table width="100%" cellspacing="0" cellpadding="6" border="1" style="border-collapse:collapse; border-color:#dde;">
<tr style="background:#efeafe;"><th align="left">Item</th><th>Qtd</th><th align="right">Unitário</th><th align="right">Total</th></tr>
{linhas}
<tr><td colspan='3' align='right'>Subtotal</td><td align='right'>{formatar_moeda(totais.subtotal)}</td></tr>
{extras}
<tr style="background:#efeafe;"><td colspan='3' align='right'><b>Total</b></td>
<td align='right'><b>{formatar_moeda(totais.total)}</b></td></tr>
</table>
<p><b>Prazo de entrega:</b> {e(prazo_entrega or "-")}<br/>
<b>Forma de pagamento:</b> {e(pagamento or "-")}</p>
{f"<p><b>Observações:</b> {e(observacoes)}</p>" if observacoes else ""}
<p style="color:#889; font-size:9pt;">Orçamento gerado com Maker Price 3D — software livre (GPLv3).</p>
</body></html>
"""
