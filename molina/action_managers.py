from typing import Any, List


class FileActionManager:
    """
    A class used to track recently open image files

    recent_images: list
        list of image paths
    """

    def __init__(self):
        self.recent_images = []

    def addRecentImage(self, image_path: str) -> None:
        """
        Adding recent images and remove the oldest image
        if recent_images is biggerS than 10

        :param image_path: path to chosen image
        """
        if image_path in self.recent_images:
            self.recent_images.remove(image_path)

        self.recent_images.insert(0, image_path)

        if len(self.recent_images) > 10:
            self.recent_images.pop()

    def getRecentImages(self) -> List:
        """Get list of image paths

        :return: list of image path
        """
        return self.recent_images


class DrawingActionManager:
    """
    This class saves a sequence of operations in the drawing widget for using
    ctrl+z combination to cancel the last (several) action

    widget: DrawingWidget
            class for drawing
    action_history: list
            list of operations (add, delete, clean)
    max_actions: int
            maximum of actions which contain action_history
    """

    def __init__(self, widget):
        self.widget = widget
        self.action_history = []
        self.max_actions = 15
        self._map_actions = {
            "add_atom": self.widget.undoAddAtom,
            "delete_atom": self.widget.undoDeleteAtom,
            "add_bond": self.widget.undoAddBond,
            "delete_bond": self.widget.undoDeleteBond,
            "delete_atom_and_bond": self.widget.undoDeleteAtomAndBond,
            "move_atom": self.widget.undoUpdateAtomPosition,
        }

    def addAction(self, data: Any, action_type: str) -> None:
        """Add a new action to action_history and remove the oldest action
        if action_history is bigger than max_actions

        :param id: list of unique indexes or one unique index
        :param action_type: type of action
        """
        if len(self.action_history) >= self.max_actions:
            self.action_history.pop(0)
        self.action_history.append({"type": action_type, "data": data})

    def undo(self) -> None:
        """Call undo function due to last action"""

        if self.action_history:
            last_action = self.action_history.pop()
            action_type = last_action["type"]
            data = last_action["data"]

            self._map_actions[action_type](data)
