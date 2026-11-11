import sys 
from PyQt6.QtWidgets import QApplication
from gui.main_window import AttendanceMainWindow
from gui.styles import get_modern_stylesheet

def main():
    app = QApplication(sys.argv)

    # กำหนด style ให้กับโปรแกรม
    app.setStyle('Fusion')

    # ใส่ style แบบ modern ให้กับทั้งโปรแกรม
    app.setStyleSheet(get_modern_stylesheet())

    # เรียกหน้าต่างหลักมาแสดง
    window = AttendanceMainWindow()
    window.show()

    # รัน loop โปรแกรม
    sys.exit(app.exec())

if __name__ == '__main__':
    main()