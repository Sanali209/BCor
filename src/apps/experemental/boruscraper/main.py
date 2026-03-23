import sys
import asyncio
import qasync
from pathlib import Path

# Add root to sys.path and remove script dir to prevent double-imports
root_dir = str(Path(__file__).resolve().parents[4])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

script_dir = str(Path(__file__).resolve().parent)
if script_dir in sys.path:
    sys.path.remove(script_dir)

from PySide6.QtWidgets import QApplication
from src.core.system import System
from src.apps.experemental.boruscraper.provider import BoruScraperProvider
from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.common.deduplication import DeduplicationManager
from src.apps.experemental.boruscraper.application.handlers import ScrapeTaskManager
from src.apps.experemental.boruscraper.infrastructure.events_adapter import GuiEventAdapter
from src.porting.porting import WindowsLoopManager

async def amain(app: QApplication):
    # Bootstrap BCor System
    manifest_path = Path(__file__).parent / "app.toml"
    system = System.from_manifest(str(manifest_path))
    await system.start()
    
    try:
        async with system.container() as request_container:
            # Resolve dependencies from Dishka container
            db = await request_container.get(DatabaseManager)
            dedup = await request_container.get(DeduplicationManager)
            task_manager = await request_container.get(ScrapeTaskManager)
            bus = await request_container.get(MessageBus)
            adapter = await request_container.get(GuiEventAdapter)
            from src.apps.experemental.boruscraper.application.template_registry import ScrapingTemplateRegistry
            template_registry = await request_container.get(ScrapingTemplateRegistry)
            loop = asyncio.get_running_loop()
            
            window = MainWindow(db=db, dedup=dedup, task_manager=task_manager, bus=bus, adapter=adapter, loop=loop, template_registry=template_registry)
            window.show()
            
            # Keep asyncio alive while qt loop runs
            stop_future = loop.create_future()
            app.aboutToQuit.connect(lambda: stop_future.set_result(None) if not stop_future.done() else None)
            await stop_future
    finally:
        logger.info("Closing system...")
        await system.stop()
        await WindowsLoopManager.drain_loop(0.2)

def main():
    WindowsLoopManager.setup_loop()
    app = QApplication.instance() or QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(amain(app))

if __name__ == "__main__":
    main()
