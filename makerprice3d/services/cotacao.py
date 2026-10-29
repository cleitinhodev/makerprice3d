# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Cotação de moedas em tempo real, com cache local como alternativa offline."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

URL_COTACAO = "https://api.exchangerate-api.com/v4/latest/BRL"
#: Mesmas moedas da v1.x.
MOEDAS = ("USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "ARS", "BTC")


@dataclass
class Cotacoes:
    """Taxas de conversão a partir do real."""

    taxas: dict[str, Decimal]
    origem: str  # "online", "cache" ou "indisponível"
    data: str = ""

    def converter(self, valor_brl: Decimal, moeda: str) -> Decimal | None:
        """Converte um valor em reais (``None`` se a moeda não tiver taxa)."""
        taxa = self.taxas.get(moeda)
        return None if taxa is None else valor_brl * taxa


def _requisitar(url: str, timeout: float) -> dict[str, Any]:
    import requests  # importação tardia: o núcleo não depende de rede

    resposta = requests.get(url, timeout=timeout)
    resposta.raise_for_status()
    return resposta.json()


def buscar_cotacoes(
    cache: Path | None = None,
    requisitar: Callable[[str, float], dict[str, Any]] = _requisitar,
    timeout: float = 5,
) -> Cotacoes:
    """Busca as cotações online; se falhar, usa o último cache salvo."""
    try:
        dados = requisitar(URL_COTACAO, timeout)
        taxas = {m: Decimal(str(v)) for m, v in (dados.get("rates") or {}).items() if m in MOEDAS}
        if not taxas:
            raise ValueError("Resposta sem cotações.")
        data = str(dados.get("date", ""))
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"date": data, "rates": {k: str(v) for k, v in taxas.items()}}), "utf-8")
        return Cotacoes(taxas, "online", data)
    except Exception:  # noqa: BLE001 - qualquer falha de rede cai no cache
        if cache and cache.exists():
            try:
                dados = json.loads(cache.read_text("utf-8"))
                taxas = {m: Decimal(v) for m, v in dados.get("rates", {}).items()}
                return Cotacoes(taxas, "cache", str(dados.get("date", "")))
            except (ValueError, OSError):
                pass
        return Cotacoes({}, "indisponível")
