''''''
import json

from typing import List, Dict

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
    QTextEdit,
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
)

from molina.ocsr import AnnotatedImageData


COLOR_BACKGROUD_WIDGETS = QColor(250, 250, 250)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.data_images = AnnotatedImageData()
        self.data_images.model_completed.connect(self.on_model_completed)

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

        self.right_widget = QTextEdit(splitter)
        splitter.addWidget(self.right_widget)
        self.right_widget.setMinimumSize(200, 200)
        self.setColor(self.right_widget, COLOR_BACKGROUD_WIDGETS)
        self.right_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.right_widget.setReadOnly(True)

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
        btn.pressed.connect(self.data_images.imageToSmiles)
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
                self.data_images.setImage(pixmap)

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

    def on_model_completed(self, model_result: Dict):
        if model_result:
            model_result_json = json.dumps(model_result, indent=4, sort_keys=True)
            self.right_widget.setPlainText(model_result_json)

        