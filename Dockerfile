FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

# =========================
# Công cụ cơ bản
# =========================
RUN apt-get update && apt-get install -y \
    curl \
    lsb-release \
    gnupg \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*


# =========================
# Thêm Gazebo OSRF repository
# =========================
RUN curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
    -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
    https://packages.osrfoundation.org/gazebo/ubuntu-stable \
    $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/gazebo-stable.list


# =========================
# ROS 2 Jazzy + Gazebo Harmonic
# =========================
RUN apt-get update && apt-get install -y \
    gz-harmonic \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros2-control \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-rviz2 \
    && rm -rf /var/lib/apt/lists/*


# =========================
# Workspace
# =========================
WORKDIR /cr10a_robot


# =========================
# Tự động source ROS 2
# =========================
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc


CMD ["/bin/bash"]
