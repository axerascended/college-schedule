from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import UserRole
from app.templating import templates

router = APIRouter(tags=["home"])


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return templates.TemplateResponse(
            request,
            "home.html",
            {"user": None, "flash": request.session.pop("flash", [])},
        )
    if user.role == UserRole.admin:
        return RedirectResponse(url="/admin/schedule", status_code=303)
    if user.role == UserRole.student:
        return RedirectResponse(url="/student/schedule", status_code=303)
    return templates.TemplateResponse(
        request,
        "home.html",
        {"user": user, "flash": request.session.pop("flash", [])},
    )
