
# Cài đặt docker

Cài đặt theo hướng dẫn https://docs.docker.com/engine/install/ubuntu/



```bash
cd ~/docker/ros2_jazzy
git clone ...
docker build -t pj_robot3t:jazzy-v1
```
Clone project về:
```bash
mkdir ~/pj_robot3t
cd ~/pj_robot3t
git clone ...
```
Tạo container mới:
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
    -v ~/pj_robot3t:/pj_robot3t \
    pj_robot3t:jazzy-v1
```

