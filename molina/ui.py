''''''

#from PySide6.QtCore import QSize
#from PySide6.QtWidgets import QMainWindow, QPushButton


#class MainWindow(QMainWindow):
#    def __init__(self):
#       super().__init__()
#        
#        self.setWindowTitle("My App")
#        
#        button = QPushButton("Press Me!")
        
#        self.setFixedSize(QSize(400, 300))
        
        # Set the central widget of the Window.
#        self.setCentralWidget(button)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QLabel,
    QToolBar,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QSplitter,
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
)


class ColoredWidget(QWidget):
    def __init__(self, color):
        super(ColoredWidget, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("My App")

        pagelayout = QVBoxLayout()
        splitter =  QSplitter(self)
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        pagelayout.addWidget(splitter)
        
        self.left_widget = QLabel(splitter)

        self.right_widget = QWidget(splitter)

        btn = QPushButton("Open")
        btn.pressed.connect(self.open_image)
        toolbar.addWidget(btn)

        btn = QPushButton("Save")
        toolbar.addWidget(btn)

        btn = QPushButton("Annotate")
        toolbar.addWidget(btn)

        btn = QPushButton("Predict")
        toolbar.addWidget(btn)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)

    def open_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self, options=options)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.bmp)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            pixmap = self.load_image(selected_file)
            if pixmap:
                self.left_widget.setPixmap(pixmap)

    def load_image(self, file_path):
        pixmap = None
        try:
            pixmap = QPixmap(file_path)
        except Exception as e:
            print(f"Error loading image: {e}")
        return pixmap


