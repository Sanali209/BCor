from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Slot
from loguru import logger

class BaseGuiAdapter(QObject):
    """Standardizes communication between BCor MessageBus and Qt UI.
    
    This class acts as a bridge between the asynchronous domain events
    of the BCor framework and the synchronous signal-slot mechanism of Qt.
    Inherit from this class to create application-specific adapters.
    """
    
    # Common lifecycle signals
    started = Signal(str)  # Emitted when a task or process starts.
    progress = Signal(int, str)  # Emitted with percentage (0-100) and status text.
    completed = Signal(str, dict)  # Emitted when a task finishes with status and results.
    error = Signal(str)  # Emitted when an error occurs.
    
    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the adapter.
        
        Args:
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        logger.debug(f"{self.__class__.__name__} initialized")

    @Slot(str)
    def on_task_started(self, task_name: str):
        """Slot to handle task start events.
        
        Args:
            task_name: Name of the started task.
        """
        self.started.emit(task_name)

    @Slot(int, str)
    def on_progress_update(self, percent: int, status: str):
        """Slot to handle progress updates.
        
        Args:
            percent: Completion percentage (0-100).
            status: Description of the current status.
        """
        self.progress.emit(percent, status)

    @Slot(str, dict)
    def on_task_completed(self, status: str, results: dict):
        """Slot to handle task completion.
        
        Args:
            status: Final status message.
            results: Dictionary containing task results.
        """
        self.completed.emit(status, results)

    @Slot(str)
    def on_error(self, message: str):
        """Slot to handle errors.
        
        Args:
            message: Error message string.
        """
        self.error.emit(message)
