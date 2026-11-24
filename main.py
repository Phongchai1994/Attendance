
import sys
from PyQt6.QtCore import QLocale

from PyQt6.QtWidgets import QApplication
from gui.main_window import AttendanceMainWindow

from gui.styles import (
    get_modern_stylesheet,
    configure_app_font,
)


def main():
    # ใช้เลขอารบิกและรูปแบบวันที่สากล
    QLocale.setDefault(
        QLocale(
            QLocale.Language.English,
            QLocale.Country.UnitedStates
        )
    )
    app = QApplication(sys.argv)

    # กำหนดรูปแบบพื้นฐานของ Qt
    app.setStyle("Fusion")

    # โหลด Font ภาษาไทย
    font_name = configure_app_font(app)
    print(f"Application Font: {font_name}")

    # โหลด Theme กลางของโปรแกรม
    app.setStyleSheet(get_modern_stylesheet())

    # แสดงหน้าต่างหลัก
    window = AttendanceMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
