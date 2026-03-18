from typing import Optional, Type, TypeVar
from sqlalchemy.orm import Session
from src.core.domain import Aggregate
from src.core.repository import AbstractRepository

T = TypeVar("T", bound=Aggregate)


class SqlAlchemyRepository(AbstractRepository[T]):
    """Concrete implementation of AbstractRepository using SQLAlchemy.

    This repository uses an active SQLAlchemy session to persist and
    retrieve domain aggregates.

    Attributes:
        session: The active SQLAlchemy Session.
        model_class: The SQLAlchemy mapped class for the aggregate.
    """

    def __init__(self, session: Session, model_class: Type[T]) -> None:
        """Initializes the repository with a session and model class.

        Args:
            session: The SQLAlchemy session to use for DB operations.
            model_class: The domain aggregate class to manage.
        """
        super().__init__()
        self.session = session
        self.model_class = model_class

    def _add(self, aggregate: T) -> None:
        """Adds an aggregate to the SQLAlchemy session.

        Args:
            aggregate: The aggregate instance to persist.
        """
        self.session.add(aggregate)

    def _get(self, reference: str) -> Optional[T]:
        """Retrieves an aggregate by reference from the database.

        Attempts to fetch by primary key first, then falls back to 
        filtering by a `ref` column.

        Args:
            reference: The unique reference or ID of the aggregate.

        Returns:
            The aggregate instance if found, otherwise None.
        """
        instance = self.session.get(self.model_class, reference)

        if instance is None:
            instance = (
                self.session.query(self.model_class).filter_by(ref=reference).first()
            )

        return instance
