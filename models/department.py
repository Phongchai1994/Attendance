from typing import TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.employee import Employee

class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    department_code: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )

    department_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department"
    )