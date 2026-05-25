from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models.schedule_entry import WeekType
from app.services.schedule_conflict_service import DAY_NAMES
from app.services.time_slot_display_service import format_time, format_time_range

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

templates.env.globals["college_name"] = settings.college_name
templates.env.globals["DAY_NAMES"] = DAY_NAMES
templates.env.globals["format_time"] = format_time
templates.env.globals["format_time_range"] = format_time_range
templates.env.globals["WeekType"] = WeekType

WEEK_TYPE_LABELS = {
    WeekType.every: "Каждую неделю",
    WeekType.odd: "Нечётная",
    WeekType.even: "Чётная",
}
templates.env.globals["WEEK_TYPE_LABELS"] = WEEK_TYPE_LABELS


def resolve_nav_section(path: str) -> str | None:
    """Ключ активного пункта главного меню по URL."""
    if path.startswith("/admin/directories"):
        return "directories"
    if path.startswith("/admin/schedule") or path.startswith("/admin/entries"):
        return "schedule"
    if path.startswith("/admin/periods"):
        return "periods"
    if path.startswith("/admin/users"):
        return "users"
    if path.startswith("/student/schedule"):
        return "student_schedule"
    if path.startswith("/teacher/entries"):
        return "teacher_entries"
    if path.startswith("/teacher/"):
        return "teacher_schedule"
    if path in ("/login", "/register"):
        return "login"
    return None


templates.env.globals["resolve_nav_section"] = resolve_nav_section
