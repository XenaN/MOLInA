from typing import Dict, Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    Qt, 
    QSize,
    QRect,  
    QPoint, 
    QLine,
)
from PySide6.QtGui import (
    QPainter,
    QPen,
    QPaintEvent,
)

from molina.data_manager import DataManager
from molina.drawing_objects import Atom, TypedLine
from molina.hotkeys import Hotkeys
    

class DrawingWidget(QWidget):
    """ This class is drawing area with image size.
    There are atoms and bonds. Atom is a point with position and symbol.
    Bond is a line between two atoms, which can be different type. 
    Here user can add and delete points and lines or clean whole area. 
    Also existing annotation or model prediction is drawn here.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines = []
        self._points = []
        self._temp_text = ""
        
        self._temp_line = None
        self._atom_type = None
        self._bond_type = None
        self._temp_atom = None
        
        self._zoom_factor = 1.0
        
        self._text_size = None
        self._bond_constant = None
        self._closest_atom_threshold = None
        
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False
        self._is_writing = False
        
        self.setFocusPolicy(Qt.StrongFocus)     

        self._hotkeys = Hotkeys()
        self._map_keys = self._hotkeys.getHotkeys()
        self._hotkeys.mapUpdate.connect(self.setHotkeysMap)

        self._data_manager = DataManager()
        self._data_manager.newDataToDrawingWidget.connect(self.drawNewData)
        self._data_manager.pointUpdate.connect(self.updatePoint)
        self._data_manager.lineUpdate.connect(self.updateLine)

    def paintEvent(self, event: QPaintEvent) -> None:
        """ Function to draw points and lines """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(Qt.red, 5)
        painter.setPen(pen)

        for line in self._lines:
            line.constants = self.getScaledBondConstants(self._bond_constant)
            line.draw(painter)

        for point in self._points:
            point.size = int(self.getScaledConstants(self._text_size))
            point.draw(painter)

        # Draw current text being written
        if self._temp_atom:
            self._temp_atom.size = int(self.getScaledConstants(self._text_size))
            self._temp_atom.draw(painter, self._is_writing)

        # Draw current line while button mouse is pushed       
        if self._temp_line:
            self._temp_line.draw(painter)
    
    def addPoint(self, atom: Atom) -> None:
        """ Add atom to DataManager data """
        not_scaled_atom = Atom(QPoint(atom.position.x() / self._zoom_factor, 
                                      atom.position.y() / self._zoom_factor),
                               atom.name,
                               atom.size)
        
        self._points.append(atom)

        self._data_manager.addAtom(not_scaled_atom, len(self._points)-1)
        self.update()
    
    def getScaledConstants(self, threshold: float) -> float:
        """ Scaled thresholds or sizes, or return maximum or minimum value """
        value = threshold * self._zoom_factor
        return 1 if value < 1 else 100 if value > 100 else value
    
    def getScaledBondConstants(self, bond_constants: float) -> float:
        """ Scaled thresholds or distances, or return maximum or minimum value """
        min_value = 1
        max_value = 20
        scaled_dict = {key: min(max(int(value  * self._zoom_factor), min_value), max_value) 
                       for key, value in bond_constants.items()}
        return scaled_dict

    def findAtoms(self, line: QLine) -> Dict:
        """ Save temporal line only if there are near two points """
        threshold = self.getScaledConstants(self._closest_atom_threshold)

        # Keep order founded atoms
        close_point = {"start": [], "end": []}

        for i, atom in enumerate(self._points):
            point = atom.position
            distance_to_start = (line.p1() - point).manhattanLength()
            distance_to_end = (line.p2() - point).manhattanLength()
            
            if distance_to_start <= threshold:
                close_point["start"].append({"pos": point, 
                                             "idx": i})
            elif distance_to_end <= threshold:
                close_point["end"].append({"pos": point, 
                                             "idx": i})
        
        # Check how many atoms are founded, if two - ok
        if (len(close_point["start"]) + len(close_point["end"])) == 2: 
            return close_point
        else:
            return

    def addLine(self, line: TypedLine) -> None:
        """ Add bond to DataManager data """
        atoms = self.findAtoms(line.line)
        if atoms:
            p1, p2 = atoms["start"][0]["pos"], atoms["end"][0]["pos"]
            line_from_atom = QLine(p1, p2)
            line.line = line_from_atom
            self._lines.append(line)

            not_scaled_line = QLine(line_from_atom.x1() / self._zoom_factor, 
                                    line_from_atom.y1() / self._zoom_factor,
                                    line_from_atom.x2() / self._zoom_factor,
                                    line_from_atom.y2() / self._zoom_factor)
            
            self._data_manager.addBond(TypedLine(not_scaled_line, 
                                                 line.type, 
                                                 self._bond_constant),
                                       [atoms["start"][0]["idx"], atoms["end"][0]["idx"]], 
                                       len(self._lines)-1)
        else: 
            self._temp_line = None

        self.update()
    
    def deleteLine(self, idx: int) -> None:
        """ Delete chosen line """
        self._lines.pop(idx)
        self._data_manager.deleteBond(idx, len(self._lines))

        self.update()
                
    def deletePoint(self, idx: int) -> None:
        """ Delete chosen atom """
        self._points.pop(idx)
        self._data_manager.deleteAtom(idx, len(self._points))

        self.update()

    def lineCenter(self, line: QLine) -> QPoint:
        """ Calculate center of chosen line """
        x_center = (line.x1() + line.x2()) / 2
        y_center = (line.y1() + line.y2()) / 2
        return QPoint(x_center, y_center)
    
    def partLine(self, end_line: QPoint, center: QPoint, part: float = 0.66) -> QPoint:
        """ Calculate 2/3 of chosen line """
        x = center.x() + part * (end_line.x() - center.x())
        y = center.y() + part * (end_line.y() - center.y())
        return QPoint(x, y)
    
    def createToleranceRectangle(self, start: QPoint, end: QPoint, tolerance: int) -> QRect:
        """ Calculate tolerance rectangle around line """
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
        """ Check if click is on tolerance rectangle of chosen line """
        tolerance_rect = self.createToleranceRectangle(start, 
                                                       end, 
                                                       self.getScaledBondConstants(self._bond_constant))
        if tolerance_rect:
            return tolerance_rect.contains(point)
        
        line_length = (start - end).manhattanLength()
        d1 = (point - start).manhattanLength()
        d2 = (point - end).manhattanLength()

        return abs(d1 + d2 - line_length) < 1e-5 

    def findClosestObject(self, position: QPoint) -> None:
        """ According to scaled threshold choose the closest object and delete it """
        threshold = self.getScaledConstants(self._closest_atom_threshold)
        
        for i in range(len(self._points)):
            distance = (position - self._points[i].position).manhattanLength()
            if distance <= threshold:
                 self.deletePoint(i)
                 return

        for i in range(len(self._lines)):
            center = self.lineCenter(self._lines[i].line)
            part_P1 = self.partLine(self._lines[i].line.p1(), center)
            part_P2 = self.partLine(self._lines[i].line.p2(), center)
            if self.isPointOnLineSegment(part_P1, part_P2, position):
                self.deleteLine(i)
                return

    def setDrawingMode(self, enabled: bool, type: str, info: str) -> None:
        """ Set flag for drawing line or point mode """
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
        """ Scale data after change image size """
        not_scaled_data = self._data_manager.getDrawingData()

        if len(not_scaled_data["points"]) != 0:
            if len(self._points) != len(not_scaled_data["points"]):
                self._points = [Atom(atom.position, atom.name, atom.size) for atom in not_scaled_data["points"]]
            
            for i in range(len(not_scaled_data["points"])):
                point = not_scaled_data["points"][i]
                self._points[i].position = QPoint(point.position.x() * self._zoom_factor,
                                                  point.position.y() * self._zoom_factor)
            
            if len(not_scaled_data["lines"]) != 0:
                if len(self._lines) != len(not_scaled_data["lines"]):
                    self._lines = [TypedLine(line.line, line.type, line.constants) for line in not_scaled_data["lines"]]
                
                for i in range(len(not_scaled_data["lines"])):
                    line = not_scaled_data["lines"][i]
                    self._lines[i].line = QLine(
                        line.line.x1() * self._zoom_factor,
                        line.line.y1() * self._zoom_factor,
                        line.line.x2() * self._zoom_factor,
                        line.line.y2() * self._zoom_factor)
                                                  
            self.update()
    
    def drawNewData(self):
        """ Set not scaled distances and font size to DataManager data
          and scale data to draw it 
        """
        self._data_manager.updateDistances(self._text_size, self._bond_constant)
        self.updateDrawScale()
    
    def updatePoint(self, update_type: str, idx: Optional[int] = None, point: Optional[Atom] = None) -> None:
        """ Delete or add atom """
        if update_type == "delete" and idx is None:
            self._points.pop()
        elif update_type == "delete" and idx is not None:
            self._points.pop(idx)
        elif update_type == "add":
            scaled_point = QPoint(point.position.x() * self._zoom_factor,
                                  point.position.y() * self._zoom_factor)
            self._points.insert(idx, Atom(scaled_point, point.name, point.size))
        
        self.update()

    def updateLine(self, update_type: str, idx: Optional[int] = None, 
                   line: Optional[TypedLine] = None) -> None:
        """ Delete or add bond """
        if update_type == "delete" and idx is None:
            self._lines.pop()
        elif update_type == "delete" and idx is not None:
            self._lines.pop(idx)
        elif update_type == "add":
            new_line = QLine(line.line.x1() * self._zoom_factor,
                             line.line.y1() * self._zoom_factor,
                             line.line.x2() * self._zoom_factor,
                             line.line.y2() * self._zoom_factor)
            
            self._lines.insert(idx, TypedLine(new_line, line.type, line.constants))
        
        self.update()
    
    def setHotkeysMap(self, new_map: Dict) -> None:
        """set new hotkeys map"""
        self._map_keys = new_map
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False
    
    def setConstants(self, image_size: QSize) -> None:
        """ Choose smallest image side and scale all constants """
        smallest_dim = min(image_size.width(), image_size.height())

        self._bond_constant = {"bond_distance": 14, 
                               "line_width": 8,
                               "max_width": 12,
                               "segment_number": 20}
        self._closest_atom_threshold = smallest_dim * 0.03
        self._text_size = 45

    def setZoomFactor(self, factor: float) -> None:
        """ Set new zoom factor after scale factor changing """
        self._zoom_factor = factor
        self.update()
    
    def cleanDrawingWidget(self) -> None:
        """ Reset all variables after image changing """
        self._lines = []
        self._points = []
        self._temp_text = ""
        self._temp_line = None
        self._zoom_factor = 1.0
        self._text_size = None
        self._bond_constant = None
        self._closest_atom_threshold = None
        self._is_writing = False
        self._drawing_line_enabled = False
        self._drawing_point_enabled = False

        self._data_manager.cleanAll()

    def clearAll(self) -> None:
        """ Reset drawing data """
        self._lines = []
        self._points = []
        self._temp_line = None
        self._data_manager.allDeleted()
        self.update()

    def mousePressEvent(self, event: QPaintEvent) -> None:
        """ Set point mode or line mode if left button is clicked.
        And find closest object to delete if right button
        """
        if event.button() == Qt.LeftButton:
            if self._drawing_point_enabled:
                self.addPoint(Atom(event.pos(), self._atom_type, self._text_size))

            elif self._drawing_line_enabled:
                self._temp_line = TypedLine(QLine(event.pos(), event.pos()),
                                            self._bond_type, 
                                            self.getScaledBondConstants(self._bond_constant))
            
            elif self._is_writing:
                self._temp_atom = Atom(event.pos(), "", self._text_size)
                self._temp_text = ""
                self.update()
                
        elif event.button() == Qt.RightButton:
            self.findClosestObject(event.pos())
    
    def mouseMoveEvent(self, event) -> None:
        """ Draw temporal line while mouse button pushed """
        if self._drawing_line_enabled:
            if self._temp_line:
                self._temp_line.line.setP2(event.pos())
                self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        """ Add line if two atoms are nearby """
        if event.button() == Qt.LeftButton and self._drawing_line_enabled:
            self._temp_line.constants = self._bond_constant
            self.addLine(self._temp_line)
            self._temp_line = None

    def keyPressEvent(self, event: QPaintEvent) -> None:
        """ Run action according to the key pressed """
        super().keyPressEvent(event)
        
        # Reset any mode
        if self._drawing_line_enabled:
            self._drawing_line_enabled = False
        elif self._drawing_point_enabled:
            self._drawing_point_enabled = False
        
        if self._is_writing:
            if event.key() == Qt.Key_Return:
                if self._temp_atom and self._temp_text != "":
                    self._temp_atom.name = self._temp_text
                    self.addPoint(self._temp_atom)
                self._is_writing = False
                self._temp_text = ""
                self._temp_atom = None
            
            elif event.key() == Qt.Key_Backspace:
                self._temp_text = self._temp_text[:-1]
                self._temp_atom.name = self._temp_text
            
            else:
                self._temp_text += event.text()
                self._temp_atom.name = self._temp_text
            
            self.update()
        
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self._data_manager.undo()
        
        elif event.key() == Qt.Key_W:
            self._is_writing = not self._is_writing
            self._temp_atom = None
            self.update()

        else:
            key = event.key()
            try:
                if self._map_keys[chr(event.key())]:
                    type_action, name = self._map_keys[chr(event.key())][0], self._map_keys[chr(event.key())][1]
                    self.setDrawingMode(True, type_action, name)
            except (ValueError, KeyError):
                pass
        
        