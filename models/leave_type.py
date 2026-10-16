from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.employee_leave import EmployeeLeave


class LeaveType(TimestampMixin, Base):
    __tablename__ = "leave_types"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    leave_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    leave_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    employee_leaves: Mapped[list["EmployeeLeave"]] = relationship(
        back_populates='leave_type'
    )