import datetime

import pytest

from app.models.schedule_entry import ScheduleEntry, WeekType
from app.schemas.schedule import ScheduleEntryCreate
from app.services.schedule_conflict_service import (
    ScheduleConflictService,
    dates_overlap,
    week_types_overlap,
)
from app.services.schedule_service import ScheduleService, ScheduleServiceError


def test_week_types_overlap():
    assert week_types_overlap(WeekType.every, WeekType.odd)
    assert week_types_overlap(WeekType.odd, WeekType.odd)
    assert not week_types_overlap(WeekType.odd, WeekType.even)


def test_dates_overlap():
    assert dates_overlap(
        datetime.date(2025, 9, 1),
        datetime.date(2025, 12, 31),
        datetime.date(2025, 10, 1),
        datetime.date(2026, 1, 1),
    )
    assert not dates_overlap(
        datetime.date(2025, 1, 1),
        datetime.date(2025, 6, 1),
        datetime.date(2025, 7, 1),
        datetime.date(2025, 12, 1),
    )


def test_group_conflict(db_session, sample_data):
    d = sample_data
    entry = ScheduleEntry(
        period_id=d["period"].id,
        group_id=d["group"].id,
        subject_id=d["subject"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    db_session.add(entry)
    db_session.commit()

    conflicts = ScheduleConflictService(db_session).check(
        group_id=d["group"].id,
        teacher_id=d["teacher2"].id,
        room_id=d["room2"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    assert any(c.conflict_type == "group" for c in conflicts)


def test_teacher_conflict(db_session, sample_data):
    d = sample_data
    entry = ScheduleEntry(
        period_id=d["period"].id,
        group_id=d["group"].id,
        subject_id=d["subject"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    db_session.add(entry)
    db_session.commit()

    conflicts = ScheduleConflictService(db_session).check(
        group_id=d["group2"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room2"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    assert any(c.conflict_type == "teacher" for c in conflicts)


def test_room_conflict(db_session, sample_data):
    d = sample_data
    entry = ScheduleEntry(
        period_id=d["period"].id,
        group_id=d["group"].id,
        subject_id=d["subject"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    db_session.add(entry)
    db_session.commit()

    conflicts = ScheduleConflictService(db_session).check(
        group_id=d["group2"].id,
        teacher_id=d["teacher2"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    assert any(c.conflict_type == "room" for c in conflicts)


def test_no_conflict_different_week_type(db_session, sample_data):
    d = sample_data
    entry = ScheduleEntry(
        period_id=d["period"].id,
        group_id=d["group"].id,
        subject_id=d["subject"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.odd,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    db_session.add(entry)
    db_session.commit()

    conflicts = ScheduleConflictService(db_session).check(
        group_id=d["group"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.even,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    assert conflicts == []


def test_no_conflict_different_slot(db_session, sample_data):
    d = sample_data
    entry = ScheduleEntry(
        period_id=d["period"].id,
        group_id=d["group"].id,
        subject_id=d["subject"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    db_session.add(entry)
    db_session.commit()

    conflicts = ScheduleConflictService(db_session).check(
        group_id=d["group"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot2"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    assert conflicts == []


def test_schedule_service_raises_on_conflict(db_session, sample_data):
    d = sample_data
    svc = ScheduleService(db_session)
    data = ScheduleEntryCreate(
        period_id=d["period"].id,
        group_id=d["group"].id,
        subject_id=d["subject"].id,
        teacher_id=d["teacher"].id,
        room_id=d["room"].id,
        time_slot_id=d["slot"].id,
        week_type=WeekType.every,
        valid_from=d["period"].valid_from,
        valid_to=d["period"].valid_to,
    )
    svc.create_entry(data)
    with pytest.raises(ScheduleServiceError) as exc_info:
        svc.create_entry(data)
    assert exc_info.value.conflicts
