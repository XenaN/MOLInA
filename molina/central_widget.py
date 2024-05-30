import sys, os

from PySide6.QtCore import Qt, QDir, QEvent
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
from molina.styles import FOCUSED, UNFOCUSED, COLOR_BACKGROUND_WIDGETS


class ResourcePathMixin:
    def setup_resource_path(self) -> None:
        """Sets up the base path for resources depending on the execution mode"""
        if getattr(sys, "frozen", False):
            base_path = os.path.join(sys._MEIPASS, "resources")
        else:
            base_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "resources")
            )

        # Create a method that composes full paths to resources
        self.resource_path = lambda filename: os.path.join(base_path, filename)

    def get_icon(self, icon_name: str) -> QIcon:
        """Utility method to get an icon with the given name."""
        return QIcon(self.resource_path(icon_name))


class CentralWidget(QWidget, ResourcePathMixin):
    """
    Widget between File Manager and Annotation text.
    It contains zoom buttons, an image representation and a drawing area.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_resource_path()
        self.setObjectName("CentralWidget")
        self.updateStyleSheet(focused=False)

        self.setAttribute(Qt.WA_StyledBackground, True)

        # Relation between image size, and widget size, then it changes depending on zooming
        self._scale_factor = 1
        self._pixmap = QPixmap()

        self.central_widget_layout = QVBoxLayout()
        self.setLayout(self.central_widget_layout)

        # Area for zoom buttons
        self.toolbar_zoom = QToolBar()

        self.button_zoom_in = QToolButton()
        self.button_zoom_in.setIcon(self.get_icon("plus.png"))
        self.button_zoom_in.clicked.connect(self.zoomIn)
        self.toolbar_zoom.addWidget(self.button_zoom_in)

        self.button_zoom_out = QToolButton()
        self.button_zoom_out.setIcon(self.get_icon("minus.png"))
        self.button_zoom_out.clicked.connect(self.zoomOut)
        self.toolbar_zoom.addWidget(self.button_zoom_out)

        self.central_widget_layout.addWidget(self.toolbar_zoom)

        # Layout for drawing over image, also it is a reason of a lot of containers
        self.image_layout = QStackedLayout()
        self.image_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.image_layout.setContentsMargins(0, 0, 0, 0)

        self.image_container = QWidget()
        self.image_container.setLayout(self.image_layout)

        self.image_widget = QLabel()
        self.image_widget.setStyleSheet(
            "QWidget { border: none; background-color: white; }"
        )
        self.image_widget.setAlignment(Qt.AlignCenter)
        self.image_widget.setMinimumSize(200, 200)

        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("QWidget { border: none; }")
        self.container_layout = QHBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        self.drawing_widget = DrawingWidget()
        self.drawing_widget.setFocus()
        # self.drawing_widget.focusUpdated.connect(self.updateStyleSheet)
        self.container_layout.addWidget(self.drawing_widget, alignment=Qt.AlignCenter)

        self.image_layout.addWidget(self.container_widget)
        self.image_layout.addWidget(self.image_widget)
        self.setColor(self.image_widget, COLOR_BACKGROUND_WIDGETS)

        # When image zooms bigger than image widget
        self.scrollArea = QScrollArea()
        self.scrollArea.setStyleSheet("QWidget { border: none;}")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.image_container)
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.central_widget_layout.addWidget(self.scrollArea)

        self.drawing_widget.installEventFilter(self)

    def eventFilter(self, obj: DrawingWidget, event: QEvent) -> bool:
        """Catch focus"""
        if obj == self.drawing_widget and event.type() == QEvent.FocusIn:
            self.updateStyleSheet(True)
        elif obj == self.drawing_widget and event.type() == QEvent.FocusOut:
            self.updateStyleSheet(False)

        return super().eventFilter(obj, event)

    def updateStyleSheet(self, focused: bool = False) -> None:
        """Change border color"""
        border_color = FOCUSED if focused else UNFOCUSED

        self.setStyleSheet(
            f"""
            QWidget#CentralWidget {{  
                border: 2px solid {border_color}; 
                border-radius: 10px;
                background-color: white; 
            }} 
        """
        )

    def hasPixmap(self) -> bool:
        """Check Pixmap existing"""
        if self._pixmap.isNull():
            return False
        else:
            return True

    def setScaleFactor(self, factor: float) -> None:
        """Set new scale factor and zoom factor to drawing widget"""
        self._scale_factor = factor
        self.drawing_widget.setZoomFactor(self._scale_factor)

    def zoomIn(self) -> None:
        """Increase image"""
        self._scale_factor *= 1.1
        self.resizeImage()

    def zoomOut(self) -> None:
        """Decrease image"""
        self._scale_factor /= 1.1
        self.resizeImage()

    def resizeImage(self) -> None:
        """Change image representation size with saving original image size"""
        if not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(
                self._scale_factor * self._pixmap.size(), Qt.KeepAspectRatio
            )

            self.image_widget.setPixmap(scaled_pixmap)
            self.image_widget.setMinimumSize(scaled_pixmap.size())

            self.drawing_widget.setZoomFactor(self._scale_factor)

            # Drawing widget size strongly relates to scaled image size
            self.drawing_widget.setFixedSize(scaled_pixmap.size())
            self.drawing_widget.updateDrawScale()

    def setPixmapSize(self) -> None:
        """Save image widget size when main window resizes"""
        if not self._pixmap.isNull():
            self.image_widget.setPixmap(
                self._pixmap.scaled(
                    self._scale_factor * self._pixmap.size(), Qt.KeepAspectRatio
                )
            )

    def fitImage(self) -> QPixmap:
        """When image opens at first time it should fit to image widget size"""
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
        """Changes sizes, factors and clean drawing area when new image is opened"""
        self._pixmap = image
        if not self._pixmap.isNull():

            # To return image_widget size after zooming to usual size save policy
            sp = self.image_widget.sizePolicy()

            # Set scrollArea.size without scrollbar width
            if self.scrollArea.horizontalScrollBar().isVisible():
                scrollAreaHeight = (
                    self.scrollArea.height()
                    - self.scrollArea.horizontalScrollBar().height()
                )
                scrollAreaWidth = (
                    self.scrollArea.width()
                    - self.scrollArea.verticalScrollBar().width()
                )
            else:
                scrollAreaHeight = self.image_widget.height()
                scrollAreaWidth = self.image_widget.width()

            self.image_widget.setFixedSize(scrollAreaWidth, scrollAreaHeight)

            # Change pixmap size as image_widget size
            original_size = self._pixmap.height() + self._pixmap.width()
            scaled_pixmap = self.fitImage()

            # Return old policy
            self.image_widget.setMaximumSize(2000, 2000)
            self.image_widget.setSizePolicy(sp)

            self.drawing_widget.setFixedSize(scaled_pixmap.size())
            self.drawing_widget.cleanDrawingWidget()

            self.setScaleFactor(
                (scaled_pixmap.height() + scaled_pixmap.width()) / original_size
            )
            self.drawing_widget.setConstants(self._pixmap.size())

    def setColor(self, widget: QWidget, color: QColor) -> None:
        """Set background widget color"""
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, color)
        widget.setPalette(palette)
