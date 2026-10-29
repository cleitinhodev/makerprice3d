# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Tela principal de precificação: todos os campos da v1.x + os novos cálculos."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from PySide6.QtCore import QLocale, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from makerprice3d.core import calculadora as calc
from makerprice3d.core import precificacao as p
from makerprice3d.core.formulas import CORES_SUGESTAO
from makerprice3d.core.numeros import formatar_moeda, formatar_numero, formatar_percentual, para_decimal
from makerprice3d.core.projeto import Projeto, definir_valor, obter_valor
from makerprice3d.ui.contexto import Contexto
from makerprice3d.ui.dialogos import DialogoCalculadoraEnergia, DialogoDespesa
from makerprice3d.ui.widgets import (
    CampoNumerico,
    Card,
    GradeResponsiva,
    GraficoComposicao,
    Legenda,
    Selo,
    rotulo_campo,
    separador,
)

COR = {c.chave: c.cor for c in calc.CATEGORIAS}

# (caminho, rótulo, dica) — rótulos da v1.x mantidos ao pé da letra.
CAMPOS_MATERIAL = (
    ("material.resina", "Resina 1Kg (R$)", "Preço de 1 kg de resina."),
    ("material.suporte", "Suportes (%)", "Percentual extra de resina gasto com suportes."),
    ("material.peso", "Peso da Peça (g)", "Peso da peça em gramas (veja no fatiador)."),
    ("material.custo_fixo", "Custo Fixo", "Valor fixo somado ao material."),
)
CAMPOS_ENERGIA = (
    ("energia.impressao", "Impressão", "Custo de energia da impressão (R$)."),
    ("energia.lixa_retificadora", "Lixa (Retificadora)", "Custo de energia da retificadora (R$)."),
    ("energia.lavagem_cura", "Lavagem/CuraUV", "Custo de energia da lavagem e cura (R$)."),
    ("energia.pintura", "Pintura(Aerógrafo)", "Custo de energia do aerógrafo/compressor (R$)."),
)
CAMPOS_DESGASTE = (
    ("desgaste.preco_lcd", "Preço LCD (R$)", "Preço da tela LCD."),
    ("desgaste.vida_util", "Vida Útil (h)", "Vida útil da tela LCD em horas."),
    ("desgaste.tempo_total", "Tempo Total (h)", "Tempo de impressão (da mesa inteira se compartilhada)."),
    ("desgaste.preco_fep", "Preço FEP (R$)", "Preço do filme FEP."),
    ("desgaste.durabilidade", "Durabilidade (qnt)", "Quantas impressões o FEP aguenta."),
    ("desgaste.porcentagem_area", "Area (%)", "Percentual da área da mesa usada (vazio = 100%)."),
    ("desgaste.manutencao", "Manutenção (R$)", "Manutenção fixa extra por impressão."),
)
ABAS_ACABAMENTO = (
    (
        "lavagem",
        "Lavagem",
        (
            ("acabamento.lavagem.custo_solvente", "Solvente 1L (R$)", "Preço de 1 litro de solvente/álcool."),
            ("acabamento.lavagem.lavagens_por_peca", "Qnt. Lavagens/1L", "Quantas lavagens rende 1 litro."),
            ("acabamento.lavagem.litros_usados", "Total Usado (L)", "Litros usados (vazio = 1)."),
        ),
    ),
    (
        "lixa",
        "Lixa",
        (
            ("acabamento.lixa.custo_ponta", "Custo de Ponta(R$)", "Preço de uma ponta/lixa."),
            ("acabamento.lixa.vida_util", "Vida Útil (qnt)", "Quantas peças cada ponta aguenta."),
            ("acabamento.lixa.pontas_usadas", "Pontas Usadas (qnt)", "Pontas usadas (vazio = 1)."),
        ),
    ),
    (
        "pintura",
        "Pintura",
        (
            ("acabamento.pintura.custo_tinta", "Custo Unidade(R$)", "Preço de um frasco de tinta."),
            ("acabamento.pintura.ml_por_unidade", "ml / Unidade", "Mililitros por frasco."),
            ("acabamento.pintura.uso_medio", "Uso Médio (ml)", "Mililitros usados na peça (vazio = 1)."),
        ),
    ),
)
CAMPOS_LOGISTICA = (
    ("logistica.embrulho", "Embrulho (R$)", "Embalagem."),
    ("logistica.descontos", "Descontos (R$)", "Desconto concedido (subtrai)."),
    ("logistica.impostos", "Impostos (R$)", "Imposto em valor fixo (além do % em Tributos)."),
    ("logistica.frete", "Frete (R$)", "Frete pago por você."),
)
CAMPOS_MAO_DE_OBRA = (
    ("mao_de_obra.ganho_por_hora", "Ganho por Hora", "Quanto vale sua hora de trabalho."),
    ("mao_de_obra.horas_trabalhadas", "Horas Trabalhadas", "Horas de trabalho manual na peça."),
)
CAMPOS_MESA = (
    ("mesa.peso_total_mesa", "Peso total da mesa (g)", "Soma do peso de todas as peças da mesa."),
    ("mesa.pecas_na_mesa", "Peças na mesa (qnt)", "Usado se o peso total estiver vazio (divide igual)."),
    ("mesa.altura_mm", "Altura da mais alta (mm)", "Em resina o tempo depende da altura, não da quantidade."),
    ("mesa.altura_camada_mm", "Altura da camada (mm)", "Ex.: 0,05"),
    ("mesa.segundos_por_camada", "Segundos por camada", "Exposição + movimento por camada (veja no fatiador)."),
)
CAMPOS_PERDAS = (
    ("perdas.tanque", "Perda no tanque (%)", "Resina que fica no tanque/filtro."),
    ("perdas.lavagem", "Perda na lavagem (%)", "Resina perdida na lavagem."),
    ("perdas.suportes", "Perda extra suportes (%)", "Só se não incluiu em 'Suportes (%)' do Material."),
    ("perdas.taxa_falha", "Taxa de falha (%)", "De cada 100 impressões, quantas falham (máx. 95)."),
)
CAMPOS_FIXOS = (
    ("custos_fixos.mensal", "Custos fixos/mês (R$)", "Aluguel, internet, softwares..."),
    ("custos_fixos.horas_maquina_mes", "Horas máquina/mês", "Horas de impressão por mês."),
    ("custos_fixos.preco_impressora", "Preço impressora (R$)", "Para depreciação por hora."),
    ("custos_fixos.vida_util_impressora", "Vida útil impressora (h)", ""),
    ("custos_fixos.preco_mesa", "Preço plataforma (R$)", "Plataforma/mesa de impressão."),
    ("custos_fixos.vida_util_mesa", "Vida útil plataforma (h)", ""),
)
CAMPOS_EXTRAS = (
    ("extras.licenca_custo", "Licença STL (R$)", "Licença comercial do modelo (Patreon, MMF...)."),
    ("extras.licenca_vendas_previstas", "Vendas previstas", "Quantas peças pretende vender com essa licença."),
    ("extras.papel_por_peca", "Papel/consumíveis por peça", "Papel toalha, palitos etc. (R$ por peça)."),
    ("extras.luvas_custo", "Luvas (R$ caixa)", ""),
    ("extras.luvas_pecas", "Peças por caixa", ""),
    ("extras.mascara_custo", "Máscara/filtro resp. (R$)", ""),
    ("extras.mascara_pecas", "Peças por máscara", ""),
    ("extras.filtro_custo", "Filtro de resina/ar (R$)", ""),
    ("extras.filtro_pecas", "Peças por filtro", ""),
    ("extras.clima_potencia_w", "Climatização (W)", "Ar-condicionado/aquecedor do ambiente."),
    ("extras.clima_horas", "Climatização (h)", "Vazio = tempo de impressão."),
    ("extras.tarifa_kwh", "Tarifa (R$/kWh)", "Tarifa da conta de luz."),
)
CAMPOS_TRIBUTOS = (
    ("tributos.das_mensal", "DAS mensal (R$)", "Valor do DAS do MEI (confira o atual)."),
    ("tributos.vendas_mes", "Vendas por mês", "Peças vendidas por mês para ratear o DAS."),
    ("venda.impostos_percentual", "Imposto sobre venda (%)", "Ex.: alíquota do Simples Nacional (editável)."),
)
CAMPOS_VENDA = (
    ("venda.taxa_percentual", "Taxa do canal (%)", "Comissão do marketplace/maquininha."),
    ("venda.taxa_fixa", "Taxa fixa (R$)", "Tarifa fixa por venda."),
    ("venda.preco_alvo", "Preço de venda alvo (R$)", "Preço reverso: veja o lucro real nesse preço."),
    ("venda.acrescimo_premium", "Acréscimo premium (p.p.)", "Pontos percentuais acima do lucro."),
)
REGIMES = (("nenhum", "Nenhum/Outro"), ("mei", "MEI (DAS fixo rateado)"), ("simples", "Simples Nacional (% da venda)"))


class PaginaCalculadora(QWidget):
    """Calculadora de preço de uma peça em resina."""

    projeto_alterado = Signal()
    pedir_catalogo = Signal()
    pedir_orcamento = Signal()
    pedir_simulacao = Signal()
    pedir_cotacao = Signal()

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.contexto = contexto
        self.projeto: Projeto = {}
        self.resultado: calc.Resultado | None = None
        self.campos: dict[str, CampoNumerico] = {}
        self.cards: dict[str, Card] = {}
        self._carregando = False
        self._montar()

    # ------------------------------------------------------------------ montagem
    def _montar(self) -> None:
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.setChildrenCollapsible(False)
        raiz.addWidget(divisor)

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.Shape.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        conteudo = QWidget()
        coluna = QVBoxLayout(conteudo)
        coluna.setContentsMargins(18, 16, 10, 18)
        coluna.setSpacing(14)
        coluna.addWidget(self._card_projeto())
        self.grade = GradeResponsiva(360)
        for card in (
            self._card_simples("material", "Material", CAMPOS_MATERIAL, 2),
            self._card_energia(),
            self._card_desgaste(),
            self._card_acabamento(),
            self._card_despesas(),
            self._card_simples("logistica", "Logística", CAMPOS_LOGISTICA, 2),
            self._card_simples("mao_de_obra", "Mão de obra", CAMPOS_MAO_DE_OBRA, 2),
            self._card_mesa(),
            self._card_perdas(),
            self._card_simples(
                "custos_fixos",
                "Custos fixos e depreciação",
                CAMPOS_FIXOS,
                2,
                "Rateio por hora de máquina. A depreciação aparece em cor própria.",
                True,
            ),
            self._card_extras(),
            self._card_tributos(),
            self._card_venda(),
        ):
            self.grade.adicionar(card)
        coluna.addWidget(self.grade)
        coluna.addStretch(1)
        rolagem.setWidget(conteudo)
        divisor.addWidget(rolagem)
        divisor.addWidget(self._painel_resumo())
        divisor.setStretchFactor(0, 3)
        divisor.setStretchFactor(1, 1)
        divisor.setSizes([900, 380])

    def _campo(self, caminho: str, dica: str) -> CampoNumerico:
        campo = CampoNumerico(caminho, dica)
        campo.valor_alterado.connect(self._ao_editar)
        self.campos[caminho] = campo
        return campo

    def _preencher(self, card: Card, campos, colunas: int) -> None:
        for caminho, rotulo, dica in campos:
            card.adicionar_campo(rotulo, self._campo(caminho, dica), colunas)

    def _card_simples(self, chave, titulo, campos, colunas=2, subtitulo="", novo=False) -> Card:
        card = Card(titulo, COR.get(chave), subtitulo, novo)
        self._preencher(card, campos, colunas)
        self.cards[chave] = card
        return card

    def _card_projeto(self) -> QFrame:
        card = Card("Projeto", None, "Dados do trabalho e perfis salvos (impressora, resina, canal).")
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Ex.: Busto do Kratos 75mm")
        self.cliente = QLineEdit()
        self.cliente.setPlaceholderText("Cliente (opcional)")
        self.quantidade = QSpinBox()
        self.quantidade.setRange(1, 100000)
        self.quantidade.setToolTip("Quantidade de peças iguais no pedido.")
        self.nome.textEdited.connect(lambda t: self._ao_editar("meta.nome", t))
        self.cliente.textEdited.connect(lambda t: self._ao_editar("meta.cliente", t))
        self.quantidade.valueChanged.connect(lambda v: self._ao_editar("meta.quantidade", str(v)))
        card.adicionar_campo("Nome da peça", self.nome, 4)
        card.adicionar_campo("Cliente", self.cliente, 4)
        card.adicionar_campo("Quantidade", self.quantidade, 4)
        card.adicionar_campo("", QWidget(), 4)
        self.combo_impressora = QComboBox()
        self.combo_resina = QComboBox()
        self.combo_canal = QComboBox()
        for combo, dica in (
            (self.combo_impressora, "Preenche LCD, FEP, depreciação e potência a partir do perfil."),
            (self.combo_resina, "Preenche o preço por kg a partir do preço por litro e densidade."),
            (self.combo_canal, "Preenche as taxas do canal de venda."),
        ):
            combo.setToolTip(dica)
            combo.activated.connect(self._aplicar_perfis)
        card.adicionar_campo("Impressora", self.combo_impressora, 4)
        card.adicionar_campo("Resina", self.combo_resina, 4)
        card.adicionar_campo("Canal de venda", self.combo_canal, 4)
        self.observacoes = QLineEdit()
        self.observacoes.setPlaceholderText("Observações")
        self.observacoes.textEdited.connect(lambda t: self._ao_editar("meta.observacoes", t))
        card.adicionar_campo("Observações", self.observacoes, 4)
        self.atualizar_listas()
        return card

    def _card_energia(self) -> Card:
        card = self._card_simples("energia", "Energia", CAMPOS_ENERGIA, 2, "Valores em R$ por peça.")
        linha = QHBoxLayout()
        botao_kwh = QPushButton("Calcular KWh")
        botao_kwh.clicked.connect(self._abrir_kwh)
        botao_imp = QPushButton("Impressão pela impressora")
        botao_imp.setToolTip("Potência da impressora (perfil) × Tempo Total × tarifa.")
        botao_imp.clicked.connect(self._energia_pela_impressora)
        linha.addWidget(botao_kwh)
        linha.addWidget(botao_imp)
        card.corpo.addLayout(linha)
        return card

    def _card_desgaste(self) -> Card:
        card = Card("Desgaste", COR["desgaste"], "Tela LCD, filme FEP e manutenção.")
        self.cards["desgaste"] = card
        self._preencher(card, CAMPOS_DESGASTE[:3], 3)
        card.nova_linha()
        self._preencher(card, CAMPOS_DESGASTE[3:6], 3)
        card.nova_linha()
        self._preencher(card, CAMPOS_DESGASTE[6:], 3)
        return card

    def _card_acabamento(self) -> Card:
        card = Card("Acabamento", None, "Lavagem, lixa e pintura.")
        self.cards["acabamento"] = card
        abas = QTabWidget()
        self.selos_acabamento: dict[str, Selo] = {}
        for chave, titulo, campos in ABAS_ACABAMENTO:
            pagina = QWidget()
            grade = QGridLayout(pagina)
            for indice, (caminho, rotulo, dica) in enumerate(campos):
                grade.addWidget(rotulo_campo(rotulo), 0, indice)
                grade.addWidget(self._campo(caminho, dica), 1, indice)
            abas.addTab(pagina, titulo)
            selo = Selo(COR[chave])
            self.selos_acabamento[chave] = selo
        card.corpo.addWidget(abas)
        linha = QGridLayout()
        for indice, (chave, titulo, _) in enumerate(ABAS_ACABAMENTO):
            linha.addWidget(rotulo_campo(titulo), 0, indice)
            linha.addWidget(self.selos_acabamento[chave], 1, indice)
        card.corpo.addLayout(linha)
        return card

    def _card_despesas(self) -> Card:
        card = Card("Despesas", COR["despesas"], "Itens extras (valor × quantidade).")
        self.cards["despesas"] = card
        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["Nome", "Tipo", "Qtd", "Valor"])
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setMinimumHeight(150)
        self.tabela.doubleClicked.connect(self._editar_despesa)
        card.corpo.addWidget(self.tabela)
        linha = QHBoxLayout()
        for texto, funcao in (
            ("Adicionar", self._adicionar_despesa),
            ("Editar", self._editar_despesa),
            ("Deletar", self._deletar_despesa),
            ("Limpar Tudo", self._limpar_despesas),
        ):
            botao = QPushButton(texto)
            botao.clicked.connect(funcao)
            linha.addWidget(botao)
        card.corpo.addLayout(linha)
        return card

    def _card_mesa(self) -> Card:
        card = Card(
            "Mesa compartilhada",
            None,
            "Várias peças na mesma impressão: tempo, energia e desgaste são divididos pelo peso.",
            True,
        )
        self.cards["mesa"] = card
        self._preencher(card, CAMPOS_MESA, 2)
        card.nova_linha()
        self.rotulo_fator = QLabel("Esta peça: 100% da mesa")
        self.rotulo_fator.setObjectName("suave")
        botao = QPushButton("Calcular Tempo Total pela altura")
        botao.setToolTip("camadas = altura ÷ camada; tempo = camadas × segundos ÷ 3600")
        botao.clicked.connect(self._tempo_pela_altura)
        card.corpo.addWidget(self.rotulo_fator)
        card.corpo.addWidget(botao)
        return card

    def _card_perdas(self) -> Card:
        card = Card(
            "Perdas e falhas", COR["perdas_resina"], "Resina desperdiçada e custo das impressões que falham.", True
        )
        self.cards["perdas_resina"] = card
        self._preencher(card, CAMPOS_PERDAS, 2)
        self.selo_falhas = Selo(COR["falhas"])
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Custo das falhas"))
        linha.addWidget(self.selo_falhas)
        botao = QPushButton("Usar taxa medida")
        botao.setToolTip("Usa a taxa de falha registrada em Equipamentos para a impressora/resina escolhidas.")
        botao.clicked.connect(self._usar_taxa_medida)
        linha.addWidget(botao)
        card.corpo.addLayout(linha)
        return card

    def _card_extras(self) -> Card:
        card = Card("Custos extras", None, "Licença do STL, EPI/consumíveis e climatização.", True)
        self.cards["extras"] = card
        self._preencher(card, CAMPOS_EXTRAS, 3)
        linha = QGridLayout()
        self.selos_extras: dict[str, Selo] = {}
        for indice, (chave, rotulo) in enumerate((("licenca", "Licença"), ("epi", "EPI"), ("climatizacao", "Clima"))):
            linha.addWidget(rotulo_campo(rotulo), 0, indice)
            self.selos_extras[chave] = Selo(COR[chave])
            linha.addWidget(self.selos_extras[chave], 1, indice)
        card.corpo.addLayout(linha)
        return card

    def _card_tributos(self) -> Card:
        card = Card(
            "Tributos", COR["das_mei"], "MEI (DAS rateado) ou Simples (% sobre a venda). Valores editáveis.", True
        )
        self.cards["das_mei"] = card
        self.combo_regime = QComboBox()
        for valor, texto in REGIMES:
            self.combo_regime.addItem(texto, valor)
        self.combo_regime.activated.connect(
            lambda _: self._ao_editar("tributos.regime", self.combo_regime.currentData())
        )
        card.adicionar_campo("Regime", self.combo_regime, 2)
        card.nova_linha()
        self._preencher(card, CAMPOS_TRIBUTOS, 2)
        return card

    def _card_venda(self) -> Card:
        card = Card("Venda e preço reverso", COR.get("taxas", "#3a86ff"), "Taxas do canal e análise de um preço.", True)
        self.cards["venda"] = card
        self.campo_canal_nome = QLineEdit()
        self.campo_canal_nome.textEdited.connect(lambda t: self._ao_editar("venda.canal_nome", t))
        card.adicionar_campo("Canal", self.campo_canal_nome, 2)
        card.nova_linha()
        self._preencher(card, CAMPOS_VENDA, 2)
        self.rotulo_reverso = QLabel("Informe um preço alvo para ver o lucro real.")
        self.rotulo_reverso.setWordWrap(True)
        self.rotulo_reverso.setObjectName("suave")
        card.corpo.addWidget(self.rotulo_reverso)
        return card

    def _painel_resumo(self) -> QWidget:
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.Shape.NoFrame)
        rolagem.setMinimumWidth(360)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        painel = QFrame()
        painel.setObjectName("cardResumo")
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        titulo = QLabel("Total")
        titulo.setObjectName("tituloCard")
        layout.addWidget(titulo)

        linha_lucro = QHBoxLayout()
        linha_lucro.addWidget(QLabel("Lucro Estimado"))
        self.spin_lucro = QDoubleSpinBox()
        self.spin_lucro.setRange(0, 1000)
        self.spin_lucro.setDecimals(1)
        self.spin_lucro.setSuffix(" %")
        self.spin_lucro.setLocale(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
        linha_lucro.addStretch(1)
        linha_lucro.addWidget(self.spin_lucro)
        layout.addLayout(linha_lucro)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        layout.addWidget(self.slider)
        self.combo_modo = QComboBox()
        self.combo_modo.addItem("Markup (sobre o custo) — igual à v1.x", p.ModoLucro.MARKUP.value)
        self.combo_modo.addItem("Margem (sobre o preço de venda)", p.ModoLucro.MARGEM.value)
        self.combo_modo.setToolTip(
            "Markup: preço = custo × (1 + %).\nMargem: o % é a fatia de lucro dentro do preço: custo ÷ (1 − %)."
        )
        layout.addWidget(self.combo_modo)
        self.slider.valueChanged.connect(self._slider_mudou)
        self.spin_lucro.valueChanged.connect(self._spin_mudou)
        self.combo_modo.activated.connect(lambda _: self._ao_editar("lucro.modo", self.combo_modo.currentData()))

        self.grafico = GraficoComposicao()
        layout.addWidget(self.grafico)
        self.legenda = Legenda()
        layout.addWidget(self.legenda)
        layout.addWidget(separador())

        self.metricas: dict[str, QLabel] = {}
        grade = QHBoxLayout()
        for chave, rotulo in (("gasto", "Total Gasto"), ("lucro", "Lucro"), ("sugestao", "Sugestão")):
            caixa = QVBoxLayout()
            r = QLabel(rotulo)
            r.setObjectName("suave")
            v = QLabel("R$ 0,00")
            v.setObjectName("metricaValor")
            caixa.addWidget(r)
            caixa.addWidget(v)
            grade.addLayout(caixa)
            self.metricas[chave] = v
        layout.addLayout(grade)
        self.total_grande = QLabel("R$ 0,00")
        self.total_grande.setObjectName("totalGrande")
        self.total_grande.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_grande.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.total_grande)
        self.subtotal_grande = QLabel("")
        self.subtotal_grande.setObjectName("suave")
        self.subtotal_grande.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtotal_grande)
        layout.addWidget(separador())

        self.precos: dict[str, QLabel] = {}
        for chave, rotulo, dica in (
            ("minimo", "Preço mínimo", "Cobre custos + taxas, lucro zero."),
            ("sugerido", "Preço sugerido", "Com o lucro escolhido + taxas."),
            ("premium", "Preço premium", "Lucro + acréscimo premium + taxas."),
            ("taxas", "Taxas/impostos no sugerido", ""),
            ("markup", "Markup equivalente", ""),
            ("margem", "Margem equivalente", ""),
            ("pedido", "Total do pedido", "Preço sugerido × quantidade."),
        ):
            linha = QHBoxLayout()
            r = QLabel(rotulo)
            r.setToolTip(dica)
            v = QLabel("—")
            v.setAlignment(Qt.AlignmentFlag.AlignRight)
            linha.addWidget(r)
            linha.addWidget(v, 1)
            layout.addLayout(linha)
            self.precos[chave] = v
        self.avisos = QLabel("")
        self.avisos.setObjectName("alerta")
        self.avisos.setWordWrap(True)
        self.avisos.hide()
        layout.addWidget(self.avisos)
        layout.addWidget(separador())
        for texto, sinal, primario in (
            ("Salvar no catálogo", self.pedir_catalogo, False),
            ("Criar orçamento", self.pedir_orcamento, True),
            ("Simular cenário", self.pedir_simulacao, False),
            ("Cotação em outras moedas", self.pedir_cotacao, False),
        ):
            botao = QPushButton(texto)
            if primario:
                botao.setObjectName("primario")
            botao.clicked.connect(sinal.emit)
            layout.addWidget(botao)
        layout.addStretch(1)
        rolagem.setWidget(painel)
        return rolagem

    # --------------------------------------------------------------- perfis
    def atualizar_listas(self) -> None:
        """Recarrega as listas de impressoras, resinas e canais."""
        banco = self.contexto.banco
        for combo, tabela, vazio in (
            (self.combo_impressora, "impressoras", "— sem perfil —"),
            (self.combo_resina, "resinas", "— sem perfil —"),
            (self.combo_canal, "canais", "— sem canal —"),
        ):
            atual = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(vazio, None)
            for registro in banco.listar(tabela):
                combo.addItem(registro["nome"], registro["id"])
            indice = combo.findData(atual)
            combo.setCurrentIndex(max(0, indice))
            combo.blockSignals(False)

    def _selecionar_perfis(self) -> None:
        for combo, caminho in (
            (self.combo_impressora, "perfil.impressora_id"),
            (self.combo_resina, "perfil.resina_id"),
            (self.combo_canal, "perfil.canal_id"),
        ):
            valor = obter_valor(self.projeto, caminho, None)
            try:
                valor = int(valor) if valor not in (None, "") else None
            except (TypeError, ValueError):
                valor = None
            combo.setCurrentIndex(max(0, combo.findData(valor)))

    def _aplicar_perfis(self) -> None:
        """Copia os dados dos perfis escolhidos para os campos (só valores preenchidos)."""
        banco = self.contexto.banco
        sender = self.sender()
        mudancas: dict[str, Any] = {}
        if sender is self.combo_impressora:
            ident = self.combo_impressora.currentData()
            mudancas["perfil.impressora_id"] = ident
            imp = banco.obter("impressoras", ident) if ident else None
            if imp:
                for origem, destino in (
                    ("preco_lcd", "desgaste.preco_lcd"),
                    ("vida_lcd_h", "desgaste.vida_util"),
                    ("preco_fep", "desgaste.preco_fep"),
                    ("durabilidade_fep", "desgaste.durabilidade"),
                    ("preco", "custos_fixos.preco_impressora"),
                    ("vida_util_h", "custos_fixos.vida_util_impressora"),
                    ("preco_mesa", "custos_fixos.preco_mesa"),
                    ("vida_mesa_h", "custos_fixos.vida_util_mesa"),
                ):
                    if str(imp.get(origem) or "").strip():
                        mudancas[destino] = str(imp[origem])
        elif sender is self.combo_resina:
            ident = self.combo_resina.currentData()
            mudancas["perfil.resina_id"] = ident
            resina = banco.obter("resinas", ident) if ident else None
            if resina and str(resina.get("preco_litro") or "").strip():
                densidade = para_decimal(resina.get("densidade"), Decimal("1.1")) or Decimal("1.1")
                kg = p.preco_por_kg(para_decimal(resina["preco_litro"]), densidade)
                mudancas["material.resina"] = f"{kg:.2f}"
        elif sender is self.combo_canal:
            ident = self.combo_canal.currentData()
            mudancas["perfil.canal_id"] = ident
            canal = banco.obter("canais", ident) if ident else None
            if canal:
                mudancas["venda.canal_nome"] = canal["nome"]
                mudancas["venda.taxa_percentual"] = str(canal.get("taxa_percentual") or "")
                mudancas["venda.taxa_fixa"] = str(canal.get("taxa_fixa") or "")
        for caminho, valor in mudancas.items():
            definir_valor(self.projeto, caminho, valor)
        self._sincronizar_campos()
        self._marcar_alterado()

    def _energia_pela_impressora(self) -> None:
        ident = self.combo_impressora.currentData()
        imp = self.contexto.banco.obter("impressoras", ident) if ident else None
        potencia = para_decimal(imp.get("potencia_w")) if imp else Decimal(0)
        tarifa = para_decimal(obter_valor(self.projeto, "extras.tarifa_kwh", "")) or self.contexto.config_decimal(
            "tarifa_kwh"
        )
        tempo = para_decimal(obter_valor(self.projeto, "desgaste.tempo_total", ""))
        if not potencia or not tarifa or not tempo:
            QMessageBox.information(
                self,
                "Energia pela impressora",
                "Escolha uma impressora com potência cadastrada, informe a tarifa (Custos extras ou Configurações) "
                "e o Tempo Total (h) no Desgaste.",
            )
            return
        valor = p.custo_energia_por_potencia(potencia, tempo, tarifa)
        self.campos["energia.impressao"].setText(f"{valor:.2f}")

    def _tempo_pela_altura(self) -> None:
        altura = para_decimal(obter_valor(self.projeto, "mesa.altura_mm", ""))
        camada = para_decimal(obter_valor(self.projeto, "mesa.altura_camada_mm", ""))
        segundos = para_decimal(obter_valor(self.projeto, "mesa.segundos_por_camada", ""))
        if not (altura and camada and segundos):
            QMessageBox.information(
                self, "Tempo pela altura", "Preencha altura, altura da camada e segundos por camada."
            )
            return
        horas = p.tempo_por_altura(altura, camada, segundos)
        self.campos["desgaste.tempo_total"].setText(f"{horas:.2f}")

    def _usar_taxa_medida(self) -> None:
        from makerprice3d.core import gestao

        medida = gestao.taxa_falha_medida(
            self.contexto.banco.listar("impressoes"),
            self.combo_impressora.currentData(),
            self.combo_resina.currentData(),
        )
        if not medida.total:
            QMessageBox.information(
                self, "Taxa medida", "Ainda não há impressões registradas em Equipamentos para essa combinação."
            )
            return
        self.campos["perdas.taxa_falha"].setText(f"{medida.percentual:.1f}")

    def _abrir_kwh(self) -> None:
        tarifa = obter_valor(self.projeto, "extras.tarifa_kwh", "") or self.contexto.banco.config("tarifa_kwh")
        DialogoCalculadoraEnergia(self, tarifa).exec()

    # --------------------------------------------------------------- despesas
    def _linha_selecionada(self) -> int:
        linhas = self.tabela.selectionModel().selectedRows()
        return linhas[0].row() if linhas else -1

    def _despesas(self) -> list[dict[str, str]]:
        return self.projeto.setdefault("despesas", {}).setdefault("tabela", [])

    def _adicionar_despesa(self) -> None:
        dialogo = DialogoDespesa(self)
        if dialogo.exec():
            self._despesas().append(dialogo.item())
            self._atualizar_tabela()
            self._marcar_alterado()

    def _editar_despesa(self) -> None:
        linha = self._linha_selecionada()
        if linha < 0:
            return
        dialogo = DialogoDespesa(self, self._despesas()[linha])
        if dialogo.exec():
            self._despesas()[linha] = dialogo.item()
            self._atualizar_tabela()
            self._marcar_alterado()

    def _deletar_despesa(self) -> None:
        linha = self._linha_selecionada()
        if linha >= 0:
            del self._despesas()[linha]
            self._atualizar_tabela()
            self._marcar_alterado()

    def _limpar_despesas(self) -> None:
        if self._despesas():
            self._despesas().clear()
            self._atualizar_tabela()
            self._marcar_alterado()

    def _atualizar_tabela(self) -> None:
        itens = self._despesas()
        self.tabela.setRowCount(len(itens))
        for linha, item in enumerate(itens):
            valores = (
                item.get("nome", ""),
                item.get("tipo", ""),
                str(item.get("quantidade", "")),
                formatar_moeda(para_decimal(item.get("valor"))),
            )
            for coluna, texto in enumerate(valores):
                celula = QTableWidgetItem(texto)
                if coluna >= 2:
                    celula.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(linha, coluna, celula)

    # --------------------------------------------------------------- lucro
    def _slider_mudou(self, valor: int) -> None:
        if self._carregando:
            return
        self.spin_lucro.blockSignals(True)
        self.spin_lucro.setValue(valor)
        self.spin_lucro.blockSignals(False)
        self._ao_editar("lucro.estado", str(valor))

    def _spin_mudou(self, valor: float) -> None:
        if self._carregando:
            return
        self.slider.blockSignals(True)
        self.slider.setValue(int(min(100, valor)))
        self.slider.blockSignals(False)
        texto = formatar_numero(Decimal(str(valor)), 1).replace(".", "").replace(",", ".")
        self._ao_editar("lucro.estado", texto.rstrip("0").rstrip(".") if "." in texto else texto)

    # --------------------------------------------------------------- dados
    def _ao_editar(self, caminho: str, texto: Any) -> None:
        if self._carregando:
            return
        definir_valor(self.projeto, caminho, texto)
        self._marcar_alterado()

    def _marcar_alterado(self) -> None:
        self.recalcular()
        self.projeto_alterado.emit()

    def carregar(self, projeto: Projeto) -> None:
        """Mostra um projeto na tela."""
        self.projeto = projeto
        self._sincronizar_campos()
        self.recalcular()

    def _sincronizar_campos(self) -> None:
        self._carregando = True
        try:
            for caminho, campo in self.campos.items():
                campo.definir_texto(str(obter_valor(self.projeto, caminho, "") or ""))
            self.nome.setText(str(obter_valor(self.projeto, "meta.nome", "") or ""))
            self.cliente.setText(str(obter_valor(self.projeto, "meta.cliente", "") or ""))
            self.observacoes.setText(str(obter_valor(self.projeto, "meta.observacoes", "") or ""))
            self.campo_canal_nome.setText(str(obter_valor(self.projeto, "venda.canal_nome", "") or ""))
            quantidade = para_decimal(obter_valor(self.projeto, "meta.quantidade", "1"), Decimal(1))
            self.quantidade.setValue(max(1, int(quantidade)))
            lucro = para_decimal(obter_valor(self.projeto, "lucro.estado", "0"))
            self.spin_lucro.setValue(float(lucro))
            self.slider.setValue(int(min(Decimal(100), lucro)))
            self.combo_modo.setCurrentIndex(max(0, self.combo_modo.findData(obter_valor(self.projeto, "lucro.modo"))))
            regime = obter_valor(self.projeto, "tributos.regime", "nenhum")
            self.combo_regime.setCurrentIndex(max(0, self.combo_regime.findData(regime)))
            self._selecionar_perfis()
            self._atualizar_tabela()
        finally:
            self._carregando = False

    def recalcular(self) -> None:
        """Recalcula tudo e atualiza subtotais, gráfico e preços."""
        r = calc.calcular(self.projeto)
        self.resultado = r
        s = r.subtotais
        for chave, card in self.cards.items():
            if card.selo is not None and chave in s:
                card.selo.definir_valor(s[chave])
        self.cards["custos_fixos"].selo.definir_valor(s["custos_fixos"] + s["depreciacao"])
        self.cards["venda"].selo.definir_valor(r.taxas_valor)
        for chave, selo in self.selos_acabamento.items():
            selo.definir_valor(s[chave])
        for chave, selo in self.selos_extras.items():
            selo.definir_valor(s[chave])
        self.selo_falhas.definir_valor(s["falhas"])
        fator = calc.fator_mesa(self.projeto)
        self.rotulo_fator.setText(f"Esta peça: {formatar_percentual(fator * 100, 1)} da mesa")

        fatias = [(c.rotulo, c.cor, v) for c, v in r.valores_grafico()]
        self.grafico.definir_fatias(fatias)
        self.legenda.definir(fatias)
        self.metricas["gasto"].setText(formatar_moeda(r.total_gasto))
        self.metricas["lucro"].setText(formatar_moeda(r.total_ganho))
        texto, cor = r.sugestao
        self.metricas["sugestao"].setText(texto)
        self.metricas["sugestao"].setStyleSheet(f"color: {CORES_SUGESTAO.get(cor, cor)};")
        self.total_grande.setText(formatar_moeda(r.preco_sugerido))
        if r.taxas_valor:
            self.subtotal_grande.setText(f"Sem taxas: {formatar_moeda(r.total_absoluto)}")
        else:
            self.subtotal_grande.setText("")
        self.precos["minimo"].setText(formatar_moeda(r.preco_minimo))
        self.precos["sugerido"].setText(formatar_moeda(r.preco_sugerido))
        self.precos["premium"].setText(formatar_moeda(r.preco_premium))
        self.precos["taxas"].setText(
            f"{formatar_moeda(r.taxas_valor)} ({formatar_percentual(r.taxas.percentual_total)})"
        )
        self.precos["markup"].setText(formatar_percentual(r.markup_percentual, 1))
        self.precos["margem"].setText(formatar_percentual(r.margem_percentual, 1))
        self.precos["pedido"].setText(f"{r.quantidade} × = {formatar_moeda(r.total_pedido)}")
        if r.analise_reversa:
            a = r.analise_reversa
            cor_lucro = "#3ddc84" if a.lucro >= 0 else "#ff5c6c"
            self.rotulo_reverso.setText(
                f"Vendendo a {formatar_moeda(a.preco_venda)}: taxas {formatar_moeda(a.taxas)}, "
                f"você recebe {formatar_moeda(a.receita_liquida)} e lucra "
                f"<b style='color:{cor_lucro}'>{formatar_moeda(a.lucro)}</b> "
                f"(margem {formatar_percentual(a.margem_percentual, 1)}, "
                f"markup {formatar_percentual(a.markup_percentual, 1)})."
            )
        else:
            self.rotulo_reverso.setText("Informe um preço alvo para ver o lucro real.")
        self.avisos.setVisible(bool(r.avisos))
        self.avisos.setText("\n".join(f"⚠ {a}" for a in r.avisos))

    def campos_invalidos(self) -> list[str]:
        """Caminhos de campos com valor inválido."""
        return [c for c, w in self.campos.items() if not w.valido]
