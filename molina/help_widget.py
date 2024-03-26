from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QScrollArea, 
    QWidget, 
    QLabel, 
    QSpacerItem, 
    QSizePolicy,
    QLineEdit,
)


class HelpWindow(QDialog):
    """Help window describes abilities of applications. 
    Here user can change hotkeys for atoms.
    """
    def __init__(self, hotkeys):
        super().__init__()
        self.setWindowTitle("Help")
        self.layout = QVBoxLayout()
        self.scroll_area = QScrollArea(self)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # Get current hotkeys
        self.hotkeys = hotkeys
        self.map_keys = self.hotkeys.getHotkeys()

        # Common text at the beginning
        self.formatted_text = """
        <h1>Welcome to the Help Page</h1>
        <p style='font-size: 14px;'>In MOLInA, you can annotate your chemical 
        structures using hotkeys. To do so, press the appropriate key on your keyboard as 
        described, and then click with any mouse button to initiate the action. 
        Some hotkeys you can edit, press Enter to save new value for hotkey.</p>

        <p><i><b>Actions</b></i></p>
        <p style='text-indent: 20px;'><b>Left mouse button</b> — add bond or atom </p>
        <p style='text-indent: 20px;'><b>Right mouse button</b> — delete bond or atom </p>

        <p><i><b>Hotkeys</b></i></p>
        <p style='text-indent: 20px;'><b>CTRL+Z:</b> undo an action </p>

        <p style='text-indent: 20px;'><b>W:</b></b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; write any atom or group </p>
        """
        
        self.intro_label = QLabel(self.formatted_text)
        self.intro_label.setWordWrap(True)
        self.intro_label.setMaximumWidth(750)
        self.content_layout.addWidget(self.intro_label)
        
        # Create label and line edit for each key-value pair
        self.edit_fields = {}
        self.margin = 20
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        for key, value in self.map_keys.items():
            row_layout = QHBoxLayout()
            
            key_label = QLabel(f"{key}:")
            key_label.setFixedWidth(30 + self.margin)
            key_label.setStyleSheet(f"font-weight: bold; margin-left: {self.margin}px;")
            
            if key.isalpha():
                value = QLineEdit(value[1])
                value.returnPressed.connect(lambda key=key: self.onReturnPressed(key))
                self.edit_fields[key] = value
            else:
                value = QLabel(f"{value[1]} bond")
            
            value.setMaximumWidth(150)
            row_layout.addWidget(key_label, 0)
            row_layout.addWidget(value, 0)
           
            row_layout.addSpacerItem(self.spacer)
            self.content_layout.addLayout(row_layout)

        # Common text at the end
        self.formatted_text_end = """
        <p>If pressing a keyboard key and clicking a mouse button simultaneously 
        do not produce the expected result, check your keyboard layout settings.

        Atom font style does not affect the result. Mouse click position is more important for annotation.</p>
        """

        self.outro_label = QLabel(self.formatted_text_end)
        self.outro_label.setWordWrap(True)
        self.outro_label.setMaximumWidth(750)
        self.content_layout.addWidget(self.outro_label)

        self.setLayout(self.layout)
        self.setMaximumSize(600, 300)

        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

    def onReturnPressed(self, key) -> None:
        """ When Enter is pressed value for hotkeys saves and the focus is reset """
        value_edit = self.edit_fields[key]
        new_value = value_edit.text()
        self.hotkeys.setNewValue(key, new_value)
        value_edit.clearFocus()
