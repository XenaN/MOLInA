from PySide6.QtCore import Signal

from molina.drawing_widget import DrawingWidget
from molina.data_structs import Dataset


class DataManager:
    """
    DataManager managers the exchange of information between DrawingWidget and Dataset.
    DrawingWidget needs coordinates, image size, types of bonds and atoms.
    Dataset stores coordinates in fractions and indices of atoms between which there is a bond.
    Also it save types of atoms and bonds.
    """
    def __init__(self):
        pass