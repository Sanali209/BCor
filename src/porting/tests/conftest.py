import sys
import asyncio
import os
import pytest
from unittest.mock import patch
from src.core.loop_policies import WindowsLoopManager

# Ensure Windows stability for async tests
WindowsLoopManager.setup_loop()

@pytest.fixture(autouse=True)
def reset_service_container():
    """Reset the legacy ServiceContainer singleton between tests."""
    from src.apps.experemental.sanali.Python.core_apps.services.service_container import _service_container
    import src.apps.experemental.sanali.Python.core_apps.services.service_container as sc
    sc._service_container = None
    yield
    sc._service_container = None

def pytest_unconfigure(config):
    """
    Force process exit on Windows to avoid hangs during interpreter teardown.
    """
    if sys.platform == "win32":
        # Final cleanup attempt
        print("\nBCor Porting Kit: Forcing process exit to prevent teardown hang...", flush=True)
        import time
        time.sleep(0.1)
        os._exit(0)
