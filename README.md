
Cài đặt docker theo hướng dẫn: https://docs.docker.com/engine/install/ubuntu/

Thêm user vào group docker

```bash
sudo usermod -aG docker <USERNAME>
newgrp docker
```
Clone repo :
```bash
cd ~
git clone https://github.com/Dinameo/cr10a_robot_robot3t.git
```



build image:
```bash
cd ~/cr10a_robot_robot3t
docker build -t ros2_jazzy .
```

Cho phép container truy cập màn hình (X server):
```bash
xhost +local:docker
```
> Cần chạy lệnh nãy mỗi khi khởi động lại máy
Tạo container mới:
```bash
mkdir -p /tmp/runtime
chmod 700 /tmp/runtime

docker run -it \
    --name cr10a_ros2 \
    --device=/dev/dri:/dev/dri \
    -e DISPLAY=$DISPLAY \
    -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=/tmp/runtime \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY:/tmp/$WAYLAND_DISPLAY \
    -v ~/cr10a_robot_robot3t:/cr10a_robot_robot3t \
    ros2_jazzy
```

Build package
```bash
colcon build
source install/setup.bash
```
Chạy mô phỏng:
```bash
ros2 launch cr10a_robot gazebo.launch.py
```

Điểu khiển góc, ví dụ điểu khiển khớp 1 về vị trí 0.5 rad trong 3s:
```bash
ros2 action send_goal -f /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "trajectory:
    joint_names: [Joint1, Joint2, Joint3, Joint4, Joint5, Joint6]
    points:
    - positions: [0.5, 0.0, 0.0, 0.0, 0.0, 0.0]
      time_from_start: {sec: 3}"

```