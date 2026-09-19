from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)

from robot_gui.ui.styles import DIALOG_STYLE


class GazeboDialog(QDialog):

    def __init__(
        self,
        current_control_topic="",
        current_joint_state_topic="",
        robot_infos=None,
        parent=None
    ):
        super().__init__(parent)

        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowTitle("Connect Gazebo")
        self.resize(520, 380)

        self.selected_control_topic = ""
        self.selected_joint_state_topic = ""
        self.discovery_mode = robot_infos is not None
        self.robot_infos = list(robot_infos or [])

        layout = QVBoxLayout(self)

        self.robot_list = None
        if self.discovery_mode:
            title = QLabel("Robot khả dụng")
            title.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(title)
            layout.addWidget(
                QLabel("Chọn một robot đang online để bắt đầu kết nối.")
            )
            self.robot_list = QListWidget()
            self.robot_list.setStyleSheet(
                "QListWidget { padding: 6px; }"
                "QListWidget::item { padding: 10px; margin: 3px 0; }"
                "QListWidget::item:selected { background: #4a6572; }"
            )
            layout.addWidget(self.robot_list, 1)
            for info in self.robot_infos:
                self.robot_list.addItem(self._robot_display_text(info))
            if not self.robot_infos:
                self.robot_list.addItem("Đang quét...")
            self.robot_list.currentRowChanged.connect(
                self._select_robot
            )
            self.discovery_count_label = QLabel(
                f"{len(self.robot_infos)} robot được tìm thấy"
            )
            layout.addWidget(self.discovery_count_label)

        # ==================================================
        # CONTROL TOPIC
        # ==================================================

        self.control_title = QLabel("Control topic:")
        self.control_title.setStyleSheet(
            "font-weight: bold;"
        )

        layout.addWidget(self.control_title)

        self.control_topic_edit = QLineEdit(
            current_control_topic
        )

        self.control_topic_edit.setPlaceholderText(
            "/arm_controller/joint_trajectory"
        )

        layout.addWidget(
            self.control_topic_edit
        )

        self.control_info = QLabel(
            "Đây là một ROS 2 Action Server "
            "(control_msgs/action/FollowJointTrajectory)\n"
            "do controller_manager trong Gazebo cung cấp — "
            "KHÔNG phải topic thông thường."
        )

        self.control_info.setStyleSheet(
            "color: #aaaaaa;"
        )

        layout.addWidget(self.control_info)

        # ==================================================
        # JOINT STATE TOPIC
        # ==================================================

        self.joint_state_title = QLabel(
            "Joint state topic:"
        )

        self.joint_state_title.setStyleSheet(
            "font-weight: bold;"
        )

        layout.addWidget(self.joint_state_title)

        self.joint_state_topic_edit = QLineEdit(
            current_joint_state_topic
        )

        self.joint_state_topic_edit.setPlaceholderText(
            "/joint_states"
        )

        if self.discovery_mode and self.robot_infos:
            self._select_robot(0)

        layout.addWidget(
            self.joint_state_topic_edit
        )

        self.joint_state_info = QLabel(
            "Topic đọc góc hiện tại của các khớp robot."
        )

        self.joint_state_info.setStyleSheet(
            "color: #aaaaaa;"
        )

        if self.discovery_mode:
            self._set_manual_fields_visible(False)
            self.control_topic_edit.setReadOnly(True)
            self.joint_state_topic_edit.setReadOnly(True)

        layout.addWidget(
            self.joint_state_info
        )

        # ==================================================
        # BUTTONS
        # ==================================================

        buttons = QHBoxLayout()

        self.exit_button = QPushButton(
            "Thoát"
        )

        self.connect_button = QPushButton(
            "Kết nối robot"
        )

        self.connect_button.setDefault(
            True
        )

        if self.discovery_mode:
            self.manual_button = QPushButton("Nhập topic thủ công")
            self.manual_button.clicked.connect(self._show_manual_fields)
            buttons.addWidget(self.manual_button)

        buttons.addStretch()

        buttons.addWidget(
            self.exit_button
        )

        buttons.addWidget(
            self.connect_button
        )

        layout.addLayout(
            buttons
        )

        # ==================================================
        # SIGNALS
        # ==================================================

        self.exit_button.clicked.connect(
            self.reject
        )

        self.connect_button.clicked.connect(
            self.connect_topics
        )

    def _select_robot(self, row):
        if row < 0 or row >= len(self.robot_infos):
            return
        info = self.robot_infos[row]
        self.control_topic_edit.setText(
            info.get("control_action_topic", "")
        )
        self.joint_state_topic_edit.setText(
            info.get("joint_state_topic", "")
        )

    def _set_manual_fields_visible(self, visible):
        for widget in (
            self.control_title,
            self.control_topic_edit,
            self.control_info,
            self.joint_state_title,
            self.joint_state_topic_edit,
            self.joint_state_info,
        ):
            widget.setVisible(visible)

    def _show_manual_fields(self):
        self._set_manual_fields_visible(True)
        self.control_topic_edit.setReadOnly(False)
        self.joint_state_topic_edit.setReadOnly(False)
        self.manual_button.setVisible(False)

    def add_robot_info(self, info):
        if not self.discovery_mode:
            return
        key = (
            info.get("robot_info_topic"),
            info.get("model") or info.get("name"),
            info.get("control_action_topic"),
            info.get("joint_state_topic"),
        )
        for index, current in enumerate(self.robot_infos):
            current_key = (
                current.get("robot_info_topic"),
                current.get("model") or current.get("name"),
                current.get("control_action_topic"),
                current.get("joint_state_topic"),
            )
            if current_key == key:
                return
        if self.robot_list.count() == 1 and self.robot_list.item(0).text() == "Đang quét...":
            self.robot_list.clear()
        self.robot_infos.append(dict(info))
        self.robot_list.addItem(self._robot_display_text(info))
        self.discovery_count_label.setText(
            f"{len(self.robot_infos)} robot được tìm thấy"
        )
        self.robot_list.setCurrentRow(self.robot_list.count() - 1)

    @staticmethod
    def _robot_display_text(info):
        robot_id = info.get("robot_id") or "?"
        model_name = info.get("model") or info.get("model_name") or "?"
        dof = info.get("dof", "?")
        return (
            f"Robot ID: {robot_id}\n"
            f"Model: {model_name}  |  DOF: {dof}"
        )

    def remove_robot_info(self, topic_name):
        if not self.discovery_mode:
            return
        for index, info in enumerate(self.robot_infos):
            if info.get("robot_info_topic") != topic_name:
                continue
            self.robot_infos.pop(index)
            self.robot_list.takeItem(index)
            break
        if not self.robot_infos:
            self.robot_list.addItem("Đang quét...")
        self.discovery_count_label.setText(
            f"{len(self.robot_infos)} robot được tìm thấy"
        )

    # ======================================================
    # CONNECT
    # ======================================================

    def connect_topics(self):

        control_topic = (
            self.control_topic_edit
            .text()
            .strip()
        )

        joint_state_topic = (
            self.joint_state_topic_edit
            .text()
            .strip()
        )

        if not control_topic:
            return

        if not joint_state_topic:
            return

        self.selected_control_topic = (
            control_topic
        )

        self.selected_joint_state_topic = (
            joint_state_topic
        )

        self.accept()