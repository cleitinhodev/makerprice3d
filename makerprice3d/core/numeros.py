# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Conversão e arredondamento de números digitados pelo usuário.

As regras de conversão reproduzem o comportamento da versão 1.x (campo vazio ou
inválido vira um valor padrão), mas agora aceitam vírgula ou ponto em todos os campos
e trabalham com :class:`~decimal.Decimal` para evitar erros de ponto flutuante.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

ZERO = Decimal("0")
UM = Decimal("1")
CEM = Decimal("100")
CENTAVO = Decimal("0.01")

NumeroLike = Decimal | int | float | str | None

_RE_SIMBOLOS = re.compile(r"[R$\s%]")


def para_decimal(valor: NumeroLike, padrao: Decimal = ZERO) -> Decimal:
    """Converte um valor digitado (``"12,5"``, ``"R$ 3.40"``, ``7``) para ``Decimal``.

    Aceita vírgula ou ponto como separador decimal. Quando existem os dois
    (ex.: ``"1.234,56"``), o último é tratado como separador decimal.

    :param valor: Texto, número ou ``None``.
    :param padrao: Valor devolvido quando o campo está vazio ou é inválido.
    :return: O número convertido ou ``padrao``.
    """
    if valor is None:
        return padrao
    if isinstance(valor, Decimal):
        return valor if valor.is_finite() else padrao
    if isinstance(valor, bool):
        return padrao
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, float):
        return Decimal(str(valor))

    texto = _RE_SIMBOLOS.sub("", str(valor))
    if not texto:
        return padrao
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    else:
        texto = texto.replace(",", ".")
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return padrao
    return numero if numero.is_finite() else padrao


def texto_valido(valor: str | None) -> bool:
    """Indica se o texto está vazio ou representa um número válido.

    Usado pela validação em tempo real dos campos da interface.
    """
    if valor is None or not str(valor).strip():
        return True
    sentinela = Decimal("-999999999.123")
    return para_decimal(valor, sentinela) != sentinela


def esta_vazio(valor: NumeroLike) -> bool:
    """Retorna ``True`` quando o campo não foi preenchido."""
    return valor is None or (isinstance(valor, str) and not valor.strip())


def arredondar(valor: Decimal, casas: Decimal = CENTAVO) -> Decimal:
    """Arredonda para centavos (meio para cima), como numa nota fiscal."""
    return valor.quantize(casas, rounding=ROUND_HALF_UP)


def nao_negativo(valor: Decimal) -> Decimal:
    """Limita o valor a zero ou mais (substitui o antigo limite 0..9999,99)."""
    return valor if valor > ZERO else ZERO


def dividir(numerador: Decimal, denominador: Decimal, padrao: Decimal = ZERO) -> Decimal:
    """Divide sem quebrar quando o denominador é zero."""
    if denominador == ZERO:
        return padrao
    return numerador / denominador


def formatar_moeda(valor: Decimal, simbolo: str = "R$") -> str:
    """Formata no padrão brasileiro: ``R$ 1.234,56``."""
    numero = arredondar(valor)
    negativo = numero < ZERO
    inteiro, _, frac = f"{abs(numero):.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    texto = f"{'.'.join(grupos)},{frac}"
    return f"{'-' if negativo else ''}{simbolo} {texto}".strip()


def formatar_numero(valor: Decimal, casas: int = 2) -> str:
    """Formata um número com vírgula decimal (sem símbolo de moeda)."""
    quantum = Decimal(1).scaleb(-casas)
    return f"{valor.quantize(quantum, rounding=ROUND_HALF_UP):.{casas}f}".replace(".", ",")


def formatar_percentual(valor: Decimal, casas: int = 1) -> str:
    """Formata ``Decimal('12.345')`` como ``12,3%``."""
    return f"{formatar_numero(valor, casas)}%"
