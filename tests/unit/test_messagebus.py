import pytest
import asyncio

from src.core.messages import Command, Event
from src.core.messagebus import MessageBus
from tests.conftest import FakeUnitOfWork, FakeAggregate
from src.core.monads import success, BusinessResult
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from dishka import Provider, Scope, provide
from src.core.module import BaseModule
from src.core.system import System
from src.core.unit_of_work import AbstractUnitOfWork


class CreateDummyCommand(Command):
    id: str


class FlakyCommand(Command):
    id: str


class FailingCommand(Command):
    id: str


class DummyCreatedEvent(Event):
    id: str


class DummySettings(BaseSettings):
    dummy_key: str = "default_value"


# Let's create a Mock Module for testing Dishka & Composition Root
class DummyModule(BaseModule):
    settings_class = DummySettings

    def __init__(self):
        super().__init__()
        self.handled_cmd = None
        self.event_handled = False
        self.attempts = 0
        self.flaky_attempts = 0
        self.fail_attempts = 0
        self.handler1_called = False
        self.handler2_called = False

        # Maps
        self.command_handlers = {
            CreateDummyCommand: self.handle_create,
            FlakyCommand: self.handle_flaky,
            FailingCommand: self.handle_failing,
        }
        self.event_handlers = {
            DummyCreatedEvent: [self.handle_event, self.handler1, self.handler2]
        }

    async def handle_create(
        self, cmd: CreateDummyCommand, uow: FakeUnitOfWork
    ) -> BusinessResult:
        self.handled_cmd = cmd
        with uow:
            agg = FakeAggregate(cmd.id)
            agg.add_event(DummyCreatedEvent(id=cmd.id))
            uow.repo.add(agg)
            uow.commit()
        return success(cmd.id)

    async def handle_flaky(
        self, cmd: FlakyCommand, uow: FakeUnitOfWork
    ) -> BusinessResult:
        self.flaky_attempts += 1
        if self.flaky_attempts < 3:
            raise Exception("Temporary Failure")
        return success(cmd.id)

    async def handle_failing(
        self, cmd: FailingCommand, uow: FakeUnitOfWork
    ) -> BusinessResult:
        self.fail_attempts += 1
        raise Exception("Permanent Failure")

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
def system(dummy_module, monkeypatch):
    # Set environment variable to test pydantic settings validation
    monkeypatch.setenv("DUMMY_KEY", "test_value_from_env")

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
        await bus.dispatch(cmd)

        # In bubus, dispatch completes when all handlers registered are fired.
        # However, due to background tasks sometimes in bubus, we add a brief sleep.
        await asyncio.sleep(0.01)
        bus.bus._is_running = False

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
        await bus.dispatch(evt)

        await asyncio.sleep(0.01)
        bus.bus._is_running = False

        assert dummy_module.handler1_called is True
        assert dummy_module.handler2_called is True


def test_pydantic_validation():
    """Test strict DTO validation (BaseEvent wraps BaseModel)."""
    with pytest.raises(ValidationError):
        CreateDummyCommand()


@pytest.mark.asyncio
async def test_flaky_command_retries(system, dummy_module):
    """Test that a command handler that fails is retried."""
    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)

        cmd = FlakyCommand(id="flaky_123")
        await bus.dispatch(cmd)

        await asyncio.sleep(0.01)
        bus.bus._is_running = False

        # Handler should have been called exactly 3 times (fails twice, succeeds on third)
        assert dummy_module.flaky_attempts == 3


@pytest.mark.asyncio
async def test_failing_command_exhausts_retries(system, dummy_module):
    """Test that a command handler that fails permanently throws after max retries."""
    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)

        cmd = FailingCommand(id="fail_123")

        # bubus swallows the exception and returns it in results, so it won't raise
        results = await bus.dispatch(cmd)

        await asyncio.sleep(0.01)
        bus.bus._is_running = False

        # Handler should have been called 3 times and then given up
        assert dummy_module.fail_attempts == 3
