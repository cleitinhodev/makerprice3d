"""Classic three-column arrangement with Qt controls and reusable Studio actions."""
from PySide6.QtCore import Qt, QStandardPaths
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QHBoxLayout, QVBoxLayout, QGridLayout, QScrollArea, QSpinBox, QComboBox,
    QDialog, QStackedWidget, QTableWidget, QTextEdit)
from pathlib import Path
from .domain import Quote, calculate
from .storage import Library
from .ui import StudioActions, STYLE, COLORS, CostBar, label, button

STAGES = {
    'Material': '#ff4c4c', 'Energia': '#4cff4c', 'Desgaste': '#7c7cff',
    'Acabamento': '#ffd24c', 'Despesas': '#f26522', 'Logística': '#b187ff',
    'Mão de obra': '#4cff9d', 'Total': '#ff4c9d',
}
DASH_STYLE = STYLE + '''
QWidget { font-size: 12px; }
QLabel#heading { font-size: 15px; }
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { padding: 3px 6px; min-height: 21px; }
QPushButton { padding: 6px 9px; }
QLabel#price { font-size: 32px; color: #ff89ba; }
QLabel#error { padding: 5px; }
QTextEdit { padding: 5px; }
QDialog { background: #10151e; }
'''


class MainWindow(StudioActions):
    def __init__(self, data_dir=None):
        QMainWindow.__init__(self)
        location = data_dir or QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        self.library = Library(Path(location) / 'studio.sqlite3')
        self.fields = {}
        self.loading, self.dirty = True, False
        self.identity = self.result = None
        self.panels = {}
        self.breakdown_labels = {}
        self.setStyleSheet(DASH_STYLE)
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1440, max(1100, screen.width() - 40)), min(860, max(700, screen.height() - 60)))
        self.setMinimumSize(1100, 680)
        root = QWidget()
        root.setObjectName('root')
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 10, 12, 8)
        outer.setSpacing(8)
        toolbar = QHBoxLayout()
        brand = label('◈  MAKER PRICE 3D', 'heading')
        toolbar.addWidget(brand)
        toolbar.addWidget(label('STUDIO · PAINEL CLÁSSICO', 'eyebrow'))
        toolbar.addStretch()
        toolbar.addWidget(button('Novo', self.new))
        toolbar.addWidget(button('Abrir JSON', self.open_file))
        toolbar.addWidget(button('Biblioteca', lambda: self.go(3)))
        toolbar.addWidget(button('Exportar', self.show_exports))
        toolbar.addWidget(button('Salvar', self.save, True))
        outer.addLayout(toolbar)
        identity = QHBoxLayout()
        for name, title in [('title', 'Projeto'), ('client', 'Cliente')]:
            identity.addWidget(label(title, 'muted'))
            identity.addWidget(self.text_field(name), 1)
        identity.addWidget(label('Lote', 'muted'))
        units = QSpinBox()
        units.setRange(1, 100000)
        units.setSuffix(' peça(s)')
        units.valueChanged.connect(self.changed)
        self.fields['units'] = units
        identity.addWidget(units)
        identity.addWidget(self.combo('process', ['Resina', 'FDM']))
        outer.addLayout(identity)
        # One shared viewport preserves the original columns. At lower heights only
        # the cost area scrolls; the bottom-right Total stays outside the viewport.
        area = QHBoxLayout()
        area.setSpacing(10)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_root = QWidget()
        left = QHBoxLayout(left_root)
        left.setContentsMargins(0, 0, 4, 0)
        left.setSpacing(10)
        self.columns = []
        for _ in range(2):
            column = QVBoxLayout()
            column.setSpacing(10)
            left.addLayout(column, 1)
            self.columns.append(column)
        left_scroll.setWidget(left_root)
        area.addWidget(left_scroll, 2)
        right = QVBoxLayout()
        right.setSpacing(10)
        area.addLayout(right, 1)
        self.build_material(self.columns[0])
        self.build_energy(self.columns[0])
        self.build_wear(self.columns[0])
        self.columns[0].addStretch()
        self.build_finishing(self.columns[1])
        self.build_expenses(self.columns[1])
        self.columns[1].addStretch()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_root = QWidget()
        right_costs = QVBoxLayout(right_root)
        right_costs.setContentsMargins(0, 0, 0, 0)
        right_costs.setSpacing(10)
        self.build_logistics(right_costs)
        self.build_labor(right_costs)
        right_costs.addStretch()
        right_scroll.setWidget(right_root)
        right.addWidget(right_scroll, 1)
        self.build_total(right)
        outer.addLayout(area, 1)
        self.build_dialogs()
        self.refresh_profiles('material')
        self.refresh_profiles('printer')
        for shortcut, fn in [('Ctrl+S', self.save), ('Ctrl+N', self.new), ('Ctrl+O', self.open_file), ('Ctrl+Shift+S', self.export_json)]:
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(fn)
            self.addAction(action)
        self.statusBar().showMessage('Valores de exemplo · Consumo e tempo são do lote inteiro · Ctrl+S salva na biblioteca')
        self.load_quote(Quote())

    def panel(self, parent, name, category=None):
        color = STAGES[name]
        frame = QFrame()
        frame.setObjectName('stage' + str(len(self.panels)))
        frame.setStyleSheet(f'QFrame#{frame.objectName()} {{ background: #171f2b; border: 1px solid {color}; border-top: 3px solid {color}; border-radius: 9px; }}')
        box = QVBoxLayout(frame)
        box.setContentsMargins(12, 9, 12, 12)
        box.setSpacing(7)
        head = QHBoxLayout()
        title = label(name, 'heading')
        title.setStyleSheet(f'color: {color}; font-weight: 700;')
        head.addWidget(title)
        head.addStretch()
        if category:
            subtotal = label('R$ 0,00')
            subtotal.setStyleSheet(f'color: {color}; font-weight: 700;')
            head.addWidget(subtotal)
            self.breakdown_labels[category] = subtotal
        box.addLayout(head)
        parent.addWidget(frame)
        self.panels[name] = frame
        return box

    def compact_fields(self, box, rows):
        grid = QGridLayout()
        grid.setVerticalSpacing(6)
        grid.setHorizontalSpacing(8)
        for row, (title, widget) in enumerate(rows):
            text = label(title, 'muted', True)
            grid.addWidget(text, row, 0)
            grid.addWidget(widget, row, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        box.addLayout(grid)

    def paired_fields(self, box, rows):
        grid = QGridLayout()
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(10)
        for i, (title, widget) in enumerate(rows):
            row, col = (i // 2) * 2, i % 2
            grid.addWidget(label(title, 'muted'), row, col)
            grid.addWidget(widget, row + 1, col)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        box.addLayout(grid)

    def build_material(self, parent):
        box = self.panel(parent, 'Material', 'Material')
        row = QHBoxLayout()
        self.material_profiles = QComboBox()
        self.material_profiles.currentIndexChanged.connect(lambda: self.apply_profile('material'))
        row.addWidget(self.material_profiles, 1)
        row.addWidget(button('Salvar perfil', lambda: self.save_profile('material')))
        box.addLayout(row)
        self.paired_fields(box, [
            ('Preço / kg (R$)', self.numeric('material_price')),
            ('Consumo do lote', self.numeric('amount', decimals=3)),
            ('Unidade', self.combo('amount_unit', ['g', 'ml'])),
            ('Densidade (g/ml)', self.numeric('density', decimals=3, maximum=100)),
            ('Suportes adicionais', self.numeric('supports', ' %', 1000)),
            ('Perda de material', self.numeric('waste', ' %', 1000))])
        box.addWidget(label('Suportes já incluídos no fatiador? Use 0%.', 'muted', True))

    def build_energy(self, parent):
        box = self.panel(parent, 'Energia', 'Energia')
        self.compact_fields(box, [('Tempo total de máquina', self.numeric('hours', ' h', decimals=3)),
                                 ('Potência média', self.numeric('watts', ' W')),
                                 ('Tarifa / kWh (R$)', self.numeric('tariff', decimals=4))])

    def build_wear(self, parent):
        box = self.panel(parent, 'Desgaste', 'Desgaste')
        self.printer_profiles = QComboBox()
        self.printer_profiles.currentIndexChanged.connect(lambda: self.apply_profile('printer'))
        box.addWidget(self.printer_profiles)
        self.compact_fields(box, [('Manutenção / hora (R$)', self.numeric('wear_hour', decimals=3))])
        box.addWidget(button('Salvar perfil de impressora', lambda: self.save_profile('printer')))
        box.addWidget(label('Inclua desgaste de LCD/FEP ou componentes FDM.', 'muted', True))

    def build_finishing(self, parent):
        box = self.panel(parent, 'Acabamento', 'Acabamento')
        for text, color in [('● Lavagem e cura', '#ffd24c'), ('● Lixa e preparação', '#ff7afc'), ('● Pintura e verniz', '#4cfff6')]:
            item = label(text)
            item.setStyleSheet(f'color: {color};')
            box.addWidget(item)
        self.compact_fields(box, [('Consumíveis do lote (R$)', self.numeric('finishing'))])
        box.addWidget(label('Some solvente, lixas, primer e tinta usados no lote. O trabalho ativo entra em Mão de obra.', 'muted', True))

    def build_expenses(self, parent):
        box = self.panel(parent, 'Despesas', 'Outros custos')
        self.compact_fields(box, [('Outras despesas (R$)', self.numeric('extra')),
                                 ('Reserva de imprevistos', self.numeric('contingency', ' %', 1000))])
        reserve = label('')
        reserve.setStyleSheet('color: #dae982;')
        self.breakdown_labels['Reserva de imprevistos'] = reserve
        box.addWidget(reserve)
        box.addWidget(label('Reserva aplicada sobre a soma dos custos.', 'muted', True))
        box.addWidget(label('Observações / condições da proposta', 'muted'))
        notes = QTextEdit()
        notes.setPlaceholderText('Detalhes do acabamento, prazo, cor, condições…')
        notes.setMinimumHeight(110)
        notes.setMaximumHeight(180)
        notes.textChanged.connect(self.changed)
        self.fields['notes'] = notes
        box.addWidget(notes)

    def build_logistics(self, parent):
        box = self.panel(parent, 'Logística', 'Embalagem e frete')
        self.compact_fields(box, [('Embalagem / peça (R$)', self.numeric('packaging_unit')),
                                 ('Frete do pedido (R$)', self.numeric('shipping')),
                                 ('Taxas sobre venda', self.numeric('fee', ' %', 99.99)),
                                 ('Desconto no pedido (R$)', self.numeric('discount'))])

    def build_labor(self, parent):
        box = self.panel(parent, 'Mão de obra', 'Mão de obra')
        self.compact_fields(box, [('Trabalho ativo no lote', self.numeric('labor_hours', ' h', decimals=3)),
                                 ('Valor da hora (R$)', self.numeric('labor_rate'))])

    def build_total(self, parent):
        box = self.panel(parent, 'Total')
        self.panels['Total'].setMinimumHeight(310)
        row = QHBoxLayout()
        row.addWidget(self.combo('pricing', ['Margem sobre venda', 'Acréscimo sobre custo']), 1)
        target = self.numeric('target', ' %', 1000)
        target.setMaximumWidth(100)
        row.addWidget(target)
        box.addLayout(row)
        self.bar = CostBar()
        box.addWidget(self.bar)
        legend = label('● Material  ● Energia  ● Desgaste  ● Acabamento\n● Mão de obra  ● Logística  ● Despesas  ● Reserva', 'muted')
        legend.setText('<span style="color:#ff4c4c">● Material</span> · <span style="color:#4cff4c">● Energia</span> · <span style="color:#7c7cff">● Desgaste</span> · <span style="color:#ffd24c">● Acabamento</span><br><span style="color:#4cff9d">● Trabalho</span> · <span style="color:#b187ff">● Logística</span> · <span style="color:#f26522">● Despesas</span> · <span style="color:#dae982">● Reserva</span>')
        legend.setStyleSheet('font-size: 10px;')
        box.addWidget(legend)
        self.metrics = label('', wrap=True)
        box.addWidget(self.metrics)
        self.price_label = label('', 'price')
        box.addWidget(self.price_label)
        self.unit_label = label('', 'muted', True)
        box.addWidget(self.unit_label)
        self.error = label('', 'error', True)
        box.addWidget(self.error)
        row = QHBoxLayout()
        row.addWidget(button('Comparar metas', self.show_exports))
        row.addWidget(button('Proposta PDF', self.export_pdf, True))
        box.addLayout(row)

    def build_dialogs(self):
        self.library_dialog = QDialog(self)
        self.library_dialog.setWindowTitle('Biblioteca de orçamentos')
        self.library_dialog.resize(800, 580)
        library_layout = QVBoxLayout(self.library_dialog)
        self.stack = QStackedWidget()
        library_layout.addWidget(self.stack)
        self.make_library_page()
        self.exports_dialog = QDialog(self)
        self.exports_dialog.setWindowTitle('Comparação e exportação')
        self.exports_dialog.resize(650, 340)
        box = QVBoxLayout(self.exports_dialog)
        box.addWidget(label('Compare suas metas', 'heading'))
        box.addWidget(label('Custos, taxas e desconto são mantidos. O desconto reduz a margem final.', 'muted', True))
        self.scenarios = QTableWidget(3, 3)
        self.scenarios.setHorizontalHeaderLabels(['Meta', 'Pedido', 'Resultado'])
        self.configure_table(self.scenarios)
        box.addWidget(self.scenarios)
        row = QHBoxLayout()
        for title, fn in [('Proposta PDF', self.export_pdf), ('Custos CSV', self.export_csv), ('Orçamento JSON', self.export_json)]:
            row.addWidget(button(title, fn))
        box.addLayout(row)

    def show_exports(self):
        self.recalculate()
        self.exports_dialog.show()
        self.exports_dialog.raise_()

    def go(self, index):
        if index == 3:
            self.refresh_history()
            self.library_dialog.show()
            self.library_dialog.raise_()
        else:
            self.library_dialog.hide()
