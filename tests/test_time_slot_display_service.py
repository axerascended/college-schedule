import datetime

from app.services.time_slot_display_service import (
    build_pair_times_and_breaks,
    format_time_range,
)


class Slot:
    def __init__(self, day: int, pair: int, start: str, end: str):
        self.day_of_week = day
        self.pair_number = pair
        self.start_time = datetime.time.fromisoformat(start)
        self.end_time = datetime.time.fromisoformat(end)


def test_build_pair_times_and_breaks():
    slots = [
        Slot(0, 1, "08:30", "10:00"),
        Slot(1, 1, "08:30", "10:00"),
        Slot(0, 2, "10:15", "11:45"),
        Slot(1, 2, "10:15", "11:45"),
    ]
    pair_times, breaks = build_pair_times_and_breaks(slots)

    assert pair_times[1]["start"] == datetime.time(8, 30)
    assert pair_times[1]["end"] == datetime.time(10, 0)
    assert pair_times[2]["start"] == datetime.time(10, 15)
    assert breaks[1] == {
        "start": datetime.time(10, 0),
        "end": datetime.time(10, 15),
    }


def test_format_time_range():
    assert format_time_range(datetime.time(8, 30), datetime.time(10, 0)) == "08:30–10:00"
