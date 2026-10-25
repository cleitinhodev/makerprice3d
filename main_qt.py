"""Run the new Qt edition without changing the classic main.py entry point."""
import os
import sys
import tempfile
from pathlib import Path


def main():
    smoke = '--smoke-test' in sys.argv
    if smoke:
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from makerprice.dashboard import MainWindow
    app = QApplication(sys.argv)
    app.setOrganizationName('CleitinhoDEV')
    app.setApplicationName('MakerPrice3D-Studio')
    if smoke:
        with tempfile.TemporaryDirectory() as folder:
            window = MainWindow(folder)
            window.show()
            app.processEvents()
            assert window.result is not None
            assert window.save()
            window.write_pdf(Path(folder) / 'smoke.pdf')
            assert len(window.library.list()) == 1
            window.close()
        return 0
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
