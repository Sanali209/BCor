import asyncio
from dataclasses import dataclass
from typing import Annotated, NewType

import pytest
from dishka import Provider, Scope, make_async_container, provide

from src.core.messagebus import MessageBus
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.agm.metadata import Live, Stored

FetchLiveStatus = NewType("FetchLiveStatus", str)


@dataclass
class NodeData:
    id: str
    text: str

    # Metadata pipeline: stored as vector embedding. Source is 'text'
    embedding: Annotated[list[float], Stored(source_field="text")] = None

    # Metadata pipeline: live data hydration from a NATS/Bubus queue.
    # Uses 'user_id' injected from Dishka scope.
    status: Annotated[str, Live(handler=FetchLiveStatus)] = "offline"


class MockHandlerProvider(Provider):
    scope = Scope.APP

    @provide
    async def fetch_live_status(self) -> FetchLiveStatus:
        await asyncio.sleep(0.01)
        return FetchLiveStatus("online")


@pytest.fixture
def container():
    provider = MockHandlerProvider()
    return make_async_container(provider)


@pytest.mark.asyncio
async def test_agm_load_pipeline(container, mocker):
    mock_bus = mocker.AsyncMock(spec=MessageBus)
    mapper = AGMMapper(container=container, message_bus=mock_bus)

    # Fake neo4j.Record dict
    db_record = {
        "id": "123",
        "text": "Hello world",
        "embedding": [0.1, 0.2, 0.3],
    }

    node = await mapper.load(NodeData, db_record)

    # Native & Stored properties
    assert node.id == "123"
    assert node.text == "Hello world"
    assert node.embedding == [0.1, 0.2, 0.3]

    # Live Hydration (from Dishka DI mock)
    assert node.status == "online"


@pytest.mark.asyncio
async def test_agm_save_pipeline(container, mocker):
    mock_bus = mocker.AsyncMock(spec=MessageBus)
    mapper = AGMMapper(container=container, message_bus=mock_bus)
    node = NodeData(id="123", text="Changed text", embedding=[0.1, 0.2, 0.3])

    db_record = {
        "id": "123",
        "text": "Hello world",
        "embedding": [0.1, 0.2, 0.3],
    }

    await mapper.save(node, previous_state=db_record)

    # 'text' was changed, so we expect a task to compute new 'embedding' to be queued
    assert mock_bus.dispatch.call_count == 1
    event = mock_bus.dispatch.call_args[0][0]
    assert isinstance(event, StoredFieldRecalculationRequested)
    assert event.node_id == "123"
    assert event.field_name == "embedding"
    assert event.new_source_val == "Changed text"
