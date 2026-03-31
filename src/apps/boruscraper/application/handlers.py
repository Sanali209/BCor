from typing import Optional, Dict
import asyncio
from loguru import logger

from src.apps.experemental.boruscraper.application.messages import (
    StartScrapeCommand, PauseScrapeCommand, ResumeScrapeCommand, 
    StopScrapeCommand, SetResolutionActionCommand
)
from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.common.deduplication import DeduplicationManager
from src.apps.experemental.boruscraper.application.use_cases import ScrapeProjectUseCase
from src.apps.experemental.boruscraper.infrastructure.uow import SqliteUnitOfWork
from src.core.messagebus import MessageBus

class ScrapeTaskManager:
    """Manages active async scrape tasks."""
    
    def __init__(self, bus: MessageBus, db: DatabaseManager, dedup: DeduplicationManager):
        self.bus = bus
        self.db = db
        self.dedup = dedup
        self.active_use_cases: Dict[int, ScrapeProjectUseCase] = {}
        self.active_tasks: Dict[int, asyncio.Task] = {}

    def start_worker(self, project_id: int, debug_mode: bool):
        if project_id in self.active_use_cases and self.active_use_cases[project_id].is_running:
            return  # already running
        
        uow = SqliteUnitOfWork(self.db)
        use_case = ScrapeProjectUseCase(self.bus, uow, self.db, self.dedup)
        self.active_use_cases[project_id] = use_case
        
        logger.info(f"ScrapeTaskManager: Starting worker for project {project_id} (debug={debug_mode})")
        task = asyncio.create_task(use_case.execute(project_id, debug_mode))
        self.active_tasks[project_id] = task

        # Add a callback to cleanup when done
        task.add_done_callback(lambda t: self._cleanup_task(project_id))

    def _cleanup_task(self, project_id: int):
        if project_id in self.active_use_cases:
            del self.active_use_cases[project_id]
        if project_id in self.active_tasks:
            del self.active_tasks[project_id]

    def get_worker(self, project_id: int) -> Optional[ScrapeProjectUseCase]:
        return self.active_use_cases.get(project_id)

    async def stop_worker(self, project_id: int):
        use_case = self.get_worker(project_id)
        if use_case:
            use_case.is_running = False
            use_case.is_paused = False # unpause to let it exit
            
            # Wait for task to finish gracefully subject to a timeout
            task = self.active_tasks.get(project_id)
            if task:
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except asyncio.TimeoutError:
                    task.cancel()


async def start_scrape_handler(cmd: StartScrapeCommand, task_manager: ScrapeTaskManager):
    logger.info(f"start_scrape_handler: Received command for project {cmd.project_id}")
    task_manager.start_worker(cmd.project_id, cmd.debug_mode)

async def pause_scrape_handler(cmd: PauseScrapeCommand, task_manager: ScrapeTaskManager):
    use_case = task_manager.get_worker(cmd.project_id)
    if use_case:
        use_case.is_paused = True

async def resume_scrape_handler(cmd: ResumeScrapeCommand, task_manager: ScrapeTaskManager):
    use_case = task_manager.get_worker(cmd.project_id)
    if use_case:
        use_case.is_paused = False

async def stop_scrape_handler(cmd: StopScrapeCommand, task_manager: ScrapeTaskManager):
    await task_manager.stop_worker(cmd.project_id)

async def set_resolution_action_handler(cmd: SetResolutionActionCommand, task_manager: ScrapeTaskManager):
    use_case = task_manager.get_worker(cmd.project_id)
    if use_case:
        use_case.resolution_action = cmd.action
        use_case.is_paused = False
