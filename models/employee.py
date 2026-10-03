from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.attendance_punch import AttendancePunch
    from models.department import Department


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    employee_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    position_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    position_level: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"),
        nullable=True,
    )

    card_no: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    legacy_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
        index=True,
    )

    hired_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    department: Mapped["Department | None"] = relationship(
        back_populates="employees"
    )

    punches: Mapped[list["AttendancePunch"]] = relationship(
        back_populates='employee'
    )