"""E2E tests for boruscraper porting kit integration.

These tests verify:
- BCorTestSystem lifecycle (start/stop with loop drainage)
- DatabaseManager project creation via SqliteRepositoryBase
- MessageBus command dispatching
- ScrapeTaskManager worker registration/cleanup

Note: Tests that launch Playwright are skipped if chromium is not installed.
Run `playwright install chromium` to enable browser-based tests.
"""
import pytest
import asyncio
import uuid
import shutil
from pathlib import Path

from src.porting.testing_utils import BCorTestSystem
from src.core.messagebus import MessageBus
from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.application.messages import StartScrapeCommand, StopScrapeCommand
from src.apps.experemental.boruscraper.application.handlers import ScrapeTaskManager


MANIFEST = Path("src/apps/experemental/boruscraper/app.toml").absolute()

# Skip playwright tests if chromium executable is not available
import glob as _glob
_chromium_exes = _glob.glob(str(Path.home() / "AppData/Local/ms-playwright/chromium-*/chrome-win64/chrome.exe"))
_PLAYWRIGHT_AVAILABLE = bool(_chromium_exes) or bool(_shutil.which("chromium") or _shutil.which("chromium-browser") or _shutil.which("google-chrome"))
playwright_required = pytest.mark.skipif(
    not _PLAYWRIGHT_AVAILABLE,
    reason="Playwright/Chromium not installed. Run: playwright install chromium"
)


@pytest.mark.asyncio
async def test_system_lifecycle():
    """Verify BCorTestSystem starts/stops with loop drainage.
    
    This is a pure infrastructure test — no browser required.
    Validates WindowsLoopManager integration in testing_utils.
    """
    async with BCorTestSystem(str(MANIFEST)).run() as system:
        assert system is not None
        assert system.container is not None


@pytest.mark.asyncio
async def test_database_manager_create_project(tmp_path):
    """Verify DatabaseManager can create projects (SqliteRepositoryBase inheritance).
    
    Tests the refactored DatabaseManager that now inherits from SqliteRepositoryBase.
    """
    async with BCorTestSystem(str(MANIFEST)).run() as system:
        db: DatabaseManager = await system.container.get(DatabaseManager)

        unique_name = f"Test Project {uuid.uuid4().hex[:8]}"
        project_id = db.create_project(
            name=unique_name,
            settings={
                "start_urls": ["https://example.com"],
                "save_path": str(tmp_path / "downloads"),
                "resource_save_path_pattern": "{topic_id}/{field_name}.{ext}",
                "selectors": {
                    "topic_preview": "div.item",
                    "topic_link": "a",
                    "pagination_next": "a.next",
                },
                "fields_to_parse": [],
                "delays": {
                    "delay_between_list_pages_s": 0.1,
                    "delay_between_topics_s": 0.1,
                    "download_delay_range_s": [0.1, 0.2],
                },
                "navigation_timeout_ms": 5000,
                "download_timeout_ms": 5000,
            },
            start_urls=["https://example.com"],
        )
        assert project_id > 0, f"Expected a valid project ID, got {project_id}"

        # Verify via get_all_projects (uses row_to_dict from SqliteRepositoryBase)
        projects = db.get_all_projects()
        project_names = [p["name"] for p in projects]
        assert unique_name in project_names


@pytest.mark.asyncio
@playwright_required
async def test_scrape_worker_lifecycle(tmp_path):
    """Verify full scraping worker start/stop lifecycle.
    
    Requires Playwright/Chromium. Tests:
    - MessageBus command dispatch  
    - ScrapeTaskManager worker registration
    - TaskThrottler integration (concurrency management)
    - WorkerFinishedEvent cleanup
    """
    async with BCorTestSystem(str(MANIFEST)).run() as system:
        container = system.container
        task_manager: ScrapeTaskManager = await container.get(ScrapeTaskManager)
        db: DatabaseManager = await container.get(DatabaseManager)
        bus: MessageBus = await container.get(MessageBus)

        unique_name = f"Test Project {uuid.uuid4().hex[:8]}"
        project_id = db.create_project(
            name=unique_name,
            settings={
                "start_urls": ["https://example.com"],
                "save_path": str(tmp_path / "downloads"),
                "resource_save_path_pattern": "{topic_id}/{field_name}.{ext}",
                "selectors": {
                    "topic_preview": "div.item",
                    "topic_link": "a",
                    "pagination_next": "a.next",
                },
                "fields_to_parse": [],
                "delays": {
                    "delay_between_list_pages_s": 0.1,
                    "delay_between_topics_s": 0.1,
                    "download_delay_range_s": [0.1, 0.2],
                },
                "navigation_timeout_ms": 5000,
                "download_timeout_ms": 5000,
            },
            start_urls=["https://example.com"],
        )
        assert project_id > 0

        # Start worker
        await bus.dispatch(StartScrapeCommand(project_id=project_id, debug_mode=True))
        await asyncio.sleep(2)

        worker = task_manager.get_worker(project_id)
        assert worker is not None, "ScrapeTaskManager must register a worker"
        assert worker.is_running

        # Stop worker
        await bus.dispatch(StopScrapeCommand(project_id=project_id))
        await asyncio.sleep(1)
        assert task_manager.get_worker(project_id) is None
