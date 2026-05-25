"""Создать администратора: python -m app.scripts.create_admin"""

import getpass
import sys

from app.database import SessionLocal
from app.models.user import UserRole
from app.services.auth_service import AuthService


def main() -> None:
    email = input("Email: ").strip()
    if not email:
        print("Email обязателен")
        sys.exit(1)
    password = getpass.getpass("Пароль: ")
    full_name = input("ФИО: ").strip() or "Администратор"

    db = SessionLocal()
    try:
        auth = AuthService(db)
        if auth.users.get_by_email(email):
            print("Пользователь с таким email уже существует")
            sys.exit(1)
        auth.create_user(email, password, full_name, UserRole.admin)
        print(f"Администратор {email} создан")
    finally:
        db.close()


if __name__ == "__main__":
    main()
