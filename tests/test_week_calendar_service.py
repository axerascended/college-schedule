import datetime

from app.models.schedule_entry import WeekType
from app.services.week_calendar_service import (
    entry_visible_in_week,
    filter_entries_for_week,
    iter_weeks_in_period,
    monday_of,
    resolve_week_start,
    week_type_for_date,
)


def test_resolve_week_start_clamps_to_period():
    start = datetime.date(2025, 9, 1)
    end = datetime.date(2025, 9, 30)
    far = resolve_week_start("2020-01-01", start, end)
    assert far == monday_of(start)
    late = resolve_week_start("2030-01-01", start, end)
    assert late == monday_of(end)


def test_iter_weeks_in_period():
    start = datetime.date(2025, 9, 1)
    end = datetime.date(2025, 10, 15)
    weeks = iter_weeks_in_period(start, end)
    assert len(weeks) >= 6
    assert weeks[0].week_start.weekday() == 0


def test_entry_visible_odd_even():
    week_start = datetime.date(2025, 9, 8)
    week_end = datetime.date(2025, 9, 13)

    class Entry:
        def __init__(self, wt, vf, vt):
            self.week_type = wt
            self.valid_from = vf
            self.valid_to = vt

    parity = week_type_for_date(week_start)
    matching = Entry(parity, week_start, week_end)
    opposite = Entry(
        WeekType.even if parity == WeekType.odd else WeekType.odd,
        week_start,
        week_end,
    )
    every = Entry(WeekType.every, week_start, week_end)

    assert entry_visible_in_week(matching, week_start, week_end)
    assert not entry_visible_in_week(opposite, week_start, week_end)
    assert entry_visible_in_week(every, week_start, week_end)
