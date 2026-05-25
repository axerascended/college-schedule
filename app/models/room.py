from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.schedule_entry import ScheduleEntry


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(50), unique=True)
    capacity: Mapped[int] = mapped_column(Integer, default=30)

    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(back_populates="room")
