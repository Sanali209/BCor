import pytest
import asyncio
import time
from src.common.asyncio_utils import TaskThrottler

@pytest.mark.asyncio
async def test_task_throttler_concurrency():
    """Verify that TaskThrottler correctly limits concurrency."""
    limit = 2
    throttler = TaskThrottler(limit)
    active_count = 0
    max_observed_concurrency = 0
    
    async def task():
        nonlocal active_count, max_observed_concurrency
        active_count += 1
        max_observed_concurrency = max(max_observed_concurrency, active_count)
        await asyncio.sleep(0.1)
        active_count -= 1
        
    tasks = [throttler.run(task) for _ in range(5)]
    await asyncio.gather(*tasks)
    
    assert max_observed_concurrency <= limit
    assert active_count == 0

@pytest.mark.asyncio
async def test_task_throttler_decorator():
    """Verify that the throttle decorator working correctly."""
    throttler = TaskThrottler(1)
    
    @throttler.throttle
    async def throttled_task():
        return True
        
    assert await throttled_task() is True
