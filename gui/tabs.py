from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox,
    QDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt
from gui.dialogs import SingleTimeEditDialog
from gui.styles import apply_card_shadow, to_arabic_digits
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
        # แสดงเลขอารบิกในเวลาเข้า เวลาออก และรายละเอียด
        self.table.setItem(
            row, 5, QTableWidgetItem(to_arabic_digits(time_in))
        )

        self.table.setItem(
            row, 6, QTableWidgetItem(to_arabic_digits(time_out))
        )

        self.table.setItem(
            row, 7, QTableWidgetItem(to_arabic_digits(detail))
        )
        

    
    def show_context_menu(self, pos):

        main_window = self.window()

        if (
            getattr(main_window, "_loaded_attendance_date", None)
            != main_window.date_edit.date().toPyDate()
        ):
            QMessageBox.information(
                self,
                "วันที่ข้อมูลไม่ตรงกัน",
                "กรุณากดประมวลผลข้อมูลสำหรับวันที่เลือก "
                "ก่อนแก้ไขรายการ",
            )
            return
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
            f"🗑️ ลบสถานะและเวลา Manual ({count} รายการ)"
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

        # ปิดเฉพาะส่วนที่อาจทำให้บันทึกผิดวันที่
        self.table.setEnabled(False)
        main_window.date_edit.setEnabled(False)
        main_window.btn_load.setEnabled(False)

        self._status_thread.start()


    def on_status_saved(self, result):
        main_window = self.window()

        self.table.setEnabled(True)
        main_window.date_edit.setEnabled(True)
        main_window.btn_load.setEnabled(True)

        main_window.update_attendance_date_state()

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
                # ข้อมูลเวลาเดิมอาจถูกลบแล้ว
                # ล้างเวลาบนหน้าจอเพื่อไม่ให้แสดงข้อมูลเก่า
                self.table.setItem(
                    row, 5, QTableWidgetItem("-")
                )
                self.table.setItem(
                    row, 6, QTableWidgetItem("-")
                )

                self.table.setItem(
                    row, 7,
                    QTableWidgetItem(
                        "ลบสถานะ/เวลา Manual แล้ว "
                        "รอประมวลผลใหม่"
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
        main_window = self.window()

        self.table.setEnabled(True)
        main_window.date_edit.setEnabled(True)
        main_window.btn_load.setEnabled(True)

        main_window.update_attendance_date_state()

        QMessageBox.critical(
            self,
            "ข้อผิดพลาด",
            f"บันทึกข้อมูลไม่สำเร็จ:\n{error_msg}",
        )

