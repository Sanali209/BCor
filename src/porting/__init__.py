"""
BCor Porting Kit.

A framework-level module designed to streamline the porting of legacy applications
to the BCor framework, with a specific focus on Windows stability, robust 
path handling, and resource management.
"""

from src.core.loop_policies import WindowsLoopManager
from src.common.paths import PathNormalizer
from src.common.asyncio_utils import AsyncPoolExecutor, async_delay, TaskThrottler
from src.porting.ui_bridge import BaseGuiAdapter
from src.common.database.sqlite_utils import SqliteRepositoryBase
from src.core.testing import BCorTestSystem, run_test_system

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
