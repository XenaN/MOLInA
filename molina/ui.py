''''''
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QLabel,
    QToolBar,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QWidget,
    QSplitter,
    QSizePolicy
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
)

COLOR_BACKGROUD_WIDGETS = QColor(250, 250, 250)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("MOLInA")

        pagelayout = QHBoxLayout()
        splitter =  QSplitter(self)
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        pagelayout.addWidget(splitter)
        
        self.left_widget = QLabel(splitter)
        splitter.addWidget(self.left_widget)
        self.left_widget.setMinimumSize(200, 200)
        self.setColor(self.left_widget, COLOR_BACKGROUD_WIDGETS)

        self.right_widget = QWidget(splitter)
        splitter.addWidget(self.right_widget)
        self.right_widget.setMinimumSize(200, 200)
        self.setColor(self.right_widget, COLOR_BACKGROUD_WIDGETS)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        btn = QPushButton("Open")
        btn.pressed.connect(self.openImage)
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

    def openImage(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self, options=options)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.bmp)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            pixmap = self.loadImage(selected_file)
            if pixmap:
                self.left_widget.setPixmap(pixmap)

    def loadImage(self, file_path: str):
        pixmap = None
        try:
            pixmap = QPixmap(file_path)
        except Exception as e:
            print(f"Error loading image: {e}")
        return pixmap

    def setColor(self, widget: QWidget, color: QColor):
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)


