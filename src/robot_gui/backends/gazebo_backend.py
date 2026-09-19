import json
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)

from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

from PySide6.QtCore import (
    QObject,
    QThread,
    QTimer,
    Signal,
    Slot,
)


JOINT_NAMES = [
    "Joint1",
    "Joint2",
    "Joint3",
    "Joint4",
    "Joint5",
    "Joint6",
]

DEFAULT_ACTION = "/arm_controller/follow_joint_trajectory"
DEFAULT_JOINT_STATE_TOPIC = "/joint_states"


# ============================================================
# ROS WORKER
# ============================================================

class RosWorker(QObject):

    connected = Signal()
    disconnected = Signal()

    error = Signal(str)
    success = Signal(str)
    log = Signal(str)

    joint_state_received = Signal(list)

    robot_info_received = Signal(dict)
    robot_info_removed = Signal(str)

    def __init__(self):
        super().__init__()
        self.node = None

        self.action_client = None
        self.joint_state_sub = None
        self.robot_info_subscriptions = {}
        self.robot_info_republish_clients = {}
        self.spin_timer = None
        self.discovery_timer = None

        self.action_name = DEFAULT_ACTION
        self.joint_state_topic = DEFAULT_JOINT_STATE_TOPIC

        self.latest_positions = [0.0] * 6
        self.latest_robot_info = None
        self.discovered_robot_infos = {}

        self.received_joint_state = False
        self.running = False

    # --------------------------------------------------------
    # START ROS
    # --------------------------------------------------------

    @Slot()
    def start(self):

        try:

            if not rclpy.ok():
                rclpy.init()

            self.node = Node("robot_gui")

            self.running = True

            robot_qos = QoSProfile(
                history=QoSHistoryPolicy.KEEP_LAST,
                depth=1,
                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                reliability=QoSReliabilityPolicy.RELIABLE,
            )

            self.spin_timer = QTimer(self)
            self.spin_timer.timeout.connect(self._spin_once)
            self.spin_timer.start(50)
            self.discovery_timer = QTimer(self)
            self.discovery_timer.timeout.connect(
                lambda: self._scan_robot_info_topics(robot_qos)
            )
            self.discovery_timer.start(1000)
            self._scan_robot_info_topics(robot_qos)

            self.success.emit("ROS2 worker đã khởi động")

        except Exception as e:

            self.error.emit(
                f"Không thể khởi động ROS2: {e}"
            )

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    @Slot(str, str)
    def connect_robot(
        self,
        action_name,
        joint_state_topic
    ):

        try:

            if self.node is None:

                self.error.emit(
                    "ROS2 chưa được khởi tạo."
                )

                return

            self.action_name = action_name.strip()
            self.joint_state_topic = joint_state_topic.strip()

            if not self.action_name:
                self.error.emit(
                    "ROS2 Action không được để trống."
                )
                return

            if not self.joint_state_topic:
                self.error.emit(
                    "Joint State Topic không được để trống."
                )
                return

            # ------------------------------------------------
            # Destroy old subscription
            # ------------------------------------------------

            if self.joint_state_sub is not None:

                self.node.destroy_subscription(
                    self.joint_state_sub
                )

                self.joint_state_sub = None

            # ------------------------------------------------
            # Action Client
            # ------------------------------------------------

            self.action_client = ActionClient(
                self.node,
                FollowJointTrajectory,
                self.action_name
            )

            self.success.emit(f"Action: {self.action_name}")

            # ------------------------------------------------
            # Joint State Subscriber
            # ------------------------------------------------

            self.joint_state_sub = (
                self.node.create_subscription(
                    JointState,
                    self.joint_state_topic,
                    self.joint_state_callback,
                    10
                )
            )

            self.success.emit(
                f"Joint State Topic: {self.joint_state_topic}"
            )
            # ------------------------------------------------
            # Check Action Server
            # ------------------------------------------------

            if not self.action_client.wait_for_server(
                timeout_sec=3.0
            ):

                self.error.emit(
                    f"Không tìm thấy Action Server:\n"
                    f"{self.action_name}"
                )

                return

            self.success.emit("Action Server đã kết nối.")

            # ------------------------------------------------
            # Wait first JointState
            # ------------------------------------------------

            self.received_joint_state = False

            for _ in range(30):

                rclpy.spin_once(
                    self.node,
                    timeout_sec=0.1
                )

                if self.received_joint_state:
                    break

            if not self.received_joint_state:

                self.error.emit(
                    f"Không nhận được JointState "
                    f"từ topic:\n"
                    f"{self.joint_state_topic}"
                )

                return

            # ------------------------------------------------
            # Connected
            # ------------------------------------------------

            self.connected.emit()

            self.success.emit("Robot đã kết nối thành công.")

            current_text = ", ".join(
                f"{angle:.2f}°" for angle in self.latest_positions
            )
            self.success.emit(f"Current position: {current_text}")

        except Exception as e:

            self.error.emit(
                f"Gazebo connection error: {e}"
            )

    # --------------------------------------------------------
    # ROBOT INFO
    # --------------------------------------------------------

    def robot_info_callback(self, msg, topic_name="/robot_info"):

        try:

            info = json.loads(msg.data)
            info.setdefault("robot_info_topic", topic_name)

            self.latest_robot_info = info

            self.robot_info_received.emit(
                info
            )

        except Exception as e:

            self.error.emit(
                f"RobotInfo parse error: {e}"
            )

    # --------------------------------------------------------
    # JOINT STATE CALLBACK
    # --------------------------------------------------------

    def joint_state_callback(self, msg):

        try:

            positions = {}

            for name, position in zip(
                msg.name,
                msg.position
            ):
                positions[name] = position

            # Kiểm tra đủ 6 joint
            if not all(
                joint in positions
                for joint in JOINT_NAMES
            ):
                return

            # rad -> degree
            self.latest_positions = [
                math.degrees(
                    positions[joint]
                )
                for joint in JOINT_NAMES
            ]

            if not self.received_joint_state:
                self.log.emit(
                    f"Đã nhận JointState từ {self.joint_state_topic}"
                )

            self.received_joint_state = True

            # Chỉ gửi dữ liệu lên GUI, không log từng message
            self.joint_state_received.emit(
                list(self.latest_positions)
            )

        except Exception as e:

            self.error.emit(
                f"JointState error: {e}"
            )

    # --------------------------------------------------------
    # SEND JOINT COMMAND
    # --------------------------------------------------------

    @Slot(list, int)
    def send_joint_command(
        self,
        target_angles_deg,
        speed_override
    ):

        if self.action_client is None:

            self.error.emit(
                "Gazebo chưa được kết nối."
            )

            return

        try:

            if len(target_angles_deg) != 6:

                self.error.emit(
                    "Phải có đúng 6 góc joint."
                )

                return

            # ------------------------------------------------
            # Speed
            # ------------------------------------------------

            robot_info = self.latest_robot_info or {}
            max_speeds = robot_info.get("max_speed_deg_s", [])
            if len(max_speeds) != len(target_angles_deg):
                self.error.emit(
                    "Chưa nhận được tốc độ khớp từ topic /robot_info."
                )
                return

            override = float(speed_override) / 100.0
            joint_speeds = [
                float(max_speed) * override
                for max_speed in max_speeds
            ]

            if any(speed <= 0 for speed in joint_speeds):

                self.error.emit(
                    "Speed Override phải lớn hơn 0."
                )

                return

            # ------------------------------------------------
            # Calculate duration
            # ------------------------------------------------

            durations = []

            for current, target, speed in zip(
                self.latest_positions,
                target_angles_deg,
                joint_speeds,
            ):

                delta = abs(
                    float(target) - float(current)
                )

                durations.append(
                    delta / speed
                )

            duration = max(
                durations
            )

            # Không cho thời gian bằng 0
            duration = max(
                duration,
                0.1
            )

            # ------------------------------------------------
            # Create Goal
            # ------------------------------------------------

            goal = FollowJointTrajectory.Goal()

            goal.trajectory.joint_names = (
                list(JOINT_NAMES)
            )

            # degree -> radian
            # ------------------------------------------------

            point = JointTrajectoryPoint()

            point.positions = [
                math.radians(
                    float(angle)
                )
                for angle in target_angles_deg
            ]

            # ------------------------------------------------
            # Time
            # ------------------------------------------------

            sec = int(duration)

            nanosec = int(
                (duration - sec)
                * 1e9
            )

            point.time_from_start.sec = sec
            point.time_from_start.nanosec = nanosec

            goal.trajectory.points = [
                point
            ]

            # ------------------------------------------------
            # Send
            # ------------------------------------------------

            future = (
                self.action_client.send_goal_async(
                    goal
                )
            )

            future.add_done_callback(
                self.goal_response_callback
            )

            message = (
                f"Gửi trajectory ({duration:.2f}s, {speed_override}%)"
            )
            self.success.emit(message)

        except Exception as e:

            self.error.emit(
                f"Send command error: {e}"
            )

    # --------------------------------------------------------
    # GOAL RESPONSE
    # --------------------------------------------------------

    def goal_response_callback(
        self,
        future
    ):

        try:

            goal_handle = future.result()

            if not goal_handle.accepted:

                self.error.emit(
                    "Trajectory bị từ chối."
                )

                return

            self.success.emit("Trajectory đã được chấp nhận.")

            result_future = (
                goal_handle.get_result_async()
            )

            result_future.add_done_callback(
                self.goal_result_callback
            )

        except Exception as e:

            self.error.emit(
                f"Goal response error: {e}"
            )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    def goal_result_callback(
        self,
        future
    ):

        try:

            result = future.result()

            self.success.emit("Trajectory hoàn thành.")

        except Exception as e:

            self.error.emit(
                f"Trajectory result error: {e}"
            )

    # --------------------------------------------------------
    # SPIN
    # --------------------------------------------------------

    def _spin_once(self):
        if self.node is not None and rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0.0)

    def _scan_robot_info_topics(self, qos):
        if self.node is None:
            return
        topic_names = {
            name
            for name, types in self.node.get_topic_names_and_types()
            if name.startswith("/robot_info/")
            and "std_msgs/msg/String" in types
            and self.node.get_publishers_info_by_topic(name)
        }
        for topic_name in topic_names - self.robot_info_subscriptions.keys():
            self.robot_info_subscriptions[topic_name] = (
                self.node.create_subscription(
                    String,
                    topic_name,
                    lambda msg, topic=topic_name: self.robot_info_callback(
                        msg,
                        topic,
                    ),
                    qos,
                )
            )
            self.robot_info_republish_clients[topic_name] = (
                self.node.create_client(
                    Trigger,
                    f"{topic_name}/republish",
                )
            )

        for topic_name in (
            self.robot_info_subscriptions.keys() - topic_names
        ):
            self.node.destroy_subscription(
                self.robot_info_subscriptions.pop(topic_name)
            )
            self.robot_info_republish_clients.pop(topic_name, None)
            self.robot_info_removed.emit(topic_name)

    @Slot()
    def spin(self):

        while self.running and rclpy.ok():

            try:

                rclpy.spin_once(
                    self.node,
                    timeout_sec=0.05
                )

            except Exception as e:

                self.error.emit(
                    f"ROS spin error: {e}"
                )

                break

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    @Slot()
    def stop(self):

        self.running = False

        try:

            if self.spin_timer is not None:
                self.spin_timer.stop()
                self.spin_timer.deleteLater()
                self.spin_timer = None

            if self.discovery_timer is not None:
                self.discovery_timer.stop()
                self.discovery_timer.deleteLater()
                self.discovery_timer = None

            for client in self.robot_info_republish_clients.values():
                if client.wait_for_service(timeout_sec=0.5):
                    future = client.call_async(Trigger.Request())
                    rclpy.spin_until_future_complete(
                        self.node,
                        future,
                        timeout_sec=0.5,
                    )
                    if future.done() and future.result() is not None:
                        self.success.emit(future.result().message)
            self.robot_info_republish_clients.clear()

            if self.joint_state_sub is not None:

                self.node.destroy_subscription(
                    self.joint_state_sub
                )

                self.joint_state_sub = None

            for subscription in self.robot_info_subscriptions.values():
                self.node.destroy_subscription(
                    subscription
                )
            self.robot_info_subscriptions.clear()

            if self.node is not None:

                self.node.destroy_node()

                self.node = None

            self.action_client = None

            self.disconnected.emit()

        except Exception as e:

            self.error.emit(
                f"ROS shutdown error: {e}"
            )


# ============================================================
# GAZEBO BACKEND
# ============================================================

class GazeboBackend(QObject):

    joint_state_received = Signal(list)

    robot_info_received = Signal(dict)
    robot_info_removed = Signal(str)

    connected = Signal()
    disconnected = Signal()

    error = Signal(str)
    success = Signal(str)
    log = Signal(str)

    # GUI -> Worker
    connect_requested = Signal(str, str)
    publish_requested = Signal(list, int)
    stop_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.latest_positions = [
            0.0
        ] * 6

        self.latest_robot_info = None
        self.discovered_robot_infos = {}

        # ----------------------------------------------------
        # Thread
        # ----------------------------------------------------

        self.thread = QThread()

        self.worker = RosWorker()

        self.worker.moveToThread(
            self.thread
        )

        # ----------------------------------------------------
        # Thread start
        # ----------------------------------------------------

        self.thread.started.connect(
            self.worker.start
        )

        # ----------------------------------------------------
        # GUI -> Worker
        # ----------------------------------------------------

        self.connect_requested.connect(
            self.worker.connect_robot
        )

        self.publish_requested.connect(
            self.worker.send_joint_command
        )

        self.stop_requested.connect(
            self.worker.stop
        )

        # ----------------------------------------------------
        # Worker -> GUI
        # ----------------------------------------------------

        self.worker.joint_state_received.connect(
            self._on_joint_state
        )

        self.worker.robot_info_received.connect(
            self._on_robot_info
        )
        self.worker.robot_info_removed.connect(
            self._on_robot_info_removed
        )

        self.worker.connected.connect(
            self.connected
        )

        self.worker.disconnected.connect(
            self.disconnected
        )

        self.worker.disconnected.connect(
            lambda: self.log.emit("Đã ngắt kết nối ROS2.")
        )

        self.worker.error.connect(
            self.error
        )

        self.worker.success.connect(
            self.success
        )

        self.worker.log.connect(
            self.log
        )

        # ----------------------------------------------------
        # Start thread
        # ----------------------------------------------------

        self.thread.start()

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    def connect(
        self,
        action_name,
        joint_state_topic="/joint_states"
    ):

        self.connect_requested.emit(
            str(action_name),
            str(joint_state_topic)
        )

        return True

    # --------------------------------------------------------
    # JOINT STATE
    # --------------------------------------------------------

    def _on_joint_state(
        self,
        positions
    ):

        self.latest_positions = list(
            positions
        )

        self.joint_state_received.emit(
            list(positions)
        )

    # --------------------------------------------------------
    # ROBOT INFO
    # --------------------------------------------------------

    def _on_robot_info(
        self,
        info
    ):

        self.latest_robot_info = dict(
            info
        )
        robot_name = info.get("model") or info.get("name")
        robot_key = (
            info.get("robot_info_topic"),
            robot_name,
            info.get("control_action_topic"),
            info.get("joint_state_topic"),
        )
        self.discovered_robot_infos[robot_key] = dict(info)

        self.robot_info_received.emit(
            dict(info)
        )

    def _on_robot_info_removed(self, topic_name):
        removed_keys = [
            key
            for key, info in self.discovered_robot_infos.items()
            if info.get("robot_info_topic") == topic_name
        ]
        for key in removed_keys:
            self.discovered_robot_infos.pop(key, None)
        if removed_keys:
            self.robot_info_removed.emit(topic_name)

    # --------------------------------------------------------
    # SEND COMMAND
    # --------------------------------------------------------

    def publish_joint_command(
        self,
        angles_deg,
        speed_override
    ):

        self.publish_requested.emit(
            list(angles_deg),
            int(speed_override)
        )

    # --------------------------------------------------------
    # DISCONNECT
    # --------------------------------------------------------

    def disconnect(self):

        if self.thread.isRunning():

            self.stop_requested.emit()

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    def close(self):

        if not self.thread.isRunning():
            return

        self.stop_requested.emit()

        self.thread.quit()

        if not self.thread.wait(3000):

            self.thread.terminate()

            self.thread.wait()