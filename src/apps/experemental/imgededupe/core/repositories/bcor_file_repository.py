from typing import Optional, List
from src.core.repository import AbstractRepository
from src.apps.experemental.imgededupe.core.models import FileAggregate
from src.apps.experemental.imgededupe.core.database import DatabaseManager

class BcorFileRepository(AbstractRepository):
    """
    BCor-native Repository for File entities.
    Extends AbstractRepository to support aggregate tracking and domain events.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager

    def save(self, file_aggregate: FileAggregate) -> None:
        """Saves a file aggregate and tracks it."""
        self.db.upsert_file(
            path=file_aggregate.path,
            phash=file_aggregate.phash,
            size=file_aggregate.size or file_aggregate.file_size,
            width=file_aggregate.width,
            height=file_aggregate.height,
            mtime=file_aggregate.last_modified
        )
        self.seen.add(file_aggregate)

    def get_by_path(self, path: str):
        """Retrieves a file by path."""
        return None # TODO: Implement lazy loading into aggregate
