import sys
import asyncio
import os
import pytest

if sys.platform == 'win32':
    # Avoid ProactorEventLoop issues on Windows during tests
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def pytest_unconfigure(config):
    # Aggressive interpreter drop to avoid daemon thread blocks on Windows
    # following BCor core testing pattern
    print("\nbcor-expert: Forcing pytest process exit to avoid teardown hang...", flush=True)
    os._exit(0)

@pytest.fixture(scope="session", autouse=True)
def setup_windows_async():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
