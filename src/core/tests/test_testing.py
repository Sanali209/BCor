import pytest
from src.core.testing import BCorTestSystem
from src.core.system import System

@pytest.mark.asyncio
async def test_bcor_test_system_lifecycle():
    """Verify that BCorTestSystem correctly manages system start/stop."""
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        assert isinstance(system, System)
        assert system._started is True
    
    assert system._started is False
