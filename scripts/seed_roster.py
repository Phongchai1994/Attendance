from datetime import date

from database.session import SessionLocal
from models.duty_roster import DutyRoster
from models.employee import Employee
from models.shift_type import ShiftType


def seed_roster():
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

        shift = (
            db.query(ShiftType)
            .filter(ShiftType.shift_code == 'NIGHT_DUTY')
            .first()
        )

        if shift is None:
            print('ไม่พบประเภทกะ NORMAL')
            return

        duty_date = date(2026, 10, 15)

        existing = (
            db.query(DutyRoster)
            .filter(
                DutyRoster.employee_id == employee.id,
                DutyRoster.duty_date == duty_date,
            )
            .first()
        )

        if existing:
            print('มีตารางเวรของพนักงานวันนี้แล้ว')
            return

        roster = DutyRoster(
            employee_id=employee.id,
            duty_date=duty_date,
            shift_type_id=shift.id,
            source='TEST',
            note='ข้อมูลสำหรับทดสอบ',
        )

        db.add(roster)
        db.commit()

        print('เพิ่มตารางเวรสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roster()