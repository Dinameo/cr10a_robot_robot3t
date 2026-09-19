from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy


class CameraPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Camera", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 10)
        self.camera_label = QLabel("Camera View")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(550, 450)
        self.camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.camera_label)
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.camera_status = QLabel("Disconnected")
        status_layout.addWidget(self.camera_status)
        status_layout.addStretch()
        layout.addLayout(status_layout)

    def set_frame(self, image):
        if image.isNull():
            return
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_label.setPixmap(scaled)

    def set_connected(self, description):
        self.camera_status.setText(f"Connected: {description}")

    def set_disconnected(self):
        self.camera_label.clear()
        self.camera_label.setText("Camera View")
        self.camera_status.setText("Disconnected")

    def set_error(self, message):
        self.camera_status.setText(f"Error: {message}")
