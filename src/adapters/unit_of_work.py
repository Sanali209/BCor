from typing import Callable, Type
from sqlalchemy.orm import Session
from src.core.unit_of_work import AbstractUnitOfWork
from src.adapters.repository import SqlAlchemyRepository
from src.core.domain import Aggregate


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Concrete UnitOfWork implementation using SQLAlchemy.

    Manages the lifecycle of a SQLAlchemy session and ensures that
    changes are committed or rolled back atomically.

    Attributes:
        session_factory: A callable that returns a new SQLAlchemy session.
        model_class: The aggregate class that the internal repository manages.
        session: The active SQLAlchemy session (available after __enter__).
        repository: The repository instance associated with the session.
    """

    def __init__(
        self, session_factory: Callable[[], Session], model_class: Type[Aggregate]
    ):
        """Initializes the Unit of Work with a session factory.

        Args:
            session_factory: Callable yielding a SQLAlchemy session.
            model_class: The domain model class for the default repository.
        """
        self.session_factory = session_factory
        self.model_class = model_class

    def __enter__(self):
        """Starts a session and initializes the repository."""
        self.session = self.session_factory()
        self.repository = SqlAlchemyRepository(self.session, self.model_class)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the session after rolling back if necessary."""
        super().__exit__(exc_type, exc_val, exc_tb)
        self.session.close()

    def _commit(self):
        """Commits the SQLAlchemy session."""
        self.session.commit()

    def rollback(self):
        """Rolls back the SQLAlchemy session."""
        self.session.rollback()
