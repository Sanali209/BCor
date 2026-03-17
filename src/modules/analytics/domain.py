import asyncio
import logging

from pydantic_settings import BaseSettings

from src.core.messages import Command, Event
from src.core.monads import BusinessResult, success
from src.core.module import BaseModule
from src.core.unit_of_work import AbstractUnitOfWork
from src.adapters.taskiq_broker import broker

logger = logging.getLogger(__name__)


# --- 1. Define Settings ---
class AnalyticsSettings(BaseSettings):
    report_timeout: int = 600


# --- 2. Define Commands and Events ---
class GenerateReportCommand(Command):
    report_type: str
    user_id: str


class ReportGenerationStartedEvent(Event):
    report_id: str


# --- 3. Define the heavy background TaskIQ Task ---
# This function will run outside the main event loop, executed by a NATS worker.
@broker.task
async def build_heavy_report_task(report_type: str, user_id: str) -> dict:
    logger.info(
        f"Generating {report_type} report for user {user_id} in background via NATS..."
    )
    # Simulate heavy DB query / PDF generation
    await asyncio.sleep(2)
    return {"status": "success", "file_url": f"https://s3.local/reports/{user_id}.pdf"}


# --- 4. Define the Domain Module ---
class AnalyticsModule(BaseModule):
    """Analytics Domain Module
    Demonstrates handling a command via MessageBus and delegating heavy work to TaskIQ.
    """

    settings_class = AnalyticsSettings

    def __init__(self):
        super().__init__()

        # Declarative CQRS Routing
        self.command_handlers = {GenerateReportCommand: self.handle_generate_report}

    async def handle_generate_report(
        self, cmd: GenerateReportCommand, uow: AbstractUnitOfWork
    ) -> BusinessResult:
        logger.info(f"Received GenerateReportCommand for {cmd.user_id}")

        # 1. Dispatch heavy background work to TaskIQ via NATS adapter
        # This returns immediately, not blocking the bubus event loop
        task_info = await build_heavy_report_task.kiq(cmd.report_type, cmd.user_id)

        # 2. Add domain event to unit of work
        # In a real app we'd load an aggregate, but for demo we just add it to the bus indirectly via UoW if needed,
        # or return early to the FastAPI controller

        return success({"status": "processing", "task_id": task_info.task_id})
