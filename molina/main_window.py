from typing import List, Dict, Any
from collections import defaultdict

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
    QSizePolicy,
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
    QRegion,
)

from molina.data_structs import Dataset, Worker
from molina.central_widget import CentralWidget
from molina.action_managers import FileActionManager
from molina.file_manager import FileManager
from molina.help_widget import HelpWindow
from molina.hotkeys import Hotkeys
from molina.styles import TOOLBAR_STYLE, TEXT_STYLE


RESOURCES_PATH = QDir("molina/resources")
COLOR_BACKGROUND_WIDGETS = QColor(250, 250, 250)


class MainWindow(QMainWindow):
    """Main Window class contains three parts: File Manager, Drawing Widget and Text Representation.
    It has toolbar with open, save, left, right, recent, current model, clean all and predict buttons.
    Also it will have Help button for describing hot keys abilities.
    """

    imagePathSelected = Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("MOLInA")
        self.setWindowIcon(QIcon(RESOURCES_PATH.filePath("icon.png")))

        self.page_layout = QHBoxLayout()
        self.splitter = QSplitter(self)
        self.toolbar_main = QToolBar()
        self.fileAction = FileActionManager()

        self.data_images = Dataset({})
        self.data_images._current_image_signal.current_image.connect(self.changeImage)
        self.data_images._current_image_signal.current_annotation.connect(
            self.changeAnnotation
        )

        self.central_widget = CentralWidget()

        self.file_widget = FileManager(self)
        self.file_widget.itemSelected.connect(self.changeCurrentImage)

        self.addToolBar(self.toolbar_main)
        self.page_layout.addWidget(self.splitter)

        self.text_widget = QTextEdit(self.splitter)
        self.text_widget.setStyleSheet(TEXT_STYLE)
        self.text_widget.setMinimumSize(200, 200)
        self.text_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_widget.setReadOnly(True)

        self.splitter.addWidget(self.file_widget)
        self.splitter.addWidget(self.central_widget)
        self.splitter.addWidget(self.text_widget)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 10)
        self.splitter.setStretchFactor(2, 5)

        self.button_open = QToolButton()
        self.button_open.setToolTip("Open")
        self.button_open.setIcon(QIcon(RESOURCES_PATH.filePath("open.png")))
        self.button_open.pressed.connect(self.openImage)

        self.button_save = QToolButton()
        self.button_save.setToolTip("Save")
        self.button_save.setIcon(QIcon(RESOURCES_PATH.filePath("save.png")))
        self.button_save.pressed.connect(self.data_images.saveAnnotation)

        self.button_clean = QToolButton()
        self.button_clean.setToolTip("Clean All")
        self.button_clean.setIcon(QIcon(RESOURCES_PATH.filePath("eraser.png")))
        self.button_clean.pressed.connect(self.central_widget.drawing_widget.clearAll)

        self.model_menu = QMenu()
        self.button_current_model = QToolButton()
        self.button_current_model.setToolTip("Choose model")
        self.button_current_model.setIcon(QIcon(RESOURCES_PATH.filePath("choose.png")))
        self.button_current_model.setMenu(self.model_menu)

        self.model_menu_items = ["MolScribe", "another"]
        self.setModelMenu()
        self.button_current_model.pressed.connect(self.onModelButtonClicked)

        self.button_predict = QToolButton()
        self.button_predict.setToolTip("Predict")
        self.button_predict.setIcon(QIcon(RESOURCES_PATH.filePath("predict.png")))
        self.button_predict.pressed.connect(self.startPrediction)

        # Add a spacer widget between buttons
        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.button_left = QToolButton()
        self.button_left.setToolTip("Back")
        self.button_left.setIcon(QIcon(RESOURCES_PATH.filePath("left.png")))
        self.button_left.pressed.connect(self.leftImage)

        self.recent_menu = QMenu()
        self.button_recent = QToolButton()
        self.button_recent.setToolTip("Recent")
        self.button_recent.setIcon(QIcon(RESOURCES_PATH.filePath("recent.png")))
        self.button_recent.setMenu(self.recent_menu)
        self.button_recent.pressed.connect(self.showRecent)

        self.help_button = QToolButton()
        self.help_button.setToolTip("Help")
        self.help_button.setIcon(QIcon(RESOURCES_PATH.filePath("help.png")))
        self.help_button.clicked.connect(self.showHelpWindow)

        self.hotkeys = Hotkeys()
        self.thread = None

        self.toolbar_main.addWidget(self.button_open)
        self.toolbar_main.addWidget(self.button_save)
        self.toolbar_main.addWidget(self.button_clean)
        self.toolbar_main.addWidget(self.button_current_model)
        self.toolbar_main.addWidget(self.button_predict)
        self.toolbar_main.addWidget(self.spacer)
        self.toolbar_main.addWidget(self.button_left)
        self.toolbar_main.addWidget(self.button_recent)
        self.toolbar_main.addWidget(self.help_button)

        self.toolbar_main.setIconSize(QSize(25, 25))
        self.toolbar_main.setStyleSheet(TOOLBAR_STYLE)

        self.imagePathSelected.connect(self.data_images.changeCurrentImage)

        self.widget = QWidget()
        self.widget.setLayout(self.page_layout)
        self.setCentralWidget(self.widget)

        self.showMaximized()

    def showHelpWindow(self):
        help_window = HelpWindow(self.hotkeys)
        help_window.exec_()

    def changeImage(self, image: npt.NDArray) -> None:
        """Convert numpy array to QPixmap"""
        self.central_widget.setScaleFactor(1.0)

        if image.ndim == 3:
            h, w, ch = image.shape
            bytes_per_line = ch * w
            if image.shape[2] == 4:
                q_image = QImage(
                    image.data, w, h, bytes_per_line, QImage.Format_RGBA8888
                )
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
        """Open image with file dialog window"""
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self, options=options)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.bmp)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.changeCurrentImage(selected_file)

    def changeCurrentImage(self, path: str) -> None:
        """Add image to file action and change current image in Dataset"""
        self.fileAction.addRecentImage(path)
        self.imagePathSelected.emit(path)

    def changeAnnotation(self, annotation: Dict[str, List[Any]]) -> None:
        """Make text more pretty look and set it into text area"""
        annotation_pretty = ""
        tab = "        "
        for key in annotation.keys():
            annotation_pretty = annotation_pretty + str(key) + ":\n"
            for item in annotation[key]:
                for internal_key, internal_value in item.items():
                    if (
                        internal_key == "confidence"
                        and internal_value == "not_modeling"
                    ):
                        continue
                    annotation_pretty = (
                        annotation_pretty
                        + tab
                        + str(internal_key)
                        + ": "
                        + str(internal_value)
                        + "\n"
                    )
                annotation_pretty += "\n"

        scrollbar = self.text_widget.verticalScrollBar()
        current_pos = scrollbar.value()

        self.text_widget.setText(annotation_pretty)

        scrollbar.setValue(current_pos)

    def startPrediction(self) -> None:
        """Start new thread to parallel prediction
        Block FileManager and toolbar"""
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
        self.thread.finished.connect(self.onThreadFinished)
        self.worker.result.connect(self.onModelCompleted)

        self.thread.start()

    def onThreadFinished(self) -> None:
        """Clean thread and worker after prediction finishing"""
        self.worker.deleteLater()
        self.thread = None

    def closeEvent(self, event) -> None:
        """Finish thread if application was closed"""
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()

        event.accept()

    def onModelCompleted(self, model_result: Dict) -> None:
        """Unblock FileManager and toolbar and change annotation text"""
        if model_result:
            self.changeAnnotation(model_result)

        self.file_widget.setEnabled(True)
        self.toolbar_main.setEnabled(True)

    def resizeEvent(self, event: QPaintEvent) -> None:
        """Save central widget size as image size while
        main window or central part of main window is changed
        """
        super().resizeEvent(event)
        self.central_widget.setPixmapSize()

    def setColor(self, widget: QWidget, color: QColor) -> None:
        """Fill widget background by one color"""
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)

    def showRecent(self) -> None:
        """Show recent opened images"""
        self.recent_menu.clear()
        recent_images = self.fileAction.getRecentImages()

        # Create a count of filenames to check for duplicates
        filename_counts = defaultdict(int)
        for path in recent_images:
            filename_counts[path.name] += 1

        for file_path in recent_images:
            display_name = file_path.name
            if filename_counts[file_path.name] > 1:
                display_name = f"{file_path.parent.name}/{file_path.name}"

            action = self.recent_menu.addAction(display_name)
            action.triggered[bool].connect(
                lambda checked, path=str(file_path): self.changeCurrentImage(path)
            )

        menu_pos = self.button_recent.parentWidget().mapToGlobal(
            self.button_recent.geometry().bottomLeft()
        )
        self.recent_menu.popup(menu_pos)

    def leftImage(self) -> None:
        """Shift in recently opened image list"""
        if len(self.fileAction.getRecentImages()) != 0:
            left_image_path = self.fileAction.getRecentImages()[-1]
            self.changeCurrentImage(left_image_path)

    def setModel(self, model_name: str) -> None:
        """Change current model according to user click"""
        self.data_images.setCurrentModel(model_name)

        for action in self.model_menu.actions():
            action.setChecked(action.text() == model_name)

    def setModelMenu(self) -> None:
        """Fill menu of models by existing models"""
        for item in self.model_menu_items:
            action = QAction(item, self)
            action.setCheckable(True)
            action.triggered[bool].connect(lambda _, name=item: self.setModel(name))
            self.model_menu.addAction(action)

        self.model_menu.actions()[0].setChecked(True)

    def onModelButtonClicked(self):
        """Show menu with models"""
        menu_pos = self.button_current_model.parentWidget().mapToGlobal(
            self.button_current_model.geometry().bottomLeft()
        )
        self.model_menu.popup(menu_pos)
