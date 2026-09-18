import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    pkg_dir = get_package_share_directory('cr10a_robot')

    urdf_file = os.path.join(
        pkg_dir,
        'urdf',
        'urdf_files.urdf'
    )

    # Đọc URDF
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # Bỏ XML declaration để tránh lỗi parser
    robot_description = robot_description.replace(
        '<?xml version="1.0"?>',
        ''
    ).replace(
        '<?xml version="1.0" encoding="UTF-8"?>',
        ''
    )

    # Đổi đường dẫn mesh package:// thành đường dẫn tuyệt đối
    mesh_dir = os.path.join(
        pkg_dir,
        'meshes'
    )

    resource_dir = os.path.dirname(pkg_dir)
    ros_distro = os.environ.get('ROS_DISTRO', 'jazzy')
    plugin_dir = os.path.join('/opt/ros', ros_distro, 'lib')

    robot_description = robot_description.replace(
        'package://urdf_files/meshes/',
        'file://' + mesh_dir + '/'
    )

    return LaunchDescription([

        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=resource_dir
        ),

        SetEnvironmentVariable(
            name='GZ_SIM_SYSTEM_PLUGIN_PATH',
            value=plugin_dir + ':' + os.environ.get(
                'GZ_SIM_SYSTEM_PLUGIN_PATH',
                ''
            )
        ),

        # =========================
        # Gazebo Sim
        # =========================
        ExecuteProcess(
            cmd=[
                'gz',
                'sim',
                '-s',
                '-r',
                'empty.sdf'
            ],
            output='screen'
        ),

        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'gz',
                        'sim',
                        '-g'
                    ],
                    output='screen'
                )
            ]
        ),

        # =========================
        # Robot State Publisher
        # =========================
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',

            parameters=[
                {
                    'robot_description': robot_description
                }
            ],

            output='screen'
        ),

        # =========================
        # Spawn robot vào Gazebo
        # =========================
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package='ros_gz_sim',
                    executable='create',
                    arguments=[
                        '-world',
                        'empty',
                        '-name',
                        'urdf_files',
                        '-x',
                        '0',
                        '-y',
                        '0',
                        '-z',
                        '0',
                        '-topic',
                        'robot_description'
                    ],
                    output='screen'
                )
            ]
        ),

        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'joint_state_broadcaster',
                        '--controller-manager',
                        '/controller_manager'
                    ],
                    output='screen'
                ),
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'arm_controller',
                        '--controller-manager',
                        '/controller_manager'
                    ],
                    output='screen'
                )
            ]
        ),
    ])