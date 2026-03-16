import pytest
import asyncio
from typing import Annotated, NewType
from dataclasses import dataclass
from adaptix import Retort
from dishka import make_async_container, Provider, Scope, provide
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.metadata import Stored, Live

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
async def test_agm_load_pipeline(container):
    mapper = AGMMapper(container=container)

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
    mapper = AGMMapper(container=container)
    node = NodeData(id="123", text="Changed text", embedding=[0.1, 0.2, 0.3])

    # Mock NATS/TaskIQ trigger
    mock_trigger = mocker.patch("src.modules.agm.tasks.compute_stored_field.kiq")

    db_record = {
        "id": "123",
        "text": "Hello world",
        "embedding": [0.1, 0.2, 0.3],
    }

    await mapper.save(node, previous_state=db_record)

    # 'text' was changed, so we expect a task to compute new 'embedding' to be queued
    mock_trigger.assert_called_once_with(node.id, "embedding", "Changed text")
