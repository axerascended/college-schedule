from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_login
from app.models.user import User, UserRole
from app.repositories.schedule_repository import SchedulePeriodRepository
from app.services.schedule_view_service import ScheduleViewService
from app.templating import templates

router = APIRouter(prefix="/student", tags=["student"])


@router.get("/schedule")
def student_schedule(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_login)],
    db: Session = Depends(get_db),
    week_start: str | None = Query(None),
    view: str = Query("week"),
):
    if isinstance(user, RedirectResponse):
        return user
    if user.role != UserRole.student:
        return RedirectResponse("/", status_code=303)
    user = (
        db.query(User)
        .options(joinedload(User.group))
        .filter(User.id == user.id)
        .first()
    )
    if user.group_id is None:
        return templates.TemplateResponse(
            request,
            "schedule/empty.html",
            {
                "user": user,
                "flash": request.session.pop("flash", []),
                "message": "Ваш аккаунт не привязан к группе. Обратитесь к администратору.",
            },
        )

    published = SchedulePeriodRepository(db).get_published()
    if published is None:
        return templates.TemplateResponse(
            request,
            "schedule/empty.html",
            {
                "user": user,
                "flash": request.session.pop("flash", []),
                "message": "Расписание ещё не опубликовано администратором.",
            },
        )

    page = ScheduleViewService(db).build_schedule_page(
        group_id=user.group_id,
        period_id=published.id,
        week_start_param=week_start,
        view_mode=view,
    )

    return templates.TemplateResponse(
        request,
        "schedule/grid.html",
        {
            "user": user,
            "flash": request.session.pop("flash", []),
            "readonly": True,
            "teacher_mode": False,
            "current_teacher_id": None,
            "schedule_base": "",
            "groups": [],
            "periods": [],
            "unpublished_warning": False,
            **(page or {}),
        },
    )
