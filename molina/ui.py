''''''
import json

from typing import List, Dict
import numpy.typing as npt

from PySide6.QtCore import (
    Qt, 
    QSize, 
    QDir, 
    Signal, 
    QModelIndex,
)
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
    QFileSystemModel,
    QTreeView,
    QAbstractItemView,
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
    QIcon,
    QImage,
)

from molina.data_structs import Dataset


COLOR_BACKGROUND_WIDGETS = QColor(250, 250, 250)
RESOURCES_PATH = QDir("molina/resources")


class FileManager(QWidget):
    itemSelected = Signal(str)
    def __init__(self, parent: QWidget) -> None:
        super(FileManager, self).__init__(parent)
        self.file_layout = QVBoxLayout(self)
        self.file_view = QTreeView(self)
        
        self.file_model = QFileSystemModel(self)
        self.file_model.setRootPath(QDir.rootPath())
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        self.file_model.setNameFilters(["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"])
        self.file_model.setNameFilterDisables(False)
        self.file_model.setReadOnly(False)
        
        self.file_view.setModel(self.file_model)
        self.file_view.setColumnWidth(0,200)
        self.file_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_view.setMinimumSize(200, 200)
        self.file_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.file_layout.addWidget(self.file_view)

        #TODO: don't emit signal when it is not

        self.file_view.clicked.connect(self.onClicked)

    def onClicked(self, index: QModelIndex):
        path = self.sender().model().filePath(index)
        self.itemSelected.emit(path)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.scale_factor = 1

        self.data_images = Dataset(images = {})
        self.data_images.current_image_signal.current_image.connect(self.changeImage)
        # self.data_images.model_completed.connect(self.on_model_completed)

        self.setWindowTitle("MOLInA")

        self.page_layout = QHBoxLayout()
        self.splitter =  QSplitter(self)
        self.toolbar_main = QToolBar()
        
        self.left_widget = QWidget()
        self.left_widget_layout = QVBoxLayout(self.left_widget)
        self.toolbar_zoom = QToolBar()
        self.file_widget = FileManager(self)
        self.file_widget.itemSelected.connect(self.data_images.change_current_image)

        self.splitter.addWidget(self.file_widget)

        self.addToolBar(self.toolbar_main)
        self.page_layout.addWidget(self.splitter)

        self.button_zoom_in = QToolButton()
        self.button_zoom_in.setIcon(QIcon(RESOURCES_PATH.filePath("plus.png")))
        self.button_zoom_in.clicked.connect(self.zoomIn)
        self.toolbar_zoom.addWidget(self.button_zoom_in)

        self.button_zoom_out = QToolButton() 
        self.button_zoom_out.setIcon(QIcon(RESOURCES_PATH.filePath("minus.png")))
        self.button_zoom_out.clicked.connect(self.zoomOut)
        self.toolbar_zoom.addWidget(self.button_zoom_out)

        self.left_widget_layout.addWidget(self.toolbar_zoom)
        
        self.image_widget = QLabel(self.splitter)
        self.left_widget_layout.addWidget(self.image_widget)
        self.image_widget.setMinimumSize(200, 200)
        self.image_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setColor(self.image_widget, COLOR_BACKGROUND_WIDGETS)
        self.image_widget.updateGeometry()
        self.pixmap = None

        self.splitter.addWidget(self.left_widget)

        self.right_widget = QTextEdit(self.splitter)
        self.right_widget.setMinimumSize(200, 200)
        self.setColor(self.right_widget, COLOR_BACKGROUND_WIDGETS)
        self.right_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.right_widget.setReadOnly(True)

        self.splitter.addWidget(self.right_widget)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 10)
        self.splitter.setStretchFactor(2, 5)

        self.button_open = QPushButton("Open")
        self.button_open.pressed.connect(self.openImage)
        self.toolbar_main.addWidget(self.button_open)

        self.button_save = QPushButton("Save")
        self.toolbar_main.addWidget(self.button_save)

        # TODO: when click on right mouse button give list of current cache 
        self.button_left = QToolButton()
        self.button_left.setIcon(QIcon(RESOURCES_PATH.filePath("left_button.png")))
        self.toolbar_main.addWidget(self.button_left)

        self.button_right = QToolButton()
        self.button_right.setIcon(QIcon(RESOURCES_PATH.filePath("right_button.png")))
        self.toolbar_main.addWidget(self.button_right)

        self.toolbar_main.setIconSize(QSize(19, 19))

        self.button_annotate = QPushButton("Annotate")
        self.toolbar_main.addWidget(self.button_annotate)

        self.button_current_model = QPushButton("Current Model")
        # self.button_current_model.pressed.connect(self.data_images.run_molscribe)
        self.toolbar_main.addWidget(self.button_current_model)

        self.button_predict = QPushButton("Predict")
        # self.button_predict.pressed.connect(self.data_images.run_molscribe)
        self.toolbar_main.addWidget(self.button_predict)

        self.widget = QWidget()
        self.widget.setLayout(self.page_layout)
        self.setCentralWidget(self.widget)
        self.showMaximized()

    def changeImage(self, image: npt.NDArray) -> None:
        self.scale_factor = 1
        
        if image.ndim == 3:  
            h, w, ch = image.shape
            bytes_per_line = ch * w
            if image.shape[2] == 4:
                q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
            elif image.shape[2] == 3:
                q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        elif image.ndim == 2:  
            h, w = image.shape
            q_image = QImage(image.data, w, h, w, QImage.Format_Grayscale8)
        else:
            raise ValueError("Unexpected array dimension")
        
        if q_image.isNull():
            ValueError("Unsupported array shape for QPixmap conversion")

        self.pixmap = QPixmap.fromImage(q_image)
        if self.pixmap:
            self.fitImage()

    def openImage(self) -> None:
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self, options=options)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.bmp)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.pixmap = QPixmap(selected_file)
            if self.pixmap:
                self.fitImage()
                # self.data_images.setImage(self.pixmap)

    def fitImage(self):
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
        
        self.image_widget.setPixmap(self.pixmap)

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
    