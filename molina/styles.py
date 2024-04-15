from PySide6.QtGui import QColor


FOCUSED = "#73738c"
UNFOCUSED = "#AEC6CF"
COLOR_BACKGROUND_WIDGETS = QColor(250, 250, 250)

SCROLLBAR_STYLE = """
QScrollBar:vertical, QScrollBar:horizontal {
    border: none;
    background: white;
    width: 10px;  
    height: 10px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #b5b5b5; 
    min-height: 20px; 
    min-width: 20px;
    border-radius: 4px; 
}

QScrollBar::add-line:vertical, QScrollBar::add-line:horizontal,
QScrollBar::sub-line:vertical, QScrollBar::sub-line:horizontal {
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:horizontal,
QScrollBar::add-page:vertical, QScrollBar::sub-page:horizontal {
    background: none;
}
QTreeView  { border: none; }
"""

TOOLBAR_STYLE = """
    QToolBar {
        padding-top: 5px;   
        padding-bottom: 5px; 
        spacing: 5px;
    }

"""
TEXT_STYLE = f"""
            QTextEdit {{
                border: 2px solid {UNFOCUSED};
                border-radius: 10px;
                padding: 5px;
                background-color: white
            }}
            QTextEdit:focus {{
                border: 2px solid {FOCUSED}; 
            }}
        """
