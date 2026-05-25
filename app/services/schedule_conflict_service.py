import datetime

from sqlalchemy.orm import Session

from app.models.schedule_entry import ScheduleEntry, WeekType
from app.repositories.schedule_repository import ScheduleEntryRepository
from app.schemas.schedule import ConflictDetail

DAY_NAMES = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота")


def week_types_overlap(a: WeekType, b: WeekType) -> bool:
    if a == WeekType.every or b == WeekType.every:
        return True
    return a == b


def dates_overlap(
    start_a: datetime.date,
    end_a: datetime.date,
    start_b: datetime.date,
    end_b: datetime.date,
) -> bool:
    return start_a <= end_b and start_b <= end_a


class ScheduleConflictService:
    def __init__(self, db: Session):
        self.entries = ScheduleEntryRepository(db)

    def check(
        self,
        *,
        group_id: int,
        teacher_id: int,
        room_id: int,
        time_slot_id: int,
        week_type: WeekType,
        valid_from: datetime.date,
        valid_to: datetime.date,
        exclude_id: int | None = None,
    ) -> list[ConflictDetail]:
        conflicts: list[ConflictDetail] = []
        candidates = self.entries.find_overlapping(
            time_slot_id, valid_from, valid_to, exclude_id=exclude_id
        )

        for entry in candidates:
            if not week_types_overlap(week_type, entry.week_type):
                continue
            if not dates_overlap(valid_from, valid_to, entry.valid_from, entry.valid_to):
                continue

            slot = entry.time_slot
            day_label = DAY_NAMES[slot.day_of_week] if slot else "?"
            pair_label = f"{day_label}, {slot.pair_number}-я пара" if slot else "?"

            if entry.group_id == group_id:
                group_name = entry.group.name if entry.group else str(group_id)
                conflicts.append(
                    ConflictDetail(
                        conflict_type="group",
                        message=f"Группа {group_name} уже занята: {pair_label}",
                        entry_id=entry.id,
                    )
                )
            if entry.teacher_id == teacher_id:
                teacher_name = entry.teacher.full_name if entry.teacher else str(teacher_id)
                conflicts.append(
                    ConflictDetail(
                        conflict_type="teacher",
                        message=f"Преподаватель {teacher_name} уже занят: {pair_label}",
                        entry_id=entry.id,
                    )
                )
            if entry.room_id == room_id:
                room_num = entry.room.number if entry.room else str(room_id)
                conflicts.append(
                    ConflictDetail(
                        conflict_type="room",
                        message=f"Аудитория {room_num} уже занята: {pair_label}",
                        entry_id=entry.id,
                    )
                )

        return conflicts

    @staticmethod
    def build_grid(
        entries: list[ScheduleEntry],
        time_slots: list,
        week_filter: WeekType | None = None,
    ) -> dict[tuple[int, int], list[ScheduleEntry]]:
        grid: dict[tuple[int, int], list[ScheduleEntry]] = {}
        for entry in entries:
            if week_filter is not None:
                if entry.week_type == WeekType.every:
                    pass
                elif entry.week_type != week_filter:
                    continue
            key = (entry.time_slot.day_of_week, entry.time_slot.pair_number)
            grid.setdefault(key, []).append(entry)
        return grid
