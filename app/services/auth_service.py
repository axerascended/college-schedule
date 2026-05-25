from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.group_repository import GroupRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MIN_PASSWORD_LENGTH = 6


class AuthRegistrationError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.groups = GroupRepository(db)
        self.teachers = TeacherRepository(db)

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or not user.is_active:
            return None
        if not self.verify_password(password.strip(), user.password_hash):
            return None
        return user

    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
        group_id: int | None = None,
        teacher_id: int | None = None,
    ) -> User:
        user = User(
            email=email.strip().lower(),
            password_hash=self.hash_password(password),
            full_name=full_name,
            role=role,
            group_id=group_id,
            teacher_id=teacher_id,
        )
        return self.users.create(user)

    def register_student(
        self,
        email: str,
        password: str,
        password_confirm: str,
        full_name: str,
        group_id: int,
    ) -> User:
        email = email.strip().lower()
        full_name = full_name.strip()

        if not full_name:
            raise AuthRegistrationError("Укажите ФИО")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AuthRegistrationError(
                f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов"
            )
        if password != password_confirm:
            raise AuthRegistrationError("Пароли не совпадают")
        if self.users.get_by_email(email):
            raise AuthRegistrationError("Пользователь с таким email уже зарегистрирован")
        if self.groups.get_by_id(group_id) is None:
            raise AuthRegistrationError("Выберите группу из списка")

        return self.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.student,
            group_id=group_id,
        )

    def register_teacher(
        self,
        email: str,
        password: str,
        password_confirm: str,
        full_name: str,
        teacher_id: int,
    ) -> User:
        email = email.strip().lower()
        full_name = full_name.strip()

        if not full_name:
            raise AuthRegistrationError("Укажите ФИО")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AuthRegistrationError(
                f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов"
            )
        if password != password_confirm:
            raise AuthRegistrationError("Пароли не совпадают")
        if self.users.get_by_email(email):
            raise AuthRegistrationError("Пользователь с таким email уже зарегистрирован")

        teacher = self.teachers.get_by_id(teacher_id)
        if teacher is None:
            raise AuthRegistrationError("Выберите преподавателя из списка")
        if self.users.get_by_teacher_id(teacher_id):
            raise AuthRegistrationError(
                f"Для преподавателя «{teacher.full_name}» уже создан аккаунт"
            )

        return self.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.teacher,
            teacher_id=teacher_id,
        )
