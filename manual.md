# Cài đặt sử dụng docker
## 1. Kiểm tra Docker đã có chưa

Kiểm tra phiên bản docker:
```bash
docker --version
```

Kiểm tra Docker chạy:
```bash
sudo systemctl status docker
```

Kết quả phải có active: running

Nếu chưa có:
```bash
sudo systemctl start docker
```
Để docker tự khởi chạy:
```bash
sudo systemctl enable docker
```

## 2. Lấy image ROS 2 Jazzy

```bash
docker pull ros:jazzy
```

Nếu báo lỗi `permission denied`, thêm user vào group docker:

```bash
sudo usermod -aG docker <ten_user>
```
Sau đó khởi động máy lại hoặc gõ lệnh `newgrp docker` để chạy trên terminal hiện tại.

Sau khi pull về xong kiểm tra:
```bash
docker images
```

Kết quả phải có:
```bash
IMAGE       ID              DISK USAGE  CONTENT SIZE    EXTRA
ros:jazzy   c3706ef0a0aa    1.32GB      321MB
```

## 3. Chạy container ROS 2 Jazzy

Khởi chạy container:
```bash
docker run -it --name <container_name> <image>
```

Khi vào được container, kiểm tra ros2 distro:
```bash
printenv ROS_DISTRO
```

Kết quả:
```bash
jazzy
```
## 4. Thoát container

Để thoát container:
```bash
exit
```
Container sẽ dừng nhưng không bị xóa.


Để liệt kê tất cả container Docker (Cả đang chạy và dừng):

```bash
docker ps -a
```
Kết quả:
```bash
33ff68fac52c    ros:jazzy   "/ros_entrypoint.sh …"  4 minutes ago   Exited (0) About a minute ago ros2_jazzy 
```

- Up: đang chạy
- Exited: đã dừng
- Created: đã tạo nhưng chưa chạy


## 5. Chạy lại container

Lần sau không cần docker run nữa:
```bash
docker start -ai <container_name>
```
## 6. Xóa container
Để xóa container:
```bash
docker stop <container_name>
docker rm <container_name>
```
## 7. mount thư mục project từ Ubuntu vào Docker

> Cần mount khi container được tạo

```bash
docker run -it --name <container_name> -v <host_path>:<container_path> <image>
```

## 8. Khởi chạy process bash mới bên trong container

Để chạy nhiều terminal trong cùng contaier, làm như sau:
```bash
docker exec -it <container_name> bash
```
## 9. Tạo docker image riêng

Thay vì mỗi lần tạo container lại cài package, bạn tạo một Dockerfile.

Tạo thư mục chứa dockerfile:
```bash
mkdir -p ~/docker/ros2_jazzy
cd ~/docker/ros2_jazzy
nano Dockerfile
```

Nội dung Dockerfile:
```bash
FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    vim \
    git \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-rviz2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

CMD ["/bin/bash"]
```

Sau đó build:
```bash
docker build -t <your_image_name> .
```

Kiểm tra image đã tạo chưa:
```bash
docker images
```

## 10. Truyền GPU/display từ host vào container

Trên terminal máy của bạn, gõ:
```bash
echo $XDG_SESSION_TYPE
```
Nếu `wayland` thì ta sẽ cấu hình Docker GUI theo Wayland/XWayland.

Kiểm tra GPU:
```bash
ls -l /dev/dri
```

Kiểm tra giao diện đồ họa (GUI) cần được hiển thị ở đâu.
```bash
echo $DISPLAY
```

Cho Docker quyền truy cập GPU:
```bash
ls -l /dev/dri/renderD128
```
Cho user của bạn vào group render va video:
```bash
sudo usermod -aG render <username>
sudo usermod -aG video <username>
```
Logout/login lại, kiểm tra có nằm trong group chưa:
```bash
groups <username>
```
Thấy video render là xong

Cấp quyền cho Docker truy cập vào màn hình GUI của máy bạn:
```bash
xhost +local:docker
```
Để tạo container ROS 2 Jazzy có quyền truy cập GPU và GUI của Ubuntu host:

```bash
mkdir -p /tmp/runtime
chmod 700 /tmp/runtime

docker run -it \
    --name ros2_jazzy \
    --device=/dev/dri:/dev/dri \
    -e DISPLAY=$DISPLAY \
    -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=/tmp/runtime \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY:/tmp/$WAYLAND_DISPLAY \
    -v <host_path>:<container_path> \
    ros:jazzy
```
## 11. Docker image creation bằng docker commit

Để tạo image từ container hiện tại:
```bash
docker commit <container> <image>:<tag>
```

# Thiết lập môi trường mô phỏng ROS2 JAZZY

## 1. Cài các package ROS cần thiết

```bash
apt update
```

```bash
apt install -y \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-rviz2
```

## 2. Cài đặt gazebo harmonic

## 3. Kiểm tra controller trước khi gửi lệnh

Sau khi chạy Gazebo và launch robot, mở terminal khác trong container:

```bash
docker exec -it ros2_jazzy bash
source /opt/ros/jazzy/setup.bash
source /pj_robot3t/install/setup.bash
ros2 control list_controllers
```

Phải thấy cả hai controller ở trạng thái `active`:

```text
joint_state_broadcaster[active]
arm_controller[active]
```

Nếu `arm_controller` chưa `active`, kiểm tra plugin và log Gazebo:

```bash
ls /opt/ros/jazzy/lib/libgz_ros2_control-system.so
ros2 topic list | grep arm_controller
```

Chỉ gửi lệnh trajectory sau khi topic sau xuất hiện:

```text
/arm_controller/joint_trajectory
```

Thông báo `Waiting for at least 1 matching subscription(s)...` nghĩa là chưa có controller nào subscribe topic này.

Cài vài công cụ cần thiết:
```bash
sudo apt-get update
sudo apt-get install curl lsb-release gnupg
```
Cài đặt gazebo harmonic:
```bash
sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt-get update
sudo apt-get install gz-harmonic
```