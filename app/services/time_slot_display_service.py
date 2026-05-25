import datetime


def build_pair_times_and_breaks(
    slots: list,
) -> tuple[dict[int, dict[str, datetime.time]], dict[int, dict[str, datetime.time]]]:
    """Время пар (одинаково по дням) и перемены после номера пары."""
    pair_times: dict[int, dict[str, datetime.time]] = {}
    for slot in slots:
        if slot.pair_number not in pair_times:
            pair_times[slot.pair_number] = {
                "start": slot.start_time,
                "end": slot.end_time,
            }

    breaks_after: dict[int, dict[str, datetime.time]] = {}
    sorted_pairs = sorted(pair_times.keys())
    for idx in range(len(sorted_pairs) - 1):
        current = sorted_pairs[idx]
        nxt = sorted_pairs[idx + 1]
        break_start = pair_times[current]["end"]
        break_end = pair_times[nxt]["start"]
        if break_start < break_end:
            breaks_after[current] = {"start": break_start, "end": break_end}

    return pair_times, breaks_after


def format_time(t: datetime.time) -> str:
    return t.strftime("%H:%M")


def format_time_range(start: datetime.time, end: datetime.time) -> str:
    return f"{format_time(start)}–{format_time(end)}"
