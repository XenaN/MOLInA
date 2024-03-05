from PySide6.QtCore import Qt, QDir
from PySide6.QtWidgets import (
    QToolButton,
    QLabel,
    QToolBar,
    QHBoxLayout,
    QVBoxLayout,
    QStackedLayout,
    QWidget,
    QScrollArea,
)
from PySide6.QtGui import (
    QPalette, 
    QColor, 
    QPixmap,
    QIcon,
)

from molina.drawing_widget import DrawingWidget


RESOURCES_PATH = QDir("molina/resources")
COLOR_BACKGROUND_WIDGETS = QColor(250, 250, 250)


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
            self.drawing_widget.setThresholds(self._pixmap.size())
            self.setScaleFactor((scaled_pixmap.height() + scaled_pixmap.width()) / original_size)

    def setColor(self, widget: QWidget, color: QColor) -> None:
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)
    

