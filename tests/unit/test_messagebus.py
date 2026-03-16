import pytest
import asyncio
from typing import Any

from src.core.messages import Command, Event
from src.core.messagebus import MessageBus
from tests.conftest import FakeUnitOfWork, FakeAggregate
from src.core.monads import success, BusinessResult
from pydantic import ValidationError

from dishka import Provider, Scope, provide
from src.core.module import BaseModule
from src.core.system import System
from src.core.unit_of_work import AbstractUnitOfWork

class CreateDummyCommand(Command):
    id: str

class DummyCreatedEvent(Event):
    id: str

# Let's create a Mock Module for testing Dishka & Composition Root
class DummyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.handled_cmd = None
        self.event_handled = False
        self.attempts = 0
        self.handler1_called = False
        self.handler2_called = False

        # Maps
        self.command_handlers = {
            CreateDummyCommand: self.handle_create
        }
        self.event_handlers = {
            DummyCreatedEvent: [self.handle_event, self.handler1, self.handler2]
        }

    async def handle_create(self, cmd: CreateDummyCommand, uow: FakeUnitOfWork) -> BusinessResult:
        self.handled_cmd = cmd
        with uow:
            agg = FakeAggregate(cmd.id)
            agg.add_event(DummyCreatedEvent(id=cmd.id))
            uow.repo.add(agg)
            uow.commit()
        return success(cmd.id)

    async def handle_event(self, evt: DummyCreatedEvent, uow: FakeUnitOfWork):
        self.event_handled = True

    async def handler1(self, evt: DummyCreatedEvent, uow: FakeUnitOfWork):
        self.handler1_called = True
        raise Exception("Failure in event handler 1")

    async def handler2(self, evt: DummyCreatedEvent, uow: FakeUnitOfWork):
        self.handler2_called = True

@pytest.fixture
def dummy_module():
    return DummyModule()

class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return FakeUnitOfWork()

@pytest.fixture
def system(dummy_module):
    system = System(modules=[dummy_module])
    # Add our test provider
    system.providers.append(MockUoWProvider())
    system._bootstrap()
    return system

@pytest.mark.asyncio
async def test_system_bootstrap_and_command_handling(system, dummy_module):
    """Test composition root logic and command routing through MessageBus."""

    # Open request scope
    async with system.container() as request_container:
        # Retrieve UoW to assert states
        uow = await request_container.get(AbstractUnitOfWork)
        # Retrieve built message bus
        bus = await request_container.get(MessageBus)

        cmd = CreateDummyCommand(id="123")
        await bus.handle(cmd)

        assert dummy_module.handled_cmd == cmd
        assert dummy_module.event_handled is True

        assert uow.repo.get("123") is not None
        assert uow.committed is True

@pytest.mark.asyncio
async def test_event_handling_multiple_subscribers_and_isolation(system, dummy_module):
    """Test event broadcasting and that exceptions in one handler don't break others."""

    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)

        evt = DummyCreatedEvent(id="123")
        await bus.handle(evt)

        assert dummy_module.handler1_called is True
        assert dummy_module.handler2_called is True

def test_pydantic_validation():
    """Test strict DTO validation (BaseEvent wraps BaseModel)."""
    with pytest.raises(ValidationError):
        CreateDummyCommand()
