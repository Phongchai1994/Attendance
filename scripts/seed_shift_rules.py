from datetime import time

from database.session import SessionLocal
from models.shift_type import ShiftType
from models.shift_rule import ShiftRule


def seed_shift_rules():
    db = SessionLocal()

    try:
        normal = (
            db.query(ShiftType)
            .filter(ShiftType.shift_code == "NORMAL")
            .first()
        )

        if normal is None:
            normal = ShiftType(
                shift_code = "NORMAL",
                shift_name="ปฏิบัติงานปกติ",
                description='เวลาปฏิบัติงานแบบปกติของเจ้าหน้าที่',
                crosses_midnight=False,
            )

            db.add(normal)
            db.flush()

        night = (
            db.query(ShiftType)
            .filter(ShiftType.shift_code == 'NIGHT_DUTY')
            .first()
        )

        if night is None:
            night = ShiftType(
                shift_code='NIGHT_DUTY',
                shift_name='เวรกลางคืน',
                description='เจ้าหน้าที่ที่ได้รับมอบหมายให้เข้าเวรกลางคืน',
                crosses_midnight=True,
            )

            db.add(night)
            db.flush()

        rules = [
            {
                'shift': normal,
                'rule_code': 'NORMAL_IN',
                'rule_name': 'เข้างานปกติ',
                'event_type': 'IN',
                'day_offset': 0,
                'scan_window_start': time(5, 0),
                'scan_window_end': time(11, 0),
                'on_time_start': time(5, 0),
                'on_time_end': time(8, 30),
                'sequence_no': 1,
            },
            {
                'shift': normal,
                'rule_code': 'NORMAL_OUT',
                'rule_name': 'ออกงานปกติ',
                'event_type': 'OUT',
                'day_offset': 0,
                'scan_window_start': time(12, 0),
                'scan_window_end': time(22, 0),
                'on_time_start': time(16, 30),
                'on_time_end': time(22, 0),
                'sequence_no': 2,
            },
            {
                'shift': night,
                'rule_code': 'EVENING_REST_OUT',
                'rule_name': 'ออกพักเวร',
                'event_type': 'OUT',
                'day_offset': 0,
                'scan_window_start': time(15, 0),
                'scan_window_end': time(16, 30),
                'on_time_start': time(15, 0),
                'on_time_end': time(15, 0),
                'sequence_no': 1,
            },
            {
                'shift': night,
                'rule_code': 'NORMAL_RETURN_IN',
                'rule_name': 'กลับเข้าปฏิบัติหน้าที่หลังจากพักเวร',
                'event_type': 'IN',
                'day_offset': 1,
                'scan_window_start': time(9, 30),
                'scan_window_end': time(11, 0),
                'on_time_start': time(9, 30),
                'on_time_end': time(10, 0),
                'sequence_no': 2,
            }

        ]

        for data in rules:
            existing = (
                db.query(ShiftRule)
                .filter(
                    ShiftRule.shift_type_id == data['shift'].id,
                    ShiftRule.rule_code == data['rule_code'],
                )
                .first()
            )

            if existing:
                continue

            rule = ShiftRule(
                shift_type_id=data['shift'].id,
                rule_code=data['rule_code'],
                rule_name=data['rule_name'],
                event_type=data['event_type'],
                day_offset=data['day_offset'],
                scan_window_start=data['scan_window_start'],
                scan_window_end=data['scan_window_end'],
                on_time_start=data['on_time_start'],
                on_time_end=data['on_time_end'],
                required=True,
                sequence_no=data['sequence_no'],
            )

            db.add(rule)

        db.commit()

        print('เพิ่มประเภทและกฎเวลาสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close


if __name__ == '__main__':
    seed_shift_rules()