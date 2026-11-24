
"""Employee Management V2 — หน้าจอจัดการเจ้าหน้าที่ใหม่"""

from datetime import date

from PyQt6.QtCore import (
    QDate, QLocale, Qt, QThread, QTimer, pyqtSignal
)
from PyQt6.QtGui import QBrush, QColor, QFont, QFontDatabase
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from services.employee_service import (
    load_employee_snapshot,
    save_employee,
    set_employee_active,
    sync_employee_to_zk,
)


def get_employee_font():
    """เลือกฟอนต์ TH SarabunPSK ที่ติดตั้งจริง"""

    families = {
        name.lower().replace(" ", ""): name
        for name in QFontDatabase.families()
    }

    for preferred in (
        "TH SarabunPSK",
        "TH Sarabun PSK",
        "TH Sarabun New",
    ):
        actual = families.get(
            preferred.lower().replace(" ", "")
        )

        if actual:
            return QFont(actual, 16)

    # หากไม่มีฟอนต์ จะใช้ฟอนต์กลางของโปรแกรม
    return QApplication.font()


class EmployeeTask(QThread):
    """ทำงานฐานข้อมูลใน Thread แยก"""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, operation, payload=None, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.payload = payload

    
    def run(self):
        try:
            if self.operation == "load":
                result = load_employee_snapshot()

            elif self.operation == "save":
                # บันทึก PostgreSQL ก่อน
                result = save_employee(self.payload)

                # จากนั้นส่งไปเครื่องสแกน
                # หากส่งไม่สำเร็จ ต้องไม่รายงานว่า DB บันทึกล้มเหลว
                try:
                    result["zk_sync"] = sync_employee_to_zk(
                        result["id"]
                    )
                except Exception as exc:
                    result["zk_sync"] = {
                        "status": "error",
                        "msg": str(exc),
                    }

            elif self.operation == "active":
                result = set_employee_active(
                    self.payload["id"],
                    self.payload["active"],
                )

            elif self.operation == "sync_zk":
                result = sync_employee_to_zk(
                    self.payload["id"]
                )

            else:
                raise ValueError("ไม่รู้จักคำสั่ง")

            self.succeeded.emit(result)

        except Exception as exc:
            self.failed.emit(str(exc))



class OptionalDate(QWidget):
    """รองรับวันที่ที่สามารถเว้นว่างเป็น NULL ได้"""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.check = QCheckBox("ระบุวันที่")
        self.edit = QDateEdit()
        self.edit.setCalendarPopup(True)
        self.edit.calendarWidget().setFont(
            get_employee_font()
        )

        self.edit.setLocale(
            QLocale(
                QLocale.Language.English,
                QLocale.Country.UnitedStates,
            )
        )

        self.edit.setDisplayFormat("dd/MM/yyyy")
        self.edit.setMinimumDate(QDate(1900, 1, 1))
        self.edit.setMaximumDate(QDate(2100, 12, 31))
        self.edit.setDate(QDate.currentDate())
        self.edit.setEnabled(False)

        self.check.toggled.connect(
            self.edit.setEnabled
        )

        layout.addWidget(self.check)
        layout.addWidget(self.edit, 1)

    def get_value(self):
        if not self.check.isChecked():
            return None

        return self.edit.date().toPyDate().isoformat()

    def set_value(self, value):
        if not value:
            self.check.setChecked(False)
            self.edit.setDate(QDate.currentDate())
            return

        d = date.fromisoformat(value)

        self.edit.setDate(
            QDate(d.year, d.month, d.day)
        )

        self.check.setChecked(True)


class EmployeeTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._records = []
        self._departments = []
        self._selected_id = None
        self._selected_record = None
        self._worker = None
        self._reload_after_task = False
        self._pending_select_id = None

        self._build_ui()

        # โหลดข้อมูลเมื่อหน้าจอพร้อมใช้งาน
        QTimer.singleShot(0, self.reload_data)


    def _apply_dropdown_fonts(self):
        """บังคับฟอนต์ทั้งช่อง ComboBox และรายการ Popup"""

        font = get_employee_font()

        combos = (
            self.status_filter,
            self.dep_filter,
            self.position_name,
            self.position_level,
            self.department,
        )

        for combo in combos:
            combo.setFont(font)
            combo.view().setFont(font)

            if combo.isEditable():
                combo.lineEdit().setFont(font)


    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ส่วนหัว
        heading = QLabel("จัดการข้อมูลเจ้าหน้าที่")
        heading.setObjectName("page_title")

        desc = QLabel(
            "ค้นหา เพิ่ม แก้ไข และจัดการสถานะ "
            "โดยเก็บประวัติเดิมไว้"
        )
        desc.setObjectName("page_description")

        root.addWidget(heading)
        root.addWidget(desc)

        # แถบค้นหาและตัวกรอง
        toolbar = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "ค้นหารหัส ชื่อ นามสกุล ตำแหน่ง หรือสังกัด..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(
            self.apply_filters
        )
        toolbar.addWidget(self.search, 3)

        self.status_filter = QComboBox()
        self.status_filter.addItem("ทุกสถานะ", "all")
        self.status_filter.addItem("ใช้งาน", "active")
        self.status_filter.addItem("ปิดใช้งาน", "inactive")
        self.status_filter.currentIndexChanged.connect(
            self.apply_filters
        )
        toolbar.addWidget(self.status_filter, 1)

        self.dep_filter = QComboBox()
        self.dep_filter.addItem("ทุกสังกัด", None)
        self.dep_filter.currentIndexChanged.connect(
            self.apply_filters
        )
        toolbar.addWidget(self.dep_filter, 1)

        self.btn_reload = QPushButton("โหลดใหม่")
        self.btn_reload.clicked.connect(
            self.reload_data
        )
        toolbar.addWidget(self.btn_reload)

        self.btn_new = QPushButton("+ เพิ่มเจ้าหน้าที่")
        self.btn_new.setObjectName("btn_primary")
        self.btn_new.clicked.connect(
            self.new_employee
        )
        toolbar.addWidget(self.btn_new)

        root.addLayout(toolbar)

        # แบ่งหน้าจอซ้ายและขวา
        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        # -----------------------------
        # ฝั่งซ้าย: ตารางเจ้าหน้าที่
        # -----------------------------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.count_label = QLabel(
            "กำลังโหลดข้อมูล..."
        )
        left_layout.addWidget(self.count_label)

        self.table = QTableWidget()

        headers = [
            "รหัส",
            "ชื่อ-นามสกุล",
            "ตำแหน่ง",
            "ระดับ",
            "สังกัด",
            "วันเริ่มงาน",
            "สถานะ",
        ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setDefaultSectionSize(
            34
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        column_widths = [
            100, 190, 150, 95, 170, 110, 100
        ]

        for index, width in enumerate(column_widths):
            self.table.setColumnWidth(index, width)

        self.table.itemSelectionChanged.connect(
            self._select_current
        )

        left_layout.addWidget(self.table, 1)
        splitter.addWidget(left)

        # -----------------------------
        # ฝั่งขวา: แบบฟอร์มเจ้าหน้าที่
        # -----------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        form_container = QWidget()
        form_root = QVBoxLayout(form_container)
        form_root.setContentsMargins(8, 0, 8, 8)

        form_group = QGroupBox(
            "ข้อมูลเจ้าหน้าที่"
        )

        form = QFormLayout(form_group)
        form.setSpacing(10)

        self.id_label = QLabel(
            "เพิ่มรายการใหม่"
        )
        form.addRow("ID ภายใน:", self.id_label)

        self.code = QLineEdit()
        self.code.setMaxLength(30)
        form.addRow(
            "รหัสเจ้าหน้าที่ *:",
            self.code,
        )

        self.title = QLineEdit()
        self.title.setMaxLength(30)
        form.addRow(
            "คำนำหน้า:",
            self.title,
        )

        self.first_name = QLineEdit()
        self.first_name.setMaxLength(100)
        form.addRow(
            "ชื่อ *:",
            self.first_name,
        )

        self.last_name = QLineEdit()
        self.last_name.setMaxLength(100)
        form.addRow(
            "นามสกุล *:",
            self.last_name,
        )

        
        # ตำแหน่ง: เลือกจากรายการที่มีหรือพิมพ์ค่าใหม่ได้
        self.position_name = QComboBox()
        self.position_name.setEditable(True)
        self.position_name.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )
        self.position_name.setMaxVisibleItems(15)
        self.position_name.lineEdit().setMaxLength(150)
        form.addRow("ตำแหน่ง:", self.position_name)

        # ระดับ: เลือกจากรายการที่มีหรือพิมพ์ค่าใหม่ได้
        self.position_level = QComboBox()
        self.position_level.setEditable(True)
        self.position_level.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )
        self.position_level.setMaxVisibleItems(15)
        self.position_level.lineEdit().setMaxLength(100)
        form.addRow("ระดับ:", self.position_level)

        # สังกัด: อ่านจากตาราง departments
        self.department = QComboBox()
        self.department.addItem("ไม่ระบุสังกัด", None)
        self.department.setMaxVisibleItems(15)
        form.addRow("หน่วยงาน/สังกัด:", self.department)


        self.card_no = QLineEdit()
        self.card_no.setMaxLength(50)
        form.addRow(
            "หมายเลขบัตร:",
            self.card_no,
        )

        self.legacy_user_id = QLineEdit()
        self.legacy_user_id.setPlaceholderText(
            "ตัวเลข ID จากเครื่องสแกน (ถ้ามี)"
        )
        self.legacy_user_id.setMaxLength(19)
        form.addRow(
            "Legacy User ID:",
            self.legacy_user_id,
        )

        # วันที่สามารถเว้นว่างได้
        self.first_hired_date = OptionalDate()
        form.addRow(
            "วันบรรจุครั้งแรก:",
            self.first_hired_date,
        )

        self.start_date = OptionalDate()
        form.addRow(
            "วันเริ่มงานที่เรือนจำ:",
            self.start_date,
        )

        self.resigned_date = OptionalDate()
        form.addRow(
            "วันสิ้นสุดงาน:",
            self.resigned_date,
        )

        self.state_label = QLabel(
            "สถานะ: รายการใหม่"
        )
        form.addRow(
            "สถานะปัจจุบัน:",
            self.state_label,
        )

        form_root.addWidget(form_group)

        # ปุ่มบันทึก / ปิดใช้งาน / เปิดใช้งาน
        buttons = QHBoxLayout()

        self.btn_save = QPushButton(
            "บันทึกข้อมูล"
        )
        self.btn_save.setObjectName(
            "btn_primary"
        )
        self.btn_save.clicked.connect(
            self.save_current
        )
        buttons.addWidget(self.btn_save)

        self.btn_toggle = QPushButton(
            "ปิดใช้งาน"
        )
        self.btn_toggle.setEnabled(False)
        self.btn_toggle.clicked.connect(
            self.toggle_active
        )
        buttons.addWidget(self.btn_toggle)

        self.btn_sync_zk = QPushButton(
            "ส่งข้อมูลไปเครื่องสแกน"
        )
        self.btn_sync_zk.setEnabled(False)
        self.btn_sync_zk.clicked.connect(
            self.sync_zk_current
        )
        buttons.addWidget(self.btn_sync_zk)

        form_root.addLayout(buttons)
        form_root.addStretch()

        scroll.setWidget(form_container)
        splitter.addWidget(scroll)

        splitter.setSizes([650, 470])

        self._clear_form()
        self._apply_dropdown_fonts()

    # ---------------------------------
    # การทำงานกับ Worker
    # ---------------------------------
    def _start_task(self, operation, payload=None):
        if (
            self._worker is not None
            and self._worker.isRunning()
        ):
            return False

        self._worker = EmployeeTask(
            operation,
            payload,
            parent=self,
        )

        self._worker.succeeded.connect(
            self._task_succeeded
        )

        self._worker.failed.connect(
            self._task_failed
        )

        self._worker.finished.connect(
            self._task_finished
        )

        self._set_busy(True)
        self._worker.start()

        return True

    def _set_busy(self, busy):
        self.btn_reload.setEnabled(not busy)
        self.btn_save.setEnabled(not busy)
        self.btn_new.setEnabled(not busy)

        self.btn_toggle.setEnabled(
            not busy
            and self._selected_record is not None
        )

        self.table.setEnabled(not busy)
        self.search.setEnabled(not busy)
        self.dep_filter.setEnabled(not busy)
        self.status_filter.setEnabled(not busy)

        self.code.setEnabled(not busy)
        self.title.setEnabled(not busy)
        self.first_name.setEnabled(not busy)
        self.last_name.setEnabled(not busy)
        self.position_name.setEnabled(not busy)
        self.position_level.setEnabled(not busy)
        self.department.setEnabled(not busy)
        self.card_no.setEnabled(not busy)
        self.legacy_user_id.setEnabled(not busy)

        for widget in (
            self.first_hired_date,
            self.start_date,
            self.resigned_date,
        ):
            widget.setEnabled(not busy)

        self.btn_sync_zk.setEnabled(
            not busy
            and self._selected_record is not None
            and self._selected_record["is_active"]
        )

    def reload_data(self):
        self.count_label.setText(
            "กำลังโหลดข้อมูลเจ้าหน้าที่..."
        )
        self._start_task("load")

    
    def _task_succeeded(self, result):
        operation = self._worker.operation

        if operation == "load":
            self._records = result["employees"]
            self._departments = result["departments"]

            self._update_department_options()
            self._update_position_level_options()
            self._render_table()
            return

        if operation == "save":
            self._pending_select_id = result["id"]
            self._reload_after_task = True

            zk_result = result.get("zk_sync", {})

            if zk_result.get("status") == "success":
                QMessageBox.information(
                    self,
                    "บันทึกสำเร็จ",
                    "บันทึก PostgreSQL เรียบร้อย\n"
                    + zk_result["msg"],
                )
            else:
                QMessageBox.warning(
                    self,
                    "บันทึกฐานข้อมูลแล้ว",
                    "บันทึก PostgreSQL สำเร็จ\n"
                    "แต่ยังส่งไปเครื่องสแกนไม่สำเร็จ\n\n"
                    + zk_result.get("msg", "ไม่ทราบสาเหตุ")
                    + "\n\nสามารถกดส่งข้อมูลไปเครื่องสแกนอีกครั้งได้",
                )

        elif operation == "active":
            self._pending_select_id = result["id"]
            self._reload_after_task = True

            QMessageBox.information(
                self,
                "สำเร็จ",
                "เปลี่ยนสถานะเจ้าหน้าที่เรียบร้อยแล้ว",
            )

        elif operation == "sync_zk":
            if result.get("status") == "success":
                QMessageBox.information(
                    self,
                    "ส่งข้อมูลสำเร็จ",
                    result["msg"],
                )
            else:
                QMessageBox.warning(
                    self,
                    "ส่งข้อมูลไม่สำเร็จ",
                    result.get("msg", "ไม่ทราบสาเหตุ"),
                )


    def _task_failed(self, message):
        QMessageBox.critical(
            self,
            "ข้อผิดพลาด",
            f"ดำเนินการไม่สำเร็จ:\n{message}",
        )

    def _task_finished(self):
        worker = self._worker
        self._worker = None

        if worker is not None:
            worker.deleteLater()

        self._set_busy(False)

        if self._reload_after_task:
            self._reload_after_task = False
            self.reload_data()

    def _update_position_level_options(self):
        """สร้างตัวเลือกจากตำแหน่งและระดับที่มีใน DB"""

        fields = (
            (self.position_name, "position_name"),
            (self.position_level, "position_level"),
        )

        for combo, key in fields:
            previous = combo.currentText().strip()

            values = sorted(
                {
                    str(rec.get(key) or "").strip()
                    for rec in self._records
                    if str(rec.get(key) or "").strip()
                },
                key=str.casefold,
            )

            combo.blockSignals(True)

            try:
                combo.clear()
                combo.addItem("")
                combo.addItems(values)
                combo.setCurrentText(previous)
            finally:
                combo.blockSignals(False)

    # ---------------------------------
    # ข้อมูลหน่วยงาน
    # ---------------------------------
    def _update_department_options(self):
        selected_form = self.department.currentData()
        selected_filter = self.dep_filter.currentData()

        self.department.blockSignals(True)
        self.dep_filter.blockSignals(True)

        try:
            self.department.clear()
            self.department.addItem(
                "ไม่ระบุสังกัด",
                None,
            )

            self.dep_filter.clear()
            self.dep_filter.addItem(
                "ทุกสังกัด",
                None,
            )

            for department in self._departments:
                caption = department["name"]

                if not department["is_active"]:
                    caption += " (ปิดใช้งาน)"

                self.department.addItem(
                    caption,
                    department["id"],
                )

                self.dep_filter.addItem(
                    caption,
                    department["id"],
                )

            self._select_combo_data(
                self.department,
                selected_form,
            )

            self._select_combo_data(
                self.dep_filter,
                selected_filter,
            )

        finally:
            self.department.blockSignals(False)
            self.dep_filter.blockSignals(False)

    @staticmethod
    def _select_combo_data(combo, value):
        index = combo.findData(value)

        combo.setCurrentIndex(
            index if index >= 0 else 0
        )

    @staticmethod
    def _format_date(value):
        if not value:
            return "-"

        return date.fromisoformat(value).strftime(
            "%d/%m/%Y"
        )

    # ---------------------------------
    # แสดงข้อมูลเจ้าหน้าที่
    # ---------------------------------
    def _render_table(self):
        preferred_id = (
            self._pending_select_id
            if self._pending_select_id is not None
            else self._selected_id
        )

        self._pending_select_id = None

        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)

        try:
            self.table.setRowCount(
                len(self._records)
            )

            for row, rec in enumerate(self._records):
                full_name = "".join([
                    rec["title"],
                    rec["first_name"],
                ]) + " " + rec["last_name"]

                values = [
                    rec["employee_code"],
                    full_name.strip(),
                    rec["position_name"] or "-",
                    rec["position_level"] or "-",
                    rec["department_name"] or "-",
                    self._format_date(rec["start_date"]),
                    (
                        "ใช้งาน"
                        if rec["is_active"]
                        else "ปิดใช้งาน"
                    ),
                ]

                for col, value in enumerate(values):
                    item = QTableWidgetItem(
                        str(value)
                    )

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        rec["id"],
                    )

                    if col == 6:
                        color = (
                            "#15803D"
                            if rec["is_active"]
                            else "#B91C1C"
                        )

                        item.setForeground(
                            QBrush(QColor(color))
                        )

                    self.table.setItem(
                        row,
                        col,
                        item,
                    )

        finally:
            self.table.setUpdatesEnabled(True)
            self.table.blockSignals(False)

        self.apply_filters()

        matching = next(
            (
                rec
                for rec in self._records
                if rec["id"] == preferred_id
            ),
            None,
        )

        if matching is not None:
            self._populate_form(matching)

            for row in range(
                self.table.rowCount()
            ):
                item = self.table.item(row, 0)

                if (
                    item.data(
                        Qt.ItemDataRole.UserRole
                    ) == preferred_id
                ):
                    if not self.table.isRowHidden(row):
                        self.table.selectRow(row)
                    break

        elif self._selected_id is not None:
            self._clear_form()

    def apply_filters(self, *_):
        search = (
            self.search.text()
            .strip()
            .casefold()
        )

        status = self.status_filter.currentData()
        department_id = self.dep_filter.currentData()

        shown = 0

        for row, rec in enumerate(self._records):
            target = " ".join(
                str(rec.get(k) or "")
                for k in (
                    "employee_code",
                    "title",
                    "first_name",
                    "last_name",
                    "position_name",
                    "position_level",
                    "department_name",
                )
            ).casefold()

            matches = (
                (not search or search in target)
                and (
                    status == "all"
                    or rec["is_active"] == (
                        status == "active"
                    )
                )
                and (
                    department_id is None
                    or rec["department_id"] == department_id
                )
            )

            self.table.setRowHidden(
                row,
                not matches,
            )

            shown += bool(matches)

        self.count_label.setText(
            f"แสดง {shown:,} จากทั้งหมด "
            f"{len(self._records):,} คน"
        )

    # ---------------------------------
    # เลือกเจ้าหน้าที่ / แสดงข้อมูลฟอร์ม
    # ---------------------------------
    def _select_current(self):
        row = self.table.currentRow()

        if (
            row < 0
            or self.table.isRowHidden(row)
        ):
            return

        item = self.table.item(row, 0)

        if item is None:
            return

        employee_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        record = next(
            (
                rec
                for rec in self._records
                if rec["id"] == employee_id
            ),
            None,
        )

        if record is not None:
            self._populate_form(record)

    def _clear_form(self):
        self._selected_id = None
        self._selected_record = None
        self.id_label.setText(
            "เพิ่มรายการใหม่"
        )

        for field in (
            self.code,
            self.title,
            self.first_name,
            self.last_name,
            self.card_no,
            self.legacy_user_id,
        ):
            field.clear()

        self.position_name.setCurrentText("")
        self.position_level.setCurrentText("")

        self._select_combo_data(
            self.department,
            None,
        )

        for field in (
            self.first_hired_date,
            self.start_date,
            self.resigned_date,
        ):
            field.set_value(None)

        self.state_label.setText(
            "สถานะ: รายการใหม่"
        )

        self.btn_toggle.setEnabled(False)
        
        self.code.setReadOnly(False)
        self.btn_sync_zk.setEnabled(False)

    def new_employee(self):
        self.table.clearSelection()
        self._clear_form()
        self.code.setFocus()

    def _populate_form(self, record):
        self._selected_id = record["id"]
        self._selected_record = record

        self.id_label.setText(
            str(record["id"])
        )

        for key, field in (
            ("employee_code", self.code),
            ("title", self.title),
            ("first_name", self.first_name),
            ("last_name", self.last_name),
            ("card_no", self.card_no),
        ):
            field.setText(
                record[key] or ""
            )

        self.position_name.setCurrentText(
            record["position_name"] or ""
        )
        self.position_level.setCurrentText(
            record["position_level"] or ""
        )
        self.legacy_user_id.setText(
            str(record["legacy_user_id"])
            if record["legacy_user_id"] is not None
            else ""
        )

        self._select_combo_data(
            self.department,
            record["department_id"],
        )

        self.first_hired_date.set_value(
            record["first_hired_date"]
        )

        self.start_date.set_value(
            record["start_date"]
        )

        self.resigned_date.set_value(
            record["resigned_date"]
        )

        active = record["is_active"]

        self.state_label.setText(
            "สถานะ: ใช้งาน"
            if active
            else "สถานะ: ปิดใช้งาน"
        )

        self.btn_toggle.setText(
            "ปิดใช้งาน"
            if active
            else "เปิดใช้งานอีกครั้ง"
        )

        self.btn_toggle.setEnabled(True)
        # ไม่ให้แก้รหัสเดิมจนกว่าจะมีระบบย้ายรหัสเครื่องสแกน
        self.code.setReadOnly(True)

        self.btn_sync_zk.setEnabled(
            record["is_active"]
        )

    # ---------------------------------
    # เพิ่ม / แก้ไขข้อมูล
    # ---------------------------------
    def save_current(self):
        code = self.code.text().strip()
        first = self.first_name.text().strip()
        last = self.last_name.text().strip()

        if not code or not first or not last:
            QMessageBox.warning(
                self,
                "ข้อมูลไม่ครบ",
                "กรุณากรอกรหัสเจ้าหน้าที่ "
                "ชื่อ และนามสกุล",
            )
            return

        payload = {
            "id": self._selected_id,
            "employee_code": code,
            "title": self.title.text(),
            "first_name": first,
            "last_name": last,
            "position_name": self.position_name.currentText().strip(),
            "position_level": self.position_level.currentText().strip(),
            "department_id": self.department.currentData(),
            "card_no": self.card_no.text(),
            "legacy_user_id": (
                self.legacy_user_id.text().strip()
            ),
            "first_hired_date": (
                self.first_hired_date.get_value()
            ),
            "start_date": self.start_date.get_value(),
            "resigned_date": (
                self.resigned_date.get_value()
            ),
        }

        self._start_task(
            "save",
            payload,
        )

    # ---------------------------------
    # ปิดใช้งาน / เปิดใช้งานอีกครั้ง
    # ---------------------------------
    def toggle_active(self):
        if self._selected_record is None:
            return

        active = not self._selected_record[
            "is_active"
        ]

        verb = (
            "เปิดใช้งาน"
            if active
            else "ปิดใช้งาน"
        )

        answer = QMessageBox.question(
            self,
            "ยืนยันการเปลี่ยนสถานะ",
            f"ต้องการ{verb}เจ้าหน้าที่รหัส "
            f"{self._selected_record['employee_code']} "
            "หรือไม่?\n"
            "ระบบจะไม่ลบประวัติการลงเวลาและใบลา",
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self._start_task(
                "active",
                {
                    "id": self._selected_id,
                    "active": active,
                },
            )


    def sync_zk_current(self):
        """ส่งข้อมูลที่บันทึกใน DB ไปเครื่องสแกนอีกครั้ง"""

        if self._selected_record is None:
            return

        if not self._selected_record["is_active"]:
            QMessageBox.warning(
                self,
                "แจ้งเตือน",
                "เจ้าหน้าที่ถูกปิดใช้งาน",
            )
            return

        self._start_task(
            "sync_zk",
            {"id": self._selected_record["id"]},
        )
