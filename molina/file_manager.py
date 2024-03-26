from PySide6.QtCore import (
    QDir, 
    Signal, 
    QModelIndex,
    QFile, 
    QFileInfo,
)
from PySide6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFileSystemModel,
    QTreeView,
    QAbstractItemView,
)


class FileManager(QWidget):
    """ This class shows directories and images inside ones. 
    One click opens directory.
    Double click on image opens image in CentralWidget.
    It doesn't work when model predicts atoms and bonds for opened image.
    """
    itemSelected = Signal(str)
    def __init__(self, parent: QWidget):
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
        """ Open/close directory """
        path = self.file_model.filePath(index)
        if QFileInfo(path).isDir():
            if self.file_view.isExpanded(index):
                self.file_view.collapse(index)
            else:
                self.file_view.expand(index)

    def onDoubleClicked(self, index: QModelIndex) -> None:
        """ Send image path to MainWindow """
        path = self.sender().model().filePath(index)
        if QFile(path).exists() and not QFileInfo(path).isDir():
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                self.itemSelected.emit(path)
