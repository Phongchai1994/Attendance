from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class AttendanceDailyResult(TimestampMixin, Base):
    __tablename__ = 'attendance_daily_result'

    __table_args__ = (
        UniqueConstraint(
            'employee_id',
            'duty_date',
            name='uq_attendance_daily_employee_date',
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey('employees.id'),
        nullable=False,
        index=True,
    )

    roster_id: Mapped[int | None] = mapped_column(
        ForeignKey('duty_rosters.id'),
        nullable=True,
    )

    duty_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    shift_code: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    leave_session: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    first_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    evening_rest_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    morning_return_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    early_leave_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    final_status_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    final_status_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )