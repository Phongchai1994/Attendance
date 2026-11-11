from datetime import date
from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService

def test_leave_finalize():
    db = SessionLocal()
    try:
        # ค้นหาพนักงานที่มีข้อมูลการลา (เช่น รหัสพนักงาน 1058 ตามที่เราทดสอบใน Google Sheets)
        employee = (
            db.query(Employee)
            .filter(Employee.employee_code == '2008')
            .first()
        )

        if employee is None:
            print('ไม่พบพนักงานรหัส 1052')
            return

        service = AttendanceService(db)

        # กำหนดวันที่ต้องการทดสอบ (ตรงกับวันที่ใน google sheets)
        test_date = date(2026, 11, 30)

        print(f'กำลังประเมินผลการปฏิบัติงานของ : {employee.first_name} {employee.last_name} วันที่ {test_date}')

        result = service.finalize_daily_attendance(
            employee_id=employee.id,
            duty_date=test_date
        )

        print("--------------------------------------------")
        print("ผลการประเมินประจำวัน (Attendance Leave Result)")
        print("--------------------------------------------")
        print(f"Employee ID   : {result.employee_id}")
        print(f"Duty Date     : {result.duty_date}")
        print(f"Shift         : {result.shift_code}")
        print(f"Leave Session : {result.leave_session}")
        print(f"Status Code   : {result.final_status_code}")
        print(f"Status Text   : {result.final_status_text}")
        print(f"First In      : {result.first_in_at}")
        print(f"Last Out      : {result.last_out_at}")
        print("--------------------------------------------")

    finally:
        db.close()


if __name__ == "__main__":
    test_leave_finalize()