from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.employee import Employee
    from models.shift_type import ShiftType


class DutyRoster(TimestampMixin, Base):
    __tablename__ = 'duty_rosters'

    __table_args__ = (
        UniqueConstraint(
            'employee_id',
            'duty_date',
            name='uq_employee_duty_date',
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

    duty_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    shift_type_id: Mapped[int] = mapped_column(
        ForeignKey('shift_types.id'),
        nullable=False,
        index=True,
    )

    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        default='MANUAL',
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    employee: Mapped["Employee"] = relationship(
        back_populates='duty_rosters'
    )

    shift_type: Mapped['ShiftType'] = relationship(
        back_populates='duty_rosters'
    )