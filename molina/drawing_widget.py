from typing import Dict, Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    Qt, 
    QSize,
    QRect, 
    Signal, 
    QPoint, 
    QLine,
)
from PySide6.QtGui import (
    QPainter,
    QPen,
    QPaintEvent,
    QFont,
)

from molina.data_manager import DataManager
from molina.drawing_objects import Atom, TypedLine
    

class DrawingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines = []
        self._points = []
        self._temp_line = None
        self._atom_type = None
        self._bond_type = None
        self._zoom_factor = 1.0
        self._text_size = None
        self._bond_distance = None
        self._closest_atom_threshold = None
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False
        self._data_manager = DataManager()
        self.setFocusPolicy(Qt.StrongFocus)     

        self._data_manager.newDataToDrawingWidget.connect(self.updateDrawScale)
        self._data_manager.pointUpdate.connect(self.updatePoint)
        self._data_manager.lineUpdate.connect(self.updateLine)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        for line in self._lines:
            line.distance = self.getScaledThresholds(self._bond_distance)
            pen = QPen(Qt.red, 5)
            painter.setPen(pen)
            line.draw(painter)

        for point in self._points:
            pen = QPen(point.color(), 5)
            painter.setPen(pen)

            font = QFont("Verdana", int(point.size * self._zoom_factor))
            painter.setFont(font)

            font_metrics = painter.fontMetrics()
            text_width = font_metrics.boundingRect(point.name).width()
            text_height = font_metrics.boundingRect(point.name).height()
            text_position = QPoint(point.position.x() - text_width // 2, point.position.y() + text_height // 2)

            painter.drawText(text_position, point.name)

        if self._temp_line:
            pen = QPen(Qt.red, 5)
            painter.setPen(pen)
            self._temp_line.draw(painter)
    
    def addPoint(self, atom: Atom) -> None:
        not_scaled_atom = Atom(QPoint(atom.position.x() / self._zoom_factor, 
                                      atom.position.y() / self._zoom_factor),
                               atom.name,
                               atom.size)
        
        self._points.append(atom)

        self._data_manager.addAtom(not_scaled_atom, len(self._points)-1)
        self.update()
    
    def getScaledThresholds(self, threshold: float) -> float:
        value = threshold * self._zoom_factor
        return 1 if value < 1 else 100 if value > 100 else value

    def findAtoms(self, line: QLine) -> Dict:
        threshold = self.getScaledThresholds(self._closest_atom_threshold)
        close_point = {}
        for i, atom in enumerate(self._points):
            point = atom.position
            distance_to_start = (line.p1() - point).manhattanLength()
            distance_to_end = (line.p2() - point).manhattanLength()
            if distance_to_start <= threshold:
                close_point[i] = point
            elif distance_to_end <= threshold:
                close_point[i] = point
        
        if len(close_point) == 2: 
            return close_point
        else:
            return

    def addLine(self, line: TypedLine) -> None:
        atoms = self.findAtoms(line.line)
        if atoms:
            p1, p2 = atoms.values()
            line_from_atom = QLine(p1, p2)
            line.line = line_from_atom
            self._lines.append(line)

            not_scaled_line = QLine(line_from_atom.x1() / self._zoom_factor, 
                                    line_from_atom.y1() / self._zoom_factor,
                                    line_from_atom.x2() / self._zoom_factor,
                                    line_from_atom.y2() / self._zoom_factor)
            
            self._data_manager.addBond(TypedLine(not_scaled_line, line.type, self._bond_distance),
                         list(atoms.keys()), len(self._lines)-1)
        else: 
            self._temp_line = None

        self.update()
    
    def deleteLine(self, idx: int) -> None:
        self._lines.pop(idx)
        self._data_manager.deleteBond(idx, len(self._lines))

        self.update()
                
    def deletePointAndLine(self, idx: int) -> None:
        self._points.pop(idx)
        self._data_manager.deleteAtom(idx, len(self._points))

        self.update()

    def lineCenter(self, line: QLine) -> QPoint:
        x_center = (line.x1() + line.x2()) / 2
        y_center = (line.y1() + line.y2()) / 2
        return QPoint(x_center, y_center)
    
    def partLine(self, end_line: QPoint, center: QPoint, part: float = 0.66) -> QPoint:
        x = center.x() + part * (end_line.x() - center.x())
        y = center.y() + part * (end_line.y() - center.y())
        return QPoint(x, y)
    
    def createToleranceRectangle(self, start: QPoint, end: QPoint, tolerance: int) -> QRect:
        if start.x() == end.x():  # Vertical line
            return QRect(start.x() - tolerance // 2, min(start.y(), end.y()),
                        tolerance, abs(start.y() - end.y()))
        elif start.y() == end.y():  # Horizontal line
            return QRect(min(start.x(), end.x()), start.y() - tolerance // 2,
                        abs(start.x() - end.x()), tolerance)
        else:
            # For non-axis-aligned lines, additional logic is needed
            # Depending on your requirements, this can be more complex
            return None

    def isPointOnLineSegment(self, start: QPoint, end: QPoint, point: QPoint) -> bool:
        tolerance_rect = self.createToleranceRectangle(start, end, self.getScaledThresholds(self._bond_distance))
        if tolerance_rect:
            return tolerance_rect.contains(point)
        
        line_length = (start - end).manhattanLength()
        d1 = (point - start).manhattanLength()
        d2 = (point - end).manhattanLength()
        return abs(d1 + d2 - line_length) < 1e-5 

    def findClosestObject(self, position: QPoint) -> None:
        threshold = self.getScaledThresholds(self._closest_atom_threshold)
        
        for i in range(len(self._points)):
            distance = (position - self._points[i].position).manhattanLength()
            if distance <= threshold:
                 self.deletePointAndLine(i)
                 return

        for i in range(len(self._lines)):
            center = self.lineCenter(self._lines[i].line)
            part_P1 = self.partLine(self._lines[i].line.p1(), center)
            part_P2 = self.partLine(self._lines[i].line.p2(), center)
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
        not_scaled_data = self._data_manager.getDrawingData()
        if len(not_scaled_data["points"]) != 0:
            
            if len(self._lines) == 0 and len(self._points) == 0:
                self._data_manager.updateDistances(self._text_size, self._bond_distance)
            if len(self._lines) != len(not_scaled_data["lines"]):
                self._lines = [TypedLine(line.line, line.type, line.distance) for line in not_scaled_data["lines"]]
            for i in range(len(not_scaled_data["lines"])):
                line = not_scaled_data["lines"][i]
                self._lines[i].line = QLine(
                    line.line.x1() * self._zoom_factor,
                    line.line.y1() * self._zoom_factor,
                    line.line.x2() * self._zoom_factor,
                    line.line.y2() * self._zoom_factor)

            if len(self._points) != len(not_scaled_data["points"]):
                self._points = [Atom(atom.position, atom.name, atom.size) for atom in not_scaled_data["points"]]
            for i in range(len(not_scaled_data["points"])):
                point = not_scaled_data["points"][i]
                self._points[i].position = QPoint(point.position.x() * self._zoom_factor,
                                                  point.position.y() * self._zoom_factor)

            self.update()
    
    def updatePoint(self, update_type: str, idx: Optional[int] = None, point: Optional[Atom] = None) -> None:
        if update_type == "delete" and idx is None:
            self._points.pop()
        elif update_type == "delete" and idx is not None:
            self._points.pop(idx)
        elif update_type == "add":
            scaled_point = QPoint(point.position.x() * self._zoom_factor,
                                  point.position.y() * self._zoom_factor)
            self._points.insert(idx, Atom(scaled_point, point.name, point.size))
        
        self.update()

    def updateLine(self, update_type: str, idx: Optional[int] = None, line: Optional[TypedLine] = None) -> None:
        if update_type == "delete" and idx is None:
            self._lines.pop()
        elif update_type == "delete" and idx is not None:
            self._lines.pop(idx)
        elif update_type == "add":
            new_line = QLine(line.line.x1() * self._zoom_factor,
                             line.line.y1() * self._zoom_factor,
                             line.line.x2() * self._zoom_factor,
                             line.line.y2() * self._zoom_factor)
            
            self._lines.insert(idx, TypedLine(new_line, line.type, line.distance))
        
        self.update()
    
    def setThresholds(self, image_size: QSize) -> None:
        smallest_dim = min(image_size.width(), image_size.height())
        self._bond_distance = smallest_dim * 0.02
        self._closest_atom_threshold = smallest_dim * 0.02
        value  = smallest_dim * 0.05
        self._text_size = 3 if value < 3 else 100 if value > 100 else int(value)

    def setZoomFactor(self, factor: float) -> None:
        self._zoom_factor = factor
        self.update()
    
    def cleanDrawingWidget(self) -> None:
        self._lines = []
        self._points = []
        self._temp_line = None
        self._zoom_factor = 1.0
        self._text_size = None
        self._bond_distance = None
        self._closest_atom_threshold = None
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False

        self._data_manager.cleanAll()

    def clearAll(self) -> None:
        self._lines = []
        self._points = []
        self._temp_line = None
        self._data_manager.allDeleted()
        self.update()

    def mousePressEvent(self, event: QPaintEvent) -> None:
        if event.button() == Qt.LeftButton:
            if self._drawing_point_enabled:
                self.addPoint(Atom(event.pos(), self._atom_type, self._text_size))
            elif self._drawing_line_enabled:
                self._temp_line = TypedLine(QLine(event.pos(), event.pos()),
                                            self._bond_type, 
                                            self.getScaledThresholds(self._bond_distance))
                
        elif event.button() == Qt.RightButton:
            self.findClosestObject(event.pos())
    
    def mouseMoveEvent(self, event) -> None:
        if self._drawing_line_enabled:
            if self._temp_line:
                self._temp_line.line.setP2(event.pos())
                self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._drawing_line_enabled:
            self._temp_line.distance = self._bond_distance
            self.addLine(self._temp_line)
            self._temp_line = None

    def keyPressEvent(self, event: QPaintEvent) -> None:
        super().keyPressEvent(event)
        
        if self._drawing_line_enabled:
            self._drawing_line_enabled = False
        elif self._drawing_point_enabled:
            self._drawing_point_enabled = False

        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            self._data_manager.undo()

        elif event.key() == Qt.Key_C:
            self.setDrawingMode(True, "point", "C")
        
        elif event.key() == Qt.Key_1:
            self.setDrawingMode(True, "line", "single")
        
        elif event.key() == Qt.Key_2:
            self.setDrawingMode(True, "line", "double")

        elif event.key() == Qt.Key_3:
            self.setDrawingMode(True, "line", "triple")