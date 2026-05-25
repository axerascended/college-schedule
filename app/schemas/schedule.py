import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.schedule_entry import WeekType


class ScheduleEntryCreate(BaseModel):
    period_id: int
    group_id: int
    subject_id: int
    teacher_id: int
    room_id: int
    time_slot_id: int
    week_type: WeekType = WeekType.every
    valid_from: datetime.date
    valid_to: datetime.date


class ScheduleEntryUpdate(ScheduleEntryCreate):
    pass


class ConflictDetail(BaseModel):
    conflict_type: str
    message: str
    entry_id: int | None = None
