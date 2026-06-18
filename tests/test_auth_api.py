import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.group import Group
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        db = TestingSession()
        group = Group(name="ИС-99", course="2")
        db.add(group)
        db.commit()
        auth = AuthService(db)
        auth.create_user("admin@test.local", "pass", "Admin", UserRole.admin)
        auth.create_user("student@test.local", "pass", "Student", UserRole.student, group.id)
        db.close()
        yield c
    app.dependency_overrides.clear()


def _login_admin(client: TestClient) -> None:
    client.post("/login", data={"email": "admin@test.local", "password": "pass"})


def test_login_redirect_admin(client):
    r = client.post("/login", data={"email": "admin@test.local", "password": "pass"}, follow_redirects=False)
    assert r.status_code == 303
    assert "/admin/schedule" in r.headers["location"]


def test_login_redirect_student(client):
    r = client.post("/login", data={"email": "student@test.local", "password": "pass"}, follow_redirects=False)
    assert r.status_code == 303
    assert "/student/schedule" in r.headers["location"]


def test_admin_schedule_requires_auth(client):
    r = client.get("/admin/schedule", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_admin_users_list_has_edit_and_delete(client):
    _login_admin(client)
    r = client.get("/admin/users")
    assert r.status_code == 200
    assert "Изменить" in r.text
    assert "Удалить" in r.text


def test_admin_user_edit_updates_student(client):
    _login_admin(client)
    db = next(app.dependency_overrides[get_db]())
    student = UserRepository(db).get_by_email("student@test.local")
    assert student is not None
    student_id = student.id
    group_id = student.group_id
    db.close()

    r = client.post(
        f"/admin/users/{student_id}/edit",
        data={
            "email": "student-new@test.local",
            "password": "",
            "full_name": "Student Updated",
            "role": "student",
            "group_id": str(group_id),
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/users"

    verify_db = next(app.dependency_overrides[get_db]())
    updated = UserRepository(verify_db).get_by_id(student_id)
    assert updated.email == "student-new@test.local"
    assert updated.full_name == "Student Updated"
    verify_db.close()


def test_admin_user_delete_student(client):
    _login_admin(client)
    db = next(app.dependency_overrides[get_db]())
    student = UserRepository(db).get_by_email("student@test.local")
    assert student is not None
    student_id = student.id
    db.close()

    r = client.post(f"/admin/users/{student_id}/delete", follow_redirects=False)
    assert r.status_code == 303

    verify_db = next(app.dependency_overrides[get_db]())
    assert UserRepository(verify_db).get_by_id(student_id) is None
    verify_db.close()


def test_admin_cannot_delete_self(client):
    _login_admin(client)
    db = next(app.dependency_overrides[get_db]())
    admin = UserRepository(db).get_by_email("admin@test.local")
    assert admin is not None
    admin_id = admin.id
    db.close()

    r = client.post(f"/admin/users/{admin_id}/delete", follow_redirects=False)
    assert r.status_code == 303

    verify_db = next(app.dependency_overrides[get_db]())
    assert UserRepository(verify_db).get_by_id(admin_id) is not None
    verify_db.close()
