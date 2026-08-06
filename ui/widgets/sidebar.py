from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QButtonGroup
)


class Sidebar(QWidget):
    navigation_changed = pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title_label = QLabel('Attendance\nSystem')
        title_label.setObjectName('titleLabel')
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title_label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.nave_buttons = {}
        nav_items = [
            ("Dashboard", "dashboard", "assets/icons/dashboard.png"),
            ("ระบบเช็คชื่อ", "attendance", "assets/icons/attendance.png"),
            ("พนักงาน", "employee", "assets/icons/employee.png"),
            ("ฝ่าย / งาน", "department", "assets/icons/department.png"),
            ("วันลา", "leave", "assets/icons/leave.png"),
            ("วันหยุด", "holiday", "assets/icons/holiday.png"),
            ("นำเข้าข้อมูล", "import", "assets/icons/import.png"),
            ("รายงาน", "report", "assets/icons/report.png"),
            ("สำรองข้อมูล", "backup", "assets/icons/backup.png"),
            ("ตั้งค่า", "setting", "assets/icons/settings.png"),
            ("Log System", "log", "assets/icons/log.png"),
        ]

        for index, (text, key, icon_path) in enumerate(nav_items):
            button = QPushButton(text)
            button.setObjectName('navButton')
            button.setCheckable(True)
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(20, 20))
            button.setMinimumHeight(46)
            button.clicked.connect(lambda checked=False, page_key = key: self.navigation_changed.emit(page_key))

            self.button_group.addButton(button, index)
            self.nave_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)

    def set_active(self, key: str):
        button = self.nave_buttons.get(key)
        if button:
            button.setChecked(True)