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

    resource_dir = os.path.dirname(pkg_dir)
    ros_distro = os.environ.get('ROS_DISTRO', 'jazzy')
    plugin_dir = os.path.join('/opt/ros', ros_distro, 'lib')
    
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
        # Bridge /clock: Gazebo → ROS 2
        # =========================
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            output='screen',
        ),

        # =========================
        # Robot Info Publisher: /robot_info
        # =========================
        Node(
            package='cr10a_robot',
            executable='robot_info_publisher',
            name='robot_info_publisher',
            output='screen',
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
                        'cr10a_robot',
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