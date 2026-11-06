from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from sqlalchemy import select

from models.employee import Employee
from models.employee_leave import EmployeeLeave
from models.leave_type import LeaveType
from services.google_leave_service import GoogleLeaveService

BANGKOK_TZ = ZoneInfo('Asia/Bangkok')


class LeaveImportService:
    def __init__(self, db:Session):
        self.db = db
        self.google_service = GoogleLeaveService()

    @staticmethod
    def _normalize_session(value: str) -> str:
        value = value.strip().upper()

        mapping = {
            "FULL_DAY": "FULL_DAY",
            "MORNING": "MORNING",
            "AFTERNOON": "AFTERNOON",
            "เต็มวัน": "FULL_DAY",
            "เช้า": "MORNING",
            "บ่าย": "AFTERNOON",
        }

        if value not in mapping:
            raise ValueError(
                f'ไม่รู้จักช่วงเวลา: {value}'
            )

        return mapping[value]

    @staticmethod
    def _normalize_status(value: str) -> str:
        value = value.strip().upper()

        mapping = {
            'APPROVED': 'APPROVED',
            'CANCELLED': 'CANCELLED',
        }

        # หากไม่ตรงกับตาราง mapping ให้ถือเป็น APPROVED ปกติ
        return mapping.get(value, 'APPROVED')

    def sync_leaves_from_sheet(self) -> dict:
        rows = self.google_service.get_rows()

        # เตรียม Cache สำหรับ Employee และ LeaveType เพื่อลดภาระ Database ดึงครั้งเดียวจบ
        emp_cache = {}
        leave_type_cache = {}

        stats = {
            'total_rows': len(rows),
            'inserted' : 0,
            'updated' : 0,
            'skipped' : 0,
            'errors' : 0,
        }

        now = datetime.now(BANGKOK_TZ)

        for row in rows:
            try:
                leave_id = str(row.get('leave_id', '')).strip()
                emp_code = str(row.get('employee_code', '')).strip()

                # หากแถวไหนไม่มี key หลัก ให้ข้ามไป
                if not leave_id or not emp_code:
                    stats['skipped'] += 1
                    continue

                # 1.ค้นหา Employee
                if emp_code not in emp_cache:
                    emp = self.db.scalar(
                        select(Employee).where(Employee.employee_code == emp_code)
                    )
                    emp_cache[emp_code] = emp

                employee = emp_cache[emp_code]
                if employee is None:
                    print(f'ไม่พบรหัสพนักงาน {emp_code} ในฐานข้อมูล')
                    stats['errors'] += 1
                    continue

                # 2.ค้นหา LeaveType
                # หมายเหตุ: สมมติว่าตาราง LeaveType ใช้ฟิลด์ชื่อ name (เช่น "ลาพักผ่อน", "ลาป่วย", )
                # หากตารางใช้ title ให้เปลี่ยน LeaveType.name เป็น LeaveType.title 
                l_code = str(row.get('leave_code', '')).strip()
                if l_code not in leave_type_cache:
                    lt = self.db.scalar(
                        select(LeaveType).where(LeaveType.leave_name == l_code)
                    )
                    leave_type_cache[l_code] = lt

                leave_type = leave_type_cache[l_code]
                if leave_type is None:
                    print(f'ไม่พบประเภทกาลา {l_code} ในตาราง leave_types')
                    stats['errors'] += 1
                    continue

                # 3. แปลงวันที่
                start_str = str(row.get('start_date', '')).strip()
                end_str = str(row.get('end_date', '')).strip()

                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

                # 4. แปลงสถานะต่าง ๆ 
                raw_session = str(row.get('leave_session', 'FULLDAY'))
                session_val = self._normalize_session(raw_session)

                raw_status = str(row.get('approval_status', 'APPROVED'))
                status_val = self._normalize_status(raw_status)

                note = str(row.get('note', '')).strip()

                # 5. กระจายวันที่ (Date Explosion) และตรวจสอบ Duplicate
                current_date = start_date
                while current_date <= end_date:
                    # ใช้ leave_id ร่วมกับวันที่ เพื่อเป็น Uniqui Key ต่อวัน
                    source_ref = f'{leave_id}_{current_date.strftime('%y%m%d')}'

                    existing = self.db.scalar(
                        select(EmployeeLeave).where(EmployeeLeave.source_ref == source_ref)
                    )

                    if existing is not None:
                        # กรณีมีข้อมูลอยู่แล้ว ตรวจสอบว่ามีการเปลี่ยนแปลงไหม เช่น ยกเลิกการลา
                        if (
                            existing.leave_session != session_val or
                            existing.approval_status != status_val or
                            existing.note != note
                        ):
                            existing.leave_session = session_val
                            existing.approval_status = status_val
                            existing.note = note
                            existing.imported_at = now
                            stats['updated'] += 1
                        else:
                            stats['skipped'] += 1

                    else:
                        # ข้อมูลใหม่ ให้ Insert ทันที
                        new_leave = EmployeeLeave(
                            employee_id=employee.id,
                            leave_type_id=leave_type.id,
                            leave_date=current_date,
                            leave_session=session_val,
                            approval_status=status_val,
                            source='GOOGLE_SHEETS',
                            source_ref=source_ref,
                            imported_at=now,
                            note=note
                        )
                        self.db.add(new_leave)
                        stats['inserted'] += 1

                    current_date += timedelta(days=1)

            except Exception as e:
                print(f'Error Processing leave_id {leave_id}: {e}')
                stats['errors'] += 1

        self.db.commit()
        return stats
