import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.group import Group
from app.models.room import Room
from app.models.schedule_entry import ScheduleEntry, SchedulePeriod, WeekType
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.time_slot import TimeSlot


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_data(db_session):
    group = Group(name="Тест-1", course="1")
    group2 = Group(name="Тест-2", course="1")
    subject = Subject(name="Алгебра")
    teacher = Teacher(full_name="Тестов Т.Т.")
    teacher2 = Teacher(full_name="Другой Д.Д.")
    room = Room(number="1", capacity=30)
    room2 = Room(number="2", capacity=30)
    slot = TimeSlot(
        day_of_week=0,
        pair_number=1,
        start_time=datetime.time(8, 0),
        end_time=datetime.time(9, 30),
    )
    slot2 = TimeSlot(
        day_of_week=0,
        pair_number=2,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 30),
    )
    period = SchedulePeriod(
        name="Семестр",
        valid_from=datetime.date(2025, 9, 1),
        valid_to=datetime.date(2026, 6, 30),
    )
    for obj in [group, group2, subject, teacher, teacher2, room, room2, slot, slot2, period]:
        db_session.add(obj)
    db_session.commit()
    return {
        "group": group,
        "group2": group2,
        "subject": subject,
        "teacher": teacher,
        "teacher2": teacher2,
        "room": room,
        "room2": room2,
        "slot": slot,
        "slot2": slot2,
        "period": period,
    }
