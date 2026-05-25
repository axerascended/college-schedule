import datetime
from dataclasses import dataclass

from app.models.schedule_entry import ScheduleEntry, WeekType

DAY_NAMES = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота")

MONTH_NAMES = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)

MONTH_NAMES_NOM = (
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)

PARITY_LABELS = {
    WeekType.odd: "нечётная",
    WeekType.even: "чётная",
    WeekType.every: "каждую неделю",
}


@dataclass
class WeekOption:
    week_start: datetime.date
    week_end: datetime.date
    label: str
    month_key: str
    month_label: str
    parity: WeekType


def monday_of(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())


def saturday_of_week(week_start: datetime.date) -> datetime.date:
    return week_start + datetime.timedelta(days=5)


def week_type_for_date(d: datetime.date) -> WeekType:
    iso_week = d.isocalendar()[1]
    return WeekType.odd if iso_week % 2 else WeekType.even


def format_short_date(d: datetime.date) -> str:
    return f"{d.day} {MONTH_NAMES[d.month - 1]}"


def format_week_range(week_start: datetime.date, week_end: datetime.date) -> str:
    if week_start.month == week_end.month:
        return f"{week_start.day}–{week_end.day} {MONTH_NAMES[week_end.month - 1]} {week_end.year}"
    return (
        f"{week_start.day} {MONTH_NAMES[week_start.month - 1]} – "
        f"{week_end.day} {MONTH_NAMES[week_end.month - 1]} {week_end.year}"
    )


def entry_visible_in_week(
    entry: ScheduleEntry,
    week_start: datetime.date,
    week_end: datetime.date,
) -> bool:
    if entry.valid_from > week_end or entry.valid_to < week_start:
        return False
    if entry.week_type == WeekType.every:
        return True
    return entry.week_type == week_type_for_date(week_start)


def filter_entries_for_week(
    entries: list[ScheduleEntry],
    week_start: datetime.date,
) -> list[ScheduleEntry]:
    week_end = saturday_of_week(week_start)
    return [e for e in entries if entry_visible_in_week(e, week_start, week_end)]


def iter_weeks_in_period(
    period_start: datetime.date,
    period_end: datetime.date,
) -> list[WeekOption]:
    options: list[WeekOption] = []
    current = monday_of(period_start)
    last_monday = monday_of(period_end)
    seen: set[datetime.date] = set()

    while current <= last_monday:
        if current in seen:
            current += datetime.timedelta(days=7)
            continue
        seen.add(current)
        week_end = saturday_of_week(current)
        if week_end < period_start:
            current += datetime.timedelta(days=7)
            continue
        parity = week_type_for_date(current)
        options.append(
            WeekOption(
                week_start=current,
                week_end=week_end,
                label=format_week_range(current, week_end),
                month_key=f"{current.year}-{current.month:02d}",
                month_label=f"{MONTH_NAMES_NOM[current.month - 1]} {current.year}",
                parity=parity,
            )
        )
        current += datetime.timedelta(days=7)

    return options


def resolve_week_start(
    week_start_param: str | None,
    period_start: datetime.date,
    period_end: datetime.date,
) -> datetime.date:
    today_monday = monday_of(datetime.date.today())
    first_monday = monday_of(period_start)
    last_monday = monday_of(period_end)

    if week_start_param:
        try:
            parsed = datetime.date.fromisoformat(week_start_param)
            candidate = monday_of(parsed)
        except ValueError:
            candidate = today_monday
    else:
        candidate = today_monday

    if candidate < first_monday:
        return first_monday
    if candidate > last_monday:
        return last_monday
    return candidate


def day_dates_for_week(week_start: datetime.date) -> dict[int, datetime.date]:
    return {i: week_start + datetime.timedelta(days=i) for i in range(6)}


def group_weeks_by_month(week_options: list[WeekOption]) -> list[tuple[str, str, list[WeekOption]]]:
    groups: list[tuple[str, str, list[WeekOption]]] = []
    index: dict[str, list[WeekOption]] = {}
    order: list[str] = []
    for opt in week_options:
        if opt.month_key not in index:
            index[opt.month_key] = []
            order.append(opt.month_key)
        index[opt.month_key].append(opt)
    for key in order:
        first = index[key][0]
        groups.append((key, first.month_label, index[key]))
    return groups
