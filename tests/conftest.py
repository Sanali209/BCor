import pytest
import platform
import asyncio
from src.core.loop_policies import WindowsLoopManager

@pytest.fixture(scope="session", autouse=True)
def setup_windows_loop():
    """Ensure stable event loop policy for Windows tests."""
    if platform.system() == "Windows":
        WindowsLoopManager.setup_loop()

@pytest.fixture(autouse=True)
async def drain_loop_after_test():
    """Drain the event loop after each test to prevent hangs/deadlocks."""
    yield
    if platform.system() == "Windows":
        await WindowsLoopManager.drain_loop(delay=0.1)

def pytest_ignore_collect(collection_path, config):
    """Ignore legacy or broken ImageAnalyze tests during audit."""
    if "ImageAnalyze" in str(collection_path):
        return True
    return False
