''''''
import json, copy, re

from typing import List, Dict, Any, Union, Tuple
import numpy.typing as npt

from PySide6.QtCore import (
    Qt, 
    QSize,
    QRect, 
    QDir, 
    Signal, 
    QModelIndex,
    QFile, 
    QFileInfo,
    QPoint, 
    QLine,
    QThread,
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
    QStackedLayout,
    QWidget,
    QSplitter,
    QTextEdit,
    QFileSystemModel,
    QTreeView,
    QAbstractItemView,
    QScrollArea,
    QMenu,
    QMessageBox,
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
    QIcon,
    QImage,
    QPainter, 
    QPen,
    QPaintEvent,
    QAction,
)

from molina.data_structs import Dataset, Worker


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

        self.file_view.setEditTriggers(QTreeView.NoEditTriggers)

        self.file_view.clicked.connect(self.onClicked)
        self.file_view.doubleClicked.connect(self.onDoubleClicked)
    
    def onClicked(self, index: QModelIndex) -> None:
        path = self.file_model.filePath(index)
        if QFileInfo(path).isDir():
            if self.file_view.isExpanded(index):
                self.file_view.collapse(index)
            else:
                self.file_view.expand(index)

    def onDoubleClicked(self, index: QModelIndex) -> None:
        path = self.sender().model().filePath(index)
        if QFile(path).exists() and not QFileInfo(path).isDir():
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                self.itemSelected.emit(path)


class FileAction:
    def __init__(self):
        self.recent_images = []
    
    def addRecentImage(self, image_path):
        if image_path in self.recent_images:
            self.recent_images.remove(image_path)

        self.recent_images.insert(0, image_path)

    def getRecentImages(self):
        return self.recent_images


class DrawingAction:
    def __init__(self, widget):
        self.widget = widget
        self.action_history = []
        self.max_actions = 15

    def addAction(self, action, action_type):
        if len(self.action_history) >= self.max_actions:
            self.action_history.pop(0)
        self.action_history.append({'type': action_type, 'data': action})

    def undo(self):
        if self.action_history:
            last_action = self.action_history.pop()
            action_type = last_action['type']
            data = last_action['data']

            if action_type == 'add_point':
                # Undo add_point by removing the last point
                self.widget.deletePoint(False)
            elif action_type == 'delete_point':
                # Undo delete_point by re-adding the point
                self.widget.addPoint(data, False)
            elif action_type == 'add_line':
                # Undo add_line by removing the last line
                self.widget.deleteLine(-1, False)
            elif action_type == 'delete_line':
                # Undo delete_line by re-adding the line
                self.widget.addLine(data, False)
            elif action_type == 'clear_all':
                self.widget.updateCoordinates(data, True)
            elif action_type == 'delete_point_and_lines': 
                self.widget.undoDeletePointAndLines(data)


class DrawingWidget(QWidget):
    coordinateUpdate = Signal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines = []
        self._points = []
        self.temp_line = None
        self._atom_type = None
        self._bond_type = None
        self._zoom_factor = 1.0
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False
        self.action_manager = DrawingAction(self)
        self.setFocusPolicy(Qt.StrongFocus)
        self._original_coordinate = {"bonds": [],
                                     "lines": [],
                                     "atoms": []}        

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        pen = QPen(Qt.red, 5)
        painter.setPen(pen)

        for line in self._lines:
            painter.drawLine(line)

        for point in self._points:
            painter.drawPoint(point)

        if self.temp_line:
            painter.drawLine(self.temp_line)
        
        # painter.setBrush(QColor(150, 150, 100, 100))
        # painter.drawRect(self.rect())

    def findAtoms(self, line: QLine, threshold: int = 20) -> Dict:
        #TODO: threshold as % of size image
        close_point = {}
        for i, atom in enumerate(self._original_coordinate["atoms"]):
            point = QPoint(atom["x"], atom["y"])
            distance_to_start = (line.p1() - point).manhattanLength()
            distance_to_end = (line.p2() - point).manhattanLength()
            if distance_to_start <= threshold:
                close_point[i] = line.p1()
            elif distance_to_end <= threshold:
                close_point[i] = line.p2()
        
        if len(close_point) == 2: 
            return close_point
        else:
            return

    def addLine(self, line: QLine, flag_undo: bool = True) -> None:
        not_scaled_line = QLine(line.x1() / self._zoom_factor, 
                                line.y1() / self._zoom_factor,
                                line.x2() / self._zoom_factor,
                                line.y2() / self._zoom_factor)
        
        atoms = self.findAtoms(not_scaled_line)
        if atoms:
            self._lines.append(line)
            if flag_undo:
                self.action_manager.addAction(line, "add_line")
            
            self._original_coordinate["lines"].append(not_scaled_line)
            self._original_coordinate["bonds"].append({"bond_type": self._bond_type,
                                                       "endpoint_atoms": list(atoms.keys())})
            
            self.coordinateUpdate.emit(self._original_coordinate)
        else: 
            self.temp_line = None

        self.update()
    
    def deleteLine(self, index=-1, flag_undo: bool = True) -> None:
        if index != -1:
            self._original_coordinate["bonds"].pop(index)
            self._original_coordinate["lines"].pop(index)
            last_line = self._lines.pop(index)
        else:
            self._original_coordinate["bonds"].pop()
            self._original_coordinate["lines"].pop()
            last_line = self._lines.pop()
        
        if flag_undo:
            self.action_manager.addAction(last_line, "delete_line")

        self.coordinateUpdate.emit(self._original_coordinate)
        self.update()

    def addPoint(self, point: QPoint, flag_undo: bool = True) -> None:
        self._original_coordinate["atoms"].append({
            "atom_symbol": self._atom_type,
            "x": point.x() / self._zoom_factor, 
            "y": point.y() / self._zoom_factor})
        
        if flag_undo:
            self.action_manager.addAction(point, "add_point")
        self._points.append(point)

        self.coordinateUpdate.emit(self._original_coordinate)
        self.update()
    
    def deletePoint(self, flag_undo: bool = True) -> None:
        self._original_coordinate["atoms"].pop()
        last_point = self._points.pop()
        
        if flag_undo:
            self.action_manager.addAction(last_point, "delete_point")
        
        self.coordinateUpdate.emit(self._original_coordinate)
        self.update()

    def recombineDeletedBonds(self, index: int) -> None:
        i = len(self._original_coordinate["bonds"]) - 1
        
        while i >= 0:
            if index in self._original_coordinate["bonds"][i]["endpoint_atoms"]:
                del self._original_coordinate["bonds"][i]
                del self._original_coordinate["lines"][i]
                del self._lines[i]
            else:
                self._original_coordinate["bonds"][i]["endpoint_atoms"] = [
                    atom - 1 if atom > index else atom for atom in self._original_coordinate["bonds"][i]["endpoint_atoms"]]
            
            i -= 1
                
    def deletePointAndLine(self, index: int) -> None:
        self.action_manager.addAction(copy.deepcopy(self._original_coordinate), "delete_point_and_lines")
        self._original_coordinate["atoms"].pop(index)
        self._points.pop(index)

        self.recombineDeletedBonds(index)
        
        self.coordinateUpdate.emit(self._original_coordinate)
        self.update()
    
    def undoDeletePointAndLines(self, data: Tuple) -> None:
        self._original_coordinate = data.copy()

        self.coordinateUpdate.emit(self._original_coordinate)
        self.updateDrawScale()
        self.update()

    def lineCenter(self, line: QLine) -> QPoint:
        x_center = (line.x1() + line.x2()) / 2
        y_center = (line.y1() + line.y2()) / 2
        return QPoint(x_center, y_center)
    
    def partLine(self, end_line: QPoint, center: QPoint, part: float = 0.66) -> QPoint:
        x = center.x() + part * (end_line.x() - center.x())
        y = center.y() + part * (end_line.y() - center.y())
        return QPoint(x, y)

    def isPointOnLineSegment(self, start: QPoint, end: QPoint, point: QPoint) -> bool:
        line_length = (start - end).manhattanLength()
        d1 = (point - start).manhattanLength()
        d2 = (point - end).manhattanLength()

        return abs(d1 + d2 - line_length) < 1e-5 

    def findClosestObject(self, position, threshold: int = 20) -> None:
        #TODO: threshold as % of size image
        for i in range(len(self._points)):
            distance = (position - self._points[i]).manhattanLength()
            if distance <= threshold:
                 self.deletePointAndLine(i)
                 return
        
        for i in range(len(self._lines)):
            center = self.lineCenter(self._lines[i])
            part_P1 = self.partLine(self._lines[i].p1(), center)
            part_P2 = self.partLine(self._lines[i].p2(), center)
            if self.isPointOnLineSegment(part_P1, part_P2, position):
                self.deleteLine(i)
                return

    def setDrawingMode(self, enabled: bool, type: str, info: str) -> None:
        if type == "point":
            self._drawing_point_enabled = enabled
            self._drawing_line_enabled = False
            self._atom_type = info
        elif type == "line":
            self._drawing_line_enabled = enabled
            self._drawing_point_enabled = False
            self._bond_type = info
        else:
            raise TypeError()
    
    def updateDrawScale(self) -> None:
        if len(self._lines) != len(self._original_coordinate["lines"]):
            self._lines = copy.deepcopy(self._original_coordinate["lines"])
        for i in range(len(self._original_coordinate["lines"])):
            line = self._original_coordinate["lines"][i]
            self._lines[i].setP1(QPoint(
                line.p1().x() * self._zoom_factor,
                line.p1().y() * self._zoom_factor))
            self._lines[i].setP2(QPoint(
                line.p2().x() * self._zoom_factor,
                line.p2().y() * self._zoom_factor))
            
        if len(self._points) != len(self._original_coordinate["atoms"]):
            self._points = [QPoint() for i in range(len(self._original_coordinate["atoms"]))]
        for i in range(len(self._original_coordinate["atoms"])):
            point = self._original_coordinate["atoms"][i]
            self._points[i].setX(point["x"] * self._zoom_factor)
            self._points[i].setY(point["y"] * self._zoom_factor)
    
    def setZoomFactor(self, factor: float) -> None:
        self._zoom_factor = factor
        self.update()
    
    def getOriginalCoordinate(self) -> Dict:
        return self._original_coordinate
    
    def cleanDrawingWidget(self) -> None:
        self._lines = []
        self._points = []
        self.temp_line = None
        self._zoom_factor = 1.0
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False
        self.action_manager = DrawingAction(self)
        self._original_coordinate = {"bonds": [],
                                     "lines": [],
                                     "atoms": []}

    def mousePressEvent(self, event: QPaintEvent) -> None:
        if event.button() == Qt.LeftButton:
            if self._drawing_point_enabled:
                self.addPoint(event.pos())
            elif self._drawing_line_enabled:
                self.temp_line = QLine(event.pos(), event.pos())
        elif event.button() == Qt.RightButton:
            self.findClosestObject(event.pos())
    
    def mouseMoveEvent(self, event) -> None:
        if self._drawing_line_enabled:
            self.temp_line.setP2(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._drawing_line_enabled:
            self.addLine(self.temp_line)
            self.temp_line = None

    def updateCoordinates(self, coordinates: Dict, flag_undo: bool = False) -> None:
        self._original_coordinate = coordinates.copy()
        self._original_coordinate["lines"] = []
        self._lines = []
        self._points = []
        atoms = self._original_coordinate["atoms"]
        for bond in self._original_coordinate["bonds"]:
            self._original_coordinate["lines"].append(
                QLine(
                    QPoint(atoms[bond["endpoint_atoms"][0]]["x"],
                           atoms[bond["endpoint_atoms"][0]]["y"]),
                    QPoint(atoms[bond["endpoint_atoms"][1]]["x"],
                           atoms[bond["endpoint_atoms"][1]]["y"])
                    )
            )
        if flag_undo:
            self.coordinateUpdate.emit(self._original_coordinate)
        
        self.updateDrawScale()
        self.update()
    
    def clearAll(self) -> None:
        self.action_manager.addAction(copy.deepcopy(self._original_coordinate), "delete_point_and_lines")
        if len(self._original_coordinate["atoms"]) != 0: 
            self.action_manager.addAction(self._original_coordinate, "clear_all")
            self._lines = []
            self._points = []
            self.temp_line = None
            self._original_coordinate = {"bonds": [],
                                        "lines": [],
                                        "atoms": []}
            self.coordinateUpdate.emit(self._original_coordinate)
            self.update()
    
    def keyPressEvent(self, event: QPaintEvent) -> None:
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            self.action_manager.undo()

        elif event.key() == Qt.Key_C:
            self.setDrawingMode(not self._drawing_point_enabled, "point", "C")
        
        elif event.key() == Qt.Key_1:
            self.setDrawingMode(not self._drawing_line_enabled, "line", "single")


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale_factor = 1
        self._pixmap = QPixmap()

        self.central_widget_layout = QVBoxLayout()
        self.setLayout(self.central_widget_layout)

        self.toolbar_zoom = QToolBar()

        self.button_zoom_in = QToolButton()
        self.button_zoom_in.setIcon(QIcon(RESOURCES_PATH.filePath("plus.png")))
        self.button_zoom_in.clicked.connect(self.zoomIn)
        self.toolbar_zoom.addWidget(self.button_zoom_in)

        self.button_zoom_out = QToolButton() 
        self.button_zoom_out.setIcon(QIcon(RESOURCES_PATH.filePath("minus.png")))
        self.button_zoom_out.clicked.connect(self.zoomOut)
        self.toolbar_zoom.addWidget(self.button_zoom_out)

        self.central_widget_layout.addWidget(self.toolbar_zoom)

        self.image_layout = QStackedLayout()
        self.image_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_container = QWidget()
        self.image_container.setLayout(self.image_layout)

        self.image_widget = QLabel()
        self.image_widget.setAlignment(Qt.AlignCenter)
        self.image_widget.setMinimumSize(200, 200)

        self.container_widget = QWidget()
        self.container_layout = QHBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)      
        
        self.drawing_widget = DrawingWidget()
        self.drawing_widget.setFocus()
        self.container_layout.addWidget(self.drawing_widget, alignment=Qt.AlignCenter)

        self.image_layout.addWidget(self.container_widget)
        self.image_layout.addWidget(self.image_widget)
        # self.setColor(self.drawing_widget, QColor(100, 250, 150, 100))
        self.setColor(self.image_widget, COLOR_BACKGROUND_WIDGETS)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.image_container)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.central_widget_layout.addWidget(self.scrollArea)
    
    def hasPixmap(self) -> bool:
        if self._pixmap.isNull():
            return False
        else:
            return True

    def setScaleFactor(self, factor: float) -> None:
        self._scale_factor = factor
        self.drawing_widget.setZoomFactor(self._scale_factor)

    def zoomIn(self) -> None:
      self._scale_factor *= 1.1
      self.resizeImage()
      
    def zoomOut(self) -> None:
      self._scale_factor /= 1.1
      self.resizeImage()
    
    def resizeImage(self) -> None:
        if not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(self._scale_factor * self._pixmap.size(), Qt.KeepAspectRatio)
            
            self.image_widget.setPixmap(scaled_pixmap)
            self.image_widget.setMinimumSize(scaled_pixmap.size())
            
            self.drawing_widget.setZoomFactor(self._scale_factor)
            self.drawing_widget.setFixedSize(scaled_pixmap.size())
            self.drawing_widget.updateDrawScale()
    
    def setPixmapSize(self) -> None: 
        if not self._pixmap.isNull():
            self.image_widget.setPixmap(self._pixmap.scaled(
                self._scale_factor * self._pixmap.size(),
                Qt.KeepAspectRatio))
        
    def fitImage(self) -> QPixmap:
        if self._pixmap.height() >= self._pixmap.width():
            scaled_pixmap = self._pixmap.scaledToHeight(self.image_widget.height())
            # if picture is still out of boundaries
            if scaled_pixmap.width() >= self.image_widget.width():
                scaled_pixmap = scaled_pixmap.scaledToWidth(self.image_widget.width())
        else:
            scaled_pixmap = self._pixmap.scaledToWidth(self.image_widget.width())
            # if picture is still out of boundaries
            if scaled_pixmap.height() >= self.image_widget.height():
                scaled_pixmap = scaled_pixmap.scaledToHeight(self.image_widget.height())
        
        self.image_widget.setPixmap(scaled_pixmap)
        return scaled_pixmap
    
    def setCentralPixmap(self, image: QPixmap) -> None:
        self._pixmap = image
        if not self._pixmap.isNull():
            original_size = self._pixmap.height() + self._pixmap.width()
            scaled_pixmap = self.fitImage()

            self.drawing_widget.setFixedSize(scaled_pixmap.size())
            self.drawing_widget.cleanDrawingWidget()
            self.setScaleFactor((scaled_pixmap.height() + scaled_pixmap.width()) / original_size)

    def setColor(self, widget: QWidget, color: QColor) -> None:
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)
    

class MainWindow(QMainWindow):
    imagePathSelected = Signal(str)
    def __init__(self) -> None:
        super(MainWindow, self).__init__()

        self.setWindowTitle("MOLInA")

        self.data_images = Dataset(images = {})

        self.data_images.current_image_signal.current_image.connect(self.changeImage)
        self.data_images.current_image_signal.current_annotation.connect(self.changeAnnotation)

        self.page_layout = QHBoxLayout()
        self.splitter =  QSplitter(self)
        self.toolbar_main = QToolBar()
        self.fileAction = FileAction()
        
        self.central_widget = CentralWidget()
        self.setColor(self.central_widget, COLOR_BACKGROUND_WIDGETS)
        self.central_widget.drawing_widget.coordinateUpdate.connect(self.addPointToDataset)
        self.data_images.current_image_signal.data_changed.connect(
            self.central_widget.drawing_widget.updateCoordinates)

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

            self.fileAction.addRecentImage(selected_file)
        
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

        self.text_widget.setText(annotation_pretty)

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
            model_result_json = json.dumps(model_result, indent=4, sort_keys=True)
            self.text_widget.setText(model_result_json)
            self.data_images.draw_annotation()
        
        self.file_widget.setEnabled(True)
        self.toolbar_main.setEnabled(True)
    
    def resizeEvent(self, event: QPaintEvent) -> None:
        self.central_widget.setPixmapSize()   

    def addPointToDataset(self, coordinate: Dict) -> None:
        self.data_images.add_coordinates(coordinate)

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
        