from datetime import date
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QDateEdit, QPushButton, QTabWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import QDate, QLocale
from PyQt6.QtGui import QFont

# นำเข้า Tab ต่างๆ
from gui.tabs import HomeTab, DashboardTab, TableTab

# นำเข้า Database & Services
from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService
from services.zk_sync_service import ZKSyncService  # <--- เพิ่มนำเข้า ZK Service
from services.leave_import_service import LeaveImportService

class AttendanceMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ระบบบริหารจัดการเวลาปฏิบัติงาน (Attendance System)")
        self.resize(1150, 750)
        self.setFont(QFont("Tahoma", 10))

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. แถบควบคุมด้านบน
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("📅 วันที่ตรวจสอบ:"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setMinimumWidth(150)
        top_layout.addWidget(self.date_edit)

        self.btn_load = QPushButton("✨ ประมวลผลข้อมูล")
        self.btn_load.setObjectName("btn_success")
        self.btn_load.clicked.connect(self.load_data)
        
        top_layout.addWidget(self.btn_load)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # 2. ระบบ Tabs
        self.tabs = QTabWidget()
        self.home_tab = HomeTab()
        self.dashboard_tab = DashboardTab()
        self.table_tab = TableTab()

        self.tabs.addTab(self.home_tab, "🏠 หน้าหลัก (Main)")
        self.tabs.addTab(self.dashboard_tab, "📊 แดชบอร์ด (Dashboard)")
        self.tabs.addTab(self.table_tab, "📋 ตารางปัจจุบัน")

        main_layout.addWidget(self.tabs)

        # 3. ผูกปุ่มจากหน้า HomeTab เข้ากับฟังก์ชัน
        self.home_tab.btn_sync_zk.clicked.connect(self.sync_zk_data)
        self.home_tab.btn_sync_leave.clicked.connect(self.sync_leave_data)

    def sync_zk_data(self):
        """ฟังก์ชันสำหรับดึงข้อมูลจากเครื่อง ZKTeco เมื่อกดปุ่ม"""
        self.home_tab.btn_sync_zk.setText("⏳ กำลังดึงข้อมูล... กรุณารอสักครู่")
        self.home_tab.btn_sync_zk.setEnabled(False)
        QApplication.processEvents()

        db = SessionLocal()
        try:
            # กำหนด IP ของเครื่อง ZK (ปรับให้ตรงกับหน้างานจริง)
            sync_service = ZKSyncService(db, device_ip="192.168.1.201")
            result = sync_service.sync_attendance_logs()

            if result["error"]:
                QMessageBox.critical(self, "ข้อผิดพลาด", f"ไม่สามารถดึงข้อมูลได้:\n{result['error']}")
            else:
                QMessageBox.information(
                    self, "ซิงค์สำเร็จ", 
                    f"ดึงข้อมูลสแกนนิ้วเรียบร้อยแล้ว!\n\n"
                    f"- ข้อมูลทั้งหมด: {result['total_fetched']} รายการ\n"
                    f"- บันทึกใหม่: {result['saved']} รายการ\n"
                    f"- ข้าม (ข้อมูลซ้ำ): {result['skipped']} รายการ"
                )
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", str(e))
        finally:
            db.close()
            self.home_tab.btn_sync_zk.setText("📥 ดึงข้อมูลสแกนนิ้ว (ZKTeco MB360)")
            self.home_tab.btn_sync_zk.setEnabled(True)


    def sync_leave_data(self):
        """ฟังก์ชันสำหรับซิงค์ข้อมูลใบลาจาก Google Sheets ลงฐานข้อมูล"""
        self.home_tab.btn_sync_leave.setText("⏳ กำลังดึงและบันทึกข้อมูล... กรุณารอสักครู่")
        self.home_tab.btn_sync_leave.setEnabled(False)
        QApplication.processEvents()

        db = SessionLocal()
        try:
            # 1. เรียกใช้ Service ตัวเก่งที่คุณเขียนเทสต์ไว้แล้ว
            service = LeaveImportService(db=db)
            
            # 2. สั่งทำงานและรับค่าผลสถิติกลับมา
            stats = service.sync_leaves_from_sheet()
            
            # 3. นำสถิติมาแสดงในกล่องข้อความ Popup
            QMessageBox.information(
                self, "ผลการนำเข้าข้อมูลใบลา", 
                f"ซิงค์ข้อมูลใบลาจาก Google Sheets เรียบร้อยแล้ว!\n\n"
                f"📊 สรุปผลการทำงาน:\n"
                f"  • อ่านข้อมูลจาก Sheet ได้:  {stats.get('total_rows', 0)} แถว\n"
                f"  • บันทึกลงฐานข้อมูลใหม่:  {stats.get('inserted', 0)} วัน\n"
                f"  • อัปเดตข้อมูลเก่า:  {stats.get('updated', 0)} วัน\n"
                f"  • ข้ามเนื่องจากซ้ำ:  {stats.get('skipped', 0)} วัน\n"
                f"  • พบข้อผิดพลาด:  {stats.get('errors', 0)} รายการ"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการซิงค์ใบลา:\n{str(e)}")
        finally:
            db.close()
            self.home_tab.btn_sync_leave.setText("☁️ ซิงค์ข้อมูลใบลา (Google Sheets)")
            self.home_tab.btn_sync_leave.setEnabled(True)

    def load_data(self):
        """ดึงข้อมูล ประมวลผล และจัดเรียงก่อนแสดงตาราง"""
        selected = self.date_edit.date()
        target_date = date(selected.year(), selected.month(), selected.day())

        self.table_tab.current_date_obj = target_date
        self.table_tab.current_date_str = target_date.strftime("%d/%m/%Y")

        db = SessionLocal()
        try:
            self.btn_load.setText("กำลังประมวลผล...")
            self.btn_load.setEnabled(False)
            QApplication.processEvents()

            service = AttendanceService(db)
            employees = db.query(Employee).order_by(Employee.employee_code.asc()).all()
            
            stats = {"normal": 0, "late": 0, "leave": 0, "absent": 0, "duty": 0, "total": len(employees)}
            
            # 1. สร้าง List เปล่าๆ เพื่อเก็บข้อมูลก่อน (ยังไม่วาดลงตาราง)
            records = [] 

            for emp in employees:
                try:
                    result = service.finalize_daily_attendance(emp.id, target_date)
                    status = result.final_status_code
                    
                    if "LEAVE" in status: stats["leave"] += 1
                    elif "LATE" in status: stats["late"] += 1
                    elif status == "OFFICIAL_DUTY": stats["duty"] += 1
                    elif status in ["NORMAL", "NORMAL_OUT", "NIGHT_DUTY_COMPLETE", "MISSING_OUT"]: 
                        stats["normal"] += 1

                    in_time = result.first_in_at.strftime('%H:%M') if result.first_in_at else "-"
                    out_time = result.last_out_at.strftime('%H:%M') if result.last_out_at else "-"

                    # 👇 สร้างตัวแปรดึงประเภทการลาแทนกะการทำงาน
                    leave_type = "-"
                    if "LEAVE" in status:
                        # พยายามดึงชื่อลา (เช่น ลาป่วย ลากิจ) จากผลลัพธ์ ถ้าหาไม่เจอให้ใช้ข้อความสถานะแทน
                        leave_type = getattr(result, 'leave_name', result.final_status_text)
                    elif status == "OFFICIAL_DUTY":
                        leave_type = "ไปราชการ"

                    # ยัดข้อมูลลง List
                    records.append({
                        "code": emp.employee_code, "name": f"{emp.first_name} {emp.last_name}",
                        "leave_type": leave_type, "status": status, # <--- เปลี่ยนตรงนี้
                        "in_time": in_time, "out_time": out_time, "detail": result.final_status_text
                    })
                except ValueError:
                    stats["absent"] += 1
                    # ยัดข้อมูลคนขาดงานลง List
                    records.append({
                        "code": emp.employee_code, "name": f"{emp.first_name} {emp.last_name}",
                        "leave_type": "-", "status": "ABSENT", "in_time": "-", "out_time": "-", "detail": "ไม่มาปฏิบัติงาน / ขาดงาน"
                    })

            # 2. ระบบจัดเรียงข้อมูลใน List ที่เราเพิ่งรวมมา
            def sort_logic(r):
                s = r["status"]
                t = r["in_time"]
                
                # กลุ่ม 1 บนสุด (รวม MISSING_OUT แล้ว)
                if s in ["NORMAL", "NORMAL_OUT", "NIGHT_DUTY_COMPLETE", "MISSING_OUT"]: prio = 0
                elif s == "OFFICIAL_DUTY": prio = 1
                elif "LATE" in s: prio = 2
                elif "LEAVE" in s: prio = 3
                elif s == "ABSENT": prio = 4
                else: prio = 5
                
                sort_time = t if t != "-" else "99:99"
                return (prio, sort_time)

            # สั่งจัดเรียง
            records.sort(key=sort_logic)

            # 3. วาดข้อมูลที่จัดเรียงเสร็จแล้วลงตาราง
            self.table_tab.clear_table()
            for r in records:
                # ส่ง r["leave_type"] เข้าไปแทนรหัสกะ
                self.table_tab.add_row(r["code"], r["name"], r["leave_type"], r["status"], r["in_time"], r["out_time"], r["detail"])

            # อัปเดตตัวเลขหน้า Dashboard
            self.dashboard_tab.update_stats(stats['total'], stats['normal'], stats['late'], stats['leave'], stats['absent'])
            self.tabs.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาด:\n{str(e)}")
        finally:
            db.close()
            self.btn_load.setText("✨ ประมวลผลข้อมูล")
            self.btn_load.setEnabled(True)