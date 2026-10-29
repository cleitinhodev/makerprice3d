# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Banco local (SQLite) com perfis, biblioteca, cadastros e configurações.

Valores em dinheiro são guardados como texto (``Decimal`` serializado) para não perder
centavos. Colunas listadas em ``colunas_json`` são gravadas como JSON.
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

#: Versão do esquema do banco (para migrações futuras).
VERSAO_BANCO = 1


@dataclass(frozen=True)
class Tabela:
    """Definição simples de uma tabela."""

    nome: str
    colunas: tuple[str, ...]
    colunas_json: tuple[str, ...] = ()
    ordem: str = "id"


TABELAS: dict[str, Tabela] = {
    t.nome: t
    for t in (
        Tabela(
            "impressoras",
            (
                "nome",
                "potencia_w",
                "preco",
                "vida_util_h",
                "preco_lcd",
                "vida_lcd_h",
                "preco_fep",
                "durabilidade_fep",
                "preco_mesa",
                "vida_mesa_h",
                "data_compra",
                "observacoes",
            ),
            ordem="nome COLLATE NOCASE",
        ),
        Tabela(
            "resinas",
            ("nome", "marca", "tipo", "cor", "preco_litro", "densidade", "observacoes"),
            ordem="nome COLLATE NOCASE",
        ),
        Tabela("canais", ("nome", "taxa_percentual", "taxa_fixa", "observacoes"), ordem="id"),
        Tabela("clientes", ("nome", "telefone", "email", "cidade", "observacoes"), ordem="nome COLLATE NOCASE"),
        Tabela(
            "produtos",
            (
                "nome",
                "escala",
                "preco",
                "custo",
                "peso_g",
                "tempo_h",
                "resina_id",
                "impressora_id",
                "foto",
                "projeto",
                "observacoes",
            ),
            colunas_json=("projeto",),
            ordem="nome COLLATE NOCASE",
        ),
        Tabela("kits", ("nome", "desconto_percentual", "itens", "observacoes"), colunas_json=("itens",)),
        Tabela(
            "orcamentos",
            (
                "cliente_id",
                "data",
                "validade_dias",
                "prazo_entrega",
                "pagamento",
                "desconto_percentual",
                "frete",
                "itens",
                "status",
                "pedido_id",
                "observacoes",
            ),
            colunas_json=("itens",),
            ordem="id DESC",
        ),
        Tabela(
            "pedidos",
            (
                "orcamento_id",
                "cliente_id",
                "data",
                "data_conclusao",
                "status",
                "prazo_entrega",
                "pagamento",
                "itens",
                "total",
                "custo",
                "impressora_id",
                "estoque_baixado",
                "observacoes",
            ),
            colunas_json=("itens",),
            ordem="id DESC",
        ),
        Tabela(
            "estoque",
            ("nome", "categoria", "unidade", "quantidade", "minimo", "custo_unitario", "consumo_por_peca", "resina_id"),
            ordem="categoria, nome COLLATE NOCASE",
        ),
        Tabela("movimentos_estoque", ("estoque_id", "data", "quantidade", "motivo", "pedido_id"), ordem="id DESC"),
        Tabela(
            "impressoes",
            ("impressora_id", "resina_id", "data", "horas", "camadas", "sucesso", "motivo_falha", "observacoes"),
            ordem="data DESC, id DESC",
        ),
        Tabela(
            "manutencoes",
            ("impressora_id", "data", "tipo", "peca", "custo", "observacoes"),
            ordem="data DESC, id DESC",
        ),
    )
}

#: Canais de venda iniciais. As taxas são EXEMPLOS editáveis — confira sempre o valor atual.
CANAIS_PADRAO: tuple[tuple[str, str, str, str], ...] = (
    ("Venda direta", "0", "0", "Sem taxas (Pix/dinheiro)."),
    ("Mercado Livre (exemplo)", "13", "6", "Valores de EXEMPLO — confira a tarifa atual da sua categoria."),
    ("Shopee (exemplo)", "20", "4", "Valores de EXEMPLO — confira a comissão atual do seu plano."),
    ("Elo7 (exemplo)", "18", "0", "Valores de EXEMPLO — confira a comissão atual."),
    ("Maquininha crédito (exemplo)", "4.99", "0", "Valores de EXEMPLO — use a taxa do seu contrato."),
)

#: Configurações globais e valores padrão.
CONFIG_PADRAO: dict[str, str] = {
    "loja_nome": "",
    "loja_telefone": "",
    "moeda": "R$",
    "tarifa_kwh": "",
    "valor_hora": "",
    "impostos_percentual": "",
    "regime_tributario": "nenhum",
    "das_mensal": "",
    "vendas_mes": "",
    "custo_fixo_mensal": "",
    "horas_maquina_mes": "",
    "margem_padrao": "30",
    "acrescimo_premium": "25",
    "validade_orcamento_dias": "7",
    "tema": "escuro",
    "autosave_segundos": "60",
    "backups_manter": "10",
    "ultimo_backup": "",
    "recentes": "[]",
}

MAX_RECENTES = 10


def agora() -> str:
    """Data/hora local ISO (segundos)."""
    return datetime.now().isoformat(timespec="seconds")


class Banco:
    """Acesso ao SQLite. Use uma instância por aplicação."""

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(str(self.caminho))
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        self._criar_esquema()

    # --- esquema --------------------------------------------------------------------
    def _criar_esquema(self) -> None:
        with self.conexao:
            self.conexao.execute("CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT)")
            for tabela in TABELAS.values():
                colunas = ", ".join(f"{c} TEXT" for c in tabela.colunas)
                self.conexao.execute(
                    f"CREATE TABLE IF NOT EXISTS {tabela.nome} (id INTEGER PRIMARY KEY AUTOINCREMENT, {colunas})"
                )
                existentes = {r["name"] for r in self.conexao.execute(f"PRAGMA table_info({tabela.nome})")}
                for coluna in tabela.colunas:
                    if coluna not in existentes:
                        self.conexao.execute(f"ALTER TABLE {tabela.nome} ADD COLUMN {coluna} TEXT")
            versao = self.conexao.execute("PRAGMA user_version").fetchone()[0]
            if versao == 0:
                for chave, valor in CONFIG_PADRAO.items():
                    self.conexao.execute(
                        "INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, valor)
                    )
                for nome, pct, fixo, obs in CANAIS_PADRAO:
                    self.conexao.execute(
                        "INSERT INTO canais (nome, taxa_percentual, taxa_fixa, observacoes) VALUES (?, ?, ?, ?)",
                        (nome, pct, fixo, obs),
                    )
                self.conexao.execute(f"PRAGMA user_version = {VERSAO_BANCO}")

    def fechar(self) -> None:
        """Fecha a conexão."""
        self.conexao.close()

    # --- configurações --------------------------------------------------------------
    def config(self, chave: str, padrao: str | None = None) -> str:
        """Lê uma configuração global."""
        linha = self.conexao.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,)).fetchone()
        if linha is None:
            return CONFIG_PADRAO.get(chave, "") if padrao is None else padrao
        return linha["valor"] or ""

    def todas_configs(self) -> dict[str, str]:
        """Todas as configurações (padrões + gravadas)."""
        dados = dict(CONFIG_PADRAO)
        dados.update({r["chave"]: r["valor"] or "" for r in self.conexao.execute("SELECT * FROM configuracoes")})
        return dados

    def definir_config(self, chave: str, valor: Any) -> None:
        """Grava uma configuração global."""
        with self.conexao:
            self.conexao.execute(
                "INSERT INTO configuracoes (chave, valor) VALUES (?, ?) "
                "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
                (chave, "" if valor is None else str(valor)),
            )

    # --- recentes -------------------------------------------------------------------
    def recentes(self) -> list[str]:
        """Projetos abertos recentemente (mais recente primeiro)."""
        try:
            lista = json.loads(self.config("recentes") or "[]")
        except json.JSONDecodeError:
            return []
        return [str(c) for c in lista if isinstance(c, str)]

    def adicionar_recente(self, caminho: str | Path) -> list[str]:
        """Coloca o projeto no topo da lista de recentes."""
        caminho = str(caminho)
        lista = [c for c in self.recentes() if c != caminho]
        lista.insert(0, caminho)
        lista = lista[:MAX_RECENTES]
        self.definir_config("recentes", json.dumps(lista, ensure_ascii=False))
        return lista

    def remover_recente(self, caminho: str | Path) -> None:
        """Tira um projeto da lista (ex.: arquivo apagado)."""
        lista = [c for c in self.recentes() if c != str(caminho)]
        self.definir_config("recentes", json.dumps(lista, ensure_ascii=False))

    # --- CRUD genérico --------------------------------------------------------------
    def _tabela(self, nome: str) -> Tabela:
        if nome not in TABELAS:
            raise KeyError(f"Tabela desconhecida: {nome}")
        return TABELAS[nome]

    def _para_dict(self, tabela: Tabela, linha: sqlite3.Row) -> dict[str, Any]:
        dados = dict(linha)
        for coluna in tabela.colunas_json:
            texto = dados.get(coluna)
            try:
                dados[coluna] = json.loads(texto) if texto else None
            except json.JSONDecodeError:
                dados[coluna] = None
        for coluna in tabela.colunas:
            if coluna.endswith("_id") and dados.get(coluna) not in (None, ""):
                with contextlib.suppress(TypeError, ValueError):
                    dados[coluna] = int(dados[coluna])
        if "sucesso" in dados:
            dados["sucesso"] = str(dados.get("sucesso")) in ("1", "True", "true")
        if "estoque_baixado" in dados:
            dados["estoque_baixado"] = str(dados.get("estoque_baixado")) in ("1", "True", "true")
        return dados

    def _valores(self, tabela: Tabela, dados: dict[str, Any]) -> dict[str, Any]:
        valores: dict[str, Any] = {}
        for coluna in tabela.colunas:
            if coluna not in dados:
                continue
            valor = dados[coluna]
            if coluna in tabela.colunas_json:
                valor = json.dumps(valor, ensure_ascii=False) if valor is not None else None
            elif isinstance(valor, bool):
                valor = "1" if valor else "0"
            elif valor is not None:
                valor = str(valor)
            valores[coluna] = valor
        return valores

    def listar(self, nome: str, **filtros: Any) -> list[dict[str, Any]]:
        """Lista registros, com filtros de igualdade opcionais (``cliente_id=3``)."""
        tabela = self._tabela(nome)
        where, parametros = "", []
        if filtros:
            partes = []
            for coluna, valor in filtros.items():
                if coluna not in tabela.colunas and coluna != "id":
                    raise KeyError(coluna)
                partes.append(f"{coluna} = ?")
                parametros.append(str(valor))
            where = " WHERE " + " AND ".join(partes)
        sql = f"SELECT * FROM {tabela.nome}{where} ORDER BY {tabela.ordem}"
        return [self._para_dict(tabela, linha) for linha in self.conexao.execute(sql, parametros)]

    def obter(self, nome: str, id_registro: int) -> dict[str, Any] | None:
        """Busca um registro pelo id."""
        tabela = self._tabela(nome)
        linha = self.conexao.execute(f"SELECT * FROM {tabela.nome} WHERE id = ?", (id_registro,)).fetchone()
        return self._para_dict(tabela, linha) if linha else None

    def inserir(self, nome: str, dados: dict[str, Any]) -> int:
        """Insere e devolve o novo id."""
        tabela = self._tabela(nome)
        valores = self._valores(tabela, dados)
        if not valores:
            valores = {tabela.colunas[0]: ""}
        colunas = ", ".join(valores)
        marcadores = ", ".join("?" for _ in valores)
        with self.conexao:
            cursor = self.conexao.execute(
                f"INSERT INTO {tabela.nome} ({colunas}) VALUES ({marcadores})", list(valores.values())
            )
        return int(cursor.lastrowid or 0)

    def atualizar(self, nome: str, id_registro: int, dados: dict[str, Any]) -> None:
        """Atualiza só as colunas informadas."""
        tabela = self._tabela(nome)
        valores = self._valores(tabela, dados)
        if not valores:
            return
        atribuicoes = ", ".join(f"{c} = ?" for c in valores)
        with self.conexao:
            self.conexao.execute(
                f"UPDATE {tabela.nome} SET {atribuicoes} WHERE id = ?", [*valores.values(), id_registro]
            )

    def excluir(self, nome: str, id_registro: int) -> None:
        """Remove um registro."""
        tabela = self._tabela(nome)
        with self.conexao:
            self.conexao.execute(f"DELETE FROM {tabela.nome} WHERE id = ?", (id_registro,))

    def exportar_tudo(self) -> dict[str, Any]:
        """Todos os dados em um dicionário (para exportação completa em JSON)."""
        return {
            "versao_banco": VERSAO_BANCO,
            "exportado_em": agora(),
            "configuracoes": self.todas_configs(),
            **{nome: self.listar(nome) for nome in TABELAS},
        }

    def backup_para(self, destino: str | Path) -> Path:
        """Cópia consistente do banco usando a API de backup do SQLite."""
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(str(destino))) as copia:
            self.conexao.backup(copia)
        return destino

    def inserir_varios(self, nome: str, registros: Iterable[dict[str, Any]]) -> list[int]:
        """Atalho para inserir vários registros."""
        return [self.inserir(nome, r) for r in registros]
