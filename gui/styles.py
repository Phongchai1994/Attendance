from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

def get_modern_stylesheet():
    return """
    /* --- พื้นหลังโปรแกรม --- */
    QMainWindow {
        background-color: #F4F7F6;
    }
    QWidget {
        font-family: "Segoe UI", "Tahoma", sans-serif;
    }

    /* --- ระบบแท็บ (QTabWidget) --- */
    QTabWidget::pane {
        border: 1px solid #E0E6ED;
        background-color: #FFFFFF;
        border-radius: 8px;
        margin-top: -1px;
    }
    QTabBar::tab {
        background-color: #F8FAFC;
        color: #64748B;
        padding: 12px 25px;
        border: 1px solid #E0E6ED;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 4px;
        font-size: 14px;
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #2563EB;
        border-top: 3px solid #2563EB;
    }
    QTabBar::tab:hover:!selected {
        background-color: #E2E8F0;
        color: #0F172A;
    }

    /* --- ปุ่มกดทั่วไป (QPushButton) --- */
    QPushButton {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #E2E8F0;
        border-color: #94A3B8;
    }
    QPushButton:pressed {
        background-color: #CBD5E1;
    }

    /* --- ปุ่มหลัก (Primary Button) --- */
    QPushButton#btn_primary {
        background-color: #2563EB;
        color: white;
        border: none;
    }
    QPushButton#btn_primary:hover {
        background-color: #1D4ED8;
    }

    /* --- ปุ่มสีเขียว (Success Button) --- */
    QPushButton#btn_success {
        background-color: #10B981;
        color: white;
        border: none;
    }
    QPushButton#btn_success:hover {
        background-color: #059669;
    }

    /* --- ตาราง (QTableWidget) --- */
    QTableWidget {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        gridline-color: #F1F5F9;
        selection-background-color: #EFF6FF;
        selection-color: #1E3A8A;
        outline: none;
    }
    QHeaderView::section {
        background-color: #F8FAFC;
        color: #475569;
        padding: 10px;
        border: none;
        border-bottom: 2px solid #E2E8F0;
        font-weight: bold;
        font-size: 14px;
    }
    QTableWidget::item {
        padding: 5px;
        border-bottom: 1px solid #F1F5F9;
    }

    /* --- ช่องเลือกวันที่ (QDateEdit) --- */
    QDateEdit {
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 6px 10px;
        background-color: white;
        font-size: 14px;
    }
    QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: 1px solid #E2E8F0;
        background-color: transparent; /* ทำให้พื้นหลังกลืนไปกับปุ่ม */
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
    }
    QDateEdit::drop-down:hover {
        background-color: #F1F5F9; /* สีเทาอ่อนตอนเอาเมาส์ชี้ */
    }
    QDateEdit::down-arrow {
        /* ปิดการใช้ภาพและขอบทึบ เพื่อดึงลูกศรดั้งเดิมมาใช้ */
        image: none; 
        border: none;
        
        /* ขยายขนาดลูกศรระบบให้ใหญ่ขึ้นนิดนึง เพื่อให้สมส่วนกับความสูงของช่อง */
        width: 12px;
        height: 12px;
    }

    
    """

def apply_card_shadow(widget):
    """เพิ่มเอฟเฟกต์เงา (Drop Shadow) ให้กับการ์ดเพื่อมิติที่สวยงาม"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)       # ความฟุ้งของเงา
    shadow.setXOffset(0)           # เงาแกน X
    shadow.setYOffset(4)           # เงาแกน Y (ตกกระทบด้านล่าง)
    shadow.setColor(QColor(0, 0, 0, 30)) # สีดำ โปร่งใส 30
    widget.setGraphicsEffect(shadow)