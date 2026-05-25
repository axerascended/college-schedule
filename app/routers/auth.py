from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_login
from app.models.user import User, UserRole
from app.services.auth_service import AuthRegistrationError, AuthService
from app.services.directory_service import DirectoryService
from app.templating import templates

router = APIRouter(tags=["auth"])


@router.get("/api/auth/account-info")
def account_info(
    user: Annotated[User | RedirectResponse, Depends(require_login)],
):
    if isinstance(user, RedirectResponse):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return {
        "email": user.email,
        "fullName": user.full_name,
        "role": user.role.value,
    }


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return _redirect_for_role(user)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"user": None, "flash": _get_flash(request), "error": None},
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_account: str | None = Form(None),
    db: Session = Depends(get_db),
):
    auth = AuthService(db)
    user = auth.authenticate(email, password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "user": None,
                "flash": [],
                "error": "Неверный email или пароль",
            },
            status_code=400,
        )
    request.session["user_id"] = user.id
    if remember_account:
        request.session["pending_account_save"] = {
            "email": user.email,
            "fullName": user.full_name,
            "role": user.role.value,
        }
    return _redirect_for_role(user)


@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return _redirect_for_role(user)
    groups = DirectoryService(db).list_groups()
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {
            "user": None,
            "flash": _get_flash(request),
            "error": None,
            "errors": [],
            "groups": groups,
            "form": {},
        },
    )


@router.post("/register")
def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    full_name: str = Form(...),
    group_id: int = Form(...),
    db: Session = Depends(get_db),
):
    form = {
        "email": email,
        "full_name": full_name,
        "group_id": group_id,
    }
    groups = DirectoryService(db).list_groups()
    if not groups:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {
                "user": None,
                "flash": [],
                "error": None,
                "errors": ["Регистрация недоступна: в системе нет групп. Обратитесь к администратору."],
                "groups": groups,
                "form": form,
            },
            status_code=400,
        )
    try:
        user = AuthService(db).register_student(
            email=email,
            password=password,
            password_confirm=password_confirm,
            full_name=full_name,
            group_id=group_id,
        )
    except AuthRegistrationError as exc:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {
                "user": None,
                "flash": [],
                "error": None,
                "errors": [str(exc)],
                "groups": groups,
                "form": form,
            },
            status_code=400,
        )
    request.session["user_id"] = user.id
    request.session.setdefault("flash", []).append(
        ("success", "Регистрация успешна. Добро пожаловать!")
    )
    return RedirectResponse(url="/student/schedule", status_code=303)


@router.get("/register/teacher")
def register_teacher_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return _redirect_for_role(user)
    teachers = DirectoryService(db).list_teachers()
    return templates.TemplateResponse(
        request,
        "auth/register_teacher.html",
        {
            "user": None,
            "flash": _get_flash(request),
            "errors": [],
            "teachers": teachers,
            "form": {},
        },
    )


@router.post("/register/teacher")
def register_teacher_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    full_name: str = Form(...),
    teacher_id: int = Form(...),
    db: Session = Depends(get_db),
):
    form = {"email": email, "full_name": full_name, "teacher_id": teacher_id}
    teachers = DirectoryService(db).list_teachers()
    if not teachers:
        return templates.TemplateResponse(
            request,
            "auth/register_teacher.html",
            {
                "user": None,
                "flash": [],
                "errors": ["Нет преподавателей в справочнике. Обратитесь к администратору."],
                "teachers": teachers,
                "form": form,
            },
            status_code=400,
        )
    try:
        user = AuthService(db).register_teacher(
            email=email,
            password=password,
            password_confirm=password_confirm,
            full_name=full_name,
            teacher_id=teacher_id,
        )
    except AuthRegistrationError as exc:
        return templates.TemplateResponse(
            request,
            "auth/register_teacher.html",
            {
                "user": None,
                "flash": [],
                "errors": [str(exc)],
                "teachers": teachers,
                "form": form,
            },
            status_code=400,
        )
    request.session["user_id"] = user.id
    request.session.setdefault("flash", []).append(
        ("success", "Регистрация преподавателя успешна.")
    )
    return RedirectResponse(url="/teacher/schedule", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


def _redirect_for_role(user):
    if user.role == UserRole.admin:
        return RedirectResponse(url="/admin/schedule", status_code=303)
    if user.role == UserRole.student:
        return RedirectResponse(url="/student/schedule", status_code=303)
    if user.role == UserRole.teacher:
        return RedirectResponse(url="/teacher/schedule", status_code=303)
    return RedirectResponse(url="/", status_code=303)


def _get_flash(request: Request):
    flash = request.session.pop("flash", [])
    return flash
