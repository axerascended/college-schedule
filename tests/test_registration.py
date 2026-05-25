import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.group import Group
from app.services.auth_service import AuthRegistrationError, AuthService


@pytest.fixture
def client_with_group():
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
        group = Group(name="ИС-01", course="1")
        db.add(group)
        db.commit()
        db.refresh(group)
        c.test_group_id = group.id
        db.close()
        yield c
    app.dependency_overrides.clear()


def test_register_student_success(client_with_group):
    gid = client_with_group.test_group_id
    r = client_with_group.post(
        "/register",
        data={
            "email": "new@student.local",
            "password": "secret1",
            "password_confirm": "secret1",
            "full_name": "Новый Студент",
            "group_id": gid,
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/student/schedule"

    login_r = client_with_group.post(
        "/login",
        data={"email": "new@student.local", "password": "secret1"},
        follow_redirects=False,
    )
    assert login_r.status_code == 303
    assert "/student/schedule" in login_r.headers["location"]


def test_register_duplicate_email(client_with_group):
    gid = client_with_group.test_group_id
    data = {
        "email": "dup@student.local",
        "password": "secret1",
        "password_confirm": "secret1",
        "full_name": "Студент",
        "group_id": gid,
    }
    client_with_group.post("/register", data=data)
    r = client_with_group.post("/register", data=data)
    assert r.status_code == 400
    assert "уже зарегистрирован" in r.text


def test_register_password_mismatch(client_with_group):
    gid = client_with_group.test_group_id
    r = client_with_group.post(
        "/register",
        data={
            "email": "x@student.local",
            "password": "secret1",
            "password_confirm": "other",
            "full_name": "Студент",
            "group_id": gid,
        },
    )
    assert r.status_code == 400
    assert "не совпадают" in r.text


def test_register_student_service():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    group = Group(name="G-1", course="1")
    db.add(group)
    db.commit()
    db.refresh(group)
    auth = AuthService(db)
    group = auth.groups.list_all()[0]
    user = auth.register_student(
        "svc@test.local",
        "pass123",
        "pass123",
        "Тест",
        group.id,
    )
    assert user.role.value == "student"
    with pytest.raises(AuthRegistrationError):
        auth.register_student(
            "svc@test.local",
            "pass123",
            "pass123",
            "Тест",
            group.id,
        )
    db.close()
