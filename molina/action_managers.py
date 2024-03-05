class FileActionManager:
    def __init__(self):
        self.recent_images = []
    
    def addRecentImage(self, image_path: str):
        if image_path in self.recent_images:
            self.recent_images.remove(image_path)

        self.recent_images.insert(0, image_path)

    def getRecentImages(self):
        return self.recent_images

class DrawingActionManager:
    def __init__(self, widget):
        self.widget = widget
        self.action_history = []
        self.max_actions = 15

    def addAction(self, action, action_type):
        if len(self.action_history) >= self.max_actions:
            self.action_history.pop(0)
        self.action_history.append({'type': action_type, 'data': action})

    def undo(self):
        if self.action_history:
            last_action = self.action_history.pop()
            action_type = last_action['type']
            data = last_action['data']

            if action_type == 'add_point':
                # Undo add_point by removing the last point
                self.widget.deletePoint(False)
            elif action_type == 'delete_point':
                # Undo delete_point by re-adding the point
                self.widget.addPoint(data, False)
            elif action_type == 'add_line':
                # Undo add_line by removing the last line
                self.widget.deleteLine(-1, False)
            elif action_type == 'delete_line':
                # Undo delete_line by re-adding the line
                self.widget.addLine(data, False)
            elif action_type == 'clear_all':
                self.widget.updateCoordinates(data, True)
            elif action_type == 'delete_point_and_lines': 
                self.widget.undoDeletePointAndLines(data)