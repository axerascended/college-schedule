from sqlalchemy.orm import Session

from app.schemas.schedule import ScheduleEntryCreate, ScheduleEntryUpdate
from app.services.schedule_service import ScheduleService, ScheduleServiceError


class TeacherScheduleService:
    """Редактирование расписания только для своих занятий."""

    def __init__(self, db: Session, teacher_id: int):
        self.teacher_id = teacher_id
        self.schedule = ScheduleService(db)

    def get_entry(self, entry_id: int):
        entry = self.schedule.get_entry(entry_id)
        if entry is None:
            raise ScheduleServiceError("Занятие не найдено")
        if entry.teacher_id != self.teacher_id:
            raise ScheduleServiceError("Можно изменять только свои занятия")
        return entry

    def create_entry(self, data: ScheduleEntryCreate):
        if data.teacher_id != self.teacher_id:
            raise ScheduleServiceError("Можно создавать занятия только от своего имени")
        return self.schedule.create_entry(data)

    def update_entry(self, entry_id: int, data: ScheduleEntryUpdate):
        self.get_entry(entry_id)
        if data.teacher_id != self.teacher_id:
            raise ScheduleServiceError("Нельзя назначить занятие другому преподавателю")
        return self.schedule.update_entry(entry_id, data)

    def delete_entry(self, entry_id: int) -> None:
        self.get_entry(entry_id)
        self.schedule.delete_entry(entry_id)

    def list_my_entries(self, period_id: int | None = None):
        return self.schedule.entries.list_for_teacher(self.teacher_id, period_id)
