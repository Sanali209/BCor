import asyncio
import platform
import pytest
from src.core.loop_policies import WindowsLoopManager

@pytest.mark.asyncio
async def test_windows_loop_policy_applied():
    """
    Test that WindowsLoopManager sets the correct loop policy on Windows.
    """
    WindowsLoopManager.setup_loop()
    
    if platform.system() == "Windows":
        policy = asyncio.get_event_loop_policy()
        assert isinstance(policy, asyncio.WindowsSelectorEventLoopPolicy)

@pytest.mark.asyncio
async def test_qasync_loop_running():
    """
    Verify that an event loop is running (simulating qasync or standard loop).
    """
    loop = asyncio.get_running_loop()
    assert loop.is_running()
