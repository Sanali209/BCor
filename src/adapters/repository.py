from typing import Optional, Type, TypeVar
from sqlalchemy.orm import Session
from src.core.domain import Aggregate
from src.core.repository import AbstractRepository

T = TypeVar("T", bound=Aggregate)


class SqlAlchemyRepository(AbstractRepository[T]):
    """
    Concrete implementation of AbstractRepository using SQLAlchemy.
    Saves and loads Aggregates through an active ORM session.
    """

    def __init__(self, session: Session, model_class: Type[T]) -> None:
        super().__init__()
        self.session = session
        self.model_class = model_class

    def _add(self, aggregate: T) -> None:
        self.session.add(aggregate)

    def _get(self, reference: str) -> Optional[T]:
        # Assumes the primary key or unique identifier mapped field is Named `ref` or similar.
        # Typically in DDD it's `id` or `reference`.
        # For simplicity, using SQLAlchemy's get assuming it resolves the primary key.
        # But for DDD reference fields it's often a custom column.

        # Here we assume the FakeAggregate uses `ref`. For real usage we might need
        # to filter by `id` or `ref` explicitly.
        # As a generalized mapper we rely on sqlalchemy's session.get if it's the PK:
        instance = self.session.get(self.model_class, reference)

        if instance is None:
            # Fallback if the primary key isn't the reference
            instance = (
                self.session.query(self.model_class).filter_by(ref=reference).first()
            )

        return instance
