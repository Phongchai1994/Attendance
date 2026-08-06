from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class ContentArea(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("contentArea")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.pages = {}

        self._add_page("dashboard", self._build_dashboard_page())
        self._add_page("attendance", self._build_simple_page("ระบบเช็คชื่อ"))
        self._add_page("employee", self._build_simple_page("พนักงาน"))
        self._add_page("department", self._build_simple_page("ฝ่าย / งาน"))
        self._add_page("leave", self._build_simple_page("วันลา"))
        self._add_page("holiday", self._build_simple_page("วันหยุด"))
        self._add_page("import", self._build_simple_page("นำเข้าข้อมูล"))
        self._add_page("report", self._build_simple_page("รายงาน"))
        self._add_page("backup", self._build_simple_page("สำรองข้อมูล"))
        self._add_page("setting", self._build_simple_page("ตั้งค่า"))
        self._add_page("log", self._build_simple_page("Log System"))

        self.show_page("dashboard")

    def _add_page(self, key: str, widget: QWidget):
        self.pages[key] = widget
        self.stack.addWidget(widget)

    def _build_dashboard_page(self):
        page = QLabel('Dashboard View (Charts & Stats)')
        page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return page

    def _build_simple_page(self, title: str):
        page = QLabel(f"{title} page")
        page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return page

    def show_page(self, key: str):
        widget = self.pages.get(key)
        if widget:
            self.stack.setCurrentWidget(widget)
