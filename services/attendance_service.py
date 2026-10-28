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
    def __init__(self, db:Session):
        self.db = db

    # ----------------------------
    # Roster
    # ----------------------------

    def _get_roster(
            self,
            employee_id: int,
            duty_date: date,
    ) -> DutyRoster | None:
        
        stmt = (
            select(DutyRoster)
            .where(
                DutyRoster.employee_id == employee_id,
                DutyRoster.duty_date == duty_date,
                DutyRoster.is_confirmed.is_(True),
            )
        )

        return self.db.scalar(stmt)

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
    def _minutes_after(
        actual: datetime,
        expected: datetime,
    ) -> int:

        difference = actual - expected

        return max(
            0,
            int(difference.total_seconds() // 60),
        )
    
    # ----------------------------
    # Normal attendance
    # ----------------------------
    
    def _evaluate_normal_in(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        rule = self._get_shift_rule(
            roster.shift_type_id,
            "NORMAL_IN",
        )

        if rule is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code="NORMAL",
                status_code='RULE_NOT_FOUND',
                status_text='ไม่พบกฎเวลาเข้างานปกติ',
            )

        scan_date = roster.duty_date + timedelta(
            days=rule.day_offset
        )

        scan_start = self._make_datetime(
            scan_date,
            rule.scan_window_start,
        )

        scan_end = self._make_datetime(
            scan_date,
            rule.scan_window_end,
        )

        punch = self._find_first_punch(
            employee_id,
            scan_start,
            scan_end,
        )

        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='MISSING_IN',
                status_text='ไม่มีข้อมูลการสแกนเข้างาน',
            )

        on_time_end = self._make_datetime(
            scan_date,
            rule.on_time_end,
        )

        actual = punch.punched_at.astimezone(
            BANGKOK_TZ
        )

        if actual <= on_time_end:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='NORMAL',
                status_text='มาปฏิบัติงานปกติ',
                punch_time=actual,
                minutes=0,
            )

        late_minutes = self._minutes_after(
            actual,
            on_time_end,
        )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NORMAL',
            status_code='LATE',
            status_text=f'มาสาย {late_minutes} นาที',
            punch_time=actual,
            minutes=late_minutes,
        )
    
    # ----------------------------
    # Morning Leave
    # ----------------------------

    def _evaluate_morning_leave(
            self,
            employee_id: int,
            roster: DutyRoster,
            current_time: datetime,
    ) -> AttendanceCheckResult:

        day_start = self._make_datetime(
            roster.duty_date,
            time(0, 0),
        )

        boundary = self._make_datetime(
            roster.duty_date,
            time(13, 0),
        )

        search_end = min(
            current_time,
            boundary,
        )

        punch = self._find_first_punch(
            employee_id,
            day_start,
            search_end,
        )

        if punch is not None:
            actual = punch.punched_at.astimezone(
                BANGKOK_TZ
            )

            if actual < boundary:
                return AttendanceCheckResult(
                    employee_id=employee_id,
                    duty_date=roster.duty_date,
                    shift_code='NORMAL',
                    status_code='LEAVE_MORNING_RETURNED',
                    status_text=(
                        'ลาเช้า และมีข้อมูลสแกน'
                        'กลับเข้าปฏิบัติงานแล้ว'
                    ),
                    punch_time=actual,
                    leave_session='MORNING',
                )

        if current_time < boundary:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='LEAVE_MORNING_PENDING',
                status_text=(
                    'ลาเช้า - รอสแกนเข้าก่อน 13:00 น.'
                ),
                leave_session='MORNING',
            )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NORMAL',
            status_code='LEAVE_MORNING_MISSING_IN',
            status_text=(
                'ลาเช้า แต่ไม่พบการสแกนเข้าก่อน 13:00 น.'
            ),
            leave_session='MORNING',
        )
    
    # ----------------------------
    # Afternoon Leave
    # ----------------------------

    def _evaluate_afternoon_leave(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        normal_result = self._evaluate_normal_in(
            employee_id,
            roster,
        )

        if normal_result.status_code == 'MISSING_IN':
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='LEAVE_AFTERNOON_MISSING_IN',
                status_text=(
                    'ลาบ่าย แต่ไม่พบข้อมูล'
                    'การมาปฏิบัติงานช่วงเช้า'
                ),
                leave_session='AFTERNOON',
            )

        if normal_result.status_code == 'LATE':
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='LEAVE_AFTERNOON_LATE',
                status_text=(
                    f'ลาบ่าย / มาสาย'
                    f'{normal_result.minutes} นาที /'
                    f'รอสแกนออกหลัง 12:00 น.'
                ),
                punch_time=normal_result.punch_time,
                minutes=normal_result.minutes,
                leave_session='AFTERNOON',
            )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NORMAL',
            status_code='LEAVE_AFTERNOON_PRESENT',
            status_text=(
                'ลาบ่าย / มาปฏิบัติงานช่วงเช้าปกติ /'
                'รอสแกนออกหลัง 12:00 น.'
            ),
            punch_time=normal_result.punch_time,
            leave_session='AFTERNOON',
        )
 
    # ----------------------------
    # Previous night duty
    # ----------------------------

    def _evaluate_previous_night_duty(
            self,
            employee_id: int,
            check_date: date,
    ) -> AttendanceCheckResult | None:
        previous_date = check_date - timedelta(days=1)

        roster = self._get_roster(
            employee_id,
            previous_date,
        )

        if roster is None:
            return None

        shift_type = self.db.get(
            shift_type,
            roster.shift_type_id,
        )

        if (
            shift_type is None
            or shift_type.shift_code != 'NIGHT_DUTY'
        ):
            return None

        rule = self._get_shift_rule(
            roster.shift_type_id,
            'MORNING_RETURN_IN',
        )

        if rule is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=previous_date,
                shift_code='NIGHT_DUTY',
                status_code='RULE_NOT_FOUND',
                status_text=(
                    'ไม่พบกฎกลับเข้าปฏิบัติงาน'
                    'หลังพักเวรเช้า'
                ),
            )

        scan_date = previous_date + timedelta(
            days=rule.day_offset
        )

        scan_start = self._make_datetime(
            scan_date,
            rule.scan_window_start,
        )

        scan_end = self._make_datetime(
            scan_date,
            rule.scan_window_end,
        )

        punch = self._find_first_punch(
            employee_id,
            scan_start,
            scan_end,
        )

        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NIGHT_DUTY',
                status_code='NIGHT_RETURN_MISSING',
                status_text=(
                    'เวรกลางคืน - ไม่พบข้อมูล'
                    'สแกนกลับเข้าหลังพักเวรเช้า'
                ),
            )

        actual = punch.punched_at.astimezone(
            BANGKOK_TZ
        )

        on_time_end = self._make_datetime(
            scan_date,
            rule.on_time_end,
        )

        if actual <= on_time_end:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=previous_date,
                shift_code='NIGHT_DUTY',
                status_text=(
                    'เวรกลางคืน - '
                    'กลับเข้าปฏิบัติงานปกติ'
                ),
                punch_time=actual,
                minutes=0,
            )

        late_minute = self._minutes_after(
            actual,
            on_time_end,
        )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NIGHT_DUTY',
            status_code='NIGHT_RETURN_LATE',
            status_text=(
                f'เวรกลางคืน - '
                f'กลับเข้าปฏิบัติงานช้า '
                f'{late_minute} นาที'
            ),
            punch_time=actual,
            minutes=late_minute,
        )
    
    # ----------------------------
    # NMain check
    # ----------------------------

    def check_attendance(
            self,
            employee_id: int,
            check_date: date,
            current_time: datetime,
    ) -> AttendanceCheckResult:

        current_time = current_time.astimezone(
            BANGKOK_TZ
        )

        # 1. ตรวจเวรกลางคืนของวันก่อน
        previous_night = (
            self._evaluate_previous_night_duty(
                employee_id,
                check_date,
            )
        )

        if previous_night is not None:
            return previous_night

        # 2. หาตารางงานวันนี้
        roster = self._get_roster(
            employee_id,
            check_date,
        )

        if roster is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=check_date,
                shift_code=None,
                status_code='NO_ROSTER',
                status_text='ไม่พบตารางปฏิบัติงาน',
            )

        shift_type = self.db.get(
            ShiftType,
            roster.shift_type_id,
        )

        if shift_type is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=check_date,
                status_code='SHIFT_NOT_FOUND',
                status_text='ไม่พบประเภทกะ',
            )

        # 3. ตรวจการลา
        leave = self._get_approved_leave(
            employee_id,
            check_date,
        )

        if leave is not None:

            if leave.leave_session == "FULL_DAY":
                return AttendanceCheckResult(
                    employee_id=employee_id,
                    duty_date=check_date,
                    shift_code=shift_type.shift_code,
                    status_code="LEAVE_FULL_DAY",
                    status_text="ลาเต็มวัน",
                    leave_session="FULL_DAY",
                )

            if leave.leave_session == 'MORNING':
                return self._evaluate_morning_leave(
                    employee_id,
                    roster,
                    current_time,
                )

            if leave.leave_session == 'AFTERNOON':
                return self._evaluate_afternoon_leave(
                    employee_id,
                    roster,
                )

        # 4. งานปกติ
        if shift_type.shift_code == 'NORMAL':
            return self._evaluate_normal_in(
                employee_id,
                roster,
            )

        # 5. เวรกลางคืนของวันนี้
        if shift_type.shift_code == 'NIGHT_DUTY':
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=check_date,
                shift_code='NIGHT_DUTY',
                status_code='NIGHT_DUTY',
                status_text='เข้าเวรกลางคืน',
            )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=check_date,
            shift_code=shift_type.shift_code,
            status_code='UNKNOWN_SHIFT',
            status_text='ไม่สามารถประเมินประเภทกะนี้ได้',
        )