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
    """Configuration settings for the Analytics module.

    Attributes:
        report_timeout: Maximum time in seconds to wait for report generation.
    """
    report_timeout: int = 600


# --- 2. Define Commands and Events ---
class GenerateReportCommand(Command):
    """Command to initiate a heavy report generation process.
    
    Attributes:
        report_type: The category of report (e.g., 'PDF', 'CSV').
        user_id: The identifier of the user requesting the report.
    """
    report_type: str
    user_id: str


class ReportGenerationStartedEvent(Event):
    """Event emitted when a report generation task has been dispatched.
    
    Attributes:
        report_id: The unique task ID of the background job.
    """
    report_id: str


# --- 3. Define the heavy background TaskIQ Task ---
@broker.task
async def build_heavy_report_task(report_type: str, user_id: str) -> dict:
    """Background worker task for generating reports.

    This function is executed by a TaskIQ worker, isolated from the 
    main application event loop.

    Args:
        report_type: The type of report to generate.
        user_id: The user ID for whom the report is being built.

    Returns:
        A dictionary containing the status and result URL.
    """
    logger.info(
        f"Generating {report_type} report for user {user_id} in background via NATS..."
    )
    # Simulate heavy DB query / PDF generation
    await asyncio.sleep(2)
    return {"status": "success", "file_url": f"https://s3.local/reports/{user_id}.pdf"}


# --- 4. Define the Domain Module ---
class AnalyticsModule(BaseModule):
    """Domain module for handling heavy analytical background tasks.
    
    Demonstrates the integration between MessageBus command handling 
    and TaskIQ background worker delegation.
    """
    settings_class = AnalyticsSettings

    def __init__(self):
        """Initialises the Analytics module and registers command handlers."""
        super().__init__()

        # Declarative CQRS Routing
        self.command_handlers = {GenerateReportCommand: self.handle_generate_report}

    async def handle_generate_report(
        self, cmd: GenerateReportCommand, uow: AbstractUnitOfWork
    ) -> BusinessResult:
        """Handles the GenerateReportCommand by dispatching to TaskIQ.

        Args:
            cmd: The command containing report parameters.
            uow: The active Unit of Work (used here for coordination).

        Returns:
            A BusinessResult containing the task ID on success.
        """
        logger.info(f"Received GenerateReportCommand for {cmd.user_id}")

        # 1. Dispatch heavy background work to TaskIQ via NATS adapter
        task_info = await build_heavy_report_task.kiq(cmd.report_type, cmd.user_id)

        return success({"status": "processing", "task_id": task_info.task_id})
