import sqlite3
from typing import Any

from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.experemental.boruscraper.infrastructure.repositories import SqliteProjectRepository, SqlitePostRepository
from src.apps.experemental.boruscraper.common.database import DatabaseManager


class SqliteUnitOfWork(AbstractUnitOfWork):
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
        self.connection = None

    def __enter__(self) -> "SqliteUnitOfWork":
        # we bypass db_manager._get_connection() as it's not maintaining state,
        # but we use its path to create our own transaction-bound connection
        self.connection = sqlite3.connect(self._db_manager.db_path)
        self.projects = SqliteProjectRepository(self.connection)
        self.posts = SqlitePostRepository(self.connection)
        return super().__enter__()

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.connection.close()

    async def __aenter__(self) -> "SqliteUnitOfWork":
        self.connection = sqlite3.connect(self._db_manager.db_path)
        self.projects = SqliteProjectRepository(self.connection)
        self.posts = SqlitePostRepository(self.connection)
        return await super().__aenter__()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self.connection.close()

    def _commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()
