import pytest
from sqlalchemy import Column, Integer, String, Table, create_engine, text
from sqlalchemy.orm import Session, clear_mappers

from src.adapters.orm import mapper_registry
from src.adapters.repository import SqlAlchemyRepository
from tests.conftest import FakeAggregate


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite:///:memory:")

    fake_table = Table(
        "fake_aggregates",
        mapper_registry.metadata,
        Column("ref", String(255), primary_key=True),
        Column("version", Integer, nullable=False, default=1),
        extend_existing=True,
    )
    mapper_registry.metadata.create_all(engine)
    mapper_registry.map_imperatively(FakeAggregate, fake_table)

    session = Session(engine)
    yield session

    session.close()
    clear_mappers()


def test_repository_can_save_aggregate(sqlite_session):
    repo = SqlAlchemyRepository(sqlite_session, FakeAggregate)

    agg = FakeAggregate(ref="agg_save")
    repo.add(agg)
    sqlite_session.commit()

    rows = list(sqlite_session.execute(text("SELECT ref, version FROM fake_aggregates")))
    assert rows == [("agg_save", 1)]


def test_repository_can_retrieve_aggregate(sqlite_session):
    sqlite_session.execute(text("INSERT INTO fake_aggregates (ref, version) VALUES ('agg_get', 2)"))
    sqlite_session.commit()

    repo = SqlAlchemyRepository(sqlite_session, FakeAggregate)
    agg = repo.get("agg_get")

    assert agg is not None
    assert agg.ref == "agg_get"
    assert agg.version == 2
