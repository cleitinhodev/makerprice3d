# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Painel mensal: faturamento, lucro, ticket médio, peças mais vendidas, payback e alertas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from makerprice3d.core import gestao
from makerprice3d.core.numeros import formatar_moeda, formatar_numero, formatar_percentual
from makerprice3d.services import negocio
from makerprice3d.ui.contexto import Contexto
from makerprice3d.ui.widgets import Card

MESES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")


class GraficoBarras(QWidget):
    """Barras simples de receita e lucro por mês."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dados: list[tuple[str, Decimal, Decimal]] = []
        self.setMinimumHeight(180)
        self.cor_texto = QColor("#9aa3b2")

    def definir(self, dados: list[tuple[str, Decimal, Decimal]]) -> None:
        """``[(rótulo, receita, lucro), ...]``"""
        self.dados = dados
        self.update()

    def paintEvent(self, _evento) -> None:  # noqa: N802 - API do Qt
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.dados:
            pintor.end()
            return
        maximo = max([max(r, lu, Decimal(0)) for _, r, lu in self.dados] + [Decimal(1)])
        largura = self.width() / len(self.dados)
        base = self.height() - 22
        for indice, (rotulo, receita, lucro) in enumerate(self.dados):
            x = indice * largura
            for deslocamento, valor, cor in ((0.18, receita, "#7c5cff"), (0.52, lucro, "#3ddc84")):
                altura = float(max(valor, Decimal(0)) / maximo) * (base - 10)
                pintor.setBrush(QColor(cor))
                pintor.setPen(Qt.PenStyle.NoPen)
                pintor.drawRoundedRect(QRectF(x + largura * deslocamento, base - altura, largura * 0.3, altura), 4, 4)
            pintor.setPen(self.cor_texto)
            pintor.drawText(QRectF(x, base + 4, largura, 18), Qt.AlignmentFlag.AlignCenter, rotulo)
        pintor.end()


class PaginaPainel(QWidget):
    """Indicadores do mês e saúde do negócio."""

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.contexto = contexto
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.Shape.NoFrame)
        conteudo = QWidget()
        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        topo = QHBoxLayout()
        titulo = QLabel("Painel do mês")
        titulo.setObjectName("tituloCard")
        topo.addWidget(titulo)
        topo.addStretch(1)
        hoje = date.today()
        self.mes = QComboBox()
        self.mes.addItems(MESES)
        self.mes.setCurrentIndex(hoje.month - 1)
        self.ano = QSpinBox()
        self.ano.setRange(2000, 2100)
        self.ano.setValue(hoje.year)
        self.mes.currentIndexChanged.connect(self.atualizar)
        self.ano.valueChanged.connect(self.atualizar)
        topo.addWidget(self.mes)
        topo.addWidget(self.ano)
        layout.addLayout(topo)

        grade = QGridLayout()
        grade.setSpacing(12)
        self.metricas: dict[str, QLabel] = {}
        for indice, (chave, rotulo) in enumerate(
            (
                ("receita", "Faturamento"),
                ("lucro", "Lucro"),
                ("ticket", "Ticket médio"),
                ("pedidos", "Pedidos concluídos"),
                ("pecas", "Peças vendidas"),
                ("resina", "Resina usada"),
            )
        ):
            card = Card(rotulo)
            valor = QLabel("—")
            valor.setObjectName("totalGrande")
            card.corpo.addWidget(valor)
            self.metricas[chave] = valor
            grade.addWidget(card, indice // 3, indice % 3)
        layout.addLayout(grade)

        self.alertas = QLabel()
        self.alertas.setObjectName("alerta")
        self.alertas.setWordWrap(True)
        layout.addWidget(self.alertas)

        linha = QHBoxLayout()
        card_grafico = Card("Últimos 6 meses", None, "Roxo: faturamento · Verde: lucro")
        self.grafico = GraficoBarras()
        card_grafico.corpo.addWidget(self.grafico)
        linha.addWidget(card_grafico, 3)
        card_top = Card("Peças mais vendidas")
        self.top = QLabel("—")
        self.top.setWordWrap(True)
        card_top.corpo.addWidget(self.top)
        linha.addWidget(card_top, 2)
        layout.addLayout(linha)

        card_payback = Card(
            "Retorno do investimento (payback)",
            None,
            "Lucro dos pedidos concluídos ligados a cada impressora × preço pago. Ponto de equilíbrio pelos custos "
            "fixos mensais das Configurações.",
        )
        self.equilibrio = QLabel()
        card_payback.corpo.addWidget(self.equilibrio)
        self.tabela_payback = QTableWidget(0, 5)
        self.tabela_payback.setHorizontalHeaderLabels(
            ["Impressora", "Investimento", "Lucro acumulado", "Pago", "Faltam"]
        )
        self.tabela_payback.horizontalHeader().setStretchLastSection(True)
        self.tabela_payback.verticalHeader().setVisible(False)
        self.tabela_payback.setMinimumHeight(140)
        card_payback.corpo.addWidget(self.tabela_payback)
        layout.addWidget(card_payback)
        layout.addStretch(1)
        rolagem.setWidget(conteudo)
        raiz.addWidget(rolagem)
        contexto.dados_alterados.connect(lambda _: self.atualizar())
        self.atualizar()

    def atualizar(self) -> None:
        """Recalcula os indicadores."""
        banco = self.contexto.banco
        ano, mes = self.ano.value(), self.mes.currentIndex() + 1
        r = negocio.resumo_do_mes(banco, ano, mes)
        self.metricas["receita"].setText(formatar_moeda(r.receita))
        self.metricas["lucro"].setText(formatar_moeda(r.lucro))
        self.metricas["ticket"].setText(formatar_moeda(r.ticket_medio))
        self.metricas["pedidos"].setText(str(r.pedidos))
        self.metricas["pecas"].setText(str(r.pecas))
        self.metricas["resina"].setText(f"{formatar_numero(r.resina_g, 0)} g")
        self.top.setText(
            "<br>".join(f"{i + 1}. {nome} — <b>{qtd}</b>" for i, (nome, qtd) in enumerate(r.top_pecas))
            or "Nenhuma venda concluída no mês."
        )
        dados = []
        for atras in range(5, -1, -1):
            m = mes - atras
            a = ano
            while m <= 0:
                m += 12
                a -= 1
            resumo = negocio.resumo_do_mes(banco, a, m)
            dados.append((MESES[m - 1], resumo.receita, resumo.lucro))
        self.grafico.definir(dados)

        paybacks = negocio.payback_impressoras(banco)
        self.tabela_payback.setRowCount(len(paybacks))
        for linha, (imp, pb) in enumerate(paybacks):
            if pb.quitado:
                faltam = "Quitada ✔"
            elif pb.meses_restantes is None:
                faltam = "Sem dados"
            else:
                faltam = f"~{formatar_numero(pb.meses_restantes, 1)} meses"
            for coluna, texto in enumerate(
                (
                    imp["nome"],
                    formatar_moeda(pb.investimento),
                    formatar_moeda(pb.lucro_acumulado),
                    formatar_percentual(pb.percentual_pago, 0),
                    faltam,
                )
            ):
                self.tabela_payback.setItem(linha, coluna, QTableWidgetItem(texto))
        pe = negocio.ponto_equilibrio_mensal(banco)
        if pe is None:
            self.equilibrio.setText("Ponto de equilíbrio: conclua alguns pedidos para calcular.")
        else:
            self.equilibrio.setText(
                f"Ponto de equilíbrio: <b>{formatar_numero(pe, 0)} peças/mês</b> para cobrir os custos fixos."
            )

        alertas = list(negocio.alertas_de_troca(banco))
        baixos = gestao.estoque_baixo(banco.listar("estoque"))
        if baixos:
            alertas.append("Estoque baixo: " + ", ".join(b["nome"] for b in baixos))
        self.alertas.setVisible(bool(alertas))
        self.alertas.setText("\n".join(f"⚠ {a}" for a in alertas))
