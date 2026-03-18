import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from src.core.system import System
from src.core.messagebus import MessageBus
from typing import List, Any, Optional, Annotated, List as TypingList
from src.core.discovery import ModuleDiscovery
from src.core.module import BaseModule
from src.core.messages import Command, Event
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.agm.handlers import handle_stored_field_recalc
from src.modules.agm.messages import StoredFieldRecalculationRequested
from dishka import Provider, Scope, provide

# Mock UoW for MessageBus tests
class MockUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass
    def _get_events(self): return []

class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return MockUoW()

class MockModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.provider = MockUoWProvider()

@pytest.fixture(autouse=True)
def cleanup_bubus():
    yield
    import bubus
    for bus in bubus.EventBus.all_instances:
        bus._is_running = False

@pytest.mark.asyncio
async def test_system_stop_not_started():
    system = System(modules=[MockModule()])
    # Case: Stopping a system that was never started
    await system.stop() # Should log warning and return

@pytest.mark.asyncio
async def test_system_bootstrap_twice():
    system = System(modules=[MockModule()])
    system._bootstrap()
    # Case: Calling _bootstrap again should return early
    system._bootstrap()
    assert system._initialized is True
    if system.container:
        await system.container.close()

@pytest.mark.asyncio
async def test_messagebus_sync_handlers():
    uow = MockUoW()
    bus = MessageBus(uow=uow)
    
    class SyncCommand(Command): pass
    class SyncEvent(Event): pass
    
    cmd_handled = False
    evt_handled = False
    
    def sync_cmd_handler(cmd, uow):
        nonlocal cmd_handled
        cmd_handled = True
        
    def sync_evt_handler(evt, uow):
        nonlocal evt_handled
        evt_handled = True
        
    bus.register_command(SyncCommand, sync_cmd_handler)
    bus.register_event(SyncEvent, sync_evt_handler)
    
    # Case: Dispatch sync command (coverage for line 69)
    await bus.dispatch(SyncCommand())
    assert cmd_handled is True
    
    # Case: Dispatch sync event (coverage for line 102)
    await bus.dispatch(SyncEvent())
    assert evt_handled is True
    
    await bus.bus.stop(clear=True)

def test_module_discovery_missing_manifest():
    # Case: Manifest file does not exist (coverage for line 14)
    with pytest.raises(FileNotFoundError):
        ModuleDiscovery.load_from_manifest("non_existent_manifest.toml")

def test_module_discovery_import_error():
    # Case: Module not found in any provided paths (coverage for line 47)
    with pytest.raises(ImportError):
        ModuleDiscovery._import_module("invalid_module", ["src.modules"])

@pytest.mark.asyncio
async def test_agm_handler_error_handling():
    event = StoredFieldRecalculationRequested(
        node_id="node1", field_name="field1", new_source_val=10.0
    )
    
    # Case: TaskIQ job dispatch fails (coverage for line 21)
    with patch("src.modules.agm.tasks.compute_stored_field.kiq", new_callable=AsyncMock) as mock_kiq:
        mock_kiq.side_effect = Exception("TaskIQ error")
        await handle_stored_field_recalc(event)
        # Should catch exception and log error without crashing

@pytest.mark.asyncio
async def test_agm_mapper_polymorphism():
    from src.modules.agm.mapper import AGMMapper
    from src.modules.agm.metadata import Live
    from dataclasses import dataclass, field
    from typing import Annotated, Optional

    @dataclass
    class BaseNode:
        id: str = field(default=None)
        labels: list[str] = field(default_factory=list)

    @dataclass
    class SubNode(BaseNode):
        extra: str = "val"

    container = AsyncMock()
    bus = AsyncMock()
    mapper = AGMMapper(container, bus)
    mapper.register_subclass("SubNode", SubNode)

    # Case: Polymorphic loading (coverage for lines 30-32)
    record = {"id": "1", "labels": ["SubNode"], "extra": "custom"}
    instance = await mapper.load(BaseNode, record)
    assert isinstance(instance, SubNode)
    assert instance.extra == "custom"

@pytest.mark.asyncio
async def test_agm_mapper_live_hydration_failure():
    from src.modules.agm.mapper import AGMMapper
    from src.modules.agm.metadata import Live
    from dataclasses import dataclass, field
    from typing import Annotated, Optional

    @dataclass
    class Node:
        id: str
        handler: Annotated[Optional[Any], Live(handler=int)] = None

    container = AsyncMock()
    # Case: Live Hydration fails (coverage for lines 46-47)
    container.get.side_effect = Exception("DI Failure")
    
    bus = AsyncMock()
    mapper = AGMMapper(container, bus)
    
    instance = await mapper.load(Node, {"id": "1"})
    assert instance.handler is None

@pytest.mark.asyncio
async def test_agm_mapper_save_no_id():
    from src.modules.agm.mapper import AGMMapper
    from dataclasses import dataclass

    @dataclass
    class Node:
        name: str

    mapper = AGMMapper(AsyncMock(), AsyncMock())
    # Case: Save without 'id' (coverage for lines 76-77)
    await mapper.save(Node(name="test"))
    # Should log error and return

@pytest.mark.asyncio
async def test_agm_mapper_rel_merge_outgoing():
    from src.modules.agm.mapper import AGMMapper
    from src.modules.agm.metadata import Rel
    from dataclasses import dataclass, field
    from typing import Annotated, List

    @dataclass
    class Target:
        id: str

    @dataclass
    class Root:
        id: str
        friends: Annotated[List[Target], Rel(type="FRIEND", direction="OUTGOING")] = field(default_factory=list)

    mapper = AGMMapper(AsyncMock(), AsyncMock())
    session = AsyncMock()
    
    root = Root(id="1", friends=[Target(id="2")])
    # Case: Save relationship (coverage for lines 106-119, 138)
    await mapper.save(root, session=session)
    assert session.run.called

@pytest.mark.asyncio
async def test_agm_mapper_event_dispatch_failure():
    from src.modules.agm.mapper import AGMMapper
    from src.modules.agm.metadata import Stored
    from dataclasses import dataclass
    from typing import Annotated

    @dataclass
    class Node:
        id: str
        val: int
        calc: Annotated[int, Stored(source_field="val")] = 0

    bus = AsyncMock()
    # Case: Dispatch failure (coverage for lines 164-165)
    bus.dispatch.side_effect = Exception("Bus error")
    
    mapper = AGMMapper(AsyncMock(), bus)
    await mapper.save(Node(id="1", val=10), previous_state={"val": 5})
    # Should log error and continue

@pytest.mark.asyncio
async def test_ecs_handler_move_entity_success():
    from src.modules.ecs.handlers import handle_move_entity_command
    from src.modules.ecs.messages import MoveEntityCommand
    from src.modules.ecs.domain import PositionComponent
    
    uow = MagicMock()
    world = MagicMock()
    pos = PositionComponent(x=0, y=0)
    
    uow.worlds.get_world = AsyncMock(return_value=world)
    world.get_component.return_value = pos
    
    cmd = MoveEntityCommand(entity_id="1", target_x=10, target_y=20)
    # Case: Successful move (coverage for lines 40-45)
    result = await handle_move_entity_command(cmd, uow)
    assert result.unwrap() is True
    assert pos.x == 10
    assert pos.y == 20
    assert uow.commit.called
