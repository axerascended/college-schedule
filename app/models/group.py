from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.schedule_entry import ScheduleEntry
    from app.models.user import User


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    course: Mapped[str] = mapped_column(String(50), default="")

    students: Mapped[list["User"]] = relationship(back_populates="group")
    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(back_populates="group")
