from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services.directory_service import DirectoryService
from app.templating import templates

router = APIRouter(prefix="/admin/directories", tags=["admin-directories"])


def _flash(request: Request, message: str, category: str = "success"):
    request.session.setdefault("flash", []).append((category, message))


@router.get("/groups")
def list_groups(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    svc = DirectoryService(db)
    return templates.TemplateResponse(
        request,
        "directories/groups.html",
        {"user": user, "flash": request.session.pop("flash", []), "active": "groups", "items": svc.list_groups()},
    )


@router.get("/groups/new")
@router.get("/groups/{entity_id}/edit")
def group_form(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    svc = DirectoryService(db)
    entity = svc.groups.get_by_id(entity_id) if entity_id else None
    return templates.TemplateResponse(
        request,
        "directories/form.html",
        {
            "user": user,
            "flash": [],
            "title": "Редактировать группу" if entity else "Новая группа",
            "form_fields": [
                {"name": "name", "label": "Название", "value": entity.name if entity else "", "required": True},
                {"name": "course", "label": "Курс", "value": entity.course if entity else "", "required": True},
            ],
            "cancel_url": "/admin/directories/groups",
        },
    )


@router.post("/groups/new")
@router.post("/groups/{entity_id}/edit")
def group_save(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    name: str = Form(...),
    course: str = Form(...),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).save_group(name, course, entity_id)
    _flash(request, "Группа сохранена")
    return RedirectResponse("/admin/directories/groups", status_code=303)


@router.post("/groups/{entity_id}/delete")
def group_delete(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).delete_group(entity_id)
    _flash(request, "Группа удалена")
    return RedirectResponse("/admin/directories/groups", status_code=303)


@router.get("/subjects")
def list_subjects(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    svc = DirectoryService(db)
    return templates.TemplateResponse(
        request,
        "directories/subjects.html",
        {
            "user": user,
            "flash": request.session.pop("flash", []),
            "active": "subjects",
            "items": svc.list_subjects(),
        },
    )


@router.get("/subjects/new")
@router.get("/subjects/{entity_id}/edit")
def subject_form(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    entity = DirectoryService(db).subjects.get_by_id(entity_id) if entity_id else None
    return templates.TemplateResponse(
        request,
        "directories/form.html",
        {
            "user": user,
            "flash": [],
            "title": "Редактировать предмет" if entity else "Новый предмет",
            "form_fields": [
                {"name": "name", "label": "Название", "value": entity.name if entity else "", "required": True},
            ],
            "cancel_url": "/admin/directories/subjects",
        },
    )


@router.post("/subjects/new")
@router.post("/subjects/{entity_id}/edit")
def subject_save(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    name: str = Form(...),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).save_subject(name, entity_id)
    _flash(request, "Предмет сохранён")
    return RedirectResponse("/admin/directories/subjects", status_code=303)


@router.post("/subjects/{entity_id}/delete")
def subject_delete(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).delete_subject(entity_id)
    _flash(request, "Предмет удалён")
    return RedirectResponse("/admin/directories/subjects", status_code=303)


@router.get("/teachers")
def list_teachers(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    svc = DirectoryService(db)
    return templates.TemplateResponse(
        request,
        "directories/teachers.html",
        {
            "user": user,
            "flash": request.session.pop("flash", []),
            "active": "teachers",
            "items": svc.list_teachers(),
        },
    )


@router.get("/teachers/new")
@router.get("/teachers/{entity_id}/edit")
def teacher_form(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    entity = DirectoryService(db).teachers.get_by_id(entity_id) if entity_id else None
    return templates.TemplateResponse(
        request,
        "directories/form.html",
        {
            "user": user,
            "flash": [],
            "title": "Редактировать преподавателя" if entity else "Новый преподаватель",
            "form_fields": [
                {"name": "full_name", "label": "ФИО", "value": entity.full_name if entity else "", "required": True},
            ],
            "cancel_url": "/admin/directories/teachers",
        },
    )


@router.post("/teachers/new")
@router.post("/teachers/{entity_id}/edit")
def teacher_save(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    full_name: str = Form(...),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).save_teacher(full_name, entity_id)
    _flash(request, "Преподаватель сохранён")
    return RedirectResponse("/admin/directories/teachers", status_code=303)


@router.post("/teachers/{entity_id}/delete")
def teacher_delete(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).delete_teacher(entity_id)
    _flash(request, "Преподаватель удалён")
    return RedirectResponse("/admin/directories/teachers", status_code=303)


@router.get("/rooms")
def list_rooms(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if isinstance(user, RedirectResponse):
        return user
    svc = DirectoryService(db)
    return templates.TemplateResponse(
        request,
        "directories/rooms.html",
        {"user": user, "flash": request.session.pop("flash", []), "active": "rooms", "items": svc.list_rooms()},
    )


@router.get("/rooms/new")
@router.get("/rooms/{entity_id}/edit")
def room_form(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    entity = DirectoryService(db).rooms.get_by_id(entity_id) if entity_id else None
    return templates.TemplateResponse(
        request,
        "directories/form.html",
        {
            "user": user,
            "flash": [],
            "title": "Редактировать аудиторию" if entity else "Новая аудитория",
            "form_fields": [
                {"name": "number", "label": "Номер", "value": entity.number if entity else "", "required": True},
                {
                    "name": "capacity",
                    "label": "Вместимость",
                    "type": "number",
                    "value": entity.capacity if entity else 30,
                    "required": True,
                },
            ],
            "cancel_url": "/admin/directories/rooms",
        },
    )


@router.post("/rooms/new")
@router.post("/rooms/{entity_id}/edit")
def room_save(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    number: str = Form(...),
    capacity: int = Form(...),
    entity_id: int | None = None,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).save_room(number, capacity, entity_id)
    _flash(request, "Аудитория сохранена")
    return RedirectResponse("/admin/directories/rooms", status_code=303)


@router.post("/rooms/{entity_id}/delete")
def room_delete(
    request: Request,
    user: Annotated[User | RedirectResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
    entity_id: int = 0,
):
    if isinstance(user, RedirectResponse):
        return user
    DirectoryService(db).delete_room(entity_id)
    _flash(request, "Аудитория удалена")
    return RedirectResponse("/admin/directories/rooms", status_code=303)
