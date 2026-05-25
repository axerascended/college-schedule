from sqlalchemy.orm import Session

from app.models.room import Room
from app.repositories.base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, db: Session):
        super().__init__(db, Room)
