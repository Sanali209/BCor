import pytest
import asyncio
import os
import sqlite3
from src.common.paths import PathNormalizer
from src.core.loop_policies import WindowsLoopManager
from src.common.asyncio_utils import TaskThrottler
from src.common.database.sqlite_utils import SqliteRepositoryBase

# --- PathNormalizer Tests ---
@pytest.mark.asyncio
async def test_path_normalizer_norm():
    p = "relative/path/../path"
    normalized = PathNormalizer.norm(p)
    assert os.path.isabs(normalized)
    assert ".." not in normalized

@pytest.mark.asyncio
async def test_path_normalizer_decorator():
    class TestObj:
        @PathNormalizer.normalize_args("path_arg", "list_arg")
        def method(self, path_arg, list_arg, other_arg):
            return path_arg, list_arg, other_arg

    obj = TestObj()
    p1, p2, p3 = obj.method("test/path", ["a/b", "c/d"], "not_a_path")
    
    assert os.path.isabs(p1)
    assert isinstance(p2, list)
    assert os.path.isabs(p2[0])
    assert p3 == "not_a_path"

# --- TaskThrottler Tests ---
@pytest.mark.asyncio
async def test_task_throttler_concurrency():
    throttler = TaskThrottler(concurrency_limit=2)
    active_tasks = 0
    max_active = 0

    async def worker():
        nonlocal active_tasks, max_active
        async with throttler:
            active_tasks += 1
            max_active = max(max_active, active_tasks)
            await asyncio.sleep(0.1)
            active_tasks -= 1

    await asyncio.gather(*[worker() for _ in range(5)])
    assert max_active == 2

# --- SqliteRepositoryBase Tests ---
class MockRepo(SqliteRepositoryBase):
    def __init__(self, db_path):
        self.db_path = db_path
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

@pytest.mark.asyncio
async def test_sqlite_repository_utils(tmp_path):
    db_file = tmp_path / "test.db"
    repo = MockRepo(str(db_file))
    conn = repo.get_conn()
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'Alice')")
    conn.commit()
    
    row = conn.execute("SELECT * FROM test").fetchone()
    d = repo.row_to_dict(row)
    assert d == {"id": 1, "name": "Alice"}
    assert repo.get_field(row, "name") == "Alice"
    assert repo.get_field(row, "missing", "default") == "default"
    conn.close()

# --- WindowsLoopManager Tests ---
@pytest.mark.asyncio
async def test_windows_loop_manager_setup():
    # Just ensure it doesn't crash
    WindowsLoopManager.setup_loop()
    assert True
