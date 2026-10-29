# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Estrutura do projeto (``.mp3d``) e migração dos arquivos ``.json`` da v1.x.

Os valores dos campos são guardados como **texto**, exatamente como o usuário digitou
(igual à v1.x). Assim nada se perde ao salvar e abrir, e a conversão numérica acontece
só na hora do cálculo.
"""

from __future__ import annotations

import copy
from datetime import datetime
from decimal import Decimal
from typing import Any

from makerprice3d import __version__
from makerprice3d.core.numeros import arredondar, dividir, para_decimal

#: Versão atual do formato de projeto.
SCHEMA_VERSION = 2

Projeto = dict[str, Any]


class ProjetoInvalidoError(ValueError):
    """O conteúdo não é um projeto do Maker Price 3D."""


class VersaoNaoSuportadaError(ProjetoInvalidoError):
    """O projeto foi salvo por uma versão mais nova do programa."""


def agora_iso() -> str:
    """Data/hora local em ISO 8601 (segundos)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


#: Seções e campos herdados da v1.x — nenhum foi removido.
CAMPOS_LEGADOS: dict[str, tuple[str, ...]] = {
    "material": ("resina", "suporte", "peso", "custo_fixo"),
    "energia": ("impressao", "lixa_retificadora", "lavagem_cura", "pintura"),
    "desgaste": (
        "preco_lcd",
        "vida_util",
        "tempo_total",
        "preco_fep",
        "durabilidade",
        "porcentagem_area",
        "manutencao_fixa_extra",
    ),
    "logistica": ("embrulho", "descontos", "impostos", "frete"),
    "mao_de_obra": ("ganho_por_hora", "horas_trabalhadas"),
}

CAMPOS_ACABAMENTO: dict[str, tuple[str, ...]] = {
    "lavagem": ("custo_solvente", "lavagens_por_peca", "litros_usados"),
    "lixa": ("custo_de_ponta", "vida_util_ponta", "pontas_usadas"),
    "pintura": ("custo_unidade_tinta", "ml_por_unidade", "uso_de_tinta_medio"),
}

#: Seções novas da v2.0.
CAMPOS_NOVOS: dict[str, tuple[str, ...]] = {
    "perdas": ("tanque", "lavagem", "suportes", "taxa_falha"),
    "custos_fixos": (
        "mensal",
        "horas_maquina_mes",
        "preco_impressora",
        "vida_util_impressora",
        "preco_mesa",
        "vida_util_mesa",
    ),
    "mesa": ("peso_total_mesa", "pecas_na_mesa", "altura_mm", "altura_camada_mm", "segundos_por_camada"),
    "extras": (
        "licenca_custo",
        "licenca_vendas_previstas",
        "luvas_custo",
        "luvas_pecas",
        "mascara_custo",
        "mascara_pecas",
        "filtro_custo",
        "filtro_pecas",
        "papel_por_peca",
        "clima_potencia_w",
        "clima_horas",
        "tarifa_kwh",
    ),
    "tributos": ("regime", "das_mensal", "vendas_mes"),
    "venda": (
        "canal_nome",
        "taxa_percentual",
        "taxa_fixa",
        "impostos_percentual",
        "preco_alvo",
        "acrescimo_premium",
    ),
}


def projeto_vazio(padroes: dict[str, Any] | None = None) -> Projeto:
    """Cria um projeto novo, opcionalmente com valores padrão das configurações.

    :param padroes: Valores iniciais no formato ``{"secao.campo": valor}``,
        por exemplo ``{"mao_de_obra.ganho_por_hora": "25"}`` ou ``{"lucro.estado": 30}``.
    """
    momento = agora_iso()
    projeto: Projeto = {
        "schema_version": SCHEMA_VERSION,
        "app_version": __version__,
        "meta": {
            "nome": "",
            "cliente": "",
            "observacoes": "",
            "quantidade": "1",
            "criado_em": momento,
            "modificado_em": momento,
        },
        "perfil": {"impressora_id": None, "resina_id": None, "canal_id": None},
    }
    for secao, campos in CAMPOS_LEGADOS.items():
        projeto[secao] = dict.fromkeys(campos, "")
    projeto["acabamento"] = {sub: dict.fromkeys(campos, "") for sub, campos in CAMPOS_ACABAMENTO.items()}
    projeto["despesas"] = {"tabela": []}
    projeto["lucro"] = {"estado": 0, "modo": "markup"}
    for secao, campos in CAMPOS_NOVOS.items():
        projeto[secao] = dict.fromkeys(campos, "")
    projeto["venda"]["acrescimo_premium"] = "25"
    projeto["tributos"]["regime"] = "nenhum"

    for chave, valor in (padroes or {}).items():
        definir_valor(projeto, chave, valor)
    return projeto


def obter_valor(projeto: Projeto, caminho: str, padrao: Any = "") -> Any:
    """Lê ``"secao.sub.campo"`` do projeto."""
    atual: Any = projeto
    for parte in caminho.split("."):
        if not isinstance(atual, dict) or parte not in atual:
            return padrao
        atual = atual[parte]
    return atual


def definir_valor(projeto: Projeto, caminho: str, valor: Any) -> None:
    """Escreve ``"secao.sub.campo"`` no projeto, criando os níveis que faltarem."""
    partes = caminho.split(".")
    atual = projeto
    for parte in partes[:-1]:
        atual = atual.setdefault(parte, {})
    atual[partes[-1]] = valor


def item_despesa(nome: str, tipo: str, quantidade: int, valor_unitario: Decimal | str) -> dict[str, str]:
    """Cria uma linha da tabela de despesas.

    Como na v1.x, o valor guardado é o total da linha: ``valor_unitario × quantidade``,
    com duas casas.
    """
    qtd = max(1, abs(int(quantidade)))
    unitario = abs(para_decimal(valor_unitario))
    total = arredondar(unitario * qtd)
    return {"nome": str(nome), "tipo": str(tipo), "quantidade": str(qtd), "valor": f"{total:.2f}"}


def valor_unitario_despesa(item: dict[str, str]) -> Decimal:
    """Valor unitário de uma linha (total ÷ quantidade), como na edição da v1.x."""
    qtd = para_decimal(item.get("quantidade"), Decimal(1))
    return dividir(para_decimal(item.get("valor")), qtd)


def _migrar_despesas_v1(tabela: Any) -> list[dict[str, str]]:
    """Converte linhas ``[nome, tipo, "2", "R$ 14,99"]`` para dicionários."""
    linhas: list[dict[str, str]] = []
    for linha in tabela or []:
        if isinstance(linha, dict):
            linhas.append({k: str(linha.get(k, "")) for k in ("nome", "tipo", "quantidade", "valor")})
            continue
        valores = [*list(linha), "", "", "", ""][:4]
        nome, tipo, qtd, valor = valores
        total = para_decimal(valor)
        linhas.append(
            {
                "nome": str(nome),
                "tipo": str(tipo),
                "quantidade": str(qtd or "1"),
                "valor": f"{total:.2f}",
            }
        )
    return linhas


def _como_texto(valor: Any) -> str:
    return "" if valor is None else str(valor)


def migrar(dados: Any) -> tuple[Projeto, bool]:
    """Converte qualquer versão conhecida para o formato atual.

    * Sem ``schema_version``: arquivo ``.json`` da v1.x (todas as chaves de
      ``_resetar_dados`` do menu principal antigo).
    * ``schema_version`` 2: formato atual; campos ausentes são completados.

    :return: ``(projeto, migrado)`` — ``migrado`` é ``True`` quando veio de versão antiga.
    :raises ProjetoInvalidoError: se não parecer um projeto do Maker Price 3D.
    :raises VersaoNaoSuportadaError: se vier de uma versão mais nova.
    """
    if not isinstance(dados, dict):
        raise ProjetoInvalidoError("O arquivo não contém um projeto válido.")

    versao = dados.get("schema_version")
    migrado = versao is None
    if versao is None:
        chaves_v1 = {"material", "energia", "desgaste", "acabamento", "despesas", "logistica", "mao_de_obra", "lucro"}
        if not chaves_v1 & dados.keys():
            raise ProjetoInvalidoError("Arquivo inválido: chave(s) não encontrada(s).")
    elif not isinstance(versao, int):
        raise ProjetoInvalidoError("Versão de projeto inválida.")
    elif versao > SCHEMA_VERSION:
        raise VersaoNaoSuportadaError(
            f"Este projeto foi salvo por uma versão mais nova (formato {versao}). Atualize o Maker Price 3D."
        )

    projeto = projeto_vazio()
    if isinstance(dados.get("meta"), dict):
        projeto["meta"].update({k: _como_texto(v) for k, v in dados["meta"].items()})
    if isinstance(dados.get("perfil"), dict):
        projeto["perfil"].update(dados["perfil"])

    for secao, campos in {**CAMPOS_LEGADOS, **CAMPOS_NOVOS}.items():
        origem = dados.get(secao)
        if isinstance(origem, dict):
            for campo in campos:
                if campo in origem:
                    projeto[secao][campo] = _como_texto(origem[campo])

    acabamento = dados.get("acabamento")
    if isinstance(acabamento, dict):
        for sub, campos in CAMPOS_ACABAMENTO.items():
            origem = acabamento.get(sub)
            if isinstance(origem, dict):
                for campo in campos:
                    if campo in origem:
                        projeto["acabamento"][sub][campo] = _como_texto(origem[campo])

    despesas = dados.get("despesas")
    if isinstance(despesas, dict):
        projeto["despesas"]["tabela"] = _migrar_despesas_v1(despesas.get("tabela"))

    lucro = dados.get("lucro")
    if isinstance(lucro, dict):
        estado = lucro.get("estado", 0)
        projeto["lucro"]["estado"] = estado if isinstance(estado, int | float) else _como_texto(estado)
        if lucro.get("modo") in ("markup", "margem"):
            projeto["lucro"]["modo"] = lucro["modo"]

    projeto["schema_version"] = SCHEMA_VERSION
    return projeto, migrado


def preparar_para_salvar(projeto: Projeto) -> Projeto:
    """Cópia do projeto com versão e data de modificação atualizadas."""
    copia = copy.deepcopy(projeto)
    copia["schema_version"] = SCHEMA_VERSION
    copia["app_version"] = __version__
    copia.setdefault("meta", {})["modificado_em"] = agora_iso()
    return copia
