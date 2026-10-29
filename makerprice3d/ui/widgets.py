# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Componentes visuais reutilizáveis: cards, campos com validação, selos e gráfico."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from makerprice3d.core.numeros import formatar_moeda, texto_valido


def cor_texto_para(fundo_hex: str) -> str:
    """Preto ou branco, o que tiver mais contraste com a cor de fundo."""
    cor = QColor(fundo_hex)
    luminancia = 0.299 * cor.red() + 0.587 * cor.green() + 0.114 * cor.blue()
    return "#111111" if luminancia > 150 else "#ffffff"


class Selo(QLabel):
    """Etiqueta colorida com o subtotal de um card (como os rótulos coloridos da v1.x)."""

    def __init__(self, cor: str, parent: QWidget | None = None) -> None:
        super().__init__("R$ 0,00", parent)
        self.setObjectName("selo")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(84)
        self.definir_cor(cor)

    def definir_cor(self, cor: str) -> None:
        """Muda a cor de fundo."""
        self.setStyleSheet(f"background: {cor}; color: {cor_texto_para(cor)};")

    def definir_valor(self, valor: Decimal) -> None:
        """Mostra o valor formatado em reais."""
        self.setText(formatar_moeda(valor))


class CampoNumerico(QLineEdit):
    """Campo de número com validação em tempo real (vírgula ou ponto).

    Campo inválido fica com borda vermelha e uma dica explicando o problema.
    """

    valor_alterado = Signal(str, str)  # caminho, texto

    def __init__(self, caminho: str, dica: str = "", placeholder: str = "0,00", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.caminho = caminho
        self.dica_base = dica
        self.setPlaceholderText(placeholder)
        self.setToolTip(dica)
        self.setMinimumWidth(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.textChanged.connect(self._ao_mudar)

    @property
    def valido(self) -> bool:
        """``True`` se vazio ou número válido."""
        return texto_valido(self.text())

    def _ao_mudar(self, texto: str) -> None:
        self._atualizar_estado()
        self.valor_alterado.emit(self.caminho, texto)

    def _atualizar_estado(self) -> None:
        invalido = not self.valido
        if self.property("invalido") != invalido:
            self.setProperty("invalido", invalido)
            self.style().unpolish(self)
            self.style().polish(self)
        self.setToolTip(
            "Valor inválido: use apenas números (ex.: 12,50)." + (f"\n{self.dica_base}" if self.dica_base else "")
            if invalido
            else self.dica_base
        )

    def definir_texto(self, texto: str) -> None:
        """Muda o texto sem emitir ``valor_alterado``."""
        self.blockSignals(True)
        self.setText("" if texto is None else str(texto))
        self.blockSignals(False)
        self._atualizar_estado()


def rotulo_campo(texto: str) -> QLabel:
    """Rótulo pequeno acima de um campo."""
    rotulo = QLabel(texto)
    rotulo.setObjectName("rotuloCampo")
    rotulo.setWordWrap(True)
    return rotulo


class Card(QFrame):
    """Cartão com título, selo de subtotal opcional e um grid de campos."""

    def __init__(
        self,
        titulo: str,
        cor: str | None = None,
        subtitulo: str = "",
        novo: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        cabecalho = QHBoxLayout()
        cabecalho.setSpacing(8)
        if cor:
            ponto = QLabel()
            ponto.setFixedSize(10, 10)
            ponto.setStyleSheet(f"background: {cor}; border-radius: 5px;")
            cabecalho.addWidget(ponto)
        caixa_titulo = QVBoxLayout()
        caixa_titulo.setSpacing(0)
        linha_titulo = QHBoxLayout()
        self.rotulo_titulo = QLabel(titulo)
        self.rotulo_titulo.setObjectName("tituloCard")
        linha_titulo.addWidget(self.rotulo_titulo)
        if novo:
            etiqueta = QLabel("NOVO")
            etiqueta.setObjectName("novo")
            linha_titulo.addWidget(etiqueta)
        linha_titulo.addStretch(1)
        caixa_titulo.addLayout(linha_titulo)
        if subtitulo:
            sub = QLabel(subtitulo)
            sub.setObjectName("subtituloCard")
            sub.setWordWrap(True)
            caixa_titulo.addWidget(sub)
        cabecalho.addLayout(caixa_titulo, 1)
        self.selo: Selo | None = None
        if cor:
            self.selo = Selo(cor)
            cabecalho.addWidget(self.selo, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(cabecalho)

        self.grade = QGridLayout()
        self.grade.setHorizontalSpacing(12)
        self.grade.setVerticalSpacing(4)
        layout.addLayout(self.grade)
        self.corpo = layout
        self._linha = 0
        self._coluna = 0

    def adicionar_campo(self, rotulo: str, widget: QWidget, colunas: int = 3) -> QWidget:
        """Adiciona rótulo + campo no próximo espaço livre do grid."""
        if self._coluna >= colunas:
            self._coluna = 0
            self._linha += 2
        self.grade.addWidget(rotulo_campo(rotulo), self._linha, self._coluna)
        self.grade.addWidget(widget, self._linha + 1, self._coluna)
        self._coluna += 1
        return widget

    def nova_linha(self) -> None:
        """Força os próximos campos a começarem numa nova linha."""
        if self._coluna:
            self._coluna = 0
            self._linha += 2


class GradeResponsiva(QWidget):
    """Organiza cards em colunas conforme a largura disponível (janela redimensionável)."""

    def __init__(self, largura_minima_coluna: int = 400, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.largura_minima = largura_minima_coluna
        self.cards: list[QWidget] = []
        self._grade = QGridLayout(self)
        self._grade.setContentsMargins(0, 0, 0, 0)
        self._grade.setSpacing(14)
        self._colunas = 0

    def adicionar(self, card: QWidget) -> None:
        """Inclui um card."""
        self.cards.append(card)
        self._reorganizar(force=True)

    def resizeEvent(self, evento) -> None:  # noqa: N802 - API do Qt
        super().resizeEvent(evento)
        self._reorganizar()

    def _reorganizar(self, force: bool = False) -> None:
        espaco = self._grade.spacing()
        colunas = max(1, min(3, (self.width() + espaco) // (self.largura_minima + espaco)))
        maior = max((c.minimumSizeHint().width() for c in self.cards), default=0)
        while colunas > 1 and colunas * maior + (colunas - 1) * espaco > self.width():
            colunas -= 1
        if colunas == self._colunas and not force:
            return
        self._colunas = colunas
        for card in self.cards:
            self._grade.removeWidget(card)
        alturas = [0] * colunas
        listas: list[list[QWidget]] = [[] for _ in range(colunas)]
        for card in self.cards:
            indice = alturas.index(min(alturas))
            listas[indice].append(card)
            alturas[indice] += card.sizeHint().height()
        for coluna, lista in enumerate(listas):
            for linha, card in enumerate(lista):
                self._grade.addWidget(card, linha, coluna, Qt.AlignmentFlag.AlignTop)
            self._grade.setRowStretch(len(lista), 1)
        for coluna in range(3):
            self._grade.setColumnStretch(coluna, 1 if coluna < colunas else 0)


class GraficoComposicao(QWidget):
    """Barra empilhada animada com a composição do preço (mesma ideia do gráfico da v1.x).

    Cada fatia é proporcional ao valor; a legenda mostra valor e percentual.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fatias: list[tuple[str, str, float]] = []
        self._anteriores: list[float] = []
        self._progresso = 1.0
        self._animacao = QPropertyAnimation(self, b"progresso", self)
        self._animacao.setDuration(260)
        self._animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cor_vazio = QColor("#2a2f3a")

    def sizeHint(self) -> QSize:  # noqa: N802 - API do Qt
        return QSize(300, 28)

    def _get_progresso(self) -> float:
        return self._progresso

    def _set_progresso(self, valor: float) -> None:
        self._progresso = valor
        self.update()

    progresso = Property(float, _get_progresso, _set_progresso)

    def definir_fatias(self, fatias: Sequence[tuple[str, str, Decimal]]) -> None:
        """``[(rótulo, cor, valor), ...]``"""
        atuais = self._valores_interpolados()
        self._fatias = [(r, c, float(v)) for r, c, v in fatias]
        self._anteriores = atuais if len(atuais) == len(self._fatias) else [0.0] * len(self._fatias)
        self._animacao.stop()
        self._animacao.setStartValue(0.0)
        self._animacao.setEndValue(1.0)
        self._animacao.start()

    def _valores_interpolados(self) -> list[float]:
        if not self._fatias:
            return []
        if len(self._anteriores) != len(self._fatias):
            return [v for _, _, v in self._fatias]
        t = self._progresso
        return [a + (v - a) * t for a, (_, _, v) in zip(self._anteriores, self._fatias, strict=False)]

    def paintEvent(self, _evento) -> None:  # noqa: N802 - API do Qt
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(self.rect()).adjusted(1, 4, -1, -4)
        caminho = QPainterPath()
        caminho.addRoundedRect(area, area.height() / 2, area.height() / 2)
        pintor.setClipPath(caminho)
        pintor.fillRect(area, self.cor_vazio)
        valores = self._valores_interpolados()
        total = sum(valores)
        if total > 0:
            x = area.left()
            for (_, cor, _), valor in zip(self._fatias, valores, strict=False):
                largura = area.width() * valor / total
                pintor.fillRect(QRectF(x, area.top(), largura + 0.5, area.height()), QColor(cor))
                x += largura
        pintor.end()


class Legenda(QWidget):
    """Legenda do gráfico em grade: bolinha, nome, valor e %."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grade = QGridLayout(self)
        self._grade.setContentsMargins(0, 0, 0, 0)
        self._grade.setHorizontalSpacing(10)
        self._grade.setVerticalSpacing(2)

    def definir(self, fatias: Sequence[tuple[str, str, Decimal]], colunas: int = 2) -> None:
        """Recria a legenda (fatias zeradas são omitidas)."""
        while self._grade.count():
            item = self._grade.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        total = sum((v for _, _, v in fatias), Decimal(0))
        visiveis = [f for f in fatias if f[2] > 0]
        for indice, (rotulo, cor, valor) in enumerate(visiveis):
            linha, coluna = divmod(indice, colunas)
            ponto = QLabel()
            ponto.setFixedSize(9, 9)
            ponto.setStyleSheet(f"background: {cor}; border-radius: 4px;")
            pct = (valor / total * 100) if total else Decimal(0)
            texto = QLabel(f"{rotulo} {formatar_moeda(valor)} · {pct:.0f}%")
            texto.setObjectName("suave")
            texto.setToolTip(texto.text())
            texto.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            texto.setStyleSheet("font-size: 8.5pt;")
            caixa = QHBoxLayout()
            caixa.setSpacing(6)
            caixa.addWidget(ponto)
            caixa.addWidget(texto, 1)
            contenedor = QWidget()
            contenedor.setLayout(caixa)
            caixa.setContentsMargins(0, 0, 0, 0)
            self._grade.addWidget(contenedor, linha, coluna)


def separador() -> QFrame:
    """Linha horizontal discreta."""
    linha = QFrame()
    linha.setFrameShape(QFrame.Shape.HLine)
    linha.setStyleSheet("color: rgba(128,128,128,0.25);")
    return linha
