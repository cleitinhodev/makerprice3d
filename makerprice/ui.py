"""Qt Widgets interface; calculations are isolated from presentation."""
from dataclasses import asdict
from datetime import datetime
from html import escape
from pathlib import Path
import csv
import json

from PySide6.QtCore import Qt, QLocale, QTimer, QStandardPaths
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QKeySequence, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout, QStackedWidget,
    QScrollArea, QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QMessageBox, QFileDialog, QInputDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from .domain import Quote, calculate, money, NUMERIC
from .storage import Library, read_document, write_document

COLORS = ['#54dfbd', '#66a9ff', '#bd9cff', '#ffc578', '#f68fa9', '#72cdd5', '#a7b7cb', '#dae982']
STYLE = '''
QWidget { color: #dfe8f4; font-family: "Segoe UI", "DejaVu Sans"; font-size: 13px; }
QMainWindow, QWidget#root { background: #10151e; }
QFrame#sidebar { background: #0c1119; border-right: 1px solid #253143; }
QFrame#card { background: #171f2b; border: 1px solid #293548; border-radius: 14px; }
QLabel { background: transparent; }
QLabel#muted { color: #99abc2; }
QLabel#title { font-size: 29px; font-weight: 700; }
QLabel#heading { font-size: 17px; font-weight: 600; }
QLabel#eyebrow { color: #54dfbd; font-size: 11px; font-weight: 700; }
QLabel#price { font-size: 35px; font-weight: 700; color: #71efcd; }
QLabel#error { color: #ffb6a9; background: #362329; padding: 12px; border-radius: 8px; }
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit {
 background: #101720; border: 1px solid #35445b; border-radius: 7px;
 padding: 8px; min-height: 20px; selection-background-color: #247b70;
}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus { border-color: #54dfbd; }
QComboBox QAbstractItemView { background: #202d3f; selection-background-color: #29485a; }
QPushButton { background: #233044; border: 1px solid #36465e; border-radius: 7px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #2d4059; border-color: #708bab; }
QPushButton:disabled { color: #64758b; background: #1b2635; }
QPushButton#primary { background: #54dfbd; color: #09251f; border-color: #54dfbd; }
QPushButton#primary:hover { background: #88f3d5; }
QPushButton#nav { text-align: left; border: 0; background: transparent; padding: 13px 16px; color: #9fb0c6; }
QPushButton#nav:checked { background: #18352f; color: #79edcf; }
QPushButton#nav:hover { background: #1a2836; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: #10151e; }
QTableWidget { background: #141d29; alternate-background-color: #1b2737; gridline-color: #293548; border: 1px solid #293548; border-radius: 8px; }
QHeaderView::section { background: #223047; padding: 10px; border: none; font-weight: 600; }
QTableWidget::item { padding: 8px; }
QTableWidget::item:selected { background: #265a53; }
QStatusBar { background: #0c1119; color: #8ca0ba; }
QToolTip { color: #e3ecf7; background: #26384d; border: 1px solid #708bab; padding: 8px; }
QScrollBar:vertical { background: #141c27; width: 10px; }
QScrollBar::handle:vertical { background: #43566f; min-height: 25px; border-radius: 4px; }
'''


def label(text, kind=None, wrap=False):
    widget = QLabel(text)
    if kind:
        widget.setObjectName(kind)
    widget.setWordWrap(wrap)
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    if primary:
        widget.setObjectName('primary')
    widget.clicked.connect(callback)
    return widget


def card(title, subtitle=''):
    frame = QFrame()
    frame.setObjectName('card')
    box = QVBoxLayout(frame)
    box.setContentsMargins(22, 20, 22, 22)
    box.setSpacing(12)
    box.addWidget(label(title, 'heading'))
    if subtitle:
        box.addWidget(label(subtitle, 'muted', True))
    return frame, box


class CostBar(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self.setFixedHeight(15)

    def paintEvent(self, event):
        painter = QPainter(self)
        total = sum(self.values)
        if total <= 0:
            painter.fillRect(self.rect(), QColor('#293548'))
            return
        left = 0
        for index, value in enumerate(self.values):
            right = left + float(value / total) * self.width()
            painter.fillRect(round(left), 0, max(0, round(right) - round(left)), self.height(), QColor(COLORS[index]))
            left = right


class MainWindow(QMainWindow):
    def __init__(self, data_dir=None):
        super().__init__()
        location = data_dir or QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        self.library = Library(Path(location) / 'studio.sqlite3')
        self.fields = {}
        self.loading = True
        self.dirty = False
        self.identity = None
        self.result = None
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1400, max(1080, screen.width() - 60)), min(900, max(680, screen.height() - 70)))
        self.setMinimumSize(1080, 680)
        self.setStyleSheet(STYLE)
        self.root = QWidget()
        self.root.setObjectName('root')
        self.setCentralWidget(self.root)
        layout = QHBoxLayout(self.root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(205)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18, 30, 18, 20)
        nav.setSpacing(8)
        nav.addWidget(label('◈  MAKER PRICE', 'heading'))
        nav.addWidget(label('3D STUDIO  /  PREVIEW', 'eyebrow'))
        nav.addSpacing(32)
        self.nav_buttons = []
        for index, text in enumerate(['01   Orçamento', '02   Produção', '03   Preço e lucro', '04   Biblioteca']):
            b = button(text, lambda checked=False, i=index: self.go(i))
            b.setObjectName('nav')
            b.setCheckable(True)
            nav.addWidget(b)
            self.nav_buttons.append(b)
        nav.addStretch()
        nav.addWidget(label('FEITO PARA MAKERS', 'eyebrow'))
        nav.addWidget(label('Custos claros.\nDecisões melhores.', 'muted'))
        nav.addSpacing(12)
        nav.addWidget(label('CleitinhoDEV · v2 experimental', 'muted', True))
        layout.addWidget(sidebar)
        body = QVBoxLayout()
        body.setContentsMargins(28, 24, 28, 18)
        body.setSpacing(20)
        layout.addLayout(body, 1)
        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label('SEU ATELIÊ, EM NÚMEROS', 'eyebrow'))
        self.page_title = label('Um bom projeto começa aqui.', 'title', True)
        titles.addWidget(self.page_title)
        top.addLayout(titles, 1)
        top.addWidget(button('Novo', self.new))
        top.addWidget(button('Abrir JSON', self.open_file))
        top.addWidget(button('Salvar', self.save, True))
        body.addLayout(top)
        content = QHBoxLayout()
        content.setSpacing(20)
        self.stack = QStackedWidget()
        content.addWidget(self.stack, 1)
        self.make_quote_page()
        self.make_production_page()
        self.make_price_page()
        self.make_library_page()
        self.make_summary(content)
        body.addLayout(content, 1)
        for shortcut, fn in [('Ctrl+S', self.save), ('Ctrl+N', self.new), ('Ctrl+O', self.open_file), ('Ctrl+Shift+S', self.export_json)]:
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(fn)
            self.addAction(action)
        self.statusBar().showMessage('Offline · Dados salvos neste computador · Valores iniciais são exemplos editáveis')
        self.load_quote(Quote())
        self.go(0)

    def page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 0, 8, 0)
        box.setSpacing(16)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.stack.addWidget(scroll)
        return box

    def text_field(self, key, placeholder=''):
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        widget.setMaxLength(300)
        widget.textChanged.connect(self.changed)
        self.fields[key] = widget
        return widget

    def combo(self, key, items):
        widget = QComboBox()
        widget.addItems(items)
        widget.currentTextChanged.connect(self.changed)
        self.fields[key] = widget
        return widget

    def numeric(self, key, suffix='', maximum=1000000000, decimals=2):
        widget = QDoubleSpinBox()
        widget.setLocale(QLocale('pt_BR'))
        widget.setDecimals(decimals)
        widget.setRange(0, maximum)
        widget.setGroupSeparatorShown(True)
        widget.setSuffix(suffix)
        widget.setKeyboardTracking(False)
        widget.valueChanged.connect(self.changed)
        widget.setMinimumWidth(120)
        self.fields[key] = widget
        return widget

    def form(self, box, rows):
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)
        for index, (title, widget) in enumerate(rows):
            column = index % 2
            row = (index // 2) * 2
            grid.addWidget(label(title, 'muted'), row, column)
            grid.addWidget(widget, row + 1, column)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        box.addLayout(grid)

    def make_quote_page(self):
        page = self.page()
        frame, box = card('01 / Identidade do projeto', 'Organize o lote, o cliente e os detalhes da sua próxima criação.')
        self.form(box, [('Nome do projeto', self.text_field('title', 'Ex.: Miniaturas — coleção romana')),
                        ('Cliente', self.text_field('client', 'Nome ou referência do cliente'))])
        row = QHBoxLayout()
        self.units = QSpinBox()
        self.units.setRange(1, 100000)
        self.units.valueChanged.connect(self.changed)
        self.fields['units'] = self.units
        row.addWidget(label('Peças no lote', 'muted'))
        row.addWidget(self.units)
        row.addWidget(label('Tecnologia', 'muted'))
        row.addWidget(self.combo('process', ['Resina', 'FDM']))
        box.addLayout(row)
        page.addWidget(frame)
        frame, box = card('02 / Material', 'Informe o consumo de TODO o lote. Se o fatiador já inclui suportes, deixe o adicional em 0%.')
        self.material_profiles = QComboBox()
        self.material_profiles.currentIndexChanged.connect(lambda: self.apply_profile('material'))
        box.addWidget(self.material_profiles)
        self.form(box, [('Preço do material / kg (R$)', self.numeric('material_price')),
                        ('Consumo do lote', self.numeric('amount', decimals=3)),
                        ('Unidade do consumo', self.combo('amount_unit', ['g', 'ml'])),
                        ('Densidade (g/ml)', self.numeric('density', decimals=3, maximum=100)),
                        ('Suportes adicionais', self.numeric('supports', ' %', 1000)),
                        ('Perda de material', self.numeric('waste', ' %', 1000))])
        box.addWidget(button('Salvar perfil de material', lambda: self.save_profile('material')))
        page.addWidget(frame)
        frame, box = card('Notas do orçamento')
        notes = QTextEdit()
        notes.setPlaceholderText('Acabamento, cor, prazo, condições e observações…')
        notes.setMaximumHeight(110)
        notes.textChanged.connect(self.changed)
        self.fields['notes'] = notes
        box.addWidget(notes)
        page.addWidget(frame)
        page.addStretch()
        self.refresh_profiles('material')

    def make_production_page(self):
        page = self.page()
        frame, box = card('03 / Máquina e energia', 'Tempo total de máquina para produzir o lote. Os perfis são preenchidos por você.')
        self.printer_profiles = QComboBox()
        self.printer_profiles.currentIndexChanged.connect(lambda: self.apply_profile('printer'))
        box.addWidget(self.printer_profiles)
        self.form(box, [('Tempo de impressão', self.numeric('hours', ' h', decimals=3)),
                        ('Potência média', self.numeric('watts', ' W')),
                        ('Tarifa por kWh (R$)', self.numeric('tariff', decimals=4)),
                        ('Desgaste por hora (R$)', self.numeric('wear_hour', decimals=3))])
        box.addWidget(label('Desgaste/h: rateie manutenção, LCD/FEP ou componentes FDM pela vida útil estimada.', 'muted', True))
        box.addWidget(button('Salvar perfil de impressora', lambda: self.save_profile('printer')))
        page.addWidget(frame)
        frame, box = card('04 / Trabalho e acabamento', 'Horas de trabalho ativo; o tempo de máquina é calculado separadamente.')
        self.form(box, [('Trabalho ativo no lote', self.numeric('labor_hours', ' h', decimals=3)),
                        ('Valor da sua hora (R$)', self.numeric('labor_rate')),
                        ('Acabamento do lote (R$)', self.numeric('finishing')),
                        ('Outros custos do lote (R$)', self.numeric('extra'))])
        box.addWidget(label('Em acabamento, inclua lavagem, cura, lixas, primer, pintura e consumíveis.', 'muted', True))
        page.addWidget(frame)
        frame, box = card('05 / Entrega e imprevistos')
        self.form(box, [('Embalagem por peça (R$)', self.numeric('packaging_unit')),
                        ('Frete do pedido (R$)', self.numeric('shipping')),
                        ('Reserva sobre custos', self.numeric('contingency', ' %', 1000))])
        box.addWidget(label('A reserva é um adicional de segurança configurável, não uma probabilidade calculada de falha.', 'muted', True))
        page.addWidget(frame)
        page.addStretch()
        self.refresh_profiles('printer')

    def make_price_page(self):
        page = self.page()
        frame, box = card('06 / Sua estratégia de preço', 'Escolha a meta. O desconto é aplicado depois do preço sugerido e reduz a margem final.')
        self.form(box, [('Método de precificação', self.combo('pricing', ['Margem sobre venda', 'Acréscimo sobre custo'])),
                        ('Meta desejada', self.numeric('target', ' %', 1000)),
                        ('Taxas sobre a venda', self.numeric('fee', ' %', 99.99)),
                        ('Desconto no pedido (R$)', self.numeric('discount'))])
        box.addWidget(label('Margem: parcela do preço de venda que sobra após custos e taxas.\nAcréscimo: percentual aplicado sobre o custo, com taxas compensadas no preço.', 'muted', True))
        page.addWidget(frame)
        frame, box = card('Simule antes de fechar', 'Comparação de preços com três metas. Mantém custos, taxas e desconto do orçamento atual.')
        self.scenarios = QTableWidget(3, 3)
        self.scenarios.setHorizontalHeaderLabels(['Meta', 'Pedido', 'Resultado'])
        self.configure_table(self.scenarios)
        self.scenarios.setFixedHeight(168)
        box.addWidget(self.scenarios)
        page.addWidget(frame)
        frame, box = card('Compartilhe o orçamento')
        box.addWidget(label('PDF apresenta a proposta ao cliente. CSV detalha os custos para seu controle. JSON permite reabrir no Studio.', 'muted', True))
        row = QHBoxLayout()
        row.addWidget(button('Proposta PDF', self.export_pdf, True))
        row.addWidget(button('Custos CSV', self.export_csv))
        row.addWidget(button('Exportar JSON', self.export_json))
        box.addLayout(row)
        page.addWidget(frame)
        page.addStretch()

    @staticmethod
    def configure_table(table):
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().hide()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)

    def make_library_page(self):
        page = self.page()
        frame, box = card('Seus projetos, sempre à mão', 'Salvar atualiza o orçamento aberto. Duplicar cria uma cópia independente.')
        search = QLineEdit()
        search.setPlaceholderText('Buscar por projeto ou cliente…')
        search.textChanged.connect(self.refresh_history)
        self.search = search
        box.addWidget(search)
        self.history = QTableWidget(0, 3)
        self.history.setHorizontalHeaderLabels(['Projeto', 'Cliente', 'Atualização'])
        self.configure_table(self.history)
        self.history.setMinimumHeight(280)
        self.history.doubleClicked.connect(self.open_history)
        box.addWidget(self.history)
        row = QHBoxLayout()
        row.addWidget(button('Abrir selecionado', self.open_history, True))
        row.addWidget(button('Duplicar selecionado', self.duplicate_history))
        box.addLayout(row)
        page.addWidget(frame)
        page.addStretch()

    def make_summary(self, layout):
        frame, box = card('Resumo do orçamento')
        frame.setFixedWidth(305)
        box.addWidget(label('PREÇO DO PEDIDO', 'eyebrow'))
        self.price_label = label('', 'price')
        box.addWidget(self.price_label)
        self.unit_label = label('', 'muted', True)
        box.addWidget(self.unit_label)
        self.bar = CostBar()
        box.addSpacing(10)
        box.addWidget(self.bar)
        self.breakdown = QFormLayout()
        self.breakdown.setSpacing(9)
        self.breakdown_labels = {}
        for index, name in enumerate(calculate(Quote()).categories):
            title = label('● ' + name)
            title.setStyleSheet(f'color: {COLORS[index]}; font-size: 11px;')
            value = label('')
            value.setAlignment(Qt.AlignRight)
            self.breakdown.addRow(title, value)
            self.breakdown_labels[name] = value
        box.addLayout(self.breakdown)
        self.metrics = label('', wrap=True)
        box.addSpacing(8)
        box.addWidget(self.metrics)
        self.error = label('', 'error', True)
        box.addWidget(self.error)
        box.addStretch()
        box.addWidget(button('Exportar proposta PDF', self.export_pdf, True))
        box.addWidget(label('Valores estimados · revise antes de vender.\nConsumos e tempos referem-se ao lote.', 'muted', True))
        layout.addWidget(frame)

    def current(self):
        data = {}
        for name, widget in self.fields.items():
            if isinstance(widget, QDoubleSpinBox):
                widget.interpretText()
                data[name] = str(widget.value())
            elif isinstance(widget, QSpinBox):
                widget.interpretText()
                data[name] = widget.value()
            elif isinstance(widget, QComboBox):
                data[name] = widget.currentText()
            elif isinstance(widget, QTextEdit):
                data[name] = widget.toPlainText()
            else:
                data[name] = widget.text()
        return Quote(**data)

    def changed(self, *args):
        if self.loading:
            return
        self.dirty = True
        self.update_title()
        self.recalculate()

    def update_title(self):
        self.setWindowTitle(('● ' if self.dirty else '') + 'Maker Price 3D Studio — ' + self.fields['title'].text())

    def recalculate(self):
        try:
            quote = self.current()
            result = calculate(quote)
        except (ValueError, TypeError) as exc:
            self.result = None
            self.error.setText(str(exc))
            self.error.show()
            self.price_label.setText('—')
            self.unit_label.setText('Revise os campos para calcular.')
            self.metrics.clear()
            self.bar.values = []
            self.bar.update()
            for value in self.breakdown_labels.values():
                value.setText('—')
            self.scenarios.clearContents()
            return
        self.result = result
        self.price_label.setText(money(result.price))
        self.unit_label.setText(f'{quote.units} peça(s) · {money(result.unit_price)} / peça\n{float(result.grams):.1f} g de material com adicionais')
        self.bar.values = list(result.categories.values())
        self.bar.update()
        for name, value in result.categories.items():
            self.breakdown_labels[name].setText(money(value))
        self.metrics.setText(f'Custo do lote: {money(result.cost)}\nTaxas da venda: {money(result.fees)}\nResultado estimado: {money(result.profit)}\nMargem efetiva: {float(result.margin):.2f}%')
        self.error.setVisible(result.profit < 0)
        self.error.setText('Atenção: este preço está abaixo dos custos e taxas.')
        for row, delta in enumerate((-10, 0, 10)):
            data = asdict(quote)
            data['target'] = str(max(0, float(quote.target) + delta))
            try:
                scenario = calculate(Quote(**data))
                values = [f'{float(data["target"]):g}%', money(scenario.price), money(scenario.profit)]
            except ValueError:
                values = [f'{float(data["target"]):g}%', 'Meta inválida', '—']
            for column, value in enumerate(values):
                self.scenarios.setItem(row, column, QTableWidgetItem(value))

    def load_quote(self, quote, identity=None):
        quote.validate()
        self.loading = True
        for name, value in asdict(quote).items():
            widget = self.fields[name]
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(float(value) if isinstance(widget, QDoubleSpinBox) else value)
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(value)
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(value)
            else:
                widget.setText(value)
        self.identity = identity
        self.loading = False
        self.dirty = False
        self.update_title()
        self.recalculate()

    def go(self, index):
        self.stack.setCurrentIndex(index)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == index)
        self.page_title.setText(['Um bom projeto começa aqui.', 'Do material ao acabamento.', 'Valorize o seu trabalho.', 'Sua próxima ideia já tem história.'][index])
        if index == 3:
            self.refresh_history()

    def failure(self, error):
        QMessageBox.warning(self, 'Não foi possível concluir', str(error))

    def save(self):
        try:
            quote = self.current()
            calculate(quote)
            self.identity = self.library.save(quote, self.identity)
            self.dirty = False
            self.update_title()
            self.refresh_history()
            self.statusBar().showMessage('Orçamento salvo na biblioteca deste computador.', 6000)
            return True
        except Exception as exc:
            self.failure(exc)
            return False

    def confirm_replace(self):
        if not self.dirty:
            return True
        answer = QMessageBox.question(self, 'Salvar alterações?', 'Deseja salvar o orçamento atual antes de continuar?',
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        if answer == QMessageBox.Save:
            return self.save()
        return answer == QMessageBox.Discard

    def new(self):
        if self.confirm_replace():
            self.load_quote(Quote())
            self.go(0)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir orçamento Studio', '', 'Orçamento JSON (*.json)')
        if not path:
            return
        try:
            quote = read_document(path)
            calculate(quote)
            if self.confirm_replace():
                self.load_quote(quote)
                self.dirty = True
                self.update_title()
                self.go(0)
        except Exception as exc:
            self.failure(exc)

    def refresh_history(self, *args):
        try:
            self.history_rows = self.library.list(self.search.text())
            self.history.setRowCount(len(self.history_rows))
            for row, (_, title, client, date) in enumerate(self.history_rows):
                local_date = datetime.fromisoformat(date).astimezone().strftime('%d/%m/%Y %H:%M')
                for col, text in enumerate((title or 'Sem título', client or '—', local_date)):
                    self.history.setItem(row, col, QTableWidgetItem(text))
        except Exception as exc:
            self.failure(exc)

    def selected_history(self):
        row = self.history.currentRow()
        return self.history_rows[row][0] if row >= 0 else None

    def open_history(self, *args, duplicate=False):
        identity = self.selected_history()
        if identity is None:
            self.statusBar().showMessage('Selecione um orçamento na tabela.', 4000)
            return
        try:
            quote = self.library.get(identity)
            if self.confirm_replace():
                if duplicate:
                    quote.title += ' — cópia'
                self.load_quote(quote, None if duplicate else identity)
                self.dirty = duplicate
                self.update_title()
                self.go(0)
        except Exception as exc:
            self.failure(exc)

    def duplicate_history(self):
        self.open_history(duplicate=True)

    def profile_fields(self, kind):
        return ('material_price', 'density', 'process') if kind == 'material' else ('watts', 'wear_hour', 'process')

    def refresh_profiles(self, kind):
        widget = self.material_profiles if kind == 'material' else self.printer_profiles
        widget.blockSignals(True)
        widget.clear()
        widget.addItem('Selecionar perfil salvo…', None)
        for name, data in self.library.profiles(kind):
            widget.addItem(name, data)
        widget.blockSignals(False)

    def save_profile(self, kind):
        name, ok = QInputDialog.getText(self, 'Salvar perfil', 'Nome do material ou impressora:')
        if not ok or not name.strip():
            return
        try:
            if any(existing == name.strip() for existing, _ in self.library.profiles(kind)):
                if QMessageBox.question(self, 'Substituir perfil?', 'Já existe um perfil com esse nome. Substituir?') != QMessageBox.Yes:
                    return
            quote = self.current().validate()
            self.library.save_profile(kind, name.strip(), {key: getattr(quote, key) for key in self.profile_fields(kind)})
            self.refresh_profiles(kind)
            self.statusBar().showMessage('Perfil salvo. Selecione-o em futuros orçamentos.', 5000)
        except Exception as exc:
            self.failure(exc)

    def apply_profile(self, kind):
        widget = self.material_profiles if kind == 'material' else self.printer_profiles
        data = widget.currentData()
        if not data or self.loading:
            return
        try:
            quote = self.current()
            for key in self.profile_fields(kind):
                setattr(quote, key, data[key])
            identity = self.identity
            self.load_quote(quote, identity)
            self.dirty = True
            self.update_title()
        except Exception as exc:
            self.failure(exc)

    def export_json(self):
        try:
            quote = self.current()
            calculate(quote)
            path, _ = QFileDialog.getSaveFileName(self, 'Exportar orçamento', 'orcamento-studio.json', 'JSON (*.json)')
            if path:
                write_document(path, quote)
                self.statusBar().showMessage('JSON exportado. Use Salvar para manter uma cópia na biblioteca.', 6000)
        except Exception as exc:
            self.failure(exc)

    def export_csv(self):
        try:
            result = calculate(self.current())
            path, _ = QFileDialog.getSaveFileName(self, 'Exportar custos', 'custos.csv', 'CSV (*.csv)')
            if path:
                with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
                    writer = csv.writer(stream, delimiter=';')
                    writer.writerow(['Categoria', 'Valor (R$)'])
                    for name, value in [*result.categories.items(), ('Custo total', result.cost), ('Taxas de venda', result.fees), ('Preço do pedido', result.price), ('Resultado estimado', result.profit)]:
                        writer.writerow([name, f'{value:.2f}'.replace('.', ',')])
                self.statusBar().showMessage('CSV exportado.', 4000)
        except Exception as exc:
            self.failure(exc)

    def write_pdf(self, path):
        quote = self.current()
        result = calculate(quote)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(path))
        printer.setDocName(quote.title)
        document = QTextDocument()
        document.setDefaultFont(QFont('Arial', 11))
        notes = escape(quote.notes).replace('\n', '<br>')
        document.setHtml(f'''<style>body {{ color: #172c38; }} h1 {{ color: #18745e; }} td {{ padding: 12px; }}
        th {{ background: #e6f1ec; padding: 12px; text-align: left; }}</style>
        <p>MAKER PRICE 3D · PROPOSTA</p><h1>{escape(quote.title) or 'Orçamento'}</h1>
        <p>Cliente: {escape(quote.client) or 'Não informado'}<br>Data: {datetime.now():%d/%m/%Y}<br>Tecnologia: {escape(quote.process)}</p>
        <table width="100%" cellspacing="0"><tr><th>Quantidade</th><th>Valor médio por peça</th><th>Total do pedido</th></tr>
        <tr><td>{quote.units}</td><td>{money(result.unit_price)}</td><td><b>{money(result.price)}</b></td></tr></table>
        <p>Desconto aplicado ao pedido: {money(quote.discount)}</p><h3>Detalhes e condições</h3><p>{notes or 'Condições e prazo a combinar.'}</p>
        <hr><p>Proposta estimativa. Confirme detalhes, prazo e condições antes da produção.<br>
        O valor médio por peça é arredondado para exibição; prevalece o total do pedido.</p>''')
        document.print_(printer)
        if not Path(path).is_file() or Path(path).stat().st_size == 0:
            raise OSError('Não foi possível gravar o PDF.')

    def export_pdf(self):
        try:
            calculate(self.current())
            path, _ = QFileDialog.getSaveFileName(self, 'Exportar proposta', 'proposta.pdf', 'PDF (*.pdf)')
            if path:
                self.write_pdf(path)
                self.statusBar().showMessage('Proposta PDF exportada.', 4000)
        except Exception as exc:
            self.failure(exc)

    def closeEvent(self, event):
        if self.confirm_replace():
            self.library.close()
            event.accept()
        else:
            event.ignore()
