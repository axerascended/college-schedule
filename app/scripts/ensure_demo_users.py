"""Добавить демо-пользователей, если их нет: python -m app.scripts.ensure_demo_users"""

from app.database import SessionLocal
from app.models.user import UserRole
from app.repositories.group_repository import GroupRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.auth_service import AuthService


def main() -> None:
    db = SessionLocal()
    try:
        auth = AuthService(db)
        groups = GroupRepository(db).list_all()
        teachers = TeacherRepository(db).list_all()
        if not groups or not teachers:
            print("Need groups and teachers. Run: py -3 -m app.scripts.seed")
            return
        demos = [
            ("admin@college.local", "admin123", "Administrator", UserRole.admin, None, None),
            ("student@college.local", "student123", "Student", UserRole.student, groups[0].id, None),
            ("teacher@college.local", "teacher123", "Ivanov", UserRole.teacher, None, teachers[0].id),
        ]
        created = []
        for email, pwd, name, role, gid, tid in demos:
            if not auth.users.get_by_email(email):
                auth.create_user(email, pwd, name, role, group_id=gid, teacher_id=tid)
                created.append(email)
        if created:
            print("Created:", ", ".join(created))
        else:
            print("All demo accounts already exist.")
        print("admin@college.local / admin123")
        print("student@college.local / student123")
        print("teacher@college.local / teacher123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
