"""Progress tracking and visualization utilities.

Ported and modernized from legacy appGlue/progress_visualize.py.
"""
from __future__ import annotations

import logging
from typing import Callable, Protocol

logger = logging.getLogger(__name__)


class IProgressVisualizer(Protocol):
    """Protocol for objects that can visualize progress."""
    def update_progress(self, progress: int, max_progress: int, message: str, description: str) -> None:
        ...


class ProgressManager:
    """Manager for tracking and notifying progress of long-running operations.
    
    Replaces legacy ProgressManager service.
    """

    def __init__(self, max_progress: int = 100):
        self.visualizers: list[IProgressVisualizer | Callable[..., None]] = []
        self.progress = 0
        self.max_progress = max_progress
        self.message = ""
        self.description = ""

    def add_visualizer(self, visualizer: IProgressVisualizer | Callable[..., None]) -> None:
        """Add a progress listener."""
        self.visualizers.append(visualizer)

    def set_description(self, description: str) -> None:
        """Set the overall task description."""
        self.description = description
        self.notify()

    def set_max(self, max_progress: int) -> None:
        """Set the maximum progress value."""
        self.max_progress = max_progress
        self.notify()

    def step(self, message: str = "", amount: int = 1) -> None:
        """Advance progress by a certain amount."""
        self.progress += amount
        if message:
            self.message = message
        self.notify()

    def reset(self, max_progress: int = 100) -> None:
        """Reset progress state."""
        self.progress = 0
        self.max_progress = max_progress
        self.message = ""
        self.description = ""
        self.notify()

    def notify(self) -> None:
        """Notify all visualizers of current state."""
        for visualizer in self.visualizers:
            try:
                if hasattr(visualizer, 'update_progress'):
                    visualizer.update_progress(
                        self.progress, self.max_progress, self.message, self.description
                    )
                else:
                    # Assume callable
                    visualizer(self.progress, self.max_progress, self.message, self.description)
            except Exception as e:
                logger.error(f"Error in progress visualizer: {e}")
