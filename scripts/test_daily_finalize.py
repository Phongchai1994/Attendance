from datetime import date

from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService


def test_finalize():
    db = SessionLocal()

    try:
        employee = (
            db.query(Employee)
            .filter(Employee.employee_code == '0001')
            .first()
        )

        if employee is None:
            print('ไม่พบพนักงาน 0001')
            return

        service = AttendanceService(db)

        result = service.finalize_dialy_attendance(
            employee_id=employee.id,
            duty_date=(2026, 10, 15)
        )

        print("----------------------------")
        print("สรุปผลประจำวัน")
        print("----------------------------")

        print(
            f"Employee ID : {result.employee_id}"
        )

        print(
            f"Duty Date   : {result.duty_date}"
        )

        print(
            f"Shift       : {result.shift_code}"
        )

        print(
            f"Status Code : {result.final_status_code}"
        )

        print(
            f"Status      : {result.final_status_text}"
        )

        print(
            f"First In    : {result.first_in_at}"
        )

        print(
            f"Last Out    : {result.last_out_at}"
        )

        print(
            f"Late        : {result.late_minutes}"
        )

        print(
            f"Early Leave : {result.early_leave_minutes}"
        )

    finally:
        db.close()

if __name__ == '__main__':
    test_finalize()
