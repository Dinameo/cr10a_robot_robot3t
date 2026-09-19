from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QSlider, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGroupBox,
)


class JointRow(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.label = QLabel(name)
        self.label.setFixedWidth(65)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.value = QLineEdit("0°")
        self.value.setFixedWidth(65)
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setReadOnly(True)
        self.slider.valueChanged.connect(lambda value: self.value.setText(f"{value}°"))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)
        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value)


class JointPanel(QGroupBox):
    joint_changed = Signal(int, int)
    joint_released = Signal(int, int)
    home_clicked = Signal()
    stop_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Joint Control", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(2)

        self.joints = []
        for i in range(1, 7):
            row = JointRow(f"Joint {i}")
            self.joints.append(row)
            layout.addWidget(row)
            row.slider.sliderReleased.connect(
                lambda index=i - 1, r=row: self.joint_released.emit(
                    index, r.slider.value()
                )
            )

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.home_button = QPushButton("Home")
        self.stop_button = QPushButton("STOP")
        self.home_button.clicked.connect(self.home_clicked)
        self.stop_button.clicked.connect(self.stop_clicked)
        buttons.addWidget(self.home_button)
        buttons.addWidget(self.stop_button)
        layout.addSpacing(8)
        layout.addLayout(buttons)

    def values(self):
        return [joint.slider.value() for joint in self.joints]

    def set_values(self, values):
        for row, value in zip(self.joints, values):
            value = max(row.slider.minimum(), min(row.slider.maximum(), int(value)))
            row.slider.setValue(value)

    def set_limits(self, limits):
        for row, (minimum, maximum) in zip(self.joints, limits):
            lo = int(round(minimum))
            hi = int(round(maximum))
            if lo > hi:
                lo, hi = hi, lo
            row.slider.setRange(lo, hi)
            row.slider.setValue(max(lo, min(hi, row.slider.value())))
            row.slider.setEnabled(True)
