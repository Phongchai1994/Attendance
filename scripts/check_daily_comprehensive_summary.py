from datetime import date
from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService

def generate_comprehensive_summary():
    db = SessionLocal()
    try:
        service = AttendanceService(db)
        
        # กำหนดวันที่ต้องการตรวจสอบสรุปผล (สามารถเปลี่ยนวันที่ได้ตามต้องการ)
        target_date = date(2026, 11, 9)
        
        # ดึงรายชื่อพนักงานทั้งหมดในระบบ
        employees = db.query(Employee).order_by(Employee.employee_code.asc()).all()
        
        print(f"======================================================================")
        print(f" รายงานสรุปผลการปฏิบัติงานและการลาประจำวันที่: {target_date}")
        print(f"======================================================================")
        print(f"{'รหัส':<6} | {'ชื่อ-นามสกุล':<22} | {'กะ':<8} | {'สถานะ / รายละเอียด':<25} | {'เข้า':<8} | {'ออก':<8}")
        print("-" * 70)

        for emp in employees:
            try:
                # สั่งรันประเมินผลรายวัน (ระบบจะเช็กทั้งตารางเวร, สแกนนิ้ว และใบลา ให้อัตโนมัติ)
                result = service.finalize_daily_attendance(
                    employee_id=emp.id,
                    duty_date=target_date
                )
                
                name_str = f"{emp.first_name} {emp.last_name}"
                shift_str = result.shift_code or "-"
                status_str = f"[{result.final_status_code}]"
                
                in_str = result.first_in_at.strftime('%H:%M') if result.first_in_at else "-"
                out_str = result.last_out_at.strftime('%H:%M') if result.last_out_at else "-"

                # พิมพ์ข้อมูลสรุปแบบตารางบรรทัดเดียว กระชับและดูง่าย
                print(f"{emp.employee_code:<6} | {name_str:<22} | {shift_str:<8} | {status_str:<25} | {in_str:<8} | {out_str:<8}")
                
                # ถ้ามีรายละเอียดเพิ่มเติม (เช่น ข้อความสถานะยาวๆ หรือประเภทการลา) ให้แสดงบรรทัดย่อย
                if result.final_status_text:
                    print(f"       └─ หมายเหตุ: {result.final_status_text}")
                
            except ValueError:
                # เคสที่พนักงานไม่มีตารางเวร, ไม่มีประวัติสแกนนิ้ว และไม่ได้ลาในวันนี้ (ถือว่าไม่มีข้อมูล/ขาดงาน)
                # เราสามารถข้าม หรือเลือกแสดงผลได้ตามต้องการ
                continue

        print("======================================================================")

    finally:
        db.close()

if __name__ == '__main__':
    generate_comprehensive_summary()