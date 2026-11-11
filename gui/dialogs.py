from PyQt6.QtWidgets import QDialog, QFormLayout, QTimeEdit, QDialogButtonBox, QLabel
from PyQt6.QtCore import QTime, QLocale

class TimeEditDialog(QDialog):
    def __init__(self, current_in, current_out, parent=None):
        super().__init__(parent)
        self.setWindowTitle("แก้ไขเวลาเข้า-ออก")
        self.resize(250, 120)
        layout = QFormLayout(self)

        # ช่องกรอกเวลาเข้า
        self.time_in = QTimeEdit()
        self.time_in.setDisplayFormat("HH:mm")
        if current_in and current_in != "-":
            self.time_in.setTime(QTime.fromString(current_in, "HH:mm"))
        
        # ช่องกรอกเวลาออก
        self.time_out = QTimeEdit()
        self.time_out.setDisplayFormat("HH:mm")
        if current_out and current_out != "-":
            self.time_out.setTime(QTime.fromString(current_out, "HH:mm"))

        layout.addRow("เวลาเข้า:", self.time_in)
        layout.addRow("เวลาออก:", self.time_out)

        # ปุ่มตกลง / ยกเลิก
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_times(self):
        return self.time_in.time().toString("HH:mm"), self.time_out.time().toString("HH:mm")

# (โค้ดคลาส TimeEditDialog เดิมที่มีอยู่แล้ว เอาไว้เหมือนเดิมครับ)

class SingleTimeEditDialog(QDialog):
    def __init__(self, title, label_text, current_time, current_date_str, parent=None): # <--- เพิ่มรับค่า current_date_str
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(280, 130)
        layout = QFormLayout(self)

        # 1. แสดงวันที่
        lbl_date = QLabel(f"<b>{current_date_str}</b>")
        lbl_date.setStyleSheet("color: #2563EB; font-size: 14px;")
        layout.addRow("📅 วันที่แก้ไข:", lbl_date)

        # 2. ช่องกรอกเวลา (บังคับเลขอารบิก)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        
        # 👇 บังคับให้เป็นภาษาอังกฤษเพื่อไม่ให้เป็นเลขไทย
        self.time_edit.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        
        if current_time and current_time != "-":
            self.time_edit.setTime(QTime.fromString(current_time, "HH:mm"))

        layout.addRow(label_text, self.time_edit)

        # ปุ่มตกลง / ยกเลิก
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_time(self):
        return self.time_edit.time().toString("HH:mm")