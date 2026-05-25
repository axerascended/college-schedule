import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.schedule_entry import WeekType
from app.models.user import User
from app.schemas.schedule import ScheduleEntryCreate, ScheduleEntryUpdate
from app.services.directory_service import DirectoryService
from app.services.schedule_service import ScheduleService, ScheduleServiceError
from app.services.schedule_view_service import ScheduleViewService
from app.templating import templates
from app.utils.http_params import parse_optional_int, schedule_cancel_url

router = APIRouter(prefix="/admin", tags=["admin-schedule"])


def _flash(request: Request, message: str, category: str = "success"):
    request.session.setdefault("flash", []).append((category, message))


def _schedule_redirect_url(base: str, group_id: int, period_id: int, request: Request) -> str:
    url = f"{base}/schedule?group_id={group_id}&period_id={period_id}"
    week_start = request.query_params.get("week_start")
    if week_start:
        url += f"&week_start={week_start}"
    return url


def _schedule_context(
    request: Request,
    user: User,
    db: Session,
    group_id: int | None,
    period_id: int | None,
    week_start: str | None,
    view_mode: str = "week",
):
    page = ScheduleViewService(db).build_schedule_page(
        group_id=group_id,
        period_id=period_id,
        week_start_param=week_start,
        view_mode=view_mode,
    )
    if page is None:
        return templates.TemplateResponse(
            request,
            "schedule/empty.html",
            {
                "user": user,
                "flash": request.session.pop("flash", []),
                "message": "Сначала создайте группы и период в справочниках.",
            },
        )

    return templates.TemplateResponse(
        request,
        "schedule/grid.html",
        {
            "user": user,
            "flash": request.session.pop("flash", []),
            "readonly": False,
            "teacher_mode": False,
            "current_teacher_id": None,
            "schedule_base": "/admin",
            "unpublished_warning": False,
            **page,
        },
    )


@router.get("/schedule")
def admin_schedule_grid(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    group_id: str | None = Query(None),
    period_id: str | None = Query(None),
    week_start: str | None = Query(None),
    view: str = Query("week"),
):
    if isinstance(user, RedirectResponse):
        return user
    return _schedule_context(
        request,
        user,
        db,
        parse_optional_int(group_id),
        parse_optional_int(period_id),
        week_start,
        view,
    )


@router.get("/entries")
def entries_list(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    schedule = ScheduleService(db)
    entries = []
    for period in schedule.list_periods():
        entries.extend(schedule.entries.list_for_period(period.id))
    return templates.TemplateResponse(
        request,
        "schedule/entries_list.html",
        {
            "user": user,
            "flash": request.session.pop("flash", []),
            "entries": entries,
            "schedule_base": "/admin",
            "teacher_mode": False,
            "current_teacher_id": None,
        },
    )


def _form_context(request, user, db, form: dict, errors: list | None = None):
    directory = DirectoryService(db)
    schedule = ScheduleService(db)
    groups = directory.list_groups()
    periods = schedule.list_periods()
    schedule_base = "/admin"
    return {
        "user": user,
        "flash": [],
        "title": "Редактировать занятие" if form.get("entry_id") else "Новое занятие",
        "form": form,
        "errors": errors or [],
        "periods": periods,
        "groups": groups,
        "subjects": directory.list_subjects(),
        "teachers": directory.list_teachers(),
        "rooms": directory.list_rooms(),
        "time_slots": directory.list_time_slots(),
        "week_types": list(WeekType),
        "teacher_mode": False,
        "schedule_base": schedule_base,
        "cancel_url": schedule_cancel_url(
            schedule_base,
            form.get("group_id"),
            form.get("period_id"),
            groups,
            periods,
            form.get("week_start_iso"),
        ),
    }


@router.get("/entries/new")
def entry_new(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    group_id: int | None = None,
    period_id: int | None = None,
    time_slot_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    directory = DirectoryService(db)
    periods = directory.list_periods()
    period = periods[0] if periods else None
    week_start_q = request.query_params.get("week_start")
    form = {
        "entry_id": None,
        "period_id": period_id or (period.id if period else None),
        "group_id": group_id,
        "subject_id": None,
        "teacher_id": None,
        "room_id": None,
        "time_slot_id": time_slot_id,
        "week_type": WeekType.every.value,
        "valid_from": period.valid_from.isoformat() if period else "",
        "valid_to": period.valid_to.isoformat() if period else "",
        "week_start_iso": week_start_q or "",
    }
    return templates.TemplateResponse(
        request, "schedule/form.html", _form_context(request, user, db, form)
    )


@router.get("/entries/{entry_id}/edit")
def entry_edit(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entry_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    entry = ScheduleService(db).get_entry(entry_id)
    if entry is None:
        return RedirectResponse("/admin/entries", status_code=303)
    form = {
        "entry_id": entry.id,
        "period_id": entry.period_id,
        "group_id": entry.group_id,
        "subject_id": entry.subject_id,
        "teacher_id": entry.teacher_id,
        "room_id": entry.room_id,
        "time_slot_id": entry.time_slot_id,
        "week_type": entry.week_type.value,
        "valid_from": entry.valid_from.isoformat(),
        "valid_to": entry.valid_to.isoformat(),
    }
    return templates.TemplateResponse(
        request, "schedule/form.html", _form_context(request, user, db, form)
    )


@router.post("/entries/new")
@router.post("/entries/{entry_id}/edit")
def entry_save(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entry_id: int | None = None,
    period_id: int = Form(...),
    group_id: int = Form(...),
    subject_id: int = Form(...),
    teacher_id: int = Form(...),
    room_id: int = Form(...),
    time_slot_id: int = Form(...),
    week_type: str = Form(...),
    valid_from: str = Form(...),
    valid_to: str = Form(...),
):
    if isinstance(user, RedirectResponse):
        return user
    form = {
        "entry_id": entry_id,
        "period_id": period_id,
        "group_id": group_id,
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "room_id": room_id,
        "time_slot_id": time_slot_id,
        "week_type": week_type,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }
    try:
        data = ScheduleEntryCreate(
            period_id=period_id,
            group_id=group_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            room_id=room_id,
            time_slot_id=time_slot_id,
            week_type=WeekType(week_type),
            valid_from=datetime.date.fromisoformat(valid_from),
            valid_to=datetime.date.fromisoformat(valid_to),
        )
        svc = ScheduleService(db)
        if entry_id:
            svc.update_entry(entry_id, ScheduleEntryUpdate(**data.model_dump()))
            _flash(request, "Занятие обновлено")
        else:
            svc.create_entry(data)
            _flash(request, "Занятие добавлено")
        return RedirectResponse(
            _schedule_redirect_url("/admin", group_id, period_id, request),
            status_code=303,
        )
    except (ScheduleServiceError, ValueError) as exc:
        errors = [str(exc)]
        if hasattr(exc, "conflicts"):
            errors = [c.message for c in exc.conflicts] or errors
        form["week_start_iso"] = request.query_params.get("week_start", "")
        ctx = _form_context(request, user, db, form, errors)
        return templates.TemplateResponse(request, "schedule/form.html", ctx, status_code=400)


@router.post("/entries/{entry_id}/delete")
def entry_delete(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entry_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    try:
        ScheduleService(db).delete_entry(entry_id)
        _flash(request, "Занятие удалено")
    except ScheduleServiceError as exc:
        _flash(request, str(exc), "danger")
    return RedirectResponse("/admin/entries", status_code=303)


@router.get("/periods")
def periods_list(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    periods = DirectoryService(db).list_periods()
    return templates.TemplateResponse(
        request,
        "admin/periods.html",
        {"user": user, "flash": request.session.pop("flash", []), "periods": periods},
    )


@router.get("/periods/new")
@router.get("/periods/{period_id}/edit")
def period_form(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    period_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    entity = DirectoryService(db).periods.get_by_id(period_id) if period_id else None
    return templates.TemplateResponse(
        request,
        "directories/form.html",
        {
            "user": user,
            "flash": [],
            "title": "Редактировать период" if entity else "Новый период",
            "form_fields": [
                {"name": "name", "label": "Название", "value": entity.name if entity else "Семестр 1", "required": True},
                {
                    "name": "valid_from",
                    "label": "С",
                    "type": "date",
                    "value": entity.valid_from.isoformat() if entity else "2025-09-01",
                    "required": True,
                },
                {
                    "name": "valid_to",
                    "label": "По",
                    "type": "date",
                    "value": entity.valid_to.isoformat() if entity else "2026-06-30",
                    "required": True,
                },
            ],
            "cancel_url": "/admin/periods",
        },
    )


@router.post("/periods/new")
@router.post("/periods/{period_id}/edit")
def period_save(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    name: str = Form(...),
    valid_from: str = Form(...),
    valid_to: str = Form(...),
    period_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).save_period(
        name,
        datetime.date.fromisoformat(valid_from),
        datetime.date.fromisoformat(valid_to),
        period_id,
    )
    _flash(request, "Период сохранён")
    return RedirectResponse("/admin/periods", status_code=303)


@router.post("/periods/{period_id}/publish")
def period_publish(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    period_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    ScheduleService(db).publish_period(period_id)
    _flash(request, "Расписание опубликовано для студентов")
    return RedirectResponse("/admin/periods", status_code=303)


@router.get("/users")
def users_list(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    from app.repositories.user_repository import UserRepository

    users = UserRepository(db).list_all()
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"user": user, "flash": request.session.pop("flash", []), "users": users},
    )


@router.get("/users/new")
def user_new_form(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    directory = DirectoryService(db)
    return templates.TemplateResponse(
        request,
        "admin/user_form.html",
        {
            "user": user,
            "flash": [],
            "groups": directory.list_groups(),
            "teachers": directory.list_teachers(),
        },
    )


@router.post("/users/new")
def user_create(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    group_id: str = Form(""),
    teacher_id: str = Form(""),
):
    if isinstance(user, RedirectResponse):
        return user
    from app.models.user import UserRole
    from app.services.auth_service import AuthService

    gid = int(group_id) if group_id and role == "student" else None
    tid = int(teacher_id) if teacher_id and role == "teacher" else None
    auth = AuthService(db)
    if role == "teacher" and tid and auth.users.get_by_teacher_id(tid):
        _flash(request, "У этого преподавателя уже есть аккаунт", "danger")
        return RedirectResponse("/admin/users/new", status_code=303)
    auth.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=UserRole(role),
        group_id=gid,
        teacher_id=tid,
    )
    _flash(request, "Пользователь создан")
    return RedirectResponse("/admin/users", status_code=303)
