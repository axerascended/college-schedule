"""Заполнение БД демо-данными: python -m app.scripts.seed"""

import datetime

from app.database import SessionLocal
from app.models.group import Group
from app.models.room import Room
from app.models.schedule_entry import ScheduleEntry, SchedulePeriod, WeekType
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.time_slot import TimeSlot
from app.models.user import User, UserRole
from app.repositories.group_repository import GroupRepository
from app.services.auth_service import AuthService

PAIR_TIMES = [
    (datetime.time(8, 30), datetime.time(10, 0)),
    (datetime.time(10, 15), datetime.time(11, 45)),
    (datetime.time(12, 0), datetime.time(13, 30)),
    (datetime.time(14, 0), datetime.time(15, 30)),
    (datetime.time(15, 45), datetime.time(17, 15)),
    (datetime.time(17, 30), datetime.time(19, 0)),
]


def run_seed() -> None:
    db = SessionLocal()
    try:
        if GroupRepository(db).list_all():
            print("База уже содержит данные, пропуск seed.")
            return

        groups = [
            Group(name="ИС-21", course="2"),
            Group(name="П-31", course="3"),
            Group(name="Э-11", course="1"),
        ]
        for g in groups:
            db.add(g)
        db.flush()

        subjects = [
            Subject(name="Математика"),
            Subject(name="Программирование"),
            Subject(name="Базы данных"),
            Subject(name="Физическая культура"),
        ]
        for s in subjects:
            db.add(s)
        db.flush()

        teachers = [
            Teacher(full_name="Иванов И.И."),
            Teacher(full_name="Петрова А.С."),
            Teacher(full_name="Сидоров П.П."),
        ]
        for t in teachers:
            db.add(t)
        db.flush()

        rooms = [
            Room(number="101", capacity=30),
            Room(number="202", capacity=25),
            Room(number="спортзал", capacity=40),
        ]
        for r in rooms:
            db.add(r)
        db.flush()

        for day in range(6):
            for pair_num, (start, end) in enumerate(PAIR_TIMES, start=1):
                db.add(
                    TimeSlot(
                        day_of_week=day,
                        pair_number=pair_num,
                        start_time=start,
                        end_time=end,
                    )
                )
        db.flush()

        period = SchedulePeriod(
            name="Семестр 1 (2025–2026)",
            valid_from=datetime.date(2025, 9, 1),
            valid_to=datetime.date(2026, 1, 31),
            is_published=True,
        )
        db.add(period)
        db.flush()

        slots = db.query(TimeSlot).order_by(TimeSlot.id).all()
        mon_pair1 = next(s for s in slots if s.day_of_week == 0 and s.pair_number == 1)
        mon_pair2 = next(s for s in slots if s.day_of_week == 0 and s.pair_number == 2)
        wed_pair3 = next(s for s in slots if s.day_of_week == 2 and s.pair_number == 3)

        entries = [
            ScheduleEntry(
                period_id=period.id,
                group_id=groups[0].id,
                subject_id=subjects[1].id,
                teacher_id=teachers[0].id,
                room_id=rooms[0].id,
                time_slot_id=mon_pair1.id,
                week_type=WeekType.every,
                valid_from=period.valid_from,
                valid_to=period.valid_to,
            ),
            ScheduleEntry(
                period_id=period.id,
                group_id=groups[0].id,
                subject_id=subjects[2].id,
                teacher_id=teachers[1].id,
                room_id=rooms[1].id,
                time_slot_id=mon_pair2.id,
                week_type=WeekType.odd,
                valid_from=period.valid_from,
                valid_to=period.valid_to,
            ),
            ScheduleEntry(
                period_id=period.id,
                group_id=groups[1].id,
                subject_id=subjects[0].id,
                teacher_id=teachers[2].id,
                room_id=rooms[0].id,
                time_slot_id=wed_pair3.id,
                week_type=WeekType.every,
                valid_from=period.valid_from,
                valid_to=period.valid_to,
            ),
        ]
        for e in entries:
            db.add(e)

        auth = AuthService(db)
        if not auth.users.get_by_email("admin@college.local"):
            auth.create_user(
                "admin@college.local",
                "admin123",
                "Администратор",
                UserRole.admin,
            )
        if not auth.users.get_by_email("student@college.local"):
            auth.create_user(
                "student@college.local",
                "student123",
                "Студент Иванов",
                UserRole.student,
                group_id=groups[0].id,
            )
        if not auth.users.get_by_email("teacher@college.local"):
            auth.create_user(
                "teacher@college.local",
                "teacher123",
                "Иванов И.И.",
                UserRole.teacher,
                teacher_id=teachers[0].id,
            )

        db.commit()
        print("Seed выполнен: группы, предметы, расписание, admin@college.local / admin123")
        print("Студент: student@college.local / student123")
        print("Преподаватель: teacher@college.local / teacher123")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
