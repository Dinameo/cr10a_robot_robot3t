from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QCamera, QCameraDevice, QMediaCaptureSession, QMediaDevices, QVideoSink


class CameraBackend(QObject):
    frame_ready = Signal(QImage)
    connected = Signal(str)
    disconnected = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = None
        self.camera_device = None
        self.capture_session = QMediaCaptureSession(self)
        self.video_sink = QVideoSink(self)
        self.capture_session.setVideoSink(self.video_sink)
        self.video_sink.videoFrameChanged.connect(self._on_frame)
        self._connection_notified = False

    @staticmethod
    def available_cameras():
        return QMediaDevices.videoInputs()

    def connect_camera(self, camera_device: QCameraDevice):
        if camera_device is None:
            self.error.emit("Camera không hợp lệ.")
            return False
        self.disconnect_camera()
        try:
            self.camera_device = camera_device
            self.camera = QCamera(camera_device, self)
            self._connection_notified = False
            self.camera.activeChanged.connect(self._on_camera_active_changed)
            self.camera.errorOccurred.connect(self._on_camera_error)
            self.capture_session.setCamera(self.camera)
            self.camera.start()
            return True
        except Exception as exc:
            self.camera = None
            self.camera_device = None
            self.error.emit(f"Không thể kết nối camera: {exc}")
            return False

    @Slot()
    def disconnect_camera(self):
        was_connected = self.camera is not None or self.camera_device is not None
        if self.camera is not None:
            self.camera.stop()
            self.capture_session.setCamera(None)
            self.camera.deleteLater()
            self.camera = None
        self.camera_device = None
        self._connection_notified = False
        if was_connected:
            self.disconnected.emit()

    @Slot(bool)
    def _on_camera_active_changed(self, active):
        if active and self.camera is not None and not self._connection_notified:
            self._connection_notified = True
            self.connected.emit(self.camera.cameraDevice().description())

    @Slot(object, str)
    def _on_camera_error(self, _error, error_string):
        self._connection_notified = False
        self.error.emit(f"Không thể kết nối camera: {error_string}")

    @Slot(object)
    def _on_frame(self, frame):
        if not frame.isValid():
            return
        image = frame.toImage()
        if not image.isNull():
            self.frame_ready.emit(image.copy())
