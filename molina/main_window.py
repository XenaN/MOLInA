from typing import List, Dict, Any, Union, Tuple
import numpy.typing as npt

from PySide6.QtCore import (
    QSize,
    QDir, 
    Signal, 
    QThread,
)
from PySide6.QtWidgets import (
    QToolButton,
    QToolBar,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QWidget,
    QSplitter,
    QTextEdit,
    QMenu,
    QMessageBox,
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
    QIcon,
    QImage,
    QPaintEvent,
    QAction,
)

from molina.data_structs import Dataset, Worker
from molina.central_widget import CentralWidget
from molina.drawing_widget import TypedLine
from molina.action_managers import FileActionManager
from molina.file_manager import FileManager
from molina.data_manager import DataManager


RESOURCES_PATH = QDir("molina/resources")
COLOR_BACKGROUND_WIDGETS = QColor(250, 250, 250)


class MainWindow(QMainWindow):
    imagePathSelected = Signal(str)
    def __init__(self) -> None:
        super(MainWindow, self).__init__()

        self.setWindowTitle("MOLInA")

        self.data_images = Dataset(_images = {})

        self.data_images._current_image_signal.current_image.connect(self.changeImage)
        self.data_images._current_image_signal.current_annotation.connect(self.changeAnnotation)

        self.page_layout = QHBoxLayout()
        self.splitter =  QSplitter(self)
        self.toolbar_main = QToolBar()
        self.fileAction = FileActionManager()
        
        self.central_widget = CentralWidget()
        self.setColor(self.central_widget, COLOR_BACKGROUND_WIDGETS)
        self.central_widget.drawing_widget.pointUpdate.connect(self.addPointToDataManager)
        self.central_widget.drawing_widget.lineUpdate.connect(self.addLineToDataManager)
        
        # self.data_manager = DataManager()
        # self.data_manager.dataUpdateToDataset.connect(self.data_images.update_coordinates)
        # self.data_manager.newDataToDrawingWidget.connect(self.central_widget.drawing_widget.updateDrawScale)
        # self.data_manager.pointUpdate.connect(self.central_widget.drawing_widget.updatePoint)
        # self.data_manager.lineUpdate.connect(self.central_widget.drawing_widget.updateLine)

        self.file_widget = FileManager(self)
        self.file_widget.itemSelected.connect(self.changeCurrentImage)

        self.splitter.addWidget(self.file_widget)

        self.addToolBar(self.toolbar_main)
        self.page_layout.addWidget(self.splitter)

        self.splitter.addWidget(self.central_widget)

        self.text_widget = QTextEdit(self.splitter)
        self.text_widget.setMinimumSize(200, 200)
        self.setColor(self.text_widget, COLOR_BACKGROUND_WIDGETS)
        self.text_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_widget.setReadOnly(True)

        self.splitter.addWidget(self.text_widget)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 10)
        self.splitter.setStretchFactor(2, 5)

        self.button_open = QPushButton("Open")
        self.button_open.pressed.connect(self.openImage)
        self.toolbar_main.addWidget(self.button_open)

        self.button_save = QPushButton("Save")
        self.button_save.pressed.connect(self.data_images.save_annotation)
        self.toolbar_main.addWidget(self.button_save)

        # TODO: when click on right mouse button give list of current cache 
        self.button_left = QToolButton()
        self.button_left.setIcon(QIcon(RESOURCES_PATH.filePath("left_button.png")))
        self.toolbar_main.addWidget(self.button_left)

        self.button_right = QToolButton()
        self.button_right.setIcon(QIcon(RESOURCES_PATH.filePath("right_button.png")))
        self.toolbar_main.addWidget(self.button_right)

        self.recent_menu = QMenu()
        self.button_recent = QToolButton()
        self.button_recent.setIcon(QIcon(RESOURCES_PATH.filePath("recent.png")))
        self.button_recent.setMenu(self.recent_menu)
        self.button_recent.pressed.connect(self.showRecent)
        self.toolbar_main.addWidget(self.button_recent)

        self.button_clean = QToolButton()
        self.button_clean.setIcon(QIcon(RESOURCES_PATH.filePath("eraser.png")))
        self.button_clean.pressed.connect(self.central_widget.drawing_widget.clearAll)
        self.toolbar_main.addWidget(self.button_clean)

        self.model_menu = QMenu()
        self.button_current_model = QPushButton("Current Model")
        self.button_current_model.setMenu(self.model_menu)
        self.toolbar_main.addWidget(self.button_current_model)

        self.model_menu_items = ["MolScribe", "another"]
        self.setModelMenu()

        self.button_predict = QPushButton("Predict")
        self.button_predict.pressed.connect(self.startPrediction)
        self.toolbar_main.addWidget(self.button_predict)
        
        self.toolbar_main.setIconSize(QSize(19, 19))

        self.imagePathSelected.connect(self.data_images.change_current_image)
          
        self.widget = QWidget()
        self.widget.setLayout(self.page_layout)
        self.setCentralWidget(self.widget)
        self.showMaximized()

    def changeImage(self, image: npt.NDArray) -> None:
        self.central_widget.setScaleFactor(1.0)
        
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

        self.central_widget.setCentralPixmap(QPixmap.fromImage(q_image))

    def openImage(self) -> None:
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self, options=options)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.bmp)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.changeCurrentImage(selected_file)
        
    def changeCurrentImage(self, path: str) -> None:
        self.fileAction.addRecentImage(path)
        self.imagePathSelected.emit(path)
    
    def changeAnnotation(self, annotation: Dict[str, List[Any]]) -> None:
        # annotation_json = json.dumps(annotation, indent=4, sort_keys=False)
        annotation_pretty = ''
        tab = '        '
        for key in annotation.keys():
            annotation_pretty = annotation_pretty + str(key) + ':\n' 
            for i, item in enumerate(annotation[key]):
                if key == "atoms":
                    annotation_pretty = annotation_pretty + tab + "atom_number: " + str(i) + '\n'
                for internal_key, internal_value in item.items(): 
                    annotation_pretty = annotation_pretty + tab + str(internal_key) + ': ' + str(internal_value) + '\n'
                annotation_pretty += '\n'
        
        scrollbar = self.text_widget.verticalScrollBar()
        current_pos = scrollbar.value()

        self.text_widget.setText(annotation_pretty)

        scrollbar.setValue(current_pos)

    def startPrediction(self) -> None:
        if not self.central_widget.hasPixmap():
            QMessageBox.warning(self, "Prediction Error", "No image to predict.")
            return
        
        self.file_widget.setEnabled(False)
        self.toolbar_main.setEnabled(False)
        self.thread = QThread()
        self.worker = Worker(self.data_images)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.onModelCompleted)

        self.thread.start()

    def onModelCompleted(self, model_result: Dict) -> None:
        if model_result:
            self.changeAnnotation(model_result)
            self.data_images.draw_annotation()
        
        self.file_widget.setEnabled(True)
        self.toolbar_main.setEnabled(True)
    
    def resizeEvent(self, event: QPaintEvent) -> None:
        self.central_widget.setPixmapSize()   

    def addPointToDataManager(self, point: Dict, index: int) -> None:
        self.data_manager.addAtom(point)
    
    def addLineToDataManager(self, line: TypedLine, endpoint: List, index: int) -> None:
        self.data_manager.addBond(line, endpoint)

    def setColor(self, widget: QWidget, color: QColor) -> None:
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)
    
    def showRecent(self) -> None:
        self.recent_menu.clear()
        for file_path in self.fileAction.getRecentImages():
            action = self.recent_menu.addAction(file_path)
            action.triggered[bool].connect(lambda checked, path=file_path: self.changeCurrentImage(path))
        
        menu_pos = self.button_recent.parentWidget().mapToGlobal(self.button_recent.geometry().bottomLeft())
        self.recent_menu.popup(menu_pos)
    
    def setModelMenu(self) -> None:
        for item in self.model_menu_items:
            action = QAction(item, self)
            action.setCheckable(True)
            action.triggered[bool].connect(lambda _, name=item: self.set_model(name))
            self.model_menu.addAction(action)

        self.model_menu.actions()[0].setChecked(True)
    
    def updateCheckedModel(self, selected_model_name: str) -> None:
        for action in self.model_menu.actions():
            action.setChecked(action.text() == selected_model_name)

    def set_model(self, model_name: str) -> None:
        self.data_images.set_current_model(model_name)
        self.updateCheckedModel(model_name)
        