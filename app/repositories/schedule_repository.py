import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.schedule_entry import ScheduleEntry, SchedulePeriod
from app.repositories.base_repository import BaseRepository


class SchedulePeriodRepository(BaseRepository[SchedulePeriod]):
    def __init__(self, db: Session):
        super().__init__(db, SchedulePeriod)

    def get_published(self) -> SchedulePeriod | None:
        return (
            self.db.query(SchedulePeriod)
            .filter(SchedulePeriod.is_published.is_(True))
            .order_by(SchedulePeriod.valid_from.desc())
            .first()
        )


class ScheduleEntryRepository(BaseRepository[ScheduleEntry]):
    def __init__(self, db: Session):
        super().__init__(db, ScheduleEntry)

    def list_for_group(self, group_id: int, period_id: int | None = None) -> list[ScheduleEntry]:
        query = (
            self.db.query(ScheduleEntry)
            .options(
                joinedload(ScheduleEntry.subject),
                joinedload(ScheduleEntry.teacher),
                joinedload(ScheduleEntry.room),
                joinedload(ScheduleEntry.time_slot),
                joinedload(ScheduleEntry.group),
            )
            .filter(ScheduleEntry.group_id == group_id)
        )
        if period_id is not None:
            query = query.filter(ScheduleEntry.period_id == period_id)
        return query.all()

    def list_for_teacher(self, teacher_id: int, period_id: int | None = None) -> list[ScheduleEntry]:
        query = (
            self.db.query(ScheduleEntry)
            .options(
                joinedload(ScheduleEntry.subject),
                joinedload(ScheduleEntry.teacher),
                joinedload(ScheduleEntry.room),
                joinedload(ScheduleEntry.time_slot),
                joinedload(ScheduleEntry.group),
            )
            .filter(ScheduleEntry.teacher_id == teacher_id)
        )
        if period_id is not None:
            query = query.filter(ScheduleEntry.period_id == period_id)
        return query.all()

    def list_for_period(self, period_id: int) -> list[ScheduleEntry]:
        return (
            self.db.query(ScheduleEntry)
            .options(
                joinedload(ScheduleEntry.subject),
                joinedload(ScheduleEntry.teacher),
                joinedload(ScheduleEntry.room),
                joinedload(ScheduleEntry.time_slot),
                joinedload(ScheduleEntry.group),
            )
            .filter(ScheduleEntry.period_id == period_id)
            .all()
        )

    def find_overlapping(
        self,
        time_slot_id: int,
        valid_from: datetime.date,
        valid_to: datetime.date,
        exclude_id: int | None = None,
    ) -> list[ScheduleEntry]:
        query = (
            self.db.query(ScheduleEntry)
            .options(
                joinedload(ScheduleEntry.group),
                joinedload(ScheduleEntry.teacher),
                joinedload(ScheduleEntry.room),
                joinedload(ScheduleEntry.time_slot),
            )
            .filter(
                ScheduleEntry.time_slot_id == time_slot_id,
                ScheduleEntry.valid_from <= valid_to,
                ScheduleEntry.valid_to >= valid_from,
            )
        )
        if exclude_id is not None:
            query = query.filter(ScheduleEntry.id != exclude_id)
        return query.all()
