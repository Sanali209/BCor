from typing import Callable, Type
from sqlalchemy.orm import Session
from src.core.unit_of_work import AbstractUnitOfWork
from src.adapters.repository import SqlAlchemyRepository
from src.core.domain import Aggregate


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Concrete UnitOfWork using SQLAlchemy.
    Manages the lifecycle of the SQLAlchemy Session and corresponding Repository.
    """

    def __init__(
        self, session_factory: Callable[[], Session], model_class: Type[Aggregate]
    ):
        self.session_factory = session_factory
        self.model_class = model_class

    def __enter__(self):
        self.session = self.session_factory()
        self.repository = SqlAlchemyRepository(self.session, self.model_class)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self.session.close()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
