from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.device import Device
    from models.employee import Employee


class AttendancePunch(TimestampMixin, Base):
    __tablename__ = "attendance_punches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    device_id: Mapped[int | None] = mapped_column(
        ForeignKey('devices.id'),
        nullable=True,
        index=True,
    )

    punched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    direction_hint: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    verify_code: Mapped[str | None] = mapped_column(
        Integer,
        nullable=True,
    )

    work_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ZK",
    )

    source_ref: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    legacy_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    raw_check_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    raw_sensor_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    employee: Mapped['Employee'] = relationship(
        back_populates='punches'
    )

    device: Mapped["Device | None"] = relationship(
        back_populates='punches'
    )