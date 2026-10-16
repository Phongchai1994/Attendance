from typing import TYPE_CHECKING

from datetime import time

from sqlalchemy import String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class LeaveAttendanceRule(TimestampMixin, Base):
    __tablename__ = 'leave_attendance_rules'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    leave_session: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )

    required_event: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    boundary_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    comparison: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=False,
    )