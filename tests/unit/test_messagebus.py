import pytest
import asyncio
from src.core.messages import Command, Event
from src.core.messagebus import MessageBus
from tests.conftest import FakeUnitOfWork, FakeAggregate
from src.core.monads import success, BusinessResult
from pydantic import ValidationError

class CreateDummyCommand(Command):
    id: str

class DummyCreatedEvent(Event):
    id: str

@pytest.fixture(autouse=True)
def stop_bubus():
    """Stop bubus loop after every test so we don't hang pytest."""
    yield
    import bubus
    for bus in bubus.EventBus.all_instances:
        bus._is_running = False

@pytest.mark.asyncio
async def test_command_handling_success():
    uow = FakeUnitOfWork()
    bus = MessageBus(uow=uow)

    handled_cmd = None
    event_handled = False

    def handle_create(cmd: CreateDummyCommand, uow: FakeUnitOfWork) -> BusinessResult:
        nonlocal handled_cmd
        handled_cmd = cmd
        with uow:
            agg = FakeAggregate(cmd.id)
            agg.add_event(DummyCreatedEvent(id=cmd.id))
            uow.repo.add(agg)
            uow.commit()
        return success(cmd.id)

    async def handle_event(evt: DummyCreatedEvent):
        nonlocal event_handled
        event_handled = True

    bus.register_command(CreateDummyCommand, handle_create)
    bus.bus.on(DummyCreatedEvent, handle_event)

    cmd = CreateDummyCommand(id="123")
    result = await bus.handle_command(cmd)

    await asyncio.sleep(0.01)
    bus.bus._is_running = False

    assert handled_cmd == cmd
    assert result.unwrap() == "123"
    assert uow.repo.get("123") is not None
    assert uow.committed is True
    assert event_handled is True

@pytest.mark.asyncio
async def test_event_handling_multiple_subscribers():
    uow = FakeUnitOfWork()
    bus = MessageBus(uow=uow)

    handler1_called = False
    handler2_called = False

    async def handler1(evt: DummyCreatedEvent):
        nonlocal handler1_called
        handler1_called = True
        raise Exception("Failure in event handler 1")

    async def handler2(evt: DummyCreatedEvent):
        nonlocal handler2_called
        handler2_called = True

    bus.bus.on(DummyCreatedEvent, handler1)
    bus.bus.on(DummyCreatedEvent, handler2)

    evt = DummyCreatedEvent(id="123")
    await bus.bus.dispatch(evt)

    await asyncio.sleep(0.01)
    bus.bus._is_running = False

    assert handler1_called is True
    assert handler2_called is True

@pytest.mark.asyncio
async def test_retry_policy():
    uow = FakeUnitOfWork()
    bus = MessageBus(uow=uow)
    bus.bus._is_running = False # Not needing events for this

    attempts = 0
    def failing_handler(cmd: CreateDummyCommand, uow: FakeUnitOfWork):
        nonlocal attempts
        attempts += 1
        raise ValueError("Simulated temporary failure")

    bus.register_command(CreateDummyCommand, failing_handler, with_retry=True)

    with pytest.raises(ValueError):
        await bus.handle_command(CreateDummyCommand(id="retry-test"))

    assert attempts == 3

def test_pydantic_validation():
    with pytest.raises(ValidationError):
        CreateDummyCommand()
