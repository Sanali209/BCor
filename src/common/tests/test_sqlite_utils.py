import pytest
import sqlite3
from src.common.database.sqlite_utils import SqliteRepositoryBase

def test_sqlite_repository_row_to_dict():
    """Verify that SqliteRepositoryBase correctly converts rows to dicts."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    db.execute("INSERT INTO test VALUES (1, 'Alice')")
    db.commit()
    
    row = db.execute("SELECT * FROM test").fetchone()
    d = SqliteRepositoryBase.row_to_dict(row)
    
    assert isinstance(d, dict)
    assert d["name"] == "Alice"
    assert d["id"] == 1
    db.close()

def test_sqlite_repository_get_field():
    """Verify safe field retrieval."""
    assert SqliteRepositoryBase.get_field({"a": 1}, "a") == 1
    assert SqliteRepositoryBase.get_field({"a": 1}, "b", default=2) == 2
    assert SqliteRepositoryBase.get_field(None, "any", default=3) == 3
