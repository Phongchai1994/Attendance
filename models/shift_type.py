from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import TimestampMixin, Base

if TYPE_CHECKING:
    from models.shift_rule import ShiftRule
    from models.duty_roster import DutyRoster


class ShiftType(TimestampMixin, Base):
    __tablename__ = 'shift_types'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    shift_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    shift_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    crosses_midnight: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    rules: Mapped[list["ShiftRule"]] = relationship(
        back_populates="shift_type",
        cascade="all, delete-orphan",
    )

    duty_rosters: Mapped[list['DutyRoster']] = relationship(
        back_populates='shift_type'
    )