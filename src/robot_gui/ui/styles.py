MAIN_STYLE = """
QMenuBar { background-color: #202124; color: #eeeeee; }
QMenuBar::item { background-color: transparent; padding: 6px 10px; }
QMenuBar::item:selected { background-color: #414246; }
QMenu { background-color: #303134; color: #eeeeee; border: 1px solid #555555; }
QMenu::item { padding: 7px 24px; }
QMenu::item:selected { background-color: #414246; }
QMainWindow { background-color: #202124; }
QWidget { font-size: 14px; }
QGroupBox { font-weight: bold; border: 1px solid #555555; border-radius: 6px; margin-top: 10px; padding-top: 10px; color: #eeeeee; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QLabel { color: #eeeeee; }
QLineEdit { background-color: #303134; color: #ffffff; border: 1px solid #666666; border-radius: 4px; padding: 5px; }
QSlider::groove:horizontal { height: 5px; background: #555555; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; border-radius: 7px; background: #dddddd; }
QPushButton { background-color: #303134; color: #ffffff; border: 1px solid #666666; border-radius: 4px; padding: 7px 10px; }
QPushButton:hover { background-color: #414246; }
QPushButton:pressed { background-color: #505154; }
"""

CAMERA_LABEL_STYLE = """
QLabel { background-color: #111111; color: #777777; border: 1px solid #444444; border-radius: 4px; }
"""
STATUS_STYLE = "QLabel { background-color: transparent; color: #aaaaaa; border: none; }"
LOG_STYLE = """
QPlainTextEdit { background-color: #111111; color: #eeeeee; border: 1px solid #444444; border-radius: 4px; padding: 5px; font-family: monospace; }
"""
STOP_STYLE = """
QPushButton { background-color: #8b1e1e; color: white; font-weight: bold; }
QPushButton:hover { background-color: #a52a2a; }
"""
MOVE_STYLE = "QPushButton { font-weight: bold; }"

DIALOG_STYLE = """
QDialog {
    background-color: #252525;
    color: #eeeeee;
}

QLabel {
    color: #eeeeee;
}

QLineEdit {
    background-color: #333333;
    color: #eeeeee;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
}

QListWidget {
    background-color: #333333;
    color: #eeeeee;
    border: 1px solid #555555;
}

QPushButton {
    background-color: #3a3a3a;
    color: #eeeeee;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #4a4a4a;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}
"""