import pytest
from sqlalchemy import Table, Column, String, Integer, create_engine, text
from sqlalchemy.orm import Session, clear_mappers
from src.adapters.orm import mapper_registry
from tests.conftest import FakeAggregate


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine


def test_imperative_mapping_loads_fake_aggregate(sqlite_engine):
    # Setup test table for FakeAggregate
    fake_table = Table(
        "fake_aggregates",
        mapper_registry.metadata,
        Column("ref", String(255), primary_key=True),
        Column("version", Integer, nullable=False, default=1),
    )

    # Create tables
    mapper_registry.metadata.create_all(sqlite_engine)

    # Map the class
    mapper_registry.map_imperatively(FakeAggregate, fake_table)

    try:
        # Insert raw data (bypassing ORM)
        with sqlite_engine.connect() as conn:
            conn.execute(
                text("INSERT INTO fake_aggregates (ref, version) VALUES ('agg1', 1)")
            )
            conn.commit()

        # Verify ORM loads it as a domain object
        with Session(sqlite_engine) as session:
            agg = session.query(FakeAggregate).filter_by(ref="agg1").one()
            assert agg.ref == "agg1"
            assert agg.version == 1
    finally:
        # Clean up mapping so we don't pollute other tests
        clear_mappers()
