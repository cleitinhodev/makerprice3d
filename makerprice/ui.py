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

COLORS = ['#ff4c4c', '#4cff4c', '#7c7cff', '#ffd24c', '#4cff9d', '#b187ff', '#f26522', '#dae982']
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


class StudioActions(QMainWindow):

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
