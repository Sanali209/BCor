import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from loguru import logger

from src.core.system import System
from src.apps.experemental.imgededupe.module import ImgeDeduplicationModule
from src.apps.experemental.imgededupe.ui.mainwindow import MainWindow
from src.apps.experemental.imgededupe.ui.adapter import GuiEventAdapter
from src.apps.experemental.imgededupe.core.scan_session import ScanSession
from src.apps.experemental.imgededupe.core.repositories.file_repository import FileRepository
from src.apps.experemental.imgededupe.core.repositories.cluster_repository import ClusterRepository
from src.apps.experemental.imgededupe.core.database import DatabaseManager
from src.apps.experemental.imgededupe.core.logger import qt_log_handler

from src.porting.porting import WindowsLoopManager

async def async_main():
    # 1. Logging Setup
    logger.remove()
    logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
    logger.add(qt_log_handler, format="{time:HH:mm:ss} <level>{message}</level>", level="INFO")

    # 2. BCor System Bootstrap
    system = System(modules=[ImgeDeduplicationModule()])
    await system.start()

    # 3. Resolve Dependencies from Container
    container = system.container
    
    session = await container.get(ScanSession)
    file_repo = await container.get(FileRepository)
    cluster_repo = await container.get(ClusterRepository)
    db_manager = await container.get(DatabaseManager)
    adapter = await container.get(GuiEventAdapter)

    # 4. Initialize UI
    from src.core.messagebus import MessageBus
    bus = await container.get(MessageBus)

    window = MainWindow(
        session=session,
        file_repo=file_repo,
        cluster_repo=cluster_repo,
        db_manager=db_manager,
        adapter=adapter,
        bus=bus
    )
    window.show()

    # Keep the async main running until the window is closed
    while window.isVisible():
        await asyncio.sleep(0.1)
    
    await system.stop()
    await WindowsLoopManager.drain_loop()

def main():
    WindowsLoopManager.setup_loop()
    app = QApplication(sys.argv)
    app.setApplicationName("ImageDeduper (BCor)")
    
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(async_main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == "__main__":
    main()
