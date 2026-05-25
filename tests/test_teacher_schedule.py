import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.group import Group
from app.models.room import Room
from app.models.schedule_entry import ScheduleEntry, SchedulePeriod, WeekType
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.time_slot import TimeSlot
from app.models.user import UserRole
from app.services.auth_service import AuthService


@pytest.fixture
def teacher_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        db = TestingSession()
        group = Group(name="ИС-1", course="1")
        subject = Subject(name="Математика")
        teacher1 = Teacher(full_name="Первый")
        teacher2 = Teacher(full_name="Второй")
        room = Room(number="101", capacity=30)
        slot = TimeSlot(
            day_of_week=0,
            pair_number=1,
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 30),
        )
        period = SchedulePeriod(
            name="Сем",
            valid_from=datetime.date(2025, 9, 1),
            valid_to=datetime.date(2026, 6, 30),
        )
        db.add_all([group, subject, teacher1, teacher2, room, slot, period])
        db.commit()
        db.refresh(teacher1)
        db.refresh(teacher2)

        entry_own = ScheduleEntry(
            period_id=period.id,
            group_id=group.id,
            subject_id=subject.id,
            teacher_id=teacher1.id,
            room_id=room.id,
            time_slot_id=slot.id,
            week_type=WeekType.every,
            valid_from=period.valid_from,
            valid_to=period.valid_to,
        )
        entry_other = ScheduleEntry(
            period_id=period.id,
            group_id=group.id,
            subject_id=subject.id,
            teacher_id=teacher2.id,
            room_id=room.id,
            time_slot_id=slot.id,
            week_type=WeekType.odd,
            valid_from=period.valid_from,
            valid_to=period.valid_to,
        )
        db.add_all([entry_own, entry_other])
        db.commit()
        own_id = entry_own.id
        other_id = entry_other.id

        auth = AuthService(db)
        auth.create_user("t1@test.local", "pass", "T1", UserRole.teacher, teacher_id=teacher1.id)
        db.close()
        c.entry_own_id = own_id
        c.entry_other_id = other_id
        c.teacher_email = "t1@test.local"
        yield c
    app.dependency_overrides.clear()


def test_teacher_login_redirect(teacher_client):
    r = teacher_client.post(
        "/login",
        data={"email": teacher_client.teacher_email, "password": "pass"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/teacher/schedule" in r.headers["location"]


def test_teacher_cannot_edit_other_lesson(teacher_client):
    teacher_client.post(
        "/login",
        data={"email": teacher_client.teacher_email, "password": "pass"},
    )
    r = teacher_client.get(
        f"/teacher/entries/{teacher_client.entry_other_id}/edit",
        follow_redirects=False,
    )
    assert r.status_code == 303


def test_teacher_can_edit_own_lesson(teacher_client):
    teacher_client.post(
        "/login",
        data={"email": teacher_client.teacher_email, "password": "pass"},
    )
    r = teacher_client.get(f"/teacher/entries/{teacher_client.entry_own_id}/edit")
    assert r.status_code == 200
    assert "Редактировать" in r.text
