''''''

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QMainWindow, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("My App")
        
        button = QPushButton("Press Me!")
        
        self.setFixedSize(QSize(400, 300))
        
        # Set the central widget of the Window.
        self.setCentralWidget(button)
