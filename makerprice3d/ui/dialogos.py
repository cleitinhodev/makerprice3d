# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Janelas auxiliares: despesa, calculadora de kWh, cotação, simulação, configurações e sobre."""

from __future__ import annotations

import threading
import webbrowser
from decimal import Decimal

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from makerprice3d import __version__
from makerprice3d.core import gestao
from makerprice3d.core.energia import calcular_consumo
from makerprice3d.core.numeros import formatar_moeda, formatar_numero, para_decimal
from makerprice3d.core.projeto import Projeto, item_despesa, valor_unitario_despesa
from makerprice3d.services import caminhos
from makerprice3d.services.cotacao import MOEDAS, Cotacoes, buscar_cotacoes
from makerprice3d.ui.widgets import CampoNumerico


def _titulo(texto: str) -> QLabel:
    rotulo = QLabel(texto)
    rotulo.setObjectName("tituloCard")
    return rotulo


class DialogoDespesa(QDialog):
    """Adicionar/editar item da tabela de despesas (Nome, Tipo, Quantidade, Valor unitário)."""

    def __init__(self, parent: QWidget | None = None, item: dict[str, str] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar")
        self.setMinimumWidth(420)
        formulario = QFormLayout(self)
        self.nome = QLineEdit(item.get("nome", "") if item else "")
        self.tipo = QLineEdit(item.get("tipo", "") if item else "")
        self.tipo.setPlaceholderText("Ex.: EPI, ferramenta, embalagem")
        self.quantidade = QSpinBox()
        self.quantidade.setRange(1, 100000)
        self.quantidade.setValue(int(para_decimal(item.get("quantidade"), Decimal(1))) if item else 1)
        self.valor = CampoNumerico("valor", "Valor de UMA unidade; o total é valor × quantidade.")
        if item:
            self.valor.definir_texto(formatar_numero(valor_unitario_despesa(item)))
        formulario.addRow("Nome:", self.nome)
        formulario.addRow("Tipo:", self.tipo)
        formulario.addRow("Quantidade:", self.quantidade)
        formulario.addRow("Valor (R$):", self.valor)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Confirmar")
        botoes.accepted.connect(self._confirmar)
        botoes.rejected.connect(self.reject)
        formulario.addRow(botoes)

    def _confirmar(self) -> None:
        if self.valor.valido:
            self.accept()

    def item(self) -> dict[str, str]:
        """Linha pronta para a tabela (valor total = unitário × quantidade, como na v1.x)."""
        return item_despesa(self.nome.text(), self.tipo.text(), self.quantidade.value(), self.valor.text())


class DialogoCalculadoraEnergia(QDialog):
    """Calculadora de Consumo (kWh) — mesma fórmula da v1.x."""

    def __init__(self, parent: QWidget | None = None, tarifa: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Calculadora de Consumo")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        layout.addWidget(_titulo("Calculadora de Consumo"))
        formulario = QFormLayout()
        self.potencia = CampoNumerico("potencia", "Potência indicada no aparelho.", "Ex: 60")
        self.minutos = CampoNumerico("minutos", "Minutos ligado por dia.", "Ex: 120")
        self.dias = CampoNumerico("dias", "Dias de uso por mês.", "Ex: 30")
        self.valor = CampoNumerico("valor", "Tarifa da sua conta de luz.", "Ex: 0,80")
        self.valor.definir_texto(tarifa)
        formulario.addRow("Potência (W)", self.potencia)
        formulario.addRow("Minutos/dia", self.minutos)
        formulario.addRow("Dias/mês", self.dias)
        formulario.addRow("R$/kWh", self.valor)
        layout.addLayout(formulario)
        botao = QPushButton("Calcular")
        botao.setObjectName("primario")
        botao.clicked.connect(self.calcular)
        layout.addWidget(botao)
        self.resultado = QLabel("Consumo: 0,0 kWh\nCusto Mensal: R$ 0,00\nCusto Diário: R$ 0,00")
        self.resultado.setObjectName("metricaValor")
        layout.addWidget(self.resultado)
        self.custo_dia = Decimal(0)

    def calcular(self) -> None:
        """Calcula e mostra o consumo."""
        campos = (self.potencia, self.minutos, self.dias, self.valor)
        if any(not c.text().strip() or not c.valido for c in campos):
            self.resultado.setText("Preencha todos\nos campos corretamente.")
            return
        try:
            r = calcular_consumo(*(para_decimal(c.text()) for c in campos))
        except ValueError:
            self.resultado.setText("Preencha todos\nos campos corretamente.")
            return
        self.custo_dia = r.custo_dia
        self.resultado.setText(
            f"Consumo: {formatar_numero(r.consumo_mes_kwh, 1)} kWh\n"
            f"Custo Mensal: {formatar_moeda(r.custo_mes)}\nCusto Diário: {formatar_moeda(r.custo_dia)}"
        )


class _Sinal(QObject):
    pronto = Signal(object)


class DialogoCotacao(QDialog):
    """Cotações em tempo real do valor total (com cache offline)."""

    def __init__(self, parent: QWidget | None = None, valor_base: Decimal = Decimal(0), cache=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Conversor de Moedas")
        self.setMinimumWidth(400)
        self.valor_base = valor_base
        layout = QVBoxLayout(self)
        layout.addWidget(_titulo("Cotações em Tempo Real"))
        grade = QGridLayout()
        self.rotulos: dict[str, QLabel] = {}
        for indice, moeda in enumerate(MOEDAS):
            rotulo = QLabel(f"{moeda}:\n-,-")
            rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rotulo.setObjectName("card")
            rotulo.setMinimumHeight(56)
            grade.addWidget(rotulo, indice // 2, indice % 2)
            self.rotulos[moeda] = rotulo
        layout.addLayout(grade)
        self.base = QLabel(f"Valor Base:\n{formatar_moeda(valor_base)}")
        self.base.setObjectName("metricaValor")
        self.base.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.base)
        self.status = QLabel("Buscando cotações…")
        self.status.setObjectName("suave")
        layout.addWidget(self.status)
        self._sinal = _Sinal()
        self._sinal.pronto.connect(self._mostrar)
        threading.Thread(target=lambda: self._sinal.pronto.emit(buscar_cotacoes(cache)), daemon=True).start()

    def _mostrar(self, cotacoes: Cotacoes) -> None:
        for moeda, rotulo in self.rotulos.items():
            valor = cotacoes.converter(self.valor_base, moeda)
            if valor is None:
                rotulo.setText(f"{moeda}:\n-,-")
            else:
                casas = 0 if moeda == "JPY" else (8 if moeda == "BTC" else 2)
                rotulo.setText(f"{moeda}:\n{formatar_numero(valor, casas)}")
        textos = {
            "online": "Cotações online",
            "cache": f"Sem internet — usando última cotação salva ({cotacoes.data})",
            "indisponível": "Cotações indisponíveis no momento.",
        }
        self.status.setText(textos.get(cotacoes.origem, ""))


class DialogoSimulacao(QDialog):
    """Simulação de cenários: e se a resina subir 20%? E se a tarifa mudar?"""

    def __init__(self, projeto: Projeto, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Simulação de cenários")
        self.setMinimumSize(560, 460)
        self.projeto = projeto
        layout = QVBoxLayout(self)
        layout.addWidget(_titulo("Simulação de cenários"))
        explicacao = QLabel("Ajuste os percentuais e veja o impacto no preço sem mexer no projeto.")
        explicacao.setObjectName("suave")
        layout.addWidget(explicacao)
        formulario = QFormLayout()
        self.ajustes: dict[str, QDoubleSpinBox] = {}
        for chave, (rotulo, _) in gestao.AJUSTES_CENARIO.items():
            caixa = QDoubleSpinBox()
            caixa.setRange(-90, 500)
            caixa.setSuffix(" %")
            caixa.setDecimals(1)
            caixa.valueChanged.connect(self.atualizar)
            formulario.addRow(rotulo, caixa)
            self.ajustes[chave] = caixa
        layout.addLayout(formulario)
        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["", "Atual", "Cenário"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.verticalHeader().setVisible(False)
        layout.addWidget(self.tabela, 1)
        self.atualizar()

    def atualizar(self) -> None:
        """Recalcula o cenário."""
        ajustes = {k: Decimal(str(c.value())) for k, c in self.ajustes.items()}
        atual, cenario = gestao.simular(self.projeto, ajustes)
        linhas = [
            ("Total gasto", atual.total_gasto, cenario.total_gasto),
            ("Preço mínimo", atual.preco_minimo, cenario.preco_minimo),
            ("Preço sugerido", atual.preco_sugerido, cenario.preco_sugerido),
            ("Preço premium", atual.preco_premium, cenario.preco_premium),
        ]
        self.tabela.setRowCount(len(linhas) + 1)
        for indice, (rotulo, a, c) in enumerate(linhas):
            self.tabela.setItem(indice, 0, QTableWidgetItem(rotulo))
            self.tabela.setItem(indice, 1, QTableWidgetItem(formatar_moeda(a)))
            self.tabela.setItem(indice, 2, QTableWidgetItem(formatar_moeda(c)))
        diferenca = cenario.preco_sugerido - atual.preco_sugerido
        self.tabela.setItem(len(linhas), 0, QTableWidgetItem("Diferença no preço sugerido"))
        self.tabela.setItem(len(linhas), 2, QTableWidgetItem(formatar_moeda(diferenca)))
        self.tabela.resizeColumnsToContents()


class DialogoConfiguracoes(QDialog):
    """Configurações globais usadas como padrão nos projetos novos."""

    CAMPOS = (
        ("loja_nome", "Nome da loja/ateliê", "texto", "Aparece no orçamento em PDF."),
        ("loja_telefone", "Contato da loja", "texto", "Telefone/WhatsApp ou Instagram mostrado no orçamento."),
        ("tarifa_kwh", "Tarifa de energia (R$/kWh)", "numero", "Veja na sua conta de luz (com impostos)."),
        ("valor_hora", "Valor da sua hora (R$)", "numero", "Padrão do campo Ganho por Hora."),
        ("margem_padrao", "Lucro padrão (%)", "numero", "Posição inicial do lucro em projetos novos."),
        ("acrescimo_premium", "Acréscimo do preço premium (p.p.)", "numero", "Pontos percentuais acima do lucro."),
        ("impostos_percentual", "Impostos sobre a venda (%)", "numero", "Ex.: alíquota do Simples Nacional. Editável."),
        ("das_mensal", "DAS mensal do MEI (R$)", "numero", "Confira o valor atual do seu DAS."),
        ("vendas_mes", "Peças vendidas por mês", "numero", "Usado para ratear o DAS do MEI."),
        ("custo_fixo_mensal", "Custos fixos mensais (R$)", "numero", "Aluguel, internet, softwares..."),
        ("horas_maquina_mes", "Horas de máquina por mês", "numero", "Para ratear os custos fixos por hora."),
        ("validade_orcamento_dias", "Validade padrão do orçamento (dias)", "numero", ""),
        ("autosave_segundos", "Salvamento automático (segundos)", "numero", "0 desliga."),
        ("backups_manter", "Backups automáticos a manter", "numero", "Um backup do banco por dia."),
    )

    def __init__(self, banco, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.banco = banco
        self.setWindowTitle("Configurações")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.addWidget(_titulo("Configurações gerais"))
        formulario = QFormLayout()
        self.widgets: dict[str, QLineEdit] = {}
        for chave, rotulo, tipo, dica in self.CAMPOS:
            campo = CampoNumerico(chave, dica, "") if tipo == "numero" else QLineEdit()
            if isinstance(campo, CampoNumerico):
                campo.definir_texto(banco.config(chave))
            else:
                campo.setText(banco.config(chave))
                campo.setToolTip(dica)
            formulario.addRow(rotulo, campo)
            self.widgets[chave] = campo
        self.regime = QComboBox()
        for valor, texto in (
            ("nenhum", "Nenhum/Outro"),
            ("mei", "MEI (DAS fixo)"),
            ("simples", "Simples Nacional (%)"),
        ):
            self.regime.addItem(texto, valor)
        self.regime.setCurrentIndex(max(0, self.regime.findData(banco.config("regime_tributario"))))
        formulario.addRow("Regime tributário", self.regime)
        layout.addLayout(formulario)
        aviso = QLabel("Nenhuma alíquota oficial é fixada no programa: confira os valores com seu contador.")
        aviso.setObjectName("suave")
        aviso.setWordWrap(True)
        layout.addWidget(aviso)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _salvar(self) -> None:
        if any(isinstance(w, CampoNumerico) and not w.valido for w in self.widgets.values()):
            return
        for chave, widget in self.widgets.items():
            self.banco.definir_config(chave, widget.text().strip())
        self.banco.definir_config("regime_tributario", self.regime.currentData())
        self.accept()


class DialogoSobre(QDialog):
    """Sobre o Maker Price 3D (créditos e licenças)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sobre")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo = caminhos.pasta_assets() / "logo.png"
        if logo.exists():
            imagem = QLabel()
            imagem.setPixmap(
                QPixmap(str(logo)).scaled(
                    180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
            imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(imagem)
        for texto, nome in (
            ("Maker Price 3D", "totalGrande"),
            (f"v{__version__}", "suave"),
            ("Desenvolvido por:\nCleitinhoDEV", ""),
        ):
            rotulo = QLabel(texto)
            rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if nome:
                rotulo.setObjectName(nome)
            layout.addWidget(rotulo)
        for rotulo, link in (
            ("Site Oficial", "https://www.bugzinho.com/"),
            ("Doações", "https://www.bugzinho.com/donate"),
        ):
            botao = QPushButton(f"{rotulo}: {link}")
            botao.clicked.connect(lambda _=False, url=link: webbrowser.open(url))
            layout.addWidget(botao)
        bugs = QLabel("Reportar Bugs: cleitinhodev@outlook.com")
        bugs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(bugs)
        licenca = QLabel(
            "Software livre sob a licença GNU GPL v3 ou posterior.\n"
            "Interface feita com PySide6 (Qt for Python), licença LGPLv3.\n"
            "Usa também requests (Apache 2.0) e SQLite (domínio público)."
        )
        licenca.setObjectName("suave")
        licenca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(licenca)
        obrigado = QLabel("Obrigado pelo apoio! :)")
        obrigado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(obrigado)
        linha = QHBoxLayout()
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        linha.addStretch(1)
        linha.addWidget(fechar)
        layout.addLayout(linha)
