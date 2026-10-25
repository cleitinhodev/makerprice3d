import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QMessageBox
from makerprice.dashboard import MainWindow


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.window = MainWindow(self.tmp.name)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.dirty = False
        self.window.close()
        self.tmp.cleanup()

    def test_classic_arrangement_and_live_total(self):
        self.window.resize(1366, 768)
        self.app.processEvents()
        from PySide6.QtCore import QPoint
        panels = self.window.panels
        pos = lambda name: panels[name].mapTo(self.window, QPoint(0, 0))
        self.assertLess(pos('Material').x(), pos('Acabamento').x())
        self.assertLess(pos('Acabamento').x(), pos('Logística').x())
        self.assertLess(pos('Material').y(), pos('Energia').y())
        self.assertLess(pos('Energia').y(), pos('Desgaste').y())
        self.assertLess(pos('Logística').y(), pos('Mão de obra').y())
        self.assertLess(pos('Mão de obra').y(), pos('Total').y())
        self.assertTrue(self.window.price_label.isVisible())
        previous = self.window.result.price
        self.window.fields['amount'].setValue(200)
        self.assertGreater(self.window.result.price, previous)
        self.assertTrue(self.window.dirty)

    def test_auxiliary_windows_preserve_dashboard(self):
        self.window.go(3)
        self.assertTrue(self.window.library_dialog.isVisible())
        self.window.go(0)
        self.assertFalse(self.window.library_dialog.isVisible())
        self.window.show_exports()
        self.assertTrue(self.window.exports_dialog.isVisible())
        self.assertTrue(self.window.panels['Material'].isVisible())
        self.window.exports_dialog.close()

    def test_save_restore_duplicate(self):
        self.window.fields['title'].setText('Teste persistido')
        self.assertTrue(self.window.save())
        identity = self.window.identity
        self.window.load_quote(self.window.library.get(identity), identity)
        self.assertEqual(self.window.fields['title'].text(), 'Teste persistido')
        self.window.refresh_history()
        self.window.history.selectRow(0)
        self.window.duplicate_history()
        self.assertIsNone(self.window.identity)
        self.assertTrue(self.window.dirty)
        self.assertTrue(self.window.save())
        self.assertEqual(len(self.window.library.list()), 2)

    def test_cancel_preserves_unsaved_work(self):
        self.window.fields['title'].setText('Não perder')
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Cancel):
            self.window.new()
        self.assertEqual(self.window.fields['title'].text(), 'Não perder')

    def test_save_failure_prevents_replacement(self):
        self.window.fields['title'].setText('Não perder')
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Save), patch.object(self.window, 'save', return_value=False):
            self.assertFalse(self.window.confirm_replace())

    def test_pdf_and_invalid_margin(self):
        path = Path(self.tmp.name) / 'proposal.pdf'
        self.window.write_pdf(path)
        self.assertTrue(path.read_bytes().startswith(b'%PDF'))
        self.window.fields['target'].setValue(100)
        self.assertIsNone(self.window.result)
        self.assertEqual(self.window.price_label.text(), '—')
        self.window.fields['target'].setValue(30)
        self.assertIsNotNone(self.window.result)
