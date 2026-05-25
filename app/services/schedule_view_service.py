import datetime

from sqlalchemy.orm import Session

from app.services.directory_service import DirectoryService
from app.services.schedule_conflict_service import ScheduleConflictService
from app.services.schedule_service import ScheduleService
from app.services.time_slot_display_service import build_pair_times_and_breaks
from app.services.week_calendar_service import (
    PARITY_LABELS,
    day_dates_for_week,
    filter_entries_for_week,
    format_week_range,
    group_weeks_by_month,
    iter_weeks_in_period,
    monday_of,
    resolve_week_start,
    saturday_of_week,
    week_type_for_date,
)


class ScheduleViewService:
    def __init__(self, db: Session):
        self.db = db
        self.directory = DirectoryService(db)
        self.schedule = ScheduleService(db)

    def build_schedule_page(
        self,
        *,
        group_id: int | None,
        period_id: int | None,
        week_start_param: str | None,
        view_mode: str = "week",
    ) -> dict | None:
        """Контекст для grid.html или None, если нет групп/периодов."""
        groups = self.directory.list_groups()
        periods = self.schedule.list_periods()
        if not groups or not periods:
            return None

        group = self.directory.groups.get_by_id(group_id or groups[0].id)
        period = self.schedule.get_period(period_id or periods[0].id)
        if group is None or period is None:
            return None

        week_start = resolve_week_start(
            week_start_param, period.valid_from, period.valid_to
        )
        week_end = saturday_of_week(week_start)
        parity = week_type_for_date(week_start)

        all_entries = self.schedule.entries.list_for_group(group.id, period.id)
        entries = filter_entries_for_week(all_entries, week_start)

        slots = self.schedule.time_slots.list_ordered()
        grid = ScheduleConflictService.build_grid(entries, slots, week_filter=None)
        pairs = sorted({s.pair_number for s in slots})
        days = sorted({s.day_of_week for s in slots})
        slot_map = {(s.day_of_week, s.pair_number): s for s in slots}
        pair_times, breaks_after_pair = build_pair_times_and_breaks(slots)
        day_dates = day_dates_for_week(week_start)

        today = datetime.date.today()
        today_dow = today.weekday()
        if today_dow > 5:
            today_dow = 0

        week_options = iter_weeks_in_period(period.valid_from, period.valid_to)
        week_groups = group_weeks_by_month(week_options)

        prev_week = week_start - datetime.timedelta(days=7)
        next_week = week_start + datetime.timedelta(days=7)
        first_monday = monday_of(period.valid_from)
        last_monday = monday_of(period.valid_to)
        is_current_week = week_start <= today <= week_end
        today_outside_selected_week = view_mode == "today" and not is_current_week

        if view_mode == "today" and is_current_week:
            days = [today_dow]

        return {
            "group": group,
            "groups": groups,
            "period": period,
            "periods": periods,
            "grid": grid,
            "pairs": pairs,
            "days": days,
            "slot_map": slot_map,
            "pair_times": pair_times,
            "breaks_after_pair": breaks_after_pair,
            "day_dates": day_dates,
            "week_start": week_start,
            "week_end": week_end,
            "week_start_iso": week_start.isoformat(),
            "week_label": format_week_range(week_start, week_end),
            "week_parity": parity,
            "week_parity_label": PARITY_LABELS[parity],
            "week_options": week_options,
            "week_groups": week_groups,
            "prev_week_iso": prev_week.isoformat(),
            "next_week_iso": next_week.isoformat(),
            "can_prev_week": week_start > first_monday,
            "can_next_week": week_start < last_monday,
            "is_current_week": is_current_week,
            "today": today,
            "today_dow": today_dow if is_current_week else -1,
            "view_mode": view_mode,
            "week_filter": parity,
            "today_outside_selected_week": today_outside_selected_week,
            "today_monday_iso": monday_of(today).isoformat(),
        }
