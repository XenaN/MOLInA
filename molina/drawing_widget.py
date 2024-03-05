import copy, math

from typing import Dict, Tuple

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
    QColor,
    QPen,
    QPaintEvent,
    QFont,
)

from molina.action_managers import DrawingActionManager


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
        return self.map_atoms[self.name]
    

class DrawingWidget(QWidget):
    coordinateUpdate = Signal(object)
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
        self._action_manager = DrawingActionManager(self)
        self.setFocusPolicy(Qt.StrongFocus)
        self._original_coordinate = {"bonds": [],
                                     "lines": [],
                                     "atoms": []}        

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        for line in self._lines:
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
    
    def getScaledThresholds(self, threshold: float) -> float:
        value = threshold * self._zoom_factor
        return 1 if value < 1 else 100 if value > 100 else value

    def findAtoms(self, line: QLine) -> Dict:
        threshold = self._closest_atom_threshold
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

    def addLine(self, line: TypedLine, flag_undo: bool = True) -> None:
        atoms = self.findAtoms(line.line)
        if atoms:
            scaled_line = QLine(line.line.x1() * self._zoom_factor, 
                                line.line.y1() * self._zoom_factor,
                                line.line.x2() * self._zoom_factor,
                                line.line.y2() * self._zoom_factor)
            self._lines.append(TypedLine(scaled_line,
                                         line.type, 
                                         line.distance))

            if flag_undo:
                self._action_manager.addAction(line, "add_line")
            
            self._original_coordinate["lines"].append(line)
            self._original_coordinate["bonds"].append({"bond_type": self._bond_type,
                                                       "endpoint_atoms": list(atoms.keys())})
            
            self.coordinateUpdate.emit(self._original_coordinate)
        else: 
            self._temp_line = None

        self.update()
    
    def deleteLine(self, index=-1, flag_undo: bool = True) -> None:
        if index != -1:
            self._original_coordinate["bonds"].pop(index)
            last_line  = self._original_coordinate["lines"].pop(index)
            self._lines.pop(index)
        else:
            self._original_coordinate["bonds"].pop()
            last_line  = self._original_coordinate["lines"].pop()
            self._lines.pop()
        
        if flag_undo:
            self._action_manager.addAction(last_line, "delete_line")

        self.coordinateUpdate.emit(self._original_coordinate)
        self.update()

    def addPoint(self, atom: Atom, flag_undo: bool = True) -> None:
        self._original_coordinate["atoms"].append({
            "atom_symbol": atom.name,
            "x": atom.position.x() / self._zoom_factor, 
            "y": atom.position.y() / self._zoom_factor})
        
        if flag_undo:
            self._action_manager.addAction(atom, "add_point")
        self._points.append(atom)

        self.coordinateUpdate.emit(self._original_coordinate)
        self.update()
    
    def deletePoint(self, flag_undo: bool = True) -> None:
        self._original_coordinate["atoms"].pop()
        last_point = self._points.pop()
        
        if flag_undo:
            self._action_manager.addAction(last_point, "delete_point")
        
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
        print(self._original_coordinate)
        self._action_manager.addAction(copy.deepcopy(self._original_coordinate), "delete_point_and_lines")
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
    
    def create_tolerance_rectangle(self, start: QPoint, end: QPoint, tolerance: int) -> QRect:
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
        tolerance_rect = self.create_tolerance_rectangle(start, end, self.getScaledThresholds(self._bond_distance))
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
        if len(self._lines) != len(self._original_coordinate["lines"]):
            self._lines = copy.deepcopy(self._original_coordinate["lines"])
        for i in range(len(self._original_coordinate["lines"])):
            line = self._original_coordinate["lines"][i]
            self._lines[i].line = QLine(
                line.line.x1() * self._zoom_factor,
                line.line.y1() * self._zoom_factor,
                line.line.x2() * self._zoom_factor,
                line.line.y2() * self._zoom_factor)
            self._lines[i].distance = self.getScaledThresholds(self._original_coordinate["lines"][i].distance)
            
        if len(self._points) != len(self._original_coordinate["atoms"]):
            self._points = [QPoint() for i in range(len(self._original_coordinate["atoms"]))]
        for i in range(len(self._original_coordinate["atoms"])):
            point = self._original_coordinate["atoms"][i]
            self._points[i].setX(point["x"] * self._zoom_factor)
            self._points[i].setY(point["y"] * self._zoom_factor)
    
    def setThresholds(self, image_size: QSize) -> None:
        smallest_dim = min(image_size.width(), image_size.height())
        self._bond_distance = smallest_dim * 0.02
        self._closest_atom_threshold = smallest_dim * 0.02
        value  = smallest_dim * 0.05
        self._text_size = 3 if value < 3 else 100 if value > 100 else int(value)

    def setZoomFactor(self, factor: float) -> None:
        self._zoom_factor = factor
        self.update()
    
    def getOriginalCoordinate(self) -> Dict:
        return self._original_coordinate
    
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
        self._action_manager = DrawingActionManager(self)
        self._original_coordinate = {"bonds": [],
                                     "lines": [],
                                     "atoms": []}

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
            self._temp_line.line.setP2(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._drawing_line_enabled:
            not_scaled_line = TypedLine(
                QLine(self._temp_line.line.x1() / self._zoom_factor, 
                      self._temp_line.line.y1() / self._zoom_factor,
                      self._temp_line.line.x2() / self._zoom_factor,
                      self._temp_line.line.y2() / self._zoom_factor),
                self._bond_type,
                self.getScaledThresholds(self._bond_distance)      
            )
            self.addLine(not_scaled_line)
            self._temp_line = None

    def updateCoordinates(self, coordinates: Dict, flag_undo: bool = False) -> None:
        self._original_coordinate = coordinates.copy()
        self._original_coordinate["lines"] = []
        self._lines = []
        self._points = []
        atoms = self._original_coordinate["atoms"]
        for bond in self._original_coordinate["bonds"]:
            self._original_coordinate["lines"].append(
                TypedLine(
                    QLine(
                        QPoint(atoms[bond["endpoint_atoms"][0]]["x"],
                            atoms[bond["endpoint_atoms"][0]]["y"]),
                        QPoint(atoms[bond["endpoint_atoms"][1]]["x"],
                            atoms[bond["endpoint_atoms"][1]]["y"])
                        ),
                        bond["bond_type"],
                        self.getScaledThresholds(self._bond_distance)
            ))
        if flag_undo:
            self.coordinateUpdate.emit(self._original_coordinate)
        
        self.updateDrawScale()
        self.update()
    
    def clearAll(self) -> None:
        self._action_manager.addAction(copy.deepcopy(self._original_coordinate), "delete_point_and_lines")
        if len(self._original_coordinate["atoms"]) != 0: 
            self._action_manager.addAction(self._original_coordinate, "clear_all")
            self._lines = []
            self._points = []
            self._temp_line = None
            self._original_coordinate = {"bonds": [],
                                        "lines": [],
                                        "atoms": []}
            self.coordinateUpdate.emit(self._original_coordinate)
            self.update()
    
    def keyPressEvent(self, event: QPaintEvent) -> None:
        super().keyPressEvent(event)
        
        if self._drawing_line_enabled:
            self._drawing_line_enabled = False
        elif self._drawing_point_enabled:
            self._drawing_point_enabled = False

        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            self._action_manager.undo()

        elif event.key() == Qt.Key_C:
            self.setDrawingMode(True, "point", "C")
        
        elif event.key() == Qt.Key_1:
            self.setDrawingMode(True, "line", "single")
        
        elif event.key() == Qt.Key_2:
            self.setDrawingMode(True, "line", "double")

        elif event.key() == Qt.Key_3:
            self.setDrawingMode(True, "line", "triple")