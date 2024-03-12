import math

from typing import Tuple

from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtCore import QPoint, QLine


ORGANIC_COLOR = QColor(0, 150, 0)


class TypedLine:
    """ This class is line for DrawingWidget which contains information about:
    line: QLine
        line position
    type: str
        type of line (single, double, triple and etc.)
    distance: float
        some distance for drawing related lines 
    """
    def __init__(self, line: QLine, type_line: str, distance: float) -> None:
        self.line = line
        self.type = type_line
        self.distance = distance
    
    def calculateParallelLines(self) -> Tuple[float]:
        """ Calculate deltas to make lines parallel in different rotation """
        # Calculate the direction vector of the line
        dx = self.line.x2() - self.line.x1()
        dy = self.line.y2() - self.line.y1()

        # Length of the direction vector
        length = math.sqrt(dx**2 + dy**2)

        if length != 0:
            ux = dx / length
            uy = dy / length

            return -uy, ux

    def draw(self, painter: QPainter) -> None:
        """ Drawing line according to its type """
        if self.type == "single":
            painter.drawLine(self.line)

        elif self.type == "double":
            px, py = self.calculateParallelLines()
            painter.drawLine(QLine(self.line.x1() + self.distance * px, self.line.y1() + self.distance * py, 
                                   self.line.x2() + self.distance * px, self.line.y2() + self.distance * py))
            painter.drawLine(QLine(self.line.x1() - self.distance * px, self.line.y1() - self.distance * py, 
                                   self.line.x2() - self.distance * px, self.line.y2() - self.distance * py))
        elif self.type == "triple":
            px, py = self.calculateParallelLines()
            painter.drawLine(self.line)
            painter.drawLine(QLine(self.line.x1() + self.distance * px, self.line.y1() + self.distance * py, 
                                   self.line.x2() + self.distance * px, self.line.y2() + self.distance * py))
            painter.drawLine(QLine(self.line.x1() - self.distance * px, self.line.y1() - self.distance * py, 
                                   self.line.x2() - self.distance * px, self.line.y2() - self.distance * py))


class Atom:
    """ This class is point (or Atom) for DrawingWidget which contains information about:
    position: QPoint
        point position
    name: str
        atom symbol
    size: int
        font size
    map_atoms: Dict[str, QColor]
        mapping color and symbol
    """
    def __init__(self, position: QPoint, name: str, size: int) -> None:
        self.position = position
        self.name = name
        self.size = size
        self.map_atoms = {"C": ORGANIC_COLOR,
                          "N": ORGANIC_COLOR,
                          "O": ORGANIC_COLOR,
                          "F": ORGANIC_COLOR}
        
    def color(self) -> None:
        """ Return color according to map_atoms"""
        if self.name in self.map_atoms:
            return self.map_atoms[self.name]
        else:
            return QColor(100, 30, 200)
    
    def draw(self, painter: QPainter, flag: bool = False) -> None:
        """ Draw text """
        pen = QPen(self.color(), 5)
        painter.setPen(pen)

        font_size = self.size
        font = QFont("Verdana", font_size)
        painter.setFont(font)

        font_metrics = painter.fontMetrics()
        text_width = font_metrics.boundingRect(self.name).width()
        text_height = font_metrics.boundingRect(self.name).height()
        text_position = QPoint(self.position.x() - text_width // 2, 
                               self.position.y() - text_height // 2 + font_metrics.ascent())

        painter.drawText(text_position, self.name)

        if flag:
            # Draw rectangle where temporal text will be written
            rect_width = max(text_width + 2, font_metrics.horizontalAdvance("M") + 2)  # Adding some padding
            rect_height = max(text_height + 2, font_metrics.height() + 2)

            rect_x = self.position.x() - rect_width // 2
            rect_y = self.position.y() - rect_height // 2

            painter.setPen(QPen(QColor(0, 0, 255)))  # Blue rectangle
            painter.drawRect(rect_x + 2, rect_y + 2, rect_width, rect_height)