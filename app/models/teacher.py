from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.schedule_entry import ScheduleEntry
    from app.models.user import User


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))

    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(back_populates="teacher")
    user: Mapped["User | None"] = relationship(back_populates="teacher", uselist=False)
