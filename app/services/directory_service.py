from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.room import Room
from app.models.schedule_entry import SchedulePeriod
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.time_slot import TimeSlot
from app.repositories.group_repository import GroupRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.schedule_repository import SchedulePeriodRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.time_slot_repository import TimeSlotRepository


class DirectoryService:
    def __init__(self, db: Session):
        self.groups = GroupRepository(db)
        self.subjects = SubjectRepository(db)
        self.teachers = TeacherRepository(db)
        self.rooms = RoomRepository(db)
        self.time_slots = TimeSlotRepository(db)
        self.periods = SchedulePeriodRepository(db)

    # Groups
    def list_groups(self) -> list[Group]:
        return self.groups.list_all()

    def save_group(self, name: str, course: str, entity_id: int | None = None) -> Group:
        if entity_id:
            entity = self.groups.get_by_id(entity_id)
            if entity is None:
                raise ValueError("Группа не найдена")
            entity.name = name
            entity.course = course
            return self.groups.update(entity)
        return self.groups.create(Group(name=name, course=course))

    def delete_group(self, entity_id: int) -> None:
        entity = self.groups.get_by_id(entity_id)
        if entity:
            self.groups.delete(entity)

    # Subjects
    def list_subjects(self) -> list[Subject]:
        return self.subjects.list_all()

    def save_subject(self, name: str, entity_id: int | None = None) -> Subject:
        if entity_id:
            entity = self.subjects.get_by_id(entity_id)
            if entity is None:
                raise ValueError("Предмет не найден")
            entity.name = name
            return self.subjects.update(entity)
        return self.subjects.create(Subject(name=name))

    def delete_subject(self, entity_id: int) -> None:
        entity = self.subjects.get_by_id(entity_id)
        if entity:
            self.subjects.delete(entity)

    # Teachers
    def list_teachers(self) -> list[Teacher]:
        return self.teachers.list_all()

    def save_teacher(self, full_name: str, entity_id: int | None = None) -> Teacher:
        if entity_id:
            entity = self.teachers.get_by_id(entity_id)
            if entity is None:
                raise ValueError("Преподаватель не найден")
            entity.full_name = full_name
            return self.teachers.update(entity)
        return self.teachers.create(Teacher(full_name=full_name))

    def delete_teacher(self, entity_id: int) -> None:
        entity = self.teachers.get_by_id(entity_id)
        if entity:
            self.teachers.delete(entity)

    # Rooms
    def list_rooms(self) -> list[Room]:
        return self.rooms.list_all()

    def save_room(self, number: str, capacity: int, entity_id: int | None = None) -> Room:
        if entity_id:
            entity = self.rooms.get_by_id(entity_id)
            if entity is None:
                raise ValueError("Аудитория не найдена")
            entity.number = number
            entity.capacity = capacity
            return self.rooms.update(entity)
        return self.rooms.create(Room(number=number, capacity=capacity))

    def delete_room(self, entity_id: int) -> None:
        entity = self.rooms.get_by_id(entity_id)
        if entity:
            self.rooms.delete(entity)

    # Time slots
    def list_time_slots(self) -> list[TimeSlot]:
        return self.time_slots.list_ordered()

    # Periods
    def list_periods(self) -> list[SchedulePeriod]:
        return self.periods.list_all()

    def save_period(
        self,
        name: str,
        valid_from,
        valid_to,
        entity_id: int | None = None,
    ) -> SchedulePeriod:
        if entity_id:
            entity = self.periods.get_by_id(entity_id)
            if entity is None:
                raise ValueError("Период не найден")
            entity.name = name
            entity.valid_from = valid_from
            entity.valid_to = valid_to
            return self.periods.update(entity)
        return self.periods.create(
            SchedulePeriod(name=name, valid_from=valid_from, valid_to=valid_to)
        )
