
from uuid import uuid4

from PyQt6.QtCore import QThread, pyqtSignal
from sqlalchemy import select

from database.session import SessionLocal
from models.employee import Employee
from models.employee_leave import EmployeeLeave
from models.leave_type import LeaveType

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from models.attendance_punch import AttendancePunch


class LeaveSaveThread(QThread):
    success_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        employee_codes,
        target_date,
        status_code,
        detail_text,
        leave_session,
        parent=None,
    ):
        super().__init__(parent)

        self.employee_codes = employee_codes
        self.target_date = target_date
        self.status_code = status_code
        self.detail_text = detail_text
        self.leave_session = leave_session

    def run(self):
        db = None

        try:
            db = SessionLocal()

            # ตรวจสอบคำสั่งยกเลิกสถานะ Manual
            if self.status_code == "CANCEL_MANUAL":
                self.cancel_manual_status(db)
                return


            # ตรวจสอบประเภทการลา
            leave_type = db.scalar(
                select(LeaveType).where(
                    LeaveType.leave_code == self.status_code,
                    LeaveType.is_active.is_(True),
                )
            )

            if leave_type is None:
                raise ValueError(
                    f"ไม่พบประเภทสถานะ {self.status_code}"
                )

            if self.leave_session not in (
                "FULL_DAY", "MORNING", "AFTERNOON"
            ):
                raise ValueError("ช่วงเวลาการลาไม่ถูกต้อง")

            saved = []
            skipped = []

            for code in sorted(set(self.employee_codes)):

                employee = db.scalar(
                    select(Employee)
                    .where(Employee.employee_code == code)
                    .with_for_update()
                )

                if employee is None:
                    skipped.append(f"{code}: ไม่พบเจ้าหน้าที่")
                    continue

                # ตรวจสอบรายการเดิมที่ยังไม่ถูกยกเลิก
                records = db.scalars(
                    select(EmployeeLeave).where(
                        EmployeeLeave.employee_id == employee.id,
                        EmployeeLeave.leave_date == self.target_date,
                        EmployeeLeave.approval_status != "CANCELLED",
                    )
                ).all()

                # ป้องกันการเขียนทับข้อมูลจากระบบอื่น
                if len(records) > 1:
                    skipped.append(
                        f"{code}: มีรายการเดิมหลายรายการ"
                    )
                    continue

                record = records[0] if records else None

                if record is not None:
                    if (
                        record.source != "MANUAL"
                        or record.approval_status != "APPROVED"
                        or (
                            record.source_ref
                            and not record.source_ref.startswith(
                                "MANUAL_"
                            )
                        )
                    ):
                        skipped.append(
                            f"{code}: มีรายการจากแหล่งอื่นอยู่แล้ว"
                        )
                        continue

                    # แก้ไขเฉพาะรายการ Manual เดิม
                    record.leave_type_id = leave_type.id
                    record.leave_session = self.leave_session
                    record.note = self.detail_text

                else:
                    # สร้างรายการใหม่
                    record = EmployeeLeave(
                        employee_id=employee.id,
                        leave_type_id=leave_type.id,
                        leave_date=self.target_date,
                        leave_session=self.leave_session,
                        approval_status="APPROVED",
                        source="MANUAL",
                        source_ref=f"MANUAL_{uuid4().hex}",
                        note=self.detail_text,
                    )

                    db.add(record)

                saved.append(code)

            # บันทึกก่อนส่งผลกลับไปยังหน้าจอ
            db.commit()

            self.success_signal.emit({
                "saved": saved,
                "skipped": skipped,
            })

        except Exception as e:
            if db is not None:
                db.rollback()

            self.error_signal.emit(str(e))

        finally:
            if db is not None:
                db.close()

    
    
    def cancel_manual_status(self, db):
        """ยกเลิกสถานะ Manual และลบเวลาเข้าออก Manual"""

        from models.attendance_dialy_result import (
            AttendanceDailyResult
        )

        bangkok_tz = ZoneInfo("Asia/Bangkok")

        # กำหนดช่วงวันที่ตามเวลาประเทศไทย
        start_at = datetime.combine(
            self.target_date,
            time.min,
            tzinfo=bangkok_tz,
        )
        end_at = start_at + timedelta(days=1)

        saved = []
        skipped = []
        deleted_punches = 0

        for code in sorted(set(self.employee_codes)):

            employee = db.scalar(
                select(Employee)
                .where(Employee.employee_code == code)
                .with_for_update()
            )

            if employee is None:
                skipped.append(f"{code}: ไม่พบเจ้าหน้าที่")
                continue

            # 1. ค้นหาสถานะที่เพิ่มเองผ่าน GUI เท่านั้น
            leaves = db.scalars(
                select(EmployeeLeave).where(
                    EmployeeLeave.employee_id == employee.id,
                    EmployeeLeave.leave_date == self.target_date,
                    EmployeeLeave.source == "MANUAL",
                    EmployeeLeave.approval_status == "APPROVED",
                )
            ).all()

            manual_leaves = [
                record
                for record in leaves
                if (
                    not record.source_ref
                    or record.source_ref.startswith("MANUAL_")
                )
            ]

            # 2. ค้นหาเวลาเข้า-ออก Manual ภายในวันที่เลือก
            manual_punches = db.scalars(
                select(AttendancePunch)
                .where(
                    AttendancePunch.employee_id == employee.id,
                    AttendancePunch.source == "MANUAL",
                    AttendancePunch.punched_at >= start_at,
                    AttendancePunch.punched_at < end_at,
                )
                .with_for_update()
            ).all()

            # ไม่มีข้อมูล Manual ให้ลบ
            if not manual_leaves and not manual_punches:
                skipped.append(
                    f"{code}: ไม่พบสถานะหรือเวลา Manual"
                )
                continue

            # 3. ยกเลิกสถานะ Manual โดยเก็บประวัติไว้
            for record in manual_leaves:
                record.approval_status = "CANCELLED"

            # 4. ลบเฉพาะข้อมูลเวลา Manual
            # ไม่แตะ Raw Data จากเครื่อง ZKTeco
            for punch in manual_punches:
                db.delete(punch)
                deleted_punches += 1

            # 5. ยกเลิกผลสรุปเดิมที่อาจใช้เวลา Manual
            result = db.scalar(
                select(AttendanceDailyResult)
                .where(
                    AttendanceDailyResult.employee_id == employee.id,
                    AttendanceDailyResult.duty_date == self.target_date,
                )
                .with_for_update()
            )

            if result is not None:
                result.leave_session = None
                result.first_in_at = None
                result.last_out_at = None
                result.evening_rest_out_at = None
                result.morning_return_in_at = None
                result.late_minutes = 0
                result.early_leave_minutes = 0
                result.final_status_code = "PENDING_REVIEW"
                result.final_status_text = (
                    "ลบข้อมูล Manual แล้ว รอประมวลผลใหม่"
                )
                result.finalized_at = None

            saved.append(code)

        # บันทึกการเปลี่ยนแปลงทั้งหมดใน Transaction เดียว
        db.commit()

        self.success_signal.emit({
            "saved": saved,
            "skipped": skipped,
            "deleted_punches": deleted_punches,
        })


