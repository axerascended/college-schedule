from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User, UserRole


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def require_login(
    request: Request,
    db: Session = Depends(get_db),
) -> User | RedirectResponse:
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return user


def require_admin(user: Annotated[User | RedirectResponse, Depends(require_login)]) -> User | RedirectResponse:
    if isinstance(user, RedirectResponse):
        return user
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён")
    return user


def require_teacher(
    request: Request,
    db: Session = Depends(get_db),
) -> User | RedirectResponse:
    user = require_login(request, db)
    if isinstance(user, RedirectResponse):
        return user
    if user.role != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён")
    user = (
        db.query(User)
        .options(joinedload(User.teacher))
        .filter(User.id == user.id)
        .first()
    )
    if user is None or user.teacher_id is None:
        return RedirectResponse(url="/login", status_code=303)
    return user
