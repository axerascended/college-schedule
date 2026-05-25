import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.schedule_entry import ScheduleEntry


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Mon .. 5=Sat
    pair_number: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[datetime.time] = mapped_column(Time)
    end_time: Mapped[datetime.time] = mapped_column(Time)

    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(back_populates="time_slot")
