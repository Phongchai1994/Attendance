from typing import TYPE_CHECKING

from datetime import time

from sqlalchemy import(
    Boolean,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.shift_type import ShiftType


class ShiftRule(TimestampMixin, Base):
    __tablename__ = "shift_rules"

    __table_args__ = (
        UniqueConstraint(
            "shift_type_id",
            "rule_code",
            name="uq_shift_rule_code",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    shift_type_id: Mapped[int] = mapped_column(
        ForeignKey('shift_types.id'),
        nullable=False,
        index=True,
    )

    rule_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    rule_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    day_offset: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    scan_window_start: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    scan_window_end: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    on_time_start: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    on_time_end: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    sequence_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    shift_type: Mapped["ShiftType"] = relationship(
        back_populates='rules'
    )