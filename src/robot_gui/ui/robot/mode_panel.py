from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton


class ModePanel(QGroupBox):
    mode_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__("Control Mode", parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        self.manual_button = QPushButton("Manual")
        self.auto_button = QPushButton("Automatic")
        self.manual_button.setCheckable(True)
        self.auto_button.setCheckable(True)
        self.manual_button.setChecked(True)
        self.manual_button.clicked.connect(lambda: self.set_manual(True))
        self.auto_button.clicked.connect(lambda: self.set_manual(False))
        layout.addWidget(self.manual_button)
        layout.addWidget(self.auto_button)

    def set_manual(self, manual=True):
        self.manual_button.setChecked(manual)
        self.auto_button.setChecked(not manual)
        self._update_style()
        self.mode_changed.emit(manual)

    def _update_style(self):
        selected = """
            QPushButton { background-color: #2e7d32; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #388e3c; }
        """
        self.manual_button.setStyleSheet(selected if self.manual_button.isChecked() else "")
        self.auto_button.setStyleSheet(selected if self.auto_button.isChecked() else "")

    def is_manual(self):
        return self.manual_button.isChecked()
