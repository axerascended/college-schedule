from sqlalchemy.orm import Session

from app.models.schedule_entry import ScheduleEntry, SchedulePeriod
from app.repositories.schedule_repository import ScheduleEntryRepository, SchedulePeriodRepository
from app.repositories.time_slot_repository import TimeSlotRepository
from app.schemas.schedule import ConflictDetail, ScheduleEntryCreate, ScheduleEntryUpdate
from app.services.schedule_conflict_service import ScheduleConflictService


class ScheduleServiceError(Exception):
    def __init__(self, message: str, conflicts: list[ConflictDetail] | None = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db
        self.entries = ScheduleEntryRepository(db)
        self.periods = SchedulePeriodRepository(db)
        self.time_slots = TimeSlotRepository(db)
        self.conflicts = ScheduleConflictService(db)

    def get_entry(self, entry_id: int) -> ScheduleEntry | None:
        return self.entries.get_by_id(entry_id)

    def list_periods(self) -> list[SchedulePeriod]:
        return self.periods.list_all()

    def get_period(self, period_id: int) -> SchedulePeriod | None:
        return self.periods.get_by_id(period_id)

    def publish_period(self, period_id: int) -> SchedulePeriod:
        for period in self.periods.list_all():
            period.is_published = period.id == period_id
            self.periods.update(period)
        period = self.periods.get_by_id(period_id)
        if period is None:
            raise ScheduleServiceError("Период не найден")
        return period

    def create_entry(self, data: ScheduleEntryCreate) -> ScheduleEntry:
        conflict_list = self.conflicts.check(
            group_id=data.group_id,
            teacher_id=data.teacher_id,
            room_id=data.room_id,
            time_slot_id=data.time_slot_id,
            week_type=data.week_type,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
        )
        if conflict_list:
            raise ScheduleServiceError("Обнаружены конфликты расписания", conflict_list)

        entry = ScheduleEntry(**data.model_dump())
        return self.entries.create(entry)

    def update_entry(self, entry_id: int, data: ScheduleEntryUpdate) -> ScheduleEntry:
        entry = self.entries.get_by_id(entry_id)
        if entry is None:
            raise ScheduleServiceError("Занятие не найдено")

        conflict_list = self.conflicts.check(
            group_id=data.group_id,
            teacher_id=data.teacher_id,
            room_id=data.room_id,
            time_slot_id=data.time_slot_id,
            week_type=data.week_type,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            exclude_id=entry_id,
        )
        if conflict_list:
            raise ScheduleServiceError("Обнаружены конфликты расписания", conflict_list)

        for key, value in data.model_dump().items():
            setattr(entry, key, value)
        return self.entries.update(entry)

    def delete_entry(self, entry_id: int) -> None:
        entry = self.entries.get_by_id(entry_id)
        if entry is None:
            raise ScheduleServiceError("Занятие не найдено")
        self.entries.delete(entry)

    def get_grid_data(
        self,
        group_id: int,
        period_id: int,
        week_filter=None,
    ):
        entries = self.entries.list_for_group(group_id, period_id)
        slots = self.time_slots.list_ordered()
        grid = ScheduleConflictService.build_grid(entries, slots, week_filter)
        pairs = sorted({s.pair_number for s in slots})
        days = sorted({s.day_of_week for s in slots})
        slot_map = {(s.day_of_week, s.pair_number): s for s in slots}
        return grid, pairs, days, slot_map, entries
