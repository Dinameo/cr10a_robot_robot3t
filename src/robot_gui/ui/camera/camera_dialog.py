from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout

from robot_gui.ui.styles import DIALOG_STYLE


class CameraDialog(QDialog):
    log_message = Signal(str)

    def __init__(self, cameras, parent=None):
        super().__init__(parent)
        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowTitle("Connect Camera")
        self.resize(520, 360)
        self.selected_camera = None
        layout = QVBoxLayout(self)
        title = QLabel("Camera trên máy:")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        self.camera_list = QListWidget()
        self.camera_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.camera_list, 1)
        buttons = QHBoxLayout()
        self.exit_button = QPushButton("Thoát")
        self.connect_button = QPushButton("Connect")
        self.connect_button.setDefault(True)
        buttons.addStretch()
        buttons.addWidget(self.exit_button)
        buttons.addWidget(self.connect_button)
        layout.addLayout(buttons)
        self.exit_button.clicked.connect(self.reject)
        self.connect_button.clicked.connect(self.connect_camera)
        self.camera_list.itemDoubleClicked.connect(lambda item: self.connect_camera())
        self.load_cameras(cameras)

    def load_cameras(self, cameras):
        self.camera_list.clear()
        if not cameras:
            item = QListWidgetItem("Không tìm thấy camera")
            item.setFlags(Qt.NoItemFlags)
            self.camera_list.addItem(item)
            self.connect_button.setEnabled(False)
            self.log_message.emit("Không tìm thấy camera.")
            return
        for index, camera in enumerate(cameras):
            description = camera.description()
            device_id = bytes(camera.id()).decode("utf-8", errors="replace")
            text = f"{index}: {description}"
            if device_id:
                text += f"  [{device_id}]"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, camera)
            self.camera_list.addItem(item)
        self.camera_list.setCurrentRow(0)

    def connect_camera(self):
        item = self.camera_list.currentItem()
        if item is None:
            return
        camera = item.data(Qt.UserRole)
        if camera is None:
            return
        self.selected_camera = camera
        self.accept()
