from datetime import date
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QDateEdit, QPushButton, QTabWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import QDate, QLocale, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# นำเข้า Tab ต่างๆ
from gui.tabs import HomeTab, DashboardTab, TableTab, EmployeeTab

# นำเข้า Database & Services
from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService
from services.zk_sync_service import ZKSyncService  # <--- เพิ่มนำเข้า ZK Service
from services.leave_import_service import LeaveImportService

class DataLoaderThread(QThread):
    # สร้างสัญญาณเพื่อส่งข้อมูล (List ของพนักงาน และ Dict สถิติ) กลับไปยังหน้า UI
    finished_signal = pyqtSignal(list, dict)
    error_signal = pyqtSignal(str)

    def __init__(self, target_date):
        super().__init__()
        self.target_date = target_date

    def run(self):
        """โค้ดส่วนนี้จะทำงานเบื้องหลัง ไม่ทำให้หน้าต่าง UI ค้าง"""
        from database.session import SessionLocal
        from models.employee import Employee
        from models.employee_leave import EmployeeLeave
        from models.leave_type import LeaveType
        from services.attendance_service import AttendanceService

        db = SessionLocal()
        try:
            service = AttendanceService(db)
            employees = db.query(Employee).order_by(Employee.employee_code.asc()).all()
            
            stats = {"normal": 0, "late": 0, "leave": 0, "absent": 0, "duty": 0, "total": len(employees)}
            records = [] 

            for emp in employees:
                # ----------------------------------------------------
                # 💡 แยกชื่อ-สกุล (รวมคำนำหน้า) และ ตำแหน่ง ออกจากกัน
                # ----------------------------------------------------
                title = emp.title if emp.title else ""
                fname = emp.first_name if emp.first_name else ""
                lname = emp.last_name if emp.last_name else ""
                pos_name = emp.position_name if emp.position_name else ""
                pos_lvl = emp.position_level if emp.position_level else ""
                
                full_name = f"{title}{fname} {lname}".strip()
                
                position_text = f"{pos_name} {pos_lvl}".strip()
                if not position_text: 
                    position_text = "-"
                # ----------------------------------------------------

                try:
                    result = service.finalize_daily_attendance(emp.id, self.target_date)
                    status = result.final_status_code
                    
                    if "LEAVE" in status: stats["leave"] += 1
                    elif "LATE" in status: stats["late"] += 1
                    elif status == "OFFICIAL_DUTY": stats["duty"] += 1
                    elif status in ["NORMAL", "NORMAL_OUT", "NIGHT_DUTY_COMPLETE", "MISSING_OUT"]: 
                        stats["normal"] += 1

                    in_time = result.first_in_at.strftime('%H:%M') if result.first_in_at else "-"
                    out_time = result.last_out_at.strftime('%H:%M') if result.last_out_at else "-"

                    # ----------------------------------------------------
                    # 💡 กำหนดตัวแปร leave_type (ตรงนี้แหละที่หายไปจนเกิด Error)
                    # ----------------------------------------------------
                    leave_type = "-"
                    
                    # รวบรวมสถานะทั้งหมดที่ถือว่าเป็นการลาหรือปฏิบัติงานนอกสถานที่
                    special_statuses = [
                        "OFFICIAL_DUTY", "ACTING_COMMANDER", "HOSPITAL_ESCORT",
                        "SICK", "PERSONAL", "VACATION", "MATERNITY", "ORDINATION", "STUDY"
                    ]
                    
                    if "LEAVE" in status or status in special_statuses:
                        
                        leave_record = db.query(EmployeeLeave).filter(
                            EmployeeLeave.employee_id == emp.id,
                            EmployeeLeave.leave_date == self.target_date
                        ).first()
                        
                        if leave_record:
                            lt = db.query(LeaveType).filter(LeaveType.id == leave_record.leave_type_id).first()
                            if lt: leave_type = lt.leave_name
                        
                        if leave_type == "-":
                            leave_mapping = {
                                "OFFICIAL_DUTY": "ไปราชการ",
                                "ACTING_COMMANDER": "รักษาราชการแทน",
                                "HOSPITAL_ESCORT": "ควบคุมผู้ต้องขังป่วย รพ.",
                                "SICK": "ลาป่วย",
                                "PERSONAL": "ลากิจ",
                                "VACATION": "ลาพักผ่อน",
                                "MATERNITY": "ลาคลอด",
                                "ORDINATION": "ลาอุปสมบท",
                                "STUDY": "ลาศึกษาต่อ"
                            }
                            leave_type = leave_mapping.get(status, getattr(result, 'leave_name', "ลาหยุด"))

                    # บันทึกข้อมูลลงตาราง แยก name และ position
                    records.append({
                        "code": emp.employee_code, "name": full_name, "position": position_text,
                        "leave_type": leave_type, "status": status,
                        "in_time": in_time, "out_time": out_time, "detail": result.final_status_text
                    })
                except ValueError:
                    stats["absent"] += 1
                    # แยก name และ position เช่นเดียวกันสำหรับคนที่ขาดงาน
                    records.append({
                        "code": emp.employee_code, "name": full_name, "position": position_text,
                        "leave_type": "-", "status": "ABSENT", "in_time": "-", "out_time": "-", "detail": "ไม่มาปฏิบัติงาน / ขาดงาน"
                    })

            # ระบบจัดเรียงตาราง
            def sort_logic(r):
                s = r["status"]
                t = r["in_time"]
                
                if s in ["NORMAL", "NORMAL_OUT", "NIGHT_DUTY_COMPLETE", "MISSING_OUT"]: prio = 0
                elif s == "OFFICIAL_DUTY": prio = 1
                elif "LATE" in s: prio = 2
                elif "LEAVE" in s: prio = 3
                elif s == "ABSENT": prio = 4
                else: prio = 5
                
                sort_time = t if t != "-" else "99:99"
                return (prio, sort_time)

            records.sort(key=sort_logic)

            # ประมวลผลเสร็จแล้ว ส่งข้อมูลกลับไปให้ UI
            self.finished_signal.emit(records, stats)

        except Exception as e:
            # ถ้ามี Error ส่งข้อความกลับไปแจ้งเตือน
            self.error_signal.emit(str(e))
        finally:
            db.close()

class ZKSyncThread(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def run(self):
        """Thread สำหรับดึงข้อมูลจากเครื่องสแกนนิ้ว"""
        from database.session import SessionLocal
        from services.zk_sync_service import ZKSyncService

        db = SessionLocal()
        try:
            sync_service = ZKSyncService(db, device_ip="192.168.1.201")
            result = sync_service.sync_attendance_logs()
            
            if result.get("error"):
                self.error_signal.emit(result["error"])
            else:
                self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            db.close()


class LeaveSyncThread(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def run(self):
        """Thread สำหรับดึงข้อมูลใบลาจาก Google Sheets"""
        from database.session import SessionLocal
        from services.leave_import_service import LeaveImportService

        db = SessionLocal()
        try:
            service = LeaveImportService(db=db)
            stats = service.sync_leaves_from_sheet()
            self.finished_signal.emit(stats)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            db.close()

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
        self.employee_tab = EmployeeTab() # <--- สร้าง Instance

        self.tabs.addTab(self.home_tab, "🏠 หน้าหลัก (Main)")
        self.tabs.addTab(self.dashboard_tab, "📊 แดชบอร์ด (Dashboard)")
        self.tabs.addTab(self.table_tab, "📋 ตารางปัจจุบัน")
        self.tabs.addTab(self.employee_tab, "👥 จัดการพนักงาน") # <--- เพิ่มเข้าหน้าต่างหลัก

        main_layout.addWidget(self.tabs)

        # 3. ผูกปุ่มจากหน้า HomeTab เข้ากับฟังก์ชัน
        self.home_tab.btn_sync_zk.clicked.connect(self.sync_zk_data)
        self.home_tab.btn_sync_leave.clicked.connect(self.sync_leave_data)


    # ---------------------------------------------------------
    # ส่วนที่ 1: ระบบดึงข้อมูลจากเครื่อง ZKTeco (Thread)
    # ---------------------------------------------------------
    def sync_zk_data(self):
        self.home_tab.btn_sync_zk.setText("⏳ กำลังดึงข้อมูล ZK... กรุณารอสักครู่")
        self.home_tab.btn_sync_zk.setEnabled(False)

        # สั่ง Thread ZK ให้ทำงานเบื้องหลัง
        self.zk_thread = ZKSyncThread()
        self.zk_thread.finished_signal.connect(self.on_zk_sync_finished)
        self.zk_thread.error_signal.connect(self.on_zk_sync_error)
        self.zk_thread.start()

    def on_zk_sync_finished(self, result):
        QMessageBox.information(
            self, "ซิงค์สำเร็จ", 
            f"ดึงข้อมูลสแกนนิ้วเรียบร้อยแล้ว!\n\n"
            f"- ข้อมูลทั้งหมด: {result.get('total_fetched', 0)} รายการ\n"
            f"- บันทึกใหม่: {result.get('saved', 0)} รายการ\n"
            f"- ข้าม (ข้อมูลซ้ำ): {result.get('skipped', 0)} รายการ"
        )
        self.home_tab.btn_sync_zk.setText("📥 ดึงข้อมูลสแกนนิ้ว (ZKTeco MB360)")
        self.home_tab.btn_sync_zk.setEnabled(True)

    def on_zk_sync_error(self, error_msg):
        QMessageBox.critical(self, "ข้อผิดพลาด", f"ไม่สามารถดึงข้อมูลได้:\n{error_msg}")
        self.home_tab.btn_sync_zk.setText("📥 ดึงข้อมูลสแกนนิ้ว (ZKTeco MB360)")
        self.home_tab.btn_sync_zk.setEnabled(True)

    # ---------------------------------------------------------
    # ส่วนที่ 2: ระบบซิงค์ใบลา Google Sheets (Thread)
    # ---------------------------------------------------------
    def sync_leave_data(self):
        self.home_tab.btn_sync_leave.setText("⏳ กำลังดึงข้อมูลใบลา... กรุณารอสักครู่")
        self.home_tab.btn_sync_leave.setEnabled(False)

        # สั่ง Thread ใบลาให้ทำงานเบื้องหลัง
        self.leave_thread = LeaveSyncThread()
        self.leave_thread.finished_signal.connect(self.on_leave_sync_finished)
        self.leave_thread.error_signal.connect(self.on_leave_sync_error)
        self.leave_thread.start()

    def on_leave_sync_finished(self, stats):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("ผลการนำเข้าข้อมูลใบลา")
        msg_box.setText("ซิงค์ข้อมูลใบลาจาก Google Sheets เรียบร้อยแล้ว!")
        
        summary_text = (
            f"📊 สรุปผลการทำงาน:\n"
            f"  • อ่านข้อมูลจาก Sheet ได้:  {stats.get('total_rows', 0)} แถว\n"
            f"  • บันทึกลงฐานข้อมูลใหม่:  {stats.get('inserted', 0)} วัน\n"
            f"  • อัปเดตข้อมูลเก่า:  {stats.get('updated', 0)} วัน\n"
            f"  • ข้ามเนื่องจากซ้ำ:  {stats.get('skipped', 0)} วัน\n"
            f"  • พบข้อผิดพลาด:  {stats.get('errors', 0)} รายการ"
        )
        msg_box.setInformativeText(summary_text)

        error_list = stats.get('error_details', [])
        if error_list:
            detail_str = "\n".join(error_list[:50])
            if len(error_list) > 50:
                detail_str += f"\n... และอีก {len(error_list) - 50} รายการ"
            msg_box.setDetailedText(f"รายการที่เกิดข้อผิดพลาด:\n\n{detail_str}")

        msg_box.exec()
        
        # คืนสถานะปุ่ม
        self.home_tab.btn_sync_leave.setText("☁️ ซิงค์ข้อมูลใบลา (Google Sheets)")
        self.home_tab.btn_sync_leave.setEnabled(True)

    def on_leave_sync_error(self, error_msg):
        QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการซิงค์ใบลา:\n{error_msg}")
        self.home_tab.btn_sync_leave.setText("☁️ ซิงค์ข้อมูลใบลา (Google Sheets)")
        self.home_tab.btn_sync_leave.setEnabled(True)



    def load_data(self):
        """เริ่มแสดงสถานะโหลด และส่งงานไปทำเบื้องหลัง"""
        selected = self.date_edit.date()
        target_date = date(selected.year(), selected.month(), selected.day())
        
        # ส่งวันที่ไปเก็บไว้ที่ TableTab สำหรับการคลิกขวาแก้ไขเวลา
        self.table_tab.current_date_obj = target_date
        self.table_tab.current_date_str = target_date.strftime("%d/%m/%Y")

        # เคลียร์ตารางเดิม และเปลี่ยนปุ่มเป็นสถานะโหลด
        self.table_tab.clear_table()
        self.btn_load.setText("⏳ กำลังประมวลผล...")
        self.btn_load.setEnabled(False)

        # สั่ง QThread ให้ไปทำงานเบื้องหลัง
        self.loader_thread = DataLoaderThread(target_date)
        self.loader_thread.finished_signal.connect(self.on_load_finished)
        self.loader_thread.error_signal.connect(self.on_load_error)
        self.loader_thread.start()

    def on_load_finished(self, records, stats):
        """รับข้อมูลจากเบื้องหลัง มาวาดลงหน้าต่าง UI"""
        for r in records:
            # 👇 เพิ่ม r["position"] เข้ามาแทรกกลาง
            self.table_tab.add_row(r["code"], r["name"], r["position"], r["leave_type"], r["status"], r["in_time"], r["out_time"], r["detail"])
        
        # อัปเดตตัวเลขหน้า Dashboard
        self.dashboard_tab.update_stats(stats['total'], stats['normal'], stats['late'], stats['leave'], stats['absent'])
        
        # สลับหน้าไปที่ตาราง และคืนสถานะปุ่ม
        self.tabs.setCurrentIndex(2) # Index 2 คือตารางปัจจุบัน
        self.btn_load.setText("✨ ประมวลผลข้อมูล")
        self.btn_load.setEnabled(True)

    def on_load_error(self, error_msg):
        """รับข้อผิดพลาดจากเบื้องหลัง มาแสดง Popup"""
        QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาด:\n{error_msg}")
        self.btn_load.setText("✨ ประมวลผลข้อมูล")
        self.btn_load.setEnabled(True)