import enum
import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.room import Room
    from app.models.subject import Subject
    from app.models.teacher import Teacher
    from app.models.time_slot import TimeSlot


class WeekType(str, enum.Enum):
    every = "every"
    odd = "odd"
    even = "even"


class SchedulePeriod(Base):
    __tablename__ = "schedule_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="Семестр")
    valid_from: Mapped[datetime.date] = mapped_column(Date)
    valid_to: Mapped[datetime.date] = mapped_column(Date)
    is_published: Mapped[bool] = mapped_column(default=False)

    entries: Mapped[list["ScheduleEntry"]] = relationship(back_populates="period")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("schedule_periods.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"))
    week_type: Mapped[WeekType] = mapped_column(Enum(WeekType), default=WeekType.every)
    valid_from: Mapped[datetime.date] = mapped_column(Date)
    valid_to: Mapped[datetime.date] = mapped_column(Date)

    period: Mapped["SchedulePeriod"] = relationship(back_populates="entries")
    group: Mapped["Group"] = relationship(back_populates="schedule_entries")
    subject: Mapped["Subject"] = relationship(back_populates="schedule_entries")
    teacher: Mapped["Teacher"] = relationship(back_populates="schedule_entries")
    room: Mapped["Room"] = relationship(back_populates="schedule_entries")
    time_slot: Mapped["TimeSlot"] = relationship(back_populates="schedule_entries")
