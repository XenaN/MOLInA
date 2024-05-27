import sys

from PySide6.QtWidgets import QApplication

from molina import MainWindow
from molina.styles import SCROLLBAR_STYLE

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(SCROLLBAR_STYLE)
    window = MainWindow()
    window.show()
    app.exec()
