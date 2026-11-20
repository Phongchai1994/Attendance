from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox,
    QDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt
from gui.dialogs import SingleTimeEditDialog
from gui.styles import apply_card_shadow
from gui.leave_worker import LeaveSaveThread


class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        welcome = QLabel("ระบบบริหารจัดการเวลาปฏิบัติงาน\nเรือนจำจังหวัดจันทบุรี")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("font-size: 28px; font-weight: bold; color: #2C3E50; margin-top: 50px;")
        layout.addWidget(welcome)

        btn_layout = QHBoxLayout()
        self.btn_sync_zk = QPushButton("📥 ดึงข้อมูลจากเครื่องสแกน")
        self.btn_sync_zk.setMinimumHeight(60)
        self.btn_sync_zk.setMinimumWidth(250)
        
        self.btn_sync_leave = QPushButton("☁️ ซิงค์ข้อมูลใบลา (Google Sheets)")
        self.btn_sync_leave.setMinimumHeight(60)
        self.btn_sync_leave.setMinimumWidth(250)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_sync_zk)
        btn_layout.addWidget(self.btn_sync_leave)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setSpacing(25) # เพิ่มระยะห่างระหว่างการ์ด

        # เปลี่ยนสีการ์ดเป็นโทนโมเดิร์น (Tailwind Colors)
        self.card_total = self._create_stat_card("เจ้าหน้าที่ทั้งหมด", "0", "#4F46E5")   # Indigo
        self.card_normal = self._create_stat_card("มาปฏิบัติงานปกติ", "0", "#10B981")  # Emerald
        self.card_late = self._create_stat_card("มาสาย", "0", "#F59E0B")               # Amber
        self.card_leave = self._create_stat_card("ลาหยุด", "0", "#0EA5E9")             # Sky Blue
        self.card_absent = self._create_stat_card("ขาด / ไม่มีข้อมูล", "0", "#EF4444")   # Red

        grid.addWidget(self.card_total['widget'], 0, 0, 1, 2)
        grid.addWidget(self.card_normal['widget'], 1, 0)
        grid.addWidget(self.card_late['widget'], 1, 1)
        grid.addWidget(self.card_leave['widget'], 2, 0)
        grid.addWidget(self.card_absent['widget'], 2, 1)

        layout.addStretch()
        layout.addLayout(grid)
        layout.addStretch()

    def _create_stat_card(self, title, value, bg_color):

        card = QWidget()

        card.setStyleSheet(f"""
            QWidget {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 5px solid {bg_color};
                border-radius: 12px;
            }}

            QLabel {{
                border: none;
                background-color: transparent;
            }}
        """)

        card.setMinimumSize(230, 145)

        apply_card_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 16, 22, 16)
        card_layout.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "color: #64748B; font-weight: bold;"
        )

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"""
            color: {bg_color};
            font-size: 32pt;
            font-weight: bold;
        """)

        lbl_unit = QLabel("คน")
        lbl_unit.setStyleSheet("color: #94A3B8;")

        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_value)
        card_layout.addWidget(lbl_unit)
        card_layout.addStretch()

        return {
            "widget": card,
            "value_label": lbl_value,
        }


    def update_stats(self, total, normal, late, leave, absent):
        self.card_total['value_label'].setText(str(total))
        self.card_normal['value_label'].setText(str(normal))
        self.card_late['value_label'].setText(str(late))
        self.card_leave['value_label'].setText(str(leave))
        self.card_absent['value_label'].setText(str(absent))


class TableTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 1. 🔍 ระบบค้นหา 
        search_layout = QHBoxLayout()
        lbl_search = QLabel("🔍 ค้นหา:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("พิมพ์ค้นหาได้ทุกช่อง (รหัส, ชื่อ, สถานะ, ประเภท...)")
        self.search_box.textChanged.connect(self.filter_table)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["รหัส", "ชื่อ-สกุล", "ตำแหน่ง", "ประเภทการลา", "สถานะ", "เข้า", "ออก", "รายละเอียด"])

        # สลับสีพื้นหลังแต่ละแถว
        self.table.setAlternatingRowColors(True)

        # ลดเส้นตารางที่ไม่จำเป็น
        self.table.setShowGrid(False)

        # ป้องกันการแก้ไข Cell โดยตรง
        # ใช้เมนูคลิกขวาสำหรับแก้ไขข้อมูลแทน
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # ปรับความสูงของแถวให้เหมาะกับภาษาไทย
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.verticalHeader().setMinimumWidth(46)

        self.table.horizontalHeader().setMinimumHeight(44)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        # กำหนดความกว้างเริ่มต้นของแต่ละคอลัมน์
        column_widths = [
            90,    # รหัส
            230,   # ชื่อ-สกุล
            220,   # ตำแหน่ง
            180,   # ประเภทการลา
            160,   # สถานะ
            80,    # เวลาเข้า
            80,    # เวลาออก
            250,   # รายละเอียด
        ]

        for index, width in enumerate(column_widths):
            self.table.setColumnWidth(index, width)

        self.table.horizontalHeader().setStretchLastSection(
            True
        )


        # 👇 1. แก้คอลัมน์ไม่เต็มจอ: บังคับให้คอลัมน์สุดท้าย (รายละเอียด) ยืดจนสุดขอบหน้าต่างเสมอ
        self.table.horizontalHeader().setStretchLastSection(True)
        
        
        # 👇 2. แก้ตัวเลขแถวขาด: ขยายความกว้างของแถบตัวเลขด้านซ้าย เพื่อรองรับเลข 2-3 หลัก
        self.table.verticalHeader().setMinimumWidth(45)
                
        # 2. 🖱️ เปิดให้คลุมดำกด Ctrl / Shift เลือกได้หลายบรรทัด
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)

    def filter_table(self, text):
        """ระบบกรองตารางเมื่อพิมพ์ค้นหา"""
        search_text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def clear_table(self):
        self.table.setRowCount(0)

    # 👇 เพิ่มพารามิเตอร์ position
    def add_row(self, code, name, position, leave_type, status, time_in, time_out, detail):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(str(code)))
        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(position))     # <--- คอลัมน์ใหม่
        self.table.setItem(row, 3, QTableWidgetItem(leave_type))   # <--- ขยับเป็นช่อง 3
        
        status_item = QTableWidgetItem(status)
        if "LEAVE" in status: status_item.setForeground(Qt.GlobalColor.blue)
        elif "LATE" in status: status_item.setForeground(Qt.GlobalColor.darkYellow)
        elif status == "ABSENT": status_item.setForeground(Qt.GlobalColor.red)
        elif status in ["OFFICIAL_DUTY", "ACTING_COMMANDER"]: status_item.setForeground(Qt.GlobalColor.darkMagenta)
        else: status_item.setForeground(Qt.GlobalColor.darkGreen)

        self.table.setItem(row, 4, status_item)                    # <--- ขยับเป็นช่อง 4
        self.table.setItem(row, 5, QTableWidgetItem(time_in))      # <--- ขยับเป็นช่อง 5
        self.table.setItem(row, 6, QTableWidgetItem(time_out))     # <--- ขยับเป็นช่อง 6
        self.table.setItem(row, 7, QTableWidgetItem(detail))       # <--- ขยับเป็นช่อง 7
        

    
    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)

        if not item:
            return

        clicked_row = item.row()

        # รองรับการเลือกเจ้าหน้าที่หลายคน
        selected_rows = [
            r.row()
            for r in self.table.selectionModel().selectedRows()
        ]

        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)
            selected_rows = [clicked_row]

        count = len(selected_rows)
        menu = QMenu(self)

        # กลุ่มแก้ไขเวลา
        action_in = menu.addAction(
            f"แก้ไขเวลาเข้า ({count} รายการ)"
        )

        action_out = menu.addAction(
            f"แก้ไขเวลาออก ({count} รายการ)"
        )

        menu.addSeparator()

        # ประเภทสถานะและช่วงเวลาการลา
        groups = [
            [
                ("NO_FACE_SCAN", "ไม่สแกนหน้า", "FULL_DAY"),
            ],
            [
                ("SICK", "ลาป่วย", "FULL_DAY"),
                ("SICK_MORNING", "ลาป่วยครึ่งวันเช้า", "MORNING"),
                ("SICK_AFTERNOON", "ลาป่วยครึ่งวันบ่าย", "AFTERNOON"),
            ],
            [
                ("VACATION", "ลาพักผ่อน", "FULL_DAY"),
                ("VACATION_MORNING", "ลาพักผ่อนครึ่งวันเช้า", "MORNING"),
                ("VACATION_AFTERNOON", "ลาพักผ่อนครึ่งวันบ่าย", "AFTERNOON"),
            ],
            [
                ("PERSONAL", "ลากิจ", "FULL_DAY"),
                ("PERSONAL_MORNING", "ลากิจครึ่งวันเช้า", "MORNING"),
                ("PERSONAL_AFTERNOON", "ลากิจครึ่งวันบ่าย", "AFTERNOON"),
            ],
            [
                ("MATERNITY", "ลาคลอด", "FULL_DAY"),
                ("ORDINATION", "ลาอุปสมบท", "FULL_DAY"),
                ("STUDY", "ลาศึกษาต่อ", "FULL_DAY"),
            ],
            [
                ("OFFICIAL_DUTY", "ไปราชการ", "FULL_DAY"),
                ("ACTING_COMMANDER", "รักษาราชการแทน ผบ.", "FULL_DAY"),
                ("HOSPITAL_ESCORT", "ควบคุมผู้ต้องขังป่วย รพ.", "FULL_DAY"),
            ],
        ]

        action_map = {}

        for index, group in enumerate(groups):
            if index > 0:
                menu.addSeparator()

            for code, label, session in group:
                action = menu.addAction(
                    f"{label} ({count} รายการ)"
                )
                action_map[action] = (code, label, session)

        # เมนูลบสถานะที่กำหนดเอง
        menu.addSeparator()

        action_delete = menu.addAction(
            f"🗑️ ลบข้อมูลที่กำหนดเอง ({count} รายการ)"
        )

        action_map[action_delete] = (
            "CANCEL_MANUAL",
            "ลบข้อมูลที่กำหนดเอง",
            "FULL_DAY",
        )

        # ตรวจสอบเมนูที่ผู้ใช้เลือก
        action = menu.exec(
            self.table.viewport().mapToGlobal(pos)
        )

        if action == action_in:
            self.edit_multi_time(
                selected_rows,
                is_time_in=True,
            )

        elif action == action_out:
            self.edit_multi_time(
                selected_rows,
                is_time_in=False,
            )

        elif action in action_map:
            code, label, session = action_map[action]

            self.set_multi_status(
                selected_rows,
                code,
                label,
                leave_session=session,
            )


    def edit_multi_time(self, rows, is_time_in):
        col, title, label = (5, "แก้ไขเวลาเข้า", "เวลาเข้าใหม่:") if is_time_in else (6, "แก้ไขเวลาออก", "เวลาออกใหม่:")
        default_time = "08:30" if is_time_in else "16:30"
        current_time = self.table.item(rows[0], col).text()
        
        dialog = SingleTimeEditDialog(title, label, current_time, getattr(self, 'current_date_str', '-'), default_time, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_time = dialog.get_time()
            
            from database.session import SessionLocal
            from models.employee import Employee
            from models.attendance_punch import AttendancePunch
            from datetime import datetime
            
            db = SessionLocal()
            success_count = 0
            not_found = []
            
            try:
                time_obj = datetime.strptime(new_time, "%H:%M").time()
                combined_dt = datetime.combine(self.current_date_obj, time_obj)
                
                # กำหนดทิศทาง (IN หรือ OUT)
                direction = "IN" if is_time_in else "OUT"
                
                for row in rows:
                    emp_code = str(self.table.item(row, 0).text()).strip()
                    emp = db.query(Employee).filter(Employee.employee_code == emp_code).first()
                    
                    if not emp: 
                        not_found.append(emp_code)
                        continue
                    
                    # ค้นหาว่ามีประวัติการสแกนแบบ MANUAL ในวันนั้นและทิศทางนั้นอยู่แล้วหรือไม่
                    existing_punch = db.query(AttendancePunch).filter(
                        AttendancePunch.employee_id == emp.id,
                        # กรองเอาเฉพาะรายการที่เกิดขึ้นในวันที่กำลังแก้ไข
                        AttendancePunch.punched_at >= datetime.combine(self.current_date_obj, datetime.min.time()),
                        AttendancePunch.punched_at <= datetime.combine(self.current_date_obj, datetime.max.time()),
                        AttendancePunch.direction_hint == direction,
                        AttendancePunch.source == "MANUAL"
                    ).first()

                    if existing_punch:
                        # ถ้ามีประวัติแบบ MANUAL อยู่แล้ว ให้อัปเดตเวลาใหม่ทับไปเลย
                        existing_punch.punched_at = combined_dt
                    else:
                        # ถ้ายังไม่มี ให้สร้างการสแกน (Punch) รายการใหม่
                        new_punch = AttendancePunch(
                            employee_id=emp.id,
                            punched_at=combined_dt,
                            direction_hint=direction,
                            source="MANUAL",
                            # สามารถเพิ่ม device_id หรือ source_ref ได้ถ้าระบบบังคับ
                        )
                        db.add(new_punch)
                        
                    # อัปเดต UI ทันที
                    self.table.item(row, col).setText(new_time)
                    status_item = QTableWidgetItem("MANUAL_UPDATE")
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                    self.table.setItem(row, 4, status_item)
                    self.table.setItem(row, 7, QTableWidgetItem("เพิ่มเวลาสแกนสำเร็จ (รอประมวลผลใหม่)"))
                    
                    success_count += 1
                    
                db.commit()
                
                if not_found:
                    QMessageBox.warning(self, "แจ้งเตือน", f"เพิ่มข้อมูลสแกนได้ {success_count} รายการ\nแต่หารหัสเหล่านี้ไม่เจอใน DB:\n{', '.join(not_found)}\n\n💡 กรุณากดปุ่ม 'ประมวลผลข้อมูล' อีกครั้งเพื่อคำนวณสถานะใหม่")
                else:
                    QMessageBox.information(self, "สำเร็จ", f"เพิ่มข้อมูลสแกน (MANUAL) เรียบร้อย {success_count} รายการ\n\n💡 กรุณากดปุ่ม 'ประมวลผลข้อมูล' อีกครั้งเพื่อคำนวณสถานะใหม่")
                    
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "ข้อผิดพลาด DB", f"บันทึกประวัติการสแกนไม่สำเร็จ:\n{str(e)}")
            finally:
                db.close()

    
    def set_multi_status(
        self,
        rows,
        status_code,
        detail_text,
        leave_session="FULL_DAY",
    ):
        target_date = getattr(self, "current_date_obj", None)

        if target_date is None:
            QMessageBox.warning(
                self,
                "แจ้งเตือน",
                "กรุณาโหลดข้อมูลประจำวันที่ต้องการก่อน",
            )
            return

        # ป้องกันการบันทึกซ้อน
        worker = getattr(self, "_status_thread", None)

        if worker is not None and worker.isRunning():
            return

        # ป้องกันการบันทึกพร้อมกับงาน Sync หรือประมวลผล
        main_window = self.window()

        for name in (
            "loader_thread", "zk_thread", "leave_thread"
        ):
            other_worker = getattr(main_window, name, None)

            if other_worker and other_worker.isRunning():
                QMessageBox.warning(
                    self,
                    "แจ้งเตือน",
                    "กรุณารอให้งานปัจจุบันเสร็จสิ้นก่อน",
                )
                return

        codes = [
            self.table.item(row, 0).text().strip()
            for row in rows
            if self.table.item(row, 0) is not None
        ]

        if not codes:
            return

        reply = QMessageBox.question(
            self,
            "ยืนยันการบันทึก",
            f"กำหนดสถานะ: {detail_text}\n"
            f"วันที่: {target_date:%d/%m/%Y}\n"
            f"จำนวน: {len(codes)} คน\n\n"
            "รายการ Manual เดิมอาจถูกแทนที่",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._pending_status = (
            status_code,
            detail_text,
            leave_session,
        )

        self._status_thread = LeaveSaveThread(
            employee_codes=codes,
            target_date=target_date,
            status_code=status_code,
            detail_text=detail_text,
            leave_session=leave_session,
            parent=self,
        )

        self._status_thread.success_signal.connect(
            self.on_status_saved
        )

        self._status_thread.error_signal.connect(
            self.on_status_error
        )

        # ป้องกันการเปลี่ยนวันที่ระหว่างบันทึก
        main_window.setEnabled(False)

        self._status_thread.start()


    def on_status_saved(self, result):
        self.window().setEnabled(True)

        status_code, detail_text, leave_session = (
            self._pending_status
        )

        saved_codes = set(result["saved"])

        # กำหนดสีตามประเภทสถานะ
        if status_code == "NO_FACE_SCAN":
            color = Qt.GlobalColor.darkYellow

        elif status_code in (
            "OFFICIAL_DUTY", "ACTING_COMMANDER"
        ):
            color = Qt.GlobalColor.darkMagenta

        elif status_code == "HOSPITAL_ESCORT":
            color = Qt.GlobalColor.darkYellow

        else:
            color = Qt.GlobalColor.blue

        for row in range(self.table.rowCount()):

            item = self.table.item(row, 0)

            if not item or item.text() not in saved_codes:
                continue

            # กรณียกเลิกสถานะ Manual
            if status_code == "CANCEL_MANUAL":

                status_item = QTableWidgetItem("PENDING_REVIEW")

                status_item.setForeground(
                    Qt.GlobalColor.darkYellow
                )

                self.table.setItem(
                    row, 3, QTableWidgetItem("-")
                )

                self.table.setItem(
                    row, 4, status_item
                )

                self.table.setItem(
                    row, 7,
                    QTableWidgetItem(
                        "ลบสถานะ Manual แล้ว / รอตรวจสอบใหม่"
                    ),
                )

                continue


            status_item = QTableWidgetItem(status_code)
            status_item.setForeground(color)

            self.table.setItem(row, 4, status_item)

            leave_label = (
                "-" if status_code == "NO_FACE_SCAN"
                else detail_text
            )

            self.table.setItem(
                row, 3,
                QTableWidgetItem(leave_label),
            )

            self.table.setItem(
                row, 7,
                QTableWidgetItem(
                    f"{detail_text} (บันทึกแล้ว)"
                ),
            )

            # ลาเต็มวันเท่านั้นที่ไม่ต้องแสดงเวลา
            # ลาครึ่งวันต้องรักษาเวลาเข้าและออกเดิม
            if (
                leave_session == "FULL_DAY"
                and status_code != "NO_FACE_SCAN"
            ):
                self.table.setItem(
                    row, 5, QTableWidgetItem("-")
                )
                self.table.setItem(
                    row, 6, QTableWidgetItem("-")
                )

        message = (
            f"บันทึกสำเร็จ {len(saved_codes)} รายการ"
        )

        if result["skipped"]:
            message += (
                "\n\nรายการที่ข้าม:\n"
                + "\n".join(result["skipped"])
            )

            QMessageBox.warning(
                self, "ผลการบันทึก", message
            )
        else:
            QMessageBox.information(
                self, "สำเร็จ", message
            )

    def on_status_error(self, error_msg):
        self.window().setEnabled(True)

        QMessageBox.critical(
            self,
            "ข้อผิดพลาด",
            f"บันทึกข้อมูลไม่สำเร็จ:\n{error_msg}",
        )



from PyQt6.QtWidgets import QFormLayout, QGroupBox, QHeaderView, QDateEdit
from PyQt6.QtCore import QDate

class EmployeeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)

        # ----------------------------------------
        # ฝั่งซ้าย: ฟอร์มกรอกข้อมูลพนักงาน
        # ----------------------------------------
        form_group = QGroupBox("📝 ข้อมูลพนักงาน")
        form_layout = QFormLayout()
        
        self.txt_id = QLineEdit()
        self.txt_id.setReadOnly(True)
        self.txt_id.setPlaceholderText("Auto ID (ระบบจัดการให้)")
        
        self.txt_code = QLineEdit()
        self.txt_title = QLineEdit()
        self.txt_fname = QLineEdit()
        self.txt_lname = QLineEdit()
        self.txt_pos_name = QLineEdit()
        self.txt_pos_level = QLineEdit()

        form_layout.addRow("ID ภายใน:", self.txt_id)
        form_layout.addRow("รหัสพนักงาน:", self.txt_code)
        form_layout.addRow("คำนำหน้า:", self.txt_title)
        form_layout.addRow("ชื่อ:", self.txt_fname)
        form_layout.addRow("นามสกุล:", self.txt_lname)
        form_layout.addRow("ตำแหน่ง:", self.txt_pos_name)
        form_layout.addRow("ระดับ:", self.txt_pos_level)

        # ปุ่มจัดการ (CRUD)
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 บันทึก (เพิ่ม/แก้)")
        self.btn_save.setStyleSheet("background-color: #10B981; color: white;")
        self.btn_clear = QPushButton("🧹 ล้างฟอร์ม")
        self.btn_delete = QPushButton("🗑️ ปิดการใช้งาน")
        self.btn_delete.setStyleSheet("background-color: #EF4444; color: white;")
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_delete)
        form_layout.addRow(btn_layout)

        # ปุ่ม ZKTeco
        self.btn_sync_zk = QPushButton("📡 ส่งข้อมูลพนักงานนี้ไปเครื่องสแกน")
        self.btn_sync_zk.setStyleSheet("background-color: #3B82F6; color: white; margin-top: 15px;")
        form_layout.addRow(self.btn_sync_zk)

        form_group.setLayout(form_layout)
        form_group.setMaximumWidth(350)
        layout.addWidget(form_group)

        # ----------------------------------------
        # ฝั่งขวา: ตารางแสดงข้อมูล
        # ----------------------------------------
        right_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 ค้นหารหัส, ชื่อ, นามสกุล...")
        self.search_box.textChanged.connect(self.filter_table)
        self.btn_refresh = QPushButton("🔄 โหลดข้อมูลใหม่")
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.btn_refresh)
        right_layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "รหัส", "ชื่อ-สกุล", "ตำแหน่ง", "ระดับ", "สถานะ"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self.load_to_form)
        right_layout.addWidget(self.table)
        
        layout.addLayout(right_layout)

        # ผูกฟังก์ชันปุ่ม
        self.btn_refresh.clicked.connect(self.load_employees)
        self.btn_clear.clicked.connect(self.clear_form)
        self.btn_save.clicked.connect(self.save_employee)
        self.btn_delete.clicked.connect(self.delete_employee)
        self.btn_sync_zk.clicked.connect(self.send_to_zk)

        self.date_hired = QDateEdit()
        self.date_hired.setCalendarPopup(True)
        self.date_hired.setDisplayFormat("dd/MM/yyyy")
        self.date_hired.setDate(QDate.currentDate())
        
        self.date_resigned = QDateEdit()
        self.date_resigned.setCalendarPopup(True)
        self.date_resigned.setDisplayFormat("dd/MM/yyyy")
        # อนุญาตให้เว้นว่างได้ (มี Checkbox ด้านหน้า สำหรับคนที่ยังไม่สิ้นสุดการทำงาน)
        self.date_resigned.setSpecialValueText("ยังคงปฏิบัติงานอยู่") 
        self.date_resigned.setDate(QDate.fromString("01/01/2000", "dd/MM/yyyy")) # ค่าสมมติเพื่อให้โชว์ Special Text
        self.date_resigned.setMinimumDate(QDate.fromString("01/01/2000", "dd/MM/yyyy"))

        # ตอน addRow เข้า Form
        form_layout.addRow("วันเริ่มงาน:", self.date_hired)
        form_layout.addRow("วันสิ้นสุด (ย้าย/ออก):", self.date_resigned)

    def filter_table(self, text):
        search_text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def load_employees(self):
        from database.session import SessionLocal
        from models.employee import Employee
        db = SessionLocal()
        try:
            emps = db.query(Employee).order_by(Employee.employee_code).all()
            self.table.setRowCount(0)
            for emp in emps:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(emp.id)))
                self.table.setItem(row, 1, QTableWidgetItem(emp.employee_code))
                
                full_name = f"{emp.title or ''}{emp.first_name or ''} {emp.last_name or ''}".strip()
                self.table.setItem(row, 2, QTableWidgetItem(full_name))
                self.table.setItem(row, 3, QTableWidgetItem(emp.position_name or "-"))
                self.table.setItem(row, 4, QTableWidgetItem(emp.position_level or "-"))
                
                status_txt = "ใช้งาน" if emp.is_active else "ปิดใช้งาน"
                status_item = QTableWidgetItem(status_txt)
                status_item.setForeground(Qt.GlobalColor.darkGreen if emp.is_active else Qt.GlobalColor.red)
                self.table.setItem(row, 5, status_item)
        finally:
            db.close()

    def load_to_form(self, item):
        row = item.row()
        emp_id = self.table.item(row, 0).text()
        
        from database.session import SessionLocal
        from models.employee import Employee
        db = SessionLocal()
        emp = db.query(Employee).filter(Employee.id == int(emp_id)).first()
        if emp:
            self.txt_id.setText(str(emp.id))
            self.txt_code.setText(emp.employee_code)
            self.txt_title.setText(emp.title or "")
            self.txt_fname.setText(emp.first_name or "")
            self.txt_lname.setText(emp.last_name or "")
            self.txt_pos_name.setText(emp.position_name or "")
            self.txt_pos_level.setText(emp.position_level or "")
        db.close()

    def clear_form(self):
        self.txt_id.clear()
        self.txt_code.clear()
        self.txt_title.clear()
        self.txt_fname.clear()
        self.txt_lname.clear()
        self.txt_pos_name.clear()
        self.txt_pos_level.clear()
        self.table.clearSelection()

    def save_employee(self):
        code = self.txt_code.text().strip()
        fname = self.txt_fname.text().strip()
        
        if not code or not fname:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณากรอก รหัสพนักงาน และ ชื่อ เป็นอย่างน้อย")
            return
            
        from database.session import SessionLocal
        from models.employee import Employee
        db = SessionLocal()
        try:
            emp_id = self.txt_id.text()
            if emp_id: # อัปเดตข้อมูลเก่า
                emp = db.query(Employee).filter(Employee.id == int(emp_id)).first()
                emp.employee_code = code
                emp.title = self.txt_title.text().strip()
                emp.first_name = fname
                emp.last_name = self.txt_lname.text().strip()
                emp.position_name = self.txt_pos_name.text().strip()
                emp.position_level = self.txt_pos_level.text().strip()
                emp.is_active = True
                msg = "อัปเดตข้อมูลสำเร็จ"
            else: # เพิ่มข้อมูลใหม่
                exist = db.query(Employee).filter(Employee.employee_code == code).first()
                if exist:
                    QMessageBox.warning(self, "แจ้งเตือน", "รหัสพนักงานนี้มีในระบบแล้ว")
                    return
                new_emp = Employee(
                    employee_code=code, title=self.txt_title.text().strip(),
                    first_name=fname, last_name=self.txt_lname.text().strip(),
                    position_name=self.txt_pos_name.text().strip(),
                    position_level=self.txt_pos_level.text().strip(),
                    is_active=True
                )
                db.add(new_emp)
                msg = "เพิ่มพนักงานใหม่สำเร็จ"
                
            db.commit()
            QMessageBox.information(self, "สำเร็จ", msg)
            self.load_employees()
            self.clear_form()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "ข้อผิดพลาด", str(e))
        finally:
            db.close()

    def delete_employee(self):
        emp_id = self.txt_id.text()
        if not emp_id: return
        
        reply = QMessageBox.question(self, "ยืนยัน", "ต้องการปิดการใช้งานพนักงานคนนี้หรือไม่?\n(ข้อมูลจะไม่ถูกลบเพื่อรักษาประวัติการทำงาน)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from database.session import SessionLocal
            from models.employee import Employee
            db = SessionLocal()
            try:
                emp = db.query(Employee).filter(Employee.id == int(emp_id)).first()
                emp.is_active = False
                db.commit()
                self.load_employees()
                self.clear_form()
                QMessageBox.information(self, "สำเร็จ", "ปิดการใช้งานสำเร็จ")
            except Exception as e:
                db.rollback()
            finally:
                db.close()

    def send_to_zk(self):
        emp_id = self.txt_id.text()
        code = self.txt_code.text().strip()
        fname = self.txt_fname.text().strip()
        if not emp_id or not code:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาเลือกพนักงานจากตารางก่อน")
            return
            
        from services.zk_sync_service import ZKSyncService
        from database.session import SessionLocal
        
        db = SessionLocal()
        service = ZKSyncService(db, device_ip="192.168.1.201")
        # เราใช้ ID ของพนักงานใน Database เป็น UID เพื่อให้ตรงกัน
        res = service.upload_employee_to_zk(employee_code=code, employee_name=fname, uid=int(emp_id))
        db.close()
        
        if res["status"] == "success":
            QMessageBox.information(self, "สำเร็จ", res["msg"])
        else:
            QMessageBox.critical(self, "ข้อผิดพลาด ZKTeco", res["msg"])