from datetime import date
from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService

def check_all_employees_attendance():
    db = SessionLocal()
    try:
        service = AttendanceService(db)

        # กำหนดวันที่ทดสอบ
        target_date = date(2026, 11, 9)

        # ดังรายชื่อพนักงานทั้งหมดในระบบ
        employees = db.query(Employee).all()

        print(f"==================================================")
        print(f" สรุปผลการปฏิบัติงานประจำวันที่: {target_date}")
        print(f"==================================================")

        for emp in employees:
            try:
                # สั่งรันประเมินรายวัน (ระบบจะ auto detect สแกนนิ้ว/ใบลาให้เอง)
                result = service.finalize_daily_attendance(
                    employee_id=emp.id,
                    duty_date=target_date
                )

                # กรองแสดงเฉพาะคนที่มาทำงาน หรือมีสถานะที่เกี่ยวข้อง
                print(f"รหัส: {emp.employee_code} | ชื่อ-สกุล: {emp.first_name} {emp.last_name}")
                print(f"  - กะงาน     : {result.shift_code}")
                print(f"  - สถานะ    : [{result.final_status_code}] {result.final_status_text}")
                if result.first_in_at:
                    print(f"  - เวลาเข้า  : {result.first_in_at.strftime('%H:%M:%S')}")
                if result.last_out_at:
                    print(f"  - เวลาออก  : {result.last_out_at.strftime('%H:%M:%S')}")
                print("-" * 50)

            except ValueError as e:
                # เคสที่ไม่มีทั้งตารางเวร, ไม่มีสแกนนิ้ว, และไม่ได้ลา (ถือว่าขาดงานหรือไม่มียอด)
                continue

    finally:
        db.close()

if __name__ == '__main__':
    check_all_employees_attendance()