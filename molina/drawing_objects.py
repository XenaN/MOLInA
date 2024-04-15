import math

from typing import Tuple, Dict, Optional, List

from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath
from PySide6.QtCore import QPoint, QLine, Qt


ORGANIC_COLOR = QColor(0, 150, 0)
LINE_COLOR = QColor("#3366ff")


class Atom:
    """This class is point (or Atom) for DrawingWidget which contains information about:
    position: QPoint
        point position
    name: str
        atom symbol
    size: int
        font size
    map_atoms: Dict[str, QColor]
        mapping color and symbol
    """

    def __init__(self, position: QPoint, name: str):
        self.position = position
        self.name = name
        self.map_atoms = {
            "C": ORGANIC_COLOR,
            "N": ORGANIC_COLOR,
            "O": ORGANIC_COLOR,
            "F": ORGANIC_COLOR,
        }

    def color(self) -> None:
        """Return color according to map_atoms"""
        if self.name in self.map_atoms:
            return self.map_atoms[self.name]
        else:
            return QColor(100, 30, 200)

    def draw(self, painter: QPainter, size: int, flag: bool = False) -> None:
        """Draw text"""
        font = QFont("Verdana", size)
        font.setBold(True)
        painter.setFont(font)

        font_metrics = painter.fontMetrics()
        text_width = font_metrics.boundingRect(self.name).width()
        text_height = font_metrics.boundingRect(self.name).height()

        text_position = QPoint(
            self.position.x() - text_width // 2 - 3,
            self.position.y() - text_height // 2 + font_metrics.ascent(),
        )

        pen = QPen(QColor("white"), 5, Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        path = QPainterPath()
        path.addText(text_position, font, self.name)

        painter.setPen(pen)

        # painter.drawText(text_position, self.name)
        painter.drawPath(path)
        painter.fillPath(path, self.color())

        if flag:
            # Draw rectangle where temporal text will be written
            rect_width = max(
                text_width + 2, font_metrics.horizontalAdvance("M") + 4
            )  # Adding some padding
            rect_height = max(text_height + 4, font_metrics.height() + 4)

            rect_x = self.position.x() - rect_width // 2
            rect_y = self.position.y() - rect_height // 2

            painter.setPen(QPen(QColor(0, 0, 255)))  # Blue rectangle
            painter.drawRoundedRect(
                rect_x - 4, rect_y + 2, rect_width + 4, rect_height, 10, 10
            )


class TypedLine:
    """This class is line for DrawingWidget which contains information about:
    line: QLine
        line position
    type: str
        type of line (single, double, triple and etc.)
    distance: float
        some distance for drawing related lines
    """

    def __init__(
        self, line: QLine, type_line: str, atom_indexes: Optional[List[int]] = None
    ):
        self.line = line
        self.type = type_line
        self.atom_indexes = atom_indexes

    def setAtomIndexes(self, atom_indexes: List[int]) -> None:
        """Connect atoms with line ends"""
        self.atom_indexes = atom_indexes

    def update(self, atom1: QPoint, atom2: QPoint) -> None:
        """Update positions"""
        self.line = QLine(atom1, atom2)

    def calculateParallelLines(self) -> Tuple[float]:
        """Calculate deltas to make lines parallel in different rotation"""
        # Calculate the direction vector of the line
        dx = self.line.x2() - self.line.x1()
        dy = self.line.y2() - self.line.y1()

        # Length of the direction vector
        length = math.sqrt(dx**2 + dy**2)

        if length != 0:
            ux = dx / length
            uy = dy / length

            return -uy, ux

        else:
            return None, None

    def draw(self, painter: QPainter, constants: Dict) -> None:
        """Drawing line according to its type"""

        pen = QPen(LINE_COLOR, constants["line_width"], Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.type == "single":
            painter.drawLine(self.line)

        elif self.type == "double":
            px, py = self.calculateParallelLines()
            if px:
                painter.drawLine(
                    QLine(
                        self.line.x1() + constants["bond_distance"] * px,
                        self.line.y1() + constants["bond_distance"] * py,
                        self.line.x2() + constants["bond_distance"] * px,
                        self.line.y2() + constants["bond_distance"] * py,
                    )
                )
                painter.drawLine(
                    QLine(
                        self.line.x1() - constants["bond_distance"] * px,
                        self.line.y1() - constants["bond_distance"] * py,
                        self.line.x2() - constants["bond_distance"] * px,
                        self.line.y2() - constants["bond_distance"] * py,
                    )
                )
        elif self.type == "triple":
            px, py = self.calculateParallelLines()
            if px:
                painter.drawLine(self.line)
                painter.drawLine(
                    QLine(
                        self.line.x1() + constants["bond_distance"] * px,
                        self.line.y1() + constants["bond_distance"] * py,
                        self.line.x2() + constants["bond_distance"] * px,
                        self.line.y2() + constants["bond_distance"] * py,
                    )
                )
                painter.drawLine(
                    QLine(
                        self.line.x1() - constants["bond_distance"] * px,
                        self.line.y1() - constants["bond_distance"] * py,
                        self.line.x2() - constants["bond_distance"] * px,
                        self.line.y2() - constants["bond_distance"] * py,
                    )
                )

        elif self.type == "aromatic":
            px, py = self.calculateParallelLines()
            if px:
                painter.drawLine(
                    QLine(
                        self.line.x1() - constants["bond_distance"] * px,
                        self.line.y1() - constants["bond_distance"] * py,
                        self.line.x2() - constants["bond_distance"] * px,
                        self.line.y2() - constants["bond_distance"] * py,
                    )
                )
                dotted_line = QLine(
                    self.line.x1() + constants["bond_distance"] * px,
                    self.line.y1() + constants["bond_distance"] * py,
                    self.line.x2() + constants["bond_distance"] * px,
                    self.line.y2() + constants["bond_distance"] * py,
                )

                dotted_pen = QPen(LINE_COLOR, constants["line_width"], Qt.DotLine)
                painter.setPen(dotted_pen)
                painter.drawLine(dotted_line)

        elif self.type == "solid unwedge":
            pen = QPen(LINE_COLOR, int(constants["line_width"] * 1.5), Qt.SolidLine)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(self.line)

        elif self.type == "solid wedge":
            start_point = self.line.p1()
            end_point = self.line.p2()

            # Calculate the number of segments
            num_segments = 30
            dx = end_point.x() - start_point.x()
            dy = end_point.y() - start_point.y()

            max_pen_width = constants["max_width"]
            min_pen_width = 1

            for i in range(num_segments):
                # Calculate start and end points of this segment
                fraction_start = i / num_segments
                fraction_end = (i + 1) / num_segments
                segment_start = QPoint(
                    start_point.x() + fraction_start * dx,
                    start_point.y() + fraction_start * dy,
                )
                segment_end = QPoint(
                    start_point.x() + fraction_end * dx,
                    start_point.y() + fraction_end * dy,
                )

                pen_width = min_pen_width + (max_pen_width - min_pen_width) * (
                    i / num_segments
                )
                pen = QPen(LINE_COLOR, pen_width, Qt.SolidLine)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)

                # Draw the segment
                painter.drawLine(segment_start, segment_end)

        elif self.type == "dashed wedge":
            pen = QPen(LINE_COLOR, int(constants["line_width"] * 0.8), Qt.SolidLine)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            start_point = self.line.p1()
            end_point = self.line.p2()

            min_length = 1
            max_length = constants["max_width"]
            num_lines = constants["segment_number"]

            # Calculate the direction of the main line
            dx = end_point.x() - start_point.x()
            dy = end_point.y() - start_point.y()

            for i in range(num_lines):
                fraction = i / (num_lines - 1)

                # Position along the main line
                x = start_point.x() + fraction * dx
                y = start_point.y() + fraction * dy

                # Length of the perpendicular line at this point
                perp_length = min_length + fraction * (max_length - min_length)

                # Calculate start and end points of the perpendicular line
                angle = math.atan2(dy, dx) + math.pi / 2  # Rotate by 90 degrees
                dx_perp = math.cos(angle) * perp_length / 2
                dy_perp = math.sin(angle) * perp_length / 2
                perp_start = QPoint(x - dx_perp, y - dy_perp)
                perp_end = QPoint(x + dx_perp, y + dy_perp)

                painter.drawLine(perp_start, perp_end)
