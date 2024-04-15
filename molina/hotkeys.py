from typing import Dict

from PySide6.QtCore import Qt, Signal, QObject


class Hotkeys(QObject):
    """
    Class for saving information about hotkeys.
    It returns actual values and changes some values if user rewrite it in HelpWindow
    """

    mapUpdate = Signal(dict)
    _instance = None
    _is_init = False

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Hotkeys, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._is_init:
            return
        super(Hotkeys, self).__init__()
        self._is_init = True
        self._map_keys = {
            "C": ("point", "C"),
            "N": ("point", "N"),
            "O": ("point", "O"),
            "I": ("point", "I"),
            "S": ("point", "S"),
            "F": ("point", "F"),
            "K": ("point", "K"),
            "L": ("point", "L"),
            "R": ("point", "Ru"),
            "Y": ("point", "Y"),
            "P": ("point", "P"),
            "A": ("point", "A"),
            "G": ("point", "Ga"),
            "Z": ("point", "Zn"),
            "V": ("point", "V"),
            "B": ("point", "B"),
            "M": ("point", "Mn"),
            "1": ("line", "single"),
            "2": ("line", "double"),
            "3": ("line", "triple"),
            "4": ("line", "aromatic"),
            "5": ("line", "solid wedge"),
            "6": ("line", "solid unwedge"),
            "7": ("line", "dashed wedge"),
            #   "8": ("line", "hydrogen"),
            #   "9": ("line", "dative"),
        }

    def getHotkeys(self) -> Dict:
        """Return hotkeys"""
        return self._map_keys.copy()

    def setNewValue(self, key, value) -> None:
        """Change value for key"""
        self._map_keys[key] = (self._map_keys[key][0], value)
        self.mapUpdate.emit(self._map_keys.copy())
