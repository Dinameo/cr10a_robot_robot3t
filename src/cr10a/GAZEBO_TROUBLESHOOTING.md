# Báo cáo lỗi hiển thị robot trong Gazebo

## 1. Hiện tượng

Chạy lệnh:

```bash
ros2 launch urdf_files gazebo.launch.py
```

Gazebo mở được nhưng robot CR10A không xuất hiện trong world. Trong một số lần chạy, node `ros_gz_sim create` báo tạo entity thành công nhưng danh sách model chỉ có `ground_plane`.

## 2. Nguyên nhân đã xác minh

### 2.1. Mesh chưa có trong thư mục `install/`

Launch file lấy URDF từ thư mục package đã cài:

```text
install/urdf_files/share/urdf_files/urdf/urdf_files.urdf
```

URDF tham chiếu các file STL trong thư mục `meshes`. Nếu chỉ sửa file trong `src/` mà chưa build lại package, các file STL có thể chưa tồn tại trong `install/`. Khi đó Gazebo không thể nạp hình học của robot.

Cách kiểm tra:

```bash
find install/urdf_files/share/urdf_files/meshes -type f -o -type l
```

### 2.2. Không tương thích giữa Gazebo và `ros_gz_sim`

Đây là nguyên nhân chính.

- `ros_gz_sim` của ROS 2 Humble trên máy dùng thư viện `libignition-transport11` và `ignition-msgs8`.
- Các thư viện này tương ứng với Ignition Gazebo / Gazebo Fortress 6.
- Launch ban đầu lại chạy `gz sim 8`, tức Gazebo Sim 8, dùng hệ transport khác.

Kết quả là ROS 2 có thể kết nối không đúng tới Gazebo. Lệnh spawn có thể in `OK creation of entity`, nhưng model không thực sự xuất hiện trong world.

Có thể xác minh backend mà `ros_gz_sim` đang link bằng:

```bash
ldd /opt/ros/humble/lib/ros_gz_sim/create | grep -E 'gz|ignition'
```

## 3. Cách sửa đã áp dụng

### 3.1. Khai báo dependency

Đã thêm dependency vào `package.xml`:

```xml
<exec_depend>ros_gz_sim</exec_depend>
```

### 3.2. Dùng đúng Gazebo backend

Trong `launch/gazebo.launch.py`, thay:

```python
'gz', 'sim'
```

bằng:

```python
'ign', 'gazebo'
```

Launch hiện chạy:

- `ign gazebo -s -r empty.sdf` cho server.
- `ign gazebo -g` cho GUI.
- `ros_gz_sim create` để spawn robot.

Server và GUI được tách riêng để GUI không làm dừng server mô phỏng.

### 3.3. Xử lý đường dẫn mesh

Các URI mesh `package://urdf_files/meshes/...` được chuyển thành URI file tuyệt đối:

```text
file:///mnt/d/RB3T/CR10A/ros2_ws/install/urdf_files/share/urdf_files/meshes/...
```

Launch cũng thiết lập `GZ_SIM_RESOURCE_PATH` tới thư mục `share` của package.

### 3.4. Chờ Gazebo khởi động

Node spawn được trì hoãn 3 giây để world và service `/world/empty/create` sẵn sàng. GUI được khởi động sau server 2 giây.

### 3.5. Build lại workspace

Sau khi thay đổi package, phải build và source lại:

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select urdf_files --symlink-install
source install/setup.bash
```

## 4. Cách chạy đúng

```bash
cd /mnt/d/RB3T/CR10A/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select urdf_files --symlink-install
source install/setup.bash
ros2 launch urdf_files gazebo.launch.py
```

Kiểm tra robot đã tồn tại trong world:

```bash
ign model --list
```

Kết quả đúng phải có:

```text
Available models:
    - ground_plane
    - urdf_files
```

## 5. Checklist phòng tránh lỗi lần sau

1. Kiểm tra ROS distro và Gazebo backend:

   ```bash
   echo "$ROS_DISTRO"
   ign gazebo --version
   gz sim --versions
   ```

2. Kiểm tra `ros_gz_sim` đang dùng transport nào:

   ```bash
   ldd /opt/ros/$ROS_DISTRO/lib/ros_gz_sim/create | grep -E 'gz|ignition'
   ```

3. Không trộn `gz sim` với `ros_gz_sim` nếu package ROS đang dùng thư viện `ignition-*`. Với cấu hình hiện tại phải dùng `ign gazebo`.

4. Sau khi thêm hoặc đổi mesh, luôn build lại package và kiểm tra thư mục cài đặt:

   ```bash
   colcon build --packages-select urdf_files --symlink-install
   find install/urdf_files/share/urdf_files/meshes -type f -o -type l
   ```

5. Kiểm tra node spawn và model trong world:

   ```bash
   ros2 node list
   ign model --list
   ```

6. Phân biệt warning với error:

   ```text
   The root link base_link has an inertia specified...
   ```

   Đây là cảnh báo của KDL về inertia ở root link, không phải nguyên nhân robot không xuất hiện.

7. Khi launch mở GUI nhưng không có robot, kiểm tra server trước bằng service/world state. Nếu `ign model --list` chỉ có `ground_plane`, robot chưa được spawn; vấn đề nằm ở backend, resource path, URDF hoặc mesh, không phải camera GUI.

## 6. Kết luận

Lỗi được giải quyết bằng cách dùng đúng cặp phiên bản:

```text
ROS 2 Humble + ros_gz_sim + Ignition Gazebo 6
```

Không dùng:

```text
ROS 2 Humble ros_gz_sim + Gazebo Sim 8 (`gz sim`)
```

## 7. Lỗi đế robot bị lật

### Nguyên nhân

`base_link` ban đầu là root link tự do, không có liên kết với `world`. Gazebo
vì vậy mô phỏng toàn bộ robot như một vật thể có thể rơi, trượt và lật trên
mặt phẳng.

### Cách sửa

Đã thêm link `world` và fixed joint `base_to_world_fixed` trong URDF:

```xml
<link name="world" />
<joint name="base_to_world_fixed" type="fixed">
   <parent link="world" />
   <child link="base_link" />
</joint>
```

Joint này cố định đế robot với world, nhưng không khóa các joint `Joint1` đến
`Joint6` của tay máy.

Kiểm tra cấu trúc sau khi sửa:

```bash
xmllint --noout src/urdf_files/urdf/urdf_files.urdf
gz sdf -p src/urdf_files/urdf/urdf_files.urdf | grep -E 'world|base_to_world_fixed'
```
