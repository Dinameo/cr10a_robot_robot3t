from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel


class ActualPositionPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Actual Joint Position", parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(6)

        self.values = []
        for index in range(6):
            name = QLabel(f"Joint {index + 1}")
            value = QLabel("0.00°")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value.setMinimumWidth(80)
            layout.addWidget(name, index, 0)
            layout.addWidget(value, index, 1)
            self.values.append(value)

    def set_values(self, positions):
        for label, position in zip(self.values, positions):
            label.setText(f"{float(position):.2f}°")
