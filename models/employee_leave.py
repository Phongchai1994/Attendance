from typing import TYPE_CHECKING

from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.leave_type import LeaveType
    from models.employee import Employee


class EmployeeLeave(TimestampMixin, Base):
    __tablename__ = 'employee_leaves'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey('employees.id'),
        nullable=False,
        index=True,
    )

    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey('leave_types.id'),
        nullable=False,
    )

    leave_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    leave_session: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    approval_status: Mapped[str] = mapped_column(
        String(20),
        default='APPROVED',
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

    employee: Mapped['Employee'] = relationship(
        back_populates='leaves'
    )

    leave_type: Mapped['LeaveType'] = relationship(
        back_populates='employee_leaves'
    )