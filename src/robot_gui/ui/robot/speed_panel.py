from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton


class SpeedPanel(QGroupBox):
    speed_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Speed Override", parent)
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        label = QLabel("Speed")
        label.setFixedWidth(45)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.value_label = QLabel("50 %")
        self.value_label.setFixedWidth(50)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.slider.valueChanged.connect(self._on_changed)
        row.addWidget(label)
        row.addWidget(self.slider, 1)
        row.addWidget(self.value_label)
        layout.addLayout(row)

        presets = QHBoxLayout()
        for value in [10, 25, 50, 75, 100]:
            button = QPushButton(f"{value}%")
            button.clicked.connect(lambda checked=False, v=value: self.slider.setValue(v))
            presets.addWidget(button)
        layout.addLayout(presets)

    def _on_changed(self, value):
        self.value_label.setText(f"{value} %")
        self.speed_changed.emit(value)

    def value(self):
        return self.slider.value()
