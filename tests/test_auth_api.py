import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.group import Group
from app.models.user import UserRole
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
