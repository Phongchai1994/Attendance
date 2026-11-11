from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.attendance_punch import AttendancePunch
from models.duty_roster import DutyRoster
from models.employee_leave import EmployeeLeave
from models.shift_rule import ShiftRule
from models.shift_type import ShiftType
from models.attendance_dialy_result import AttendanceDailyResult


BANGKOK_TZ = ZoneInfo('Asia/Bangkok')


@dataclass
class AttendanceCheckResult:
    employee_id: int
    duty_date: date | None
    shift_code: str | None

    status_code: str
    status_text: str

    punch_time: datetime | None = None
    minutes: int | None = None

    leave_session: str | None = None


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db

    # ----------------------------
    # Roster (Smart Auto-Detection)
    # ----------------------------

    def _get_roster(
            self,
            employee_id: int,
            duty_date: date,
    ) -> DutyRoster | None:
        
        # 1. ค้นหาจากตารางเวรที่บันทึกและยืนยันไว้ก่อน
        stmt = (
            select(DutyRoster)
            .where(
                DutyRoster.employee_id == employee_id,
                DutyRoster.duty_date == duty_date,
                DutyRoster.is_confirmed.is_(True),
            )
        )
        roster = self.db.scalar(stmt)
        if roster is not None:
            return roster

        # 2. Smart Auto-Detection: หากไม่มี DutyRoster ล่วงหน้า
        # ระบบจะเช็กว่ามี "ประวัติการสแกนนิ้ว (Punches)" หรือ "ใบลาที่อนุมัติแล้ว" หรือไม่
        day_start = datetime.combine(duty_date, time(0, 0), tzinfo=BANGKOK_TZ)
        day_end = datetime.combine(duty_date, time(23, 59, 59), tzinfo=BANGKOK_TZ)
        
        has_punch = self.db.scalar(
            select(AttendancePunch.id)
            .where(
                AttendancePunch.employee_id == employee_id,
                AttendancePunch.punched_at >= day_start,
                AttendancePunch.punched_at <= day_end,
            )
            .limit(1)
        ) is not None

        has_leave = self._get_approved_leave(employee_id, duty_date) is not None

        # ถ้ามีสแกนนิ้วหรือมีการลา ให้สร้างตารางเวรชั่วคราว (NORMAL) อัตโนมัติทันที
        if has_punch or has_leave:
            default_shift = self.db.scalar(
                select(ShiftType).where(ShiftType.shift_code == 'NORMAL').limit(1)
            )
            default_shift_type_id = default_shift.id if default_shift else 1

            class DummyRoster:
                def __init__(self, emp_id, d_date, shift_id):
                    self.id = None
                    self.employee_id = emp_id
                    self.duty_date = d_date
                    self.shift_type_id = shift_id

            return DummyRoster(employee_id, duty_date, default_shift_type_id)

        return None

    # ----------------------------
    # Leave
    # ----------------------------
    
    def _get_approved_leave(
            self,
            employee_id: int,
            leave_date: date,
    ) -> EmployeeLeave | None:

        stmt = (
            select(EmployeeLeave)
            .where(
                EmployeeLeave.employee_id == employee_id,
                EmployeeLeave.leave_date == leave_date,
                EmployeeLeave.approval_status == 'APPROVED',
            )
        )

        return self.db.scalar(stmt)

    # ----------------------------
    # Shift rule
    # ----------------------------
    
    def _get_shift_rule(
            self,
            shift_type_id: int,
            rule_code: str,
    ) -> ShiftRule | None:

        stmt = (
            select(ShiftRule)
            .where(
                ShiftRule.shift_type_id == shift_type_id,
                ShiftRule.rule_code == rule_code,
            )
        )

        return self.db.scalar(stmt)

    # ----------------------------
    # Punch
    # ----------------------------

    def _find_first_punch(
            self,
            employee_id: int,
            start_at: datetime,
            end_at: datetime,
    ) -> AttendancePunch | None:

        stmt = (
            select(AttendancePunch)
            .where(
                AttendancePunch.employee_id == employee_id,
                AttendancePunch.punched_at >= start_at,
                AttendancePunch.punched_at <= end_at,
            )
            .order_by(AttendancePunch.punched_at.asc())
            .limit(1)
        )

        return self.db.scalar(stmt)

    def _find_last_punch(
            self,
            employee_id: int,
            start_at: datetime,
            end_at: datetime,
    ) -> AttendancePunch | None:
        stmt = (
            select(AttendancePunch)
            .where(
                AttendancePunch.employee_id == employee_id,
                AttendancePunch.punched_at >= start_at,
                AttendancePunch.punched_at <= end_at,
            )
            .order_by(AttendancePunch.punched_at.desc())
            .limit(1)
        )

        return self.db.scalar(stmt)

    # ----------------------------
    # Helper
    # ----------------------------

    @staticmethod
    def _make_datetime(
        target_date: date,
        target_time: time,
    ) -> datetime:

        return datetime.combine(
            target_date,
            target_time,
            tzinfo=BANGKOK_TZ,
        )

    @staticmethod
    def _minutes_before(
        actual: datetime,
        expected: datetime,
    ) -> int:

        difference = expected - actual
        return max(0, int(difference.total_seconds() // 60))

    @staticmethod
    def _minutes_after(
        actual: datetime,
        expected: datetime,
    ) -> int:

        difference = actual - expected
        return max(0, int(difference.total_seconds() // 60))
    
    # ----------------------------
    # Normal attendance & Leaves evaluations
    # ----------------------------
    
    def _evaluate_normal_in(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        rule = self._get_shift_rule(roster.shift_type_id, "NORMAL_IN")
        if rule is None:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code="NORMAL", status_code='RULE_NOT_FOUND', status_text='ไม่พบกฎเวลาเข้างานปกติ'
            )

        scan_date = roster.duty_date + timedelta(days=rule.day_offset)
        scan_start = self._make_datetime(scan_date, rule.scan_window_start)
        scan_end = self._make_datetime(scan_date, rule.scan_window_end)

        punch = self._find_first_punch(employee_id, scan_start, scan_end)
        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='MISSING_IN', status_text='ไม่มีข้อมูลการสแกนเข้างาน'
            )

        on_time_end = self._make_datetime(scan_date, rule.on_time_end)
        actual = punch.punched_at.astimezone(BANGKOK_TZ)

        if actual <= on_time_end:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='NORMAL', status_text='มาปฏิบัติงานปกติ',
                punch_time=actual, minutes=0
            )

        late_minutes = self._minutes_after(actual, on_time_end)
        return AttendanceCheckResult(
            employee_id=employee_id, duty_date=roster.duty_date,
            shift_code='NORMAL', status_code='LATE', status_text=f'มาสาย {late_minutes} นาที',
            punch_time=actual, minutes=late_minutes
        )

    def _evaluate_normal_out(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        rule = self._get_shift_rule(roster.shift_type_id, 'NORMAL_OUT')
        if rule is None:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='RULE_NOT_FOUND', status_text='ไม่พบกฎเวลาออกงานปกติ'
            )

        scan_date = roster.duty_date + timedelta(days=rule.day_offset)
        scan_start = self._make_datetime(scan_date, rule.scan_window_start)
        scan_end = self._make_datetime(scan_date, rule.scan_window_end)

        punch = self._find_last_punch(employee_id, scan_start, scan_end)
        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='MISSING_OUT', status_text='ไม่มีข้อมูลสแกนออกงาน'
            )

        actual = punch.punched_at.astimezone(BANGKOK_TZ)
        expected_out = self._make_datetime(scan_date, rule.on_time_start)

        if actual < expected_out:
            early_minutes = self._minutes_before(actual, expected_out)
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='EARLY_LEAVE', status_text=f'ออกก่อนเวลา {early_minutes} นาที',
                punch_time=actual, minutes=early_minutes
            )

        return AttendanceCheckResult(
            employee_id=employee_id, duty_date=roster.duty_date,
            shift_code='NORMAL', status_code='NORMAL_OUT', status_text='ออกงานปกติ',
            punch_time=actual, minutes=0
        )

    def _evaluate_afternoon_leave_out(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:
        boundary = self._make_datetime(roster.duty_date, time(12, 0))
        day_end = self._make_datetime(roster.duty_date, time(23, 59, 59))
        search_start = boundary + timedelta(seconds=1)

        punch = self._find_last_punch(employee_id, search_start, day_end)
        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='LEAVE_AFTERNOON_MISSING_OUT',
                status_text='ลาบ่าย แต่ไม่พบข้อมูลสแกนออกหลัง 12:00 น.', leave_session='AFTERNOON'
            )

        actual = punch.punched_at.astimezone(BANGKOK_TZ)
        return AttendanceCheckResult(
            employee_id=employee_id, duty_date=roster.duty_date,
            shift_code='NORMAL', status_code='LEAVE_AFTERNOON_OUT_OK',
            status_text='ลาบ่าย - สแกนถูกต้อง', punch_time=actual, leave_session='AFTERNOON'
        )

    def _evaluate_morning_leave(
            self,
            employee_id: int,
            roster: DutyRoster,
            current_time: datetime,
    ) -> AttendanceCheckResult:
        day_start = self._make_datetime(roster.duty_date, time(0, 0))
        boundary = self._make_datetime(roster.duty_date, time(13, 0))
        search_end = min(current_time, boundary)

        punch = self._find_first_punch(employee_id, day_start, search_end)
        if punch is not None:
            actual = punch.punched_at.astimezone(BANGKOK_TZ)
            if actual < boundary:
                return AttendanceCheckResult(
                    employee_id=employee_id, duty_date=roster.duty_date,
                    shift_code='NORMAL', status_code='LEAVE_MORNING_RETURNED',
                    status_text='ลาเช้า และมีข้อมูลสแกนกลับเข้าปฏิบัติงานแล้ว', punch_time=actual, leave_session='MORNING'
                )

        if current_time < boundary:
            return AttendanceCheckResult(
                employee_id=employee_id, duty_date=roster.duty_date,
                shift_code='NORMAL', status_code='LEAVE_MORNING_PENDING',
                status_text='ลาเช้า - รอสแกนเข้าก่อน 13:00 น.', leave_session='MORNING'
            )

        return AttendanceCheckResult(
            employee_id=employee_id, duty_date=roster.duty_date,
            shift_code='NORMAL', status_code='LEAVE_MORNING_MISSING_IN',
            status_text='ลาเช้า แต่ไม่พบการสแกนเข้าก่อน 13:00 น.', leave_session='MORNING'
        )

    def _build_normal_final_status(
        self,
        in_result: AttendanceCheckResult,
        out_result: AttendanceCheckResult,
    ) -> tuple[str, str]:
        if in_result.status_code == "MISSING_IN" and out_result.status_code == "MISSING_OUT":
            return ("MISSING_IN_OUT", "ไม่พบข้อมูลสแกนเข้าและออกงาน")
        if in_result.status_code == "MISSING_IN":
            return ("MISSING_IN", "ไม่พบข้อมูลสแกนเข้างาน")
        if out_result.status_code == "MISSING_OUT":
            return ("MISSING_OUT", "ไม่พบข้อมูลสแกนออกงาน")
        if in_result.status_code == "LATE" and out_result.status_code == "EARLY_LEAVE":
            return ("LATE_AND_EARLY", f"มาสาย {in_result.minutes} นาที และออกก่อน {out_result.minutes} นาที")
        if in_result.status_code == "LATE":
            return ("LATE", f"มาสาย {in_result.minutes} นาที")
        if out_result.status_code == "EARLY_LEAVE":
            return ("EARLY_LEAVE", f"ออกก่อนเวลา {out_result.minutes} นาที")
        return ("NORMAL", "มาปฏิบัติงานและออกงานปกติ")

    # ----------------------------
    # Main Finalize Daily Attendance
    # ----------------------------

    def finalize_daily_attendance(
            self,
            employee_id: int,
            duty_date: date,
    ) -> AttendanceDailyResult:

        # 1. ดึงตารางเวร (หากไม่มี ระบบจะเช็กสแกนนิ้วหรือใบลาแล้ว Auto-create ให้)
        roster = self._get_roster(employee_id, duty_date)
        leave = self._get_approved_leave(employee_id, duty_date)

        if roster is None and leave is None:
            raise ValueError('ไม่พบตารางปฏิบัติงานและไม่มีประวัติการสแกนนิ้ว/ใบลาของพนักงาน')

        shift_type = self.db.get(ShiftType, roster.shift_type_id) if roster else None
        if shift_type is None:
            # ถ้าหา shift_type ไม่เจอ ให้ fallback เป็น NORMAL
            shift_type = self.db.scalar(select(ShiftType).where(ShiftType.shift_code == 'NORMAL').limit(1))

        existing = (
            self.db.query(AttendanceDailyResult)
            .filter(
                AttendanceDailyResult.employee_id == employee_id,
                AttendanceDailyResult.duty_date == duty_date,
            )
            .first()
        )

        roster_id_val = getattr(roster, 'id', None)
        shift_code_val = shift_type.shift_code if shift_type else 'NORMAL'

        if existing is None:
            result = AttendanceDailyResult(
                employee_id=employee_id,
                roster_id=roster_id_val,
                duty_date=duty_date,
                shift_code=shift_code_val,
                final_status_code="PROCESSING",
                final_status_text="กำลังประมวลผล",
            )
            self.db.add(result)
        else:
            result = existing

        # -----------------------------------
        # ประเมินผลการลา
        # -----------------------------------
        if leave is not None and leave.leave_session == 'FULL_DAY':
            result.leave_session = 'FULL_DAY'
            result.final_status_code = 'LEAVE_FULL_DAY'
            result.final_status_text = 'ลาเต็มวัน'

        elif leave is not None and leave.leave_session == "MORNING":
            end_of_day = self._make_datetime(duty_date, time(23, 59, 59))
            morning_result = self._evaluate_morning_leave(employee_id, roster, end_of_day)
            out_result = self._evaluate_normal_out(employee_id, roster)

            result.leave_session = "MORNING"
            result.first_in_at = morning_result.punch_time
            result.last_out_at = out_result.punch_time

            if morning_result.status_code == "LEAVE_MORNING_RETURNED" and out_result.status_code == "NORMAL_OUT":
                result.final_status_code = "LEAVE_MORNING_COMPLETE"
                result.final_status_text = "ลาเช้าครึ่งวัน และปฏิบัติงานช่วงบ่ายถูกต้อง"
            else:
                result.final_status_code = "LEAVE_MORNING_ISSUE"
                result.final_status_text = f"{morning_result.status_text} / {out_result.status_text}"
                if out_result.status_code == "EARLY_LEAVE":
                    result.early_leave_minutes = out_result.minutes or 0

        elif leave is not None and leave.leave_session == "AFTERNOON":
            in_result = self._evaluate_normal_in(employee_id, roster)
            out_result = self._evaluate_afternoon_leave_out(employee_id, roster)

            result.leave_session = "AFTERNOON"
            result.first_in_at = in_result.punch_time
            result.last_out_at = out_result.punch_time

            if in_result.status_code in ("NORMAL", "LATE") and out_result.status_code == "LEAVE_AFTERNOON_OUT_OK":
                if in_result.status_code == "LATE":
                    result.final_status_code = "LEAVE_AFTERNOON_LATE"
                    result.final_status_text = f"ลาบ่าย / มาสาย {in_result.minutes} นาที"
                    result.late_minutes = in_result.minutes or 0
                else:
                    result.final_status_code = "LEAVE_AFTERNOON_COMPLETE"
                    result.final_status_text = "ปฏิบัติงานช่วงเช้าและลาบ่ายถูกต้อง"
            else:
                result.final_status_code = "LEAVE_AFTERNOON_ISSUE"
                result.final_status_text = f"{in_result.status_text} / {out_result.status_text}"

        # -----------------------------------
        # ประเมินผลวันทำงานปกติ (NORMAL)
        # -----------------------------------
        elif shift_type and shift_type.shift_code == "NORMAL":
            in_result = self._evaluate_normal_in(employee_id, roster)
            out_result = self._evaluate_normal_out(employee_id, roster)

            status_code, status_text = self._build_normal_final_status(in_result, out_result)

            result.first_in_at = in_result.punch_time
            result.last_out_at = out_result.punch_time
            result.late_minutes = in_result.minutes or 0 if in_result.status_code == "LATE" else 0
            result.early_leave_minutes = out_result.minutes or 0 if out_result.status_code == "EARLY_LEAVE" else 0
            result.final_status_code = status_code
            result.final_status_text = status_text

        else:
            result.final_status_code = "UNKNOWN_SHIFT"
            result.final_status_text = "ไม่สามารถประมวลผลกะนี้ได้"

        result.finalized_at = datetime.now(BANGKOK_TZ)

        self.db.commit()
        self.db.refresh(result)

        return result