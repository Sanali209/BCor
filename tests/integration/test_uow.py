import pytest
from sqlalchemy import Column, Integer, String, Table, create_engine, text
from sqlalchemy.orm import clear_mappers, sessionmaker

from src.adapters.orm import mapper_registry
from src.adapters.unit_of_work import SqlAlchemyUnitOfWork
from tests.conftest import FakeAggregate


@pytest.fixture
def sqlite_session_factory():
    engine = create_engine("sqlite:///:memory:")

    fake_table = Table(
        "fake_aggregates_uow",
        mapper_registry.metadata,
        Column("ref", String(255), primary_key=True),
        Column("version", Integer, nullable=False, default=1),
        extend_existing=True,
    )
    mapper_registry.metadata.create_all(engine)
    mapper_registry.map_imperatively(FakeAggregate, fake_table)

    yield sessionmaker(bind=engine)

    clear_mappers()


def test_uow_can_retrieve_and_commit(sqlite_session_factory):
    session = sqlite_session_factory()
    session.execute(text("INSERT INTO fake_aggregates_uow (ref, version) VALUES ('agg_uow1', 1)"))
    session.commit()

    uow = SqlAlchemyUnitOfWork(sqlite_session_factory, model_class=FakeAggregate)
    with uow:
        agg = uow.repository.get("agg_uow1")
        agg.version = 2
        uow.commit()

    session = sqlite_session_factory()
    rows = list(session.execute(text("SELECT version FROM fake_aggregates_uow WHERE ref='agg_uow1'")))
    assert rows == [(2,)]


def test_uow_rolls_back_on_error(sqlite_session_factory):
    uow = SqlAlchemyUnitOfWork(sqlite_session_factory, model_class=FakeAggregate)

    class MyException(Exception):
        pass

    with pytest.raises(MyException):
        with uow:
            agg = FakeAggregate(ref="agg_uow2")
            uow.repository.add(agg)
            raise MyException()

    # Session rollback should have been called, let's verify nothing was saved
    session = sqlite_session_factory()
    rows = list(session.execute(text("SELECT ref FROM fake_aggregates_uow")))
    assert rows == []
