
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QFont, QFontDatabase


def configure_app_font(app):
    """เลือก Font ภาษาไทยที่มีอยู่ในเครื่อง"""

    available_fonts = set(QFontDatabase.families())

    font_options = [
        ("Sarabun", 12),
        ("TH Sarabun PSK", 16),
        ("Noto Sans Thai", 11),
        ("Tahoma", 11),
    ]

    for family, size in font_options:
        if family in available_fonts:
            app.setFont(QFont(family, size))
            return family

    app.setFont(QFont("Segoe UI", 11))
    return "Segoe UI"


def get_modern_stylesheet():
    return """
    /* ========================================
       พื้นหลังและสีข้อความ
       ======================================== */

    QMainWindow {
        background-color: #F1F5F9;
    }

    QDialog {
        background-color: #F8FAFC;
    }

    QLabel {
        color: #334155;
    }

    QLabel#page_title {
        color: #14243B;
        font-size: 20pt;
        font-weight: bold;
    }

    QLabel#page_description {
        color: #64748B;
    }

    QWidget#toolbar_card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }

    /* ========================================
       Sidebar
       ======================================== */

    QListWidget#sidebar {
        background-color: #14243B;
        color: #CBD5E1;
        border: none;
        border-radius: 10px;
        padding: 8px;
        outline: none;
    }

    QListWidget#sidebar::item {
        padding: 11px 14px;
        margin: 3px;
        border-radius: 7px;
    }

    QListWidget#sidebar::item:hover {
        background-color: #263C56;
        color: #FFFFFF;
    }

    QListWidget#sidebar::item:selected {
        background-color: #2563EB;
        color: #FFFFFF;
        font-weight: bold;
    }

    /* ========================================
       Tabs
       ======================================== */

    QTabWidget::pane {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }

    QTabBar::tab {
        background-color: #E2E8F0;
        color: #475569;
        padding: 12px 24px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }

    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #2563EB;
        font-weight: bold;
        border-top: 3px solid #2563EB;
    }

    /* ========================================
       ปุ่มกด
       ======================================== */

    QPushButton {
        background-color: #FFFFFF;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 7px;
        padding: 8px 18px;
        min-height: 23px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #EFF6FF;
        border-color: #93C5FD;
        color: #1D4ED8;
    }

    QPushButton:pressed {
        background-color: #DBEAFE;
    }

    QPushButton#btn_primary {
        background-color: #2563EB;
        border: none;
        color: #FFFFFF;
    }

    QPushButton#btn_primary:hover {
        background-color: #1D4ED8;
    }

    QPushButton#btn_success {
        background-color: #059669;
        border: none;
        color: #FFFFFF;
    }

    QPushButton#btn_success:hover {
        background-color: #047857;
    }

    QPushButton#btn_danger {
        background-color: #DC2626;
        border: none;
        color: #FFFFFF;
    }

    QPushButton#btn_danger:hover {
        background-color: #B91C1C;
    }

    QPushButton:disabled,
    QPushButton#btn_primary:disabled,
    QPushButton#btn_success:disabled,
    QPushButton#btn_danger:disabled {
        background-color: #E2E8F0;
        color: #94A3B8;
        border: 1px solid #E2E8F0;
    }

    /* ========================================
       ช่องกรอกข้อมูล
       ======================================== */

    QLineEdit, QDateEdit, QTimeEdit,
    QComboBox, QSpinBox, QTextEdit {
        background-color: #FFFFFF;
        color: #1E293B;
        border: 1px solid #CBD5E1;
        border-radius: 7px;
        padding: 7px 10px;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A8A;
    }

    QLineEdit:focus, QDateEdit:focus,
    QTimeEdit:focus, QComboBox:focus,
    QTextEdit:focus, QSpinBox:focus {
        border: 1px solid #2563EB;
        background-color: #F8FAFF;
    }

    QDateEdit::drop-down,
    QComboBox::drop-down {
        width: 28px;
        border-left: 1px solid #E2E8F0;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #334155;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A8A;
        border: 1px solid #CBD5E1;
        padding: 4px;
    }

    /* ========================================
       ตารางข้อมูล
       ======================================== */

    QTableWidget {
        background-color: #FFFFFF;
        alternate-background-color: #F8FAFC;
        color: #1E293B;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A8A;
        outline: none;
    }

    QHeaderView::section {
        background-color: #EAF0F8;
        color: #334155;
        border: none;
        border-bottom: 1px solid #CBD5E1;
        padding: 9px;
        font-weight: bold;
    }

    QTableWidget::item {
        padding: 5px 8px;
        border-bottom: 1px solid #E2E8F0;
    }

    QTableWidget::item:hover:!selected {
        background-color: #F1F5F9;
    }

    /* ========================================
       เมนูคลิกขวา
       ======================================== */

    QMenu {
        background-color: #FFFFFF;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 6px;
    }

    QMenu::item {
        padding: 7px 24px 7px 14px;
        border-radius: 5px;
    }

    QMenu::item:selected {
        background-color: #DBEAFE;
        color: #1D4ED8;
    }

    QMenu::item:disabled {
        color: #94A3B8;
    }

    QMenu::separator {
        height: 1px;
        background-color: #E2E8F0;
        margin: 5px 8px;
    }

    /* ========================================
       กลุ่มข้อมูล
       ======================================== */

    QGroupBox {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 9px;
        margin-top: 18px;
        padding: 16px 12px 12px 12px;
        font-weight: bold;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 6px;
        color: #334155;
    }

    /* ========================================
       Scrollbar
       ======================================== */

    QScrollBar:vertical {
        background-color: #F1F5F9;
        width: 11px;
        border: none;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background-color: #CBD5E1;
        border-radius: 5px;
        min-height: 30px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #94A3B8;
    }

    QScrollBar:horizontal {
        background-color: #F1F5F9;
        height: 11px;
        border: none;
        margin: 0;
    }

    QScrollBar::handle:horizontal {
        background-color: #CBD5E1;
        border-radius: 5px;
        min-width: 30px;
    }

    QScrollBar::add-line,
    QScrollBar::sub-line {
        width: 0;
        height: 0;
    }

    QScrollBar::add-page,
    QScrollBar::sub-page {
        background: none;
    }

    QToolTip {
        background-color: #14243B;
        color: #FFFFFF;
        border: none;
        padding: 6px;
    }
    """


def apply_card_shadow(widget):
    """เพิ่มเงาให้การ์ดข้อมูล"""

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(20)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(15, 23, 42, 22))

    widget.setGraphicsEffect(shadow)
