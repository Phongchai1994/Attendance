from datetime import date, datetime
from zoneinfo import ZoneInfo

from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService


def test_attendance():
    db = SessionLocal()

    try:
        employee = (
            db.query(Employee)
            .filter(Employee.employee_code == "0001")
            .first()
        )

        if employee is None:
            print("ไม่พบพนักงาน 0001")
            return

        service = AttendanceService(db)

        check_date = date(2026, 10, 15)

        current_time = datetime(
            2026,
            10,
            15,
            10,
            30,
            0,
            tzinfo=ZoneInfo("Asia/Bangkok"),
        )

        result = service.check_attendance(
            employee_id=employee.id,
            check_date=check_date,
            current_time=current_time,
        )

        print("----------------------------")
        print("ผลการตรวจเช็คชื่อ")
        print("----------------------------")

        print(f"Employee ID  : {result.employee_id}")
        print(f"Duty Date    : {result.duty_date}")
        print(f"Shift        : {result.shift_code}")
        print(f"Status Code  : {result.status_code}")
        print(f"Status       : {result.status_text}")

        if result.punch_time is not None:
            print(f"Punch Time   : {result.punch_time}")

        if result.minutes is not None:
            print(f"Minutes      : {result.minutes}")

        if result.leave_session is not None:
            print(
                f"Leave Session: {result.leave_session}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_attendance()