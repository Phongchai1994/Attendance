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
    from models.employee import Employee

class OfficialDuty(TimestampMixin, Base):
    __tablename__ = 'official_duties'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey('employees.id'),
        nullable=False,
        index=True,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    duty_session: Mapped[str] = mapped_column(
        String(20),
        default='FULL_DAY',
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    destination: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    document_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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
        back_populates='official_duties'
    )