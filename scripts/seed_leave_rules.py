from datetime import time

from database.session import SessionLocal
from models.leave_type import LeaveType
from models.leave_attendance_rule import LeaveAttendanceRule


def seed_leave_rules():
    db = SessionLocal()

    try:
        leave_types = [
            ('SICK','ลาป่วย'),
            ('PERSONAL', 'ลากิจ'),
            ('VACATION', 'ลาพักผ่อน'),
            ('METERNITY', 'ลาคลอด'),
        ]

        for code, name in leave_types:
            existing = (
                db.query(LeaveType)
                .filter(LeaveType.leave_code == code)
                .first()
            )

            if existing:
                continue

            db.add(
                LeaveType(
                    leave_code=code,
                    leave_name=name,
                )
            )

        morning_rule = (
            db.query(LeaveAttendanceRule)
            .filter(
                LeaveAttendanceRule.leave_session == 'MORNING'
            )
            .first()
        )

        if morning_rule is None:
            db.add(
                LeaveAttendanceRule(
                    leave_session='MORNING',
                    required_event='IN',
                    boundary_time=time(13, 0),
                    comparison='BEFORE',
                    description=(
                        "ลาเช้าครึ่งวัน ต้องแสกนเข้าก่อน 13:00 น."
                    ),
                )
            )
        affternoon_rule = (
            db.query(LeaveAttendanceRule)
            .filter(
                LeaveAttendanceRule.leave_session == "AFTERNOON"
            )
            .first()
        )

        if affternoon_rule is None:
            db.add(
                LeaveAttendanceRule(
                    leave_session='AFTERNOON',
                    required_event='OUT',
                    boundary_time=time(12, 0),
                    comparison="AFTER",
                    description=(
                        "ลาบ่ายครึ่งวัน ต้องสแกนออกหลัง 12:00 น."
                    ),
                )
            )

        db.commit()

        print("เพิ่มประเภทการลาและกฎลาครึ่งวันสำเร็จ")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_leave_rules()