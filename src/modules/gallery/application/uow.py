from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session, sessionmaker

from src.core.unit_of_work import AbstractUnitOfWork
from ..infrastructure.repositories import SqlImageRepository, SqlCategoryRepository, SqlRelationRepository
from ..infrastructure.models import start_mappers


class GalleryUnitOfWork(AbstractUnitOfWork):
    """Unit of Work for the Gallery module."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self.session_factory = session_factory
        self.session: Session = None
        # Repositories
        self.images: SqlImageRepository = None
        self.categories: SqlCategoryRepository = None
        self.relations: SqlRelationRepository = None

    async def __aenter__(self) -> GalleryUnitOfWork:
        self.session = self.session_factory()
        self.images = SqlImageRepository(self.session)
        self.categories = SqlCategoryRepository(self.session)
        self.relations = SqlRelationRepository(self.session)
        return await super().__aenter__()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self.session.close()

    def _commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
