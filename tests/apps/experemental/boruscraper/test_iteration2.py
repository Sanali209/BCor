import pytest
from src.apps.experemental.boruscraper.application.messages import StartScrapeCommand, PauseScrapeCommand
from src.apps.experemental.boruscraper.application.handlers import StartScrapeHandler, PauseScrapeHandler
from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.common.deduplication import DeduplicationManager

@pytest.mark.asyncio
async def test_commands_can_be_instantiated():
    cmd = StartScrapeCommand(project_id=1, debug_mode=False)
    assert cmd.project_id == 1
    assert cmd.debug_mode is False

@pytest.mark.asyncio
async def test_start_scrape_handler(tmp_path):
    # Setup mock dependencies
    db = DatabaseManager(db_path=str(tmp_path / "test.db"))
    dedup = DeduplicationManager(db)
    
    # We will simulate a simplistic ScrapeTaskManager that the handler will call
    class MockScrapeTaskManager:
        def __init__(self):
            self.started_project = None
        
        def start_worker(self, project_id, debug_mode):
            self.started_project = project_id

    manager = MockScrapeTaskManager()
    
    # Instantiate handler
    handler = StartScrapeHandler(task_manager=manager)
    
    # Execute command
    cmd = StartScrapeCommand(project_id=42, debug_mode=True)
    await handler(cmd)
    
    assert manager.started_project == 42

