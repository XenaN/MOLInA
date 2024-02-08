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
    QVBoxLayout,
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

# from molina.data_structs import Dataset


COLOR_BACKGROUND_WIDGETS = QColor(250, 250, 250)
RESOURCES_PATH = QDir("molina/resources")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.scale_factor = 1

        # self.data_images = Dataset()
        # self.data_images.model_completed.connect(self.on_model_completed)

        self.setWindowTitle("MOLInA")

        pagelayout = QHBoxLayout()
        splitter =  QSplitter(self)
        toolbar_main = QToolBar()
        
        
        left_widget = QWidget()
        left_widget_layout = QVBoxLayout(left_widget)
        toolbar_zoom = QToolBar()
        
        self.addToolBar(toolbar_main)
        pagelayout.addWidget(splitter)

        self.button_zoom_in = QToolButton()
        self.button_zoom_in.setIcon(QIcon(RESOURCES_PATH.filePath("plus.png")))
        self.button_zoom_in.clicked.connect(self.zoomIn)
        toolbar_zoom.addWidget(self.button_zoom_in)

        self.button_zoom_out = QToolButton() 
        self.button_zoom_out.setIcon(QIcon(RESOURCES_PATH.filePath("minus.png")))
        self.button_zoom_out.clicked.connect(self.zoomOut)
        toolbar_zoom.addWidget(self.button_zoom_out)

        left_widget_layout.addWidget(toolbar_zoom)
        
        self.image_widget = QLabel(splitter)
        left_widget_layout.addWidget(self.image_widget)
        self.image_widget.setMinimumSize(200, 200)
        self.image_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setColor(self.image_widget, COLOR_BACKGROUND_WIDGETS)
        self.image_widget.updateGeometry()
        self.pixmap = None

        splitter.addWidget(left_widget)

        self.right_widget = QTextEdit(splitter)
        self.right_widget.setMinimumSize(200, 200)
        self.setColor(self.right_widget, COLOR_BACKGROUND_WIDGETS)
        self.right_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.right_widget.setReadOnly(True)

        splitter.addWidget(self.right_widget)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        button_open = QPushButton("Open")
        button_open.pressed.connect(self.openImage)
        toolbar_main.addWidget(button_open)

        button_save = QPushButton("Save")
        toolbar_main.addWidget(button_save)

        button_left = QToolButton()
        button_left.setIcon(QIcon(RESOURCES_PATH.filePath("left_button.png")))
        toolbar_main.addWidget(button_left)

        button_right = QToolButton()
        button_right.setIcon(QIcon(RESOURCES_PATH.filePath("right_button.png")))
        toolbar_main.addWidget(button_right)

        toolbar_main.setIconSize(QSize(19, 19))

        button_annotate = QPushButton("Annotate")
        toolbar_main.addWidget(button_annotate)

        button_current_model = QPushButton("Current Model")
        # btn.pressed.connect(self.data_images.run_molscribe)
        toolbar_main.addWidget(button_current_model)

        button_predict = QPushButton("Predict")
        # btn.pressed.connect(self.data_images.run_molscribe)
        toolbar_main.addWidget(button_predict)

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
            self.pixmap = self.loadImage(selected_file)
            if self.pixmap:
                self.image_widget.setPixmap(self.pixmap)
                # self.data_images.setImage(self.pixmap)

    def loadImage(self, file_path: str) -> QPixmap:
        try:
            self.pixmap = QPixmap(file_path)
            if self.pixmap.height() >= self.pixmap.width():
                self.pixmap = self.pixmap.scaledToHeight(self.image_widget.height())
                # if picture is still out of boundaries
                if self.pixmap.width() >= self.image_widget.width():
                    self.pixmap = self.pixmap.scaledToWidth(self.image_widget.width())
            else:
                self.pixmap = self.pixmap.scaledToWidth(self.image_widget.width())
                # if picture is still out of boundaries
                if self.pixmap.height() >= self.image_widget.height():
                    self.pixmap = self.pixmap.scaledToHeight(self.image_widget.height())

        except Exception as e:
            print(f"Error loading image: {e}")
        return self.pixmap

    def setColor(self, widget: QWidget, color: QColor) -> None:
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)

    def onModelCompleted(self, model_result: Dict) -> None:
        if model_result:
            model_result_json = json.dumps(model_result, indent=4, sort_keys=True)
            self.right_widget.setPlainText(model_result_json)
    
    def resizeEvent(self, event) -> None:
        self.setPixmapSize()   
    
    def setPixmapSize(self) -> None: 
        if not self.pixmap:
            return
        size = self.image_widget.size()
        self.image_widget.setPixmap(self.pixmap.scaled(
            self.scale_factor * size,
            Qt.KeepAspectRatio))

    def zoomIn(self) -> None:
      self.scale_factor *= 1.1
      self.resizeImage()
      
    def zoomOut(self) -> None:
      self.scale_factor /= 1.1
      self.resizeImage()

    def resizeImage(self) -> None:
        if not self.pixmap:
            return
        size = self.image_widget.size()
        scaled_pixmap = self.pixmap.scaled(self.scale_factor * size, Qt.KeepAspectRatio)
        self.image_widget.setPixmap(scaled_pixmap)
    