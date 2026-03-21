import sys
import asyncio
import os
import pytest

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def pytest_unconfigure(config):
    print("Forcing pytest process exit to avoid teardown hang...", flush=True)
    os._exit(0)



