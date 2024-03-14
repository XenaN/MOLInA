from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser


class HelpWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help")
        layout = QVBoxLayout()

        text_browser = QTextBrowser(self)

        formatted_text = """
        <h1>Welcome to the Help Page</h1>
        <p style='font-size: 14px;'>In MOLInA, you have the ability to annotate your chemical 
        structures using hotkeys. To do so, press the appropriate key on your keyboard as 
        described, and then click with any mouse button to initiate the action</p>

        <p><i><b>Actions</b></i></p>
        <p style='text-indent: 20px;'><b>Left mouse button</b> — add bond or atom </p>
        <p style='text-indent: 20px;'><b>Right mouse button</b> — delete bond or atom </p>

        <p><i><b>Hotkeys</b></i></p>
        <p style='text-indent: 20px;'><b>CTRL+Z</b> — undo an action </p>

        <p style='text-indent: 20px;'><b>C</b> — add C </p>
        <p style='text-indent: 20px;'><b>N</b> — add N </p>
        <p style='text-indent: 20px;'><b>O</b> — add O </p>
        <p style='text-indent: 20px;'><b>I</b> — add I </p>
        <p style='text-indent: 20px;'><b>S</b> — add S </p>
        <p style='text-indent: 20px;'><b>F</b> — add F </p>
        <p style='text-indent: 20px;'><b>K</b> — add K </p>
        <p style='text-indent: 20px;'><b>L</b> — add Li </p>
        <p style='text-indent: 20px;'><b>R</b> — add Ru </p>
        <p style='text-indent: 20px;'><b>Y</b> — add Y </p>
        <p style='text-indent: 20px;'><b>P</b> — add P </p>
        <p style='text-indent: 20px;'><b>A</b> — add Al </p>
        <p style='text-indent: 20px;'><b>G</b> — add Ga </p>
        <p style='text-indent: 20px;'><b>Z</b> — add Zn </p>
        <p style='text-indent: 20px;'><b>V</b> — add V </p>
        <p style='text-indent: 20px;'><b>B</b> — add B </p>
        <p style='text-indent: 20px;'><b>M</b> — add Mn </p>

        <p style='text-indent: 20px;'><b>W</b> — write any atom or group </p>

        <p style='text-indent: 20px;'><b>1</b> — add single bond </p>
        <p style='text-indent: 20px;'><b>2</b> — add double bond </p>
        <p style='text-indent: 20px;'><b>3</b> — add triple bond </p>
        <p style='text-indent: 20px;'><b>4</b> — add aromatic bond </p>
        <p style='text-indent: 20px;'><b>5</b> — add up bond </p>
        <p style='text-indent: 20px;'><b>6</b> — add wide bond </p>
        <p style='text-indent: 20px;'><b>7</b> — add down bond </p>

        <p>If pressing a keyboard key and clicking a mouse button simultaneously 
        do not produce the expected result, check your keyboard layout settings.

        Atom font style does not affect the result. Mouse click position is more important for annotation.</p>
        """

        text_browser.setHtml(formatted_text)
        layout.addWidget(text_browser)

        self.setLayout(layout)
        self.resize(600, 300)