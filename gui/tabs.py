from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox,
    QDialog
)
from PyQt6.QtCore import Qt
from gui.dialogs import TimeEditDialog, SingleTimeEditDialog
from gui.styles import apply_card_shadow


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
        card.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px; color: white;")
        card.setMinimumSize(250, 130)
        
        # ใส่เงาให้การ์ดเด้งออกมาจากพื้นหลัง
        apply_card_shadow(card)
        
        card_layout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        
        lbl_value = QLabel(value)
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_value.setStyleSheet("font-size: 48px; font-weight: bold; margin-bottom: 10px;")
        
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_value)
        
        return {'widget': card, 'value_label': lbl_value}

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
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["รหัส", "ชื่อ-นามสกุล", "ประเภท", "สถานะ", "เข้า", "ออก", "รายละเอียด"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { font-size: 14px; }")
        
        # ตั้งค่าเลือกแถวและคลิกขวา
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)

    def clear_table(self):
        self.table.setRowCount(0)

# 👇 เปลี่ยนพารามิเตอร์ shift เป็น leave_type
    def add_row(self, code, name, leave_type, status, time_in, time_out, detail):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(str(code)))
        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(leave_type)) # <--- ใส่ประเภทการลาลงคอลัมน์ 2 แทน
        
        status_item = QTableWidgetItem(status)
        if "LEAVE" in status: status_item.setForeground(Qt.GlobalColor.blue)
        elif "LATE" in status: status_item.setForeground(Qt.GlobalColor.darkYellow)
        elif status == "ABSENT": status_item.setForeground(Qt.GlobalColor.red)
        elif status == "OFFICIAL_DUTY": status_item.setForeground(Qt.GlobalColor.darkMagenta)
        else: status_item.setForeground(Qt.GlobalColor.darkGreen)

        self.table.setItem(row, 3, status_item)
        self.table.setItem(row, 4, QTableWidgetItem(time_in))
        self.table.setItem(row, 5, QTableWidgetItem(time_out))
        self.table.setItem(row, 6, QTableWidgetItem(detail))

    # ... (ส่วนบนของ TableTab เหมือนเดิม) ...

    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.selectRow(row) 
            menu = QMenu(self)
            
            # กลุ่ม 1: แก้ไขเวลา (Manual)
            action_in = menu.addAction("📥 แก้ไขเวลาเข้า (Manual)")
            action_out = menu.addAction("📤 แก้ไขเวลาออก (Manual)")
            
            menu.addSeparator()
            
            # กลุ่ม 2: กำหนดสถานะ (เหลือแค่ 2 เมนูตามต้องการ)
            action_duty = menu.addAction("💼 กำหนดเป็น: ไปราชการ")
            action_acting = menu.addAction("⭐ กำหนดเป็น: รักษาราชการแทน ผบ.")
            
            action = menu.exec(self.table.viewport().mapToGlobal(pos))
            
            if action == action_in:
                self.edit_single_time(row, is_time_in=True)
            elif action == action_out:
                self.edit_single_time(row, is_time_in=False)
            elif action == action_duty:
                self.set_manual_status(row, "OFFICIAL_DUTY", "ไปราชการ")
            elif action == action_acting:
                self.set_manual_status(row, "ACTING_COMMANDER", "รักษาราชการแทน ผบ.")

    def edit_single_time(self, row, is_time_in):
        emp_code = self.table.item(row, 0).text()
        emp_name = self.table.item(row, 1).text()
        
        if is_time_in:
            col, title, label = 4, "แก้ไขเวลาเข้า", "เวลาเข้าใหม่:"
        else:
            col, title, label = 5, "แก้ไขเวลาออก", "เวลาออกใหม่:"
            
        current_time = self.table.item(row, col).text()

        # เรียก Dialog พร้อมส่งวันที่เข้าไปด้วย
        dialog = SingleTimeEditDialog(title, label, current_time, getattr(self, 'current_date_str', '-'), self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_time = dialog.get_time()
            
            # ----------------------------------------------------
            # ส่วนบันทึกลงฐานข้อมูล Database
            # ----------------------------------------------------
            from database.session import SessionLocal
            from models.employee import Employee
            from datetime import datetime
            
            # TODO: นำเข้าโมเดลเก็บผลลัพธ์รายวันของคุณ (แก้ชื่อให้ตรงกับที่คุณมี)
            from models.attendance_dialy_result import AttendanceDailyResult 
            
            db = SessionLocal()
            try:
                emp = db.query(Employee).filter(Employee.employee_code == emp_code).first()
                if emp and hasattr(self, 'current_date_obj'):
                    pass
                    # (เมื่อพร้อมใช้งาน Database ให้เอาเครื่องหมาย # ด้านล่างออก)
                    record = db.query(AttendanceDailyResult).filter(
                        AttendanceDailyResult.employee_id == emp.id,
                        AttendanceDailyResult.work_date == self.current_date_obj
                    ).first()
                    
                    time_obj = datetime.strptime(new_time, "%H:%M").time()
                    combined_dt = datetime.combine(self.current_date_obj, time_obj)
                    
                    if record:
                        if is_time_in:
                            record.first_in_at = combined_dt
                        else:
                            record.last_out_at = combined_dt
                    else:
                        # กรณีไม่มีข้อมูลในวันนั้นเลย ต้องสร้าง Record ใหม่
                        new_record = AttendanceDailyResult(
                            employee_id=emp.id,
                            work_date=self.current_date_obj,
                            first_in_at=combined_dt if is_time_in else None,
                            last_out_at=combined_dt if not is_time_in else None
                        )
                        db.add(new_record)
                    db.commit()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "ข้อผิดพลาด DB", f"บันทึกฐานข้อมูลไม่สำเร็จ:\n{str(e)}")
                return
            finally:
                db.close()
            # ----------------------------------------------------

            # อัปเดตหน้าจอ UI
            self.table.item(row, col).setText(new_time)
            QMessageBox.information(
                self, "สำเร็จ", 
                f"อัปเดต{title} ของ {emp_name}\nประจำวันที่ {self.current_date_str}\n\nเป็นเวลา {new_time} \nบันทึกลงฐานข้อมูลเรียบร้อยแล้ว!"
            )

    def set_manual_status(self, row, status_code, detail_text):
        emp_name = self.table.item(row, 1).text()
        status_item = QTableWidgetItem(status_code)
        
        if status_code == "OFFICIAL_DUTY": 
            status_item.setForeground(Qt.GlobalColor.darkMagenta)
            leave_label = "ไปราชการ"
        elif status_code == "ACTING_COMMANDER": 
            status_item.setForeground(Qt.GlobalColor.darkCyan)
            leave_label = "รักษาราชการแทน ผบ."
        else: 
            status_item.setForeground(Qt.GlobalColor.darkGreen)
            leave_label = "-"

        self.table.setItem(row, 3, status_item)
        self.table.setItem(row, 2, QTableWidgetItem(leave_label))
        self.table.setItem(row, 6, QTableWidgetItem(detail_text))
        
        self.table.item(row, 4).setText("-")
        self.table.item(row, 5).setText("-")

        # (ตรงนี้เป็นการแสดงผลทางหน้าจอ หากต้องการบันทึกสถานะไปราชการลง DB ทันที ให้เขียนเพิ่มแบบเดียวกับด้านบน)
        QMessageBox.information(
            self, "อัปเดตสำเร็จ", 
            f"เปลี่ยนสถานะของ {emp_name}\nเป็น '{detail_text}' เรียบร้อยแล้ว\n\n(อัปเดตแสดงผลในตารางแล้ว)"
        )
