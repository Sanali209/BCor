"""
BCor Porting Kit.

A framework-level module designed to streamline the porting of legacy applications
to the BCor framework, with a specific focus on Windows stability, robust 
path handling, and resource management.
"""

from .porting import WindowsLoopManager, PathNormalizer, AsyncPoolExecutor, async_delay
from .ui_bridge import BaseGuiAdapter
from .repository_utils import SqliteRepositoryBase
from .testing_utils import BCorTestSystem, run_test_system
from .async_utils import TaskThrottler

__all__ = [
    "WindowsLoopManager",
    "PathNormalizer",
    "AsyncPoolExecutor",
    "async_delay",
    "BaseGuiAdapter",
    "SqliteRepositoryBase",
    "BCorTestSystem",
    "run_test_system",
    "TaskThrottler",
]
