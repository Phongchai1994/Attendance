from datetime import datetime
from zoneinfo import ZoneInfo

from database.session import SessionLocal
from models.device import Device
from models.employee import Employee
from models.attendance_punch import AttendancePunch


def seed_punch():
    db = SessionLocal()

    try:
        employee = (
            db.query(Employee)
            .filter(Employee.employee_code == "0001")
            .first()
        )

        if employee is None:
            print('ไม่พบพนักงาน 0001')
            return

        device = (
            db.query(Device)
            .filter(Device.device_code == 'DEV01')
            .first()
        )

        if device is None:
            print('ไม่พบเครื่อง DEV01')
            return

        punched_at = datetime(
            2026,
            10,
            2,
            7,
            48,
            12,
            tzinfo=ZoneInfo('Asia/Bangkok'),
        )

        source_ref = (
            f'TEST:{employee.id}:'
            f'{punched_at.isoformat()}:'
            f'{device.id}'
        )

        existing = (
            db.query(AttendancePunch)
            .filter(
                AttendancePunch.source_ref == source_ref
            )
            .first()
        )

        if existing:
            print('ข้อมูลสแกนนี้มีอยู่แล้ว')
            return

        punch = AttendancePunch(
            employee_id = employee.id,
            device_id = device.id,
            punched_at = punched_at,
            direction_hint = "IN",
            source = "TEST",
            source_ref = source_ref,
            legacy_user_id = employee.legacy_user_id,
        )

        db.add(punch)
        db.commit()

        print('เพิ่มข้อมูลสแกนสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_punch()