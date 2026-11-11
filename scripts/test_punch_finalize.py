from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from database.session import SessionLocal
from models.employee import Employee
from models.attendance_punch import AttendancePunch
from services.attendance_service import AttendanceService

BANGKOK_TZ = ZoneInfo('Asia/Bangkok')

def test_punch():
    db = SessionLocal()
    try:
        # 1. ค้นหาพนักงานที่ต้องการทดสอบ (เช่น รหัสพนักงาน 1058)
        employee = (
            db.query(Employee)
            .filter(Employee.employee_code == '1058')
            .first()
        )

        if employee is None:
            print("ไม่พบพนักงานรหัส 1058")
            return

        # 2. กำหนดวันที่ต้องการจำลองการสแกนนิ้ว (เช่น วันที่ 2026-11-04)
        test_date = date(2026, 11, 4)

        # 3. สร้างข้อมูลจำลองการสแกนนิ้วเข้า (Punch In) และออก (Punch Out)
        # ตัวอย่าง: สแกนเข้า 08:45 น. (มาสาย) และสแกนออก 16:30 น.
        punch_in_dt = datetime.combine(test_date, time(8, 45), tzinfo=BANGKOK_TZ)
        punch_out_dt = datetime.combine(test_date, time(16, 30), tzinfo=BANGKOK_TZ)

        # ลบข้อมูล Punch เก่าของวันนี้ทิ้งก่อน (ถ้ามี) เพื่อไม่ให้ซ้ำ
        db.query(AttendancePunch).filter(
            AttendancePunch.employee_id == employee.id,
            AttendancePunch.punched_at >= datetime.combine(test_date, time(0, 0), tzinfo=BANGKOK_TZ),
            AttendancePunch.punched_at <= datetime.combine(test_date, time(23, 59, 59), tzinfo=BANGKOK_TZ)
        ).delete()

        # บันทึก Punch ใหม่ลงฐานข้อมูล
        punch_in = AttendancePunch(
            employee_id=employee.id,
            punched_at=punch_in_dt,
            device_id=1,
            source="MANUAL_TEST"
        )
        punch_out = AttendancePunch(
            employee_id=employee.id,
            punched_at=punch_out_dt,
            device_id=1,
            source="MANUAL_TEST"
        )
        db.add(punch_in)
        db.add(punch_out)
        db.commit()

        print(f"จำลองการสแกนนิ้วของ: {employee.first_name} ({test_date}) สำเร็จ")
        print(f"- เข้า: {punch_in_dt}")
        print(f"- ออก: {punch_out_dt}")

        # 4. สั่งให้ AttendanceService ประมวลผลประจำวัน (ระบบจะ Smart Auto-Detect กะ NORMAL ให้จาก Punches)
        service = AttendanceService(db)
        result = service.finalize_daily_attendance(
            employee_id=employee.id,
            duty_date=test_date
        )

        print("\n--------------------------------------------")
        print("ผลการประเมินจาก Attendance Punch Result")
        print("--------------------------------------------")
        print(f"Employee ID   : {result.employee_id}")
        print(f"Duty Date     : {result.duty_date}")
        print(f"Shift         : {result.shift_code}")
        print(f"First In      : {result.first_in_at}")
        print(f"Last Out      : {result.last_out_at}")
        print(f"Late Minutes  : {result.late_minutes} นาที")
        print(f"Status Code   : {result.final_status_code}")
        print(f"Status Text   : {result.final_status_text}")
        print("--------------------------------------------")

    finally:
        db.close()

if __name__ == '__main__':
    test_punch()