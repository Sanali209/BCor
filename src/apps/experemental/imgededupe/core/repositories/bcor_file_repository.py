from typing import Optional, List
from src.core.repository import AbstractRepository
from src.apps.experemental.imgededupe.core.models import FileAggregate
from src.apps.experemental.imgededupe.core.database import DatabaseManager

class BcorFileRepository(AbstractRepository[FileAggregate]):
    """
    BCor-native Repository for File entities.
    Extends AbstractRepository to support aggregate tracking and domain events.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager

    def _add(self, file_aggregate: FileAggregate) -> None:
        """Saves a file aggregate and tracks it."""
        self.db.upsert_file(
            path=file_aggregate.path,
            phash=file_aggregate.phash,
            size=file_aggregate.size or file_aggregate.file_size,
            width=file_aggregate.width,
            height=file_aggregate.height,
            mtime=file_aggregate.last_modified
        )

    def _get(self, path: str) -> Optional[FileAggregate]:
        """Retrieves a file by path."""
        row = self.db.get_file_by_path(path)
        if not row:
            return None
        
        # Bridge legacy row to BCor aggregate
        return FileAggregate(
            path=row['path'],
            id=row['id'],
            phash=row['phash'],
            file_size=row['file_size'],
            size=row['file_size'],
            width=row['width'],
            height=row['height'],
            last_modified=row['last_modified']
        )
