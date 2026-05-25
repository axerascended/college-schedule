from sqlalchemy.orm import Session

from app.models.teacher import Teacher
from app.repositories.base_repository import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: Session):
        super().__init__(db, Teacher)
