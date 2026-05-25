from sqlalchemy.orm import Session

from app.models.time_slot import TimeSlot
from app.repositories.base_repository import BaseRepository


class TimeSlotRepository(BaseRepository[TimeSlot]):
    def __init__(self, db: Session):
        super().__init__(db, TimeSlot)

    def list_ordered(self) -> list[TimeSlot]:
        return (
            self.db.query(TimeSlot)
            .order_by(TimeSlot.day_of_week, TimeSlot.pair_number)
            .all()
        )
