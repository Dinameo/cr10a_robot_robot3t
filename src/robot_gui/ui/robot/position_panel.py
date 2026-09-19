from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QGroupBox, QGridLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout


class PositionPanel(QGroupBox):
    move_clicked = Signal(dict)
    clear_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Position Control", parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)
        self.inputs = {}
        fields = [("X", 0, 0), ("Y", 1, 0), ("Z", 2, 0),
                  ("Roll", 0, 2), ("Pitch", 1, 2), ("Yaw", 2, 2)]
        for name, row, col in fields:
            label = QLabel(name)
            label.setFixedWidth(45)
            edit = QLineEdit()
            edit.setPlaceholderText("0.0")
            edit.setAlignment(Qt.AlignCenter)
            edit.setMinimumWidth(90)
            layout.addWidget(label, row, col)
            layout.addWidget(edit, row, col + 1)
            self.inputs[name] = edit
        buttons = QHBoxLayout()
        self.move_button = QPushButton("Move")
        self.clear_button = QPushButton("Clear")
        buttons.setSpacing(10)
        self.move_button.clicked.connect(self._move)
        self.clear_button.clicked.connect(self._clear)
        buttons.addWidget(self.move_button)
        buttons.addWidget(self.clear_button)
        layout.addLayout(buttons, 3, 0, 1, 4)

    def _move(self):
        data = {}
        for name, edit in self.inputs.items():
            text = edit.text().strip()
            if text == "":
                data[name] = 0.0
            else:
                try:
                    data[name] = float(text)
                except ValueError:
                    data[name] = None
        self.move_clicked.emit(data)

    def _clear(self):
        for edit in self.inputs.values():
            edit.clear()
        self.clear_clicked.emit()
