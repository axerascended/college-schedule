from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get_by_id(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list_all(self) -> list[ModelT]:
        return self.db.query(self.model).order_by(self.model.id).all()

    def create(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.commit()
