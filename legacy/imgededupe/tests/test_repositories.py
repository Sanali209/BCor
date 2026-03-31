import pytest
from src.apps.experemental.imgededupe.core.repositories.bcor_file_repository import BcorFileRepository
from src.apps.experemental.imgededupe.core.database import DatabaseManager
from src.apps.experemental.imgededupe.core.models import FileAggregate
from src.apps.experemental.imgededupe.core.unit_of_work import SqliteUnitOfWork

@pytest.mark.asyncio
async def test_bcor_file_repository_save():
    """TDD for BCor FileRepository extension."""
    db = DatabaseManager(":memory:")
    uow = SqliteUnitOfWork(db)
    
    file_agg = FileAggregate(path="/tmp/test.jpg", phash="abc", size=1024)
    
    with uow:
        uow.files.add(file_agg)
        uow.commit()
        
    assert len(uow.files.seen) == 1
    # Verify legacy fallback/persistence if implemented
