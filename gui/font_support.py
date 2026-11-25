"""โหลด Google Sarabun จากไฟล์บนเครื่อง และปรับฟอนต์ของ PyQt ComboBox"""
from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QStyledItemDelegate


def load_local_sarabun(app):
    """ถ้ามี assets/fonts/Sarabun-*.ttf จะโหลดเข้าแอปโดยไม่ต้องติดตั้ง Windows"""
    folder = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    loaded_families = []

    for filename in ("Sarabun-Regular.ttf", "Sarabun-Bold.ttf"):
        path = folder / filename
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id == -1:
            print("Cannot load Sarabun font:", path)
            continue
        loaded_families.extend(QFontDatabase.applicationFontFamilies(font_id))

    if loaded_families:
        family = next((f for f in loaded_families if f.lower() == "sarabun"), loaded_families[0])
        app.setFont(QFont(family, 12))
        print("Application Font:", family, "(local file)")
        return family

    installed = QFontDatabase.families()
    for wanted in ("Sarabun", "TH SarabunPSK", "TH Sarabun PSK", "TH Sarabun New"):
        found = next((f for f in installed if f.lower().replace(" ", "") == wanted.lower().replace(" ", "")), None)
        if found:
            app.setFont(QFont(found, 12 if found.lower() == "sarabun" else 16))
            print("Application Font:", found, "(installed)")
            return found

    print("Sarabun not found; using Qt fallback:", app.font().family())
    return app.font().family()


def ui_font():
    return QApplication.font()


def apply_combo_font(combo):
    """ฟอนต์ของช่องเลือกและ popup มีขนาดเดียวกัน"""
    font = ui_font()
    combo.setFont(font)
    combo.view().setFont(font)
    combo.view().viewport().setFont(font)
    if combo.isEditable() and combo.lineEdit():
        combo.lineEdit().setFont(font)
    combo.view().setStyleSheet("font-family: '%s'; font-size: %dpt;" % (
        font.family().replace("'", ""), font.pointSize()
    ))
    # บังคับให้ view ของ combo ใช้ delegate ของ Qt ที่รองรับฟอนต์ที่กำหนด
    if combo.itemDelegate() is None:
        combo.setItemDelegate(QStyledItemDelegate(combo))


def to_arabic_digits(value):
    if value is None:
        return ""
    return str(value).translate(str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789"))
