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

        return max(
            0,
            int(difference.total_seconds() // 60),
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

    def _evaluate_normal_out(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        rule = self._get_shift_rule(
            roster.shift_type_id,
            'NORMAL_OUT',
        )

        if rule is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='RULE_NOT_FOUND',
                status_text='ไม่พบกฎเวลาออกงานปกติ',
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

        punch = self._find_last_punch(
            employee_id,
            scan_start,
            scan_end,
        )

        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='MISSING_OUT',
                status_text='ไม่มีข้อมูลสแกนออกงาน',
            )

        actual = punch.punched_at.astimezone(
            BANGKOK_TZ
        )

        expected_out = self._make_datetime(
            scan_date,
            rule.on_time_start,
        )

        if actual < expected_out:
            early_minutes = self._minutes_before(
                actual,
                expected_out,
            )

            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='EARLY_LEAVE',
                status_text=(
                    f'ออกก่อนเวลา {early_minutes} นาที'
                ),
                punch_time=actual,
                minutes=early_minutes,
            )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NORMAL',
            status_code='NORMAL_OUT',
            status_text='ออกงานปกติ',
            punch_time=actual,
            minutes=0
        )

    def _evaluate_afternoon_leave_out(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        boundary = self._make_datetime(
            roster.duty_date,
            time(12, 0),
        )

        day_end = self._make_datetime(
            roster.duty_date,
            time(23, 59, 59),
        )

        # เงื่อนไขคือ "หลัง 12.00"
        search_start = boundary + timedelta(seconds=1)

        punch = self._find_last_punch(
            employee_id,
            search_start,
            day_end,
        )

        if punch is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NORMAL',
                status_code='LEAVE_AFTERNOON_MISSING_OUT',
                status_text=(
                    'ลาบ่าย แต่ไม่พบข้อมูลสแกนออกหลัง 12:00 น.'
                ),
                leave_session='AFTERNOON',
            )

        actual = punch.punched_at.astimezone(
            BANGKOK_TZ
        )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NORMAL',
            status_code='LEAVE_AFTERNOON_OUT_OK',
            status_text='ลาบ่าย - สแกนถูกต้อง',
            punch_time=actual,
            leave_session='AFTERNOON',
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

    def _evaluate_night_evening_rest(
            self,
            employee_id: int,
            roster: DutyRoster,
    ) -> AttendanceCheckResult:

        rule = self._get_shift_rule(
            roster.shift_type_id,
            'EVENING_REST_out',
        )

        if rule is None:
            return AttendanceCheckResult(
                employee_id=employee_id,
                duty_date=roster.duty_date,
                shift_code='NIGHT_DUTY',
                status_code='RULE_NOT_FOUND',
                status_text='ไม่พบกฎออกพักเวรช่วงเย็น',
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
                shift_code='NIGHT_DUTY',
                status_code='NIGHT_REST_OUT_MISSING',
                status_text=(
                    'เวรกลางคืน - ไม่พบการสแกนออกพักเวรช่วงเย็น'
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
                duty_date=roster.duty_date,
                shift_code='NIGHT_DUTY',
                status_code='NIGHT_REST_OUT_NORMAL',
                status_text=(
                    'เวรกลางคืน - ออกพักเวรช่วงเย็นปกติ'
                ),
                punch_time=actual,
            )

        return AttendanceCheckResult(
            employee_id=employee_id,
            duty_date=roster.duty_date,
            shift_code='NIGHT_DUTY',
            status_code='NIGHT_REST_OUT_LATE',
            status_text=(
                'เวรกลางคืน - สแกนออกพักเวร'
                'หลังช่วง 15:00-15:30 น.'
            ),
            punch_time=actual
        )

    def _build_normal_final_status(
        self,
        in_result: AttendanceCheckResult,
        out_result: AttendanceCheckResult,
    ) -> tuple[str, str]:

        if (
            in_result.status_code == "MISSING_IN"
            and out_result.status_code == "MISSING_OUT"
        ):
            return (
                "MISSING_IN_OUT",
                "ไม่พบข้อมูลสแกนเข้าและออกงาน",
            )

        if in_result.status_code == "MISSING_IN":
            return (
                "MISSING_IN",
                "ไม่พบข้อมูลสแกนเข้างาน",
            )

        if out_result.status_code == "MISSING_OUT":
            return (
                "MISSING_OUT",
                "ไม่พบข้อมูลสแกนออกงาน",
            )

        if (
            in_result.status_code == "LATE"
            and out_result.status_code == "EARLY_LEAVE"
        ):
            return (
                "LATE_AND_EARLY",
                (
                    f"มาสาย {in_result.minutes} นาที "
                    f"และออกก่อน {out_result.minutes} นาที"
                ),
            )

        if in_result.status_code == "LATE":
            return (
                "LATE",
                f"มาสาย {in_result.minutes} นาที",
            )

        if out_result.status_code == "EARLY_LEAVE":
            return (
                "EARLY_LEAVE",
                f"ออกก่อนเวลา {out_result.minutes} นาที",
            )

        return (
            "NORMAL",
            "มาปฏิบัติงานและออกงานปกติ",
        )
    
    # ----------------------------
    # Main check
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

    def finalize_dialy_attendance(
            self,
            employee_id: int,
            duty_date: date,
    ) -> AttendanceDailyResult:

        roster = self._get_roster(
            employee_id,
            duty_date
        )

        if roster is None:
            raise ValueError(
                'ไม่พบตารางปฏิบัติงานของพนักงาน'
            )

        shift_type = self.db.get(
            ShiftType,
            roster.shift_type_id,
        )

        if shift_type is None:
            raise ValueError('ไม่พบประเภทกะ')

        leave = self._get_approved_leave(
            employee_id,
            duty_date,
        )

        existing = (
            self.db.query(AttendanceDailyResult)
            .filter(
                AttendanceDailyResult.employee_id == employee_id,
                AttendanceDailyResult.duty_date == duty_date,
            )
            .first()
        )

        if existing is None:
            result = AttendanceDailyResult(
                employee_id=employee_id,
                roster_id=roster.id,
                duty_date=duty_date,
                shift_code=shift_type.shift_code,
                final_status_code="PROCESSING",
                final_status_text="กำลังประมวลผล",
            )

            self.db.add(result)

        else:
            result = existing

        # -----------------------------------
        # ลาเต็มวัน
        # -----------------------------------

        if (
            leave is not None
            and leave.leave_session == 'FULL_DAY'
        ):
            result.leave_session = 'FULL_DAY'
            result.final_status_code = 'LEAVE_FULL_DAY'
            result.final_status_text = 'ลาเต็มวัน'

        # -----------------------------------
        # ลาเช้า
        # -----------------------------------
        
        elif (
            leave is not None
            and leave.leave_session == "MORNING"
        ):
            end_of_day = self._make_datetime(
                duty_date,
                time(23, 59, 59),
            )

            morning_result = (
                self._evaluate_morning_leave(
                    employee_id,
                    roster,
                    end_of_day,
                )
            )

            out_result = self._evaluate_normal_out(
                employee_id,
                roster,
            )

            result.leave_session = "MORNING"

            result.first_in_at = (
                morning_result.punch_time
            )

            result.last_out_at = (
                out_result.punch_time
            )

            if (
                morning_result.status_code
                == "LEAVE_MORNING_RETURNED"
                and out_result.status_code
                == "NORMAL_OUT"
            ):
                result.final_status_code = (
                    "LEAVE_MORNING_COMPLETE"
                )

                result.final_status_text = (
                    "ลาเช้าครึ่งวัน "
                    "และปฏิบัติงานช่วงบ่ายถูกต้อง"
                )

            else:
                result.final_status_code = (
                    "LEAVE_MORNING_ISSUE"
                )

                result.final_status_text = (
                    f"{morning_result.status_text} / "
                    f"{out_result.status_text}"
                )

                if out_result.status_code == "EARLY_LEAVE":
                    result.early_leave_minutes = (
                        out_result.minutes or 0
                    )

        # ----------------------------------------
        # ลาบ่าย
        # ----------------------------------------

        elif (
            leave is not None
            and leave.leave_session == "AFTERNOON"
        ):

            in_result = self._evaluate_normal_in(
                employee_id,
                roster,
            )

            out_result = (
                self._evaluate_afternoon_leave_out(
                    employee_id,
                    roster,
                )
            )

            result.leave_session = "AFTERNOON"

            result.first_in_at = in_result.punch_time
            result.last_out_at = out_result.punch_time

            if (
                in_result.status_code
                in ("NORMAL", "LATE")
                and out_result.status_code
                == "LEAVE_AFTERNOON_OUT_OK"
            ):

                if in_result.status_code == "LATE":
                    result.final_status_code = (
                        "LEAVE_AFTERNOON_LATE"
                    )

                    result.final_status_text = (
                        f"ลาบ่าย / "
                        f"มาสาย {in_result.minutes} นาที"
                    )

                    result.late_minutes = (
                        in_result.minutes or 0
                    )

                else:
                    result.final_status_code = (
                        "LEAVE_AFTERNOON_COMPLETE"
                    )

                    result.final_status_text = (
                        "ปฏิบัติงานช่วงเช้าและลาบ่ายถูกต้อง"
                    )

            else:
                result.final_status_code = (
                    "LEAVE_AFTERNOON_ISSUE"
                )

                result.final_status_text = (
                    f"{in_result.status_text} / "
                    f"{out_result.status_text}"
                )

        # ----------------------------------------
        # NORMAL
        # ----------------------------------------

        elif shift_type.shift_code == "NORMAL":

            in_result = self._evaluate_normal_in(
                employee_id,
                roster,
            )

            out_result = self._evaluate_normal_out(
                employee_id,
                roster,
            )

            status_code, status_text = (
                self._build_normal_final_status(
                    in_result,
                    out_result,
                )
            )

            result.first_in_at = in_result.punch_time
            result.last_out_at = out_result.punch_time

            result.late_minutes = (
                in_result.minutes or 0
                if in_result.status_code == "LATE"
                else 0
            )

            result.early_leave_minutes = (
                out_result.minutes or 0
                if out_result.status_code == "EARLY_LEAVE"
                else 0
            )

            result.final_status_code = status_code
            result.final_status_text = status_text

        # ----------------------------------------
        # NIGHT DUTY
        # ----------------------------------------

        elif shift_type.shift_code == "NIGHT_DUTY":

            evening_result = (
                self._evaluate_night_evening_rest(
                    employee_id,
                    roster,
                )
            )

            next_date = duty_date + timedelta(days=1)

            morning_result = (
                self._evaluate_previous_night_duty(
                    employee_id,
                    next_date,
                )
            )

            result.evening_rest_out_at = (
                evening_result.punch_time
            )

            if morning_result is not None:
                result.morning_return_in_at = (
                    morning_result.punch_time
                )

            evening_ok = (
                evening_result.status_code
                == "NIGHT_REST_OUT_NORMAL"
            )

            morning_ok = (
                morning_result is not None
                and morning_result.status_code
                == "NIGHT_RETURN_NORMAL"
            )

            if evening_ok and morning_ok:
                result.final_status_code = (
                    "NIGHT_DUTY_COMPLETE"
                )

                result.final_status_text = (
                    "ปฏิบัติเวรกลางคืนถูกต้อง"
                )

            else:
                result.final_status_code = (
                    "NIGHT_DUTY_ISSUE"
                )

                morning_text = (
                    morning_result.status_text
                    if morning_result is not None
                    else "ไม่พบผลกลับเข้าปฏิบัติงาน"
                )

                result.final_status_text = (
                    f"{evening_result.status_text} / "
                    f"{morning_text}"
                )

        else:
            result.final_status_code = "UNKNOWN_SHIFT"
            result.final_status_text = (
                "ไม่สามารถประมวลผลกะนี้ได้"
            )

        result.finalized_at = datetime.now(
            BANGKOK_TZ
        )

        self.db.commit()
        self.db.refresh(result)

        return result

