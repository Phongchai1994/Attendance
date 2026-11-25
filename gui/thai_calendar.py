"""ปฏิทินชื่อวัน/เดือนภาษาไทย แต่ตัวเลขวัน/ปีเป็นเลขอารบิก"""
from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QCalendarWidget, QSpinBox, QToolButton
from gui.font_support import ui_font, to_arabic_digits


class ThaiArabicCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLocale(QLocale(QLocale.Language.Thai, QLocale.Country.Thailand))
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setFont(ui_font())
        self.currentPageChanged.connect(self._fix_year_label)
        self._fix_year_label()

    def _fix_year_label(self, *_):
        # QCalendarWidget ตั้งชื่อวิดเจ็ตภายในไว้เองใน Qt รุ่นปัจจุบัน
        button = self.findChild(QToolButton, "qt_calendar_yearbutton")
        if button is not None:
            button.setText(str(self.yearShown()))
            button.setFont(ui_font())
        year_edit = self.findChild(QSpinBox, "qt_calendar_yearedit")
        if year_edit is not None:
            year_edit.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
            year_edit.setFont(ui_font())

    def showEvent(self, event):
        super().showEvent(event)
        self._fix_year_label()

    def paintCell(self, painter, rect, cell_date):
        # เรียกวาดพื้นหลังจาก Qt ก่อน เพื่อรักษาลักษณะปฏิทิน
        super().paintCell(painter, rect, cell_date)
        # วาดทับบนพื้นเดียวกันด้วยเลขอารบิก (ไม่เปลี่ยนค่า QDate ในระบบ)
        # ใช้สีพื้นจริงที่มาจาก palette เพื่อลบเลขไทยของ Qt
        painter.save()
        is_selected = cell_date == self.selectedDate()
        is_outside = cell_date.month() != self.monthShown() or cell_date.year() != self.yearShown()
        if is_selected:
            bg = self.palette().highlight().color()
            fg = self.palette().highlightedText().color()
        else:
            bg = self.palette().base().color()
            fg = self.palette().mid().color() if is_outside else self.palette().text().color()
        painter.fillRect(rect.adjusted(1, 1, -1, -1), bg)
        painter.setPen(fg)
        painter.setFont(ui_font())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, to_arabic_digits(cell_date.day()))
        painter.restore()


def configure_thai_date_edit(edit):
    """QDateEdit ยังใช้เลขอารบิก ค.ศ. แต่ Popup มีชื่อเดือนและวันภาษาไทย"""
    edit.setCalendarPopup(True)
    edit.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    edit.setDisplayFormat("dd/MM/yyyy")
    edit.setCalendarWidget(ThaiArabicCalendar(edit))
    edit.setFont(ui_font())
    return edit
