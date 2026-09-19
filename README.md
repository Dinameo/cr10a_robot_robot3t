
## 1. Máy host: cài đặt và tạo container

Cài đặt Docker theo hướng dẫn: https://docs.docker.com/engine/install/ubuntu/

Thêm user vào group Docker:

```bash
sudo usermod -aG docker <USERNAME>
newgrp docker
```

Clone repository và build image:

```bash
cd ~
git clone https://github.com/Dinameo/cr10a_robot_robot3t.git
cd ~/cr10a_robot_robot3t
docker build -t ros2_jazzy .
```

Các lệnh dưới đây vẫn chạy trên **máy host**:

Container duy nhất `cr10a_ros2` đã được cấp quyền truy cập GPU/display và webcam
`/dev/video0`:

```bash
xhost +local:docker

mkdir -p /tmp/runtime
chmod 700 /tmp/runtime

docker run -it \
    --name cr10a_ros2 \
    --device=/dev/dri:/dev/dri \
    --device=/dev/video0:/dev/video0 \
    -e DISPLAY=$DISPLAY \
    -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=/tmp/runtime \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY:/tmp/$WAYLAND_DISPLAY \
    -v ~/cr10a_robot_robot3t:/cr10a_robot_robot3t \
    ros2_jazzy
```

`xhost +local:docker` cần chạy lại sau mỗi lần khởi động máy. Kiểm tra webcam
trước khi tạo container:

```bash
ls /dev/video*
```

Sau lệnh `docker run`, terminal hiện tại đã chuyển vào container. Từ đây,
mọi lệnh có prompt `root@cr10a_robot$` đều chạy **bên trong container**.

## 2. Trong container: build và chạy mô phỏng

Thực hiện trong container:

```bash
cd /cr10a_robot_robot3t
colcon build
source install/setup.bash
ros2 launch cr10a_robot gazebo.launch.py
```

Ví dụ đưa Joint1 về `0.5` rad trong 3 giây:

```bash
ros2 action send_goal -f /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "trajectory:
    joint_names: [Joint1, Joint2, Joint3, Joint4, Joint5, Joint6]
    points:
    - positions: [0.5, 0.0, 0.0, 0.0, 0.0, 0.0]
      time_from_start: {sec: 3}"
```

## 3. Trong container: kiểm tra camera

Phần này chỉ dùng để kiểm tra container có truy cập được webcam hay chưa.
Camera được sử dụng trực tiếp bởi Robot GUI.

```bash
ls -l /dev/video0
```

Nếu file tồn tại, kiểm tra camera có thể mở được:

```bash
python3 - <<'PY'
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaDevices

app = QApplication([])
cameras = QMediaDevices.videoInputs()
print(f"Found {len(cameras)} camera(s)")
for camera in cameras:
  print(camera.description(), bytes(camera.id()).decode(errors="replace"))
PY
```

Kết quả cần thấy webcam và thiết bị tương ứng, thường là `/dev/video0`.

## 4. Trong container: Robot GUI

Mở terminal thứ hai trên **máy host**, sau đó dùng `docker exec` để mở shell
thứ hai bên trong container:

```bash
docker exec -it cr10a_ros2 bash
cd /cr10a_robot_robot3t
source install/setup.bash
python3 -m robot_gui.main
```