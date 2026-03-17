import pytest
import asyncio

from tests.conftest import FakeUnitOfWork
from dishka import Provider, Scope, provide

from src.core.system import System
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork

from src.modules.analytics.domain import (
    AnalyticsModule,
    GenerateReportCommand,
    build_heavy_report_task,
)


class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return FakeUnitOfWork()


@pytest.fixture
def system(monkeypatch):
    monkeypatch.setenv("REPORT_TIMEOUT", "1200")

    analytics_mod = AnalyticsModule()
    sys = System(modules=[analytics_mod])
    sys.providers.append(MockUoWProvider())
    sys._bootstrap()
    return sys


@pytest.mark.asyncio
async def test_analytics_background_task_dispatch(system, monkeypatch):
    """Test the flow from Command -> internal MessageBus -> external NATS task dispatch"""

    # Mock taskiq's `.kiq` method so we don't actually try to reach NATS in tests
    called_args = None

    class DummyTaskInfo:
        task_id = "mock-1234-uuid"

    async def mock_kiq(*args, **kwargs):
        nonlocal called_args
        called_args = args
        return DummyTaskInfo()

    monkeypatch.setattr(build_heavy_report_task, "kiq", mock_kiq)

    # Resolve message bus from Composition Root
    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)

        # FastAPI/UI dispatches command:
        cmd = GenerateReportCommand(report_type="monthly_sales", user_id="user_88")

        # bubus dispatch handles routing
        await bus.dispatch(cmd)

        await asyncio.sleep(0.01)
        bus.bus._is_running = False

        # Assert the TaskIQ background worker was properly called via NATS
        assert called_args == ("monthly_sales", "user_88")
        assert system.settings["analytics"].report_timeout == 1200
