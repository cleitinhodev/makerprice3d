# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Tela genérica de cadastro (lista + formulário) usada por perfis, clientes, estoque etc."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from makerprice3d.core.numeros import formatar_moeda, formatar_numero, para_decimal, texto_valido
from makerprice3d.services.exportacao import exportar_tabela_csv
from makerprice3d.ui.contexto import Contexto
from makerprice3d.ui.widgets import CampoNumerico

Registro = dict[str, Any]


@dataclass
class Campo:
    """Campo de formulário/coluna.

    ``tipo``: texto, numero, moeda, data, multilinha, foto, booleano, escolha, ref:<tabela>.
    """

    nome: str
    rotulo: str
    tipo: str = "texto"
    dica: str = ""
    opcoes: Sequence[tuple[str, str]] = ()
    obrigatorio: bool = False
    padrao: str = ""
    na_lista: bool = True
    no_formulario: bool = True
    calcular: Callable[[Registro], str] | None = None


@dataclass
class Acao:
    """Botão extra na barra da tela de cadastro."""

    texto: str
    funcao: Callable[[Registro | None], None]
    precisa_selecao: bool = True
    primario: bool = False


@dataclass
class Especificacao:
    """Configuração de uma tela de cadastro."""

    tabela: str
    titulo: str
    subtitulo: str
    campos: list[Campo]
    acoes: list[Acao] = field(default_factory=list)
    destacar: Callable[[Registro], str | None] | None = None
    filtros: dict[str, Any] = field(default_factory=dict)
    preparar: Callable[[Registro], Registro] | None = None


def nome_referencia(contexto: Contexto, tabela: str, ident: Any) -> str:
    """Nome do registro referenciado (ou vazio)."""
    if ident in (None, ""):
        return ""
    try:
        registro = contexto.banco.obter(tabela, int(ident))
    except (TypeError, ValueError):
        return ""
    return str(registro.get("nome", f"#{ident}")) if registro else ""


def formatar_celula(contexto: Contexto, campo: Campo, valor: Any) -> str:
    """Texto exibido na lista."""
    if valor in (None, ""):
        return ""
    if campo.tipo == "moeda":
        return formatar_moeda(para_decimal(valor))
    if campo.tipo == "numero":
        numero = para_decimal(valor)
        return formatar_numero(numero, 0 if numero == numero.to_integral_value() else 2)
    if campo.tipo == "booleano":
        return "Sim" if str(valor) in ("1", "true", "True", "sim") else "Não"
    if campo.tipo == "escolha":
        return dict(campo.opcoes).get(str(valor), str(valor))
    if campo.tipo.startswith("ref:"):
        return nome_referencia(contexto, campo.tipo[4:], valor)
    if campo.tipo == "data":
        try:
            return date.fromisoformat(str(valor)[:10]).strftime("%d/%m/%Y")
        except ValueError:
            return str(valor)
    if campo.tipo == "foto":
        return Path(str(valor)).name
    return str(valor)


class DialogoRegistro(QDialog):
    """Formulário gerado a partir da lista de campos."""

    def __init__(self, contexto: Contexto, spec: Especificacao, registro: Registro | None, parent=None) -> None:
        super().__init__(parent)
        self.contexto = contexto
        self.spec = spec
        self.setWindowTitle(("Editar " if registro else "Novo ") + spec.titulo.lower().rstrip("s"))
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        formulario = QFormLayout()
        self.widgets: dict[str, QWidget] = {}
        registro = registro or {}
        for campo in spec.campos:
            if not campo.no_formulario:
                continue
            valor = registro.get(campo.nome, campo.padrao)
            widget = self._criar(campo, valor)
            if campo.dica:
                widget.setToolTip(campo.dica)
            formulario.addRow(campo.rotulo + (" *" if campo.obrigatorio else ""), widget)
            self.widgets[campo.nome] = widget
        layout.addLayout(formulario)
        self.erro = QLabel("")
        self.erro.setStyleSheet("color: #ff5c6c;")
        layout.addWidget(self.erro)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self._validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _criar(self, campo: Campo, valor: Any) -> QWidget:
        texto = "" if valor is None else str(valor)
        if campo.tipo == "booleano":
            if isinstance(valor, bool):
                texto = "1" if valor else "0"
            texto = texto if texto in ("1", "0") else (campo.padrao or "1")
        if campo.tipo in ("numero", "moeda"):
            widget = CampoNumerico(campo.nome, campo.dica, "")
            widget.definir_texto(texto)
            return widget
        if campo.tipo == "multilinha":
            widget = QPlainTextEdit(texto)
            widget.setFixedHeight(70)
            return widget
        if campo.tipo == "data":
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("dd/MM/yyyy")
            data = QDate.fromString(texto[:10], "yyyy-MM-dd")
            widget.setDate(data if data.isValid() else QDate.currentDate())
            return widget
        if campo.tipo in ("escolha", "booleano") or campo.tipo.startswith("ref:"):
            widget = QComboBox()
            if campo.tipo == "booleano":
                opcoes: Sequence[tuple[Any, str]] = (("1", "Sim"), ("0", "Não"))
            elif campo.tipo == "escolha":
                opcoes = campo.opcoes
            else:
                opcoes = [(None, "—")] + [
                    (r["id"], r.get("nome", f"#{r['id']}")) for r in self.contexto.banco.listar(campo.tipo[4:])
                ]
            for dado, rotulo in opcoes:
                widget.addItem(rotulo, dado)
            if campo.tipo.startswith("ref:"):
                try:
                    alvo: Any = int(texto) if texto else None
                except ValueError:
                    alvo = None
            else:
                alvo = texto
            widget.setCurrentIndex(max(0, widget.findData(alvo)))
            return widget
        if campo.tipo == "foto":
            caixa = QWidget()
            linha = QHBoxLayout(caixa)
            linha.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(texto)
            edit.setReadOnly(True)
            botao = QPushButton("Escolher…")

            def escolher() -> None:
                arquivo, _ = QFileDialog.getOpenFileName(self, "Foto", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
                if arquivo:
                    edit.setText(arquivo)

            botao.clicked.connect(escolher)
            linha.addWidget(edit, 1)
            linha.addWidget(botao)
            caixa.edit = edit  # type: ignore[attr-defined]
            return caixa
        widget = QLineEdit(texto)
        return widget

    def _ler(self, campo: Campo, widget: QWidget) -> Any:
        if isinstance(widget, QPlainTextEdit):
            return widget.toPlainText().strip()
        if isinstance(widget, QDateEdit):
            return widget.date().toString("yyyy-MM-dd")
        if isinstance(widget, QComboBox):
            return widget.currentData()
        if campo.tipo == "foto":
            return widget.edit.text()  # type: ignore[attr-defined]
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return None

    def _validar(self) -> None:
        for campo in self.spec.campos:
            widget = self.widgets.get(campo.nome)
            if widget is None:
                continue
            valor = self._ler(campo, widget)
            if campo.obrigatorio and valor in (None, ""):
                self.erro.setText(f"Preencha: {campo.rotulo}")
                return
            if campo.tipo in ("numero", "moeda") and not texto_valido(valor or ""):
                self.erro.setText(f"Número inválido em: {campo.rotulo}")
                return
        self.accept()

    def dados(self) -> Registro:
        """Valores digitados."""
        return {c.nome: self._ler(c, self.widgets[c.nome]) for c in self.spec.campos if c.nome in self.widgets}


class PaginaCadastro(QWidget):
    """Lista com busca, novo/editar/excluir, exportar CSV e ações extras."""

    def __init__(self, contexto: Contexto, spec: Especificacao, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.contexto = contexto
        self.spec = spec
        self.registros: list[Registro] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        titulo = QLabel(spec.titulo)
        titulo.setObjectName("tituloCard")
        layout.addWidget(titulo)
        if spec.subtitulo:
            sub = QLabel(spec.subtitulo)
            sub.setObjectName("suave")
            sub.setWordWrap(True)
            layout.addWidget(sub)
        barra = QHBoxLayout()
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar…")
        self.busca.textChanged.connect(self._filtrar)
        barra.addWidget(self.busca, 1)
        self.botoes_selecao: list[QPushButton] = []
        for texto, funcao, precisa, primario in (
            ("Novo", self.novo, False, True),
            ("Editar", self.editar, True, False),
            ("Excluir", self.excluir, True, False),
        ):
            botao = QPushButton(texto)
            if primario:
                botao.setObjectName("primario")
            botao.clicked.connect(funcao)
            barra.addWidget(botao)
            if precisa:
                self.botoes_selecao.append(botao)
        for acao in spec.acoes:
            botao = QPushButton(acao.texto)
            if acao.primario:
                botao.setObjectName("primario")
            botao.clicked.connect(lambda _=False, a=acao: a.funcao(self.selecionado()))
            barra.addWidget(botao)
            if acao.precisa_selecao:
                self.botoes_selecao.append(botao)
        exportar = QPushButton("Exportar CSV")
        exportar.clicked.connect(self.exportar_csv)
        barra.addWidget(exportar)
        layout.addLayout(barra)
        self.extra = QVBoxLayout()
        layout.addLayout(self.extra)
        self.colunas = [c for c in spec.campos if c.na_lista]
        self.tabela = QTableWidget(0, len(self.colunas))
        self.tabela.setHorizontalHeaderLabels([c.rotulo for c in self.colunas])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.doubleClicked.connect(self.editar)
        self.tabela.itemSelectionChanged.connect(self._atualizar_botoes)
        layout.addWidget(self.tabela, 1)
        contexto.dados_alterados.connect(self._ao_mudar_dados)
        self.atualizar()

    def _ao_mudar_dados(self, tabela: str) -> None:
        if not tabela or tabela == self.spec.tabela or any(c.tipo == f"ref:{tabela}" for c in self.spec.campos):
            self.atualizar()

    def atualizar(self) -> None:
        """Recarrega os registros do banco."""
        self.registros = self.contexto.banco.listar(self.spec.tabela, **self.spec.filtros)
        self._filtrar()

    def _filtrar(self) -> None:
        termo = self.busca.text().strip().lower()
        visiveis = [
            r
            for r in self.registros
            if not termo
            or any(
                termo in formatar_celula(self.contexto, c, r.get(c.nome)).lower()
                for c in self.colunas
                if not c.calcular
            )
        ]
        self.tabela.setRowCount(len(visiveis))
        for linha, registro in enumerate(visiveis):
            cor = self.spec.destacar(registro) if self.spec.destacar else None
            for coluna, campo in enumerate(self.colunas):
                texto = (
                    campo.calcular(registro)
                    if campo.calcular
                    else formatar_celula(self.contexto, campo, registro.get(campo.nome))
                )
                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, registro["id"])
                if campo.tipo in ("moeda", "numero"):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if campo.tipo == "foto" and registro.get(campo.nome):
                    mapa = QPixmap(str(registro[campo.nome]))
                    if not mapa.isNull():
                        item.setIcon(mapa.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio))
                if cor:
                    item.setForeground(QColor(cor))
                self.tabela.setItem(linha, coluna, item)
        self.tabela.resizeColumnsToContents()
        self._atualizar_botoes()

    def _atualizar_botoes(self) -> None:
        tem = self.selecionado() is not None
        for botao in self.botoes_selecao:
            botao.setEnabled(tem)

    def selecionado(self) -> Registro | None:
        """Registro da linha selecionada."""
        linhas = self.tabela.selectionModel().selectedRows()
        if not linhas:
            return None
        ident = self.tabela.item(linhas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return next((r for r in self.registros if r["id"] == ident), None)

    def _salvar(self, dados: Registro, ident: int | None) -> int:
        if self.spec.preparar:
            dados = self.spec.preparar(dados)
        if ident is None:
            ident = self.contexto.banco.inserir(self.spec.tabela, dados)
        else:
            self.contexto.banco.atualizar(self.spec.tabela, ident, dados)
        self.contexto.avisar(self.spec.tabela)
        return ident

    def novo(self) -> None:
        """Cria um registro."""
        dialogo = DialogoRegistro(self.contexto, self.spec, None, self)
        if dialogo.exec():
            self._salvar(dialogo.dados(), None)

    def editar(self) -> None:
        """Edita o selecionado."""
        registro = self.selecionado()
        if not registro:
            return
        dialogo = DialogoRegistro(self.contexto, self.spec, registro, self)
        if dialogo.exec():
            self._salvar(dialogo.dados(), registro["id"])

    def excluir(self) -> None:
        """Exclui o selecionado após confirmação."""
        registro = self.selecionado()
        if not registro:
            return
        nome = registro.get("nome") or f"#{registro['id']}"
        resposta = QMessageBox.question(self, "Excluir", f"Excluir “{nome}”? Essa ação não pode ser desfeita.")
        if resposta == QMessageBox.StandardButton.Yes:
            self.contexto.banco.excluir(self.spec.tabela, registro["id"])
            self.contexto.avisar(self.spec.tabela)

    def exportar_csv(self) -> None:
        """Exporta a lista em CSV (abre no Excel/LibreOffice)."""
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", f"{self.spec.tabela}.csv", "CSV (*.csv)")
        if not caminho:
            return
        registros = [
            {
                c.rotulo: c.calcular(r) if c.calcular else formatar_celula(self.contexto, c, r.get(c.nome))
                for c in self.colunas
            }
            for r in self.registros
        ]
        exportar_tabela_csv(caminho, registros, [c.rotulo for c in self.colunas])


def decimal_de(registro: Registro, campo: str) -> Decimal:
    """Atalho para ler número de um registro."""
    return para_decimal(registro.get(campo))
