''''''
import json

from typing import List, Dict

from PySide6.QtCore import Qt, QSize, QDir
from PySide6.QtWidgets import (
    QToolButton,
    QSizePolicy,
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
    QIcon,
)

from molina.data_structs import Dataset


COLOR_BACKGROUD_WIDGETS = QColor(250, 250, 250)
RESOURCES_PATH = QDir("molina/resources")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.zoom_increment = 0.1

        # self.data_images = Dataset()
        # self.data_images.model_completed.connect(self.on_model_completed)

        self.setWindowTitle("MOLInA")

        pagelayout = QHBoxLayout()
        splitter =  QSplitter(self)
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        pagelayout.addWidget(splitter)
        
        self.left_widget = QLabel(splitter)
        splitter.addWidget(self.left_widget)
        self.left_widget.setMinimumSize(200, 200)
        self.left_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setColor(self.left_widget, COLOR_BACKGROUD_WIDGETS)
        self.left_widget.updateGeometry()

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

        btn = QToolButton()
        btn.setIcon(QIcon(RESOURCES_PATH.filePath("left_button.png")))
        toolbar.addWidget(btn)

        btn = QToolButton()
        btn.setIcon(QIcon(RESOURCES_PATH.filePath("right_button.png")))
        toolbar.addWidget(btn)

        toolbar.setIconSize(QSize(19, 19))

        btn = QPushButton("Annotate")
        toolbar.addWidget(btn)

        btn = QPushButton("Current Model")
        # btn.pressed.connect(self.data_images.run_molscribe)
        toolbar.addWidget(btn)

        btn = QPushButton("Predict")
        # btn.pressed.connect(self.data_images.run_molscribe)
        toolbar.addWidget(btn)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)
        self.showMaximized()

    
    def openImage(self) -> None:
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

    def setColor(self, widget: QWidget, color: QColor) -> None:
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)

    def on_model_completed(self, model_result: Dict) -> None:
        if model_result:
            model_result_json = json.dumps(model_result, indent=4, sort_keys=True)
            self.right_widget.setPlainText(model_result_json)

    def zoom_in(self):
      
      self.scale_factor = min(self.scale_factor + self.zoom_increment, 5) 
      self.update()
      
    def zoom_out(self):
      
      self.scale_factor = max(2.5, self.scale_factor - self.zoom_increment)
      self.update()

