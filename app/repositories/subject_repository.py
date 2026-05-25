from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.repositories.base_repository import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: Session):
        super().__init__(db, Subject)
