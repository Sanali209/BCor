from __future__ import annotations

import sys
import logging
from PySide6.QtWidgets import QApplication
from src.core.messagebus import MessageBus
from .messages import LaunchGuiCommand, LoadProjectCommand
from .ui.mainwindow import MainWindow
from .use_cases.load_project import LoadProjectUseCase
from .core.database import DatabaseManager

from .core.repositories.file_repository import FileRepository
from .core.repositories.cluster_repository import ClusterRepository
from .core.scan_session import ScanSession

logger = logging.getLogger(__name__)

async def launch_gui_handler(
    command: LaunchGuiCommand,
    bus: MessageBus,
    db: DatabaseManager,
    file_repo: FileRepository,
    cluster_repo: ClusterRepository,
    session: ScanSession,
) -> None:
    """Handler to launch the legacy MainWindow with dependencies from DI."""
    logger.info("Launching ImageDedup GUI via BCor Handler")
    
    # Ensure QApplication exists
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ImageDeduper (BCor)")
    
    # Inject dependencies into MainWindow (legacy style for now)
    window = MainWindow(session, file_repo, cluster_repo, db, bus=bus)
    window.show()

    
    # In a real async system, we might not block here, 
    # but for PySide6 we usually need the exec loop.
    # For now, we block since this is the top-level app launcher.
    app.exec()

async def load_project_handler(
    command: LoadProjectCommand,
    use_case: LoadProjectUseCase,
) -> None:
    """Handler to load a project using the BCor Use Case."""
    logger.info(f"Handling LoadProjectCommand for {command.path}")
    event = await use_case.execute(command.path)
    logger.info(f"Project loaded: {event.project_id}")

