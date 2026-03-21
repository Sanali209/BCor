import pytest
from dishka import Provider, Scope, provide

from src.core.decorators import clear_hooks, on_start, on_stop
from src.core.module import BaseModule
from src.core.system import System
from src.core.unit_of_work import AbstractUnitOfWork


class MockUoW(AbstractUnitOfWork):
    def commit(self):
        pass

    def rollback(self):
        pass

    def _get_events(self):
        return []


class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return MockUoW()


class MockModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.provider = MockUoWProvider()


@pytest.fixture(autouse=True)
def cleanup():
    clear_hooks()
    yield
    clear_hooks()


@pytest.mark.asyncio
async def test_lifecycle_hooks_execution():
    start_called = 0
    stop_called = 0

    @on_start
    async def async_start():
        nonlocal start_called
        start_called += 1

    @on_start
    def sync_start():
        nonlocal start_called
        start_called += 1

    @on_stop
    async def async_stop():
        nonlocal stop_called
        stop_called += 1

    @on_stop
    def sync_stop():
        nonlocal stop_called
        stop_called += 1

    system = System(modules=[MockModule()])

    # 1. Start
    await system.start()
    assert start_called == 2
    assert stop_called == 0

    # 2. Stop
    await system.stop()
    assert start_called == 2
    assert stop_called == 2


@pytest.mark.asyncio
async def test_system_prevent_multiple_start():
    start_count = 0

    @on_start
    def increment():
        nonlocal start_count
        start_count += 1

    system = System(modules=[MockModule()])
    await system.start()
    await system.start()  # Should warn and return

    assert start_count == 1


@pytest.mark.asyncio
async def test_hook_error_propagation():
    @on_start
    def fail():
        raise ValueError("Hook failed")

    system = System(modules=[MockModule()])

    with pytest.raises(ValueError, match="Hook failed"):
        await system.start()
