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


class AuthUserAdminError(Exception):
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

    def update_user(
        self,
        user_id: int,
        email: str,
        full_name: str,
        role: UserRole,
        group_id: int | None = None,
        teacher_id: int | None = None,
        password: str | None = None,
    ) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise AuthUserAdminError("Пользователь не найден")

        email = email.strip().lower()
        full_name = full_name.strip()
        if not full_name:
            raise AuthUserAdminError("Укажите ФИО")

        existing = self.users.get_by_email(email)
        if existing is not None and existing.id != user_id:
            raise AuthUserAdminError("Пользователь с таким email уже существует")

        if password is not None and password.strip():
            if len(password.strip()) < MIN_PASSWORD_LENGTH:
                raise AuthUserAdminError(
                    f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов"
                )
            user.password_hash = self.hash_password(password.strip())

        if role == UserRole.student:
            if group_id is None or self.groups.get_by_id(group_id) is None:
                raise AuthUserAdminError("Выберите группу для студента")
            user.group_id = group_id
            user.teacher_id = None
        elif role == UserRole.teacher:
            if teacher_id is None:
                raise AuthUserAdminError("Выберите преподавателя")
            teacher = self.teachers.get_by_id(teacher_id)
            if teacher is None:
                raise AuthUserAdminError("Выберите преподавателя из списка")
            linked = self.users.get_by_teacher_id(teacher_id)
            if linked is not None and linked.id != user_id:
                raise AuthUserAdminError(f"У преподавателя «{teacher.full_name}» уже есть аккаунт")
            user.teacher_id = teacher_id
            user.group_id = None
        else:
            user.group_id = None
            user.teacher_id = None

        user.email = email
        user.full_name = full_name
        user.role = role
        return self.users.update(user)

    def delete_user(self, user_id: int, acting_user_id: int) -> None:
        if user_id == acting_user_id:
            raise AuthUserAdminError("Нельзя удалить свой аккаунт")

        user = self.users.get_by_id(user_id)
        if user is None:
            raise AuthUserAdminError("Пользователь не найден")

        if user.role == UserRole.admin:
            admins = [u for u in self.users.list_all() if u.role == UserRole.admin and u.is_active]
            if len(admins) <= 1:
                raise AuthUserAdminError("Нельзя удалить последнего администратора")

        self.users.delete(user)
