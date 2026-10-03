from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.attendance_punch import AttendancePunch

class Device(TimestampMixin, Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    device_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    device_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    port: Mapped[int] = mapped_column(
        Integer,
        default=4370,
        nullable=False,
    )

    location_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    device_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    punches: Mapped[list["AttendancePunch"]] = relationship(
        back_populates="device"
    )