cmake_minimum_required(VERSION 3.8)
project(cr10a_robot)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    config
    launch
    meshes
    urdf
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/robot_info_publisher
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()