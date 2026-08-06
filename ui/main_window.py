from pathlib import Path
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from ui.widgets.sidebar import Sidebar
from ui.views.content_area import ContentArea


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ระบบเช็คชื่อเข้าทำงาน "เรือนจำจังหวัดจันทบุรี"')
        self.setMinimumSize(1280, 720)

        main_widget = QWidget()
        main_widget.setObjectName("root")
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        self.sidebar = Sidebar()
        self.content_area = ContentArea()

        self.sidebar.navigation_changed.connect(self.on_navigation_changed)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)

        self.apply_theme()
        self.sidebar.set_active('dashboard')

    def on_navigation_changed(self, page_key: str):
        self.content_area.show_page(page_key)
        self.sidebar.set_active(page_key)

    def _resource_path(self, relative_path: str) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parent.parent
        return base_path / relative_path

    def apply_theme(self):
        qss_path = self._resource_path("assets/styles/styles.qss")
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))