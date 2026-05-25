from sqlalchemy.orm import Session

from app.models.group import Group
from app.repositories.base_repository import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, db: Session):
        super().__init__(db, Group)
