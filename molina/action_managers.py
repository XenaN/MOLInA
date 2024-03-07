from typing import Union, List

class FileActionManager:
    def __init__(self):
        self.recent_images = []
    
    def addRecentImage(self, image_path: str):
        if image_path in self.recent_images:
            self.recent_images.remove(image_path)

        self.recent_images.insert(0, image_path)
    
        if len(self.recent_images) > 10:
            self.recent_images.pop()

    def getRecentImages(self) -> List:
        return self.recent_images

class DrawingActionManager:
    def __init__(self, widget):
        self.widget = widget
        self.action_history = []
        self.max_actions = 15

    def addAction(self, id: Union[List, int], action_type):
        if len(self.action_history) >= self.max_actions:
            self.action_history.pop(0)
        self.action_history.append({"type": action_type, "data": id})

    def undo(self):
        if self.action_history:
            last_action = self.action_history.pop()
            action_type = last_action["type"]
            data = last_action["data"]

            if action_type == "add_atom":
                # Undo add_point by removing the last point
                self.widget.undoAddAtom(data)
            elif action_type == "delete_atom":
                # Undo delete_point by re-adding the point
                self.widget.undoDeleteAtom(data)
            elif action_type == "add_bond":
                # Undo add_line by removing the last line
                self.widget.undoAddBond(data)
            elif action_type == "delete_bond":
                # Undo delete_line by re-adding the line
                self.widget.undoDeleteBond(data)
            elif action_type == "delete_atom_and_bond":
                self.widget.undoDeleteAtomAndBond(data)

