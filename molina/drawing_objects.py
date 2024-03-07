import math

from typing import Tuple

from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import QPoint, QLine


ORGANIC_COLOR = QColor(0, 150, 0)


class TypedLine:
    def __init__(self, line: QLine, type_line: str, distance: float):
        self.line = line
        self.type = type_line
        self.distance = distance
    
    def calculateParallelLines(self) -> Tuple[float]:
        # Calculate the direction vector of the line
        dx = self.line.x2() - self.line.x1()
        dy = self.line.y2() - self.line.y1()

        # Length of the direction vector
        length = math.sqrt(dx**2 + dy**2)

        if length != 0:
            ux = dx / length
            uy = dy / length

            return -uy, ux

    def draw(self, painter: QPainter):
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
    def __init__(self, position: QPoint, name: str, size: int) -> None:
        self.position = position
        self.name = name
        self.size = size
        self.map_atoms = {"C": ORGANIC_COLOR,
                          "N": ORGANIC_COLOR,
                          "O": ORGANIC_COLOR,
                          "F": ORGANIC_COLOR}
        
    def color(self):
        if self.name in self.map_atoms:
            return self.map_atoms[self.name]
        else:
            return QColor(100, 30, 200)