from PySide6.QtCore import Qt
from PySide6.QtWidgets import QBoxLayout
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout

from robot_gui.backends.camera_backend import CameraBackend
from robot_gui.backends.gazebo_backend import GazeboBackend
from robot_gui.ui.camera.camera_panel import CameraPanel
from robot_gui.ui.camera.camera_dialog import CameraDialog
from robot_gui.ui.gazebo.gazebo_dialog import GazeboDialog
from robot_gui.ui.robot.joint_panel import JointPanel
from robot_gui.ui.robot.actual_position_panel import ActualPositionPanel
from robot_gui.ui.robot.speed_panel import SpeedPanel
from robot_gui.ui.robot.position_panel import PositionPanel
from robot_gui.ui.robot.mode_panel import ModePanel
from robot_gui.ui.log.log_panel import LogPanel
from robot_gui.ui.styles import MAIN_STYLE, CAMERA_LABEL_STYLE, STATUS_STYLE, LOG_STYLE, STOP_STYLE, MOVE_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("4 DOF Robot Control")
        self.resize(1400, 1000)
        self.setMinimumSize(1000, 600)

        self.camera_backend = CameraBackend(self)
        self.gazebo_backend = GazeboBackend(self)

        self.gazebo_control_topic = ""
        self.gazebo_joint_state_topic = ""

        self.current_camera = None
        self._updating_sliders = False

        self.camera_panel = CameraPanel()
        self.joint_panel = JointPanel()
        self.actual_position_panel = ActualPositionPanel()
        self.speed_panel = SpeedPanel()
        self.position_panel = PositionPanel()
        self.mode_panel = ModePanel()
        self.log_panel = LogPanel()

        self.setup_ui()
        self.setup_menu()
        self.connect_signals()
        self.setup_style()

        self.mode_panel.set_manual(True)
        self.log_panel.info("Chương trình khởi động. Chế độ Manual được chọn.")

    # ---------------------------------------------------------
    # UI composition
    # ---------------------------------------------------------
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        camera_column = QVBoxLayout()
        camera_column.setSpacing(12)
        camera_column.addWidget(self.camera_panel, 1)
        camera_column.addWidget(self.log_panel, 0)

        control_column = QVBoxLayout()
        control_column.setSpacing(12)
        control_column.addWidget(self.joint_panel)
        control_column.addWidget(self.actual_position_panel)
        control_column.addWidget(self.speed_panel)
        control_column.addWidget(self.position_panel)
        control_column.addWidget(self.mode_panel)
        control_column.addStretch()

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        top_layout.addLayout(camera_column, 3)
        top_layout.addLayout(control_column, 2)

        main_layout.addLayout(top_layout, 1)

    def setup_menu(self):
        menu_bar = self.menuBar()

        camera_menu = menu_bar.addMenu("Camera")
        camera_menu.addAction("Connect...", self.open_camera_dialog)
        camera_menu.addAction("Disconnect", self.disconnect_camera)

        gazebo_menu = menu_bar.addMenu("Gazebo")
        gazebo_menu.addAction("Connect...", self.open_gazebo_dialog)
        gazebo_menu.addAction("Disconnect", self.disconnect_gazebo)

        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.addAction("Settings...", self.open_settings)

    def connect_signals(self):
        # Camera
        self.camera_backend.frame_ready.connect(self.camera_panel.set_frame)
        self.camera_backend.connected.connect(self.on_camera_connected)
        self.camera_backend.disconnected.connect(self.on_camera_disconnected)
        self.camera_backend.error.connect(self.on_camera_error)

        # Gazebo
        self.gazebo_backend.robot_info_received.connect(self.on_robot_info)
        self.gazebo_backend.joint_state_received.connect(
            self.actual_position_panel.set_values
        )
        self.gazebo_backend.connected.connect(self.on_gazebo_connected)
        self.gazebo_backend.disconnected.connect(self.on_gazebo_disconnected)
        self.gazebo_backend.error.connect(self.on_gazebo_error)
        self.gazebo_backend.success.connect(self.log_panel.success)
        self.gazebo_backend.log.connect(self.log_panel.info)

        # Robot controls
        self.joint_panel.joint_released.connect(self.on_joint_changed)
        self.joint_panel.home_clicked.connect(self.on_home)
        self.joint_panel.stop_clicked.connect(self.on_stop)
        self.position_panel.move_clicked.connect(self.on_move)
        self.position_panel.clear_clicked.connect(lambda: self.log_panel.info("Đã xóa thông tin Position Control."))
        self.mode_panel.mode_changed.connect(self.on_mode_changed)

    # ---------------------------------------------------------
    # Camera
    # ---------------------------------------------------------
    def open_camera_dialog(self):
        dialog = CameraDialog(self.camera_backend.available_cameras(), self)
        dialog.log_message.connect(self.log_panel.warning)
        if dialog.exec() == QDialog.Accepted and dialog.selected_camera is not None:
            self.current_camera = dialog.selected_camera
            self.camera_backend.connect_camera(self.current_camera)

    def disconnect_camera(self):
        self.camera_backend.disconnect_camera()

    def on_camera_connected(self, description):
        self.camera_panel.set_connected(description)
        self.log_panel.success(f"Đã kết nối camera: {description}")

    def on_camera_disconnected(self):
        self.current_camera = None
        self.camera_panel.set_disconnected()
        self.log_panel.info("Đã ngắt kết nối camera.")

    def on_camera_error(self, message):
        self.camera_panel.set_error(message)
        self.log_panel.error(f"Camera: {message}")

    # ---------------------------------------------------------
    # Gazebo
    # ---------------------------------------------------------
    def open_gazebo_dialog(self):
        dialog = GazeboDialog(
            self.gazebo_control_topic,
            self.gazebo_joint_state_topic,
            list(self.gazebo_backend.discovered_robot_infos.values()),
            self
        )
        self.gazebo_backend.robot_info_received.connect(
            dialog.add_robot_info
        )
        self.gazebo_backend.robot_info_removed.connect(
            dialog.remove_robot_info
        )

        if dialog.exec() == QDialog.Accepted:

            control_topic = (
                dialog.selected_control_topic
            )

            joint_state_topic = (
                dialog.selected_joint_state_topic
            )

            if self.gazebo_backend.connect(
                control_topic,
                joint_state_topic
            ):

                self.gazebo_control_topic = (
                    control_topic
                )

                self.gazebo_joint_state_topic = (
                    joint_state_topic
                )

                self.log_panel.info(
                    f"Đang kết nối Gazebo: {control_topic}"
                )


    def disconnect_gazebo(self):

        self.gazebo_backend.disconnect()

        self.gazebo_control_topic = ""
        self.gazebo_joint_state_topic = ""

        self.log_panel.info(
            "Đang ngắt kết nối Gazebo..."
        )


    def on_gazebo_connected(self):

        lines = [
            "Đã kết nối Gazebo.",
            f"Control Action: {self.gazebo_control_topic}",
            f"Joint State Topic: {self.gazebo_joint_state_topic}",
        ]

        info = self.gazebo_backend.latest_robot_info

        if info:
            limits = list(
                zip(
                    info.get("min_angle_deg", []),
                    info.get("max_angle_deg", []),
                )
            )
            if len(limits) == 6:
                self.joint_panel.set_limits(limits)

            lines.append("--- Robot Info ---")
            lines.append(
                f"Model: {info.get('model', '?')}"
            )
            lines.append(
                f"DOF: {info.get('dof', '?')}"
            )
            joints = info.get("joints", [])
            speeds = info.get("max_speed_deg_s", [])
            min_angles = info.get("min_angle_deg", [])
            max_angles = info.get("max_angle_deg", [])
            unit = info.get("unit", "deg")

            if info.get("control_action_topic"):
                lines.append(
                    f"Control topic: {info['control_action_topic']}"
                )

            if info.get("joint_state_topic"):
                lines.append(
                    f"Joint state topic: {info['joint_state_topic']}"
                )

        self.log_panel.success(
            "\n".join(lines)
        )
        if info:
            rows = [
                (
                    name,
                    f"{speed:.1f} {unit}/s",
                    f"{lo:.1f} .. {hi:.1f} {unit}",
                )
                for name, speed, lo, hi in zip(
                    joints, speeds, min_angles, max_angles
                )
            ]
            self.log_panel.add_table(
                "SUCC",
                "Joint limits and speeds",
                ["Joint", "Max speed", "Angle range"],
                rows,
            )


    def on_gazebo_disconnected(self):

        self.gazebo_control_topic = ""
        self.gazebo_joint_state_topic = ""
        self.joint_panel.set_enabled(False)

        self.log_panel.info(
            "Đã ngắt kết nối Gazebo."
        )


    def on_gazebo_error(self, message):

        self.log_panel.error(
            message
        )

    def on_robot_info(self, info):

        try:

            limits = list(
                zip(
                    info["min_angle_deg"],
                    info["max_angle_deg"],
                )
            )

        except (KeyError, TypeError, ValueError):
            pass

    # ---------------------------------------------------------
    # Joint / manual control
    # ---------------------------------------------------------
    def on_joint_state_received(self, _positions):
        return

    def on_joint_changed(self, _index, _value):
        if self._updating_sliders or not self.mode_panel.is_manual():
            return
        self.publish_manual_command()

    def publish_manual_command(self):
        angles = self.joint_panel.values()
        speed = self.speed_panel.value()
        if not self.gazebo_control_topic:
            self.log_panel.error(
                "Không thể điều khiển robot: Gazebo chưa được kết nối."
            )
            return
        self.gazebo_backend.publish_joint_command(angles, speed)
        angle_text = ", ".join(str(x) for x in angles)
        self.log_panel.info(f"Gửi góc khớp [{angle_text}], tốc độ {speed}%.")

    def on_mode_changed(self, manual):
        if manual:
            self.log_panel.info("Chuyển sang chế độ Manual.")
        else:
            self.log_panel.info("Chuyển sang chế độ Automatic.")

    def on_home(self):
        if not self.gazebo_control_topic:
            self.log_panel.error(
                "Không thể Home robot: Gazebo chưa được kết nối."
            )
            return
        self.joint_panel.set_values([0] * 6)
        self.publish_manual_command()
        self.log_panel.info("Đã gửi lệnh Home.")

    def on_stop(self):
        if not self.gazebo_control_topic:
            self.log_panel.error("Không thể STOP robot: Gazebo chưa được kết nối.")
            return
        self.gazebo_backend.emergency_stop()
        self.log_panel.warning("Đã gửi lệnh dừng khẩn trajectory hiện tại.")

    def on_move(self, data):
        invalid = [name for name, value in data.items() if value is None]
        if invalid:
            self.log_panel.error(f"Giá trị không hợp lệ: {', '.join(invalid)}.")
            return
        self.log_panel.info(f"Yêu cầu Move: {data}")

    # ---------------------------------------------------------
    def open_settings(self):
        self.log_panel.info("Settings chưa được triển khai.")

    def setup_style(self):
        self.setStyleSheet(MAIN_STYLE)
        self.camera_panel.camera_label.setStyleSheet(CAMERA_LABEL_STYLE)
        self.camera_panel.camera_status.setStyleSheet(STATUS_STYLE)
        self.log_panel.output.setStyleSheet(LOG_STYLE)
        self.joint_panel.stop_button.setStyleSheet(STOP_STYLE)
        self.position_panel.move_button.setStyleSheet(MOVE_STYLE)
        self.mode_panel._update_style()

    def closeEvent(self, event):
        self.camera_backend.disconnect_camera()
        self.gazebo_backend.close()
        event.accept()


def run():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
