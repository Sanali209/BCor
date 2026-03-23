from typing import List, Set
from src.core.unit_of_work import AbstractUnitOfWork
from src.core.domain import Aggregate
from .database import DatabaseManager
from .repositories.bcor_file_repository import BcorFileRepository
from .repositories.bcor_cluster_repository import BcorClusterRepository

class SqliteUnitOfWork(AbstractUnitOfWork):
    """
    BCor UnitOfWork implementation for SQLite.
    Bridges the BCor UoW interface to the legacy DatabaseManager.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.files = BcorFileRepository(db_manager)
        self.clusters = BcorClusterRepository(db_manager)

    def _commit(self) -> None:
        if self.db_manager.conn:
            self.db_manager.conn.commit()

    def rollback(self) -> None:
        if self.db_manager.conn:
            self.db_manager.conn.rollback()

    def _get_all_seen_aggregates(self) -> List[Aggregate]:
        # Collect from all repositories
        return list(self.files.seen) + list(self.clusters.seen)
